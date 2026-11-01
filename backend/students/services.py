def calculate_profile_completion(profile):
    """Return a transparent, recruiter-readiness score totaling 100 points."""

    user = profile.user
    skill_count = profile.skills.count()
    definitions = (
        (
            "personal",
            "Personal details",
            20,
            (
                ("First name", user.first_name),
                ("Last name", user.last_name),
                ("Phone", profile.phone),
                ("Date of birth", profile.date_of_birth),
                ("Location", profile.location),
                ("Career objective", profile.career_objective),
            ),
        ),
        (
            "academic",
            "Academic performance",
            20,
            (
                ("CGPA", profile.cgpa is not None),
                ("10th percentage", profile.tenth_percentage is not None),
                ("12th percentage", profile.twelfth_percentage is not None),
            ),
        ),
        (
            "career",
            "Career presence",
            10,
            (
                ("Preferred job role", profile.preferred_job_role),
                ("At least one professional link", profile.linkedin_url or profile.github_url or profile.portfolio_url),
            ),
        ),
        (
            "skills",
            "Skills",
            15,
            tuple((f"Skill {number}", number <= skill_count) for number in range(1, 4)),
        ),
        ("projects", "Projects", 15, (("At least one project", profile.projects.exists()),)),
        ("experience", "Experience", 5, (("At least one experience", profile.experiences.exists()),)),
        ("certifications", "Certifications", 5, (("At least one certification", profile.certifications.exists()),)),
        ("resume", "Resume", 10, (("A primary resume", profile.resumes.filter(is_primary=True).exists()),)),
    )

    sections = []
    overall = 0
    missing = []
    for key, label, weight, checks in definitions:
        completed = sum(bool(value) for _, value in checks)
        percent = round((completed / len(checks)) * 100)
        weighted_score = round((percent / 100) * weight)
        overall += weighted_score
        section_missing = [name for name, value in checks if not value]
        missing.extend(section_missing)
        sections.append(
            {
                "key": key,
                "label": label,
                "weight": weight,
                "percentage": percent,
                "score": weighted_score,
                "missing": section_missing,
            }
        )

    return {"percentage": min(overall, 100), "sections": sections, "missing": missing}
