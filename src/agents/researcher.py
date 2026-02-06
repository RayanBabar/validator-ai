"""
Research Node Logic.
Conducts initial market trend research before splitting into tiers.
Also handles synthesis and quality evaluation when interview completes.
"""

import logging
from src.models.inputs import ValidationState
from src.agents.interviewer import synthesize_context, evaluate_interview_quality

logger = logging.getLogger(__name__)


async def conduct_research(state: ValidationState):
    """
    Conduct research, synthesis, and quality evaluation after interview completes.

    This node runs in background (via interrupt_before) so API can return immediately.

    1. Conducts market research using Tavily
    2. Synthesizes founder Q&A + research into enriched context
    3. Evaluates interview quality for scoring adjustments

    Args:
        state: Current validation state with interview data

    Returns:
        Updated state with search_context, enriched_context, and quality scores
    """
    inp = state["inputs"]
    desc = inp.detailed_description if inp else "startup idea"

    logger.info("Research node: Starting synthesis and quality evaluation")

    # 1. Execute independent LLM tasks in parallel
    # synthesize_context = does research (60s+)
    # evaluate_interview_quality = analyzes Q&A (15s)
    import asyncio
    
    logger.info("Research node: Executing synthesis and quality evaluation in parallel")
    
    # Run concurrently
    # Return exceptions=True to prevent one failure from crashing the other
    results = await asyncio.gather(
        synthesize_context(state),
        evaluate_interview_quality(state),
        return_exceptions=True
    )
    
    enriched = results[0]
    quality_scores = results[1]
    
    # Handle exceptions
    if isinstance(enriched, Exception):
        logger.error(f"Synthesis failed in parallel execution: {enriched}")
        enriched = {} # Fallback
    
    if isinstance(quality_scores, Exception):
        logger.error(f"Quality evaluation failed in parallel execution: {quality_scores}")
        quality_scores = {"clarity_score": 5.0, "answer_quality_score": 5.0} # Fallback

    # 2. Extract context information from synthesis result (if available)
    context_extraction = {}
    extracted_geography = "global market"
    extracted_industry = "startup"
    extracted_regulatory_context = "general business"
    context_specificity_score = 5.0

    logger.info(f"Synthesis result type: {type(enriched).__name__}")

    if isinstance(enriched, dict):
        logger.info(f"✓ Synthesis returned dict with keys: {list(enriched.keys())}")
        context_extraction = enriched.get("context_extraction", {})
        if context_extraction:
            logger.info(
                f"✓ Context extraction found with keys: {list(context_extraction.keys())}"
            )
            extracted_geography = context_extraction.get(
                "primary_geography", "global market"
            )
            extracted_industry = context_extraction.get("primary_industry", "startup")
            regulatory_list = context_extraction.get("regulatory_context", [])
            extracted_regulatory_context = (
                ", ".join(regulatory_list) if regulatory_list else "general business"
            )
            context_specificity_score = float(
                context_extraction.get("context_confidence", 5.0)
            )
            logger.info(
                f"✓ Extracted: geography={extracted_geography}, industry={extracted_industry}, specificity={context_specificity_score}"
            )
        else:
            logger.warning("⚠ Synthesis dict missing 'context_extraction' key")
    else:
        logger.warning(f"⚠ Synthesis returned non-dict type: {type(enriched).__name__}")
        logger.warning(f"⚠ Content preview: {str(enriched)[:200]}...")

    # 3. Create context for downstream nodes
    # OPTIMIZATION: Removed redundant search_with_tavily call (15-20s saving)
    # Instead, we construct context from the synthesis output itself, which contains verified research.
    
    try:
        # Use the synthesized "detailed_description", "market_indicators", "competitor_analysis" as the context
        # This is high-quality, verified, and citation-backed text from Claude.
        context_parts = []
        
        if isinstance(enriched, dict):
            if enriched.get("market_indicators"):
                context_parts.append(f"MARKET INDICATORS:\n{enriched['market_indicators']}")
            if enriched.get("competitor_analysis"):
                context_parts.append(f"COMPETITOR ANALYSIS:\n{enriched['competitor_analysis']}")
            if enriched.get("detailed_description"):
                context_parts.append(f"SYNTHESIZED OVERVIEW:\n{enriched['detailed_description']}")
                
        if context_parts:
            context = "\n\n".join(context_parts)
            logger.info("✓ Using synthesized intelligence for report context (Zero Search Overhead)")
        else:
            # Only fallback to search if synthesis completely failed to yield text
            logger.warning("Synthesis text missing, falling back to minimal search")
            from src.agents.base import search_with_tavily
            context = await search_with_tavily(f"market overview {extracted_industry} {extracted_geography}")
            
    except Exception as e:
        logger.warning(f"Context assembly failed: {e}")
        context = "Market data unavailable."

    logger.info(
        f"Research complete: clarity={quality_scores.get('clarity_score', 5.0)}, answer_quality={quality_scores.get('answer_quality_score', 5.0)}"
    )
    logger.info(
        f"Extracted context: geography={extracted_geography}, industry={extracted_industry}, specificity={context_specificity_score}"
    )

    # Get dimension-specific quality scores for granular viability adjustments
    dimension_quality = quality_scores.get(
        "dimension_quality",
        {
            "problem_understanding": 5.0,
            "market_knowledge": 5.0,
            "competitive_awareness": 5.0,
            "execution_readiness": 5.0,
            "founder_credibility": 5.0,
        },
    )

    # PERFORMANCE OPTIMIZATION: Gather comprehensive research upfront for paid tiers
    # This eliminates per-module search overhead (reduces 10x Tavily calls to 1x)
    comprehensive_research = None
    tier = inp.tier if inp else "free"
    
    if tier in ("standard", "premium", "custom"):
        logger.info(f"Performing comprehensive upfront research for {tier} tier")
        try:
            # Use centralized strategy to ensure consistent, skill-optimized prompts
            from src.agents.search.strategy import conduct_comprehensive_research
            
            comprehensive_research = await conduct_comprehensive_research(
                description=desc,
                geography=extracted_geography,
                industry=extracted_industry,
                tier=tier
            )
            
            if comprehensive_research:
                logger.info(f"Comprehensive research complete: {len(comprehensive_research)} chars")
        except Exception as e:
            logger.error(f"Comprehensive research failed: {e}")
            comprehensive_research = None

    return {
        "search_context": context,
        "enriched_context": enriched,
        "clarity_score": quality_scores.get("clarity_score", 5.0),
        "answer_quality_score": quality_scores.get("answer_quality_score", 5.0),
        "dimension_quality": dimension_quality,
        # Store extracted context for downstream use
        "extracted_industry": extracted_industry,
        "extracted_geography": extracted_geography,
        "extracted_regulatory_context": extracted_regulatory_context,
        "context_specificity_score": context_specificity_score,
        # PERFORMANCE: Pre-fetched comprehensive research for modules
        "comprehensive_research": comprehensive_research,
    }
