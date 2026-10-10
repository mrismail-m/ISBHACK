
from app.models.core import Assessment
from app.models.grading import Grade, VivaSession
from app.schemas.activity import ActivitySummary


def compute_flags(
    assessment: Assessment,
    grade: Grade | None,
    viva: VivaSession | None,
    activity_summary: ActivitySummary | None
) -> list[str]:
    flags = set()
    
    if grade:
        if grade.overall_confidence < 0.6:
            flags.add("low_confidence")
            
        for crit in grade.criteria:
            evidence = crit.get("evidence", [])
            if not evidence or all(not e.get("verified", False) for e in evidence):
                flags.add("evidence_unverified")
                break
                
        # Forward grader flags directly
        if "injection_attempt" in grade.grader_flags:
            flags.add("injection_attempt")
        if "needs_manual_grading" in grade.grader_flags:
            flags.add("needs_manual_grading")
            
    viva_done = viva is not None and viva.status == "done"
    
    if viva_done and viva.understanding is not None and viva.understanding < 0.4:
        flags.add("weak_viva")
        
    if assessment.viva_enabled and not viva_done and grade and grade.status == "approved":
        flags.add("viva_skipped")
        
    if activity_summary:
        if activity_summary.pasted_pct >= 40:
            flags.add("paste_heavy")
        elif activity_summary.paste_chunks:
            for chunk in activity_summary.paste_chunks:
                if chunk.major and chunk.survived_pct >= 50:
                    flags.add("paste_heavy")
                    break
                    
    return list(flags)
