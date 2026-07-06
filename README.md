# AI Startup Validation Agent

> A sophisticated, agentic AI system for validating startup ideas. Built on **LangGraph**, it orchestrates a fleet of specialized LLMs (DeepSeek V4 Flash/Pro via OpenRouter) to interview founders, conduct real-time market research, and generate investor-grade strategic reports.

---

## 🚀 Key Features

### 🧠 Hybrid Brain Architecture
-   **Adaptive Intelligence**: Automatically routes tasks to the most efficient model tier via **OpenRouter**:
    -   **DeepSeek V4 Flash**: Running on **Baidu Qianfan** with **0.61s TTFT** for lightning-fast, conversational interviews and real-time synthesis checks.
    -   **DeepSeek V4 Pro**: Large-scale Mixture-of-Experts (1.6T parameters, 49B active) routed dynamically to the lowest-cost provider (e.g. **StreamLake** at **$0.7482/1M tokens**) for premium, highly detailed reports.
-   **Real-time Streaming**: Connects to an SSE streaming endpoint to deliver interview questions token-by-token for a smooth typewriter effect on the frontend.
-   **Prompt Caching**: 
    -   **Automatic Prefix Caching**: Matches the identical system/context blocks (>1024 tokens) across parallel module calls on DeepSeek to save up to **90%+** on input costs.
    -   **Explicit Caching (Claude Fallback)**: Automatically wraps Claude fallback messages in `cache_control` blocks with ephemeral markers for consistent caching.

### ⚡ Performance & Scalability
-   **True Parallelism**: Boosted execution limits:
    -   Global LLM semaphore lifted from `3 → 15` calls to run all 10 report modules simultaneously.
    -   Consistency summary semaphore lifted from `2 → 10` calls (with artificial cooldown delays removed) to evaluate reports in parallel.
-   **Single-Step Query & Search**: Merged extraction and search objective generation into a single LLM step, bypassing 3 sequential LLM query generation roundtrips by calling Tavily directly.
-   **Optimized Consistency Cascades**: Smart Consistency Cascades reduced from `2 → 1` cycle with a tightened budget of `8` LLM calls, ensuring high accuracy with 50% fewer reasoning passes.

### 🛡️ Robust Validation Workflow
-   **Self-Healing**: "Compiler" agent detects contradictions between modules (e.g., Market vs. Finance) and auto-corrects them before reporting.
-   **Strategic Directive**: Generates a "Truth Document" early in the pipeline to ensure all concurrent agents align on the startup's core strategy.

---

## 🛠 Tech Stack

-   **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) (Stateful Multi-Agent Workflows)
-   **Agents**: [LangChain](https://github.com/langchain-ai/langchain)
-   **API**: FastAPI (Python 3.13+)
-   **Runtime Management**: `uv` (Fast Python Package Installer)
-   **Search**: Tavily API (Real-time web research)
-   **Database**: PostgreSQL (Checkpointing)
-   **Containerization**: Docker & Docker Compose

---

## 🏗 Architecture

### The Workflow Graph

The system is modeled as a directed cyclic graph (DAG) in `src/graph/workflow.py`.

```mermaid
graph TD
    Start([User Input]) --> Interview[Interviewer Agent<br>DeepSeek V4 Flash]
    Interview <--> User((User))
    Interview -->|Complete| Research[Researcher Agent<br>V4 Flash + Tavily]
    Research --> Strategy[Strategic Directive<br>V4 Flash]
    Strategy -->|Fan Out| Parallel{Parallel Execution}
    
    subgraph "Standard/Premium Tier"
        Parallel --> Mod1[Market Analysis<br>V4 Pro]
        Parallel --> Mod2[Financials<br>V4 Pro]
        Parallel --> Mod3[Tech Stack<br>V4 Pro]
        Parallel --> Mod4[Competitors<br>V4 Pro]
        Parallel --> Mod5[...]
    end
    
    Mod1 & Mod2 & Mod3 & Mod4 & Mod5 -->|Fan In| Compiler[Compiler Agent<br>V4 Pro]
    Compiler -->|Consistency Check| Review[Quality Assurance]
    Review -->|Pass| Report[Final Report]
```

### State Management (`ValidationState`)
All agents read from and write to a shared "Blackboard" state:
-   **Inputs**: Description, Tier
-   **Context**: Interview Transcript, Research Data
-   **Outputs**: Module Results, Final Report
This allows the process to be paused (e.g., for payment) and resumed without data loss.

---

## 🚦 Getting Started

### Prerequisites

-   **Python 3.13+**
-   **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
-   **Docker** (Optional, for production)

### Local Development

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/validator-ai.git
    cd validator-ai
    ```

2.  **Install Dependencies**
    We use `uv` for lightning-fast dependency management.
    ```bash
    uv sync
    ```

3.  **Environment Configuration**
    Copy the example template and fill in your keys.
    ```bash
    cp .env.example .env
    ```

    | Variable | Description | Required | 
    |----------|-------------|----------|
    | `OPENROUTER_API_KEY` | Pinned to Baidu Qianfan/StreamLake for DeepSeek V4 | ✅ |
    | `TAVILY_API_KEY` | Search Provider | ✅ |
    | `USE_MEMORY_SAVER` | Set to `true` for local dev (no Postgres needed) | ⚠️ |

4.  **Run the Server**
    ```bash
    # Set to use in-memory checkpointer for dev
    export USE_MEMORY_SAVER=true
    
    # Run via uv
    uv run uvicorn app:app --reload --port 8000
    ```

5.  **Test the API**
    Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the Swagger UI.

---

## 📦 Service Tiers

| Feature | Free | Basic | Standard | Premium |
|:---|:---:|:---:|:---:|:---:|
| **Word Count** | ~300 | ~1,500 | ~25k | ~25k |
| **Model** | Flash | Flash | **Pro** | **Pro** |
| **Modules** | Viability | BMC | 10 Deep Dives | 10 Deep Dives |
| **Pitch Deck** | ❌ | ❌ | ❌ | ✅ |
| **Human Review**| ❌ | ✅ | ✅ | ✅ |

---

## 🧪 Testing

The project uses `pytest` for testing.

### Run All Tests
```bash
uv run pytest
```

### Specific Test Suites
-   **Workflow Logic**: Verify routing and state transitions.
    ```bash
    uv run pytest tests/test_workflow.py
    ```
-   **Agent Logic**: Test individual agent prompts and parsing.
    ```bash
    uv run pytest tests/test_agents.py
    ```
-   **Integration**: Test the full API flow.
    ```bash
    uv run pytest tests/test_api.py
    ```

---

## 🐳 Deployment

For production, use the included Docker Compose setup.

1.  **Build & Run**
    ```bash
    docker compose up --build -d
    ```

2.  **Database Migration**
    The app uses LangGraph's Postgres checkpointer implicitly. Ensure the `DATABASE_URL` in `.env` points to the postgres container.

