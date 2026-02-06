# Cost and Token Usage Analysis Report (2026)

This report provides a granular breakdown of AI service usage (OpenAI, Anthropic, Tavily) across all tiers, including the **latest "Smart Compromise" architecture** (Strategic Directive).

**LAST UPDATED:** Feb 2026 (Reflecting Strategic Directive + Basic Tier Refactoring + **Real Production Data**)

## 1. Model Definitions & Pricing Assumptions

### Current Production Models
*   **Fast LLM (Haiku 4.5)**
    *   **Input:** $1.00 / MTok (Cached Read: $0.10)
    *   **Output:** $5.00 / MTok
*   **Fast LLM (GPT-5-mini)**
    *   **Input:** $0.25 / MTok
    *   **Output:** $2.00 / MTok
*   **Complex LLM (Sonnet 4.5)**
    *   **Input:** $3.00 / MTok (Cached Read: $0.30)
    *   **Cache Write (5m):** $3.75 / MTok
    *   **Cache Write (1h):** $6.00 / MTok
    *   **Output:** $15.00 / MTok

### Hypothetical Model (Scenario B)
*   **Ultra-Complex LLM (Claude Opus 4.5)**
    *   **Input:** $5.00 / MTok
    *   **Cache Write (5m):** $6.25 / MTok
    *   **Cache Write (1h):** $10.00 / MTok
    *   **Cache Read:** $0.50 / MTok
    *   **Output:** $25.00 / MTok

*   **Tavily Search**
    *   **Cost:** ~$0.008 per search request (or credit).

---

## 2. Usage by Phase (Current Architecture)

### Phase A: Interview & Synthesis (All Tiers)
*Occurs for every user before report generation.*

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Questions** (5-10 rounds) | Anthropic | **claude-haiku-4-5** | 5-10 | 30k (cumulative) | 1k | $0.035 |
| **Context Extraction** | OpenAI | **gpt-5-mini** | 1 | 2k | 200 | $0.001 |
| **Synthesis Query Gen** | OpenAI | **gpt-5-mini** | 3 | 1.5k | 150 | $0.001 |
| **Synthesis Research** | Tavily | N/A | 6 | N/A | N/A | $0.05 |
| **Context Synthesis** | Anthropic | **claude-haiku-4-5** | 1 | 10k (Research) | 500 | $0.013 |
| **Quality Check** | OpenAI | **gpt-5-mini** | 1 | 3k | 100 | $0.001 |
| **TOTAL** | | | | | **~14 LLM / 6 Search** | **~46.5k Fast** | **~2k High** | **~$0.10** |

### Phase B: Free Tier Report
*Generates basic viability score.*

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Viability Scan** | Anthropic | **claude-haiku-4-5** | 1 | 5k | 500 | $0.008 |
| **TOTAL** | | | | | **1 LLM** | **5k Fast** | **500 Fast** | **~$0.01** |

### Phase C: Basic Tier Upgrade (New Sequential Flow)
*BMC -> Strategic Directive -> Score -> Summary.*

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Research Query Gen** | OpenAI | **gpt-5-mini** | 5 | 2.5k | 250 | $0.001 |
| **Live Research** | Tavily | N/A | 10 | N/A | N/A | $0.08 |
| **Strategic Directive** | Anthropic | **claude-sonnet-4-5** | 1 | 4k | 500 | $0.019 |
| **BMC Generation** | Anthropic | **claude-sonnet-4-5** | 1 | 5k | 1k | $0.03 |
| **Unified Scoring** | Anthropic | **claude-sonnet-4-5** | 1 | 6k (Research+Dir) | 500 | $0.025 |
| **Exec Summary** | Anthropic | **claude-sonnet-4-5** | 1 | 8k (Ctx+Score+BMC) | 1k | $0.039 |
| **TOTAL** | | | | | **6 LLM / 10 Search** | **~23k Complex** | **~3k Complex** | **~$0.20** |

*(Previously $0.11 - Cost increased by ~$0.09 due to 3 additional complex steps for higher consistency)*

### Phase D: Standard/Premium Tier Upgrade
*Comprehensive 10-module Deep Analysis with Strategic Directive.*

**1. Strategic Strategy & Research**

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Query Generation** | OpenAI | **gpt-5-mini** | 7 | 3.5k | 350 | $0.001 |
| **Comprehensive Research**| Tavily | N/A | ~21 | N/A | N/A | $0.17 |
| **Strategic Directive** | Anthropic | **claude-sonnet-4-5** | 1 | 15k (Full Research) | 500 | $0.052 |

**2. Module Generation (x10 Parallel)**
*(Uses Prompt Caching on Research + Directive)*

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Module 1 (Write)** | Anthropic | **claude-sonnet-4-5** | 1 | 15k | 2k | $0.075 |
| **Module 2-10 (Read)** | Anthropic | **claude-sonnet-4-5** | 9 | 135k (@$0.30/M) | 18k | **$0.40** |

**3. Compilation & Verification**

| Step | Service | Model Used | Calls | Input Tokens (Est.) | Output Tokens (Est.) | Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Consistency Fixes** | Anthropic | **claude-sonnet-4-5** | 2 | 10k | 2k | $0.06 |
| **Final Scoring** | Anthropic | **claude-sonnet-4-5** | 1 | 15k | 500 | $0.05 |
| **Exec Summary** | Anthropic | **claude-sonnet-4-5** | 1 | 20k | 1k | $0.08 |
| **TOTAL PHASE D** | | | | | | **~$0.90** |

---

## 3. SCENARIO: Replacing Sonnet 4.5 with Claude Opus 4.5

If we switch the **Complex LLM** tasks (Phase D) from **Sonnet 4.5** to **Opus 4.5**, here is the projected impact.

**Opus 4.5 Pricing Parameters:**
*   **Input:** $5/M
*   **Output:** $25/M
*   **Cache Write (5m):** $6.25/M
*   **Cache Hits:** $0.50/M

### Phase D (Opus 4.5) Calculation

1.  **Strategic Strategy & Research**
    *   Directive: 15k Input ($0.075) + 500 Output ($0.0125) = **$0.088**
2.  **Module Generation (x10)**
    *   **Module 1 (Write)**: 15k Input ($0.09) + 2k Output ($0.05) = **$0.14**
    *   **Module 2-10 (Read)**: 135k Input ($0.0675 @ $0.50/M) + 18k Output ($0.45) = **$0.518**
3.  **Compilation**
    *   **Score/Summary**: ~45k Input ($0.225) + ~3.5k Output ($0.0875) = **$0.313**

| Component | Standard (Sonnet 4.5) | Premium (Opus 4.5) | Increase |
| :--- | :--- | :--- | :--- |
| **Tavily Research** | $0.17 | $0.17 | 0% |
| **Strategy & Modules** | $0.52 | $0.75 | +44% |
| **Compilation** | $0.20 | $0.31 | +55% |
| **Total Phase D Cost** | **$0.89** | **$1.23** | **+38%** |

### Conclusion on Opus 4.5
Switching to Opus 4.5 creates a **"Pro" Tier** costing roughly **$1.23 per report** (vs $0.90).
This is a **38% cost increase**, but provides:
*   Significantly higher reasoning capability for the "Strategic Directive".
*   Better nuance in "Final Scoring".

**Recommendation:**
Use Opus 4.5 ONLY for the **Strategic Directive** step (~$0.09) and potentially **Final Scoring**, while keeping parallel modules on Sonnet 4.5. This "Hybrid" approach would cost ~$0.95 and yield most of the benefits.

---

## 4. OBSERVED METRICS (Langsmith Production Data - Feb 2026)

Real-world execution logs have provided concrete data points, revealing variance from initial estimates.

| Metric | Basic Tier | Standard Tier | Variance Explanation |
| :--- | :--- | :--- | :--- |
| **Total Tokens** | ~80,000 | ~462,000 | Higher retrieval density |
| **Observed Cost** | **$0.40** | **$1.98** | Cache misses on first runs |
| **Estimated Cost** | $0.31 | $1.00 | Estimates assumed 100% cache hit |

### Key Findings:
1.  **Standard Tier Reality**: The 10-module parallel execution is data-heavy. At **462k tokens**, it is significantly larger than the ~250k estimate. This suggests the research context being passed to each module is larger or less compressed than planned.
2.  **Cost Doubles without Caching**: The observed **$1.98** cost likely reflects a "cold start" run where prompt caching wrote data (expensive) but didn't benefit from reads yet.
3.  **Target Margins**:
    *   **Basic Tier**: Selling at $29 vs $0.40 cost = **98% Margin** (Healthy).
    *   **Standard Tier**: Selling at $79 vs $1.98 cost = **97% Margin** (Healthy).

### Action Items:
*   **Strict Caching**: Ensure `cache_control` markers are correctly placed (Done).
*   **Context Pruning**: Monitor token usage. If it exceeds 500k, considering pruning the `comprehensive_research` blob before passing it to parallel modules.
