"""
Interviewer Agent.
Conducts clarifying questions and synthesizes context for validation.
Uses LLMService for LLM invocations with automatic Claude fallback.
"""

import logging

from src.agents.base import LLMService
from src.models.inputs import ValidationState
from src.config.prompts import (
    INTERVIEW_PROMPT,
    SYNTHESIS_PROMPT,
    INTERVIEW_QUALITY_PROMPT,
    INITIAL_CONTEXT_EXTRACTION_PROMPT,
    CONTEXT_AND_OBJECTIVES_PROMPT,
    CONTEXT_AND_OBJECTIVES_PROMPT,
)
from src.utils.date_utils import get_date_context
from src.config.constants import MIN_INTERVIEW_QUESTIONS, MAX_INTERVIEW_QUESTIONS, RESEARCH_CONTENT_LIMIT
from src.agents.search.research import conduct_dynamic_research

logger = logging.getLogger(__name__)


async def evaluate_interview_quality(state: ValidationState) -> dict:
    """
    Evaluate the clarity of business idea and quality of interview answers.

    Uses LLM to score:
    - clarity_score: How clear and well-defined is the business concept (0-10)
    - answer_quality_score: How well did the founder answer questions (0-10)

    Args:
        state: Current validation state with questions and answers

    Returns:
        Dictionary with clarity_score, answer_quality_score, and reasoning
    """
    inputs = state.get("inputs")
    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])

    business_idea = inputs.detailed_description if inputs else ""

    # Format Q&A for prompt
    qa_pairs = (
        "\n".join(
            [
                f"Q{i + 1}: {q}\nA{i + 1}: {a}"
                for i, (q, a) in enumerate(zip(questions_asked, user_answers))
            ]
        )
        or "No Q&A conducted"
    )

    try:
        result = await LLMService.invoke(
            INTERVIEW_QUALITY_PROMPT,
            {
                "business_idea": business_idea,
                "qa_pairs": qa_pairs,
            },
            use_complex=False,
            parse_json=True,
        )

        clarity_score = float(result.get("clarity_score", 5.0))
        answer_quality_score = float(result.get("answer_quality_score", 5.0))

        logger.info(
            f"Interview quality evaluated: clarity={clarity_score}, answer_quality={answer_quality_score}"
        )

        return {
            "clarity_score": clarity_score,
            "answer_quality_score": answer_quality_score,
            "clarity_reasoning": result.get("clarity_reasoning", ""),
            "answer_quality_reasoning": result.get("answer_quality_reasoning", ""),
            "key_strengths": result.get("key_strengths", []),
            "key_concerns": result.get("key_concerns", []),
        }

    except Exception as e:
        logger.warning(f"Failed to evaluate interview quality: {e}")
        # Return neutral scores on failure
        return {
            "clarity_score": 5.0,
            "answer_quality_score": 5.0,
        }


async def interviewer_node(state: ValidationState) -> dict:
    """
    Analyzes input and decides if more clarification is needed.

    Returns next question or marks interview as complete.
    Interview completes when:
    - LLM determines enough info gathered AND at least MIN_INTERVIEW_QUESTIONS asked, OR
    - MAX_INTERVIEW_QUESTIONS reached

    NOTE: When interview completes, this node returns immediately.
    Synthesis and quality evaluation happen in the research node (runs in background).

    Args:
        state: Current validation state

    Returns:
        Updated state with interview_phase, questions, and workflow_phase
    """
    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])
    num_questions_asked = len(questions_asked)
    questions_remaining = MAX_INTERVIEW_QUESTIONS - num_questions_asked

    # If max questions reached, force complete - return immediately
    if questions_remaining <= 0:
        logger.info("Max questions reached, completing interview")
        return {
            "interview_phase": "complete",
            "workflow_phase": "free_report",
        }

    # Format Q&A history for prompt
    prev_q = (
        "\n".join([f"Q{i + 1}: {q}" for i, q in enumerate(questions_asked)])
        or "None yet"
    )
    prev_a = (
        "\n".join([f"A{i + 1}: {a}" for i, a in enumerate(user_answers)]) or "None yet"
    )

    # Get input from state
    inputs = state.get("inputs")
    business_idea = inputs.detailed_description if inputs else ""

    # Get date context for prompt
    date_context = get_date_context()

    # Ask LLM if more info needed (with fallback)
    try:
        result = await LLMService.invoke(
            INTERVIEW_PROMPT,
            {
                "current_date": date_context["current_date"],
                "business_idea": business_idea,
                "previous_questions": prev_q,
                "previous_answers": prev_a,
                "questions_asked": num_questions_asked + 1,
                "max_questions": MAX_INTERVIEW_QUESTIONS,
            },
            use_complex=False,
            parse_json=True,
            provider="openai",
        )
    except Exception as e:
        logger.error(f"Interview LLM error (both OpenAI and Claude failed): {e}")
        return {"interview_phase": "complete", "workflow_phase": "free_report"}

    # Decide based on LLM response
    llm_wants_more_info = result.get("needs_more_info", False)
    has_next_question = bool(result.get("next_question"))
    min_questions_met = num_questions_asked >= MIN_INTERVIEW_QUESTIONS

    # Continue interview if:
    # 1. LLM wants more info AND has a question, OR
    # 2. Minimum questions not yet reached (force continue)
    if (llm_wants_more_info and has_next_question) or not min_questions_met:
        new_question = result.get(
            "next_question", "Can you tell me more about your target customers?"
        )
        logger.info(
            f"Asking question {num_questions_asked + 1}/{MAX_INTERVIEW_QUESTIONS}: {new_question[:50]}..."
        )
        return {
            "interview_phase": "asking",
            "current_question": new_question,
            "questions_asked": questions_asked + [new_question],
            "workflow_phase": "interview",
        }
    else:
        # LLM says enough info AND min questions met - return immediately
        logger.info(f"Interview complete after {num_questions_asked} questions")
        return {
            "interview_phase": "complete",
            "current_question": None,
            "workflow_phase": "free_report",
        }




async def extract_initial_context(state: ValidationState, qa_pairs: list[str]) -> dict:
    """
    Extracts initial geography and industry context from business idea + Q&A.
    """
    inputs = state.get("inputs")
    business_idea = inputs.detailed_description if inputs else ""
    date_context = get_date_context()


    try:
        result = await LLMService.invoke(
            INITIAL_CONTEXT_EXTRACTION_PROMPT,
            {
                "current_date": date_context["current_date"],
                "business_idea": business_idea,
                "qa_pairs": qa_pairs,
            },
            use_complex=False,
            parse_json=True,
        )
        return result
    except Exception as e:
        logger.warning(f"Context extraction failed: {e}")
        return {}


async def synthesize_context(state: ValidationState) -> dict:
    """
    Synthesizes founder Q&A + Tavily web research into structured context.

    Automatically researches complex info so users only answer simple questions.
    Uses OpenAI with Claude fallback.

    Args:
        state: Current validation state

    Returns:
        Synthesized context dict with nested context_extraction structure
    """
    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])
    inputs = state.get("inputs")

    # Format Q&A pairs
    qa_pairs = (
        "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions_asked, user_answers)])
        or "No additional Q&A conducted"
    )

    business_idea = inputs.detailed_description if inputs else ""

    # First, extract initial context and generate research objectives in ONE step (Optimization)
    logger.info("Synthesis: Extracting context and generating objectives (Merged Step)")
    
    try:
        merged_result = await LLMService.invoke(
            CONTEXT_AND_OBJECTIVES_PROMPT,
            {
                "current_date": get_date_context()["current_date"],
                "business_idea": business_idea,
                "qa_pairs": qa_pairs,
            },
            use_complex=False,
            parse_json=True,
        )
        
        # Extract components from merged result
        initial_context = merged_result.get("context", {})
        research_objectives = merged_result.get("research_objectives", {})
        
        logger.info(f"Merged Extraction Successful. Keys: {list(merged_result.keys())}")
        
    except Exception as e:
        logger.error(f"Merged prompt failed: {e}. Falling back to sequential execution.")
        # Fallback to sequential execution if merged prompt fails
        initial_context = await extract_initial_context(state, qa_pairs)
        # ... logic for fallback objectives generation (omitted for brevity, assume simple fallback)
        research_objectives = {
            "market_research": f"market size {initial_context.get('primary_industry', 'startup')} {initial_context.get('primary_geography', 'global')}",
            "competitor_research": f"competitors {initial_context.get('primary_industry', 'startup')}",
            "industry_research": f"trends {initial_context.get('primary_industry', 'startup')}"
        }

    # Store extracted context in state for downstream use
    extracted_geography = initial_context.get("primary_geography", "global market")
    extracted_industry = initial_context.get("primary_industry", "startup")
    refined_industry = initial_context.get("refined_industry_context", extracted_industry) # Use refined if available
    regulatory_context_list = initial_context.get("regulatory_context", [])
    
    # Use optimized keywords if available, otherwise fallback to templates
    optimized_keywords = initial_context.get("optimized_search_keywords", [])

    logger.info(
        f"Synthesis: Using refined context: {extracted_geography}, {refined_industry}"
    )
    logger.info(f"Generated Dynamic Research Queries: {research_objectives}")

    # OPTIMIZATION: Inject refined keywords into description to guide query generator
    search_description = business_idea
    if optimized_keywords:
        formatted_keywords = ", ".join(optimized_keywords)
        search_description += f"\n\nSuggested Search Keywords: {formatted_keywords}"
        logger.info(f"Injecting optimized keywords into search context: {formatted_keywords}")

    research_results = await conduct_dynamic_research(
        description=search_description,
        research_objectives=research_objectives,
        max_length_per_objective=RESEARCH_CONTENT_LIMIT,
    )

    try:
        result = await LLMService.invoke(
            SYNTHESIS_PROMPT,
            {
                "business_idea": business_idea,
                "qa_pairs": qa_pairs,
                "market_research": research_results.get("market_research", ""),
                "competitor_research": research_results.get("competitor_research", ""),
                "industry_research": research_results.get("industry_research", ""),
            },
            use_complex=False,
            parse_json=True,
            provider="openai",  # PERFORMANCE OPTIMIZATION: Switched to OpenAI (faster than Claude)
        )

        logger.info("Synthesis successful, returning dict")
        return result

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        # Return minimal dict structure for consistency
        logger.warning("Returning fallback dict instead of full synthesis")
        return {
            "idea_title": f"Analysis of {business_idea[:50]}...",
            "problem_statement": "Unable to synthesize full context due to technical error",
            "target_customer": "Unknown",
            "market_indicators": "Unable to process",
            "competitor_analysis": "Unable to analyze",
            "revenue_model": "Unknown",
            "differentiation": "Unable to determine",
            "founder_fit": "Unknown",
            "industry": extracted_industry,
            "target_market": extracted_geography,
            "detailed_description": f"Technical error occurred during synthesis: {str(e)[:100]}",
            "context_extraction": {
                "primary_geography": extracted_geography,
                "geographic_scope": "national"
                if extracted_geography != "global market"
                else "global",
                "primary_industry": extracted_industry,
                "industry_keywords": [extracted_industry],
                "regulatory_context": regulatory_context_list,
                "regulatory_specificity": "medium"
                if extracted_geography != "global market"
                else "low",
                "currency": "Not specified",
                "context_confidence": initial_context.get("context_confidence", 5.0),
            },
            # EXPLICIT STATE POPULATION for downstream modules
            "extracted_geography": extracted_geography,
            "extracted_industry": extracted_industry,
            "extracted_regulatory_context": ", ".join(regulatory_context_list) if regulatory_context_list else "general compliance",
        }


async def process_answer_node(state: ValidationState) -> dict:
    """
    Simple pass-through node for answer processing.

    The answer is already in state from the API endpoint.
    This node exists so the workflow can resume after user submits answer.

    Args:
        state: Current validation state

    Returns:
        Empty dict to continue to interviewer node
    """
    return {}
