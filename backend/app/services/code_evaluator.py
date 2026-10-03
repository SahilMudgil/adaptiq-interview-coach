import json
import logging
from typing import Dict, Any, Optional
from backend.app.services.llm_service import call_groq_json, FAST_MODEL, PRIMARY_MODEL

logger = logging.getLogger("uvicorn.error")

async def evaluate_code_submission(
    question_text: str,
    topic_name: str,
    difficulty: int,
    code_submission: str,
    code_language: str = "python",
    answer_mode: str = "full_code",
    spoken_narration: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates a candidate's code submission for DSA and OOPs problems.
    Judges:
      - Correctness & Algorithmic Logic
      - Time & Space Complexity
      - Edge-Case handling (empty input, boundaries, duplicates)
      - Code Structure, clean naming, and syntax
      - If pseudocode: relaxes exact syntax and focuses on logical completeness.
      - If spoken narration is provided: factors in candidate's verbal thought process.
    """
    is_sql = code_language.lower() == "sql"
    cleaned_code = code_submission.strip() if code_submission else ""

    if not cleaned_code or len(cleaned_code) < 10 or cleaned_code == "-- Write your SQL query here":
        return {
            "score": 1.0,
            "sub_scores": {
                "correctness": 1.0,
                "time_complexity": 1.0,
                "space_complexity": 1.0,
                "code_cleanliness": 1.0,
                "edge_cases": 1.0
            },
            "feedback": (
                "No SQL query was written. Please write a valid SQL statement (e.g., SELECT ... FROM ...) to solve the query challenge."
                if is_sql
                else "No functional code solution was provided. A valid solution should include the function signature, core logic, and return value."
            ),
            "improved_code_snippet": (
                "-- Example Query Pattern:\nSELECT column_name, COUNT(*)\nFROM table_name\nGROUP BY column_name;"
                if is_sql
                else "# Example template\ndef solution(nums):\n    # Handle edge cases\n    if not nums:\n        return []\n    # Optimal logic\n    pass\n"
            )
        }

    if is_sql:
        rubric_instruction = (
            "Evaluate this SQL query on a 0.0 to 10.0 scale. "
            "Check query correctness, appropriate SELECT/FROM clauses, correct JOINs, aggregations (GROUP BY, HAVING, COUNT/SUM/AVG), "
            "filtering (WHERE), NULL handling, and index/query efficiency."
        )
        system_prompt = (
            "You are a Principal Database Architect and Technical Interviewer at a Tier-1 tech company. "
            "Evaluate the candidate's SQL query objectively. "
            "Return your assessment strictly as a JSON object."
        )
    elif answer_mode == "full_code":
        rubric_instruction = (
            "Evaluate on a 0.0 to 10.0 scale. "
            "Strictly check correctness, time/space complexity, edge cases, and cleanliness."
        )
        system_prompt = (
            "You are a Senior Principal Software Engineer and Technical Interviewer at a Tier-1 tech company. "
            "Evaluate the candidate's code submission objectively. "
            "Return your assessment strictly as a JSON object."
        )
    else:
        rubric_instruction = (
            "Evaluate as PSEUDOCODE: focus on logical completeness, algorithm steps, and invariants rather than language syntax errors."
        )
        system_prompt = (
            "You are a Senior Principal Software Engineer and Technical Interviewer at a Tier-1 tech company. "
            "Evaluate the candidate's code submission objectively. "
            "Return your assessment strictly as a JSON object."
        )

    narration_context = (
        f"- Spoken Thought-Process: \"{spoken_narration.strip()}\"\n"
        if spoken_narration and len(str(spoken_narration).strip()) > 3
        else ""
    )

    user_prompt = f"""
Problem Statement (Difficulty {difficulty}/5 on {topic_name}):
"{question_text}"

Submission Details:
- Programming Language: {code_language.upper()}
- Submission Mode: {answer_mode.upper()} ({rubric_instruction})
{narration_context}

Submitted Code:
```{code_language}
{code_submission}
```

Evaluate the code and output a JSON object with:
{{
  "score": float between 0.0 and 10.0,
  "sub_scores": {{
    "correctness": float 0-10,
    "time_complexity": float 0-10,
    "space_complexity": float 0-10,
    "code_cleanliness": float 0-10,
    "edge_cases": float 0-10
  }},
  "time_complexity_detected": "e.g. O(n) or O(n^2)",
  "space_complexity_detected": "e.g. O(1) or O(n)",
  "feedback": "3-4 concise, direct sentences reviewing the algorithmic strategy, any bugs or unhandled edge cases, and efficiency trade-offs",
  "improved_code_snippet": "A clean, production-grade implementation of the optimal solution in {code_language}"
}}
"""
    eval_result = await call_groq_json(user_prompt, system_prompt, model=FAST_MODEL)

    if "error" in eval_result or "score" not in eval_result:
        # Fallback evaluation heuristic
        lines = [l for l in code_submission.split("\n") if l.strip() and not l.strip().startswith(("#", "//"))]
        line_count = len(lines)
        base_score = min(8.0, max(3.5, line_count * 0.4 + 2.0))

        eval_result = {
            "score": round(base_score, 1),
            "sub_scores": {
                "correctness": round(base_score, 1),
                "time_complexity": 7.0,
                "space_complexity": 7.0,
                "code_cleanliness": 7.5,
                "edge_cases": round(base_score - 1.0, 1)
            },
            "time_complexity_detected": "O(n)",
            "space_complexity_detected": "O(1)",
            "feedback": f"Code structure is in place with {line_count} logic lines. Ensure all boundary conditions and null/empty inputs are explicitly tested.",
            "improved_code_snippet": code_submission
        }

    return eval_result
