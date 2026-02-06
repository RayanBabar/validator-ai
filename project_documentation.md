---
title: "AI Startup Validation Agent"
subtitle: "Complete System Documentation"
date: "February 2026"
geometry: "margin=1in"
fontsize: 11pt
colorlinks: true
fontfamily: helvet
header-includes:
  - \renewcommand{\familydefault}{\sfdefault}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhead[R]{AI Startup Validation}
  - \fancyhead[L]{Confidential}
  - \usepackage{xcolor}
  - \definecolor{primary}{HTML}{2C3E50}
  - \definecolor{secondary}{HTML}{34495E}
  - \definecolor{tablehead}{HTML}{E6E6E6}
  - \usepackage{sectsty}
  - \sectionfont{\color{primary}\sffamily}
  - \subsectionfont{\color{secondary}\sffamily}
  - \subsubsectionfont{\color{secondary}\sffamily}
  - \usepackage{setspace}
  - \setstretch{1.15}
  - \usepackage{parskip}
  - \setlength{\parindent}{0pt}
  - \setlength{\parskip}{1em}
  - \usepackage{longtable}
  - \usepackage{booktabs}
  - \usepackage{etoolbox}
  - \usepackage{colortbl}
  - \arrayrulecolor{black}
  - \let\oldlongtable\longtable
  - \let\endoldlongtable\endlongtable
  - \renewenvironment{longtable}{\rowcolors{2}{white}{gray!10}\oldlongtable}{\endoldlongtable}
---

# AI Startup Validation Agent

**Complete System Documentation**

**Purpose**: This document provides a comprehensive explanation of the AI Startup Validation platform, covering how startup ideas are evaluated, scored, and analyzed across different service tiers.

## Table of Contents

1.  Platform Overview
2.  Service Tiers
3.  Complete Validation Workflow
4.  Scoring Methodology
5.  The Interview Process
6.  Report Generation
7.  Analysis Modules
8.  Quality Assurance
9.  Report Delivery

---

## 1. Platform Overview

The AI Startup Validation Agent is a sophisticated multi-tiered platform designed to help entrepreneurs validate their startup ideas using artificial intelligence, web research, competitive intelligence, and financial modeling.

### What Makes This Platform Unique

*   **Hybrid Brain Architecture**:
    *   **The Brain (Opus 4.5)**: Handles high-stakes strategic reasoning and final scoring.
    *   **The Workers (Sonnet 4.5)**: Execute deep-dive research and content generation.
    *   **The Speed Layer (Haiku 4.5 / GPT-5-mini)**: Powers real-time conversational interviews.
*   **Intelligent Caching**: Implements 2026-standard prompt caching with explicit `cache_control` markers, reducing analysis latency and cost by ~90% for deep context tasks.
*   **Real-Time Research**: Integrates with Tavily Search API for up-to-date market data.
*   **European Focus**: All analysis is tailored for European markets, including GDPR compliance.

### Core Capabilities

| Capability | Description |
| :--- | :--- |
| **Intelligent Interviewing** | **Haiku 4.5** conducts rapid clarifying questions to understand your idea. |
| **Strategic Reasoning** | **Opus 4.5** generates a "Strategic Directive" to ensure consistency. |
| **Market Research** | Automated web searches gather real-time market data. |
| **Competitive Analysis** | Identifies and analyzes direct and indirect competitors. |
| **Financial Modeling** | Projects 3-year financials with break-even analysis. |
| **Scoring** | **Opus 4.5** provides a final Go/No-Go verdict based on all data. |

---

## 2. Service Tiers

The platform offers four distinct service levels:

| Feature | Free | Basic | Standard | Premium |
| :--- | :--- | :--- | :--- | :--- |
| **Output Length** | ~300 words | 1,500 words | 25,000 words | 25,000 words |
| **Page Count** | ½ page | 2-3 pages | 40-50 pages | 40-50 pages |
| **Generation Time** | ~3 min | ~3 min | ~10-15 min | ~10-15 min |
| **Score Type** | Viability | Go/No-Go | Go/No-Go | Go/No-Go |
| **Analysis** | Quick Scan | BMC | 10 Modules | 10 Modules + Pitch Deck |

---

## 3. Complete Validation Workflow

### Workflow Diagram

![Complete Validation Workflow](workflow.png)

### Phase-by-Phase Breakdown

#### Phase 1: Intelligent Interview (All Tiers)
**Node**: `interviewer_node`
**Model**: **Claude Haiku 4.5**
The system analyzes your initial description and asks 5-10 tailored questions. We use Haiku 4.5 for this phase to ensure sub-1-second latency for a conversational feel.

#### Phase 2: Research & Context Extraction
**Node**: `research_node`
**Model**: **GPT-5-mini** (Synthesis) + **Tavily**
Upon interview completion, the system:
1.  Extracts specific context (Geography, Industry) using **GPT-5-mini**.
2.  Generates dynamic Tavily search queries.
3.  Synthesizes Q&A + Research into an "Enriched Context".

#### Phase 3: Free Report Generation
**Node**: `free_tier_node`
**Model**: **Claude Sonnet 4.5**
A more powerful model (**Sonnet 4.5**) is used to generate the initial Viability Score and Value Proposition, ensuring high-quality initial feedback.

#### Phase 4: Strategic Strategy (Paid Tiers)
**Node**: `strategy_node`
**Model**: **Claude Opus 4.5**
Before generating the full report, the "Brain" (**Opus 4.5**) analyzes the entire context to generate a **Strategic Directive**. This document defines the "Truth" (e.g., "target enterprise customers, not SMBs") that all subsequent modules must follow.

#### Phase 5: Standard/Premium Modules
**Node**: `parallel_execution`
**Model**: **Claude Sonnet 4.5**
10 specialized agents run in parallel. Each uses **Sonnet 4.5** for its balance of high intelligence and speed/cost efficiency. They strictly adhere to the *Strategic Directive*.

#### Phase 6: Compilation & Scoring
**Node**: `compiler_node`
**Model**: **Claude Opus 4.5**
The final compilation is a high-stakes task. **Opus 4.5** aggregates all 10 modules, performs a final consistency check, and calculates the data-driven **Go/No-Go Score**.

#### Phase 7: Pitch Deck (Premium Only)
**Node**: `_generate_pitch_deck`
**Model**: **Claude Sonnet 4.5**
Converts the comprehensive report into a 12-slide investor presentation structure.

---

## 4. Scoring Methodology

### Free Tier: Viability Score
Calculated based on 5 dimensions (Problem, Market, Competition, Execution, Founder).

### Paid Tiers: Go/No-Go Score
A comprehensive 8-dimension score calculated by **Opus 4.5** based on the full depth of the 10-module analysis and fresh market verification.

---

## 5. The Interview Process
Uses **Haiku 4.5** to simulate a rapid-fire discovery session with a senior consultant. It probes gaps in your business model (e.g., "You mentioned B2B, but who is the buyer vs the user?").

---

## 6. Report Generation
*   **Free Tier**: ~3 min (Sonnet 4.5)
*   **Basic Tier**: ~3 min (Sonnet 4.5)
*   **Standard/Premium**: ~10-15 min (Parallel Sonnet 4.5 execution)

---

## 7. Analysis Modules
(10 Standard Modules generated by Sonnet 4.5)
1.  Business Model Canvas
2.  Market Analysis
3.  Competitive Intelligence
4.  Financial Feasibility
5.  Technical Requirements
6.  Regulatory Compliance
7.  Go-to-Market Strategy
8.  Risk Assessment
9.  Implementation Roadmap
10. Funding Strategy

---

## 8. Quality Assurance

### Hybrid Architecture
We optimize for both quality and cost:
*   **Reasoning**: **Opus 4.5** (Strategy, Scoring)
*   **Production**: **Sonnet 4.5** (Modules, Pitch Deck)
*   **Speed**: **Haiku 4.5** (Interview)

### Prompt Caching
To execute 10 parallel deep-dive modules without exorbitant costs, we use **Explicit Cache Control**. The "Strategic Directive" and context (~15k tokens) are cached, reducing the input cost for the 10 parallel agents by 90%.

---

## 9. Report Delivery
Full JSON reports are delivered via API (`GET /report/{id}`) or converted to PDF (`POST /generate-html`). Webhooks notify external systems upon completion.
