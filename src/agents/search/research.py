"""
Research Functions for Startup Validation.

High-level research functions using dynamic_research with:
- LLM-generated optimal search queries
- Source credibility scoring
- Parallel query execution
"""
import logging
import asyncio
from typing import Dict, List

from src.agents.base import search_with_tavily_detailed
from src.agents.search.query_generator import generate_llm_queries
from src.agents.search.credibility import score_source_credibility
from src.models.inputs import ValidationState
from src.config.constants import RESEARCH_CONTENT_LIMIT

logger = logging.getLogger(__name__)


async def conduct_scoring_research(state: ValidationState) -> dict:
    """
    Conducts internet research specifically for Go/No-Go scoring.

    UNIFIED SCORING BASELINE:
    Always uses 4 queries per objective regardless of tier.
    This ensures the Go/No-Go score is consistent and robust,
    preventing score changes when users upgrade tiers.

    Args:
        state: Current validation state with inputs

    Returns:
        Dictionary with research results for each scoring dimension
    """
    inputs = state.get("inputs")
    desc = inputs.detailed_description if inputs else "startup idea"

    # Extract dynamic context for parameterized research
    geography = state.get("extracted_geography", "global market")
    industry = state.get("extracted_industry", "")

    # Use centralized strategy prompts for consistency
    # Map scoring dimensions to strategy module keys
    from src.agents.search.topics import get_research_topics
    topics = get_research_topics(geography, industry)
    
    research_objectives = {
        "market_demand": topics.get("mod_market"),
        "competition": topics.get("mod_comp"),
        "timing": topics.get("mod_market"), # Reuse market trends for timing
        "regulatory": topics.get("mod_reg"),
        "scalability": topics.get("mod_risk"), # Use risk/challenges to infer scalability barriers
    }

    # FORCE num_queries=4 for scoring consistency (approx $0.02 cost)
    research_results = await conduct_dynamic_research(
        description=desc,
        research_objectives=research_objectives,
        max_length_per_objective=RESEARCH_CONTENT_LIMIT,
        tier="scoring_baseline" # Internal tier that maps to 4 queries
    )

    return research_results


async def dynamic_research(
    description: str,
    research_objective: str,
    max_length: int = 6000,
    min_credibility: int = 4,
    num_queries: int = 2
) -> str:
    """
    Perform high-quality research using LLM-GENERATED QUERIES, MULTI-QUERY strategy, 
    and SOURCE CREDIBILITY SCORING.
    
    This is the PRIMARY research function used across all modules.
    
    Uses LLM to generate optimal, diverse queries instead of manual keyword extraction.
    Runs queries in parallel, scores sources by credibility, and aggregates results.
    
    Args:
        description: The startup idea description
        research_objective: What to research (e.g., "market size and growth rate")
        max_length: Maximum result length
        min_credibility: Minimum credibility score to include (1-10)
        num_queries: Number of parallel queries to run (Dynamic based on tier)
        
    Returns:
        Aggregated research results from high-credibility sources
    """
    # Use LLM to generate optimal search queries 
    queries = await generate_llm_queries(description, research_objective, num_queries=num_queries)
    
    logger.info(f"Executing {len(queries)} LLM-generated queries with credibility scoring")
    
    # Execute queries in parallel for speed
    async def search_query_detailed(query: str) -> List[Dict]:
        try:
            results = await search_with_tavily_detailed(query)
            return results if results else []
        except Exception as e:
            logger.warning(f"Search query failed: {query[:50]}... - {e}")
            return []
    
    # Run all queries concurrently
    all_results = await asyncio.gather(*[search_query_detailed(q) for q in queries])
    
    # Flatten results and score credibility
    flat_results = []
    for results in all_results:
        flat_results.extend(results)
    
    # Apply credibility scoring
    scored_results = []
    for result in flat_results:
        url = result.get("url", "")
        score, level = score_source_credibility(url)
        
        if score >= min_credibility:
            result["credibility_score"] = score
            result["credibility_level"] = level
            scored_results.append(result)
    
    # FALLBACK: If strict filtering yielded no results, try with lower threshold
    if not scored_results and flat_results:
        logger.warning(f"No results met min_credibility={min_credibility}. Retrying with threshold=1 (Accept All).")
        for result in flat_results:
            # We already computed score above, but need to re-check or just add all
            # Since we didn't store scores in flat_results in the loop above (we computed on fly), 
            # let's re-score or better yet, simple re-loop since it's cheap.
            url = result.get("url", "")
            score, level = score_source_credibility(url)
            # Accept anything with score >= 1 (which is everything)
            result["credibility_score"] = score
            result["credibility_level"] = level
            scored_results.append(result)
    
    # Sort by credibility (highest first)
    scored_results.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
    
    # Aggregate unique content (deduplicate and prioritize high-credibility)
    aggregated = []
    seen_content = set()
    high_cred_count = 0
    
    for result in scored_results:
        content = result.get("content", "")
        if content:
            # Dedup by first 100 chars
            content_key = content[:100].lower()
            if content_key not in seen_content:
                seen_content.add(content_key)
                
                # Format with credibility indicator for high sources
                cred_level = result.get("credibility_level", "unknown")
                if cred_level == "high":
                    high_cred_count += 1
                    formatted = f"[HIGH CREDIBILITY SOURCE]\n{content[:1500]}"
                else:
                    formatted = content[:1500]
                    
                aggregated.append(formatted)
    
    combined = "\n\n---\n\n".join(aggregated)
    
    # -------------------------------------------------------------
    # NULL RESULT VERIFICATION LOOP (New Logic)
    # -------------------------------------------------------------
    # If standard search yields NOTHING useful, perform one "Broad Retry".
    # Condition: combined result is empty OR just the "No credible research" string.
    is_null_result = not combined or "No credible research data available" in combined
    
    if is_null_result:
        logger.warning(f"Null result detected for: '{research_objective}'. Attempting BROAD RETRY.")
        
        # Fallback Strategy: Simplify the query to just the core topic + "overview"
        # We ask LLM for a simplified query, or just strip complexity manually.
        # Here we reuse the query generator with a "broad" instruction hint.
        
        try:
            broad_queries = await generate_llm_queries(
                description, 
                f"Broad overview of {research_objective} (GENERAL TERMS ONLY)", 
                num_queries=1 # Just one broad net
            )
            
            if broad_queries:
                retry_query = broad_queries[0]
                logger.info(f"Executing Broad Retry Query: {retry_query}")
                
                # Execute single broad query without strict credibility filtering (accept everything)
                retry_results = await search_with_tavily_detailed(retry_query)
                
                if retry_results:
                    retry_content = []
                    for res in retry_results:
                        if res.get("content"):
                            retry_content.append(f"[BROAD RETRY SOURCE] {res['content'][:1000]}")
                    
                    if retry_content:
                        logger.info(f"Broad Retry successful. Found {len(retry_content)} general sources.")
                        combined = "\n\n---\n\n".join(retry_content)
                    else:
                        logger.warning("Broad Retry found results but no content.")
                else:
                    logger.warning("Broad Retry returned no results.")
        except Exception as e:
            logger.error(f"Broad Retry logic failed: {e}")

    # -------------------------------------------------------------
    # CREATIVE RETRY (New Logic)
    # -------------------------------------------------------------
    # If Broad Retry also failed, try a "Creative" approach for non-obvious results.
    if not combined or "No credible research data available" in combined:
         try:
            logger.info(f"Broad Retry failed. Attempting CREATIVE RETRY for {research_objective}...")
            creative_queries = await generate_llm_queries(
                description,
                f"Creative synonymous terms for {research_objective} (industry jargon, alternative phrasing)",
                num_queries=1
            )
            if creative_queries:
                c_query = creative_queries[0]
                c_results = await search_with_tavily_detailed(c_query)
                if c_results:
                    # Accept any result to avoid empty report
                    c_content = [f"[CREATIVE RETRY SOURCE] {r['content'][:1000]}" for r in c_results if r.get("content")]
                    if c_content:
                        logger.info(f"Creative Retry successful. Found {len(c_content)} sources.")
                        combined = "\n\n---\n\n".join(c_content)
         except Exception as e:
             logger.error(f"Creative Retry logic failed: {e}")

    # Final check
    if not combined:
        return f"No credible research data available for {research_objective}."
    
    logger.info(f"Research complete: {len(aggregated)} distinct sources details.")
    return combined[:max_length]


async def conduct_dynamic_research(
    description: str,
    research_objectives: dict[str, str],
    max_length_per_objective: int = 1500,
    tier: str = "basic"
) -> dict[str, str]:
    """
    Conduct research for multiple objectives using dynamic_research.
    
    Used by interviewer and compiler for multi-objective research.
    
    Args:
        description: The startup idea description
        research_objectives: Dict mapping objective keys to descriptions
        max_length_per_objective: Maximum result length per objective
        tier: User tier to determine query depth (basic=2, standard=4, premium=6)
        
    Returns:
        Dict mapping objective keys to research results
    """
    # Map tier to number of queries
    # Free/Basic: 2 queries (Speed/Cost priority)
    # Standard: 4 queries (Depth priority)
    # Premium: 4 queries (Deep dive)
    # Scoring Baseline: 4 queries (Consistency priority)
    tier_query_map = {
        "free": 1,
        "basic": 1,
        "standard": 1,
        "premium": 1,
        "custom": 1,
        "scoring_baseline": 1 # Used internally for consistent scores
    }
    
    num_queries = tier_query_map.get(tier, 2)
    logger.info(f"Conducting dynamic research for tier='{tier}' with {num_queries} queries per objective")

    results = {}
    
    # Run all objectives in parallel for speed
    async def research_objective(key: str, objective: str) -> tuple[str, str]:
        content = await dynamic_research(
            description=description,
            research_objective=objective,
            max_length=max_length_per_objective,
            num_queries=num_queries
        )
        return key, content
    
    tasks = [research_objective(k, v) for k, v in research_objectives.items()]
    completed = await asyncio.gather(*tasks)
    
    for key, content in completed:
        results[key] = content
        
    return results


# Backward compatibility alias
async def generate_dynamic_search_queries(
    description: str,
    research_objective: str,
    num_queries: int = 3
) -> list[str]:
    """
    Use LLM to generate optimal search queries.
    Backward compatible with the old search_agent.py interface.
    """
    return await generate_llm_queries(description, research_objective, num_queries)
