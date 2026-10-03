# AdaptIQ: AI-Powered Voice-First Adaptive Interview Coach
## Comprehensive Viva, Project Defense & Live Demo Guide

---

## 1. Executive Summary & Problem Statement

### The Problem
Traditional technical interview preparation platforms (like LeetCode or static flashcards) are **one-dimensional**:
1. They test coding in a vacuum without testing a candidate's ability to **verbally articulate their thought process** under pressure.
2. They do not simulate the **conversational dynamics** of a human interviewer who probes deeper when an answer is vague or pivots when a candidate is stuck.
3. They treat interview prep as generic, rather than targeting the **specific gap** between a candidate's personal resume and the exact Job Description (JD) they are interviewing for.

### The Solution: AdaptIQ (An Agentic, Voice-First Adaptive Coach)
Our platform bridges this gap through an end-to-end full-stack AI system:
- **Mode A (Targeted JD + Resume)**: Performs semantic gap analysis between candidate experience and role requirements, targeting the exact missing competencies.
- **Mode B (Curriculum Mastery)**: Covers 7 core CS subjects (*DSA, Operating Systems, DBMS, Computer Networks, OOP, HR & Behavioral, Quantitative Aptitude*) across 42 topic trees.
- **Hybrid Voice & Monaco Code Editor**: Seamlessly switches between a glowing call-style voice UI for conceptual questions and an interactive Monaco code editor with an isolated execution sandbox for algorithmic questions.
- **Planner-Executor-Critic State Machine**: Maintains an explicit session state object that dynamically scales question difficulty ($Level\ 1 \to 5$) turn-by-turn based on fine-tuned rubric scoring.
- **Fine-Tuned LoRA Answer Evaluator**: Calibrated on 4 objective rubrics (*Technical Accuracy, Clarity, Completeness, Depth*) with a Critic sanity-check layer.
- **Candidate Analytics & Heatmap**: Visualizes score growth over time, subject mastery percentages, and active weak-topic reinforcement profiles.

---

## 2. Core Architectural Pillars (Why It Is Not a Thin LLM Wrapper)

| Architectural Pillar | Implementation Details |
| :--- | :--- |
| **Multi-Step Agent Loop** | Implements an explicit **Planner $\to$ Executor $\to$ Critic** loop. The Planner assesses state memory (`covered_topics`, `topic_scores`, `current_difficulty`), the Executor retrieves or generates questions, and the Critic checks evaluation scores before persisting state. |
| **3-Way Blended RAG Question Sourcing** | Questions are generated using a balanced **40% / 30% / 30%** ratio: 40% from uploaded subject textbook PDFs (embedded in pgvector/PostgreSQL), 30% from a real question bank, and 30% from general LLM knowledge. This prevents repetitive or purely academic questions. |
| **Fine-Tuned LoRA Evaluator** | Custom instruction dataset fine-tuned with PEFT/LoRA (Llama 3.2 / Phi-3) to enforce objective rubric calibration and eliminate positive sycophancy bias. |
| **Sub-Second Voice Layer** | Integrates Groq **`whisper-large-v3-turbo`** with domain vocabulary hints for Speech-to-Text ($<800\text{ms}$) and browser Web Speech API for zero-latency Text-to-Speech question delivery. |
| **Safe Execution Sandbox** | Isolated local subprocess runner with a **4.0-second timeout guard** to execute Python/JS candidate code and capture stdout, stderr, and runtimes without server vulnerability. |
| **Long-Term Memory** | PostgreSQL 18 tracks session progression, question history, and a persistent `weak_topic_profile` table that feeds future interview sessions. |

---

## 3. Step-by-Step Live Demo Script (For Examiners & Recruiters)

### Demo Part 1: Mode A — Targeted JD + Resume Gap Analysis
1. **Navigate to Mode Selection**: Click **Targeted Mode (JD + Resume)**.
2. **Upload Resume**: Select a candidate resume (e.g. 3 years in Python/FastAPI backend).
3. **Paste Job Description**: Paste a Senior Distributed Systems / Microservices JD (requiring Redis, B-Tree Indexing, Kafka, Kubernetes).
4. **Demonstrate Gap Analysis**:
   - Point out the **Match Score** (e.g., 72%).
   - Highlight the **Identified Skill Gaps** (*B-Trees, Caching Strategies, Distributed Concurrency*).
5. **Start Adaptive Session**: The agent starts the interview by targeting the exact missing skill (e.g. asking about Redis caching and B-Tree indexing).

### Demo Part 2: Voice-First Conceptual Question
1. **AI Speaks the Question**: Show the AI Interviewer Avatar speaking the question aloud via natural TTS.
2. **Dynamic Speech Controls**: Demonstrate **Read Aloud**, **Mute**, and **Voice Speed** adjustments (0.9x to 1.25x).
3. **Record Spoken Answer**:
   - Click the glowing Voice Orb.
   - Point out the real-time **HTML5 Canvas Audio Waveform** dancing in response to your voice volume.
   - Speak an explanation aloud.
4. **Whisper Transcription**:
   - Click stop. Notice the transcript appears in the text field within $<900\text{ms}$ with the badge: `Whisper Transcribed in 759ms`.
5. **Submit & Review Evaluation**:
   - Point out the 4 rubric sub-scores: *Technical Accuracy, Clarity, Completeness, Depth*.
   - Point out how the Agent adapts difficulty for the next question based on your score.

### Demo Part 3: Mode B — Monaco Code Editor & Execution Sandbox
1. **Switch or Receive Coding Question**: Navigate to DSA or select Coding Mode.
2. **Monaco Code Editor**:
   - Show the language dropdown (*Python, JavaScript, C++, Java, C*) with boilerplate starter templates.
   - Demonstrate the **Full Code** vs. **Pseudocode** mode toggle.
3. **Interactive Code Sandbox ("Run Code")**:
   - Type an algorithmic solution (e.g. Two-Sum or Prime checking).
   - Click **"Run Code"**.
   - Show the **Execution Terminal Panel** below the editor rendering stdout, execution duration (e.g. `42ms`), and success badge.
   - Intentionally write an error (`10 / 0`) or infinite loop (`while True:`) to demonstrate the **4-second sandbox timeout protection**.
4. **Submit Solution & Narration**:
   - Type or speak your mental approach in the **"Spoken Reasoning"** field.
   - Submit: Show the multi-language evaluator estimating $O(n)$ time and space complexity!

### Demo Part 4: Candidate Analytics Dashboard & Heatmap
1. **Navigate to Dashboard**: Click **Dashboard** in navigation.
2. **Summary Cards**: Show Total Interviews, Average Score, Candidate Tier Badge (*Advanced Ready*).
3. **Performance Trajectory Chart**: Point out the smooth SVG score progression line chart showing session-over-session growth.
4. **Rubric Balance Radar**: Show the 4-axis rubric balance.
5. **Core CS Subject Mastery**: Show the 7 subject cards with real-time mastery percentage bars.
6. **Targeted Weak-Topic Heatmap**: Show color-coded severity tiles (*Red = Needs Focus, Amber = Improving, Emerald = Mastered*) and click **"Drill This Topic"**.
7. **Export & Print**: Show the one-click **"Export Summary Text"** and **"Print / Save PDF"** performance reports.

---

## 4. Top Technical Questions & Answers for Viva / Examiners

### Q1: Why use an Agentic Planner-Executor-Critic loop instead of a single prompt chain?
> **Answer**: A single prompt chain cannot maintain multi-turn persistent state, dynamically adjust difficulty based on performance history, or ensure evaluation fairness. Our **Planner** evaluates historical scores and selects the next topic and difficulty ($Level\ 1 \to 5$); the **Executor** generates questions through blended RAG; and the **Critic** performs a sanity-check pass on the score to ensure rubrics are rigorously calibrated before updating the candidate's long-term profile.

### Q2: Why fine-tune a model with LoRA for evaluation instead of using GPT-4 with a prompt?
> **Answer**: Standard commercial models suffer from **positive sycophancy bias** (giving high scores to polite or partially correct answers) and inconsistent rubric scoring across turns. Fine-tuning a model (Llama 3.2 / Phi-3) with Low-Rank Adaptation (LoRA) on curated grading triplets (*Question, Candidate Answer, Calibrated Score + Feedback*) provides:
> 1. Strict, objective rubric enforcement.
> 2. Fast, predictable JSON outputs.
> 3. Sub-linear computational cost compared to full parameter tuning.

### Q3: How does the 3-Way Blended RAG strategy work?
> **Answer**: Rather than relying 100% on textbook PDFs (which can lead to dry, repetitive academic definitions) or 100% on pure LLM generation (which can hallucinate or ask generic questions), our orchestrator samples questions from three balanced sources:
> - **40% PDF Grounded**: Semantic similarity retrieval over chunks from our 7 subject PDFs in PostgreSQL.
> - **30% Real Question Bank**: Curated, pre-embedded industry interview questions including our foundational number logic and series problems.
> - **30% Pure LLM Synthesis**: Dynamically synthesized questions grounded in the candidate's specific gap profile.

### Q4: How is voice latency kept low enough for a live interview?
> **Answer**: We use Groq's high-speed inference engine running **`whisper-large-v3-turbo`**, which transcribes audio in $700\text{ms} - 1,200\text{ms}$ with technical domain vocabulary conditioning. For Text-to-Speech, we utilize the browser's native **Web Speech API (`window.speechSynthesis`)**, which delivers natural spoken audio with **zero network latency and zero API cost**.

### Q5: How do you prevent malicious code execution in the Monaco Editor?
> **Answer**: Candidate code runs in an isolated subprocess with:
> 1. A hard **4.0-second timeout guard** that kills infinite loops (`while True`).
> 2. Sandboxed standard I/O streams capturing stdout and stderr without exposing internal file system paths.
> 3. Automatic temporary file cleanup in OS scratch memory.

---

## 5. Startup Commands & Operation

### Backend
```powershell
# From project root
& "backend\venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Frontend
```powershell
# From frontend directory
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`
