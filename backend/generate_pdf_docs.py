import os
import subprocess
import sys

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AdaptIQ — Project Documentation & Engineering Specification</title>
<style>
  @page {
    size: A4;
    margin: 16mm 14mm 16mm 14mm;
    @bottom-center {
      content: "AdaptIQ Engineering Specification • Page " counter(page);
      font-size: 8pt;
      color: #64748B;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #1E293B;
    background-color: #FFFFFF;
    line-height: 1.55;
    font-size: 9.5pt;
    margin: 0;
    padding: 0;
  }

  /* Cover Page */
  .cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 90vh;
    padding: 40px 20px;
    border-bottom: 3px solid #4F46E5;
  }

  .cover-badge {
    display: inline-block;
    background-color: #EEF2FF;
    color: #4338CA;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 10pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 24px;
    border: 1px solid #C7D2FE;
    width: fit-content;
  }

  .cover-title {
    font-size: 30pt;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.15;
    margin: 0 0 16px 0;
    letter-spacing: -0.03em;
  }

  .cover-subtitle {
    font-size: 13pt;
    color: #475569;
    line-height: 1.5;
    margin-bottom: 36px;
    max-width: 650px;
  }

  .cover-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
    max-width: 650px;
  }

  .cover-meta-item {
    font-size: 9.5pt;
  }

  .cover-meta-label {
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    font-size: 8pt;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
  }

  .cover-meta-value {
    color: #0F172A;
    font-weight: 600;
    word-break: break-all;
  }

  /* Headings */
  h1 {
    font-size: 18pt;
    font-weight: 800;
    color: #0F172A;
    margin-top: 28px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #E2E8F0;
    letter-spacing: -0.02em;
    page-break-after: avoid;
  }

  h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #1E293B;
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }

  h3 {
    font-size: 10.5pt;
    font-weight: 700;
    color: #334155;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }

  p {
    margin: 0 0 10px 0;
    color: #334155;
    text-align: justify;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 18px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }

  th, td {
    padding: 7px 10px;
    border: 1px solid #CBD5E1;
    text-align: left;
    vertical-align: top;
  }

  th {
    background-color: #F1F5F9;
    font-weight: 700;
    color: #0F172A;
  }

  tr:nth-child(even) {
    background-color: #F8FAFC;
  }

  /* Callout Boxes */
  .callout {
    background: #EEF2FF;
    border-left: 4px solid #4F46E5;
    padding: 10px 14px;
    margin: 12px 0;
    border-radius: 0 6px 6px 0;
    font-size: 9pt;
  }

  .callout-title {
    font-weight: 700;
    color: #312E81;
    margin-bottom: 4px;
    font-size: 9pt;
  }

  .callout-success {
    background: #ECFDF5;
    border-left-color: #10B981;
  }
  .callout-success .callout-title { color: #065F46; }

  .callout-warning {
    background: #FFFBEB;
    border-left-color: #F59E0B;
  }
  .callout-warning .callout-title { color: #92400E; }

  /* Code Block */
  pre, code {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8pt;
  }

  pre {
    background: #0F172A;
    color: #F8FAFC;
    padding: 10px 14px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 10px 0 14px 0;
    line-height: 1.45;
    page-break-inside: avoid;
  }

  code.inline {
    background: #F1F5F9;
    color: #4F46E5;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 8.5pt;
    font-weight: 600;
  }

  /* Feature Grid */
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 12px 0;
    page-break-inside: avoid;
  }

  .card {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 14px;
    background: #FFFFFF;
  }

  .card-header {
    font-weight: 700;
    font-size: 9.5pt;
    color: #0F172A;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .page-break {
    page-break-before: always;
  }

  ul, ol {
    margin: 0 0 10px 0;
    padding-left: 20px;
    color: #334155;
  }

  li {
    margin-bottom: 4px;
  }

  .tag {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    margin-right: 4px;
  }
  .tag-blue { background: #DBEAFE; color: #1E40AF; }
  .tag-purple { background: #EDE9FE; color: #5B21B6; }
  .tag-green { background: #D1FAE5; color: #065F46; }
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover-page">
  <div class="cover-badge">Engineering Whitepaper & Project Defense Guide • v2.0</div>
  <h1 class="cover-title">AdaptIQ</h1>
  <div class="cover-subtitle">
    An Agentic, Voice-First Adaptive Technical Interview Coach with Dynamic Difficulty Scaling, Sandboxed Multi-Language Code Execution, and Fine-Tuned LoRA Rubric Evaluation.
  </div>

  <div class="cover-meta-grid">
    <div class="cover-meta-item">
      <div class="cover-meta-label">Author & Creator</div>
      <div class="cover-meta-value">Sahil Mudgil</div>
    </div>
    <div class="cover-meta-item">
      <div class="cover-meta-label">Project Domain</div>
      <div class="cover-meta-value">Generative AI • Agents • Speech Tech • Full-Stack Systems</div>
    </div>
    <div class="cover-meta-item">
      <div class="cover-meta-label">Live Web Application</div>
      <div class="cover-meta-value">https://adaptiq-interview-coach.vercel.app</div>
    </div>
    <div class="cover-meta-item">
      <div class="cover-meta-label">Live Backend API</div>
      <div class="cover-meta-value">https://adaptiq-interview-coach.onrender.com</div>
    </div>
    <div class="cover-meta-item">
      <div class="cover-meta-label">Source Code Repository</div>
      <div class="cover-meta-value">https://github.com/SahilMudgil/adaptiq-interview-coach</div>
    </div>
    <div class="cover-meta-item">
      <div class="cover-meta-label">Cloud Infrastructure</div>
      <div class="cover-meta-value">Vercel (Edge) • Render (FastAPI) • Neon (PostgreSQL 16)</div>
    </div>
  </div>
</div>

<!-- SECTION 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT -->
<h1>1. Executive Summary & Problem Statement</h1>

<h2>1.1 The Silent Coder Dilemma</h2>
<p>
Traditional technical interview preparation platforms—such as LeetCode, HackerRank, and static flashcards—suffer from fundamental structural shortcomings when preparing candidates for real-world engineering interviews:
</p>
<ol>
  <li><strong>The Silent Coder Trap:</strong> Conventional platforms only evaluate whether code passes test cases in absolute silence. In real-world FAANG, Tier-1 tech, and system design interviews, <strong>verbal articulation of thoughts, communication of trade-offs, and explaining invariants under pressure accounts for 50%+ of the hiring decision.</strong></li>
  <li><strong>Static, Rigid Difficulty:</strong> Static question sets do not adapt. If a candidate struggles on a Level 4 Dynamic Programming problem, existing platforms do not recognize the foundational gap (e.g., weak recursion or series logic) and fail to adjust down to rebuild confidence.</li>
  <li><strong>The One-Size-Fits-All Fallacy:</strong> Generic question banks ignore the candidate's personal resume and the exact Job Description (JD) they are targeting, resulting in mismatched preparation.</li>
</ol>

<h2>1.2 The AdaptIQ Solution</h2>
<p>
<strong>AdaptIQ</strong> is an end-to-end full-stack agentic platform that addresses every failure mode of conventional interview preparation. It introduces an interactive, multimodal AI interviewer that listens, speaks, monitors code execution in a sandbox, verifies algorithmic pseudocode logic, dynamically scales difficulty turn-by-turn ($Level\ 1 \to 5$), and produces fine-tuned rubric-scored evaluations.
</p>

<div class="grid-2">
  <div class="card">
    <div class="card-header"><span class="tag tag-blue">Feature</span> Mode A: Targeted Role Gap Analysis</div>
    <p>Upload a candidate resume and target Job Description. The system executes semantic gap analysis, calculates match percentage, identifies missing competencies, and targets questions precisely at the resume deficit.</p>
  </div>
  <div class="card">
    <div class="card-header"><span class="tag tag-purple">Feature</span> Mode B: Curriculum Mastery Tree</div>
    <p>Spans 7 core computer science subjects across 42 granular topics: <em>Data Structures & Algorithms, Operating Systems, DBMS & SQL, Computer Networks, OOP, HR & Behavioral, and Quantitative Aptitude</em>.</p>
  </div>
</div>

<div class="grid-2">
  <div class="card">
    <div class="card-header"><span class="tag tag-green">Speech</span> Sub-Second Voice Pipeline</div>
    <p>Groq Whisper <code>whisper-large-v3-turbo</code> with domain technical vocabulary conditioning (<800ms STT) coupled with zero-latency browser Web Speech synthesis.</p>
  </div>
  <div class="card">
    <div class="card-header"><span class="tag tag-blue">Execution</span> Multi-Language Sandbox & Verifier</div>
    <p>Monaco Code Editor with sandboxed local compilation (Python, JS, C++, Java, C, SQL) + dedicated AI logic engine for algorithmic pseudocode validation.</p>
  </div>
</div>

<!-- SECTION 2: SYSTEM ARCHITECTURE -->
<div class="page-break"></div>
<h1>2. System Architecture & Agent State Machine</h1>

<h2>2.1 The Multi-Step Agent Loop (Planner → Executor → Critic)</h2>
<p>
AdaptIQ rejects the architecture of thin LLM wrappers. Instead, the backend orchestrator implements an explicit <strong>Planner → Executor → Critic</strong> state machine with persistent session memory:
</p>

<div class="callout">
  <div class="callout-title">The Three-Phase Turn Execution Loop</div>
  <ul>
    <li><strong>Phase 1: The Planner</strong> — Evaluates the active session state object (`turns_taken`, `current_difficulty`, `topic_scores`, `covered_topics`, `weak_topics`). Computes next difficulty level using mathematical rubric bounds and decides whether to probe deeper or reinforce prerequisites.</li>
    <li><strong>Phase 2: The Executor</strong> — Formulates the next question using <strong>3-Way Blended Retrieval-Augmented Generation (RAG)</strong>. Chooses mode between Spoken Conceptual Question (Voice Call UI) or Coding Challenge (Monaco Code Editor).</li>
    <li><strong>Phase 3: The Critic (Fine-Tuned Evaluator)</strong> — Inspects the candidate's audio transcript or submitted code, applies a 4-rubric scoring tensor, sanity-checks for positive sycophancy, and updates persistent PostgreSQL records.</li>
  </ul>
</div>

<h2>2.2 Dynamic Difficulty Scaling Mathematics</h2>
<p>
Question difficulty ranges on a discrete integer scale: $D \in \{1, 2, 3, 4, 5\}$. After each answer turn, the Critic produces a weighted composite score $S \in [0, 100]$ across four rubrics:
</p>
<pre>
S = (0.35 * Technical_Accuracy) + (0.25 * Clarity_Communication) + 
    (0.20 * Completeness_Invariants) + (0.20 * Depth_Tradeoffs)
</pre>

<p>The state machine applies deterministic scaling rules:</p>
<table>
  <thead>
    <tr>
      <th>Candidate Score Range</th>
      <th>State Machine Action</th>
      <th>Architectural Rationale</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>$S \ge 80\%$ (High Mastery)</strong></td>
      <td>$$\text{Difficulty} = \min(5, D + 1)$$</td>
      <td>The candidate demonstrated strong mastery. Escalate difficulty to probe deeper algorithmic edge cases, system trade-offs, and scalability.</td>
    </tr>
    <tr>
      <td><strong>$60\% \le S < 80\%$ (Competent)</strong></td>
      <td>$$\text{Difficulty} = D$$ (Hold Constant)</td>
      <td>The candidate is on track but has minor gaps. Hold difficulty level constant and introduce a lateral question to reinforce conceptual clarity.</td>
    </tr>
    <tr>
      <td><strong>$S < 60\%$ (Struggling)</strong></td>
      <td>$$\text{Difficulty} = \max(1, D - 1)$$</td>
      <td>Candidate experienced failure. Gracefully decrease difficulty, flag the topic into the persistent <code>weak_topic_profile</code>, and test foundational concepts.</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 3: RAG & FINE-TUNED LORA EVALUATOR -->
<div class="page-break"></div>
<h1>3. 3-Way Blended RAG & Fine-Tuned LoRA Evaluator</h1>

<h2>3.1 The 3-Way Blended RAG Engine</h2>
<p>
To prevent questions from being purely theoretical, repetitive, or generic, AdaptIQ uses a balanced <strong>40% / 30% / 30%</strong> sourcing algorithm:
</p>
<ul>
  <li><strong>40% Textbook PDF RAG (pgvector):</strong> Sourced from chunked textbook PDFs across the 7 CS disciplines stored as dense semantic vector embeddings. Cosine similarity retrieves domain-grounded context.</li>
  <li><strong>30% Curated Seed Question Bank:</strong> Hand-curated, difficulty-calibrated corporate interview questions (FAANG / Tier-1 benchmarks) seeded into the PostgreSQL database.</li>
  <li><strong>30% Parametric LLM Knowledge:</strong> Real-time Groq LLaMA-3.3-70B generation conditioned on candidate resume deficits and situational interview scenarios.</li>
</ul>

<h2>3.2 Fine-Tuned PEFT / LoRA Answer Evaluator</h2>
<p>
A major challenge with commercial LLMs is <em>sycophancy bias</em> (the tendency to praise flawed candidate responses to sound polite). AdaptIQ solves this with an instruction-tuned PEFT/LoRA adapter trained specifically on technical interview rubrics.
</p>

<table>
  <thead>
    <tr>
      <th>Evaluation Dimension</th>
      <th>Weight</th>
      <th>Criteria & Rubric Guidelines</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Technical Accuracy</strong></td>
      <td>35%</td>
      <td>Correctness of algorithms, data structure selection, Big-O analysis, time/space trade-offs, and conceptual accuracy.</td>
    </tr>
    <tr>
      <td><strong>Clarity & Verbal Communication</strong></td>
      <td>25%</td>
      <td>Structure of thought, articulation of problem understanding, avoiding filler language, concise technical nomenclature.</td>
    </tr>
    <tr>
      <td><strong>Completeness & Invariants</strong></td>
      <td>20%</td>
      <td>Handling of boundary conditions, null references, edge cases, loop invariants, and corner inputs.</td>
    </tr>
    <tr>
      <td><strong>Depth & Architectural Trade-offs</strong></td>
      <td>20%</td>
      <td>Exploration of alternative designs, hardware caching implications, thread-safety, indexing trade-offs, and scalability.</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 4: CODE RUNNER & PSEUDOCODE VERIFIER -->
<div class="page-break"></div>
<h1>4. Sandboxed Code Execution & AI Pseudocode Verifier</h1>

<h2>4.1 Multi-Language Execution Sandbox</h2>
<p>
The platform provides a dual-mode coding environment featuring an embedded <strong>Monaco Code Editor</strong> (the editor powering VS Code) coupled with an isolated local subprocess execution sandbox:
</p>
<ul>
  <li><strong>Supported Languages:</strong> Python 3, JavaScript (Node.js), C++ (g++), Java (javac/java), C (gcc), and SQL.</li>
  <li><strong>Process Isolation:</strong> Subprocesses execute in isolated temporary scratch directories with standard input/output streaming.</li>
  <li><strong>Safety Timeout Guard:</strong> A hard <strong>4.0-second execution timeout</strong> terminates infinite loops, memory leaks, and malicious scripts automatically.</li>
</ul>

<h2>4.2 AI Pseudocode Logic Verifier</h2>
<p>
Standard compilers (like <code>g++</code> or <code>javac</code>) immediately fail on pseudocode due to syntax errors (e.g. <code>head &lt;- nextNode</code> or <code>WHILE list NOT empty</code>). AdaptIQ implements a specialized <strong>Pseudocode Logic Verification Engine</strong> powered by LLaMA-3.3-70B:
</p>
<pre>
Candidate Pseudocode ───► [AST & Logic Parser] ───► [Trace Dry-Run Simulation]
                                                            │
    ┌───────────────────────────────────────────────────────┴───────────────────────┐
    ▼                                                                               ▼
[Pointer & State Invariant Checks]                                     [Big-O Complexity Audit]
    │                                                                               │
    └───────────────────────► [Clean ASCII Terminal Feedback] ◄────────────────────┘
</pre>

<p>
The verifier conducts a step-by-step dry-run trace (e.g. <code>1 -> 2 -> 3 -> null</code>), verifies pointer integrity (checking for orphan nodes or cyclic references), validates Big-O time and space complexity, and streams formatted output directly to the candidate's terminal without compiler syntax rejections.
</p>

<!-- SECTION 5: COMPLETE TECH STACK -->
<div class="page-break"></div>
<h1>5. Technology Stack & API Architecture</h1>

<h2>5.1 Full-Stack Technology Matrix</h2>
<table>
  <thead>
    <tr>
      <th>Layer</th>
      <th>Technology / Tool</th>
      <th>Purpose & Justification</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Frontend UI</strong></td>
      <td>React 19 + Vite</td>
      <td>Blazing fast single-page application with modular component architecture, sub-second HMR, and optimized production builds.</td>
    </tr>
    <tr>
      <td><strong>Code Editor</strong></td>
      <td>@monaco-editor/react</td>
      <td>Industry-standard VS Code editor core with multi-language syntax highlighting, line numbers, and theme integration.</td>
    </tr>
    <tr>
      <td><strong>Data Viz</strong></td>
      <td>Recharts</td>
      <td>Interactive analytics dashboards, score progression line charts, and subject mastery percentage radars.</td>
    </tr>
    <tr>
      <td><strong>Backend Framework</strong></td>
      <td>FastAPI (Python 3.11)</td>
      <td>High-concurrency async ASGI framework with automated OpenAPI validation and sub-millisecond route latency.</td>
    </tr>
    <tr>
      <td><strong>ORM & Migration</strong></td>
      <td>SQLAlchemy 2.0</td>
      <td>Robust relational persistence with connection pooling, declarative models, and automatic fallback drivers.</td>
    </tr>
    <tr>
      <td><strong>Cloud Database</strong></td>
      <td>PostgreSQL 16 (Neon)</td>
      <td>Serverless cloud PostgreSQL with auto-scaling compute, persistent storage, and native <code>pgvector</code> extension.</td>
    </tr>
    <tr>
      <td><strong>LLM Reasoning</strong></td>
      <td>Groq LLaMA-3.3-70B</td>
      <td>Ultra-low latency inference (300+ tokens/sec) for real-time question generation, pseudocode verification, and answer scoring.</td>
    </tr>
    <tr>
      <td><strong>Voice Layer</strong></td>
      <td>Groq Whisper v3 Turbo</td>
      <td>Sub-800ms speech-to-text with domain technical vocabulary conditioning hints.</td>
    </tr>
    <tr>
      <td><strong>Speech Synthesis</strong></td>
      <td>Web Speech API</td>
      <td>Browser-native text-to-speech with 0ms network latency and zero recurring API costs.</td>
    </tr>
    <tr>
      <td><strong>Hosting</strong></td>
      <td>Vercel + Render</td>
      <td>Global Edge CDN distribution for React frontend + auto-scaling Linux container service for FastAPI backend.</td>
    </tr>
  </tbody>
</table>

<h2>5.2 Core API Endpoints Reference</h2>
<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Method</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>/api/v1/auth/signup</code></td>
      <td>POST</td>
      <td>Registers candidate credentials, hashes passwords via Bcrypt, and issues signed JWT access tokens.</td>
    </tr>
    <tr>
      <td><code>/api/v1/auth/login</code></td>
      <td>POST</td>
      <td>Authenticates credentials and returns OAuth2 Bearer token.</td>
    </tr>
    <tr>
      <td><code>/api/v1/jd/gap-analysis</code></td>
      <td>POST</td>
      <td>Executes cosine similarity between candidate resume and target JD; returns missing skills matrix.</td>
    </tr>
    <tr>
      <td><code>/api/v1/session/start</code></td>
      <td>POST</td>
      <td>Initializes interview state machine, loads topic profiles, and sets initial difficulty.</td>
    </tr>
    <tr>
      <td><code>/api/v1/session/{id}/current-question</code></td>
      <td>GET</td>
      <td>Retrieves active turn question, question type (coding/conceptual), and starter boilerplate.</td>
    </tr>
    <tr>
      <td><code>/api/v1/session/{id}/answer</code></td>
      <td>POST</td>
      <td>Submits candidate voice transcript or code, triggers Critic rubric evaluation, and scales difficulty.</td>
    </tr>
    <tr>
      <td><code>/api/v1/session/run-code</code></td>
      <td>POST</td>
      <td>Routes submission to isolated local compiler or AI pseudocode logic verifier.</td>
    </tr>
    <tr>
      <td><code>/api/v1/voice/transcribe</code></td>
      <td>POST</td>
      <td>Streams raw WebM audio bytes to Groq Whisper v3 Turbo with CS vocabulary hints.</td>
    </tr>
    <tr>
      <td><code>/api/v1/analytics/dashboard</code></td>
      <td>GET</td>
      <td>Aggregates user session history, average scores, and top 12 priority weak-topic heatmap.</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 6: DATABASE SCHEMA -->
<div class="page-break"></div>
<h1>6. Database Schema & Entity Relationships</h1>

<p>
The database architecture is implemented in PostgreSQL using SQLAlchemy ORM. All entities adhere to third normal form (3NF) with foreign key constraints, automated cascade deletions, and timestamp auditing:
</p>

<table>
  <thead>
    <tr>
      <th>Table Name</th>
      <th>Primary Key</th>
      <th>Key Attributes & Relationships</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong><code>users</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>email</code>, <code>hashed_password</code>, <code>full_name</code>, <code>created_at</code>. Relates to resumes, sessions, and weak topic profiles.</td>
    </tr>
    <tr>
      <td><strong><code>resumes</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>user_id</code> (FK), <code>file_name</code>, <code>raw_text</code>, <code>parsed_skills</code> (JSONB), <code>experience_years</code>.</td>
    </tr>
    <tr>
      <td><strong><code>job_descriptions</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>title</code>, <code>company</code>, <code>raw_text</code>, <code>extracted_skills</code> (JSONB), <code>experience_level</code>.</td>
    </tr>
    <tr>
      <td><strong><code>sessions</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>user_id</code> (FK), <code>mode</code> (A/B), <code>current_difficulty</code> (1-5), <code>turns_taken</code>, <code>max_turns</code>, <code>state_json</code> (JSONB).</td>
    </tr>
    <tr>
      <td><strong><code>questions</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>session_id</code> (FK), <code>turn_number</code>, <code>topic_id</code>, <code>difficulty</code>, <code>question_type</code>, <code>question_text</code>.</td>
    </tr>
    <tr>
      <td><strong><code>answers</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>question_id</code> (FK), <code>transcript</code>, <code>code_content</code>, <code>code_language</code>, <code>answer_mode</code>, <code>duration_seconds</code>.</td>
    </tr>
    <tr>
      <td><strong><code>evaluations</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>answer_id</code> (FK), <code>score_percentage</code>, <code>rubric_scores</code> (JSONB), <code>strengths</code> (JSONB), <code>improvements</code> (JSONB), <code>feedback</code>.</td>
    </tr>
    <tr>
      <td><strong><code>weak_topic_profile</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>user_id</code> (FK), <code>topic_id</code> (FK), <code>running_score</code> (EMA float), <code>attempts_count</code>, <code>last_tested_at</code>.</td>
    </tr>
    <tr>
      <td><strong><code>pdf_chunks</code></strong></td>
      <td><code>id</code> (UUID)</td>
      <td><code>subject_id</code>, <code>source_filename</code>, <code>chunk_text</code>, <code>embedding</code> (vector/dense array).</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 7: VIVA DEFENSE & TECHNICAL FAQS -->
<div class="page-break"></div>
<h1>7. Comprehensive Viva & Project Defense Q&A</h1>

<h3>Q1: Why is this not just a simple wrapper around OpenAI or Groq?</h3>
<p>
<strong>Answer:</strong> An LLM wrapper takes a user prompt, forwards it to an API, and displays the response. AdaptIQ is a complete autonomous agent system:
1. It maintains an explicit state machine tracking turns, topics, and difficulty.
2. It blends 3 distinct knowledge sources (vector RAG, curated question bank, and LLM).
3. It runs an isolated sandbox for 5 programming languages with memory/timeout guards.
4. It features a custom AI pseudocode logic verifier that performs step-by-step invariant traces.
5. It enforces mathematical rubric scoring with anti-sycophancy validation and long-term memory across sessions.
</p>

<h3>Q2: How does the system achieve sub-second voice latency?</h3>
<p>
<strong>Answer:</strong> Latency is minimized at every pipeline stage:
1. <strong>Speech-to-Text:</strong> Client streams audio directly as lightweight WebM Opus to Groq's LPU-accelerated Whisper v3 Turbo hardware, returning transcripts in &lt;800ms.
2. <strong>Technical Vocab Hints:</strong> Transcriptions are conditioned with a domain dictionary of 50+ CS terms, eliminating transcription errors on complex terms (e.g. "Dijkstra", "BCNF", "Mutex").
3. <strong>Text-to-Speech:</strong> The frontend synthesizes interviewer voice locally using the browser's native Web Speech API with 0ms network latency.
</p>

<h3>Q3: How are infinite loops and malicious scripts prevented in candidate code?</h3>
<p>
<strong>Answer:</strong> Subprocesses execute in temporary isolated scratch directories with redirected standard I/O streams. The Python <code>subprocess.Popen</code> runner enforces a strict <strong>4.0-second safety timeout</strong> (`wait(timeout=4.0)`). If execution exceeds 4 seconds, the operating system kills the process tree immediately (`proc.kill()`), capturing stderr and runtime metrics safely.
</p>

<h3>Q4: How does the adaptive learning loop work across sessions?</h3>
<p>
<strong>Answer:</strong> Whenever a candidate scores below 60% on a topic, the state machine logs or updates that topic in the <code>weak_topic_profile</code> table using an Exponential Moving Average (EMA):
$$\text{RunningScore}_{t} = (0.7 \times \text{RunningScore}_{t-1}) + (0.3 \times \text{CurrentScore})$$
The candidate dashboard visualizes the <strong>Top 12 Priority Targets</strong>. Future sessions automatically prioritize these flagged topics when downscaling difficulty.
</p>

<div class="callout callout-success" style="margin-top: 24px;">
  <div class="callout-title">Project Defense Conclusion</div>
  <strong>AdaptIQ</strong> demonstrates production-grade full-stack engineering, advanced AI agent orchestration, real-time multimodal voice systems, sandboxed execution security, and resilient cloud deployment.
</div>

</body>
</html>
"""

def main():
    print("Generating AdaptIQ Complete Project Documentation PDF...")
    
    html_file = os.path.abspath("temp_adaptiq_docs.html")
    pdf_dest = r"C:\Users\HP\Downloads\AdaptIQ_Complete_Project_Documentation.pdf"
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"HTML source written to {html_file}")
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    
    print(f"Using Microsoft Edge at: {edge_path}")
    
    cmd = [
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_dest}",
        html_file
    ]
    
    print("Executing headless PDF render...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(pdf_dest):
        size_kb = os.path.getsize(pdf_dest) / 1024
        print(f"SUCCESS! PDF created at: {pdf_dest} ({size_kb:.1f} KB)")
    else:
        print(f"ERROR: PDF not created. Returncode: {result.returncode}")
        print("Stderr:", result.stderr)
        
    try:
        os.remove(html_file)
    except Exception:
        pass

if __name__ == "__main__":
    main()
