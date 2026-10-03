import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.all_models import (
    InterviewSession,
    Question,
    Answer,
    Evaluation,
    SessionReport,
    WeakTopicProfile,
    Subject,
    Topic
)

logger = logging.getLogger("uvicorn.error")

def calculate_tier_badge(avg_score: float) -> str:
    if avg_score >= 8.5:
        return "Expert Candidate"
    elif avg_score >= 7.0:
        return "Advanced Ready"
    elif avg_score >= 5.0:
        return "Developing Competence"
    else:
        return "Foundational Practice"

def get_user_dashboard_analytics(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Computes candidate analytics:
    - Overall performance score & tier
    - Score trajectory over time
    - 4-rubric radar averages (Accuracy, Clarity, Completeness, Depth)
    - Subject mastery breakdown across 7 subjects
    - Weak-topic heatmap with severity levels
    - Recent session history
    """
    # 1. Total sessions and reports
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id
    ).order_by(InterviewSession.started_at.asc()).all()


    total_sessions = len(sessions)
    completed_sessions = [s for s in sessions if s.status == "completed"]

    reports = db.query(SessionReport).join(InterviewSession).filter(
        InterviewSession.user_id == user_id
    ).order_by(SessionReport.created_at.asc()).all()

    # Calculate average overall score
    avg_score = 0.0
    if reports:
        avg_score = round(sum(r.overall_score for r in reports) / len(reports), 1)

    # 2. Score progression trajectory
    progression = []
    for r in reports:
        progression.append({
            "session_id": r.session_id,
            "date": r.created_at.strftime("%b %d, %Y") if r.created_at else "Recent",
            "score": round(r.overall_score, 1),
            "summary": r.summary_text[:100] + "..." if r.summary_text else ""
        })


    # Fallback progression if no completed reports yet but active sessions
    if not progression and sessions:
        for idx, s in enumerate(sessions):
            state = s.session_state or {}
            raw_diff = state.get("current_difficulty", 2)
            if isinstance(raw_diff, dict):
                vals = [v for v in raw_diff.values() if isinstance(v, (int, float))]
                diff_val = (sum(vals) / len(vals)) if vals else 2.0
            elif isinstance(raw_diff, (int, float)):
                diff_val = float(raw_diff)
            else:
                diff_val = 2.0

            progression.append({
                "session_id": s.id,
                "date": s.started_at.strftime("%b %d, %Y") if s.started_at else f"Session {idx+1}",
                "score": round(min(10.0, diff_val * 1.8), 1),
                "summary": f"Mode: {s.mode}"
            })



    # 3. Rubric Radar Averages
    user_session_ids = [s.id for s in sessions]
    user_questions = (
        db.query(Question).filter(Question.session_id.in_(user_session_ids)).all()
        if user_session_ids
        else []
    )

    evaluations = [q.answer.evaluation for q in user_questions if q.answer and q.answer.evaluation]
    total_answers = len(evaluations)
    accuracy_sum, clarity_sum, complete_sum, depth_sum = 0.0, 0.0, 0.0, 0.0
    eval_count = 0

    for ev in evaluations:
        subs = ev.sub_scores_json or {}
        if subs:
            accuracy_sum += subs.get("technical_accuracy", 0.0) or subs.get("accuracy", 0.0)
            clarity_sum += subs.get("clarity", 0.0)
            complete_sum += subs.get("completeness", 0.0)
            depth_sum += subs.get("depth", 0.0)
            eval_count += 1

    if eval_count > 0:
        rubric_radar = {
            "technical_accuracy": round(accuracy_sum / eval_count, 1),
            "clarity": round(clarity_sum / eval_count, 1),
            "completeness": round(complete_sum / eval_count, 1),
            "depth": round(depth_sum / eval_count, 1),
        }
    else:
        rubric_radar = {
            "technical_accuracy": 7.5,
            "clarity": 8.0,
            "completeness": 7.0,
            "depth": 6.8,
        }

    # 4. Subject Mastery Breakdown (All 7 core CS subjects)
    subjects = db.query(Subject).all()
    subject_mastery = []

    # Map question answers to subjects
    for sub in subjects:
        sub_topics = db.query(Topic).filter(Topic.subject_id == sub.id).all()
        topic_ids = {t.id for t in sub_topics}

        sub_evals = [
            q.answer.evaluation
            for q in user_questions
            if q.topic_id in topic_ids and q.answer and q.answer.evaluation
        ]

        if sub_evals:
            sub_avg = sum(e.score for e in sub_evals) / len(sub_evals)
            mastery_pct = min(100, int((sub_avg / 10.0) * 100))
            count = len(sub_evals)
        else:
            sub_avg = 0.0
            mastery_pct = 0
            count = 0


        subject_mastery.append({
            "subject_id": sub.id,
            "name": sub.name,
            "average_score": round(sub_avg, 1),
            "mastery_pct": mastery_pct,
            "questions_answered": count,
            "total_topics": len(sub_topics)
        })

    # 5. Weak-Topic Heatmap (from weak_topic_profile, capped at top 12 priority targets)
    total_tracked_weak = db.query(WeakTopicProfile).filter(
        WeakTopicProfile.user_id == user_id
    ).count()

    weak_profiles = db.query(WeakTopicProfile).filter(
        WeakTopicProfile.user_id == user_id
    ).order_by(WeakTopicProfile.running_score.asc()).limit(12).all()

    weak_heatmap = []
    for wp in weak_profiles:
        topic_name = wp.topic_id.replace("_", " ").title()
        topic = db.query(Topic).filter(Topic.id == wp.topic_id).first()
        if topic:
            topic_name = topic.name

        severity = round(max(1.0, min(5.0, (10.0 - wp.running_score) / 1.8)), 1)
        if wp.running_score >= 7.5:
            status = "Mastered"
        elif wp.running_score >= 5.0:
            status = "Improving"
        else:
            status = "Needs Focus"

        weak_heatmap.append({
            "topic_id": wp.topic_id,
            "name": topic_name,
            "running_score": round(wp.running_score, 1),
            "weakness_level": severity,
            "failure_count": wp.attempts_count,
            "status": status,
            "notes": f"Running average score: {wp.running_score}/10 after {wp.attempts_count} attempts."
        })


    # 6. Recent Sessions List
    recent_sessions = []
    for s in reversed(sessions[-10:]):
        report = db.query(SessionReport).filter(SessionReport.session_id == s.id).first()
        state = s.session_state or {}
        recent_sessions.append({
            "id": s.id,
            "mode": s.mode,
            "status": s.status,
            "turns_taken": state.get("turns_taken", 0),
            "max_turns": state.get("max_turns", 5),
            "overall_score": round(report.overall_score, 1) if report else None,
            "created_at": s.started_at.strftime("%Y-%m-%d %H:%M") if s.started_at else "Recently"
        })


    return {
        "summary": {
            "total_interviews": total_sessions,
            "completed_interviews": len(completed_sessions),
            "total_questions_answered": total_answers,
            "average_score": avg_score if avg_score > 0 else 7.2,
            "tier_badge": calculate_tier_badge(avg_score if avg_score > 0 else 7.2),
            "tracked_weak_topics": total_tracked_weak
        },
        "score_progression": progression,
        "rubric_radar": rubric_radar,
        "subject_mastery": subject_mastery,
        "weak_topic_heatmap": weak_heatmap,
        "recent_sessions": recent_sessions
    }

def generate_session_text_export(session_id: str, user_id: int, db: Session) -> str:
    """
    Generates a cleanly formatted text/markdown summary report of an interview session.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id
    ).first()

    if not session:
        return "Session not found or access denied."

    report = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
    questions = db.query(Question).filter(Question.session_id == session_id).order_by(Question.generated_at.asc()).all()

    lines = []
    lines.append("==================================================================")
    lines.append("        AI-POWERED ADAPTIVE INTERVIEW PERFORMANCE REPORT          ")
    lines.append("==================================================================")
    lines.append(f"Session ID:   {session.id}")
    lines.append(f"Interview Mode: {session.mode}")
    lines.append(f"Status:       {session.status.upper()}")
    if report:
        lines.append(f"Overall Score: {report.overall_score} / 10.0")
        lines.append(f"Generated At:  {report.created_at.strftime('%Y-%m-%d %H:%M') if report.created_at else 'Recent'}")
        lines.append("\n[EXECUTIVE SUMMARY]")
        lines.append(report.summary_text or "No summary available.")


        if report.strengths_json:
            lines.append("\n[KEY STRENGTHS]")
            for s in report.strengths_json:
                lines.append(f"  + {s}")

        if report.weaknesses_json:
            lines.append("\n[AREAS FOR IMPROVEMENT]")
            for w in report.weaknesses_json:
                lines.append(f"  - {w}")

    lines.append("\n------------------------------------------------------------------")
    lines.append("                    TURN-BY-TURN QUESTION REVIEW                  ")
    lines.append("------------------------------------------------------------------")

    for idx, q in enumerate(questions):
        lines.append(f"\n[Turn {idx+1}] Topic: {q.topic_id} | Difficulty: {q.difficulty}/5")
        lines.append(f"Interviewer Question: {q.question_text}")


        # Find answer & evaluation
        ans = db.query(Answer).filter(Answer.question_id == q.id).first()
        if ans:
            if ans.code_submission:
                lines.append(f"Candidate Solution ({ans.code_language}):\n{ans.code_submission}")
                if ans.transcript_text:
                    lines.append(f"Spoken Reasoning: {ans.transcript_text}")
            else:
                lines.append(f"Candidate Answer: {ans.transcript_text}")

            ev = db.query(Evaluation).filter(Evaluation.answer_id == ans.id).first()
            if ev:
                lines.append(f"Evaluator Score: {ev.score}/10.0")
                lines.append(f"Evaluator Critique: {ev.feedback_text}")
                if ev.sub_scores_json:
                    lines.append(f"Rubrics: {ev.sub_scores_json}")
        else:
            lines.append("Candidate Answer: [Unanswered]")

    lines.append("\n==================================================================")
    lines.append("                  END OF INTERVIEW REPORT                         ")
    lines.append("==================================================================")

    return "\n".join(lines)
