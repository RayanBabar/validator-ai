"""
Base configuration for all agents.
Contains LLM setup, search tool configuration, and shared helper functions.
Includes Claude (Anthropic) fallback when OpenAI fails.
"""

import os
import time
import logging
import json
from typing import Type, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from src.config import settings
from src.config.constants import TAVILY_MAX_RESULTS, RESEARCH_CONTENT_LIMIT, MODEL_PRICING, TAVILY_COST_PER_QUERY
from src.utils.health_monitor import health_monitor
from src.models.inputs import ValidationState

logger = logging.getLogger(__name__)

def _calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on model pricing."""
    pricing = MODEL_PRICING.get(model_name)
    if not pricing:
        return 0.0
    
    # Pricing is per 1M tokens
    input_cost = (input_tokens * pricing["input"]) / 1_000_000
    output_cost = (output_tokens * pricing["output"]) / 1_000_000
    
    return input_cost + output_cost

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
)

# Complex/powerful model for detailed analysis (standard/premium modules)
llm_complex = ChatOpenAI(
    model="gpt-5.2",
    api_key=settings.OPENAI_API_KEY,
)

# Default export for backward compatibility
llm = llm_fast

# ===========================================
# CLAUDE FALLBACK INSTANCES (with prompt caching enabled)
# ===========================================
claude_fast: Optional[Any] = None
claude_complex: Optional[Any] = None
claude_opus: Optional[Any] = None

if settings.ANTHROPIC_API_KEY:
    try:
        from langchain_anthropic import ChatAnthropic

        # Enable prompt caching for 90% cost savings on repeated context
        # Cache writes: $1.25/1M, Cache reads: $0.10/1M vs normal $3/1M
        # NOTE: On Feb 2, 2026, we use the stable 2024 header. The 2026-02-05 update is pending in 3 days.
        claude_fast = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=settings.ANTHROPIC_API_KEY,
        )
        claude_complex = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=settings.ANTHROPIC_API_KEY,
        )
        # Smartest/Costliest model for Strategic Directive & Final Scoring
        # Opus 4.6 with Thinking Mode (2026 Release)
        # Note: max_tokens limited to 16k. Budget must be < max_tokens.
        claude_opus = ChatAnthropic(
            model="claude-opus-4-6",
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=16000,
            thinking={
                "type": "adaptive"
            },
        )
        logger.info("Claude fallback enabled")
    except ImportError:
        logger.warning("langchain-anthropic not installed, Claude fallback disabled")


# ===========================================
# UNIFIED LLM SERVICE
# ===========================================
class LLMService:
    """
    Unified LLM invocation service with automatic Claude fallback.
    
    Consolidates all LLM invocation patterns across the codebase into
    two methods: invoke() for JSON output and invoke_structured() for
    Pydantic schema-based output.
    
    Usage:
        # JSON output
        result = await LLMService.invoke(prompt, args, use_complex=False)
        
        # Structured Pydantic output  
        result = await LLMService.invoke_structured(MySchema, prompt, args)
    """
    
    @staticmethod
    async def invoke(
        prompt: ChatPromptTemplate,
        invoke_args: dict,
        use_complex: bool = False,
        parse_json: bool = True,
        provider: str = "auto"
    ) -> Any:
        """
        Invoke LLM with automatic Claude fallback or forced provider.
        
        Args:
            prompt: ChatPromptTemplate to use
            invoke_args: Arguments for the prompt
            use_complex: If True, use gpt-5/claude-opus; else gpt-5-mini/claude-sonnet
            parse_json: If True, parse output as JSON
            provider: "auto", "openai", "claude", or "claude-opus"
            
        Returns:
            LLM response (parsed as JSON if parse_json=True)
            
        Raises:
            Exception: If selected provider fails
        """
        # Determine primary and fallback based on provider setting
        primary: Optional[Any] = None
        fallback: Optional[Any] = None
        
        if provider == "openai":
            primary = llm_complex if use_complex else llm_fast
            fallback = None
        elif provider == "claude":
            primary = claude_complex if use_complex else claude_fast
            fallback = None
        elif provider == "claude-opus":
            # Direct Opus usage for high-intelligence checks
            primary = claude_opus if claude_opus else claude_complex
            fallback = claude_complex 
        else:  # "auto"
            primary = llm_complex if use_complex else llm_fast
            fallback = claude_complex if use_complex else claude_fast
            
        if not primary:
            raise ValueError(f"Selected provider '{provider}' is not available/configured")
        
        async def execute_chain(llm_instance, args, parser=None):
            # 1. Generate messages from prompt
            messages_val = await prompt.ainvoke(args)
            messages = messages_val.to_messages()
            
            # 2. Inject cache control (Removed)
            
            # 3. Invoke LLM
            response = await llm_instance.ainvoke(messages)
            
            # Extract metadata from response BEFORE parsing
            metadata = getattr(response, "response_metadata", {})
            
            # 4. Parse if needed
            if parser:
                # Handle Opus thinking responses - extract text content only
                # Opus returns content as list: [{"type": "thinking", ...}, {"type": "text", ...}]
                content_to_parse = response.content
                if isinstance(response.content, list):
                    # Extract only text blocks, filter out thinking blocks
                    text_parts = []
                    for block in response.content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                        elif hasattr(block, "type") and block.type == "text":
                            # Handle LangChain content block objects
                            text_parts.append(getattr(block, "text", str(block)))
                    content_to_parse = "\n".join(text_parts) if text_parts else str(response.content)
                
                # Try to parse JSON from the extracted text content
                import re
                # Extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content_to_parse)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    json_str = content_to_parse.strip()
                
                try:
                    parsed = json.loads(json_str)
                    return parsed, metadata
                except json.JSONDecodeError:
                    # Fallback to LangChain parser
                    logger.warning("Direct JSON parse failed, trying LangChain parser...")
                    parsed = await parser.ainvoke(response)
                    return parsed, metadata
            return response, metadata

        parser = JsonOutputParser() if parse_json else None
        
        try:
            start_time = time.perf_counter()
            result, metadata_dict = await execute_chain(primary, invoke_args, parser)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Record metrics with correct provider tag
            tag = "claude" if provider == "claude" or provider == "claude-opus" else "openai"
            
            # Extract usage
            usage = {}
            if "token_usage" in metadata_dict: # OpenAI
                usage = metadata_dict["token_usage"]
            elif "usage" in metadata_dict: # Anthropic
                usage = metadata_dict["usage"]
            
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
            
            # Determine actual model used
            model_name = "unknown"
            if "model_name" in metadata_dict:
                 model_name = metadata_dict["model_name"]
            elif hasattr(primary, "model_name"):
                 model_name = primary.model_name
            elif hasattr(primary, "model"):
                 model_name = primary.model
            
            cost = _calculate_cost(model_name, input_tokens, output_tokens)
            
            # DEBUG LOGGING
            logger.info(f"LLM Call Info: Provider={provider}, Model={model_name}, Input={input_tokens}, Output={output_tokens}, Cost={cost}")
            if not cost and (input_tokens > 0 or output_tokens > 0):
                 logger.warning(f"Cost is 0 but tokens > 0. Check MODEL_PRICING for '{model_name}'. Metadata keys: {usage.keys() if usage else 'None'}")
            
            await health_monitor.record_call(
                service=tag, 
                latency_ms=latency_ms, 
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model_name=model_name
            )
            return result
        except Exception as primary_error:
            latency_ms = (time.perf_counter() - start_time) * 1000
            tag = "claude" if provider == "claude" or provider == "claude-opus" else "openai"
            await health_monitor.record_call(tag, latency_ms, success=False)
            logger.warning(f"{provider} primary failed: {primary_error}")
            
            if fallback:
                try:
                    logger.info("Falling back to Claude...")
                    start_time = time.perf_counter()
                    result, _ = await execute_chain(fallback, invoke_args, parser)
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    await health_monitor.record_call("claude", latency_ms, success=True)
                    return result
                except Exception as fallback_error:
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    await health_monitor.record_call("claude", latency_ms, success=False)
                    logger.error(f"Claude fallback also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise primary_error
    
    @staticmethod
    async def invoke_structured(
        schema_class: Type[BaseModel],
        prompt: ChatPromptTemplate,
        invoke_args: dict,
        use_complex: bool = True,
        provider: str = "auto"
    ) -> BaseModel:
        """
        Invoke LLM with Pydantic schema enforcement and Claude fallback.
        
        Args:
            schema_class: Pydantic model class for structured output
            prompt: ChatPromptTemplate to use
            invoke_args: Arguments for the prompt
            use_complex: If True, use gpt-5/claude-opus; else gpt-5-mini/claude-sonnet
            provider: "auto" (default), "openai", or "claude"
            
        Returns:
            Pydantic model instance
            
        Raises:
            Exception: If provider/fallback fails
        """
        # Determine primary and fallback based on provider setting
        primary: Optional[Any] = None
        fallback: Optional[Any] = None
        
        if provider == "openai":
            primary = llm_complex if use_complex else llm_fast
            fallback = None
        elif provider == "claude":
            primary = claude_complex if use_complex else claude_fast
            fallback = None
        elif provider == "claude-opus":
            # Use opus WITH thinking - we handle this with tool_choice="auto" below
            primary = claude_opus if claude_opus else claude_complex
            fallback = claude_complex
        else:  # "auto"
            primary = llm_complex if use_complex else llm_fast
            fallback = claude_complex if use_complex else claude_fast
            
        if not primary:
            raise ValueError(f"Selected provider '{provider}' is not available/configured")
        
        # Check if using Opus with thinking (requires special handling)
        is_opus_with_thinking = provider == "claude-opus" and claude_opus is not None
        
        async def execute_structured_chain(llm_instance, args, use_auto_tool_choice: bool = False):
            # 1. Generate messages from prompt
            messages_val = await prompt.ainvoke(args)
            messages = messages_val.to_messages()
            
            if use_auto_tool_choice:
                # For Opus with thinking: use tool_choice="auto" instead of forced tool use
                # Define the output tool from the Pydantic schema
                tool_def = {
                    "name": "structured_output",
                    "description": f"Output the structured response as {schema_class.__name__}. You MUST call this tool to provide your final answer.",
                    "input_schema": schema_class.model_json_schema()
                }
                
                # Bind tool with auto choice (compatible with thinking)
                llm_with_tool = llm_instance.bind_tools([tool_def], tool_choice="auto")
                
                # Add instruction to use the tool
                from langchain_core.messages import SystemMessage
                tool_instruction = SystemMessage(content=f"CRITICAL INSTRUCTION: You MUST call the 'structured_output' tool to provide your final answer. Do NOT respond with plain text or JSON in your message. After thinking, immediately invoke the structured_output tool with all required fields from the {schema_class.__name__} schema.")
                messages = [tool_instruction] + list(messages)
                
                response = await llm_with_tool.ainvoke(messages)
                
                # Extract tool call result
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tool_call = response.tool_calls[0]
                    parsed = schema_class.model_validate(tool_call['args'])
                    return {"parsed": parsed, "raw": response}
                else:
                    # FALLBACK: Try to parse JSON from content if model didn't use tool
                    logger.warning(f"Opus did not use tool. Attempting JSON parse from content...")
                    content = response.content if isinstance(response.content, str) else str(response.content)
                    
                    # Try to extract JSON from content (may be wrapped in markdown code blocks)
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    else:
                        # Try direct JSON parse
                        json_str = content.strip()
                    
                    try:
                        parsed_dict = json.loads(json_str)
                        parsed = schema_class.model_validate(parsed_dict)
                        logger.info("Successfully parsed JSON from Opus text response")
                        return {"parsed": parsed, "raw": response}
                    except (json.JSONDecodeError, Exception) as parse_error:
                        logger.error(f"Failed to parse Opus response as JSON: {parse_error}")
                        logger.error(f"Response content (first 500 chars): {content[:500]}")
                        raise ValueError(f"Model did not use the structured_output tool and response is not valid JSON. Content: {content[:300]}")
            else:
                # Standard path: use with_structured_output (forces tool use, no thinking)
                structured_llm = llm_instance.with_structured_output(schema_class, include_raw=True)
                return await structured_llm.ainvoke(messages)
        
        try:
            start_time = time.perf_counter()
            raw_result = await execute_structured_chain(primary, invoke_args, use_auto_tool_choice=is_opus_with_thinking)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            result = raw_result["parsed"]
            
            tag = "claude" if provider == "claude" or provider == "claude-opus" else "openai"
            
            # Extract usage from raw response
            usage = {}
            if "raw" in raw_result and hasattr(raw_result["raw"], "response_metadata"):
                meta = raw_result["raw"].response_metadata
                if "token_usage" in meta: # OpenAI
                    usage = meta["token_usage"]
                elif "usage" in meta: # Anthropic
                    usage = meta["usage"]
            
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
            # Determine actual model used
            model_name = "unknown"
            if "raw" in raw_result and hasattr(raw_result["raw"], "response_metadata") and "model_name" in raw_result["raw"].response_metadata:
                 model_name = raw_result["raw"].response_metadata["model_name"]
            elif hasattr(primary, "model_name"):
                 model_name = primary.model_name
            elif hasattr(primary, "model"):
                 model_name = primary.model
            
            cost = _calculate_cost(model_name, input_tokens, output_tokens)
 
            # DEBUG LOGGING
            logger.info(f"LLM Structured Call Info: Provider={provider}, Model={model_name}, Input={input_tokens}, Output={output_tokens}, Cost={cost}")
            if not cost and (input_tokens > 0 or output_tokens > 0):
                 logger.warning(f"Structured Cost is 0 but tokens > 0. Check MODEL_PRICING for '{model_name}'. Metadata keys: {usage.keys() if usage else 'None'}")
            
            await health_monitor.record_call(
                service=tag, 
                latency_ms=latency_ms, 
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model_name=model_name
            )
            return result
        except Exception as primary_error:
            latency_ms = (time.perf_counter() - start_time) * 1000
            tag = "claude" if provider == "claude" or provider == "claude-opus" else "openai"
            await health_monitor.record_call(tag, latency_ms, success=False)
            logger.warning(f"{provider} structured output failed: {primary_error}")
            
            if fallback:
                try:
                    logger.info("Falling back to Claude for structured output...")
                    start_time = time.perf_counter()
                    result = await execute_structured_chain(fallback, invoke_args)
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    await health_monitor.record_call("claude", latency_ms, success=True)
                    return result
                except Exception as fallback_error:
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    await health_monitor.record_call("claude", latency_ms, success=False)
                    logger.error(f"Claude structured fallback also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise primary_error


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
        start_time = time.perf_counter()
        search_results = await search_tool.ainvoke(search_query)
        latency_ms = (time.perf_counter() - start_time) * 1000
        await health_monitor.record_call("tavily", latency_ms, success=True, cost=TAVILY_COST_PER_QUERY)
        
        # Check if result is an error dict (Tavily wrapper sometimes returns this)
        if isinstance(search_results, dict) and "error" in search_results:
             logger.warning(f"Tavily returned error object: {search_results}")
             return "Search data unavailable."

        if isinstance(search_results, list):
            return "\n".join([r.get("content", "") for r in search_results])
            
        return str(search_results)
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        await health_monitor.record_call("tavily", latency_ms, success=False)
        
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
        start_time = time.perf_counter()
        search_results = await search_tool.ainvoke(search_query)
        latency_ms = (time.perf_counter() - start_time) * 1000
        await health_monitor.record_call("tavily", latency_ms, success=True, cost=TAVILY_COST_PER_QUERY)
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
        latency_ms = (time.perf_counter() - start_time) * 1000
        await health_monitor.record_call("tavily", latency_ms, success=False)
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
    tier: str = "basic"  # Default to basic (2 queries) if not specified
) -> dict:
    """
    Generate a module with strict Pydantic schema enforcement.
    
    Uses LLMService.invoke_structured() internally.
    
    PERFORMANCE OPTIMIZATION:
    - If state["comprehensive_research"] exists, uses that (no new search)
    - Otherwise falls back to dynamic_research per module
    
    Incorporates interview Q&A data from state for more informed analysis.

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
    
    # PERFORMANCE: Use pre-fetched comprehensive research if available
    # This optimization allows 10 modules to run in parallel without 10x API calls
    comprehensive_research = state.get("comprehensive_research")
    
    if comprehensive_research:
        # Use shared research context (much faster - no per-module search)
        logger.debug(f"Using shared comprehensive research for {output_model.__name__}")
        search_context = comprehensive_research
    else:
        # Fallback: Individual research per module (slower)
        # Use tier-based depth (2/4/6 queries)
        from src.agents.search.research import dynamic_research
        logger.debug(f"Performing individual research for {output_model.__name__} (tier={tier})")
        search_context = await dynamic_research(
            description=desc,
            research_objective=research_objective,
            max_length=RESEARCH_CONTENT_LIMIT,
            tier=tier,
            min_credibility=4
        )
    
    # Gather interview Q&A data from state
    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])
    qa_pairs = "\n".join([
        f"Q{i+1}: {q}\nA{i+1}: {a}"
        for i, (q, a) in enumerate(zip(questions_asked, user_answers))
    ]) if questions_asked else ""
    
    # Include interview context and synthesized intelligence in search results if available
    context_parts = []
    
    if qa_pairs:
        context_parts.append(f"FOUNDER INTERVIEW INSIGHTS:\n{qa_pairs}")
    
    enriched_ctx = state.get("enriched_context", "")
    if enriched_ctx:
        context_parts.append(f"SYNTHESIZED INTELLIGENCE:\n{enriched_ctx}")
        
    # STRATEGIC DIRECTIVE INJECTION (Option 1+)
    # Force the module to align with the "Truth" defined by the CSO agent
    strategic_directive = state.get("strategic_directive")
    if strategic_directive:
        # Format explicitly as a directive block
        directive_text = f"""
*** STRATEGIC DIRECTIVE (THE TRUTH) ***
You MUST align your analysis with these decided constraints. Do not deviate.
- Target Customer: {strategic_directive.target_customer_segment}
- Pricing Strategy: {strategic_directive.pricing_strategy}
- Core Value Prop: {strategic_directive.core_value_proposition}
- Key Constraints: {', '.join(strategic_directive.key_strategic_constraints)}
- Differentiation: {strategic_directive.differentiation_strategy}
"""
        context_parts.append(directive_text)
        
    context_parts.append(f"MARKET RESEARCH DATA:\n{search_context}")
    
    search_context = "\n\n".join(context_parts)
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    # Prepare prompt arguments
    invoke_args = {
        "title": desc,
        "search_results": search_context, # Use strictly 'search_results' as expected by prompts
        **(prompt_args or {})
    }

    result = await LLMService.invoke_structured(
        output_model, prompt, invoke_args, use_complex=False, provider="openai"  # Use fast model only
    )
    return result.model_dump()



# NOTE: llm_with_fallback has been removed. Use LLMService.invoke() instead.
