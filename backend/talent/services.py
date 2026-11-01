from companies.models import CompanyCollegePartnership
from students.models import StudentProfile


def recruiter_candidate_queryset(user):
    """Students discoverable by this recruiter's company through verified colleges."""

    profile = getattr(user, "recruiter_profile", None)
    if profile is None:
        return StudentProfile.objects.none()

    verified_college_ids = CompanyCollegePartnership.objects.filter(
        company=profile.company,
        status=CompanyCollegePartnership.Status.VERIFIED,
        college__is_active=True,
    ).values_list("college_id", flat=True)

    return (
        StudentProfile.objects.filter(
            college_id__in=verified_college_ids,
            is_visible_to_recruiters=True,
            user__is_active=True,
        )
        .select_related("user", "college", "program")
        .prefetch_related(
            "skills__skill", "resumes", "projects", "certifications", "experiences"
        )
        .distinct()
    )


def recruiter_can_access_student(user, student):
    return recruiter_candidate_queryset(user).filter(pk=student.pk).exists()
