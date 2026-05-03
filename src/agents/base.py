"""
Base configuration for all agents.
Contains LLM setup, search tool configuration, and shared helper functions.
Includes Claude (Anthropic) fallback when OpenAI fails.
"""

import os
import re
import time
import logging
import json
import asyncio
from typing import Type, Any, Optional, Union, List
from langchain_core.messages import BaseMessage

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from src.config.prompts import SHARED_CONTEXT_PROMPT
from pydantic import BaseModel

from src.config import settings
from src.config.constants import (
    TAVILY_MAX_RESULTS,
    RESEARCH_CONTENT_LIMIT,
    TAVILY_COST_PER_QUERY,
)
from src.models.inputs import ValidationState

logger = logging.getLogger(__name__)


# ===========================================
# ENVIRONMENT SETUP
# ===========================================
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY

# ===========================================
# OPENAI LLM INSTANCES
# ===========================================
# Fast/cheap model for simple tasks (interview, free tier, basic scoring)
llm_fast = ChatOpenAI(
    model="gpt-5-nano",
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE,
    max_retries=3,
)

# Complex/powerful model for detailed analysis (standard/premium modules)
llm_complex = ChatOpenAI(
    model="minimax-m2.5-free", # Using a free model to ensure zero API costs
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE,
    max_retries=3,
)

# Default export for backward compatibility
llm = llm_fast


# ===========================================
# UNIFIED LLM SERVICE
# ===========================================
class LLMService:
    """
    Unified LLM invocation service.
    
    Consolidates all LLM invocation patterns across the codebase into
    two methods: invoke() for JSON output and invoke_structured() for
    Pydantic schema-based output.
    """
    
    # Limit parallel calls to avoid rate limits from free providers
    _semaphore = asyncio.Semaphore(3)
    
    @staticmethod
    async def invoke(
        prompt: Union[ChatPromptTemplate, List[BaseMessage]],
        invoke_args: dict = None,
        use_complex: bool = False,
        parse_json: bool = True,
        provider: str = "auto"
    ) -> Any:
        """
        Invoke LLM with JSON output parsing.
        """
        primary = llm_complex if use_complex else llm_fast
        
        # 1. Generate messages from prompt
        if isinstance(prompt, list):
            messages = prompt
        else:
            messages_val = await prompt.ainvoke(invoke_args or {})
            messages = messages_val.to_messages()
        
        # 2. Invoke LLM
        async with LLMService._semaphore:
            try:
                if parse_json:
                    # Use with_structured_output(dict) for reliable JSON extraction
                    structured_llm = primary.with_structured_output(dict, method="json_mode", include_raw=False)
                    result = await structured_llm.ainvoke(messages)
                else:
                    response = await primary.ainvoke(messages)
                    result = response
                
                return result
            except Exception as e:
                logger.error(f"LLM primary failed: {e}")
                raise e
    
    @staticmethod
    async def invoke_structured(
        schema_class: Type[BaseModel],
        prompt: Union[ChatPromptTemplate, List[BaseMessage]],
        invoke_args: dict = None,
        use_complex: bool = False,
        provider: str = "auto"
    ) -> BaseModel:
        """
        Invoke LLM with structured output. Uses with_structured_output as primary path,
        with a full manual JSON extraction fallback for proxy providers that return
        markdown-wrapped JSON or nest results under a wrapper key.
        """
        primary = llm_complex if use_complex else llm_fast
        
        # 1. Generate messages from prompt
        if isinstance(prompt, list):
            messages = prompt
        else:
            messages_val = await prompt.ainvoke(invoke_args or {})
            messages = messages_val.to_messages()
            
        async with LLMService._semaphore:
            try:
                raw_content: Optional[str] = None
                
                # --- Phase 1: Try with_structured_output(json_mode) ---
                # json_mode forces the LLM to follow the prompt's JSON template (snake_case fields).
                # Function calling mode ignores the prompt template, causing camelCase hallucinations.
                try:
                    structured_llm = primary.with_structured_output(
                        schema_class,
                        method="json_mode",
                        include_raw=True  # Captures parse errors instead of raising
                    )
                    raw_result = await structured_llm.ainvoke(messages)
                    
                    # Happy path: parser succeeded
                    if raw_result.get("parsed") is not None:
                        return raw_result["parsed"]
                    
                    # Parser returned None — extract raw content for fallback
                    raw_msg = raw_result.get("raw")
                    if raw_msg is not None:
                        raw_content = raw_msg.content if isinstance(raw_msg.content, str) else str(raw_msg.content)
                    
                    logger.warning(
                        f"with_structured_output parse failed for {schema_class.__name__}. "
                        f"Error: {raw_result.get('parsing_error')} — falling back to manual parse."
                    )

                except Exception as structured_err:
                    # with_structured_output raised (e.g. LLM wrapped JSON in markdown code blocks)
                    # Fall back to a raw LLM call to get the content for manual parsing
                    logger.warning(
                        f"with_structured_output raised for {schema_class.__name__}: {structured_err}. "
                        f"Invoking raw LLM for manual fallback."
                    )
                    raw_response = await primary.ainvoke(messages)
                    raw_content = raw_response.content if isinstance(raw_response.content, str) else str(raw_response.content)
                
                # --- Phase 2: Manual JSON extraction fallback ---
                if not raw_content:
                    raise ValueError(f"No content available for manual fallback for {schema_class.__name__}")
                
                # Extract JSON from content (handles markdown code blocks)
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_content)
                json_str = json_match.group(1).strip() if json_match else raw_content.strip()
                
                # Find first { ... }
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    json_str = json_str[start_idx:end_idx + 1]
                
                parsed_dict = json.loads(json_str)
                
                def _to_snake(s: str) -> str:
                    """Convert camelCase / PascalCase to snake_case."""
                    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
                    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
                    return s.lower()
                
                def _normalize_keys(d: dict) -> dict:
                    """Recursively snake_case all keys in a dict (top level only for schema matching)."""
                    return {_to_snake(k): v for k, v in d.items()}
                
                # Unwrap single-key wrappers.
                # Strategy: if there's exactly one key and its value is a dict, always unwrap.
                # The guard that checked schema_fields was too strict because the inner dict
                # often has camelCase keys that don't match snake_case schema fields.
                if (
                    isinstance(parsed_dict, dict)
                    and len(parsed_dict) == 1
                    and isinstance(list(parsed_dict.values())[0], dict)
                ):
                    wrapper_key = list(parsed_dict.keys())[0]
                    inner = parsed_dict[wrapper_key]
                    schema_fields = set(schema_class.model_fields.keys())
                    inner_snake = _normalize_keys(inner)
                    # Unwrap if inner matches schema fields (after normalizing) OR if wrapper key
                    # is the class name (e.g. "BusinessModelCanvas" wrapping BusinessModelCanvas)
                    if (
                        schema_fields & set(inner_snake.keys())
                        or _to_snake(wrapper_key) == _to_snake(schema_class.__name__)
                        or not (schema_fields & set(parsed_dict.keys()))  # top-level has no schema fields
                    ):
                        logger.info(f"Unwrapping LLM response from '{wrapper_key}' wrapper key for {schema_class.__name__}")
                        parsed_dict = inner
                
                # Also handle "properties" JSON-Schema hallucination
                if (
                    isinstance(parsed_dict, dict)
                    and "properties" in parsed_dict
                    and isinstance(parsed_dict["properties"], dict)
                    and "properties" not in schema_class.model_fields
                ):
                    logger.warning(f"Unwrapping LLM 'properties' wrapper for {schema_class.__name__}")
                    meta = {k: v for k, v in parsed_dict.items() if k != "properties"}
                    parsed_dict = parsed_dict["properties"]
                    for k, v in meta.items():
                        if k in schema_class.model_fields and k not in parsed_dict:
                            parsed_dict[k] = v
                
                # Normalize camelCase keys → snake_case to match Pydantic model fields.
                # Only remap keys that don't already exist in snake_case form.
                schema_fields = set(schema_class.model_fields.keys())
                if not schema_fields.issubset(set(parsed_dict.keys())):
                    normalized = {}
                    for k, v in parsed_dict.items():
                        snake_k = _to_snake(k)
                        # Use the snake version if it's a known field and original key isn't
                        if snake_k in schema_fields and k not in schema_fields:
                            normalized[snake_k] = v
                        else:
                            normalized[k] = v
                    parsed_dict = normalized
                
                # Type coercion: fix mismatched types between LLM output and Pydantic schema
                for field_name, field_info in schema_class.model_fields.items():
                    if field_name not in parsed_dict:
                        continue
                    val = parsed_dict[field_name]
                    ann = field_info.annotation
                    ann_str = str(ann)
                    
                    # dict → str (e.g. LLM returns pricing_strategy as an object)
                    is_str_field = ann is str or ann_str in ("str", "<class 'str'>")
                    if is_str_field and isinstance(val, dict):
                        logger.warning(f"Coercing dict→str for field '{field_name}' in {schema_class.__name__}")
                        parsed_dict[field_name] = json.dumps(val, ensure_ascii=False)
                    
                    # List[dict] → List[str] (e.g. report_highlights returned as list of objects)
                    is_list_str = "List[str]" in ann_str or ann_str in ("typing.List[str]",)
                    if is_list_str and isinstance(val, list) and val and isinstance(val[0], dict):
                        logger.warning(f"Coercing List[dict]→List[str] for field '{field_name}' in {schema_class.__name__}")
                        coerced = []
                        for item in val:
                            if isinstance(item, dict):
                                # Try common text keys first
                                text = (
                                    item.get("highlight") or item.get("text") or
                                    item.get("title") or item.get("description") or
                                    item.get("content") or item.get("value") or
                                    next((v for v in item.values() if isinstance(v, str)), None) or
                                    json.dumps(item, ensure_ascii=False)
                                )
                                coerced.append(str(text))
                            else:
                                coerced.append(str(item))
                        parsed_dict[field_name] = coerced
                
                return schema_class.model_validate(parsed_dict)
                
            except Exception as e:
                logger.error(f"Structured output failed for {schema_class.__name__}: {e}")
                raise e


# ===========================================
# SEARCH TOOL
# ===========================================
search_tool = TavilySearch(
    tavily_api_key=settings.TAVILY_API_KEY, max_results=TAVILY_MAX_RESULTS
)


async def search_with_tavily(search_query: str) -> str:
    """
    Search the internet using Tavily and return context string.

    Args:
        search_query: Query string for web search

    Returns:
        Concatenated search results as string, or fallback message on error
    """
    try:
        search_results = await search_tool.ainvoke(search_query)
        
        # Check if result is an error dict (Tavily wrapper sometimes returns this)
        if isinstance(search_results, dict) and "error" in search_results:
             logger.warning(f"Tavily returned error object: {search_results}")
             return "Search data unavailable."

        if isinstance(search_results, list):
            return "\n".join([r.get("content", "") for r in search_results])
            
        return str(search_results)
    except Exception as e:
        error_msg = str(e).lower()
        if "400" in error_msg:
             logger.error(f"Tavily Bad Request (Check API Key/Query): {e}")
        elif "401" in error_msg or "403" in error_msg:
             logger.error(f"Tavily Authorization Error: {e}")
        elif "timeout" in error_msg:
             logger.error(f"Tavily Timeout: {e}")
        else:
             logger.error(f"Tavily search failed: {e}")
             
        return "Search data unavailable due to provider error."


async def search_with_tavily_detailed(search_query: str) -> list:
    """
    Search the internet using Tavily and return detailed results with URLs.
    
    Used for credibility scoring integration.

    Args:
        search_query: Query string for web search

    Returns:
        List of result dicts with 'content', 'url', 'title' fields
    """
    try:
        search_results = await search_tool.ainvoke(search_query)
        if isinstance(search_results, list):
            return search_results
            
        if isinstance(search_results, dict) and "results" in search_results:
            return search_results["results"]

        # Handle string response (sometimes returned as JSON string or error message)
        if isinstance(search_results, str):
            # Gracefully handle "No search results found" messages without warning
            if "no search results found" in search_results.lower():
                logger.info(f"Tavily returned no results query: {search_query[:50]}...")
                return []

            try:
                parsed = json.loads(search_results)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict) and "results" in parsed:
                    return parsed["results"]
            except json.JSONDecodeError:
                logger.warning(f"Tavily returned non-JSON string: {search_results[:100]}...")
                return []
        
        logger.warning(f"Tavily detailed search returned unexpected format: {type(search_results)}")
        return []
    except Exception as e:
        logger.error(f"Tavily detailed search failed: {e}")
        return []


# ===========================================
# BACKWARD COMPATIBLE HELPER FUNCTIONS
# ===========================================


async def generate_structured_module(
    output_model: type[BaseModel],
    prompt_template: ChatPromptTemplate,
    research_objective: str,
    state: ValidationState,
    prompt_args: dict = None,
    tier: str = "basic",
) -> dict:
    """
    Generate a module with strict Pydantic schema enforcement.

    Uses LLMService.invoke_structured() internally.

    PERFORMANCE OPTIMIZATION:
    - If state["comprehensive_research"] exists, builds context from that
    - Otherwise falls back to dynamic_research per module

    Args:
        output_model: Pydantic model class for structured output
        prompt_template: ChatPromptTemplate to use
        research_objective: Research objective for dynamic research
        state: Current validation state
        prompt_args: Optional dictionary of extra arguments for prompt template
        tier: Tier level for determining research depth if fallback is needed

    Returns:
        Dictionary representation of the generated module
    """
    desc = state["inputs"].detailed_description

    comprehensive_research = state.get("comprehensive_research")

    if comprehensive_research:
        search_context = comprehensive_research
    else:
        from src.agents.search.research import dynamic_research

        search_context = await dynamic_research(
            description=desc,
            research_objective=research_objective,
            max_length=RESEARCH_CONTENT_LIMIT,
            tier=tier,
            min_credibility=4,
        )

    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])
    qa_pairs = (
        "\n".join(
            [
                f"Q{i + 1}: {q}\nA{i + 1}: {a}"
                for i, (q, a) in enumerate(zip(questions_asked, user_answers))
            ]
        )
        if questions_asked
        else ""
    )

    context_parts = []

    if qa_pairs:
        context_parts.append(f"FOUNDER INTERVIEW INSIGHTS:\n{qa_pairs}")

    enriched_ctx = state.get("enriched_context", "")
    if enriched_ctx:
        context_parts.append(f"SYNTHESIZED INTELLIGENCE:\n{enriched_ctx}")

    strategic_directive = state.get("strategic_directive")
    if strategic_directive:
        directive_text = f"""*** STRATEGIC DIRECTIVE (THE TRUTH) ***
You MUST align your analysis with these decided constraints. Do not deviate.
- Target Customer: {strategic_directive.target_customer_segment}
- Pricing Strategy: {strategic_directive.pricing_strategy}
- Core Value Prop: {strategic_directive.core_value_proposition}
- Key Constraints: {", ".join(strategic_directive.key_strategic_constraints)}
- Differentiation: {strategic_directive.differentiation_strategy}"""
        context_parts.append(directive_text)

    context_parts.append(f"MARKET RESEARCH DATA:\n{search_context}")

    search_context = "\n\n".join(context_parts)

    shared_args = {
        "title": desc,
        "geography": prompt_args.get("geography", "Global"),
        "regulatory_context": prompt_args.get("regulatory_context", "General"),
        "currency": prompt_args.get("currency", "EUR"),
        "search_results": search_context,
    }

    formatted_shared_context = SHARED_CONTEXT_PROMPT.format(**shared_args)

    system_message = SystemMessage(content=formatted_shared_context)

    formatted_instruction = prompt_template.format(**(prompt_args or {}))

    human_message = HumanMessage(content=formatted_instruction)

    result = await LLMService.invoke_structured(
        output_model,
        [system_message, human_message],
        invoke_args={},
        use_complex=True,
    )
    return result.model_dump()
