from django.utils import timezone

from .models import Opportunity, OpportunityCollegeInvitation


def get_eligibility_reasons(opportunity, student):
    reasons = []
    if opportunity.min_cgpa and (student.cgpa is None or student.cgpa < opportunity.min_cgpa):
        reasons.append(f"Minimum CGPA required: {opportunity.min_cgpa}.")
    if student.active_backlogs > opportunity.max_active_backlogs:
        reasons.append(f"Maximum active backlogs allowed: {opportunity.max_active_backlogs}.")
    if opportunity.graduation_year_from and student.graduation_year < opportunity.graduation_year_from:
        reasons.append(f"Graduation year must be {opportunity.graduation_year_from} or later.")
    if opportunity.graduation_year_to and student.graduation_year > opportunity.graduation_year_to:
        reasons.append(f"Graduation year must be {opportunity.graduation_year_to} or earlier.")
    eligible_program_ids = {program.id for program in opportunity.eligible_programs.all()}
    if eligible_program_ids and student.program_id not in eligible_program_ids:
        reasons.append("Your academic program is not eligible for this opportunity.")
    return reasons


def calculate_opportunity_match(opportunity, student):
    """Return an explainable 0-100 fit score for an eligible opportunity."""
    score = 0
    reasons = []
    student_skills = {name.casefold() for name in student.skills.values_list("skill__name", flat=True)}
    required_skills = list(opportunity.required_skills.all())
    matched = [skill.name for skill in required_skills if skill.name.casefold() in student_skills]
    if required_skills:
        skill_score = round(len(matched) / len(required_skills) * 50)
        score += skill_score
        if matched:
            reasons.append(f"Matches {len(matched)} of {len(required_skills)} required skills")
    else:
        score += 25
        reasons.append("No specific skill requirement")

    preferred_role_words = set(student.preferred_job_role.casefold().split())
    title_words = set(opportunity.title.casefold().replace("-", " ").split())
    if preferred_role_words and preferred_role_words & title_words:
        score += 20
        reasons.append("Matches your preferred job role")

    preferred_locations = {
        value.strip().casefold() for value in student.preferred_locations.split(",") if value.strip()
    }
    if opportunity.work_mode == Opportunity.WorkMode.REMOTE:
        score += 15
        reasons.append("Remote work option")
    elif opportunity.location.casefold() in preferred_locations:
        score += 15
        reasons.append("Matches a preferred location")

    eligible_program_ids = {program.id for program in opportunity.eligible_programs.all()}
    if eligible_program_ids and student.program_id in eligible_program_ids:
        score += 10
        reasons.append("Specifically targets your academic program")
    elif not eligible_program_ids:
        score += 5

    if opportunity.compensation_min is not None or opportunity.compensation_max is not None:
        score += 5
        reasons.append("Compensation details available")
    return min(score, 100), reasons, matched


def get_recommended_opportunities(queryset, student, limit=12):
    from placements.services import get_college_policy_blockers

    if get_college_policy_blockers(student):
        return []
    recommendations = []
    for opportunity in queryset:
        if get_eligibility_reasons(opportunity, student):
            continue
        score, reasons, matched = calculate_opportunity_match(opportunity, student)
        opportunity.match_score = score
        opportunity.match_reasons = reasons
        opportunity.recommendation_matched_skills = matched
        recommendations.append(opportunity)
    return sorted(
        recommendations,
        key=lambda item: (-item.match_score, item.application_deadline, -item.id),
    )[:limit]


def sync_approved_opportunity_audience(opportunity):
    """Rebuild the public college/program audience from approved invitations only."""

    approved = opportunity.college_invitations.filter(
        status=OpportunityCollegeInvitation.Status.APPROVED,
    ).prefetch_related("eligible_programs")
    opportunity.target_colleges.set(invitation.college_id for invitation in approved)
    program_ids = {
        program.id
        for invitation in approved
        for program in invitation.eligible_programs.all()
    }
    opportunity.eligible_programs.set(program_ids)
    if approved.exists() and opportunity.status == Opportunity.Status.DRAFT:
        opportunity.status = Opportunity.Status.PUBLISHED
        opportunity.published_at = opportunity.published_at or timezone.now()
        opportunity.save(update_fields=("status", "published_at", "updated_at"))
    return opportunity
