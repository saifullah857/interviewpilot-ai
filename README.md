<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=24,20,12&height=220&section=header&text=InterviewPilot%20AI&fontSize=58&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=Lahore-focused%20interview%20preparation%20that%20is%20honest%20about%20its%20evidence&descAlignY=58&descSize=18" alt="InterviewPilot AI banner" width="100%"/>

<a href="https://github.com/">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1200&color=FB873F&center=true&vCenter=true&width=760&lines=Upload+your+resume.+Pick+a+Lahore+software+house.;Research+how+they+hire+%E2%80%94+with+sources.;Practice+MCQs%2C+real+code+execution+and+voice+interviews.;Get+a+scored+report+and+a+7%2F30-day+plan." alt="Typing animation" />
</a>

<br/>

![Status](https://img.shields.io/badge/status-local%20MVP-FB873F?style=for-the-badge)
![Scope](https://img.shields.io/badge/scope-Lahore%2C%20Pakistan-1f2937?style=for-the-badge)
![Backend tests](https://img.shields.io/badge/backend%20tests-524%20passed-2ea44f?style=for-the-badge)
![Frontend tests](https://img.shields.io/badge/frontend%20tests-138%20passed-2ea44f?style=for-the-badge)

![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square)
![Tavily](https://img.shields.io/badge/Tavily-research-7C3AED?style=flat-square)

**[Quick start](#-quick-start-windows)** ·
**[Problem & solution](#-the-problem-and-our-solution)** ·
**[How it works](#-how-it-works)** ·
**[Architecture](#-architecture)** ·
**[Trust & honesty](#-trust-and-honesty-rules)** ·
**[Docs](#-documentation)**

</div>

---

## ✨ What is InterviewPilot AI?

InterviewPilot AI helps **students, fresh graduates, interns and junior developers** prepare for real opportunities at **software houses and startups that have a verified office in Lahore, Pakistan**.

You upload a resume, the platform suggests the roles and Lahore companies that fit it, a research agent looks at how a chosen company hires, and you practise with **personalised questions, a real code editor that actually runs your code, and a voice interview** — then receive a transparent, evidence-labelled report.

> **It is not a generic worldwide interview app, and it never pretends practice questions are real company questions.**

---

## 🎯 The problem and our solution

| 😖 The problem | ✅ How InterviewPilot AI solves it |
|---|---|
| Interview prep is **generic** (LeetCode lists, random blogs) and ignores the company you are applying to. | **Lahore-only company directory** plus a **Research Agent** that reads the company's own website and public hiring pages. |
| Students do not know **which roles and companies fit their resume** (a web developer and an AI/ML student need different targets). | **Resume Analyst + Role Matching** rank roles by fit, then suggest companies by focus area and skill overlap. |
| Prep sites mix real and invented content, so you cannot tell what is **actually reported** by candidates. | Every item carries an **evidence label** and a source link. Generated questions are always labelled *AI-generated practice*. |
| Most platforms only show **MCQs**. Real interviews include coding and a conversation. | **Technical assessment + Monaco code editor with real execution + voice/text interview** in one flow. |
| Feedback is vague ("study more"). | **Separate scores with a visible rubric**, a skill-gap list and a **prioritised 7- or 30-day plan**. |
| AI tools fail silently when the model is slow or rate-limited. | **Retries, fallback model and a built-in practice bank** so practice is never blocked, and the screen says when the bank was used. |

```mermaid
flowchart LR
    P1["❌ Generic prep<br/>no company context"] --> S1["✅ Lahore company<br/>research with sources"]
    P2["❌ Unclear which role<br/>or company fits"] --> S2["✅ Resume-based role<br/>and company ranking"]
    P3["❌ Real vs invented<br/>questions mixed"] --> S3["✅ Evidence labels<br/>on everything"]
    P4["❌ MCQ only"] --> S4["✅ MCQ + real code run<br/>+ voice interview"]
    P5["❌ Vague feedback"] --> S5["✅ Scored report +<br/>7/30-day plan"]
    style P1 fill:#fee2e2,stroke:#ef4444,color:#000
    style P2 fill:#fee2e2,stroke:#ef4444,color:#000
    style P3 fill:#fee2e2,stroke:#ef4444,color:#000
    style P4 fill:#fee2e2,stroke:#ef4444,color:#000
    style P5 fill:#fee2e2,stroke:#ef4444,color:#000
    style S1 fill:#dcfce7,stroke:#22c55e,color:#000
    style S2 fill:#dcfce7,stroke:#22c55e,color:#000
    style S3 fill:#dcfce7,stroke:#22c55e,color:#000
    style S4 fill:#dcfce7,stroke:#22c55e,color:#000
    style S5 fill:#dcfce7,stroke:#22c55e,color:#000
```

---

## 🧭 How it works

```mermaid
journey
    title A candidate's path through InterviewPilot AI
    section Get started
      Sign up / log in: 5: Candidate
      Upload resume (PDF or DOCX): 4: Candidate
      Resume analysed into skills, projects, education: 5: Resume Analyst
    section Choose a target
      See best-fit roles for the resume: 5: Role Matching
      See ranked Lahore software houses: 5: Role Matching
      Press "Research this company": 4: Candidate, Research Agent
    section Practise
      Personalised technical assessment: 5: Assessment Agent
      Coding challenges with real execution: 5: Code Runner
      Voice or text interview with follow-ups: 5: Interview Agent
    section Improve
      Scored report and skill gaps: 5: Evaluation Service
      7 / 30-day improvement plan: 5: Candidate
```

### 1. Resume → best-fit roles and companies
The resume is parsed into a validated schema (skills, projects, education, experience). Roles are scored against your skills, then Lahore companies are ranked by **focus area** (web, frontend, backend, mobile, AI/ML, data) and **skill overlap**.

| If your resume looks like… | You will mostly be pointed to… |
|---|---|
| React, JavaScript, CSS | Frontend / Full-Stack roles and web-focused houses |
| Python, SQL, REST APIs | Backend / Python roles and backend-focused houses |
| scikit-learn, PyTorch, pandas | AI/ML and Data roles and AI-focused houses/startups |
| Flutter, Dart | Mobile roles and mobile-focused houses |

> The match percentage is a **hint, not a prediction of being hired.**

### 2. Research Agent (per company)
```mermaid
sequenceDiagram
    autonumber
    actor U as Candidate
    participant W as Web app
    participant A as API (FastAPI)
    participant R as Research Agent (LangGraph)
    participant T as Tavily search
    participant L as Groq LLM
    U->>W: Press "Research this company"
    W->>A: POST /discover/companies/{slug}/research
    A->>R: Start background run
    R->>T: Find the company's own domain
    R->>T: Search official pages (Lahore office, jobs, tech stack)
    R->>T: Search public candidate reports
    R->>L: Extract structured findings (untrusted text, injection-guarded)
    R->>A: Save findings with source URL, label, date
    A-->>W: Status and findings
    W-->>U: Lahore confirmed? plus labelled findings
```

A company is shown as **“Lahore presence confirmed”** only when a page on the company's **own website** mentions Lahore. That check is **automatic** and is labelled as such. Addresses are never invented.

### 3. Practice and report
| Stage | What you get | How it is scored |
|---|---|---|
| 📝 Technical assessment | About 20–30 MCQs, short answers and project questions | MCQs: objective. Short answers: rubric-based AI review |
| 💻 Coding | Monaco editor, visible + hidden tests, timer | **Objective** pass count from the runner (never from an LLM) |
| 🎙️ Voice / text interview | Resume- and role-based questions with follow-ups | Rubric-based AI evaluation, transcript only with consent |
| 📊 Report | Separate scores, strengths, gaps, practice questions | 7- or 30-day plan, progress over attempts |

---

## 🏷️ Trust and honesty rules

Every piece of content is labelled so you always know what you are looking at.

| Label | Meaning |
|---|---|
| 🟢 **Officially verified** | Supported by the company's official source |
| 🟡 **Public candidate report** | A public candidate experience; may be outdated and is not official |
| 🔵 **AI-generated practice** | Written for preparation; **never** claimed to be a real company question |
| ⚪ **Unverified / outdated** | Not enough evidence, or needs rechecking |

- Resume claims are **not** treated as verified facts.
- Web pages and resume text are treated as **untrusted data** (prompt-injection guarded).
- Scores are **preparation indicators**, not hiring decisions or guarantees.
- No covert surveillance; any integrity signal is transparent and best-effort.

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Browser["🌐 Browser"]
        UI["React + TypeScript + Tailwind<br/>Monaco editor · Voice UI"]
    end
    subgraph Backend["⚙️ FastAPI backend"]
        API["REST API · Auth · Ownership checks"]
        subgraph Agents["🤖 Agents (LangGraph)"]
            RA["Resume Analyst"]
            RM["Role Matching"]
            CR["Company Research"]
            AG["Assessment Generator"]
            VI["Voice / Text Interview"]
            EV["Evaluation & Report"]
        end
        BANK["Built-in practice bank<br/>(fallback)"]
    end
    DB[("🗄️ PostgreSQL / SQLite")]
    FILES[("📁 Private file storage")]
    GROQ["🧠 Groq LLM<br/>primary + fallback model"]
    TAVILY["🔎 Tavily search"]
    subgraph Runner["🧪 Separate Code Runner service"]
        LOCAL["local backend<br/>(Windows / any)"]
        BWRAP["bubblewrap backend<br/>(Linux / WSL2, stronger)"]
    end
    UI <--> API
    API --> Agents
    API <--> DB
    API <--> FILES
    Agents <--> GROQ
    CR <--> TAVILY
    AG -.->|AI slow or down| BANK
    API -->|signed HTTP request| Runner
    style Runner fill:#fff7ed,stroke:#FB873F,color:#000
    style Agents fill:#f0f9ff,stroke:#38bdf8,color:#000
```

**Key design choices**
- 🔒 User code is **never** executed inside the API process. It runs in a separate runner service; expected answers are never sent to the code that runs.
- 🛟 AI calls use short retries, a fallback model and a time budget. If the AI is still unavailable, a built-in practice bank fills the gap and the user is told.
- 🧩 Providers (LLM, search, runner) sit behind interfaces, so they can be replaced.

---

## 🚀 Quick start (Windows)

**You need:** Python 3.12+ and Node.js LTS (tick *“Add Python to PATH”* during install).

```text
1. Put your keys in apps\api\.env      (GROQ_API_KEY, LLM_MODEL_PRIMARY, TAVILY_API_KEY)
2. Double-click START.bat               (first run installs everything)
3. Open http://localhost:5173
```

`START.bat` will:
- create the Python environment and install packages (first run only),
- switch the code runner on in `.env` with a random secret (your other settings are kept),
- run database migrations and import the Lahore candidate list,
- open three windows: **Runner**, **API** and **Web**.

**Check it works:** open a coding problem. The banner should say *“Connected to the code runner (local)”*. Run the starter code (a test should fail), then a correct solution (all tests pass and a score appears).

> Full setup, WSL2 sandbox, tests, backup and troubleshooting: [`docs/SETUP_WINDOWS.md`](docs/SETUP_WINDOWS.md)

---

## 🧰 Feature checklist

| Area | Status |
|---|---|
| Sign-up, login, password change | ✅ |
| Lahore company directory (21 candidates, honest status) | ✅ |
| Resume upload (PDF/DOCX) and analysis | ✅ |
| Resume-based role and company suggestions | ✅ |
| Research Agent with source labels (user-run) | ✅ |
| AI practice assessments with built-in fallback bank | ✅ |
| Coding practice with real execution (Python) | ✅ |
| Voice and text interviews with feedback | ✅ |
| Scored reports, 7/30-day plan, progress tracking | ✅ |
| Data deletion and consent controls | ✅ |
| Verified on a real Windows machine | ⏳ please test and report |
| More coding languages | 🗓️ planned |

**Roles supported:** Python Developer · Backend Developer · Frontend Developer · Full-Stack Web Developer · Mobile App Developer · AI/ML Engineer Intern · Junior AI Engineer · Data Scientist

---

## 🛡️ Security at a glance

| Topic | Approach |
|---|---|
| Passwords & auth | Argon2 hashing, signed tokens, ownership checks on every user resource |
| Uploads | Type, size and content validation; private storage, no public URLs |
| Prompt injection | Resume and web text treated as untrusted; findings must be grounded in the source |
| Code execution | Separate runner service, one process per test, time/memory limits, hidden tests never sent to the browser |
| Secrets | Only in `.env` (git-ignored); `.env.example` has placeholders |

> ⚠️ **Runner note:** the default `local` backend is for practising on **your own machine**. It restricts time, memory and imports, but it is **not** a hardened sandbox. Do not expose port `8100`. For shared use, run the `bubblewrap` backend on Linux/WSL2.

---

## ✅ Testing

| Suite | Command | Last result |
|---|---|---|
| Backend | `cd apps/api && python -m pytest -q` | 524 passed, 78 skipped* |
| Frontend | `cd apps/web && npm run test` | 138 passed |
| Frontend quality | `npx tsc -b` · `npx eslint src` · `npx vite build` | clean |

\* The skipped tests are the Linux-only sandbox tests. They run in WSL2/Linux.
**Not yet verified:** real Windows run of `START.bat`, real browsers and microphone, and live Groq/Tavily calls.

---

## 🗂️ Project layout

```text
interviewpilot-ai/
├─ START.bat                 one-click start (runner + API + web)
├─ apps/
│  ├─ api/                   FastAPI backend, Alembic migrations, tests
│  └─ web/                   React frontend, component and route tests
├─ services/
│  └─ sandbox-runner/        separate code-runner service (local, bubblewrap, mock)
├─ data/                     company seed, role catalog, coding problem bank
├─ scripts/                  start and setup helpers
└─ docs/                     plan, decisions, contracts, rubrics, security, handover
```

---

## 📚 Documentation

| Document | Purpose |
|---|---|
| [`docs/SETUP_WINDOWS.md`](docs/SETUP_WINDOWS.md) | Step-by-step setup and troubleshooting |
| [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | What is limited or unverified |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | What changed in each release |
| [`docs/COMPANY_DATA_POLICY.md`](docs/COMPANY_DATA_POLICY.md) | Lahore eligibility, verification and source labels |
| [`docs/SCORING_RUBRICS.md`](docs/SCORING_RUBRICS.md) | How each score is computed |
| [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md) | Security review |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Modules, data flows, agent boundaries |
| [`docs/HANDOVER.md`](docs/HANDOVER.md) · [`docs/NEXT_SESSION.md`](docs/NEXT_SESSION.md) | Continue the project in a new session |

---

## ⚖️ Disclaimer

InterviewPilot AI is a **preparation tool**. Scores and recommendations are **not** guarantees of selection or hiring and have no scientific validity claim. Company information can become outdated, so always check the linked sources. Practice questions are **AI-written** and are not questions asked by any company.

Never commit `.env`, uploaded resumes, databases or transcripts; `.gitignore` covers them.

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=24,20,12&height=120&section=footer" alt="footer" width="100%"/>

**Built for Lahore's next generation of engineers 🧡**

</div>