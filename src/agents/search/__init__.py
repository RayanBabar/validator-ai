"""
Search Agent Package.

Modular research functionality for startup validation.

Modules:
- credibility: Source credibility scoring
- query_generator: LLM-powered query generation
- tools: Web search and date tools (internal use)
- query_generator: LLM-powered query generation
- tools: Web search and date tools (internal use)
- research: Main research functions
"""
from src.agents.search.credibility import (
    score_source_credibility,
    HIGH_CREDIBILITY_DOMAINS,
    MEDIUM_CREDIBILITY_DOMAINS,
)
from src.agents.search.query_generator import (
    generate_llm_queries,
)

from src.agents.search.research import (
    conduct_dynamic_research,
    dynamic_research,
    generate_dynamic_search_queries,
)

__all__ = [
    # Credibility
    "score_source_credibility",
    "HIGH_CREDIBILITY_DOMAINS",
    "MEDIUM_CREDIBILITY_DOMAINS",
    # Query Generation
    "generate_llm_queries",

    # Research Functions
    "conduct_dynamic_research",
    "dynamic_research",
    "generate_dynamic_search_queries",
]
