import json

from .models import AuditEvent


IGNORED_VIEW_NAMES = {
    "token-refresh", "logout", "password-reset-request", "password-reset-confirm",
}
SENSITIVE_FIELDS = {
    "password", "password_confirm", "access", "refresh", "token", "file",
    "logo", "profile_picture",
}

CATEGORY_PREFIXES = {
    "application": AuditEvent.Category.APPLICATION,
    "interview": AuditEvent.Category.INTERVIEW,
    "round": AuditEvent.Category.INTERVIEW,
    "opportunity": AuditEvent.Category.OPPORTUNITY,
    "partnership": AuditEvent.Category.COMPANY,
    "company": AuditEvent.Category.COMPANY,
    "document": AuditEvent.Category.DOCUMENT,
    "placement": AuditEvent.Category.PLACEMENT,
    "drive": AuditEvent.Category.PLACEMENT,
    "announcement": AuditEvent.Category.COMMUNICATION,
    "notification": AuditEvent.Category.COMMUNICATION,
    "student": AuditEvent.Category.ACCOUNT,
}


class AuditEventMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._audit_changed_fields = self._json_fields(request)
        response = self.get_response(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and 200 <= response.status_code < 300:
            self._record(request, response)
        return response

    def _record(self, request, response):
        user = getattr(request, "user", None)
        match = getattr(request, "resolver_match", None)
        view_name = match.view_name if match else ""
        if not user or not user.is_authenticated or view_name in IGNORED_VIEW_NAMES or view_name.startswith("audit-"):
            return

        college = None
        company = None
        if user.role == "ADMIN":
            profile = getattr(user, "college_admin_profile", None)
            college = profile.college if profile else None
        elif user.role == "STUDENT":
            profile = getattr(user, "student_profile", None)
            college = profile.college if profile else None
        elif user.role == "RECRUITER":
            profile = getattr(user, "recruiter_profile", None)
            company = profile.company if profile else None

        response_data = getattr(response, "data", {})
        response_data = response_data if isinstance(response_data, dict) else {}
        if college is None:
            college = self._response_college(response_data)
        fields = request._audit_changed_fields
        category = self._category(view_name)
        action = view_name.replace("-", " ").strip().title() or f"{request.method.title()} request"
        target_type = view_name.rsplit("-", 1)[0].replace("-", " ") if view_name else ""
        target_id = response_data.get("id") or (match.kwargs.get("pk") if match else "") or ""
        target_label = self._target_label(response_data)
        description = f"{user.get_full_name() or user.email} completed {action.lower()}"
        if target_label:
            description += f" for {target_label}"
        context = {
            key: response_data[key]
            for key in ("status", "status_display", "imported_count", "valid_rows", "invalid_rows")
            if key in response_data
        }
        try:
            colleges = [college] if college else []
            if not colleges and company:
                colleges = list({
                    partnership.college_id: partnership.college
                    for partnership in company.college_partnerships.select_related("college")
                }.values())
            colleges = colleges or [None]
            AuditEvent.objects.bulk_create([
                AuditEvent(
                    actor=user,
                    actor_email=user.email,
                    actor_name=user.get_full_name(),
                    actor_role=user.role,
                    college=event_college,
                    company=company,
                    category=category,
                    action=action,
                    description=description[:500],
                    endpoint=request.path[:255],
                    http_method=request.method,
                    target_type=target_type[:100],
                    target_id=str(target_id)[:80],
                    target_label=target_label[:255],
                    changed_fields=fields,
                    context=context,
                    ip_address=self._ip_address(request),
                )
                for event_college in colleges
            ])
        except Exception:
            # Audit recording must never break the completed business operation.
            return

    @staticmethod
    def _category(view_name):
        lowered = view_name.lower()
        for prefix, category in CATEGORY_PREFIXES.items():
            if prefix in lowered:
                return category
        return AuditEvent.Category.SYSTEM

    @staticmethod
    def _target_label(data):
        for key in ("title", "name", "original_filename", "email", "enrollment_number"):
            if data.get(key):
                return str(data[key])
        company = data.get("company")
        if isinstance(company, dict):
            return str(company.get("name", ""))
        student = data.get("student")
        if isinstance(student, dict):
            return str(student.get("name") or student.get("email") or "")
        return ""

    @staticmethod
    def _response_college(data):
        from colleges.models import College
        from students.models import StudentProfile

        college = data.get("college")
        if isinstance(college, dict) and college.get("id"):
            return College.objects.filter(pk=college["id"]).first()
        student = data.get("student")
        if isinstance(student, dict) and student.get("id"):
            return College.objects.filter(students__id=student["id"]).first()
        application = data.get("application")
        if isinstance(application, dict):
            student = application.get("student")
            if isinstance(student, dict) and student.get("id"):
                return College.objects.filter(students__id=student["id"]).first()
        student_id = data.get("student_id")
        if student_id:
            profile = StudentProfile.objects.filter(pk=student_id).select_related("college").first()
            return profile.college if profile else None
        return None

    @staticmethod
    def _ip_address(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        return forwarded or request.META.get("REMOTE_ADDR") or None

    @staticmethod
    def _json_fields(request):
        if request.method not in {"POST", "PUT", "PATCH"} or "application/json" not in request.content_type:
            return []
        try:
            data = json.loads(request.body or b"{}")
        except (TypeError, ValueError, UnicodeDecodeError):
            return []
        if not isinstance(data, dict):
            return []
        return sorted(key for key in data if key.lower() not in SENSITIVE_FIELDS)
