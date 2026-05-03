# Final Year Project Defense Guide

Project: **Validator AI - AI Startup Validation Platform**

Purpose of this document: prepare you to explain, justify, demo, and defend this project to a supervisor/examiner. It is written for a live project defense where you must run the app, show the database, explain the code, and answer technical questions.

## 1. Short Opening Statement

Use this when your supervisor asks, "What is your project?"

> My project is a web-based AI startup validation platform. A user submits a startup idea, the system asks a 5-question AI interview, performs structured market and business analysis, generates a free viability report, and allows the user to upgrade to deeper reports. The backend is built with FastAPI and LangGraph, the frontend is built with React, and Supabase/PostgreSQL is used for authentication, roles, session storage, reports, realtime status updates, and LangGraph workflow checkpointing. The system supports normal users and admins, and paid reports go through an admin approval workflow before release.

If you want a shorter version:

> It is a full-stack web app that validates startup ideas using an AI-assisted workflow, stores users and reports in a database, supports user/admin roles, and produces structured startup validation reports.

## 2. How This Project Meets the Given Requirements

### Requirement 1: Should be a mobile or web app

This project is a **web app**.

Evidence in code:

- Frontend app: `frontend/`
- React entry: `frontend/src/main.tsx`
- Routes: `frontend/src/App.tsx`
- Pages:
  - `/` landing page
  - `/submit` idea submission
  - `/interview/:threadId` AI interview
  - `/report/:threadId` report view
  - `/upgrade/:threadId` tier upgrade
  - `/processing/:threadId` processing status
  - `/dashboard` user dashboard
  - `/admin` admin dashboard

Frontend stack:

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/Radix UI components
- Supabase client
- React Router

What to say:

> This is a web application because users interact through a browser-based React frontend. The backend exposes REST APIs using FastAPI, and the frontend consumes those APIs.

### Requirement 2: Should have database

This project uses a database in two ways:

1. **Supabase/PostgreSQL** for application data.
2. **Supabase/PostgreSQL LangGraph checkpointing** for backend workflow state in production.

Database usage:

- Users and authentication through Supabase Auth.
- User profiles and admin flags.
- Validation sessions.
- Interview answers.
- Reports.
- Realtime report/session status updates.

Evidence in code:

- Frontend Supabase client: `frontend/src/lib/supabase.ts`
- Backend Supabase helpers: `src/utils/supabase.py`
- Backend settings: `src/config/settings.py`
- LangGraph Supabase/PostgreSQL checkpointer: `src/graph/workflow.py`
- Docker Postgres service: `docker-compose.yml`

Important frontend tables used:

- `profiles`
- `validation_sessions`
- `interview_answers`
- `reports`

What to say:

> The project uses Supabase, which is a managed PostgreSQL database with authentication and realtime features. The application stores user sessions, submitted ideas, interview answers, reports, user roles, and report statuses. The backend also uses Supabase/PostgreSQL checkpointing through LangGraph's `AsyncPostgresSaver` to persist workflow state.

### Requirement 3: Should have multi-role users

The project supports at least two roles:

- **User**
- **Admin**

User role:

- Can sign in/sign up.
- Can submit startup ideas.
- Can answer interview questions.
- Can view own dashboard.
- Can view generated reports.
- Can request upgraded reports.

Admin role:

- Can access admin dashboard.
- Can view reports waiting for approval.
- Can preview generated paid reports.
- Can save edits.
- Can approve and release reports.

Evidence in code:

- Auth context: `frontend/src/contexts/AuthContext.tsx`
- Protected route wrapper: `frontend/src/components/ProtectedRoute.tsx`
- Admin dashboard: `frontend/src/pages/AdminDashboard.tsx`
- Admin backend endpoints:
  - `POST /admin/save/{thread_id}`
  - `POST /admin/approve/{thread_id}`
- Admin check helper: `src/utils/supabase.py` function `is_user_admin`
- Backend extracts user ID: `src/api/routes.py` function `get_user_id_from_request`

What to say:

> The project implements multi-role behavior through Supabase profiles. A normal user can submit and view their own validation sessions. Admin users have an `is_admin` flag and can access the admin review queue to approve reports.

Honest limitation:

> In the current backend, JWT verification is simplified for academic/demo purposes. The frontend passes the Supabase token and `X-User-Id`, but full server-side JWT verification is marked as a future improvement.

This is important because if the examiner asks about security, you should be honest and say you know the current limitation.

### Requirement 4: Should not use external APIs, or justify them properly

This project does use external APIs, and you must justify them clearly.

External APIs/services used:

- OpenAI-compatible LLM API
- Tavily Search API
- Supabase API
- Optional webhook endpoint

Justification:

- The core academic objective is to demonstrate an AI-assisted startup validation workflow.
- LLM APIs are used for natural language reasoning, report generation, structured output, and interview questions.
- Tavily is used only for research/search data because the system needs current market information.
- Supabase is used as a database/auth platform. It is not just an API dependency; it is the database backend for the project.
- The webhook is used for report delivery/persistence integration and can be disabled or mocked for local demo if needed.

What to say:

> The project uses external APIs because the project domain requires AI reasoning and live research. If we removed external APIs, the project would still be a web app with database and roles, but the AI validation quality would be reduced to static templates. I have separated the API usage into service/helper layers, so it can be mocked, replaced, or disabled for testing and demo mode.

How to defend external APIs:

- OpenAI-compatible LLM:
  - Used for generating structured business analysis.
  - Wrapped inside `LLMService`, not scattered randomly.
  - Outputs are validated with Pydantic schemas.
  - Retries and fallbacks are handled.

- Tavily:
  - Used for current market research.
  - Search results are credibility-scored and filtered.
  - It supports startup validation because market/competitor data changes frequently.

- Supabase:
  - Used as database/auth/realtime infrastructure.
  - Stores actual project data.
  - Supports multi-role users.

- Webhook:
  - Used to send final report data to an external persistence/notification flow.
  - Non-critical to the conceptual workflow.

Possible examiner question:

> Could this project run without external APIs?

Answer:

> Partially, yes. The frontend, authentication, roles, database, dashboard, and report rendering can still run. For AI generation and live research, I would need either local models and a local search dataset, or mock data. The frontend already has a mock mode through `VITE_USE_MOCK_API=true`, and the LLM/search logic is isolated enough to replace with local implementations later.

### Requirement 5: Student should be able to explain everything used

This document gives you explanations for:

- Web app architecture.
- Database usage.
- Multi-role users.
- APIs and why they are used.
- AI agents.
- LangGraph workflow.
- Tools.
- Research layer.
- Scoring.
- Report generation.
- Admin approval.
- Frontend flow.
- Backend routes.
- Security limitations.

## 3. Best Live Demo Flow

Do not start by opening code. Start by showing the running app, then explain the code behind each action.

### Demo Preparation Before Meeting

Do these before going to supervisor:

1. Make sure backend `.env` exists.
2. Make sure frontend `.env` or `.env.local` has Supabase and API URL values.
3. Confirm Supabase project is reachable.
4. Confirm at least one normal user account exists.
5. Confirm at least one admin account exists with `is_admin = true`.
6. Prepare one short startup idea for quick demo.
7. Prepare one already-generated report in the database in case live AI generation is slow.
8. Keep backend terminal and frontend terminal ready.
9. Keep Supabase dashboard open if internet is available.
10. Keep code editor open at important files.

Recommended demo idea:

> An AI-powered platform for small restaurants that predicts food demand, reduces waste, and suggests daily purchasing quantities based on sales history, weather, and local events.

This idea is easy to explain and has clear market, customer, financial, and technical aspects.

### Terminal Commands

Backend:

```bash
cd validator-ai
uv run uvicorn app:app --reload --port 8000
```

Frontend:

```bash
cd validator-ai/frontend
npm run dev
```

Open:

- Backend docs: `http://127.0.0.1:8000/docs`
- Frontend: usually `http://localhost:5173`

If the backend needs database checkpointing instead of memory:

```bash
docker compose up --build
```

For the final defense, explain that Supabase/PostgreSQL is the intended persistent saver. `USE_MEMORY_SAVER=true` was only a convenience option for local testing if the database/checkpointer setup is not available.

### Live Demo Script

#### Part 1: Show Web App

1. Open frontend.
2. Sign in as normal user.
3. Go to dashboard.
4. Click new research or submit page.
5. Submit the startup idea.
6. Show that the app moves to interview.
7. Answer the 5 interview questions.
8. Show free report page.
9. Explain viability score and report sections.

What to say:

> This demonstrates the user role. The user submits an idea, answers the 5-question AI interview, and receives a free report generated by the backend workflow.

#### Part 2: Show Upgrade Flow

1. Click upgrade.
2. Choose Standard or Basic.
3. Show processing page.
4. Explain that paid generation runs in background.
5. If live generation is slow, open an existing completed report.

What to say:

> Paid reports are generated asynchronously. The frontend monitors Supabase realtime updates and polls as fallback. This is why the user sees a processing screen instead of waiting on one long HTTP request.

#### Part 3: Show Admin Role

1. Sign in as admin or open admin route.
2. Show admin dashboard.
3. Show pending approval sessions if available.
4. Open report preview.
5. Explain save/approve.

What to say:

> The admin role exists because paid reports should be reviewed before release. The backend pauses the LangGraph workflow before `admin_approve`, and the admin endpoint resumes it.

#### Part 4: Show Database

Open Supabase dashboard and show:

- `profiles`: user role/admin flag.
- `validation_sessions`: submitted startup idea and status.
- `interview_answers`: stored answers.
- `reports`: generated report JSON and score.

What to say:

> This proves the app has a real database. The database stores users, roles, session state, answers, and generated reports.

#### Part 5: Show Backend Code

Open these files in order:

1. `src/api/routes.py`
   - Show `/submit`, `/answer`, `/upgrade`, `/report`, `/admin/approve`.

2. `src/graph/workflow.py`
   - Show LangGraph nodes and routing.

3. `src/models/inputs.py`
   - Show `ValidationState`.

4. `src/models/outputs.py`
   - Show report schemas.

5. `src/agents/base.py`
   - Show `LLMService`.

6. `src/agents/free_tier.py`
   - Show free report generation.

7. `src/agents/parallel_executor.py`
   - Show parallel module execution.

8. `src/agents/compiler.py`
   - Show final report compilation and admin approval.

9. `src/utils/scoring.py`
   - Show deterministic weighted scoring.

What to say:

> The backend is not one big function. It is divided into API routes, graph workflow, agents, schemas, utility functions, and integrations.

#### Part 6: Show Frontend Code

Open:

1. `frontend/src/App.tsx`
   - Routes.

2. `frontend/src/lib/api.ts`
   - API calls.

3. `frontend/src/lib/supabase.ts`
   - Database helpers.

4. `frontend/src/contexts/AuthContext.tsx`
   - Login/session/admin flag.

5. `frontend/src/pages/Submit.tsx`
   - Idea submit UI.

6. `frontend/src/pages/Report.tsx`
   - Report rendering.

7. `frontend/src/pages/AdminDashboard.tsx`
   - Admin role.

## 4. Architecture Explanation

### System Diagram in Words

User browser:

> React frontend

talks to:

> FastAPI backend

which runs:

> LangGraph workflow

which calls:

> AI agents, Tavily research, scoring utilities, Supabase, webhook

and stores:

> users, sessions, answers, reports, roles, and statuses in Supabase/PostgreSQL

### Why Separate Frontend and Backend?

Answer:

> The frontend handles user interaction, routing, authentication state, and report visualization. The backend handles trusted processing: workflow state, AI calls, scoring, research, and admin approval. This separation is standard for web applications and makes the project easier to maintain.

### Why FastAPI?

Answer:

> FastAPI is a modern Python web framework. It supports async endpoints, automatic Swagger documentation, Pydantic validation, and works well with AI workflows where many operations are asynchronous, such as LLM calls and web research.

### Why React?

Answer:

> React is used for building a dynamic web UI with multiple pages, protected routes, dashboards, realtime status updates, and reusable components.

### Why Supabase?

Answer:

> Supabase provides PostgreSQL database, authentication, role/profile storage, and realtime subscriptions. It helped me implement the database and multi-role requirement faster while still using a real relational database.

### Why LangGraph?

Answer:

> This project is not a simple one-step API call. It has multiple stages: submit idea, pause for interview answer, generate free report, pause for upgrade, run paid analysis, pause for admin approval, and then release. LangGraph is useful because it models this as a stateful workflow with nodes, edges, conditional routing, checkpoints, and resumability.

## 5. AI Agents Explanation

### What is an AI Agent in This Project?

An AI agent here is a specialized function/node that uses an LLM and tools/context to perform one responsibility in the workflow.

Examples:

- Interviewer agent asks clarifying questions.
- Researcher agent synthesizes answers and market context.
- Free tier agent creates a free viability report.
- Basic tier agent creates a Business Model Canvas and Go/No-Go report.
- Standard module agents create market, competitor, finance, tech, regulatory, GTM, risk, roadmap, and funding analysis.
- Compiler agent combines modules, checks consistency, calculates final score, and builds the final report.

Important point:

> In this codebase, agents are implemented as Python async functions connected inside LangGraph. They are not separate servers.

### Agent Files

- `src/agents/interviewer.py`
- `src/agents/researcher.py`
- `src/agents/free_tier.py`
- `src/agents/basic_tier.py`
- `src/agents/standard_modules.py`
- `src/agents/parallel_executor.py`
- `src/agents/compiler.py`
- `src/agents/quality_checker.py`

### Why Use Multiple Agents?

Answer:

> Startup validation has multiple domains. Market analysis, financial modeling, technical feasibility, regulatory compliance, and GTM strategy require different prompts and output schemas. Splitting them into specialized agents makes the system modular and easier to test, improve, and explain.

### What is the Strategic Directive?

The Strategic Directive is a shared truth document generated before deeper analysis.

It defines:

- Target customer segment.
- Pricing strategy.
- Core value proposition.
- Strategic constraints.
- Differentiation strategy.
- Year 1 goals.
- Primary metric.

Why it exists:

> If 10 modules run in parallel, they might make different assumptions. The Strategic Directive gives them common assumptions so the final report is more consistent.

## 6. Workflow Explanation

The workflow is in `src/graph/workflow.py`.

### Nodes

- `interviewer`
- `process_answer`
- `research`
- `free_scan`
- `basic_gen`
- `parallel_modules`
- `compiler`
- `admin_approve`

### Flow

1. User submits idea.
2. `interviewer` asks up to 5 clarification questions.
3. Graph stops and waits for each user answer.
4. User submits each answer.
5. `process_answer` resumes graph after each answer.
6. `interviewer` completes interview after enough information is collected or the 5-question limit is reached.
7. `research` enriches context.
8. If free tier, `free_scan` creates free report and stops.
9. If upgraded to basic, `basic_gen` creates basic report.
10. If upgraded to standard/premium/custom, `parallel_modules` runs selected modules.
11. `compiler` compiles final paid report.
12. Graph pauses before `admin_approve`.
13. Admin approves.
14. Report is released.

### Why the Workflow Pauses

The workflow pauses because:

- It needs user answers during the 5-question interview.
- It needs user choice/payment/upgrade after free report.
- It needs admin review before paid report release.

What to say:

> LangGraph is useful because workflows can pause and resume using the same `thread_id`.

## 7. Research and Tools Explanation

### What Does "Research" Mean Here?

Research means the backend gathers external context about the startup idea, such as:

- Market demand.
- Competitors.
- Trends.
- Regulatory context.
- Scalability indicators.
- Funding environment.

### How Research Works

Files:

- `src/agents/search/research.py`
- `src/agents/search/query_generator.py`
- `src/agents/search/credibility.py`
- `src/agents/search/topics.py`
- `src/agents/search/strategy.py`

Steps:

1. Extract industry/geography from user idea.
2. Generate search objectives.
3. Generate search queries.
4. Search using Tavily.
5. Score source credibility.
6. Filter and deduplicate results.
7. Pass research context to report agents.

### What is Tavily?

Tavily is a search API designed for AI applications. It returns web search results that can be used as context for LLM-based analysis.

Justification:

> Startup validation needs current market and competitor information. Static hardcoded data would quickly become outdated. Tavily is used only for research context, and its outputs are filtered and summarized before being used.

### What are Tools?

In this project, tools are service integrations used by agents:

- LLM call tool through `LLMService`.
- Tavily search tool.
- Supabase database helper functions.
- Webhook delivery helper.
- Scoring utility functions.

## 8. Harness Explanation

If your supervisor asks "What is harness?" explain it like this:

> A harness is the surrounding structure that runs, coordinates, and validates components. In this project, the LangGraph workflow acts like an execution harness for agents because it controls which agent runs next, what state is passed, when to pause, and how to resume. The tests also act as a test harness because they run isolated parts of the system and verify outputs.

Where harness-like behavior exists:

- LangGraph workflow: `src/graph/workflow.py`
- LLM wrapper: `src/agents/base.py`
- Tests: `tests/`
- Frontend API wrapper: `frontend/src/lib/api.ts`

## 9. Structured Outputs and Pydantic

### Why Pydantic?

LLMs can return messy or invalid JSON. Pydantic defines strict schemas and validates data.

Examples:

- `FreeReportOutput`
- `BasicReportOutput`
- `ViabilityScores`
- `GoNoGoScores`
- `StrategicDirective`
- `InvestorPitchDeck`
- Market, competitor, finance, tech, regulatory, GTM, risk, roadmap, and funding schemas.

What to say:

> Pydantic makes AI output safer because the frontend expects predictable fields. If the LLM returns wrong types or invalid values, validation catches it.

## 10. Scoring Explanation

File: `src/utils/scoring.py`

### Free Viability Score

It uses 5 dimensions:

- Problem severity: 30%
- Market opportunity: 25%
- Competition intensity: 20%
- Execution complexity: 15%
- Founder alignment: 10%

Competition and execution complexity are inverted because high competition and high complexity are negative.

Answer:

> The LLM gives dimension-level scores, but the final score is calculated using deterministic weights. This makes the result explainable and testable.

### Paid Go/No-Go Score

It uses 8 dimensions:

- Market demand: 25%
- Financial viability: 20%
- Competition analysis: 15%
- Founder-market fit: 10%
- Technical feasibility: 10%
- Regulatory compliance: 10%
- Timing assessment: 5%
- Scalability potential: 5%

Answer:

> Paid scoring is more detailed because it includes financial, technical, regulatory, timing, and scalability dimensions.

## 11. Admin Approval Explanation

Paid reports pause before admin approval.

Why:

- Human-in-the-loop review.
- Academic quality assurance.
- Admin can inspect and save edits.
- Report is released only after approval.

Code:

- Graph interrupt: `interrupt_before=["admin_approve"]`
- Admin route: `POST /admin/approve/{thread_id}`
- Admin save route: `POST /admin/save/{thread_id}`
- Frontend page: `frontend/src/pages/AdminDashboard.tsx`

What to say:

> This shows role-based workflow control. Normal users cannot approve reports; only admins can release paid reports.

## 12. Security Explanation

### What Security Exists?

- Protected frontend routes.
- Supabase authentication.
- User sessions.
- Admin flag in profile.
- Backend checks admin status before admin actions.
- Rate limiting middleware.
- Global exception handling.
- CORS settings.

Files:

- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/components/ProtectedRoute.tsx`
- `src/api/middleware.py`
- `src/utils/supabase.py`

### Honest Security Limitation

The backend currently does simplified auth:

- It reads `Authorization` header.
- It also reads `X-User-Id`.
- There is a TODO for proper Supabase JWT verification.

Best answer:

> For academic scope, I implemented role-based access and admin checks, but a production version should verify the Supabase JWT server-side instead of trusting `X-User-Id`. I am aware of this and listed it as a future improvement.

## 13. External API Justification in Detail

### OpenAI-Compatible LLM API

Used for:

- Interview question generation.
- Context synthesis.
- Structured report generation.
- Strategic Directive.
- Scoring dimensions.
- Executive summary.
- Pitch deck.

Why needed:

> The main goal is AI-assisted startup validation. An LLM is needed for reasoning over unstructured founder input and generating structured business analysis.

How controlled:

- Centralized in `LLMService`.
- Uses Pydantic validation.
- Uses retries.
- Uses JSON parsing fallback.
- Uses deterministic scoring after dimension scores.

### Tavily Search API

Used for:

- Market research.
- Competitor context.
- Trends.
- Regulatory/scalability signals.

Why needed:

> Startup validation depends on recent market information. Tavily provides current web research, while the project adds query generation, credibility scoring, and structured analysis on top.

### Supabase

Used for:

- Database.
- Authentication.
- Roles.
- Realtime status.

Why justified:

> Supabase provides the required database and authentication layer. It is still PostgreSQL underneath, and the code shows how tables are used.

### Webhook

Used for:

- Sending final report payload externally.
- Updating/persisting report metadata through an external endpoint.

Why justified:

> It decouples report generation from report delivery/persistence notification. For demo, it can be mocked or replaced.

## 14. Known Limitations You Should Mention Only If Asked

Do not open with these, but be ready.

1. The final interview flow is 5 questions. A 1-question setting was only a temporary testing shortcut, and older 10-question frontend copy came from an earlier iteration.
2. Provider names like `claude` are passed, but current `LLMService` selects models by `use_complex`, not actual provider routing.
3. Some older docs/tests refer to Claude/Opus/Sonnet/Haiku architecture that is not fully implemented in current code.
4. Dockerfile uses Python 3.12, but `pyproject.toml` requires Python 3.13+.
5. Full backend JWT verification should be added for production.
6. `WEBHOOK_URL` is required at import time, which can make local setup stricter.
7. Some tests/verification scripts appear stale relative to the current code.

Good way to phrase:

> These are implementation gaps I identified during review. They do not invalidate the main project requirements, but they are important future improvements before production deployment.

## 15. Examiner-Style Questions and Answers

### Q1. What is the main contribution of your project?

Answer:

> The main contribution is a complete AI-assisted startup validation workflow integrated into a full-stack web application. It combines user submission, AI interview, live research, structured report generation, deterministic scoring, database persistence, role-based access, and admin approval.

### Q2. Is this only a ChatGPT wrapper?

Answer:

> No. The LLM is one component. The project also has a web frontend, FastAPI backend, LangGraph workflow, Supabase database, user/admin roles, structured Pydantic schemas, deterministic scoring, research pipeline, report persistence, realtime status tracking, and admin approval. The LLM does not directly control the whole app; it is called inside controlled agents.

### Q3. What is an agent?

Answer:

> An agent is a specialized function in the backend that uses an LLM and context to perform one task. For example, the interviewer asks questions, the researcher gathers context, standard module agents generate specific report sections, and the compiler combines everything into the final report.

### Q4. Why did you use LangGraph?

Answer:

> I used LangGraph because the process is stateful and multi-step. It needs to pause for user answers, resume after upgrade, route based on tier, run modules in parallel, and pause before admin approval. LangGraph gives nodes, conditional edges, state, checkpointing, and resumability.

### Q5. Where is the database used?

Answer:

> Supabase/PostgreSQL stores user profiles, admin flags, validation sessions, interview answers, reports, and report statuses. LangGraph uses Supabase/PostgreSQL checkpointing through `AsyncPostgresSaver` to persist workflow state.

### Q6. How do you implement multi-role users?

Answer:

> Users authenticate through Supabase. The `profiles` table contains an `is_admin` flag. Normal users can submit and view their own reports. Admins can access the admin dashboard and approve reports through protected backend endpoints.

### Q7. Why are external APIs used?

Answer:

> They are used because the project's core feature is AI-assisted validation and current market research. LLM APIs provide reasoning and structured report generation, Tavily provides current web research, and Supabase provides database/auth. Their usage is centralized and justified by the project requirements.

### Q8. How do you prevent bad AI output?

Answer:

> I use Pydantic schemas for structured outputs, JSON parsing and repair fallback, deterministic scoring functions, consistency checks across modules, and admin approval before paid reports are released.

### Q9. How is the score calculated?

Answer:

> The LLM generates dimension-level scores. Then the backend calculates the final score using fixed weights. Free reports use 5 dimensions, while paid reports use 8 dimensions. Some negative dimensions like competition are inverted during calculation.

### Q10. Why not let the LLM simply decide the final score?

Answer:

> A direct LLM score would be less explainable and harder to test. Weighted scoring lets me explain exactly how the score is calculated and keeps the final number deterministic once the dimension scores are produced.

### Q11. What happens after the user upgrades?

Answer:

> The backend loads the same LangGraph thread state, updates the tier, and resumes the workflow. Basic tier generates a Business Model Canvas and Go/No-Go report. Standard and premium run multiple modules in parallel, compile the report, and wait for admin approval.

### Q12. What is parallel execution?

Answer:

> For standard and premium reports, independent modules like market, competitor, finance, tech, risk, and roadmap analysis can run at the same time using `asyncio.gather()`. This reduces total generation time compared with running every module sequentially.

### Q13. What is the Strategic Directive?

Answer:

> It is a shared set of assumptions generated before deep analysis. It defines target customers, pricing, value proposition, constraints, differentiation, and year-one goals so that all modules stay consistent.

### Q14. How does admin approval work technically?

Answer:

> The graph is compiled with `interrupt_before=["admin_approve"]`, so paid reports pause before final release. Admin endpoints allow an admin to save edits or approve the report. Approval resumes the workflow and marks the report ready.

### Q15. How is realtime processing status shown?

Answer:

> The processing page subscribes to Supabase realtime changes for the validation session and reports table. It also polls every few seconds as a fallback.

### Q16. What are the main backend endpoints?

Answer:

> `/submit`, `/answer/{thread_id}`, `/upgrade/{thread_id}`, `/report/{thread_id}`, `/admin/save/{thread_id}`, `/admin/approve/{thread_id}`, `/profile/upgrade`, `/generate-html`, and `/health`.

### Q17. What would happen if the AI API fails?

Answer:

> The `LLMService` has retry logic and structured parsing fallback. Some nodes also return fallback values when analysis fails. In a production version, I would add a stronger queue/retry system and clearer user-facing error recovery.

### Q18. How do you handle API rate limits?

Answer:

> The backend has SlowAPI rate limiting for HTTP endpoints. The LLM service also limits concurrent LLM calls using an asyncio semaphore and retries rate-limit errors with backoff.

### Q19. How do you validate report schema?

Answer:

> Report sections are defined as Pydantic models in `src/models/outputs.py`. LLM responses are parsed into those models. If the structure is invalid, validation catches it.

### Q20. What are the most important files?

Answer:

> `src/api/routes.py` for endpoints, `src/graph/workflow.py` for workflow, `src/agents/` for AI logic, `src/models/outputs.py` for schemas, `src/utils/scoring.py` for scoring, `frontend/src/App.tsx` for routes, `frontend/src/lib/api.ts` for API calls, and `frontend/src/lib/supabase.ts` for database helpers.

### Q21. What testing did you do?

Answer:

> The project includes pytest tests for models, scoring, workflow routing, API response structures, custom tier behavior, search credibility, currency handling, and score persistence. Some tests need updating because the architecture evolved, but the testing structure is present.

### Q22. What is your biggest technical risk?

Answer:

> The biggest risks are dependency on external AI/search services and the need for stronger production authentication. I mitigated this by centralizing external service calls, supporting frontend mock mode, using schemas, and identifying server-side JWT verification as a future improvement.

### Q23. How is this different from a normal form-based report generator?

Answer:

> It is dynamic and stateful. It interviews the user, researches context, routes by tier, runs specialized modules, scores the idea, checks consistency, supports admin approval, and stores/retrieves reports per user.

### Q24. Can you explain the code flow from button click to report?

Answer:

> In `Submit.tsx`, the user clicks submit. `frontend/src/lib/api.ts` calls `POST /submit`. The backend route creates a thread and starts LangGraph. The interviewer returns a question. The user answers through `POST /answer/{thread_id}`. The graph completes interview, runs research, generates the free report, sends webhook/database updates, and the frontend fetches it through `GET /report/{thread_id}`.

### Q25. Why do you need admin if AI generates the report?

Answer:

> Admin review improves trust and quality. Since paid reports may be used academically or for serious business decisions, a human-in-the-loop approval step ensures that the AI output is reviewed before release.

## 16. Code Walkthrough Talking Points

### `src/api/routes.py`

Say:

> This file exposes the backend API. It connects HTTP requests to the LangGraph workflow and database helpers.

Show:

- `submit_idea`
- `submit_answer`
- `upgrade_tier`
- `get_report`
- `admin_approve`

### `src/graph/workflow.py`

Say:

> This is the brain of the workflow. It defines nodes and routing.

Show:

- Node definitions.
- Conditional edges.
- `interrupt_before=["admin_approve"]`.
- Supabase/PostgreSQL checkpointer, with `MemorySaver` only for local testing.

### `src/models/inputs.py`

Say:

> This defines request models and shared workflow state.

Show:

- `StartupSubmission`
- `SubmitInput`
- `AnswerInput`
- `UpgradeInput`
- `ValidationState`

### `src/models/outputs.py`

Say:

> This defines the shape of AI outputs. It is important because AI output must be structured for frontend rendering.

Show:

- `FreeReportOutput`
- `BasicReportOutput`
- `StrategicDirective`
- `InvestorPitchDeck`
- Module schemas/aliases near the bottom.

### `src/agents/base.py`

Say:

> This centralizes LLM and search access so the rest of the project does not call APIs directly everywhere.

Show:

- `LLMService.invoke`
- `LLMService.invoke_structured`
- Tavily search helpers.

### `src/utils/scoring.py`

Say:

> This file makes scoring deterministic and explainable.

Show:

- `VIABILITY_WEIGHTS`
- `GO_NO_GO_WEIGHTS`
- `calculate_viability_score`
- `calculate_go_no_go_score`

### `frontend/src/App.tsx`

Say:

> This shows the web app routes and protected pages.

### `frontend/src/lib/supabase.ts`

Say:

> This shows how the frontend saves sessions, answers, statuses, and subscribes to report updates.

## 17. Backup Plan If Live AI Generation Fails

External AI/search APIs can be slow or fail during demo. Be ready.

Backup options:

1. Show an already generated report from dashboard.
2. Use frontend mock mode:

```bash
VITE_USE_MOCK_API=true npm run dev
```

3. Show backend `/docs` and explain endpoint flow.
4. Show Supabase tables with stored sessions/reports.
5. Show code path instead of waiting for live generation.

What to say:

> Because this project depends on external AI/search APIs, live generation can depend on network/API availability. I prepared existing records and mock mode to demonstrate the system flow reliably.

## 18. Things Not to Say

Avoid:

- "I do not know."
- "The AI does everything."
- "It is just ChatGPT."
- "The database is not important."
- "Security is complete."
- "All tests pass" unless you have just run them.

Better replacements:

- "The relevant part is handled in this file..."
- "The AI is used only inside controlled agents..."
- "The database stores sessions, roles, and reports..."
- "For production, I would improve JWT verification..."
- "Some tests are present, and a few need updating because the architecture changed..."

## 19. Final 2-Minute Summary

Use this if your supervisor asks you to summarize at the end:

> Validator AI is a full-stack web app for validating startup ideas. It uses a React frontend, FastAPI backend, Supabase/PostgreSQL database, and a LangGraph workflow. Normal users can submit ideas, answer a 5-question AI interview, view reports, and upgrade analysis. Admins can review and approve paid reports. The backend uses specialized AI agents for interviewing, research synthesis, free report generation, paid module generation, scoring, and final compilation. Supabase/PostgreSQL also acts as the persistent workflow saver for LangGraph checkpoints. External APIs are used intentionally for AI reasoning, live market research, database/auth, and report delivery, and their usage is isolated in service layers. The scoring is not random; it uses deterministic weighted formulas after AI-generated dimension scores. The project satisfies the requirements of a web app, database, multi-role users, explainable AI workflow, and justified external API usage.
