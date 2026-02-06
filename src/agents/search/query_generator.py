"""
LLM-Powered Query Generation for Research.

Uses LLM to generate optimal search queries for comprehensive research.
"""

import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate

from src.utils.date_utils import get_current_year

logger = logging.getLogger(__name__)

QUERY_GENERATION_PROMPT = ChatPromptTemplate.from_template("""
You are a search query optimization expert. Generate 4-5 diverse, high-quality search queries 
to research a startup idea comprehensively.

STARTUP IDEA:
{description}

RESEARCH OBJECTIVE:
{objective}

CURRENT YEAR: {current_year}

Generate queries that:
1. Cover different aspects (market size, competitors, trends, news)
2. REQUIRE separate queries for: "market size", "competitors", "trends"
3. Are specific and actionable (not vague)
4. Focus on target geography where relevant
5. STRICTLY INCLUDE {current_year} or {current_year}-plus-1 for forward looking data

Return ONLY a JSON array of 4-5 search queries.
["query 1", "query 2", "query 3", "query 4"]

EXAMPLE for "AI invoice processing for accounting firms":
[
    "AI invoice processing automation market size global 2026",
    "invoice OCR software competitors Basware Coupa Tipalti comparison",
    "accounting automation trends DACH region fintech",
    "B2B SaaS invoice processing startup funding news 2026"
]
""")


async def generate_llm_queries(
    description: str, research_objective: str, num_queries: int = 4
) -> List[str]:
    """
    Use LLM to generate optimal search queries for research.

    Args:
        description: The startup idea description
        research_objective: What to research (market, competitors, etc.)
        num_queries: Number of queries to generate

    Returns:
        List of optimized search queries
    """
    current_year = get_current_year()

    try:
        # Replaced direct LLM pipe with unified LLMService
        from src.agents.base import LLMService

        result = await LLMService.invoke(
            QUERY_GENERATION_PROMPT,
            {
                "description": description,
                "objective": research_objective,
                "current_year": current_year,
            },
            provider="auto",
            parse_json=True
        )

        if isinstance(result, list):
            queries = result[:num_queries]
            logger.info(
                f"LLM generated {len(queries)} queries for '{research_objective[:30]}...'"
            )
            return queries
        else:
            logger.warning(f"LLM returned non-list: {type(result)}")
            return _fallback_queries(description, research_objective, current_year)

    except Exception as e:
        logger.warning(f"LLM query generation failed: {e}")
        return _fallback_queries(description, research_objective, current_year)


def _fallback_queries(description: str, objective: str, year: int) -> List[str]:
    """Fallback to simple query generation if LLM fails."""
    # Simple stopword removal to get better keywords
    stop_words = {"a", "an", "the", "for", "of", "in", "on", "at", "to", "with", "by", "from", "is", "are", "startup", "idea"}
    words = [w for w in description.split() if w.lower() not in stop_words and len(w) > 2]
    keywords = " ".join(words[:6]) # First 6 meaningful words
    
    return [
        f"{keywords} {objective} {year}",
        f"{keywords} market size trends {year}",
        f"{keywords} top competitors review",
        f"{keywords} industry analysis report {year}",
    ]
