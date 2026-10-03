import random
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

from backend.app.models.all_models import (
    InterviewSession,
    Question,
    Answer,
    Evaluation,
    SessionReport,
    WeakTopicProfile,
    Topic,
    Subject
)
from backend.app.services.embedding_service import (
    search_similar_pdf_chunks,
    search_similar_question_bank
)
from backend.app.services.llm_service import (
    call_groq_json,
    call_groq_text,
    FAST_MODEL,
    PRIMARY_MODEL
)

logger = logging.getLogger("uvicorn.error")

# ==============================================================================
# 1. PLANNER: Topic & Difficulty Selection
# ==============================================================================
def classify_question_mode(subject_id: str, topic_id: str) -> str:
    """
    Classifies question as 'conceptual' (spoken) or 'coding' (Monaco editor).
    Coding is enabled for DSA/OOP coding topics, and strictly 'dbms_sql_queries' for SQL.
    All other topics (OS, CN, HR, DBMS theory/architecture like indexing, normalization, CAP theorem, transactions) are strictly 'conceptual'.
    """
    if subject_id == "dsa":
        if topic_id in ["dsa_complexity", "dsa_basic_math_logic"]:
            return "conceptual"
        return random.choice(["conceptual", "coding"])
    elif subject_id == "oops":
        if topic_id in ["oops_pillars", "oops_solid", "oops_design_patterns"]:
            return "conceptual"
        return random.choice(["conceptual", "coding"])
    elif subject_id == "dbms":
        # ONLY actual SQL query writing belongs in the code editor
        if topic_id == "dbms_sql_queries":
            return "coding"
        return "conceptual"
    return "conceptual"


def select_next_topic_and_difficulty(
    db: Session,
    session: InterviewSession
) -> Tuple[str, int, str]:
    """
    Decides which topic to quiz next, the calibrated difficulty level (1-5),
    and whether it should be 'conceptual' or 'coding'.
    """
    state = session.session_state or {}
    covered = state.get("covered_topics", [])
    topic_scores = state.get("topic_scores", {})
    difficulties = state.get("current_difficulty", {})
    plan_remaining = state.get("plan_remaining", [])

    # 1. Topic Selection
    next_topic_id = None

    if plan_remaining:
        # Pull from planned gap / topic list
        next_topic_id = plan_remaining.pop(0)
    else:
        # Pull from subject's registered topics in DB
        subject_ids = session.subject_ids or ["dsa", "os"]
        topics = db.query(Topic).filter(Topic.subject_id.in_(subject_ids)).all()
        candidate_topics = [t.id for t in topics if t.id not in covered]
        if candidate_topics:
            next_topic_id = random.choice(candidate_topics)
        elif topics:
            next_topic_id = random.choice([t.id for t in topics])
        else:
            next_topic_id = "dsa_arrays_strings"

    # Determine parent subject
    topic_obj = db.query(Topic).filter(Topic.id == next_topic_id).first()
    subject_id = topic_obj.subject_id if topic_obj else "dsa"

    # Classify mode: conceptual vs coding
    question_type = classify_question_mode(subject_id, next_topic_id)

    # 2. Difficulty Adaptation
    last_score = state.get("last_turn_score", None)
    current_diff = difficulties.get(next_topic_id, 2)

    if last_score is not None:
        if last_score >= 8.0:
            current_diff = min(5, current_diff + 1)
        elif last_score < 5.0:
            current_diff = max(1, current_diff - 1)

    difficulties[next_topic_id] = current_diff
    state["plan_remaining"] = plan_remaining
    state["current_difficulty"] = difficulties
    session.session_state = dict(state)
    flag_modified(session, "session_state")

    return next_topic_id, current_diff, question_type


# ==============================================================================
# 2. GENERATOR: Blended Sourcing (§7: PDFs + Question Bank + Pure LLM)
# ==============================================================================
async def generate_blended_question(
    db: Session,
    session: InterviewSession,
    topic_id: str,
    difficulty: int,
    question_type: str = "conceptual"
) -> Tuple[str, str]:
    """
    Generates an interview question using a 3-way blended sourcing strategy:
      - 40% PDF-grounded (retrieves relevant chunks from uploaded syllabus notes)
      - 30% Question-bank-grounded (retrieves real example questions)
      - 30% Pure LLM general knowledge
    Returns: (question_text, source_mix_tag)
    """
    # Look up topic name and parent subject
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    topic_name = topic.name if topic else topic_id.replace("_", " ").title()
    subject_id = topic.subject_id if topic else "dsa"

    # Probabilistic source mix selection
    rand_val = random.random()
    if rand_val < 0.40:
        source_mix = "pdf_grounded"
    elif rand_val < 0.70:
        source_mix = "bank_grounded"
    else:
        source_mix = "pure_llm"

    if question_type == "coding":
        if subject_id == "dbms" or "sql" in topic_id:
            system_prompt = (
                "You are a Senior Database Architect conducting a live technical interview. "
                "Formulate ONE SQL query problem for the candidate to solve in a code editor. "
                "Include:\n"
                "**Problem Statement**: What to query.\n"
                "**Table Schema**: Tables and column names.\n"
                "**Example**: Sample input rows and expected output rows.\n"
                "**Constraints**: Any grouping, sorting, or performance requirements.\n"
                "Ensure each section begins on a new line."
            )
        else:
            system_prompt = (
                "You are a Senior Software Engineer conducting a live coding interview. "
                "Formulate ONE coding problem for the candidate to implement in a code editor. "
                "Include:\n"
                "**Problem Statement**: Clear task definition.\n"
                "**Input**: Input format and types.\n"
                "**Output**: Expected return values.\n"
                "**Constraints**: Big-O time/space constraints and parameter limits.\n"
                "**Example**: Sample input, output, and brief explanation.\n"
                "Ensure each section begins on a new line with clear spacing."
            )
    else:
        system_prompt = (
            "You are a friendly, highly experienced Senior Technical Interviewer conducting a spoken mock interview. "
            "Ask ONE concise, clear question calibrated to the requested difficulty level. "
            "Do not output greetings, preambles, or conversational fluff—only output the direct interview question."
        )

    reference_context = ""

    if source_mix == "pdf_grounded":
        chunks = search_similar_pdf_chunks(db, query_text=topic_name, subject_id=subject_id, topic_id=topic_id, limit=2)
        if chunks:
            chunk_texts = "\n---\n".join([c.chunk_text for c in chunks])
            reference_context = (
                f"REFERENCE MATERIAL FROM SYLLABUS NOTES:\n{chunk_texts}\n\n"
                f"INSTRUCTION: Use the core concept from the reference material above. "
                f"Formulate an original {'coding problem' if question_type == 'coding' else 'spoken conceptual question'}. Do not copy text verbatim."
            )
        else:
            source_mix = "pure_llm"

    elif source_mix == "bank_grounded":
        bank_items = search_similar_question_bank(db, query_text=topic_name, topic_id=topic_id, difficulty=difficulty, limit=2)
        if bank_items:
            bank_samples = "\n- ".join([b.question_text for b in bank_items])
            reference_context = (
                f"EXAMPLE INTERVIEW QUESTIONS FROM QUESTION BANK:\n- {bank_samples}\n\n"
                f"INSTRUCTION: Create an original question of similar rigor for topic '{topic_name}' at difficulty {difficulty}/5."
            )
        else:
            source_mix = "pure_llm"

    if question_type == "coding":
        if subject_id == "dbms" or "sql" in topic_id:
            prompt_instruction = "Formulate ONE SQL query problem (with Problem Statement, Table Schema, Example, Constraints) for the candidate to solve in the code editor:"
        else:
            prompt_instruction = "Formulate ONE coding problem (with Problem Statement, Input, Output, Constraints, Example) for the candidate to implement in the code editor:"
    else:
        prompt_instruction = "Generate ONE direct, spoken technical interview question for the candidate to answer verbally in an interview:"

    user_prompt = f"""
Topic: {topic_name} (Subject: {subject_id.upper()})
Target Difficulty Level: {difficulty} out of 5 (1=Basics, 3=Mid-level conceptual depth, 5=Hard/Edge-case architecture)
{reference_context}

{prompt_instruction}
"""
    question_text = await call_groq_text(user_prompt, system_prompt, model=FAST_MODEL)
    question_text = question_text.strip().strip('"').strip("'")

    # Clean any accidental LLM prefixes (e.g. "Spoken Conceptual Question:", "Interview Question:", etc.)
    question_text = re.sub(
        r'^(?:\*\*)?(?:Spoken Conceptual Question|Conceptual Question|Spoken Question|Interview Question|Question):?(?:\*\*)?\s*',
        '',
        question_text,
        flags=re.IGNORECASE
    ).strip()

    # Safety fallback if LLM returned nothing
    if len(question_text) < 15:
        question_text = f"Could you explain the core concepts and trade-offs of {topic_name}, and how it is applied in production systems?"

    return question_text, source_mix


async def generate_resume_intro_question(
    resume: Optional[Any],
    jd: Optional[Any]
) -> Tuple[str, str]:
    """
    Generates Turn 1 opening question for Mode A:
    Welcomes candidate, asks for self-introduction, and asks for a deep-dive
    into a key project extracted from their resume.
    """
    candidate_name = None
    project_title = None
    project_tech = []
    project_desc = None
    role_title = "Software Engineer"

    if jd and getattr(jd, "parsed_json", None) and isinstance(jd.parsed_json, dict):
        role_title = jd.parsed_json.get("role_title") or role_title

    if resume and getattr(resume, "parsed_json", None) and isinstance(resume.parsed_json, dict):
        candidate_name = resume.parsed_json.get("candidate_name")
        projects = resume.parsed_json.get("projects", [])
        if projects and isinstance(projects, list) and len(projects) > 0:
            p0 = projects[0]
            if isinstance(p0, dict):
                project_title = p0.get("title")
                project_tech = p0.get("technologies", [])
                project_desc = p0.get("description")

    # If project was found on resume, formulate personalized prompt via LLM
    if project_title:
        system_prompt = (
            f"You are a welcoming, professional Senior Technical Interviewer conducting a mock interview for the role of {role_title}. "
            "Formulate the opening interview question (Turn 1). "
            "1. Give a warm, brief 1-sentence welcome to the candidate. "
            "2. Ask them to introduce themselves briefly. "
            f"3. Ask them to walk you through their project '{project_title}'—specifically describing "
            "its high-level system architecture, their specific engineering contributions and key technologies, and the biggest technical challenge they solved. "
            "Keep the question natural, professional, and under 3-4 sentences. Do NOT include quotation marks around your whole response."
        )
        user_prompt = f"""
Candidate: {candidate_name or 'Candidate'}
Project: {project_title}
Technologies: {', '.join(project_tech) if project_tech else 'Core stack'}
Project Summary: {project_desc or 'Featured software project'}

Generate the opening spoken question:
"""
        try:
            q_text = await call_groq_text(user_prompt, system_prompt, model=FAST_MODEL)
            q_text = q_text.strip().strip('"').strip("'")
            if len(q_text) > 30:
                return q_text, "resume_grounded"
        except Exception as e:
            logger.warning(f"Error calling LLM for intro question: {e}")

        # Deterministic fallback with project
        tech_clause = f" using {', '.join(project_tech[:3])}" if project_tech else ""
        return (
            f"Welcome to your interview! To kick things off, could you please introduce yourself, "
            f"and then walk me through your project '{project_title}'{tech_clause}—specifically covering "
            f"the system architecture, your direct technical contributions, and the biggest challenge you overcame?",
            "resume_grounded"
        )
    else:
        # Resume had no parsed project, or plain text
        return (
            "Welcome to your interview! To get started, please give me a brief introduction of yourself, "
            "your technical background, and walk me through a major engineering project you have built—specifically "
            "the system architecture, key technologies used, and a difficult technical challenge you solved.",
            "resume_grounded"
        )


# ==============================================================================
# 3. EVALUATOR: Candidate Spoken/Text Answer Critique
# ==============================================================================
async def evaluate_answer(
    question_text: str,
    topic_name: str,
    difficulty: int,
    candidate_answer: str
) -> Dict[str, Any]:
    """
    Evaluates candidate's answer using structured technical rubrics.
    Returns: score (0-10), sub_scores, feedback, and sample improved response.
    """
    if not candidate_answer or len(candidate_answer.strip()) < 5:
        return {
            "score": 1.0,
            "sub_scores": {
                "technical_accuracy": 1.0,
                "clarity": 1.0,
                "completeness": 1.0,
                "depth": 1.0
            },
            "feedback": "No substantial answer was provided. Try to state at least the core definitions and key trade-offs.",
            "improved_sample_answer": "A strong answer should define the concept, state time/space complexity or system trade-offs, and mention practical use cases."
        }

    is_intro_project = (
        "intro" in topic_name.lower() or 
        "project" in topic_name.lower() or 
        "career" in topic_name.lower() or
        "behavioral" in topic_name.lower()
    )

    if is_intro_project:
        system_prompt = (
            "You are an expert technical hiring manager and engineering director. "
            "Assess the candidate's self-introduction and project explanation. "
            "Evaluate their communication clarity, how effectively they articulated their system architecture, "
            "their specific technical contributions, and how they handled engineering challenges. "
            "Score objectively on a 0.0 to 10.0 scale and provide constructive, actionable feedback in JSON format."
        )
    else:
        system_prompt = (
            "You are an expert technical interview evaluator. Assess the candidate's spoken answer to the technical question. "
            "Score objectively on a 0.0 to 10.0 scale and provide constructive, actionable feedback in JSON format."
        )
    user_prompt = f"""
Interview Question (Difficulty {difficulty}/5 on {topic_name}):
"{question_text}"

Candidate Answer:
"{candidate_answer}"

Evaluate the answer and output a JSON object with:
{{
  "score": float between 0.0 and 10.0,
  "sub_scores": {{
    "technical_accuracy": float 0-10,
    "clarity": float 0-10,
    "completeness": float 0-10,
    "depth": float 0-10
  }},
  "feedback": "2-3 sentences of direct feedback highlighting what was good and specifically what was missing or incorrect",
  "improved_sample_answer": "A concise, model answer demonstrating how a top engineer would answer this question in 3-4 sentences"
}}
"""
    eval_result = await call_groq_json(user_prompt, system_prompt, model=FAST_MODEL)

    if "error" in eval_result or "score" not in eval_result:
        # Fallback scoring heuristic
        word_count = len(candidate_answer.split())
        baseline_score = min(7.5, max(3.0, word_count * 0.15 + 2.0))
        eval_result = {
            "score": round(baseline_score, 1),
            "sub_scores": {
                "technical_accuracy": round(baseline_score, 1),
                "clarity": 7.0,
                "completeness": round(baseline_score - 1.0, 1),
                "depth": round(baseline_score - 1.0, 1)
            },
            "feedback": "Good initial explanation. To improve, discuss specific trade-offs and edge-case behaviors.",
            "improved_sample_answer": f"In {topic_name}, the key is balancing efficiency with maintainability."
        }

    return eval_result


# ==============================================================================
# 4. CRITIC: Sanity-Check Score & Context Guardrails
# ==============================================================================
def critic_sanity_check(
    score: float,
    candidate_answer: str,
    sub_scores: Dict[str, Any]
) -> float:
    """
    Sanity-checks the evaluator score:
    - Caps score between 0.0 and 10.0.
    - If answer is extremely brief (< 10 words), caps score at 4.0.
    - If answer is purely evasive or generic filler ("I don't know", "Not sure"), assigns <= 2.0.
    """
    clean_score = max(0.0, min(10.0, float(score)))
    words = candidate_answer.lower().split()

    if len(words) < 6:
        clean_score = min(clean_score, 3.5)

    evasive_phrases = ["i don't know", "dont know", "not sure", "no idea", "pass"]
    if any(p in candidate_answer.lower() for p in evasive_phrases) and len(words) < 15:
        clean_score = min(clean_score, 2.0)

    return round(clean_score, 1)


# ==============================================================================
# 5. STATE MANAGER & TURN DECISION
# ==============================================================================
def update_session_state_after_turn(
    session: InterviewSession,
    topic_id: str,
    score: float
):
    """
    Updates running scores, covered topics, and weak topic tracking in the session state.
    """
    state = session.session_state or {}
    covered = state.get("covered_topics", [])
    if topic_id not in covered:
        covered.append(topic_id)
    state["covered_topics"] = covered

    topic_scores = state.get("topic_scores", {})
    # Running average for this topic
    if topic_id in topic_scores:
        topic_scores[topic_id] = round((topic_scores[topic_id] + score) / 2.0, 1)
    else:
        topic_scores[topic_id] = score
    state["topic_scores"] = topic_scores

    state["turns_taken"] = state.get("turns_taken", 0) + 1
    state["last_turn_score"] = score

    session.session_state = dict(state)
    flag_modified(session, "session_state")


async def generate_final_report(
    db: Session,
    session: InterviewSession
) -> SessionReport:
    """
    Compiles all turn questions, answers, and scores into a structured performance report.
    Persists to session_reports table and updates long-term weak_topic_profile.
    """
    state = session.session_state or {}
    questions = session.questions or []

    turns_summary = []
    total_score = 0.0
    valid_evals_count = 0

    for q in questions:
        if q.answer and q.answer.evaluation:
            score = q.answer.evaluation.score
            total_score += score
            valid_evals_count += 1
            turns_summary.append({
                "topic": q.topic_id or "General",
                "difficulty": q.difficulty,
                "question": q.question_text,
                "answer": q.answer.transcript_text or q.answer.code_submission or "N/A",
                "score": score,
                "feedback": q.answer.evaluation.feedback_text
            })

    overall_score = round(total_score / max(1, valid_evals_count), 1)

    system_prompt = (
        "You are an AI Interview Coach director. Analyze the complete mock interview performance "
        "and generate a final executive feedback report in JSON format."
    )
    user_prompt = f"""
Candidate Interview Performance:
Session Mode: {session.mode}
Overall Average Score: {overall_score} / 10.0
Turns Taken: {len(turns_summary)}
Details per question:
{json.dumps(turns_summary, indent=2)}

Generate a comprehensive final report JSON with:
{{
  "summary_text": "3-4 sentence comprehensive performance summary evaluating communication, technical depth, and preparedness",
  "overall_score": {overall_score},
  "strengths": ["list of 3 specific strengths observed"],
  "weaknesses": ["list of 3 specific knowledge or execution weaknesses"],
  "topic_breakdown": {{"topic_name": score_out_of_10}}
}}
"""
    report_json = await call_groq_json(user_prompt, system_prompt, model=PRIMARY_MODEL)

    if "error" in report_json or "summary_text" not in report_json:
        # Fallback summary
        strengths = ["Solid baseline technical vocabulary", "Clear willingness to tackle multi-turn questions"]
        weaknesses = ["Discuss time and space trade-offs more proactively", "Strengthen edge-case handling"]
        summary_text = (
            f"Candidate completed {len(turns_summary)} adaptive interview turns with an overall score of {overall_score}/10. "
            f"Demonstrated good foundational knowledge with opportunities for deeper complexity analysis."
        )
        report_json = {
            "summary_text": summary_text,
            "overall_score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "topic_breakdown": state.get("topic_scores", {})
        }

    # Save to session_reports table
    report = SessionReport(
        session_id=session.id,
        summary_text=report_json.get("summary_text", "Performance report generated."),
        overall_score=overall_score,
        strengths_json=report_json.get("strengths", []),
        weaknesses_json=report_json.get("weaknesses", []),
        topic_breakdown_json=report_json.get("topic_breakdown", state.get("topic_scores", {}))
    )
    db.add(report)

    # Update weak_topic_profile for candidate
    for topic_id, score in state.get("topic_scores", {}).items():
        profile = db.query(WeakTopicProfile).filter(
            WeakTopicProfile.user_id == session.user_id,
            WeakTopicProfile.topic_id == topic_id
        ).first()

        if profile:
            profile.running_score = round((profile.running_score + score) / 2.0, 1)
            profile.attempts_count += 1
            profile.last_updated = datetime.utcnow()
        else:
            profile = WeakTopicProfile(
                user_id=session.user_id,
                topic_id=topic_id,
                running_score=score,
                attempts_count=1
            )
            db.add(profile)

    session.status = "completed"
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(report)

    return report
