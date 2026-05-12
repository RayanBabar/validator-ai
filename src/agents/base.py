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
    model="deepseek-v4-flash-free",
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
        
        # 2. Invoke LLM with retry logic
        async with LLMService._semaphore:
            max_retries = 3
            backoff = 1.0
            
            for attempt in range(max_retries):
                try:
                    if parse_json:
                        # Use with_structured_output(dict) for reliable JSON extraction
                        structured_llm = primary.with_structured_output(dict, method="json_mode", include_raw=False)
                        result = await structured_llm.ainvoke(messages)
                        return result
                    else:
                        response = await primary.ainvoke(messages)
                        raw_content = response.content if isinstance(response.content, str) else str(response.content)
                        return raw_content
                except Exception as e:
                    is_rate_limit = "429" in str(e) or "Too Many Requests" in str(e)
                    is_bad_request = "400" in str(e) and "bmc" not in str(messages)
                    
                    if (is_rate_limit or is_bad_request) and attempt < max_retries - 1:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s... Error: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    logger.error(f"LLM primary failed after {attempt+1} attempts: {e}")
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
        with a full manual JSON extraction fallback for proxy providers.
        """
        primary = llm_complex if use_complex else llm_fast
        
        if isinstance(prompt, list):
            messages = prompt
        else:
            messages_val = await prompt.ainvoke(invoke_args or {})
            messages = messages_val.to_messages()

        raw_content: Optional[str] = None
        
        async with LLMService._semaphore:
            max_retries = 3
            backoff = 1.5
            
            for attempt in range(max_retries):
                try:
                    # On first attempt, try with_structured_output
                    # On subsequent attempts, if we got a 400, try plain chat instead
                    if attempt == 0:
                        structured_llm = primary.with_structured_output(schema_class, include_raw=True)
                        raw_result = await structured_llm.ainvoke(messages)
                        
                        if raw_result.get("parsed") is not None:
                            return raw_result["parsed"]
                        
                        raw_msg = raw_result.get("raw")
                        if raw_msg is not None:
                            raw_content = raw_msg.content if isinstance(raw_msg.content, str) else str(raw_msg.content)
                    else:
                        # Standard invoke on retries
                        response = await primary.ainvoke(messages)
                        raw_content = response.content if isinstance(response.content, str) else str(response.content)
                    break
                except Exception as e:
                    error_msg = str(e)
                    is_rate_limit = "429" in error_msg
                    is_bad_request = "400" in error_msg
                    
                    if is_bad_request:
                        logger.warning(f"LLM 400 Bad Request on attempt {attempt+1}. Switching to plain invoke for retry. Error: {error_msg}")
                    
                    if (is_rate_limit or is_bad_request) and attempt < max_retries - 1:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(f"Retrying LLM call ({attempt+1}/{max_retries}) in {wait_time}s due to {error_msg}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    try:
                        raw_response = await primary.ainvoke(messages)
                        raw_content = raw_response.content if isinstance(raw_response.content, str) else str(raw_response.content)
                        break
                    except Exception as final_e:
                        logger.error(f"LLM call permanently failed: {final_e}")
                        raise e
        
        if not raw_content or not raw_content.strip():
            logger.error(f"LLM returned empty content for {schema_class.__name__}")
            raise ValueError(f"No content for {schema_class.__name__}")

        # --- Phase 2: Manual JSON extraction fallback ---
        # Extract JSON from content (handles markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_content)
        json_str = json_match.group(1).strip() if json_match else raw_content.strip()
        
        # Find first { ... }
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = json_str[start_idx:end_idx + 1]
        
        # Attempt JSON parse with recovery
        def _try_parse_json(s: str) -> dict:
            try:
                return json.loads(s)
            except json.JSONDecodeError as e:
                # Case 1: "Extra data"
                if "Extra data" in str(e):
                    depth = 0
                    in_string = False
                    escape_next = False
                    for i, ch in enumerate(s):
                        if escape_next:
                            escape_next = False
                            continue
                        if ch == '\\' and in_string:
                            escape_next = True
                            continue
                        if ch == '"':
                            in_string = not in_string
                        if not in_string:
                            if ch == '{':
                                depth += 1
                            elif ch == '}':
                                depth -= 1
                                if depth == 0:
                                    try:
                                        return json.loads(s[:i + 1])
                                    except json.JSONDecodeError:
                                        break

                # Case 2: Common syntax errors (missing commas, trailing commas, single quotes)
                repaired = s
                # Comma between a value and a next key
                repaired = re.sub(r'(\d|true|false|null|\}|\])\s*(")', r'\1, \2', repaired)
                # Comma between two strings
                repaired = re.sub(r'("[\s\S]*?")\s*(")', r'\1, \2', repaired)
                # Remove trailing commas
                repaired = re.sub(r',\s*\]', ']', repaired)
                repaired = re.sub(r',\s*\}', '}', repaired)
                
                repaired = repaired.replace(', ,', ',').replace(',,', ',')
                
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    # Try single quote replacement as last resort
                    try:
                        # Very simple replacement for single quotes used as JSON delimiters
                        # Only if it looks like a dictionary with single quotes
                        if "'" in repaired:
                            # Replace 'key': with "key":
                            repaired_sq = re.sub(r"'\s*([^':]+)\s*'\s*:", r'"\1":', repaired)
                            # Replace : 'value' with : "value"
                            repaired_sq = re.sub(r":\s*'([^']*)'", r': "\1"', repaired_sq)
                            return json.loads(repaired_sq)
                    except:
                        pass
                
                # Case 3: Truncated JSON
                brace_positions = [i for i, c in enumerate(s) if c == '}']
                for pos in reversed(brace_positions[:-1]):
                    candidate = s[:pos + 1]
                    if candidate.count('{') <= candidate.count('}'):
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            continue
                raise
        
        parsed_dict = _try_parse_json(json_str)
        
        def _to_snake(s: str) -> str:
            """Convert camelCase / PascalCase to snake_case."""
            s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
            s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
            return s.lower()

        def _normalize_keys(obj: Any) -> Any:
            """Recursively snake_case all keys in a dict/list."""
            if isinstance(obj, list):
                return [_normalize_keys(i) for i in obj]
            if isinstance(obj, dict):
                return {_to_snake(k): _normalize_keys(v) for k, v in obj.items()}
            return obj

        # Unwrap single-key wrappers (e.g. {"MarketAnalysis": {...}})
        if isinstance(parsed_dict, dict) and len(parsed_dict) == 1:
            wrapper_key = list(parsed_dict.keys())[0]
            val = parsed_dict[wrapper_key]
            # Only unwrap if the wrapper key matches the schema or looks like a wrapper
            if _to_snake(wrapper_key) == _to_snake(schema_class.__name__) or not (set(schema_class.model_fields.keys()) & set(parsed_dict.keys())):
                parsed_dict = val
        
        # Normalize and validate
        snake_dict = _normalize_keys(parsed_dict)
        
        # Type coercion for common mismatches
        for field_name, field_info in schema_class.model_fields.items():
            if field_name not in snake_dict:
                continue
            val = snake_dict[field_name]
            ann_str = str(field_info.annotation)
            
            # dict -> str coercion
            if "str" in ann_str and isinstance(val, (dict, list)):
                snake_dict[field_name] = json.dumps(val, ensure_ascii=False)
            
            # list[dict] -> list[str] coercion
            if "List[str]" in ann_str and isinstance(val, list) and val and isinstance(val[0], dict):
                snake_dict[field_name] = [json.dumps(i, ensure_ascii=False) for i in val]

        return schema_class.model_validate(snake_dict)


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
