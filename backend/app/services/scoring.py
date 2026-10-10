
from sqlmodel import Session, select

from app.models.core import Assessment, GraceAdjustment
from app.models.grading import Grade, VivaSession


def compute_final_score(
    assessment: Assessment,
    grade: Grade | None,
    viva: VivaSession | None,
    session: Session
) -> dict:
    if not grade:
        return {}

    work_marks = grade.final_total if grade.status == "approved" else grade.ai_total
    max_marks = assessment.max_marks
    work_pct = work_marks / max_marks if max_marks > 0 else 0

    viva_done = viva is not None and viva.status == "done"
    understanding = viva.understanding if viva_done else None

    if assessment.viva_enabled and viva_done and understanding is not None:
        w = assessment.viva_weight
        blended = (1 - w) * work_pct + w * understanding
    else:
        blended = work_pct
        
    final_marks = round(blended * max_marks, 1)

    # Calculate grace
    grace_total = sum(
        g.marks for g in session.exec(
            select(GraceAdjustment)
            .where(GraceAdjustment.assessment_id == assessment.id)
            .where(GraceAdjustment.undone_at.is_(None))
        ).all()
    )

    final_with_grace = min(max_marks, final_marks + grace_total)
    
    return {
        "work_marks": work_marks,
        "understanding": understanding,
        "viva_weight": assessment.viva_weight if assessment.viva_enabled else 0,
        "final_marks": final_marks,
        "grace_marks": grace_total,
        "final_with_grace": final_with_grace,
        "final_pct": round((final_with_grace / max_marks) * 100, 1) if max_marks > 0 else 0
    }
