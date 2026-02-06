"""
Standard/Premium Tier Modules.
10 parallel modules generating detailed reports with strict schemas.
Uses dynamic search with LangChain agents for intelligent query generation.
"""

from src.agents.base import generate_structured_module
import logging
from src.agents.search.research import dynamic_research
from src.models.inputs import ValidationState
from src.models.outputs import (
    BMCModule, MarketModule, CompetitorModule, FinancialsModule,
    TechModule, RegulatoryModule, GTMModule, RiskModule,
    RoadmapModule, FundingModule
)
from src.config.prompts import (
    BMC_PROMPT, MARKET_PROMPT, COMPETITOR_PROMPT, FINANCE_PROMPT,
    TECH_PROMPT, REGULATORY_PROMPT, GTM_PROMPT, RISK_PROMPT,
    ROADMAP_PROMPT, FUNDING_PROMPT
)

from src.config.constants import RESEARCH_CONTENT_LIMIT
from src.agents.search.topics import get_research_topics


def get_context_from_state(state: ValidationState) -> dict:
    """Extract dynamic context from state for parameterized queries."""
    # User Requirement: Currency is ALWAYS Euro (EUR)
    from src.config.constants import DEFAULT_CURRENCY
    currency = DEFAULT_CURRENCY 
            
    return {
        "geography": state.get("extracted_geography", "global market"),
        "industry": state.get("extracted_industry", "startup"),
        "regulatory_context": state.get("extracted_regulatory_context", "general compliance"),
        "currency": currency,
    }



def should_run_module(state: ValidationState, module_name: str) -> bool:
    """Check if the module should run based on tier and custom selection."""
    # If custom_modules is present in state, respect it regardless of tier name
    custom_modules = state.get("custom_modules")
    
    if not custom_modules:
        # No specific modules requested -> run everything (default for standard/premium)
        return True
    
    # If custom_modules list exists, only run if this module is in it
    should_run = module_name in custom_modules
    
    if should_run:
        logging.getLogger(__name__).info(f"Module selection: Running {module_name}")
    else:
        logging.getLogger(__name__).info(f"Module selection: Skipping {module_name}")
    return should_run

def log_module_start(module_name: str):
    logging.getLogger(__name__).info(f"Starting standard module: {module_name}")

async def std_bmc(state: ValidationState):
    """Business Model Canvas with strict schema"""
    if not should_run_module(state, "mod_bmc"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    return {"bmc_data": await generate_structured_module(
        BMCModule,
        BMC_PROMPT,
        f"business model canvas {ctx['industry']}",
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_market(state: ValidationState):
    """Market Analysis with strict schema - uses dynamic search"""
    if not should_run_module(state, "mod_market"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    # Use centralized prompt strategy
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    search_objective = topics.get("mod_market", f"market size {ctx['industry']} {ctx['geography']}")
    
    return {"market_data": await generate_structured_module(
        MarketModule,
        MARKET_PROMPT,
        search_objective,
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_comp(state: ValidationState):
    """Competitive Intelligence with strict schema"""
    if not should_run_module(state, "mod_comp"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"competitor_data": await generate_structured_module(
        CompetitorModule,
        COMPETITOR_PROMPT,
        topics.get("mod_comp", f"competitors {ctx['industry']}"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_finance(state: ValidationState):
    """Financial Analysis with strict schema"""
    if not should_run_module(state, "mod_finance"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"financial_data": await generate_structured_module(
        FinancialsModule,
        FINANCE_PROMPT,
        topics.get("mod_finance", "startup unit economics"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_tech(state: ValidationState):
    """Technical Requirements with strict schema - uses current year"""
    if not should_run_module(state, "mod_tech"):
        return {}

    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"tech_data": await generate_structured_module(
        TechModule,
        TECH_PROMPT,
        topics.get("mod_tech", "startup tech stack"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_reg(state: ValidationState):
    """Regulatory Compliance with strict schema - uses dynamic context"""
    if not should_run_module(state, "mod_reg"):
        return {}

    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"reg_data": await generate_structured_module(
        RegulatoryModule,
        REGULATORY_PROMPT,
        topics.get("mod_reg", "regulatory compliance"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_gtm(state: ValidationState):
    """GTM Strategy with strict schema"""
    if not should_run_module(state, "mod_gtm"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"gtm_data": await generate_structured_module(
        GTMModule,
        GTM_PROMPT,
        topics.get("mod_gtm", "go to market strategy"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_risk(state: ValidationState):
    """Risk Assessment with strict schema"""
    if not should_run_module(state, "mod_risk"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"risk_data": await generate_structured_module(
        RiskModule,
        RISK_PROMPT,
        topics.get("mod_risk", "startup risks"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_roadmap(state: ValidationState):
    """Implementation Roadmap with strict schema"""
    if not should_run_module(state, "mod_roadmap"):
        return {}


    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"roadmap_data": await generate_structured_module(
        RoadmapModule,
        ROADMAP_PROMPT,
        topics.get("mod_roadmap", "startup roadmap"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


async def std_funding(state: ValidationState):
    """Funding Strategy with strict schema - uses dynamic geography"""
    if not should_run_module(state, "mod_funding"):
        return {}

    ctx = get_context_from_state(state)
    tier = state['inputs'].tier
    
    topics = get_research_topics(ctx['geography'], ctx['industry'])
    
    return {"funding_data": await generate_structured_module(
        FundingModule,
        FUNDING_PROMPT,
        topics.get("mod_funding", "startup funding"),
        state,
        prompt_args=ctx,
        tier=tier
    )}


