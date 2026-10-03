import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.models.all_models import (
    InterviewSession,
    Question,
    Answer,
    Evaluation,
    SessionReport,
    User,
    Resume,
    JobDescription,
    Topic
)
from backend.app.schemas.all_schemas import (
    SessionCreate,
    SessionOut,
    QuestionOut,
    AnswerSubmit,
    TurnResponse,
    EvaluationOut,
    SessionReportOut
)
from backend.app.api.deps import get_current_user
from backend.app.services.agent_orchestrator import (
    select_next_topic_and_difficulty,
    generate_blended_question,
    generate_resume_intro_question,
    evaluate_answer,
    critic_sanity_check,
    update_session_state_after_turn,
    generate_final_report
)
from backend.app.services.code_evaluator import evaluate_code_submission
from backend.app.services.code_runner_service import execute_code_safely, verify_pseudocode_logic

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


class SessionStartRequest(BaseModel):
    mode: str = Field(..., description="'JD' or 'SUBJECT'")
    resume_id: Optional[str] = None
    jd_id: Optional[str] = None
    subject_ids: Optional[List[str]] = ["dsa", "os"]
    max_turns: int = Field(default=5, ge=1, le=10)

@router.post("/start", response_model=SessionOut)
async def start_interview_session(
    req: SessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plan_remaining = []

    # Mode A: Targeted Role Mock
    if req.mode.upper() == "JD":
        if req.resume_id:
            resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
        else:
            resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.uploaded_at.desc()).first()

        if req.jd_id:
            jd = db.query(JobDescription).filter(JobDescription.id == req.jd_id).first()
        else:
            jd = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).first()

        # If resume & JD available, pull target topics from gap analysis or CS mapping
        if jd and jd.parsed_json:
            core_subjects = jd.parsed_json.get("core_cs_subjects", ["DSA", "DBMS"])
            # Map subjects to topic IDs
            for s in core_subjects:
                s_clean = s.lower().replace(" ", "_")
                topics = db.query(Topic).filter(Topic.subject_id == s_clean).all()
                plan_remaining.extend([t.id for t in topics[:2]])

        if not plan_remaining:
            plan_remaining = ["dsa_arrays_strings", "os_deadlocks", "dbms_indexing", "cn_sockets_transport"]

        mode_subject_ids = req.subject_ids or ["dsa", "os", "dbms"]
    else:
        # Mode B: Multi-Subject or Single Subject Mode
        mode_subject_ids = req.subject_ids or ["dsa", "os"]
        topics_by_sub = {}
        for sub_id in mode_subject_ids:
            sub_tops = db.query(Topic).filter(Topic.subject_id == sub_id).all()
            topics_by_sub[sub_id] = [t.id for t in sub_tops]

        plan_remaining = []
        # If hr_behavioral is selected, ensure hr_intro_vision is placed first
        if "hr_behavioral" in mode_subject_ids and "hr_behavioral" in topics_by_sub:
            if "hr_intro_vision" in topics_by_sub["hr_behavioral"]:
                plan_remaining.append("hr_intro_vision")
                topics_by_sub["hr_behavioral"].remove("hr_intro_vision")

        max_len = max((len(v) for v in topics_by_sub.values()), default=0)
        for i in range(max_len):
            for sub_id in mode_subject_ids:
                if i < len(topics_by_sub[sub_id]):
                    plan_remaining.append(topics_by_sub[sub_id][i])

        if not plan_remaining:
            plan_remaining = ["dsa_basic_math_logic", "dsa_arrays_strings", "os_deadlocks", "dbms_normalization"]


    # 1. Initialize Explicit State Object per Section 4
    initial_state = {
        "mode": req.mode.upper(),
        "covered_topics": [],
        "topic_scores": {},
        "current_difficulty": {},
        "turns_taken": 0,
        "max_turns": req.max_turns,
        "plan_remaining": plan_remaining,
        "last_turn_score": None
    }

    session = InterviewSession(
        user_id=current_user.id,
        mode=req.mode.upper(),
        resume_id=req.resume_id,
        jd_id=req.jd_id,
        subject_ids=mode_subject_ids,
        session_state=initial_state,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 2. Planner & Generator: Determine first question
    if req.mode.upper() == "JD":
        # Realistic Full Technical Interview: Turn 1 is Introduction & Project Deep-Dive
        intro_topic = db.query(Topic).filter(Topic.id == "hr_intro_vision").first()
        topic_id = intro_topic.id if intro_topic else "hr_intro_vision"
        difficulty = 2
        question_type = "conceptual"
        question_text, source_mix = await generate_resume_intro_question(resume, jd)
    else:
        # Mode B: Follow selected syllabus topic
        topic_id, difficulty, question_type = select_next_topic_and_difficulty(db, session)
        question_text, source_mix = await generate_blended_question(db, session, topic_id, difficulty, question_type)

    # Save first question
    first_q = Question(
        session_id=session.id,
        topic_id=topic_id,
        difficulty=difficulty,
        question_type=question_type,
        question_text=question_text,
        source_mix=source_mix
    )
    db.add(first_q)
    db.commit()
    db.refresh(first_q)

    # Build response
    q_out = QuestionOut(
        id=first_q.id,
        session_id=session.id,
        topic_id=first_q.topic_id,
        difficulty=first_q.difficulty,
        question_type=first_q.question_type,
        question_text=first_q.question_text,
        source_mix=first_q.source_mix,
        audio_url=first_q.audio_url
    )

    return SessionOut(
        id=session.id,
        user_id=session.user_id,
        mode=session.mode,
        subject_ids=session.subject_ids or [],
        status=session.status,
        started_at=session.started_at,
        current_question=q_out
    )

@router.post("/{session_id}/answer", response_model=TurnResponse)
async def submit_session_answer(
    session_id: str,
    answer_in: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="This interview session has already concluded.")

    # Find the current pending question (the latest question without an answer)
    last_question = (
        db.query(Question)
        .filter(Question.session_id == session.id)
        .order_by(Question.generated_at.desc())
        .first()
    )
    if not last_question:
        raise HTTPException(status_code=400, detail="No active question found in session")

    # 1. Record Answer
    candidate_answer_text = answer_in.transcript_text or answer_in.code_submission or ""
    answer_record = Answer(
        question_id=last_question.id,
        transcript_text=candidate_answer_text,
        code_submission=answer_in.code_submission,
        code_language=answer_in.code_language,
        answer_mode=answer_in.answer_mode,
        audio_url=answer_in.audio_url
    )
    db.add(answer_record)
    db.commit()
    db.refresh(answer_record)

    # 2. Evaluator: Score and critique (Branch based on question_type)
    topic = db.query(Topic).filter(Topic.id == last_question.topic_id).first()
    topic_name = topic.name if topic else (last_question.topic_id or "General")

    has_code_submission = bool(answer_in.code_submission and len(answer_in.code_submission.strip()) >= 5)
    is_coding = (
        last_question.question_type == "coding" and
        has_code_submission and
        answer_in.answer_mode != "conceptual"
    )

    if is_coding:
        candidate_code = answer_in.code_submission or ""
        eval_result = await evaluate_code_submission(
            question_text=last_question.question_text,
            topic_name=topic_name,
            difficulty=last_question.difficulty,
            code_submission=candidate_code,
            code_language=answer_in.code_language or "python",
            answer_mode=answer_in.answer_mode or "full_code",
            spoken_narration=answer_in.transcript_text or None
        )
        evaluator_version = "groq-code-evaluator-v1"
    else:
        eval_result = await evaluate_answer(
            question_text=last_question.question_text,
            topic_name=topic_name,
            difficulty=last_question.difficulty,
            candidate_answer=candidate_answer_text
        )
        evaluator_version = "groq-llama-evaluator-v1"

    # 3. Critic: Sanity-check score vs context
    raw_score = float(eval_result.get("score", 5.0))
    sanitized_score = critic_sanity_check(raw_score, candidate_answer_text, eval_result.get("sub_scores", {}))

    eval_record = Evaluation(
        answer_id=answer_record.id,
        score=sanitized_score,
        sub_scores_json=eval_result.get("sub_scores", {}),
        feedback_text=eval_result.get("feedback", "Answer evaluated."),
        evaluator_model_version=evaluator_version
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)

    # 4. State Update: Track performance in persistent state
    update_session_state_after_turn(session, last_question.topic_id or "general", sanitized_score)
    db.commit()

    # 5. Decide Next Action (End condition or next turn)
    answers_count = db.query(Answer).join(Question).filter(Question.session_id == session.id).count()
    state = session.session_state or {}
    max_turns = state.get("max_turns", 5)

    is_completed = answers_count >= max_turns
    next_question_out = None

    if is_completed:
        # Trigger Final Session Report
        await generate_final_report(db, session)
    else:
        # Plan & Generate next question
        next_topic_id, next_diff, next_q_type = select_next_topic_and_difficulty(db, session)
        next_q_text, next_source_mix = await generate_blended_question(db, session, next_topic_id, next_diff, next_q_type)

        next_q = Question(
            session_id=session.id,
            topic_id=next_topic_id,
            difficulty=next_diff,
            question_type=next_q_type,
            question_text=next_q_text,
            source_mix=next_source_mix
        )
        db.add(next_q)
        db.commit()
        db.refresh(next_q)

        next_question_out = QuestionOut(
            id=next_q.id,
            session_id=session.id,
            topic_id=next_q.topic_id,
            difficulty=next_q.difficulty,
            question_type=next_q.question_type,
            question_text=next_q.question_text,
            source_mix=next_q.source_mix,
            audio_url=next_q.audio_url
        )

    eval_out = EvaluationOut(
        score=eval_record.score,
        feedback_text=eval_record.feedback_text,
        sub_scores_json=eval_record.sub_scores_json or {},
        evaluator_model_version=eval_record.evaluator_model_version
    )

    return TurnResponse(
        evaluation=eval_out,
        next_question=next_question_out,
        is_completed=is_completed,
        session_id=session.id
    )

@router.get("/{session_id}/report", response_model=SessionReportOut)
def get_session_report(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Session report not found. The session may still be in progress.")
    return report

@router.get("/{session_id}/current-question", response_model=QuestionOut)
def get_current_question(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    last_question = (
        db.query(Question)
        .filter(Question.session_id == session.id)
        .order_by(Question.generated_at.desc())
        .first()
    )
    if not last_question:
        raise HTTPException(status_code=404, detail="No questions generated for this session yet")

    return QuestionOut(
        id=last_question.id,
        session_id=last_question.session_id,
        topic_id=last_question.topic_id,
        difficulty=last_question.difficulty,
        question_type=last_question.question_type,
        question_text=last_question.question_text,
        source_mix=last_question.source_mix,
        audio_url=last_question.audio_url
    )

@router.get("/{session_id}/state")
def get_session_state(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.id,
        "mode": session.mode,
        "status": session.status,
        "state": session.session_state
    }

class CodeRunRequest(BaseModel):
    code_content: str
    code_language: str = "python"
    stdin_input: Optional[str] = None
    answer_mode: Optional[str] = "full_code"
    question_text: Optional[str] = None
    topic_name: Optional[str] = None

@router.post("/run-code")
async def run_code_sandbox(
    req: CodeRunRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Executes candidate code in an isolated local execution sandbox,
    or verifies algorithmic logic & dry-run trace if in pseudocode mode.
    """
    is_pseudocode = (
        req.answer_mode == "pseudocode" or
        req.code_language.lower() in ["pseudocode", "pseudo"]
    )
    if is_pseudocode:
        return await verify_pseudocode_logic(
            pseudocode=req.code_content,
            question_text=req.question_text or "",
            topic_name=req.topic_name or ""
        )

    result = execute_code_safely(
        code_content=req.code_content,
        language=req.code_language,
        stdin_input=req.stdin_input
    )
    return result

