import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.all_models import Resume, JobDescription
from backend.app.services.embedding_service import get_embedding, cosine_similarity, _local_semantic_embedding, EMBEDDING_DIM
from backend.app.services.llm_service import call_groq_json

logger = logging.getLogger("uvicorn.error")

async def parse_resume_to_json(raw_text: str) -> Dict[str, Any]:
    """
    Extracts structured technical competencies, experience, and domains from resume text using Groq LLM.
    """
    system_prompt = (
        "You are an expert technical recruiter and resume parser. "
        "Extract structured candidate information from the resume text into JSON format."
    )
    user_prompt = f"""
Analyze the following resume text and output a JSON object with:
{{
  "candidate_name": "string",
  "summary": "string",
  "years_of_experience": float or integer,
  "technical_skills": ["list", "of", "programming", "languages", "tools"],
  "core_cs_knowledge": ["list", "of", "domains", "like", "DSA", "OS", "DBMS", "Networks", "OOPs"],
  "frameworks_and_libraries": ["list", "of", "frameworks"],
  "projects": [
    {{"title": "project name", "technologies": ["tech1", "tech2"], "description": "short summary"}}
  ],
  "education": "string"
}}

Resume text:
{raw_text[:4000]}
"""
    result = await call_groq_json(user_prompt, system_prompt)
    if "error" in result:
        # Fallback heuristic extraction if LLM is unavailable
        words = set(raw_text.lower().split())
        cs_domains = [d for d in ["dsa", "os", "dbms", "networks", "oops", "python", "java", "sql", "c++", "javascript"] if d in words]
        return {
            "candidate_name": "Candidate",
            "summary": "Technical candidate",
            "years_of_experience": 1.0,
            "technical_skills": list(cs_domains),
            "core_cs_knowledge": list(cs_domains),
            "frameworks_and_libraries": [],
            "projects": [],
            "education": "Computer Science / Engineering"
        }
    return result

async def parse_jd_to_json(raw_text: str) -> Dict[str, Any]:
    """
    Extracts structured requirements, critical skills, and expectations from a Job Description.
    """
    system_prompt = (
        "You are an expert technical hiring manager. "
        "Extract structured technical requirements from the Job Description into JSON format."
    )
    user_prompt = f"""
Analyze the following Job Description text and output a JSON object with:
{{
  "role_title": "string",
  "required_skills": ["list", "of", "mandatory", "skills"],
  "preferred_skills": ["list", "of", "bonus", "skills"],
  "core_cs_subjects": ["list", "e.g.", "DSA", "DBMS", "OS", "Computer Networks", "OOPs"],
  "experience_level": "Entry / Mid / Senior",
  "key_responsibilities": ["bullet", "points"]
}}

Job Description text:
{raw_text[:4000]}
"""
    result = await call_groq_json(user_prompt, system_prompt)
    if "error" in result:
        words = set(raw_text.lower().split())
        matched = [d for d in ["dsa", "os", "dbms", "networks", "oops", "python", "sql", "react", "distributed systems"] if d in words]
        return {
            "role_title": "Software Engineer",
            "required_skills": list(matched) or ["Python", "Algorithms", "Databases"],
            "preferred_skills": [],
            "core_cs_subjects": ["DSA", "DBMS"],
            "experience_level": "Entry/Mid",
            "key_responsibilities": ["Software Development"]
        }
    return result

async def perform_gap_analysis(
    resume_json: Dict[str, Any],
    jd_json: Dict[str, Any],
    resume_embedding: List[float],
    jd_embedding: List[float]
) -> Dict[str, Any]:
    """
    Compares the candidate's parsed resume against role requirements to find critical skill gaps.
    Produces the target interview plan focusing on those gaps.
    """
    semantic_similarity = cosine_similarity(resume_embedding, jd_embedding)
    match_percentage = round(max(10.0, min(95.0, semantic_similarity * 100.0)), 1)

    system_prompt = (
        "You are an AI Interview Coach orchestrator. Compare candidate resume profile against target Job Description "
        "to discover capability gaps and craft a targeted spoken mock interview plan."
    )
    user_prompt = f"""
Candidate Resume Profile:
{json.dumps(resume_json, indent=2)}

Target Job Description Requirements:
{json.dumps(jd_json, indent=2)}

Semantic Match Vector Score: {match_percentage}%

Generate a comprehensive Gap Analysis JSON with:
{{
  "overall_match_percentage": {match_percentage},
  "match_summary": "1-2 sentence executive assessment of fit",
  "matched_skills": ["skills the candidate clearly possesses"],
  "missing_critical_skills": ["skills required by the JD that the candidate lacks"],
  "weak_knowledge_areas": ["areas where candidate has only surface-level exposure"],
  "recommended_interview_focus": [
    {{"topic": "e.g. Concurrency & Deadlocks", "reason": "Required by role but absent on resume", "priority": "high"}},
    {{"topic": "e.g. Distributed Caching", "reason": "Mentioned in JD as key qualification", "priority": "high"}}
  ],
  "starting_difficulty": 2 or 3
}}
"""
    gap_result = await call_groq_json(user_prompt, system_prompt)
    if "error" in gap_result:
        # Fallback calculation
        resume_skills = set(k.lower() for k in resume_json.get("technical_skills", []))
        jd_skills = set(k.lower() for k in jd_json.get("required_skills", []))
        matched = list(resume_skills.intersection(jd_skills))
        missing = list(jd_skills.difference(resume_skills))

        return {
            "overall_match_percentage": match_percentage,
            "match_summary": f"Candidate matches {len(matched)} key requirements with {len(missing)} capability gaps.",
            "matched_skills": matched,
            "missing_critical_skills": missing or ["Advanced System Design", "Low-level Concurrency"],
            "weak_knowledge_areas": ["In-depth edge cases", "Production scaling"],
            "recommended_interview_focus": [
                {"topic": missing[0] if missing else "DSA Optimization", "reason": "Critical role requirement", "priority": "high"},
                {"topic": "System Reliability", "reason": "Role expectation", "priority": "medium"}
            ],
            "starting_difficulty": 2
        }

    return gap_result
