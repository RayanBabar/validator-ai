"""
Research Strategy Module.

Centralizes high-level research strategies used across multiple agents
to prevent code duplication and ensure consistent configuration (e.g. content limits).
"""
import logging
import asyncio
from typing import Optional, List

from src.agents.search.research import conduct_dynamic_research
from src.config.constants import RESEARCH_CONTENT_LIMIT
from src.agents.search.topics import get_research_topics


from src.models.inputs import ValidationState
from src.models.outputs import StrategicDirective
from src.config.prompts import STRATEGIC_DIRECTIVE_PROMPT
from src.agents.base import LLMService

logger = logging.getLogger(__name__)


async def generate_strategic_directive(
    state: ValidationState,
    research_context: str
) -> StrategicDirective:
    """
    Generate the "Truth" document (Strategic Directive) for the startup.
    This runs BEFORE parallel modules to ensure consistency.
    """
    logger.info("Generating Strategic Directive (The Golden Fact Sheet)")
    
    desc = state["inputs"].detailed_description
    title = state.get("generated_title") or "Startup Idea"
    
    # Gather interview Q&A
    questions = state.get("questions_asked", [])
    answers = state.get("user_answers", [])
    qa_pairs = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)]) if questions else "No interview data."

    try:
        # Invoke Smart Model (Claude Sonnet / GPT-5.2)
        directive = await LLMService.invoke_structured(
            StrategicDirective,
            STRATEGIC_DIRECTIVE_PROMPT,
            {
                "title": title,
                "qa_pairs": qa_pairs,
                "research_context": research_context
            },
            use_complex=True, # Critical: Use smart model for strategy
            provider="claude-opus" # Use Opus 4.5 (via 3.5 placeholder) for maximum reasoning
        )
        logger.info(f"Strategic Directive Generated: Pricing={directive.pricing_strategy}")
        return directive
        
    except Exception as e:
        logger.error(f"Failed to generate Strategic Directive: {e}")
        # Fallback (Safe default)
        return StrategicDirective(
            target_customer_segment="Broad market (Default due to error)",
            pricing_strategy="Market standard (Default)",
            core_value_proposition="Solution to defined problem",
            key_strategic_constraints=["None defined"],
            differentiation_strategy="Standard competitive approach",
            year_1_goals="Establish product-market fit with pilot customers",
            primary_metric_goal="User Acquisition"
        )




async def conduct_comprehensive_research(
    description: str,
    geography: str = "global",
    industry: str = "startup",
    tier: str = "basic",
    requested_modules: Optional[List[str]] = None # New filter argument
) -> Optional[str]:
    """
    Conducts comprehensive upfront research for paid tiers.
    
    Strategies:
    - Generates multiple diverse queries (Market, Comp, Finance, Reg, Risks, GTM, Funding)
    - Runs in parallel
    - Returns a single combined string of research context
    
    Args:
        description: Startup description
        geography: Target geography
        industry: Target industry
        tier: Subscription tier (affects depth if needed)
        requested_modules: Optional list of module nodes (e.g. ["mod_market"]) to filter research.
        
    Returns:
        Combined string of research results or None if failed.
    """
    logger.info(f"Conducting comprehensive research strategy for {tier} tier")
    
    try:
        # Dynamic Topic Mapping
        # Maps module node names (from state) to detailed research instructions for the Query Generator LLM.
        # These prompts are optimized based on expert skills (Market Sizing, Financial Modeling, Competitive Analysis).
        topic_map = get_research_topics(geography, industry)
        
        # Determine strict list of topics
        research_topics = []
        
        if requested_modules:
            logger.info(f"Filtering research for {len(requested_modules)} modules: {requested_modules}")
            for mod in requested_modules:
                if mod in topic_map:
                    research_topics.append(topic_map[mod])
            
            # Dependencies: BMC always benefits from Market + Comp
            if "mod_bmc" in requested_modules:
                 if topic_map["mod_market"] not in research_topics:
                     research_topics.append(topic_map["mod_market"])
                 if topic_map["mod_comp"] not in research_topics:
                     research_topics.append(topic_map["mod_comp"])
                     
            if not research_topics:
                # If no mapping found (e.g. only unknown modules), fallback to at least market
                logger.warning("No specific topics mapped from custom modules. Defaulting to Market.")
                research_topics.append(topic_map["mod_market"])
        else:
            # Standard/Premium full suite (default list)
            # Use specific high-value topics (subset of map or full map)
            # Using the original list for consistency
            research_topics = [
                topic_map["mod_market"],
                topic_map["mod_comp"],
                topic_map["mod_finance"],
                topic_map["mod_reg"],
                topic_map["mod_risk"],
                topic_map["mod_gtm"],
                topic_map["mod_funding"]
            ]
        
        # Deduplicate
        research_topics = list(set(research_topics))
        
        logger.info(f"Executing research for {len(research_topics)} topics")
        
        # Execute research queries in parallel
        # We use dynamic_research directly but with explicit high limits
        research_tasks = [
            conduct_dynamic_research(
                description=description, 
                research_objectives={"topic": topic},
                max_length_per_objective=RESEARCH_CONTENT_LIMIT,
                tier=tier # Pass tier to allow dynamic_research to scale query count
            )
            for topic in research_topics
        ]
        
        # dynamic_research returns a dict keys by objective name. 
        # Since we passed a single key dict {"topic": topic}, we expect {"topic": "result"}
        
        results_dicts = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        valid_results = []
        for res in results_dicts:
            if isinstance(res, dict) and "topic" in res and res["topic"]:
                valid_results.append(res["topic"])
            elif isinstance(res, Exception):
                logger.error(f"Research task failed: {res}")
                
        if not valid_results:
            return None
            
        combined_research = "\n\n---\n\n".join(valid_results)
        logger.info(f"Comprehensive research strategy complete: {len(valid_results)} topics, {len(combined_research)} chars")
        return combined_research

    except Exception as e:
        logger.error(f"Comprehensive research strategy failed: {e}")
        # Return whatever we have if list is not empty
        if 'valid_results' in locals() and valid_results:
             logger.warning("Returning partial results despite overall failure.")
             return "\n\n---\n\n".join(valid_results)
        return None
