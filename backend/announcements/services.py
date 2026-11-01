from notifications.models import Notification
from notifications.services import notify_college_admins, notify_users
from students.models import StudentProfile


def notify_announcement_students(announcement):
    students = StudentProfile.objects.select_related("user").filter(college=announcement.college, user__is_active=True)
    program_ids = list(announcement.target_programs.values_list("id", flat=True))
    if program_ids:
        students = students.filter(program_id__in=program_ids)
    years = announcement.target_graduation_years
    if years:
        students = students.filter(graduation_year__in=years)
    return notify_users(
        users=(student.user for student in students),
        category=Notification.Category.ANNOUNCEMENT,
        title=announcement.title,
        message=f"New {announcement.get_announcement_type_display().lower()} from {announcement.college.name}.",
        link="/student/announcements",
    )


def notify_pending_announcement(announcement):
    return notify_college_admins(
        college=announcement.college,
        category=Notification.Category.SYSTEM,
        title="Announcement awaiting approval",
        message=f"{announcement.company.name} submitted “{announcement.title}” for review.",
        link="/admin/announcements",
    )
