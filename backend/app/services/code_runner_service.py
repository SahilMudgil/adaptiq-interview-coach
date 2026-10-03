import sys
import time
import subprocess
import tempfile
import os
import shutil
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("uvicorn.error")

EXECUTION_TIMEOUT_SECONDS = 4.0
COMPILATION_TIMEOUT_SECONDS = 6.0
MAX_OUTPUT_CHARS = 10000

def _truncate(text: str) -> str:
    if not text:
        return ""
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + "\n... [Output truncated after 10,000 characters]"
    return text

def execute_code_safely(
    code_content: str,
    language: str = "python",
    stdin_input: Optional[str] = None
) -> Dict[str, Any]:
    """
    Safely executes code in an isolated subprocess with strict timeout guards.
    Supports Python, JavaScript (Node.js), C++ (g++), C (gcc), and Java.
    Returns stdout, stderr, execution duration (ms), and status.
    """
    if not code_content or not code_content.strip():
        return {
            "status": "error",
            "output": "",
            "error": "No code provided to execute.",
            "execution_time_ms": 0,
            "exit_code": -1
        }

    lang = language.lower().strip()
    start_time = time.time()

    # =========================================================================
    # 1. PYTHON
    # =========================================================================
    if lang in ["python", "py"]:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(code_content)

        try:
            process = subprocess.run(
                [sys.executable, tmp_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            stdout = _truncate(process.stdout)
            stderr = _truncate(process.stderr)

            if process.returncode != 0:
                return {
                    "status": "runtime_error",
                    "output": stdout,
                    "error": stderr.strip() or f"Process exited with code {process.returncode}",
                    "execution_time_ms": elapsed_ms,
                    "exit_code": process.returncode
                }

            return {
                "status": "success",
                "output": stdout,
                "error": stderr.strip() if stderr else "",
                "execution_time_ms": elapsed_ms,
                "exit_code": 0
            }

        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s. Check for infinite loops.",
                "execution_time_ms": elapsed_ms,
                "exit_code": -1
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "execution_time_ms": elapsed_ms,
                "exit_code": -1
            }
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # =========================================================================
    # 2. JAVASCRIPT / NODE.JS
    # =========================================================================
    elif lang in ["javascript", "js"]:
        node_bin = "node"
        with tempfile.NamedTemporaryFile(suffix=".js", mode="w", encoding="utf-8", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(code_content)

        try:
            process = subprocess.run(
                [node_bin, tmp_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            stdout = _truncate(process.stdout)
            stderr = _truncate(process.stderr)

            if process.returncode != 0:
                return {
                    "status": "runtime_error",
                    "output": stdout,
                    "error": stderr.strip() or f"Node exited with code {process.returncode}",
                    "execution_time_ms": elapsed_ms,
                    "exit_code": process.returncode
                }

            return {
                "status": "success",
                "output": stdout,
                "error": stderr.strip() if stderr else "",
                "execution_time_ms": elapsed_ms,
                "exit_code": 0
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "output": "",
                "error": "Node.js is not installed locally on this machine.",
                "execution_time_ms": 0,
                "exit_code": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "exit_code": -1
            }
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # =========================================================================
    # 3. C++ (G++)
    # =========================================================================
    elif lang in ["cpp", "c++"]:
        run_code = code_content
        # If candidate wrote a function or class without main(), add a runnable harness
        if "main(" not in run_code:
            headers = ""
            if "#include" not in run_code:
                headers = "#include <iostream>\n#include <vector>\n#include <string>\n#include <algorithm>\nusing namespace std;\n\n"
            if "class Solution" in run_code:
                main_stub = (
                    "\n\nint main() {\n"
                    "    Solution sol;\n"
                    "    cout << \"[Execution completed: Solution class compiled and instantiated successfully]\" << endl;\n"
                    "    return 0;\n"
                    "}\n"
                )
            else:
                main_stub = (
                    "\n\nint main() {\n"
                    "    cout << \"[Execution completed: Code compiled and verified successfully with no syntax errors]\" << endl;\n"
                    "    return 0;\n"
                    "}\n"
                )
            run_code = headers + run_code + main_stub

        with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", encoding="utf-8", delete=False) as tmp_file:
            src_path = tmp_file.name
            tmp_file.write(run_code)

        exe_path = src_path.replace(".cpp", ".exe")

        try:
            # Step A: Compile
            compile_proc = subprocess.run(
                ["g++", "-std=c++14", src_path, "-o", exe_path],
                capture_output=True,
                text=True,
                timeout=COMPILATION_TIMEOUT_SECONDS
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            if compile_proc.returncode != 0:
                stderr_text = compile_proc.stderr or ""
                clean_err = stderr_text.replace(src_path, "solution.cpp") if isinstance(stderr_text, str) else str(stderr_text)
                return {
                    "status": "compilation_error",
                    "output": "",
                    "error": _truncate(clean_err.strip()) or "C++ compilation failed.",
                    "execution_time_ms": elapsed_ms,
                    "exit_code": compile_proc.returncode
                }

            # Step B: Run Executable
            run_proc = subprocess.run(
                [exe_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS
            )
            total_elapsed_ms = int((time.time() - start_time) * 1000)
            stdout = _truncate(run_proc.stdout)
            stderr = _truncate(run_proc.stderr)

            if run_proc.returncode != 0:
                return {
                    "status": "runtime_error",
                    "output": stdout,
                    "error": stderr.strip() or f"Process exited with code {run_proc.returncode}",
                    "execution_time_ms": total_elapsed_ms,
                    "exit_code": run_proc.returncode
                }

            return {
                "status": "success",
                "output": stdout,
                "error": stderr.strip() if stderr else "",
                "execution_time_ms": total_elapsed_ms,
                "exit_code": 0
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "output": "",
                "error": "g++ compiler not found in system PATH. Install MinGW or GCC.",
                "execution_time_ms": 0,
                "exit_code": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "exit_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "exit_code": -1
            }
        finally:
            if os.path.exists(src_path):
                try:
                    os.remove(src_path)
                except OSError:
                    pass
            if os.path.exists(exe_path):
                try:
                    os.remove(exe_path)
                except OSError:
                    pass

    # =========================================================================
    # 4. C (GCC)
    # =========================================================================
    elif lang in ["c"]:
        run_code = code_content
        if "main(" not in run_code:
            headers = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n" if "#include" not in run_code else ""
            main_stub = (
                "\n\nint main() {\n"
                "    printf(\"[Execution completed: C code compiled and verified successfully]\\n\");\n"
                "    return 0;\n"
                "}\n"
            )
            run_code = headers + run_code + main_stub

        with tempfile.NamedTemporaryFile(suffix=".c", mode="w", encoding="utf-8", delete=False) as tmp_file:
            src_path = tmp_file.name
            tmp_file.write(run_code)

        exe_path = src_path.replace(".c", ".exe")

        try:
            compile_proc = subprocess.run(
                ["gcc", src_path, "-o", exe_path],
                capture_output=True,
                text=True,
                timeout=COMPILATION_TIMEOUT_SECONDS
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            if compile_proc.returncode != 0:
                stderr_text = compile_proc.stderr or ""
                clean_err = stderr_text.replace(src_path, "solution.c") if isinstance(stderr_text, str) else str(stderr_text)
                return {
                    "status": "compilation_error",
                    "output": "",
                    "error": _truncate(clean_err.strip()) or "C compilation failed.",
                    "execution_time_ms": elapsed_ms,
                    "exit_code": compile_proc.returncode
                }

            run_proc = subprocess.run(
                [exe_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS
            )
            total_elapsed_ms = int((time.time() - start_time) * 1000)
            stdout = _truncate(run_proc.stdout)
            stderr = _truncate(run_proc.stderr)

            if run_proc.returncode != 0:
                return {
                    "status": "runtime_error",
                    "output": stdout,
                    "error": stderr.strip() or f"Process exited with code {run_proc.returncode}",
                    "execution_time_ms": total_elapsed_ms,
                    "exit_code": run_proc.returncode
                }

            return {
                "status": "success",
                "output": stdout,
                "error": stderr.strip() if stderr else "",
                "execution_time_ms": total_elapsed_ms,
                "exit_code": 0
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "output": "",
                "error": "gcc compiler not found in system PATH.",
                "execution_time_ms": 0,
                "exit_code": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "exit_code": -1
            }
        finally:
            if os.path.exists(src_path):
                try:
                    os.remove(src_path)
                except OSError:
                    pass
            if os.path.exists(exe_path):
                try:
                    os.remove(exe_path)
                except OSError:
                    pass

    # =========================================================================
    # 5. JAVA
    # =========================================================================
    elif lang in ["java"]:
        temp_dir = tempfile.mkdtemp()
        java_path = os.path.join(temp_dir, "Solution.java")

        run_code = code_content
        if "class " not in run_code:
            run_code = (
                "public class Solution {\n"
                "    public static void main(String[] args) {\n"
                f"        {code_content}\n"
                "    }\n"
                "}\n"
            )
        elif "main(" not in run_code:
            last_brace = run_code.rfind("}")
            if last_brace != -1:
                run_code = (
                    run_code[:last_brace]
                    + "\n    public static void main(String[] args) {\n"
                    "        System.out.println(\"[Execution completed: Java class verified successfully]\");\n"
                    "    }\n}"
                )

        with open(java_path, "w", encoding="utf-8") as jf:
            jf.write(run_code)

        try:
            # Modern Java 11+ single-file execution: 'java Solution.java'
            process = subprocess.run(
                ["java", java_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS + 2.0
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            stdout = _truncate(process.stdout)
            stderr = _truncate(process.stderr)

            if process.returncode != 0:
                stderr_text = stderr or ""
                clean_err = stderr_text.replace(java_path, "Solution.java") if isinstance(stderr_text, str) else str(stderr_text)
                return {
                    "status": "compilation_error" if "error:" in clean_err else "runtime_error",
                    "output": stdout,
                    "error": clean_err.strip() or f"Java exited with code {process.returncode}",
                    "execution_time_ms": elapsed_ms,
                    "exit_code": process.returncode
                }

            return {
                "status": "success",
                "output": stdout,
                "error": stderr.strip() if stderr else "",
                "execution_time_ms": elapsed_ms,
                "exit_code": 0
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "output": "",
                "error": "Java runtime (java) not found in system PATH.",
                "execution_time_ms": 0,
                "exit_code": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "exit_code": -1
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # =========================================================================
    # 6. SQL (SQLite In-Memory Execution with Pre-seeded Schemas)
    # =========================================================================
    elif lang in ["sql"]:
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        query_lower = code_content.lower()

        # Pre-seed standard interview tables if query references them
        if "orders" in query_lower:
            cursor.execute("""
                CREATE TABLE Orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    order_date TEXT,
                    amount REAL
                );
            """)
            cursor.executemany("""
                INSERT INTO Orders VALUES (?, ?, ?, ?);
            """, [
                (1, 101, '2026-01-10', 150.0),
                (2, 102, '2026-01-11', 200.0),
                (3, 101, '2026-01-15', 50.0),
                (4, 103, '2026-01-18', 320.0),
                (5, 101, '2026-01-20', 80.0),
                (6, 102, '2026-01-22', 110.0),
            ])

        if "customers" in query_lower or "customer" in query_lower:
            cursor.execute("""
                CREATE TABLE Customers (
                    customer_id INTEGER PRIMARY KEY,
                    customer_name TEXT,
                    email TEXT,
                    city TEXT
                );
            """)
            cursor.executemany("""
                INSERT INTO Customers VALUES (?, ?, ?, ?);
            """, [
                (101, 'Alice Smith', 'alice@example.com', 'New York'),
                (102, 'Bob Jones', 'bob@example.com', 'San Francisco'),
                (103, 'Charlie Brown', 'charlie@example.com', 'Chicago'),
                (104, 'Diana Prince', 'diana@example.com', 'Seattle'),
            ])

        if "employees" in query_lower or "employee" in query_lower or "department" in query_lower:
            cursor.execute("""
                CREATE TABLE Employees (
                    emp_id INTEGER PRIMARY KEY,
                    name TEXT,
                    department_id INTEGER,
                    salary REAL
                );
            """)
            cursor.executemany("""
                INSERT INTO Employees VALUES (?, ?, ?, ?);
            """, [
                (1, 'John Doe', 1, 85000.0),
                (2, 'Jane Smith', 1, 92000.0),
                (3, 'Mark Taylor', 2, 78000.0),
                (4, 'Emily Watson', 2, 81000.0),
                (5, 'David Clark', 3, 105000.0),
            ])

            cursor.execute("""
                CREATE TABLE Departments (
                    department_id INTEGER PRIMARY KEY,
                    dept_name TEXT
                );
            """)
            cursor.executemany("""
                INSERT INTO Departments VALUES (?, ?);
            """, [
                (1, 'Engineering'),
                (2, 'Marketing'),
                (3, 'Finance'),
            ])

        try:
            # Handle comments and split statements
            statements = [s.strip() for s in code_content.strip().split(";") if s.strip()]
            result_output = []

            for stmt in statements:
                # Remove comment lines
                clean_lines = [l for l in stmt.split("\n") if not l.strip().startswith("--")]
                clean_stmt = " ".join(clean_lines).strip()
                if not clean_stmt:
                    continue

                cursor.execute(clean_stmt)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()

                    col_widths = [max(len(col), max((len(str(r[i])) for r in rows), default=0)) for i, col in enumerate(columns)]
                    header_line = " | ".join(col.ljust(col_widths[i]) for i, col in enumerate(columns))
                    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(columns)))

                    data_lines = []
                    for r in rows:
                        data_lines.append(" | ".join(str(r[i]).ljust(col_widths[i]) for i in range(len(columns))))

                    table_str = f"{header_line}\n{sep_line}\n" + "\n".join(data_lines)
                    result_output.append(f"{table_str}\n\n({len(rows)} row{'s' if len(rows) != 1 else ''} returned)")
                else:
                    conn.commit()
                    result_output.append(f"Query executed successfully ({cursor.rowcount} rows affected).")

            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "success",
                "output": _truncate("\n\n".join(result_output)),
                "error": "",
                "execution_time_ms": elapsed_ms,
                "exit_code": 0
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "runtime_error",
                "output": "",
                "error": f"SQL Execution Error: {str(e)}",
                "execution_time_ms": elapsed_ms,
                "exit_code": 1
            }
        finally:
            conn.close()

    # =========================================================================
    # Fallback for unknown language
    # =========================================================================
    else:
        return {
            "status": "unsupported_runtime",
            "output": "",
            "error": f"Language '{language}' is not configured for direct sandbox execution. Supported: Python, JavaScript, C++, C, Java, SQL.",
            "execution_time_ms": 0,
            "exit_code": -1
        }


async def verify_pseudocode_logic(
    pseudocode: str,
    question_text: str = "",
    topic_name: str = ""
) -> Dict[str, Any]:
    """
    Rigorously verifies a candidate's pseudocode on algorithmic correctness,
    variable initialization, pointer update order, loop invariants, concrete dry-run trace,
    edge cases, and Big-O time/space complexity.
    Returns simulated terminal execution result with status 'success' or 'logic_error'.
    """
    from backend.app.services.llm_service import call_groq_json, FAST_MODEL
    start_time = time.time()

    clean_pseudo = pseudocode.strip() if pseudocode else ""
    if not clean_pseudo or len(clean_pseudo) < 10:
        return {
            "status": "error",
            "output": "",
            "error": "Please write your pseudocode algorithm before running logic verification.",
            "execution_time_ms": 0,
            "exit_code": 1
        }

    system_prompt = (
        "You are a Senior Principal Algorithm Engineer and Technical Interviewer at a Tier-1 tech company. "
        "You are evaluating a candidate's PSEUDOCODE for an algorithmic problem. "
        "CRITICAL RULES:\n"
        "1. DO NOT fail the candidate on language syntax (e.g. arrow notation '<-', capitalized keywords 'FUNCTION', 'WHILE', indentation, or missing types).\n"
        "2. Focus STRICTLY on ALGORITHMIC LOGIC: Are variables initialized properly? Are pointers updated in the correct order without losing references? Does the loop terminate? Are edge cases (empty input, 1 element) handled?\n"
        "3. Perform a concrete DRY-RUN step-by-step simulation on a small sample input (e.g. 1 -> 2 -> 3 -> null).\n"
        "4. Determine Time & Space complexity.\n"
        "Respond STRICTLY with a valid JSON object in this format:\n"
        "{\n"
        '  "is_valid": true,\n'
        '  "approach_title": "e.g. Iterative 3-Pointer In-Place Reversal",\n'
        '  "time_complexity": "e.g. O(n)",\n'
        '  "space_complexity": "e.g. O(1)",\n'
        '  "logic_points": ["Point 1: correctly stores next node before modifying curr.next", "Point 2: ..."],\n'
        '  "detected_issues": ["Issue 1 (only if is_valid is false)", ...],\n'
        '  "dry_run_sample": "Input: 1 -> 2 -> 3 -> null",\n'
        '  "dry_run_steps": [\n'
        '    "Init: prev = NULL, curr = [1]",\n'
        '    "Step 1: next = [2], [1].next = NULL, prev = [1], curr = [2]",\n'
        '    "..."\n'
        '  ],\n'
        '  "edge_case_notes": ["Empty list: returns NULL correctly", "Single node: returns node correctly"],\n'
        '  "interviewer_verdict": "Clear 1-sentence assessment summary"\n'
        "}"
    )

    user_prompt = f"""
Problem Statement (Topic: {topic_name or 'Algorithm'}):
"{question_text or 'Algorithmic Problem'}"

Candidate's Submitted Pseudocode:
```text
{clean_pseudo}
```

Rigorously analyze the algorithmic logic, perform a concrete dry-run trace, and return JSON:
"""
    try:
        data = await call_groq_json(user_prompt, system_prompt, model=FAST_MODEL)
        elapsed_ms = int((time.time() - start_time) * 1000)

        is_valid = bool(data.get("is_valid", True))
        status = "success" if is_valid else "logic_error"
        approach = data.get("approach_title", "Algorithmic Logic Analysis")
        time_comp = data.get("time_complexity", "O(n)")
        space_comp = data.get("space_complexity", "O(1)")
        logic_points = data.get("logic_points", [])
        issues = data.get("detected_issues", [])
        dry_run_sample = data.get("dry_run_sample", "Sample Input")
        dry_run_steps = data.get("dry_run_steps", [])
        edge_cases = data.get("edge_case_notes", [])
        verdict = data.get("interviewer_verdict", "")

        lines = [
            "=" * 70,
            "  [PSEUDOCODE ALGORITHMIC VERIFICATION & LOGIC DRY-RUN]",
            "=" * 70,
            f"[STATUS]     {'SUCCESS: Logic Verified (Algorithm is Correct)' if is_valid else 'LOGIC FLAW DETECTED'}",
            f"[APPROACH]   {approach}",
            f"[COMPLEXITY] Time: {time_comp} | Space: {space_comp}",
            ""
        ]

        if is_valid:
            lines.append("[LOGIC ANALYSIS]")
            for pt in logic_points:
                lines.append(f"  [+] {pt}")
            lines.append("")

            if dry_run_steps:
                lines.append(f"[STEP-BY-STEP DRY-RUN] ({dry_run_sample})")
                for s in dry_run_steps:
                    lines.append(f"   -> {s}")
                lines.append("")

            if edge_cases:
                lines.append("[EDGE CASE HANDLING]")
                for ec in edge_cases:
                    lines.append(f"  [ok] {ec}")
                lines.append("")
        else:
            lines.append("[LOGICAL ISSUES DETECTED]")
            for issue in issues:
                lines.append(f"  [!] {issue}")
            lines.append("")

            if logic_points:
                lines.append("[PARTIALLY CORRECT STEPS]")
                for pt in logic_points:
                    lines.append(f"  [+] {pt}")
                lines.append("")

            if dry_run_steps:
                lines.append(f"[FAILURE TRACE] ({dry_run_sample})")
                for s in dry_run_steps:
                    lines.append(f"   -> {s}")
                lines.append("")

        if verdict:
            lines.append(f"[INTERVIEWER NOTE] {verdict}")
        lines.append("=" * 70)

        terminal_output = "\n".join(lines)

        return {
            "status": status,
            "output": terminal_output if is_valid else "",
            "error": terminal_output if not is_valid else "",
            "execution_time_ms": elapsed_ms,
            "exit_code": 0 if is_valid else 1,
            "is_pseudocode_analysis": True
        }

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "error",
            "output": "",
            "error": f"Pseudocode verification error: {str(e)}",
            "execution_time_ms": elapsed_ms,
            "exit_code": 1
        }

