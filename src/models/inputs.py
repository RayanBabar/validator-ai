from typing import TypedDict, Optional, Dict, List, Any, Union
from pydantic import BaseModel
from src.models.outputs import (
    FreeReportOutput, BasicReportOutput, 
    StandardReportOutput, PremiumReportOutput
)

# --- API Input Schema ---
class StartupSubmission(BaseModel):
    """
    Internal submission model. Only detailed_description is needed.
    All other info is extracted by LLM during interview synthesis.
    """
    detailed_description: str
    tier: str = "free"  # free, basic, standard, premium, custom
    custom_modules: Optional[List[str]] = None

# Submit endpoint input - simplified to just detailed_description
class SubmitInput(BaseModel):
    """User only needs to provide a detailed description of their idea."""
    detailed_description: str

# Answer submission
class AnswerInput(BaseModel):
    answer: str

# Upgrade request (payment handled by frontend)
class UpgradeInput(BaseModel):
    tier: str  # "basic", "standard", "premium", "custom"
    custom_modules: Optional[List[str]] = None

class AdminUpdate(BaseModel):
    edited_report: Optional[Dict[str, Any]] = None

# --- LangGraph State ---
class ValidationState(TypedDict):
    inputs: StartupSubmission
    custom_modules: Optional[List[str]]  # For custom tier
    thread_id: Optional[str]  # Thread ID for webhook calls
    search_context: Optional[str]
    
    # Interview Phase State
    interview_phase: str                    # "asking" | "complete"
    questions_asked: List[str]
    user_answers: List[str]
    current_question: Optional[str]
    enriched_context: Optional[str]
    
    # Interview Quality Metrics (used in scoring)
    clarity_score: Optional[float]          # 0-10: How clear is the business idea
    answer_quality_score: Optional[float]   # 0-10: Quality of founder's answers
    dimension_quality: Optional[Dict[str, float]]  # Per-dimension quality scores for granular viability adjustments
    
    # Title (generated in free tier, used in all tiers)
    generated_title: Optional[str]          # Short, catchy title for the business idea
    
    # Extracted Context (from interview synthesis - used for dynamic queries)
    extracted_industry: Optional[str]       # e.g., "B2B SaaS", "Logistics", "FinTech"
    extracted_geography: Optional[str]      # e.g., "USA - Chicago", "Pakistan", "EU", "Global"
    extracted_regulatory_context: Optional[str]  # e.g., "GDPR", "FDA", "None specified"
    context_specificity_score: Optional[float]   # 0-10: How specific was the founder about context
    
    # Workflow Phase Tracking
    workflow_phase: str                     # "interview" | "free_report" | "paused_for_payment" | "paid_analysis" | "failed"
    
    # Error Tracking
    error: Optional[bool]                   # True if workflow encountered an error
    error_message: Optional[str]            # Error details for debugging/display
    error_node: Optional[str]               # Which node failed
    
    # Parallel Module Outputs
    bmc_data: Optional[Dict]
    market_data: Optional[Dict]
    competitor_data: Optional[Dict]
    financial_data: Optional[Dict]
    tech_data: Optional[Dict]
    reg_data: Optional[Dict]
    gtm_data: Optional[Dict]
    risk_data: Optional[Dict]
    roadmap_data: Optional[Dict]
    funding_data: Optional[Dict]
    
    # Comprehensive Research (gathered upfront for paid tiers, reused for scoring)
    comprehensive_research: Optional[str]
    
    # Score Persistence & Research Consistency
    stored_go_no_go_score: Optional[float]
    stored_score_breakdown: Optional[Dict]
    stored_scoring_research: Optional[Dict]

    # Final Output (Typed based on tier)
    final_report: Union[FreeReportOutput, BasicReportOutput, StandardReportOutput, PremiumReportOutput, Dict[str, Any]]