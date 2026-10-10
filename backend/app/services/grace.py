import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.core import Assessment, GraceAdjustment, Submission
from app.models.grading import Grade
from app.schemas.analytics import GraceEntry, GraceMetrics, GracePreview, GraceState


def get_grace_state(session: Session, assessment_id: str) -> GraceState:
    entries = session.exec(
        select(GraceAdjustment)
        .where(GraceAdjustment.assessment_id == assessment_id)
        .order_by(GraceAdjustment.applied_at)
    ).all()
    
    total = sum(e.marks for e in entries if not e.undone_at)
    
    return GraceState(
        total_marks=total,
        entries=[
            GraceEntry(
                id=e.id,
                marks=e.marks,
                reason=e.reason,
                applied_at=e.applied_at.isoformat(),
                undone_at=e.undone_at.isoformat() if e.undone_at else None
            ) for e in entries
        ]
    )

def apply_grace_marks(session: Session, assessment_id: str, marks: float, reason: str) -> GraceState:
    entry = GraceAdjustment(
        id=f"gr_{uuid.uuid4().hex[:8]}",
        assessment_id=assessment_id,
        marks=marks,
        reason=reason,
        applied_at=datetime.now(UTC)
    )
    session.add(entry)
    session.commit()
    return get_grace_state(session, assessment_id)

def undo_grace_marks(session: Session, assessment_id: str, entry_id: str = None) -> GraceState:
    query = select(GraceAdjustment).where(GraceAdjustment.assessment_id == assessment_id).where(GraceAdjustment.undone_at.is_(None))
    if entry_id:
        query = query.where(GraceAdjustment.id == entry_id)
    else:
        query = query.order_by(GraceAdjustment.applied_at.desc())
        
    entry = session.exec(query).first()
    if entry:
        entry.undone_at = datetime.now(UTC)
        session.add(entry)
        session.commit()
        
    return get_grace_state(session, assessment_id)

def preview_grace_marks(session: Session, assessment_id: str, marks: float) -> GracePreview:
    # Need to get current stats vs proposed stats
    # To keep it simple, we use the scoring function
    from app.models.grading import VivaSession
    from app.services.scoring import compute_final_score
    
    assessment = session.get(Assessment, assessment_id)
    submissions = session.exec(select(Submission).where(Submission.assessment_id == assessment_id)).all()
    
    current_pcts = []
    after_pcts = []
    
    affected = 0
    capped = 0
    
    for sub in submissions:
        grade = session.exec(select(Grade).where(Grade.submission_id == sub.id)).first()
        if grade and grade.released_at:
            viva = session.exec(select(VivaSession).where(VivaSession.submission_id == sub.id)).first()
            
            curr = compute_final_score(assessment, grade, viva, session)
            current_pcts.append(curr.get("final_pct", 0))
            
            # Simulate new grace
            # In compute_final_score, grace is already applied based on DB, we need to add the new marks
            proposed_grace = curr.get("grace_marks", 0) + marks
            proposed_final = curr.get("final_marks", 0) + proposed_grace
            
            if proposed_final > assessment.max_marks:
                proposed_final = assessment.max_marks
                capped += 1
                
            affected += 1
            after_pct = (proposed_final / assessment.max_marks) * 100 if assessment.max_marks else 0
            after_pcts.append(after_pct)
            
    import statistics
    
    def m(pcts):
        if not pcts:
            return GraceMetrics(avg_pct=0, pass_rate_pct=0)
        avg = statistics.mean(pcts)
        pr = sum(1 for p in pcts if p >= assessment.pass_mark_pct) / len(pcts) * 100
        return GraceMetrics(avg_pct=avg, pass_rate_pct=pr)
        
    return GracePreview(
        marks=marks,
        affected_students=affected,
        capped_count=capped,
        before=m(current_pcts),
        after=m(after_pcts)
    )
