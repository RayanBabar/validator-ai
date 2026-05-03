# Validator AI Project Explanation

This document explains the project as it exists in the codebase. Use it to describe the system in interviews, demos, presentations, or viva-style questioning.

## 1. One-Line Summary

Validator AI is a full-stack startup idea validation platform. A user submits a startup idea, answers a short AI interview, receives a free viability report, and can upgrade to deeper paid reports generated through a LangGraph multi-agent backend with live Tavily research, structured LLM outputs, scoring logic, Supabase/PostgreSQL persistence, admin approval, and a React frontend.

## 2. What Problem This Project Solves

Founders often need quick feedback on whether a startup idea is worth pursuing, but proper validation requires market research, customer analysis, competitor research, financial thinking, regulatory awareness, and execution planning. This project automates that workflow by combining:

- AI interview questions to clarify the founder's idea.
- Web research through Tavily.
- LLM-generated structured reports.
- Weighted scoring models.
- Tiered outputs from a short free report to a comprehensive standard or premium report.
- Human/admin approval before releasing paid reports.

## 3. High-Level Architecture

The project has two main applications:

- Backend: FastAPI + LangGraph in Python.
- Frontend: Vite + React + TypeScript + Supabase.

Important backend paths:

- `app.py`: Docker/API entrypoint; imports the FastAPI app from `src.api.server`.
- `src/api/server.py`: creates the FastAPI app, middleware, CORS, lifespan startup/shutdown, and health check.
- `src/api/routes.py`: defines the API endpoints used by the frontend.
- `src/graph/workflow.py`: defines the LangGraph workflow and routing between agents.
- `src/agents/`: contains the AI nodes and research/report generation logic.
- `src/models/inputs.py`: request and graph state schemas.
- `src/models/outputs.py`: strict Pydantic output schemas for all report tiers and modules.
- `src/utils/`: scoring, Supabase, webhook, currency, and date utilities.
- `src/config/`: settings, constants, warnings, and prompt templates.

Important frontend paths:

- `frontend/src/App.tsx`: React routes.
- `frontend/src/lib/api.ts`: backend API client.
- `frontend/src/lib/supabase.ts`: Supabase client and persistence helpers.
- `frontend/src/contexts/AuthContext.tsx`: auth state, session, and admin detection.
- `frontend/src/pages/Submit.tsx`: startup idea submission.
- `frontend/src/pages/Interview.tsx`: answer the AI interview questions.
- `frontend/src/pages/Report.tsx`: display free and paid reports.
- `frontend/src/pages/Upgrade.tsx`: select paid tier.
- `frontend/src/pages/Processing.tsx`: waiting screen for paid reports and admin approval.
- `frontend/src/pages/Dashboard.tsx`: user's saved validation sessions.
- `frontend/src/pages/AdminDashboard.tsx`: admin approval queue.

## 4. Backend Request Lifecycle

### Step 1: User Submits Startup Idea

Endpoint: `POST /submit`

The frontend sends:

```json
{
  "detailed_description": "The user's startup idea"
}
```

The backend:

1. Creates a new `thread_id` using `uuid4`.
2. Builds the initial LangGraph state.
3. Sets tier to `free`.
4. Starts the graph at the `interviewer` node.
5. Returns the first generated interview question.

The LangGraph thread ID is important because all later answers, upgrades, report polling, and approval actions use that same ID.

### Step 2: User Answers Interview Question

Endpoint: `POST /answer/{thread_id}`

The backend:

1. Loads the graph state for the thread.
2. Appends the user's answer to `user_answers`.
3. Updates graph state as the `process_answer` node.
4. Resumes the graph.
5. Either returns another question or marks the interview complete.

Intended project setting:

- `MAX_INTERVIEW_QUESTIONS = 5`
- `MIN_INTERVIEW_QUESTIONS = 1`

The interview is designed to ask up to 5 clarifying questions. During development, a 1-question setting was temporarily used to speed up testing, but the final demo configuration uses 5 questions.

### Step 3: Research and Free Report Generation

After the interview is complete, the graph routes to:

1. `research`
2. `free_scan`
3. `END`

The research node:

- Synthesizes the user's original idea and Q&A.
- Extracts geography, industry, regulatory context, and context specificity.
- Runs dynamic Tavily research.
- Evaluates interview quality.
- Builds `search_context` and `enriched_context`.

The free tier node:

- Generates a short structured report.
- Calculates a weighted viability score.
- Generates a package recommendation.
- Sends the report through the webhook.
- Updates Supabase session status to `free_report_ready`.

### Step 4: User Upgrades

Endpoint: `POST /upgrade/{thread_id}`

Allowed tiers:

- `basic`
- `standard`
- `premium`
- `custom`

The backend:

1. Loads the existing graph state.
2. Replaces the state input tier.
3. Optionally stores selected custom modules.
4. Updates Supabase session tier/status.
5. Starts the paid workflow in a FastAPI background task.

Paid tier routing:

- `basic` goes to `basic_gen`.
- `standard`, `premium`, and `custom` go to `parallel_modules`.

### Step 5: Paid Report Generation

Basic tier:

1. Conducts or reuses scoring research.
2. Generates a Strategic Directive.
3. Generates a Business Model Canvas.
4. Calculates an 8-dimension Go/No-Go score.
5. Generates an executive summary.
6. Sends webhook.
7. Routes to `admin_approve`.

Standard, Premium, and Custom:

1. Conduct or reuse comprehensive research.
2. Generate a Strategic Directive if missing.
3. Run selected modules in parallel.
4. Compile the final report.
5. Run consistency checks and possible fixes.
6. Calculate/reuse Go/No-Go score.
7. Generate executive summary.
8. Add investor pitch deck for premium or custom pitch-deck selection.
9. Send webhook.
10. Pause before admin approval.

### Step 6: Admin Approval

Paid reports pause before `admin_approve` because the graph is compiled with:

```python
interrupt_before=["admin_approve"]
```

Admin endpoints:

- `POST /admin/save/{thread_id}` saves edited report data without advancing the graph.
- `POST /admin/approve/{thread_id}` approves and resumes the graph.

The frontend admin dashboard lists sessions with status `waiting_for_admin_approval`.

### Step 7: Report Retrieval

Endpoint: `GET /report/{thread_id}?tier=free`

The backend:

1. Tries to load LangGraph state.
2. Determines whether the workflow is processing, complete, failed, paused, or waiting for admin.
3. Gets report data from graph state if available.
4. Falls back to Supabase reports for persisted report versions.
5. Returns available tiers for the thread.

## 5. LangGraph Workflow

The workflow is defined in `src/graph/workflow.py`.

Nodes:

- `interviewer`: asks a clarifying question or completes interview.
- `process_answer`: pass-through node after an answer is submitted.
- `research`: synthesizes context, extracts metadata, performs research, and evaluates quality.
- `free_scan`: creates the free viability report.
- `basic_gen`: creates the basic report.
- `parallel_modules`: runs standard/premium/custom modules concurrently.
- `compiler`: compiles paid module outputs into a final report.
- `admin_approve`: marks paid report as waiting for admin approval.

Routing:

- `interviewer` routes to `END` if still waiting for an answer.
- `interviewer` routes to `research` once interview is complete.
- `research` routes by tier:
  - free -> `free_scan`
  - basic -> `basic_gen`
  - standard/premium/custom -> `parallel_modules`
- `free_scan` ends so the user can upgrade later.
- `basic_gen` routes to `admin_approve`.
- `parallel_modules` routes to `compiler`, then `admin_approve`.

State persistence:

- If `USE_MEMORY_SAVER` is set, LangGraph uses in-memory state for local development.
- Otherwise it uses `AsyncPostgresSaver` with `DATABASE_URL`. In this project, the persistent Postgres database is supplied through Supabase/PostgreSQL.

## 6. Core State Object

The shared LangGraph state is `ValidationState` in `src/models/inputs.py`. It acts like a blackboard that every node reads and updates.

Important fields:

- `inputs`: startup description, tier, custom modules.
- `thread_id`: workflow/session ID.
- `questions_asked`, `user_answers`, `current_question`: interview state.
- `enriched_context`, `search_context`: synthesized research and report context.
- `clarity_score`, `answer_quality_score`, `dimension_quality`: quality metrics used in scoring.
- `extracted_industry`, `extracted_geography`, `extracted_regulatory_context`: dynamic context extracted from the idea.
- `workflow_phase`, `error`, `error_message`, `error_node`: workflow tracking.
- `bmc_data`, `market_data`, `competitor_data`, `financial_data`, `tech_data`, `reg_data`, `gtm_data`, `risk_data`, `roadmap_data`, `funding_data`: standard module outputs.
- `comprehensive_research`: reused research context for paid modules.
- `strategic_directive`: shared "truth" document for report consistency.
- `stored_go_no_go_score`, `stored_score_breakdown`, `stored_scoring_research`: persisted scoring data so upgrades do not unnecessarily recalculate scores.
- `final_report`: final typed report payload.

## 7. LLM Service

The common LLM wrapper is `LLMService` in `src/agents/base.py`.

It provides:

- `invoke(...)`: general JSON or text output.
- `invoke_structured(...)`: Pydantic-schema output.
- A semaphore limiting parallel LLM calls to 3.
- Retry logic for rate-limit and bad-request style failures.
- Manual JSON extraction and repair fallback when structured output fails.
- Snake-case key normalization for LLM responses.

Actual configured model objects in current code:

- `llm_fast`: `ChatOpenAI(model="gpt-5-nano")`
- `llm_complex`: `ChatOpenAI(model="minimax-m2.5-free")`

Important note: many function calls pass provider names such as `"claude"` or `"claude-opus"`, but the current `LLMService` implementation does not actually branch by provider. It selects between `llm_fast` and `llm_complex` based on `use_complex`.

## 8. Search and Research Layer

Search uses Tavily through `langchain_tavily.TavilySearch`.

Main files:

- `src/agents/search/query_generator.py`: generates search queries using an LLM, with fallback queries.
- `src/agents/search/credibility.py`: scores source credibility.
- `src/agents/search/research.py`: runs dynamic research.
- `src/agents/search/topics.py`: maps each module to research objectives.
- `src/agents/search/strategy.py`: handles comprehensive upfront research and Strategic Directive generation.

Research behavior:

1. The LLM generates search queries.
2. Tavily searches run asynchronously.
3. Results are flattened.
4. URLs are scored for credibility.
5. Low-credibility sources are filtered out unless fallback is needed.
6. Results are deduplicated and combined.
7. If no useful result is found, broad retry and creative retry logic are attempted.

The current `conduct_dynamic_research` tier query map sets all tiers to 1 query per objective, even though comments and some verification scripts describe larger query counts.

## 9. Report Tiers

### Free Tier

Generated by: `src/agents/free_tier.py`

Output schema: `FreeReportOutput`

Includes:

- Title.
- Viability score from 0 to 100.
- Gauge status: `Promising` or `Needs Work`.
- 5 score dimensions.
- Value proposition.
- Customer profile.
- What-if scenario.
- Package recommendation.
- Personalized next step.

### Basic Tier

Generated by: `src/agents/basic_tier.py`

Output schema: `BasicReportOutput`

Includes:

- Title.
- Go/No-Go score from 0 to 100.
- 8 score dimensions.
- Executive summary.
- Business Model Canvas.

### Standard Tier

Generated by:

- `src/agents/parallel_executor.py`
- `src/agents/standard_modules.py`
- `src/agents/compiler.py`

Includes:

- Go/No-Go score.
- Score breakdown.
- Executive summary.
- Modules:
  - Business Model Canvas.
  - Market Analysis.
  - Competitive Intelligence.
  - Financial Feasibility.
  - Technical Requirements.
  - Regulatory Compliance.
  - Go-to-Market Strategy.
  - Risk Assessment.
  - Implementation Roadmap.
  - Funding Strategy.

### Premium Tier

Premium uses the same standard modules and adds an investor pitch deck.

Pitch deck generation:

- Function: `_generate_pitch_deck` in `src/agents/compiler.py`.
- Schema: `InvestorPitchDeck`.
- Expected output: 12 slides with title, bullets, visual suggestion, and speaker notes.

### Custom Tier

Custom tier accepts selected module names in `custom_modules`.

Valid standard module keys:

- `mod_bmc`
- `mod_market`
- `mod_comp`
- `mod_finance`
- `mod_tech`
- `mod_reg`
- `mod_gtm`
- `mod_risk`
- `mod_roadmap`
- `mod_funding`

Extra allowed custom module:

- `investor_pitch_deck`

For custom tier, the compiler skips cross-module consistency checks for performance.

## 10. Scoring Methodology

Scoring logic is in `src/utils/scoring.py`.

### Free Viability Score

Dimensions and weights:

- `problem_severity`: 30%
- `market_opportunity`: 25%
- `competition_intensity`: 20%
- `execution_complexity`: 15%
- `founder_alignment`: 10%

Important scoring behavior:

- `competition_intensity` is inverted for calculation because high competition is bad.
- `execution_complexity` is inverted for calculation because high complexity is bad.
- Interview quality adjusts dimension scores before final calculation.
- Low context specificity penalizes market/problem scoring.
- Final score is scaled to 0-100.

Package recommendation:

- 0-35: `quit`
- 36-60: `premium`
- 61-85: `standard`
- 86-100: `basic`

Gauge:

- Above 70: `Promising`
- 70 or below: `Needs Work`

### Paid Go/No-Go Score

Dimensions and weights:

- `market_demand`: 25%
- `financial_viability`: 20%
- `competition_analysis`: 15%
- `founder_market_fit`: 10%
- `technical_feasibility`: 10%
- `regulatory_compliance`: 10%
- `timing_assessment`: 5%
- `scalability_potential`: 5%

Important scoring behavior:

- `competition_analysis` is inverted internally because more intense competition is worse.
- Scores are rounded to integer 0-10 for display.
- Final score is scaled to 0-100.
- Compiler stores scoring research and score breakdown so later runs can reuse them.

## 11. Quality Assurance and Consistency System

Quality files:

- `src/agents/quality_checker.py`
- `src/agents/schema_registry.py`
- `src/agents/dependency_analyzer.py`
- `src/agents/fix_history.py`

For standard and premium reports, the compiler performs a "Smart Cascade" consistency check:

1. Summarizes module outputs.
2. Checks for major contradictions across modules.
3. Classifies issues as critical, major, or minor.
4. Uses authority rules to decide which module should be fixed.
5. Applies fixes in limited cycles.
6. Validates fixed module data against Pydantic schemas.
7. Tracks fix history to avoid repeated bad fixes.

Examples of consistency checks:

- Market size vs financial projections.
- GTM strategy vs customer segments.
- Technical complexity vs roadmap timeline.
- Risks vs mitigation plans.

Module authority rules decide which module wins during conflict resolution. For example:

- Market data can be authoritative over financial projections and roadmap assumptions.
- Tech data can be authoritative over roadmap and development cost assumptions.
- BMC data can be authoritative for customer segments.

## 12. Persistence and External Integrations

### LangGraph State Persistence

The backend persists graph state using either:

- `MemorySaver` for local development.
- Supabase/PostgreSQL checkpointing via `AsyncPostgresSaver`.

For the final project explanation, Supabase/PostgreSQL is the intended persistent saver. `MemorySaver` is only a convenience option for quick local tests.

### Supabase

Frontend Supabase usage:

- Authentication.
- User profiles and admin flag.
- `validation_sessions`.
- `interview_answers`.
- `reports`.
- Realtime updates for processing/report status.

Backend Supabase usage:

- Update user tier.
- Check admin status.
- Update session status.
- Update session tier.
- Read reports by thread ID.

Authentication note:

The backend currently reads `X-User-Id` from the frontend and has a TODO for proper JWT verification. It does not fully verify the Supabase JWT server-side yet.

### Webhook

Webhook code is in `src/utils/webhook.py`.

The webhook sends:

- `report_score`
- `tier`
- `report_metadata` as a JSON string

It calls:

```text
PUT {WEBHOOK_URL}/{thread_id}
```

Important note: `WEBHOOK_URL` is required at import time. If it is missing, importing `src.utils.webhook` raises a `ValueError`.

## 13. API Endpoints

Main endpoints:

- `GET /health`: health check.
- `POST /submit`: starts a validation journey.
- `POST /answer/{thread_id}`: submits interview answer and continues workflow.
- `POST /upgrade/{thread_id}`: upgrades to paid/custom tier and starts deep analysis.
- `POST /profile/upgrade`: updates user's permanent profile tier.
- `GET /report/{thread_id}`: returns report status and report data.
- `POST /admin/save/{thread_id}`: saves admin edits.
- `POST /admin/approve/{thread_id}`: approves and releases paid report.
- `POST /generate-html`: renders report JSON into `src/templates/report.html`.

Rate limits:

- `/submit`: 10 per minute.
- `/answer/{thread_id}`: 30 per minute.
- `/upgrade/{thread_id}`: 5 per minute.
- Global default: controlled by `RATE_LIMIT_PER_MINUTE`.

## 14. Frontend User Flow

### Landing

Route: `/`

Marketing/entry screen for the product.

### Dashboard

Route: `/dashboard`

Shows the logged-in user's validation sessions, tiers, statuses, viability score, and Go/No-Go score.

### Submit

Route: `/submit`

The user enters a startup description. The frontend requires 100-2000 characters. On success, it stores the thread info in localStorage and routes to the interview screen.

### Interview

Route: `/interview/:threadId`

Shows the current AI question, collects an answer, stores answer history in localStorage, and routes to the free report when ready.

Interview count note:

- The final intended interview flow is 5 questions.
- A 1-question backend value was used only for faster testing during development.
- Older UI copy previously implied 10 questions; the final explanation and demo should use 5.

### Report

Route: `/report/:threadId?tier=free`

Displays:

- Animated score.
- Score dimensions.
- Free report sections.
- Basic report sections.
- Standard/premium module sections.
- Admin editing controls when in preview/admin mode.
- Tier switching if multiple reports exist.
- Upgrade CTA for free users.

### Upgrade

Route: `/upgrade/:threadId`

Lets the user request:

- Basic Research.
- Standard Analysis.
- Premium Validation.

The frontend passes selected modules to the backend when upgrading.

### Processing

Route: `/processing/:threadId`

Shows animated progress while the paid report is generating. It checks:

- Supabase session status.
- Supabase report table.
- Supabase realtime events.
- Polling fallback every 5 seconds.

If status becomes `waiting_for_admin_approval`, it shows an admin-review message.

### Admin Dashboard

Route: `/admin`

Shows pending sessions where status is `waiting_for_admin_approval`. Admins can preview and approve reports.

## 15. Configuration and Environment

Backend settings are defined in `src/config/settings.py`.

Required backend environment variables by settings:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

Optional backend variables:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_BASE`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `WEBHOOK_URL`
- `LANGSMITH_*`
- `ENVIRONMENT`
- `CORS_ORIGINS`
- `RATE_LIMIT_PER_MINUTE`

Frontend variables:

- `VITE_API_BASE_URL`
- `VITE_USE_MOCK_API`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

Local backend run command from README:

```bash
export USE_MEMORY_SAVER=true
uv run uvicorn app:app --reload --port 8000
```

Frontend run command:

```bash
cd frontend
npm run dev
```

## 16. Docker Setup

`docker-compose.yml` defines:

- `app`: FastAPI backend on port 8000.
- `db`: Postgres 15 Alpine on port 5432.

The backend Dockerfile:

- Uses `python:3.12-slim`.
- Installs `uv`.
- Copies backend files.
- Runs `uv sync`.
- Starts `uvicorn`.

Important mismatch:

- `pyproject.toml` requires Python `>=3.13`.
- `Dockerfile` uses Python 3.12.

This should be fixed before relying on Docker for production.

## 17. Tests and Verification Files

Tests are under `tests/`.

Covered areas include:

- Models and schema validation.
- Scoring formulas.
- Currency conversion.
- Workflow routing/state behavior.
- API response shape.
- Agent helper behavior.
- Search credibility and query fallback.
- Custom tier logic.
- Score persistence/reuse.

Important note:

Some tests appear stale relative to the current implementation. For example, `tests/test_model_config.py` expects model names and Claude objects that are not present in the current `src/agents/base.py`. Some verification scripts also expect tier query counts that no longer match `conduct_dynamic_research`.

## 18. Key Strengths of the Project

- Clear separation between API, graph workflow, agents, schemas, utilities, and frontend.
- LangGraph gives resumable, thread-based workflow state.
- Pydantic schemas force report outputs into structured shapes.
- Weighted scoring functions are deterministic after LLM dimension scores are generated.
- Paid analysis runs modules in parallel for speed.
- Research is dynamic and context-aware rather than relying on static templates only.
- Admin approval adds a human-in-the-loop quality step.
- Supabase provides auth, persistence, dashboard data, and realtime status updates.
- The frontend supports the full product flow: submit, interview, report, upgrade, processing, dashboard, and admin.

## 19. Current Limitations and Mismatches

These are important to mention honestly if asked technical questions:

- The README and old `project_documentation.md` describe Claude/Opus/Sonnet/Haiku routing, but current code uses `ChatOpenAI` model objects only.
- The `provider` parameter is accepted by `LLMService` methods but is not used to switch providers.
- Interview count is 5 for the final project. A 1-question value was only a development testing shortcut, and old 10-question frontend copy was from an earlier iteration.
- Docker uses Python 3.12, while `pyproject.toml` requires Python 3.13+.
- `WEBHOOK_URL` is required at import time, which can break startup/tests if missing.
- Backend auth relies on `X-User-Id` and does not yet verify Supabase JWTs.
- Supabase report persistence is mostly handled by frontend helpers and webhook/external system; backend directly reads reports but report creation depends on webhook/database integration.
- Some tests and verification scripts reflect older expected behavior.
- `get_report_from_db` is imported in routes but not used directly in the current route logic.
- Standard and premium report output schemas exist, but compiler builds a dictionary-style report rather than directly instantiating `StandardReportOutput` or `PremiumReportOutput`.

## 20. How to Explain This Project in an Interview

Use this short explanation:

"Validator AI is a multi-agent startup validation platform. The user submits an idea, the backend starts a LangGraph workflow, asks up to 5 AI-generated clarification questions, enriches the idea with Tavily research, and produces a free viability score. If the user upgrades, the same graph resumes from the saved Supabase/PostgreSQL checkpointed thread state and routes into basic or deep analysis. Standard and premium tiers run multiple specialized modules in parallel, such as market analysis, competitors, financials, technology, regulatory, GTM, risks, roadmap, and funding. A compiler then checks cross-module consistency, calculates a weighted Go/No-Go score, builds the final report, optionally adds a pitch deck, and pauses for admin approval. The frontend is a React app with Supabase auth, dashboards, realtime report updates, report rendering, upgrades, and admin approval."

## 21. Common Questions and Good Answers

### Why LangGraph?

LangGraph is useful because this is not a single request-response LLM call. The workflow needs to pause for user answers, resume after upgrade, persist state by thread ID, branch by tier, run parallel modules, and pause before admin approval.

### Why Pydantic schemas?

LLMs can produce inconsistent JSON. Pydantic models define exactly what each report should contain, validate types and allowed values, and make frontend rendering more predictable.

### Why use weighted scoring instead of only asking the LLM for a final score?

The LLM provides dimension-level judgments, but the final score is calculated deterministically with explicit weights. This makes scoring easier to explain, test, and adjust.

### How does the system handle research?

It extracts context such as industry and geography, generates search queries, runs Tavily searches, scores source credibility, filters/deduplicates results, and passes the research into LLM prompts.

### How are paid reports faster?

Standard and premium modules are independent enough to run concurrently. `parallel_executor.py` uses `asyncio.gather()` to run selected modules at the same time and merge their outputs.

### How does the project ensure consistency across modules?

The compiler summarizes modules, asks an LLM to detect contradictions, classifies issues by severity, chooses which module should be fixed using authority rules, applies limited fixes, validates the result against schemas, and tracks fix history.

### What does Supabase do?

Supabase handles frontend authentication, user profiles, admin flags, validation sessions, interview answers, report storage, and realtime updates that let the processing page know when a report is ready.

### What happens if the backend is unavailable?

The frontend has a mock API mode controlled by `VITE_USE_MOCK_API=true`. In mock mode it uses hardcoded interview questions and mock report data.

### What is the difference between free and paid scoring?

Free scoring uses 5 dimensions for a quick viability assessment. Paid scoring uses 8 dimensions for a fuller Go/No-Go recommendation, including financial viability, technical feasibility, regulatory compliance, timing, and scalability.

### What is the admin approval step?

Paid reports pause before release. Admins can preview, edit/save, and approve reports. This creates a human-in-the-loop review process for quality assurance.

### What would you improve next?

The highest-priority improvements are aligning docs/tests with current model code, implementing real provider routing or updating comments, verifying Supabase JWTs server-side, ensuring all interview UI copy says 5 questions, making webhook startup optional for local tests, and aligning Docker Python version with `pyproject.toml`.
