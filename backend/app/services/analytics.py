import statistics

from sqlmodel import Session, select

from app.models.core import Assessment, Submission, User
from app.models.grading import Grade, VivaSession
from app.schemas.analytics import (
    AssessmentPerformance,
    AssessmentStats,
    AttentionStudent,
    ClassPerformance,
    CriterionAverage,
    CriterionOverride,
    HistogramBin,
    OverrideStats,
    StudentPerformance,
    TopicAverage,
)
from app.services.scoring import compute_final_score


def get_assessment_stats(session: Session, assessment_id: str) -> AssessmentStats:
    assessment = session.get(Assessment, assessment_id)
    enrolled = session.exec(select(User).where(User.role == "student").where(User.classroom_id == assessment.classroom_id)).all()
    submissions = session.exec(select(Submission).where(Submission.assessment_id == assessment_id)).all()
    
    enrolled_count = len(enrolled)
    submitted_count = len(submissions)
    
    grades = []
    approved_count = 0
    released_count = 0
    
    final_pcts = []
    
    topic_marks = {}
    topic_counts = {}
    criterion_marks = {}
    criterion_counts = {}
    
    for sub in submissions:
        grade = session.exec(select(Grade).where(Grade.submission_id == sub.id)).first()
        if grade:
            grades.append(grade)
            if grade.status == "approved":
                approved_count += 1
            if grade.released_at:
                released_count += 1
                
            viva = session.exec(select(VivaSession).where(VivaSession.submission_id == sub.id)).first()
            score_dict = compute_final_score(assessment, grade, viva, session)
            
            if score_dict.get("final_pct") is not None:
                final_pcts.append(score_dict["final_pct"])
                
            for c in grade.criteria:
                cid = c["criterion_id"]
                c_mark = c.get("final_marks", c.get("ai_marks", 0))
                # Need to find max marks for criterion and topic
                topic = "general"
                c_max = c.get("max_marks", assessment.max_marks / len(grade.criteria))
                if assessment.rubric and "criteria" in assessment.rubric:
                    for rc in assessment.rubric["criteria"]:
                        if rc["id"] == cid:
                            topic = rc.get("topic", "general")
                            c_max = rc.get("max_marks", c_max)
                            criterion_marks.setdefault(cid, {"name": rc["name"], "total_pct": 0, "count": 0})
                            break
                            
                if c_max > 0:
                    pct = (c_mark / c_max) * 100
                    topic_marks[topic] = topic_marks.get(topic, 0) + pct
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    
                    if cid in criterion_marks:
                        criterion_marks[cid]["total_pct"] += pct
                        criterion_marks[cid]["count"] += 1

    graded_count = len(grades)
    pending_review = graded_count - approved_count
    
    final = (submitted_count > 0 and approved_count == submitted_count)
    
    avg_pct = statistics.mean(final_pcts) if final_pcts else None
    median_pct = statistics.median(final_pcts) if final_pcts else None
    highest_pct = max(final_pcts) if final_pcts else None
    lowest_pct = min(final_pcts) if final_pcts else None
    pass_rate_pct = (sum(1 for p in final_pcts if p >= assessment.pass_mark_pct) / len(final_pcts)) * 100 if final_pcts else None

    # Histogram 10 bins
    bins = [0] * 10
    for p in final_pcts:
        idx = min(9, int(p // 10))
        bins[idx] += 1
        
    histogram = []
    for i in range(10):
        start = i * 10
        end = start + 9 if i < 9 else 100
        histogram.append(HistogramBin(bin=f"{start}-{end}", count=bins[i]))
        
    topic_averages = [
        TopicAverage(topic=t, avg_pct=topic_marks[t] / topic_counts[t], n=len(final_pcts))
        for t in topic_marks
    ]
    
    criterion_averages = [
        CriterionAverage(criterion_id=cid, name=data["name"], avg_pct=data["total_pct"] / data["count"])
        for cid, data in criterion_marks.items() if data["count"] > 0
    ]
    
    return AssessmentStats(
        assessment_id=assessment_id,
        enrolled=enrolled_count,
        submitted=submitted_count,
        graded=graded_count,
        approved=approved_count,
        released=released_count,
        pending_review=pending_review,
        final=final,
        avg_pct=avg_pct,
        median_pct=median_pct,
        pass_rate_pct=pass_rate_pct,
        highest_pct=highest_pct,
        lowest_pct=lowest_pct,
        histogram=histogram,
        topic_averages=topic_averages,
        criterion_averages=criterion_averages,
        grace_marks_applied=0 # We can calculate this from grace marks entries later
    )

def get_override_stats(session: Session, assessment_id: str) -> OverrideStats:
    submissions = session.exec(select(Submission).where(Submission.assessment_id == assessment_id)).all()
    
    graded = 0
    overridden = 0
    abs_deltas = []
    signed_deltas = []
    
    crit_stats = {}
    
    for sub in submissions:
        grade = session.exec(select(Grade).where(Grade.submission_id == sub.id)).first()
        if grade:
            graded += 1
            has_override = False
            for c in grade.criteria:
                cid = c["criterion_id"]
                ai_m = c.get("ai_marks", 0)
                fi_m = c.get("final_marks", ai_m)
                
                if cid not in crit_stats:
                    crit_stats[cid] = {"total": 0, "overridden": 0, "signed_deltas": []}
                crit_stats[cid]["total"] += 1
                
                if ai_m != fi_m:
                    has_override = True
                    delta = fi_m - ai_m
                    abs_deltas.append(abs(delta))
                    signed_deltas.append(delta)
                    crit_stats[cid]["overridden"] += 1
                    crit_stats[cid]["signed_deltas"].append(delta)
                    
            if has_override:
                overridden += 1
                
    by_criterion = []
    for cid, data in crit_stats.items():
        if data["total"] > 0 and data["overridden"] > 0:
            by_criterion.append(CriterionOverride(
                criterion_id=cid,
                override_rate_pct=(data["overridden"] / data["total"]) * 100,
                mean_signed_delta_marks=statistics.mean(data["signed_deltas"])
            ))

    return OverrideStats(
        graded=graded,
        overridden=overridden,
        override_rate_pct=(overridden / graded * 100) if graded > 0 else 0,
        mean_abs_delta_marks=statistics.mean(abs_deltas) if abs_deltas else 0.0,
        mean_signed_delta_marks=statistics.mean(signed_deltas) if signed_deltas else 0.0,
        by_criterion=by_criterion
    )

def get_class_performance(session: Session, classroom_id: str) -> ClassPerformance:
    assessments = session.exec(select(Assessment).where(Assessment.classroom_id == classroom_id).order_by(Assessment.created_at)).all()
    students = session.exec(select(User).where(User.role == "student").where(User.classroom_id == classroom_id)).all()
    
    ap_list = []
    student_scores = {s.id: {"name": s.name, "scores": []} for s in students}
    
    for a in assessments:
        stats = get_assessment_stats(session, a.id)
        ap_list.append(AssessmentPerformance(
            assessment_id=a.id,
            title=a.title,
            kind=a.kind,
            due_at=a.due_at.isoformat() if a.due_at else "",
            avg_pct=stats.avg_pct,
            pass_rate_pct=stats.pass_rate_pct
        ))
        
        subs = session.exec(select(Submission).where(Submission.assessment_id == a.id)).all()
        sub_dict = {s.student_id: s for s in subs}
        
        for s in students:
            sub = sub_dict.get(s.id)
            score = 0.0
            if sub:
                grade = session.exec(select(Grade).where(Grade.submission_id == sub.id)).first()
                if grade and grade.released_at:
                    viva = session.exec(select(VivaSession).where(VivaSession.submission_id == sub.id)).first()
                    score_dict = compute_final_score(a, grade, viva, session)
                    score = score_dict.get("final_pct", 0.0)
            student_scores[s.id]["scores"].append(score)
            
    sp_list = [StudentPerformance(student_id=sid, name=data["name"], scores_pct=data["scores"]) for sid, data in student_scores.items()]
    
    return ClassPerformance(
        classroom_id=classroom_id,
        assessments=ap_list,
        students=sp_list
    )

def get_attention(session: Session, classroom_id: str) -> list[AttentionStudent]:
    perf = get_class_performance(session, classroom_id)
    attention = []
    
    for sp in perf.students:
        reasons = []
        if not sp.scores_pct:
            continue
            
        recent = sp.scores_pct[-3:] if len(sp.scores_pct) >= 3 else sp.scores_pct
        
        # Check pass rate
        # assuming pass is 50 for now, ideally check each assessment
        if recent and recent[-1] < 50:
            reasons.append("below_pass_recent")
            
        if len(recent) >= 2 and recent[-1] < recent[-2] - 10:
            reasons.append("falling_trend")
            
        if reasons:
            attention.append(AttentionStudent(
                student_id=sp.student_id,
                name=sp.name,
                reasons=reasons,
                recent_scores_pct=recent,
                last_understanding=None # Would need to pull latest viva
            ))
            
    return attention
