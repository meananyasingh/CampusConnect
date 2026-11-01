from .models import StudentDocument


REQUIRED_DOCUMENT_GROUPS = (
    {
        "key": "tenth_marksheet",
        "label": "10th marksheet",
        "types": (StudentDocument.DocumentType.TENTH_MARKSHEET,),
    },
    {
        "key": "senior_secondary",
        "label": "12th or diploma marksheet",
        "types": (
            StudentDocument.DocumentType.TWELFTH_MARKSHEET,
            StudentDocument.DocumentType.DIPLOMA_MARKSHEET,
        ),
    },
    {
        "key": "college_id",
        "label": "College identity card",
        "types": (StudentDocument.DocumentType.COLLEGE_ID,),
    },
)


def document_verification_summary(student):
    documents = list(student.documents.all())
    requirements = []
    for group in REQUIRED_DOCUMENT_GROUPS:
        matches = [item for item in documents if item.document_type in group["types"]]
        verified = any(item.status == StudentDocument.Status.VERIFIED for item in matches)
        pending = any(item.status == StudentDocument.Status.PENDING for item in matches)
        requirements.append({
            "key": group["key"],
            "label": group["label"],
            "is_verified": verified,
            "is_pending": pending and not verified,
            "status": "VERIFIED" if verified else "PENDING" if pending else "MISSING",
        })
    verified_count = sum(item["is_verified"] for item in requirements)
    return {
        "is_complete": verified_count == len(requirements),
        "verified_required": verified_count,
        "required_total": len(requirements),
        "percentage": round(verified_count / len(requirements) * 100),
        "requirements": requirements,
    }

