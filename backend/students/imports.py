import csv
import io
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import User
from accounts.services import send_activation_email
from colleges.models import AcademicProgram

from .models import StudentImportBatch, StudentProfile, enrollment_number_validator


HEADERS = (
    "email", "first_name", "last_name", "enrollment_number", "program_id",
    "graduation_year", "cgpa", "active_backlogs",
)
MAX_IMPORT_ROWS = 500
MAX_FILE_SIZE = 1024 * 1024


def build_template(college):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    program = college.academic_programs.filter(is_active=True).first()
    if program:
        writer.writerow([
            "student@example.com", "Student", "Name", f"{college.code}001",
            program.id, timezone.localdate().year + 1, "8.25", "0",
        ])
    return output.getvalue()


def preview_import(upload, college, admin):
    if upload.size > MAX_FILE_SIZE:
        raise ValidationError({"file": "CSV file must not exceed 1 MB."})
    if not upload.name.lower().endswith(".csv"):
        raise ValidationError({"file": "Upload a CSV file."})
    try:
        text = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError({"file": "CSV must use UTF-8 encoding."}) from error

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValidationError({"file": "The CSV file is empty."})
    normalized_headers = tuple((header or "").strip().lower() for header in reader.fieldnames)
    missing = [header for header in HEADERS if header not in normalized_headers]
    if missing:
        raise ValidationError({"file": f"Missing required columns: {', '.join(missing)}."})

    raw_rows = list(reader)
    if not raw_rows:
        raise ValidationError({"file": "Add at least one student row."})
    if len(raw_rows) > MAX_IMPORT_ROWS:
        raise ValidationError({"file": f"A single import can contain at most {MAX_IMPORT_ROWS} students."})

    programs = {str(item.id): item for item in college.academic_programs.filter(is_active=True)}
    seen_emails = set()
    seen_enrollments = set()
    results = []
    header_map = dict(zip(normalized_headers, reader.fieldnames))
    for index, raw in enumerate(raw_rows, start=2):
        data = {key: (raw.get(header_map[key], "") or "").strip() for key in HEADERS}
        data["email"] = data["email"].lower()
        data["enrollment_number"] = data["enrollment_number"].upper()
        errors = validate_row(data, college, programs, seen_emails, seen_enrollments)
        if data["email"]:
            seen_emails.add(data["email"])
        if data["enrollment_number"]:
            seen_enrollments.add(data["enrollment_number"])
        results.append({"row_number": index, "data": data, "errors": errors, "is_valid": not errors})

    valid_count = sum(row["is_valid"] for row in results)
    return StudentImportBatch.objects.create(
        college=college,
        created_by=admin,
        original_filename=upload.name[:255],
        total_rows=len(results),
        valid_rows=valid_count,
        invalid_rows=len(results) - valid_count,
        rows=results,
    )


def validate_row(data, college, programs, seen_emails=None, seen_enrollments=None):
    errors = {}
    email = data["email"]
    enrollment = data["enrollment_number"]
    if not email:
        errors["email"] = "Email is required."
    else:
        try:
            validate_email(email)
        except DjangoValidationError:
            errors["email"] = "Enter a valid email address."
        if User.objects.filter(email__iexact=email).exists():
            errors["email"] = "An account with this email already exists."
        elif seen_emails is not None and email in seen_emails:
            errors["email"] = "This email is repeated in the CSV."
    for field, label in (("first_name", "First name"), ("last_name", "Last name")):
        if not data[field]:
            errors[field] = f"{label} is required."
        elif len(data[field]) > 150:
            errors[field] = f"{label} is too long."
    if not enrollment:
        errors["enrollment_number"] = "Enrollment number is required."
    else:
        try:
            enrollment_number_validator(enrollment)
        except DjangoValidationError as error:
            errors["enrollment_number"] = error.messages[0]
        if StudentProfile.objects.filter(college=college, enrollment_number__iexact=enrollment).exists():
            errors["enrollment_number"] = "This enrollment number already exists in your college."
        elif seen_enrollments is not None and enrollment in seen_enrollments:
            errors["enrollment_number"] = "This enrollment number is repeated in the CSV."
    if data["program_id"] not in programs:
        errors["program_id"] = "Select an active program from your college."
    try:
        year = int(data["graduation_year"])
        if year < 2000 or year > 2100:
            raise ValueError
    except ValueError:
        errors["graduation_year"] = "Graduation year must be between 2000 and 2100."
    if data["cgpa"]:
        try:
            cgpa = Decimal(data["cgpa"])
            if cgpa < 0 or cgpa > 10:
                raise InvalidOperation
        except InvalidOperation:
            errors["cgpa"] = "CGPA must be between 0 and 10."
    try:
        backlogs = int(data["active_backlogs"] or "0")
        if backlogs < 0:
            raise ValueError
    except ValueError:
        errors["active_backlogs"] = "Active backlogs must be zero or a positive whole number."
    return errors


@transaction.atomic
def confirm_import(batch):
    if batch.status != StudentImportBatch.Status.PREVIEW:
        raise ValidationError({"batch": "This import has already been completed."})

    valid_rows = [row for row in batch.rows if row["is_valid"]]
    if not valid_rows:
        raise ValidationError({"batch": "This file has no valid student rows to import."})
    programs = {str(item.id): item for item in batch.college.academic_programs.filter(is_active=True)}
    current_errors = []
    for row in valid_rows:
        errors = validate_row(row["data"], batch.college, programs)
        if errors:
            current_errors.append({"row_number": row["row_number"], "errors": errors})
    if current_errors:
        raise ValidationError({"rows": current_errors, "batch": "Some records changed after preview. Upload the CSV again."})

    imported_users = []
    for row in valid_rows:
        data = row["data"]
        user = User(email=data["email"], first_name=data["first_name"], last_name=data["last_name"], role=User.Role.STUDENT)
        user.set_unusable_password()
        user.save()
        StudentProfile.objects.create(
            user=user,
            college=batch.college,
            program=programs[data["program_id"]],
            enrollment_number=data["enrollment_number"],
            graduation_year=int(data["graduation_year"]),
            cgpa=Decimal(data["cgpa"]) if data["cgpa"] else None,
            active_backlogs=int(data["active_backlogs"] or "0"),
        )
        imported_users.append(user)

    batch.status = StudentImportBatch.Status.COMPLETED
    batch.imported_count = len(imported_users)
    batch.completed_at = timezone.now()
    batch.save(update_fields=("status", "imported_count", "completed_at"))
    transaction.on_commit(lambda: send_activation_emails(imported_users, batch.college.name))
    return batch


def send_activation_emails(users, college_name):
    for user in users:
        send_activation_email(user, college_name)
