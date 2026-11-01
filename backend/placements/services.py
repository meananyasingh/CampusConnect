from documents.services import document_verification_summary
from students.services import calculate_profile_completion

from .models import CollegePlacementPolicy


def get_effective_policy(college):
    try:
        return college.placement_policy
    except CollegePlacementPolicy.DoesNotExist:
        return CollegePlacementPolicy(college=college)


def get_college_policy_blockers(student):
    policy = get_effective_policy(student.college)
    blockers = []
    profile_completion = calculate_profile_completion(student)["percentage"]
    document_summary = document_verification_summary(student)

    if not policy.applications_enabled:
        blockers.append(policy.student_message or "Your college has temporarily paused placement applications.")
    if policy.require_verified_documents and not document_summary["is_complete"]:
        blockers.append("Complete verification of all required academic documents.")
    if profile_completion < policy.minimum_profile_completion:
        blockers.append(
            f"Your profile must be at least {policy.minimum_profile_completion}% complete "
            f"(currently {profile_completion}%)."
        )
    if policy.minimum_cgpa is not None and (
        student.cgpa is None or student.cgpa < policy.minimum_cgpa
    ):
        blockers.append(f"Your college requires a minimum CGPA of {policy.minimum_cgpa}.")
    if policy.max_active_backlogs is not None and student.active_backlogs > policy.max_active_backlogs:
        blockers.append(
            f"Your college allows at most {policy.max_active_backlogs} active backlog(s)."
        )
    return blockers


def get_student_placement_readiness(student):
    policy = get_effective_policy(student.college)
    profile = calculate_profile_completion(student)
    documents = document_verification_summary(student)
    blockers = get_college_policy_blockers(student)
    return {
        "is_ready": not blockers,
        "blockers": blockers,
        "profile_completion": profile["percentage"],
        "document_verification": documents,
        "policy": {
            "applications_enabled": policy.applications_enabled,
            "require_verified_documents": policy.require_verified_documents,
            "minimum_profile_completion": policy.minimum_profile_completion,
            "minimum_cgpa": policy.minimum_cgpa,
            "max_active_backlogs": policy.max_active_backlogs,
            "student_message": policy.student_message,
        },
    }
