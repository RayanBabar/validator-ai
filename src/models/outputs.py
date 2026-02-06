from typing import List, Literal, Dict, Optional
from pydantic import BaseModel, Field


# ============================================
# SCORING DIMENSION SCHEMAS
# ============================================


class ScoreDetail(BaseModel):
    """
    Score with reasoning.
    """
    score: int = Field(..., ge=0, le=10, description="Numerical score 0-10")
    reasoning: str = Field(..., description="Short explanation (~10 words) of why this score was given")


class SlideContent(BaseModel):
    """Content and instructions for a single pitch deck slide"""
    slide_number: int
    title: str = Field(..., description="Slide headline")
    content_bullets: List[str] = Field(..., description="Main bullet points for the slide body")
    visual_suggestion: str = Field(..., description="Description of recommended chart/image/layout")
    speaker_notes: str = Field(..., description="Script or key points for the presenter to say")


class InvestorPitchDeck(BaseModel):
    """Complete 12-slide Investor Pitch Deck content"""
    slides: List[SlideContent] = Field(..., min_length=12, max_length=12, description="The 12 standard VC slides")
    strategic_narrative: str = Field(..., description="Brief explanation of the overall story arc")


class ViabilityScores(BaseModel):
    """
    Free Tier: 5-Dimension Viability Scores (0-10 scale each)
    Based on Quick-Assessment methodology from Tiers.docx
    Scores are integers after applying interview quality adjustments.
    """

    problem_severity: ScoreDetail = Field(
        ...,
        description="Is this a 'painkiller' (urgent, must-solve) or 'vitamin' (nice-to-have)? Search volume, forum discussions, willingness-to-pay signals. 30% weight",
    )
    market_opportunity: ScoreDetail = Field(
        ...,
        description="Market size indicators (Small/Medium/Large), growth trajectory (Declining/Stable/Growing/Exploding), European market relevance, timing alignment. 25% weight",
    )
    competition_intensity: ScoreDetail = Field(
        ...,
        description="Number of direct competitors detected, market saturation level, presence of dominant players, differentiation potential. 20% weight",
    )
    execution_complexity: ScoreDetail = Field(
        ...,
        description="Technical difficulty assessment, resource requirements (team, capital, time), regulatory burden, go-to-market complexity. 15% weight",
    )
    founder_alignment: ScoreDetail = Field(
        ...,
        description="Stated experience relevance, passion/commitment indicators, available resources mentioned, time commitment. 10% weight",
    )


class GoNoGoScores(BaseModel):
    """
    Paid Tiers: 8-Dimension Go/No-Go Scores (0-10 scale each)
    Based on Go/No-Go Scoring Methodology from Tiers.docx
    Scores are integers after applying adjustments.
    """

    market_demand: ScoreDetail = Field(
        ...,
        description="Validated problem existence (surveys, search volume, forums), market size and growth rate, customer willingness to pay, pain point severity (vitamin vs painkiller). 25% weight",
    )
    financial_viability: ScoreDetail = Field(
        ...,
        description="Revenue model clarity, unit economics (LTV:CAC ratio), break-even timeline, initial investment requirements vs available resources. 20% weight",
    )
    competition_analysis: ScoreDetail = Field(
        ...,
        description="Number and strength of competitors, market saturation level, differentiation potential, barriers to entry. 15% weight",
    )
    founder_market_fit: ScoreDetail = Field(
        ...,
        description="Relevant industry experience, technical skills match, network in target market, passion/commitment indicators. 10% weight",
    )
    technical_feasibility: ScoreDetail = Field(
        ...,
        description="Technology readiness level, development complexity, required expertise availability, time to MVP. 10% weight",
    )
    regulatory_compliance: ScoreDetail = Field(
        ...,
        description="GDPR requirements, industry-specific regulations, licensing needs, legal complexity and costs. 10% weight",
    )
    timing_assessment: ScoreDetail = Field(
        ...,
        description="Market readiness, technology maturity, economic conditions, trend alignment. 5% weight",
    )
    scalability_potential: ScoreDetail = Field(
        ...,
        description="Geographic expansion possibility, automation potential, network effects, marginal cost dynamics. 5% weight",
    )


class StrategicDirective(BaseModel):
    """
    The Strategic Directive (The Golden Fact Sheet).
    Defines the 'Truth' for this startup that all departments must follow.
    """
    target_customer_segment: str = Field(..., description="Specific, primary target customer definition that ALL modules must use.")
    pricing_strategy: str = Field(..., description="The definitive pricing model/strategy (e.g. 'B2B SaaS starting at €5k/year').")
    core_value_proposition: str = Field(..., description="The single primary value prop to focus on.")
    key_strategic_constraints: List[str] = Field(..., description="3-5 critical constraints or strategic decisions (e.g. 'Focus only on EU', 'No freemium').")
    differentiation_strategy: str = Field(..., description="How we win against incumbents (e.g. 'Cheaper', 'Better UX', 'AI-native').")
    year_1_goals: str = Field(..., description="Specific Year 1 targets (e.g., '100 paying customers', '€50k ARR') to align Finance and Roadmap.")
    primary_metric_goal: str = Field(..., description="The north star metric target for Year 1 (e.g., '10k MAUs').")


# ============================================
# FREE TIER OUTPUT (Half A4, 10 seconds)
# ============================================


class FreeReportOutput(BaseModel):
    """
    Free Tier Deliverable: Half A4 page (~250-300 words max) generated in 10 seconds.

    Output Constraints:
    - Total: ~300 words maximum
    - value_proposition: 1 sentence (~15-20 words)
    - customer_profile: 2-3 sentences (~50-60 words)
    - what_if_scenario: 2-3 sentences (~50-60 words)
    - personalized_next_step: 1-2 sentences (~30-40 words)
    """

    tier: Literal["free"] = "free"

    title: str = Field(..., description="Generated title for the startup")

    viability_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="AI Viability Score (0-100) - Instant numerical validation users can share with co-founders, family, or advisors",
    )

    gauge_status: str = Field(
        ...,
        description="Visual gauge indicator: 'Promising' if score > 70, else 'Needs Work'",
    )

    scores: ViabilityScores = Field(
        ..., description="Detailed breakdown of the 5 scoring dimensions"
    )

    value_proposition: str = Field(
        ...,
        description="AI-generated killer value proposition (1 sentence) - positioning statement users can use immediately in conversations",
    )

    customer_profile: str = Field(
        ...,
        description="Specific description of their ideal first customer - detailed persona",
    )

    what_if_scenario: str = Field(
        ...,
        description="Single pivot scenario to demonstrate platform capability and show alternative paths",
    )

    package_recommendation: str = Field(
        ...,
        description="Single word recommendation: 'basic', 'standard', 'premium' if score > 50, 'premium' (book consultation) if score 31-50, or 'quit' if score <= 30",
    )

    personalized_next_step: str = Field(
        ...,
        description="Specific action they can take today to move forward with their startup",
    )


# ============================================
# BASIC TIER OUTPUT (One A4, 30 seconds + review)
# ============================================


class BusinessModelCanvas(BaseModel):
    """
    Business Model Canvas: 9 key building blocks
    CONCISE one-page document - 2-3 short bullets per section
    """

    customer_segments: List[str] = Field(
        ...,
        description="3-4 bullets: Primary customer segments (max 15 words each)",
    )

    value_propositions: List[str] = Field(
        ..., description="3-4 bullets: Core value delivered (max 15 words each)"
    )

    channels: List[str] = Field(
        ...,
        description="3-4 bullets: Key distribution/communication channels (max 15 words each)",
    )

    customer_relationships: List[str] = Field(
        ...,
        description="3-4 bullets: Customer interaction approach (max 15 words each)",
    )

    revenue_streams: List[str] = Field(
        ..., description="3-4 bullets: How money is made (max 15 words each)"
    )

    key_resources: List[str] = Field(
        ...,
        description="3-4 bullets: Critical resources needed (max 15 words each)",
    )

    key_activities: List[str] = Field(
        ...,
        description="3-4 bullets: Critical activities to deliver value (max 15 words each)",
    )

    key_partnerships: List[str] = Field(
        ...,
        description="3-4 bullets: Strategic partners required (max 15 words each)",
    )

    cost_structure: List[str] = Field(
        ..., description="3-4 bullets: Major cost categories (max 15 words each)"
    )

class BasicRecommendation(BaseModel):
    """Final Recommendation Section"""

    go_no_go_verdict: Literal["Go", "Conditional-Go", "No-Go"] = Field(..., description="Clear Go/Conditional-Go/No-Go statement")
    rating_justification: str = Field(
        ..., description="Reasoning for the score (text only, no markdown, ~2-3 sentences)"
    )
    immediate_action_items: List[str] = Field(
        ..., description="Top 3 recommended actions"
    )


class BasicExecutiveSummary(BaseModel):
    """Structured Basic Tier Executive Summary (2 Pages Total)"""

    problem_summary: str = Field(
        ..., description="Detailed problem description: Who has this problem, severity, cost of inaction (~200-250 words)"
    )
    proposed_solution: str = Field(
        ..., description="Proposed solution and value proposition: How it solves the problem, key benefits (~200-250 words)"
    )
    report_highlights: List[str] = Field(
        ...,
        description="Top 5 key highlights from the report. Max 50 words each",
    )
    recommendation: BasicRecommendation = Field(
        ..., description="Go/No-Go verdict with justification and action steps"
    )


class BasicReportOutput(BaseModel):
    """
    Basic Tier Deliverable: 2-3 A4 pages (~1000-1500 words), generated in 30 seconds.
    Requires human review and approval before delivery.

    Output Constraints:
    - executive_summary: 2 paragraphs (~400-500 words)
    - business_model_canvas: 3-5 items per block (~500-700 words total)
    """

    tier: Literal["basic"] = "basic"

    title: str = Field(
        ..., description="Short, catchy title for the business idea (3-7 words)"
    )

    go_no_go_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Data-driven Go/No-Go Recommendation Score (0-100) based on 8 dimensions",
    )

    scores: GoNoGoScores = Field(
        ..., description="Detailed breakdown of the 8 Go/No-Go scoring dimensions"
    )

    executive_summary: BasicExecutiveSummary = Field(
        ..., description="2-paragraph structured executive summary"
    )

    business_model_canvas: BusinessModelCanvas = Field(
        ..., description="Visual one-page overview of the 9 key building blocks"
    )

# ============================================================
# STANDARD TIER OUTPUT (40-50 A4 pages, 3-5 minutes + review)
# ============================================================

# --- Enhanced Business Model Canvas ---
class EnhancedBusinessModelCanvas(BaseModel):
    """
    Enhanced BMC for Standard/Premium Tiers (Per Tiers.docx)
    - All 9 building blocks with European market context
    - Revenue streams and cost structure analysis
    - Key metrics and success indicators
    - Visual one-page overview + detailed explanations
    """

    # Override base fields with detailed descriptions
    customer_segments: List[str] = Field(
        ...,
        description="4-5 detailed items: Who exactly will buy from you - specific customer segments with European market context, demographics, firmographics, and behavior patterns",
    )

    value_propositions: List[str] = Field(
        ..., description="4-5 detailed items: Unique value delivered to each segment - pain relievers, gain creators, and differentiation from alternatives"
    )

    channels: List[str] = Field(
        ...,
        description="4-5 detailed items: Full customer journey - how customers discover, evaluate, purchase, receive, and get support (European distribution specifics)",
    )

    customer_relationships: List[str] = Field(
        ...,
        description="4-5 detailed items: Relationship types (self-service, personal, community, automated) with CAC/LTV implications",
    )

    revenue_streams: List[str] = Field(
        ..., description="4-5 detailed items: Revenue model analysis - pricing tiers, one-time vs recurring, transaction fees, with EUR projections"
    )

    key_resources: List[str] = Field(
        ...,
        description="4-5 detailed items: Essential resources - IP, technology, data, people, brand, and distribution assets needed",
    )

    key_activities: List[str] = Field(
        ...,
        description="4-5 detailed items: Critical activities - production, platform management, problem-solving, partnerships",
    )

    key_partnerships: List[str] = Field(
        ...,
        description="4-5 detailed items: Strategic partners - suppliers, alliances, technology providers, distribution partners in European markets",
    )

    cost_structure: List[str] = Field(
        ..., description="4-5 detailed items: Cost structure analysis - fixed vs variable, economies of scale, major cost drivers with EUR estimates"
    )

    # Additional Enhanced fields per Tiers.docx
    market_adjustments: List[str] = Field(
        ..., description="3-4 items: Adaptations required for European market context (regulations, culture, competition)"
    )

    key_metrics: List[str] = Field(
        ..., description="5-7 items: Success indicators and KPIs to track (LTV:CAC, MRR, churn rate, NPS, etc.)"
    )

    bmc_highlights: List[str] = Field(
        ..., description="3-5 items: Key highlights and differentiators of the business model"
    )


# --- Market Analysis ---
class MarketSizeDetails(BaseModel):
    """Market size estimation details - required for OpenAI structured output"""

    definition: str = Field(..., description="How this market segment is defined")
    estimation_method: str = Field(
        ..., description="Method used to estimate the market size"
    )
    cross_check: str = Field(
        ..., description="Cross-check or validation of the estimate"
    )


class MarketSize(BaseModel):
    """Market size with value and details"""

    value: str = Field(..., description="Market size value (e.g., '500M EUR')")
    details: MarketSizeDetails = Field(
        ..., description="Details about the market size estimation"
    )
    sources: List[str] = Field(
        ..., description="List of sources or basis for this estimate"
    )


class MarketGrowthAnalysis(BaseModel):
    """Market growth analysis with drivers/barriers"""

    drivers: List[str] = Field(..., description="Key market drivers")
    barriers: List[str] = Field(..., description="Market entry barriers")
    trends: List[str] = Field(..., description="Emerging market trends")
    growth_trajectory: str = Field(
        ..., description="Projected growth trajectory summary"
    )


class CustomerDemographics(BaseModel):
    """Customer demographics profile"""

    age_range: str = Field(..., description="Target age range (e.g., '25-45')")
    income_level: str = Field(..., description="Income level description")
    location: str = Field(..., description="Geographic focus")
    psychographics: str = Field(..., description="Interests, values, and behaviors")
    pain_points: List[str] = Field(
        ..., description="Key pain points this customer faces"
    )


class MarketAnalysisReport(BaseModel):
    """Market Analysis Report (5-7 pages) - STRICT SCHEMA"""

    total_addressable_market: MarketSize = Field(
        ..., description="TAM with market breakdown"
    )

    serviceable_addressable_market: MarketSize = Field(
        ..., description="SAM - realistic portion of TAM you can serve"
    )

    serviceable_obtainable_market: MarketSize = Field(
        ..., description="SOM Year 1-3 projections - realistic market share"
    )

    growth_trends: MarketGrowthAnalysis = Field(
        ..., description="Structured market dynamics analysis"
    )

    customer_demographics: CustomerDemographics = Field(
        ..., description="Demographics, psychographics, and customer behaviors"
    )

    market_entry_barriers: List[str] = Field(
        ..., description="Barriers to entry and market opportunities identified"
    )


# --- Competitive Intelligence ---
class Competitor(BaseModel):
    """Single competitor analysis - enhanced for Porter's Five Forces integration"""

    name: str = Field(..., description="Competitor company name")
    hq_location: str = Field(..., description="Country/City headquarters location")
    strengths: List[str] = Field(..., description="Key strengths of this competitor")
    weaknesses: List[str] = Field(..., description="Key weaknesses of this competitor")
    market_position: str = Field(
        ..., description="Market leader/Challenger/Niche player"
    )
    pricing_model: str = Field(..., description="Pricing model and {currency} range")
    threat_score: Literal["High", "Medium", "Low"] = Field(..., description="Threat level score")
    threat_rationale: str = Field(..., description="Reasoning for the threat level")


class IndirectAlternative(BaseModel):
    """Indirect alternative analysis - matches enhanced prompt output"""

    alternative: str = Field(
        ...,
        description="Description of alternative (e.g., spreadsheets, manual process)",
    )
    why_customers_use_it: str = Field(
        ..., description="Reasoning why customers use this alternative"
    )
    how_to_win_against: str = Field(
        ..., description="Strategy to convert these customers"
    )


class ForceAnalysis(BaseModel):
    """Single force analysis for Porter's Five Forces"""

    score: str = Field(..., description="High/Medium/Low assessment")
    analysis: str = Field(..., description="Detailed analysis of this force")


class PortersFiveForces(BaseModel):
    """Porter's Five Forces analysis framework"""

    threat_of_new_entrants: ForceAnalysis = Field(
        ...,
        description="What barriers protect incumbents? (technology, network effects, regulations, capital)",
    )
    supplier_power: ForceAnalysis = Field(
        ...,
        description="Are there critical dependencies? (APIs, data sources, infrastructure)",
    )
    buyer_power: ForceAnalysis = Field(
        ...,
        description="How much leverage do customers have? (switching costs, concentration)",
    )
    threat_of_substitutes: ForceAnalysis = Field(
        ...,
        description="What could make this product obsolete? (AI, regulatory changes, behavior shifts)",
    )
    competitive_rivalry: ForceAnalysis = Field(
        ...,
        description="How intense is the competition? (price wars, feature parity, market growth)",
    )


class CompetitorPosition(BaseModel):
    """Competitor position data"""

    name: str = Field(..., description="Competitor name")
    quadrant: str = Field(..., description="Quadrant position")
    x: float = Field(..., description="X value")
    y: float = Field(..., description="Y value")


class PositioningAnalysis(BaseModel):
    """Competitive positioning map data - enhanced"""

    x_axis: str = Field(..., description="X-axis label (e.g., 'Price: Low to High')")
    y_axis: str = Field(
        ..., description="Y-axis label (e.g., 'Features: Basic to Advanced')"
    )
    quadrant_descriptions: List[str] = Field(
        ..., description="Description of each quadrant"
    )
    competitor_positions: List[CompetitorPosition] = Field(
        ...,
        description="List of competitor positions",
    )
    recommended_position: str = Field(
        ..., description="Where this startup should position and why"
    )


class CompetitorStrategy(BaseModel):
    """Competitor strategy analysis"""

    competitor_name: str = Field(..., description="Name of competitor")
    strategy_summary: str = Field(..., description="Summary of their strategy")
    target_segment: str = Field(..., description="Their primary target segment")


class DifferentiationOpportunity(BaseModel):
    """Differentiation opportunity with difficulty and impact assessment"""

    opportunity: str = Field(
        ..., description="Description of the differentiation opportunity"
    )
    difficulty: str = Field(..., description="Easy/Medium/Hard to implement")
    impact: str = Field(..., description="High/Medium/Low expected impact")


class CompetitiveMoat(BaseModel):
    """Competitive moat with implementation details"""

    moat_type: str = Field(
        ..., description="Type: Network/Switching/Data/Brand/Scale/IP"
    )
    description: str = Field(..., description="How to build this moat")
    time_to_build: str = Field(..., description="Months/Years estimate to build")


class CompetitiveIntelligence(BaseModel):
    """Competitive Intelligence (4-6 pages) - Enhanced with Porter's Five Forces"""

    direct_competitors: List[Competitor] = Field(
        ...,
        description="Top 5-10 direct competitors analysis with funding and threat levels",
    )

    indirect_alternatives: List[IndirectAlternative] = Field(
        ...,
        description="Indirect alternatives and substitute solutions (backward compatible)",
    )

    porters_five_forces: PortersFiveForces = Field(
        ..., description="Porter's Five Forces analysis framework"
    )

    competitive_positioning: PositioningAnalysis = Field(
        ..., description="Structured positioning map data with recommended position"
    )

    competitor_strategies: List[CompetitorStrategy] = Field(
        ..., description="Detailed strategy analysis for key competitors"
    )

    differentiation_opportunities: List[DifferentiationOpportunity] = Field(
        ..., description="Unique value proposition and differentiation opportunities"
    )

    competitive_moats: List[CompetitiveMoat] = Field(
        ..., description="Competitive advantages and moats to build"
    )

    competitive_strategy_recommendation: str = Field(
        ...,
        description="2-3 sentence strategic recommendation for competitive positioning",
    )


# --- Financial Feasibility ---
class YearlyProjection(BaseModel):
    """Single year financial projection"""

    revenue: str = Field(..., description="Projected revenue in {currency}")
    costs: str = Field(..., description="Projected costs in {currency}")
    profit: str = Field(..., description="Projected profit/loss in {currency}")
    key_assumptions: List[str] = Field(
        ..., description="Key assumptions for this projection"
    )


class FinancialProjections(BaseModel):
    """3-year financial projections with conservative/realistic/optimistic scenarios"""

    conservative: YearlyProjection = Field(..., description="Conservative scenario (worst case) - Year 1-3 averages")
    realistic: YearlyProjection = Field(..., description="Realistic scenario (most likely) - Year 1-3 averages")
    optimistic: YearlyProjection = Field(..., description="Optimistic scenario (best case) - Year 1-3 averages")
    year_1_detailed: YearlyProjection = Field(..., description="Year 1 detailed projection (realistic case)")
    year_2_detailed: YearlyProjection = Field(..., description="Year 2 detailed projection (realistic case)")
    year_3_detailed: YearlyProjection = Field(..., description="Year 3 detailed projection (realistic case)")


class UnitEconomics(BaseModel):
    """Unit economics breakdown"""

    cac: str = Field(..., description="Customer Acquisition Cost in {currency}")
    ltv: str = Field(..., description="Lifetime Value in {currency}")
    ltv_cac_ratio: str = Field(..., description="LTV:CAC ratio (e.g., '3:1')")
    contribution_margin: str = Field(..., description="Contribution margin percentage")
    payback_period_months: str = Field(..., description="CAC payback period in months")


class RevenueModel(BaseModel):
    """Revenue model details"""

    primary_model: str = Field(
        ..., description="Primary revenue model (subscription, transaction, etc.)"
    )
    pricing_tiers: List[str] = Field(..., description="Pricing tier descriptions")
    revenue_drivers: List[str] = Field(..., description="Key revenue drivers")


class BreakEvenAnalysis(BaseModel):
    """Break-even analysis"""

    break_even_point: str = Field(
        ..., description="Break-even point in units or revenue"
    )
    timeline_months: str = Field(..., description="Months to break-even")
    key_factors: List[str] = Field(..., description="Key factors affecting break-even")


class InvestmentRequirements(BaseModel):
    """Initial investment requirements"""

    total_amount: str = Field(
        ..., description="Total initial investment needed in {currency}"
    )
    development: str = Field(..., description="Development costs in {currency}")
    marketing: str = Field(..., description="Marketing costs in {currency}")
    operations: str = Field(..., description="Operations costs in {currency}")
    contingency: str = Field(..., description="Contingency buffer in {currency}")


class FinancialKPI(BaseModel):
    """Financial KPI with detailed targets - for Financials module"""
    kpi: str = Field(..., description="Name of the KPI")
    target: str = Field(..., description="Target value")
    why_critical: str = Field(..., description="Why this KPI is critical")
    year_1_target: str = Field(..., description="Year 1 specific target")


class BurnRateRunway(BaseModel):
    """Burn rate and runway"""

    monthly_burn_rate: str = Field(..., description="Monthly burn rate in {currency}")
    runway_months: str = Field(..., description="Runway in months with current funding")
    key_expenses: Dict[str, str] = Field(..., description="Key monthly expense categories as dict")
    average_burn_calculation: Optional[str] = Field(None, description="How burn rate was calculated")
    runway_calculation: Optional[str] = Field(None, description="How runway was calculated")


class FinancialFeasibility(BaseModel):
    """Financial Feasibility (5-6 pages) - STRICT SCHEMA"""

    three_year_projections: FinancialProjections = Field(
        ..., description="3-year financial projections"
    )

    revenue_model: RevenueModel = Field(
        ..., description="Revenue model and pricing strategy"
    )

    unit_economics: UnitEconomics = Field(
        ..., description="CAC, LTV, contribution margin breakdown"
    )

    break_even_analysis: BreakEvenAnalysis = Field(
        ..., description="Break-even analysis and timeline"
    )

    initial_investment: InvestmentRequirements = Field(
        ..., description="Initial investment requirements"
    )

    burn_rate_runway: BurnRateRunway = Field(
        ..., description="Monthly burn rate and runway"
    )

    key_financial_kpis: List[FinancialKPI] = Field(
        ..., description="Key financial metrics to track as structured objects"
    )

# --- Technical Requirements ---
class TechStack(BaseModel):
    """Technology stack recommendation - enhanced with rationale"""

    frontend: List[str] = Field(
        ..., description="Frontend technologies with justification"
    )
    backend: List[str] = Field(
        ..., description="Backend technologies with justification"
    )
    database: List[str] = Field(
        ..., description="Database technologies with justification"
    )
    infrastructure: List[str] = Field(..., description="Cloud provider with EU region")
    tools: List[str] = Field(..., description="Development and monitoring tools")
    stack_rationale: str = Field(
        ..., description="Why this stack is optimal for this startup"
    )


class Milestone(BaseModel):
    """Single development milestone - enhanced with deliverable"""

    week: str = Field(..., description="Week or week range (e.g., 'Week 1-2')")
    tasks: str = Field(..., description="Tasks to complete in this period")
    deliverable: str = Field(..., description="Expected output/deliverable")


class DevelopmentTimeline(BaseModel):
    """Development timeline"""

    mvp_weeks: str = Field(..., description="Weeks to MVP with key deliverable")
    beta_weeks: str = Field(
        ..., description="Weeks to beta launch with key deliverable"
    )
    launch_weeks: str = Field(
        ..., description="Weeks to full launch with key deliverable"
    )
    key_milestones: List[Milestone] = Field(
        ..., description="Key development milestones"
    )


class MVPFeature(BaseModel):
    """MVP feature with prioritization"""

    feature: str = Field(..., description="Feature name")
    priority: str = Field(..., description="Must-have/Nice-to-have")
    effort_days: str = Field(..., description="Estimated effort in days")


class TeamComposition(BaseModel):
    """Technical team composition - enhanced with {geography} hiring notes"""

    required_roles: List[str] = Field(
        ..., description="Required technical roles with tech requirements"
    )
    skills_needed: List[str] = Field(
        ..., description="Specific technical skills needed"
    )
    team_size: str = Field(..., description="X people at each stage")
    hiring_priority: List[str] = Field(
        ..., description="Role 1 (immediate), Role 2 (month 3)"
    )
    hiring_notes: str = Field(..., description="Where to find talent in the target geography")


class InfrastructureCosts(BaseModel):
    """Infrastructure costs breakdown by stage"""

    mvp_monthly: str = Field(..., description="{currency} X-Y range at MVP stage")
    growth_monthly: str = Field(..., description="{currency} X-Y range at 10K users")
    scale_monthly: str = Field(..., description="{currency} X-Y range at 100K users")
    cost_drivers: List[str] = Field(..., description="Primary cost factors")


class ScalabilityAnalysis(BaseModel):
    """Scalability planning"""

    current_capacity: str = Field(..., description="Current system capacity")
    scaling_triggers: List[str] = Field(..., description="Triggers for scaling up")
    architecture_changes: List[str] = Field(
        ..., description="Required architecture changes"
    )


class SecurityComplianceRequirement(BaseModel):
    """Security compliance requirement with implementation details"""

    requirement: str = Field(..., description="Compliance requirement description")
    implementation: str = Field(..., description="How to implement this requirement")


class TechnicalRequirements(BaseModel):
    """Technical Requirements (3-4 pages) - Aligned with TECH_PROMPT output"""

    technology_stack: TechStack = Field(
        ..., description="Recommended technology stack with rationale"
    )

    development_timeline: DevelopmentTimeline = Field(
        ..., description="Development timeline and milestones"
    )

    mvp_features: List[MVPFeature] = Field(
        ..., description="MVP feature prioritization (structured objects)"
    )

    team_composition: TeamComposition = Field(
        ..., description="Technical team composition with hiring notes"
    )

    infrastructure_costs: InfrastructureCosts = Field(
        ..., description="Multi-stage infrastructure costs (MVP, growth, scale)"
    )

    scalability_plan: ScalabilityAnalysis = Field(
        ..., description="Structured scalability planning"
    )

    security_compliance: List[SecurityComplianceRequirement] = Field(
        ..., description="Security compliance requirements (e.g. GDPR, HIPAA) with implementation details"
    )


# --- Regulatory Compliance ---
class DataPrivacyCompliance(BaseModel):
    """Data Privacy compliance requirements (GDPR, HIPAA, etc.)"""

    applicable_regulation: str = Field(
        ..., description="Primary regulation name (e.g., 'HIPAA', 'GDPR', 'CCPA')"
    )
    data_categories: List[str] = Field(
        ..., description="Categories of personal/sensitive data collected"
    )
    legal_basis: str = Field(..., description="Legal basis for processing under this regulation")
    required_measures: List[str] = Field(
        ..., description="Required compliance measures"
    )
    estimated_cost: str = Field(..., description="Estimated compliance cost in {currency}")


class IPConsiderations(BaseModel):
    """Intellectual property considerations"""

    trademark_needs: List[str] = Field(..., description="Trademark protection needs")
    patent_opportunities: List[str] = Field(
        ..., description="Potential patent opportunities"
    )
    copyright_items: List[str] = Field(
        ..., description="Items requiring copyright protection"
    )


class ComplianceCosts(BaseModel):
    """Compliance costs breakdown"""

    setup_cost: str = Field(..., description="Estimated range ONLY (e.g. '{currency} 10,000-20,000'). NO text explanations.")
    annual_cost: str = Field(..., description="Estimated range ONLY (e.g. '{currency} 5,000-10,000'). NO text explanations.")
    legal_fees: str = Field(..., description="Estimated range ONLY (e.g. '{currency} 2,000-5,000'). NO text explanations.")
    cost_breakdown: List[str] = Field(..., description="Top 5 major cost drivers (max 10 words each)")


class RegulatoryCompliance(BaseModel):
    """Regulatory Compliance (3-4 pages) - STRICT SCHEMA"""

    data_privacy_compliance: DataPrivacyCompliance = Field(
        ..., description="Data privacy requirements and implementation"
    )

    country_regulations: List[str] = Field(
        ..., description="Country-specific regulations in target markets"
    )

    industry_compliance: List[str] = Field(
        ..., description="Industry-specific compliance needs"
    )

    licensing_permits: List[str] = Field(
        ..., description="Required licensing and permits"
    )

    intellectual_property: IPConsiderations = Field(
        ..., description="IP considerations"
    )

    terms_of_service_requirements: List[str] = Field(
        ..., description="Required clauses for Terms of Service (B2B/B2C)"
    )

    privacy_policy_requirements: List[str] = Field(
        ..., description="Specific requirements for Privacy Policy"
    )

    compliance_costs: ComplianceCosts = Field(
        ..., description="Estimated legal and compliance costs"
    )


# --- Go To Market Strategy ---
class AcquisitionChannel(BaseModel):
    """Customer acquisition channel"""

    channel: str = Field(..., description="Channel name")
    roi_rank: int = Field(..., description="ROI ranking (1=best)")
    estimated_cac: str = Field(..., description="Estimated CAC for this channel")
    strategy: str = Field(..., description="Strategy for this channel")


class LaunchStrategy(BaseModel):
    """90-day launch strategy"""

    week_1_4: List[str] = Field(..., description="Actions for weeks 1-4")
    week_5_8: List[str] = Field(..., description="Actions for weeks 5-8")
    week_9_12: List[str] = Field(..., description="Actions for weeks 9-12")


class MarketingBudget(BaseModel):
    """Marketing budget allocation"""

    total_monthly: str = Field(..., description="Total monthly marketing budget")
    paid_acquisition: str = Field(..., description="Paid acquisition budget")
    content_marketing: str = Field(..., description="Content marketing budget")
    events_pr: str = Field(..., description="Events and PR budget")


class ContentSEOStrategy(BaseModel):
    """Content and SEO strategy"""

    target_keywords: List[str] = Field(..., description="Target keywords for SEO")
    content_types: List[str] = Field(..., description="Types of content to create")
    publishing_frequency: str = Field(..., description="Content publishing frequency")


class PricingPositioning(BaseModel):
    """Pricing and positioning strategy"""

    positioning_statement: str = Field(..., description="Market positioning statement")
    pricing_strategy: str = Field(
        ..., description="Pricing strategy (premium, competitive, etc.)"
    )
    price_points: List[str] = Field(..., description="Key price points")


class GoToMarketStrategy(BaseModel):
    """Go-to-Market Strategy (4-5 pages) - STRICT SCHEMA"""

    acquisition_channels: List[AcquisitionChannel] = Field(
        ..., description="Customer acquisition channels ranked by ROI"
    )

    launch_strategy: LaunchStrategy = Field(..., description="90-day launch strategy")

    marketing_budget: MarketingBudget = Field(
        ..., description="Marketing budget allocation"
    )

    content_seo_strategy: ContentSEOStrategy = Field(
        ..., description="Content marketing and SEO strategy"
    )

    partnerships: List[str] = Field(
        ..., description="Partnership and distribution opportunities"
    )

    pricing_positioning: PricingPositioning = Field(
        ..., description="Pricing strategy and market positioning"
    )

    growth_hacking: List[str] = Field(..., description="Growth hacking tactics")


# --- Risk Assessment ---
class Risk(BaseModel):
    """Single risk assessment"""

    risk_name: str = Field(..., description="Name of the risk")
    probability: str = Field(..., description="Probability: low, medium, or high")
    impact: str = Field(..., description="Impact: low, medium, or high")
    mitigation: str = Field(..., description="Mitigation strategy")


class ContingencyPlan(BaseModel):
    """Contingency plan"""

    trigger: str = Field(..., description="What triggers this contingency")
    actions: List[str] = Field(..., description="Actions to take")
    pivot_option: str = Field(..., description="Potential pivot if needed")


class RiskAssessment(BaseModel):
    """Risk Assessment Matrix (2-3 pages) - STRICT SCHEMA"""

    top_risks: List[Risk] = Field(
        ..., description="Top 15 risks ranked by probability × impact"
    )

    mitigation_strategies: List[str] = Field(
        ..., description="Risk mitigation strategies"
    )

    contingency_plans: List[ContingencyPlan] = Field(
        ..., description="Contingency plans and pivot options"
    )

    kill_switches: List[str] = Field(
        ..., description="Clear indicators when to stop or pivot"
    )

    dependency_risks: List[str] = Field(
        ..., description="Dependency risks and single points of failure"
    )

    market_timing_risks: List[str] = Field(
        ..., description="Market timing and competition risks"
    )


# --- Implementation Roadmap ---
class NinetyDayPlan(BaseModel):
    """90-day implementation plan with weekly milestones"""

    week_1_2: List[str] = Field(..., description="Weeks 1-2 milestones: Customer discovery, problem validation")
    week_3_4: List[str] = Field(..., description="Weeks 3-4 milestones: MVP planning, initial development")
    week_5_6: List[str] = Field(..., description="Weeks 5-6 milestones: Core feature build")
    week_7_8: List[str] = Field(..., description="Weeks 7-8 milestones: Beta testing setup")
    week_9_10: List[str] = Field(..., description="Weeks 9-10 milestones: Beta testing with early customers")
    week_11_12: List[str] = Field(..., description="Weeks 11-12 milestones: Iterate and prepare for launch")


class SixMonthPlan(BaseModel):
    """6-month growth plan"""

    month_4_6: List[str] = Field(..., description="Months 4-6 objectives")
    key_metrics: List[str] = Field(..., description="Key metrics to track")
    growth_targets: str = Field(..., description="Growth targets for this period")


class OKR(BaseModel):
    """OKR"""
    objective: str = Field(..., description="OKR objective")
    key_results: List[str] = Field(..., description="OKR key results")


class YearOneObjectives(BaseModel):
    """Year 1 strategic objectives"""

    revenue_target: str = Field(..., description="Year 1 revenue target")
    customer_target: str = Field(..., description="Year 1 customer target")
    key_objectives: List[str] = Field(..., description="Key strategic objectives")
    okrs: List[OKR] = Field(..., description="Top OKRs for Year 1")

class ResourceNeed(BaseModel):
    """Single resource requirement"""
    resource: str = Field(..., description="Resource item (e.g., 'Senior Developer')")
    details: str = Field(..., description="Cost or quantity details (e.g., '{currency} 5,000/month'). Use {currency} placeholder.")


class ResourceTimeline(BaseModel):
    """Resource requirements timeline"""

    q1_needs: List[ResourceNeed] = Field(..., description="Q1 resource needs")
    q2_needs: List[ResourceNeed] = Field(..., description="Q2 resource needs")
    q3_needs: List[ResourceNeed] = Field(..., description="Q3 resource needs")
    q4_needs: List[ResourceNeed] = Field(..., description="Q4 resource needs")


class SuccessMetrics(BaseModel):
    """Success metrics by timeframe"""

    weekly_metrics: List[str] = Field(..., description="Weekly tracking metrics")
    monthly_metrics: List[str] = Field(..., description="Monthly tracking metrics")
    quarterly_metrics: List[str] = Field(..., description="Quarterly tracking metrics")


class ImplementationRoadmap(BaseModel):
    """Implementation Roadmap (3-4 pages) - STRICT SCHEMA"""

    ninety_day_plan: NinetyDayPlan = Field(
        ..., description="90-day launch plan with milestones"
    )

    six_month_plan: SixMonthPlan = Field(..., description="6-month growth plan")

    year_one_objectives: YearOneObjectives = Field(
        ..., description="Year 1 strategic objectives"
    )

    resource_timeline: ResourceTimeline = Field(
        ..., description="Resource requirements timeline"
    )

    critical_path: List[str] = Field(..., description="Critical path activities")

    success_metrics: SuccessMetrics = Field(
        ..., description="Success metrics by timeframe"
    )


# --- Funding Strategy ---
class FundingOption(BaseModel):
    """Funding option assessment"""

    option_type: str = Field(
        ..., description="Type of funding (bootstrapping, angel, VC, grants)"
    )
    suitability: str = Field(
        ..., description="Suitability for this startup: high, medium, low"
    )
    pros: List[str] = Field(..., description="Pros of this option")
    cons: List[str] = Field(..., description="Cons of this option")


class GrantOpportunity(BaseModel):
    """Grant opportunity"""

    name: str = Field(..., description="Grant program name")
    amount: str = Field(..., description="Grant amount available")
    eligibility: str = Field(..., description="Eligibility requirements")
    deadline: str = Field(..., description="Application deadline or timeline")


class InvestorProfile(BaseModel):
    """Investor landscape"""

    investor_types: List[str] = Field(..., description="Types of investors to target")
    vcs: List[str] = Field(..., description="Relevant VCs")
    angel_networks: List[str] = Field(..., description="Relevant angel networks")


class FundingTimeline(BaseModel):
    """Funding timeline and milestones"""

    pre_seed_timing: str = Field(..., description="Pre-seed round timing and target")
    seed_timing: str = Field(..., description="Seed round timing and target")
    series_a_timing: str = Field(..., description="Series A timing and target")
    milestones_for_next_round: List[str] = Field(
        ..., description="Milestones to hit before next round"
    )


class ValuationBenchmarks(BaseModel):
    """Valuation benchmarks"""

    pre_seed_range: str = Field(..., description="Pre-seed valuation range")
    seed_range: str = Field(..., description="Seed valuation range")
    comparable_companies: List[str] = Field(
        ..., description="Comparable company valuations"
    )
    equity_guidance: str = Field(..., description="Equity dilution guidance")


class FundingStrategy(BaseModel):
    """Funding Strategy Guide (3-4 pages) - STRICT SCHEMA"""

    funding_options: List[FundingOption] = Field(
        ..., description="Assessment of funding options"
    )

    grants: List[GrantOpportunity] = Field(..., description="Grant opportunities")

    investor_landscape: InvestorProfile = Field(
        ..., description="Investor landscape mapping"
    )

    funding_timeline: FundingTimeline = Field(
        ..., description="Funding timeline and milestones"
    )

    valuation_benchmarks: ValuationBenchmarks = Field(
        ..., description="Valuation benchmarks and equity"
    )

    fundraising_process: List[str] = Field(
        ..., description="Fundraising process best practices"
    )


# --- Executive Summary ---
class BusinessOpportunitySummary(BaseModel):
    """Business Opportunity Section"""

    problem_summary: str = Field(
        ..., description="Core problem being solved (text only, no markdown)"
    )
    solution_overview: str = Field(
        ..., description="Proposed solution description (text only, no markdown)"
    )
    target_market: str = Field(
        ...,
        description="Target customer and market size summary (text only, no markdown)",
    )
    value_proposition: str = Field(
        ..., description="Unique value proposition (text only, no markdown)"
    )


class RecommendationSummary(BaseModel):
    """Final Recommendation Section"""

    go_no_go_verdict: Literal["Go", "Conditional-Go", "No-Go"] = Field(..., description="Clear Go/Conditional-Go/No-Go statement")
    rating_justification: str = Field(
        ..., description="Reasoning for the verdict (text only, no markdown, 4-5 sentences)"
    )
    key_strengths: List[str] = Field(
        ..., description="Top 3-5 reasons to proceed"
    )
    key_risks: List[str] = Field(
        ..., description="Top 3-5 concerns (contrarian view)"
    )
    immediate_action_items: List[str] = Field(
        ..., description="Top 5 recommended actions with timelines"
    )


class ExecutiveSummary(BaseModel):
    """
    Structured Executive Summary for Standard/Premium/Custom Tiers
    5 pages total: Problem, Solution, Selected Modules Summary, Recommendation
    """

    problem_summary: str = Field(
        ..., description="Comprehensive problem analysis (~500 words): Who experiences this, severity, cost of inaction"
    )
    proposed_solution: str = Field(
        ..., description="Detailed solution overview (~500 words): How it solves the problem, key features, differentiation"
    )
    report_highlights: List[str] = Field(
        ..., description="Top 5 key highlights from the report. Max 50 words each"
    )
    recommendation: RecommendationSummary = Field(
        ..., description="Final recommendation (~500 words): Verdict, justification, strengths, risks, action items"
    )


# --- Modules Wrapper for Standard/Premium ---
class StandardPremiumModules(BaseModel):
    """Wrapper for all modules in Standard/Premium tiers - matches JSON structure"""
    business_model_canvas: Optional[EnhancedBusinessModelCanvas] = None
    market_analysis: Optional[MarketAnalysisReport] = None
    competitive_intelligence: Optional[CompetitiveIntelligence] = None
    financials: Optional[FinancialFeasibility] = None  # Note: JSON uses 'financials' not 'financial_feasibility'
    technical_requirements: Optional[TechnicalRequirements] = None
    regulatory: Optional[RegulatoryCompliance] = None  # Note: JSON uses 'regulatory' not 'regulatory_compliance'
    gtm_strategy: Optional[GoToMarketStrategy] = None
    risks: Optional[RiskAssessment] = None  # Note: JSON uses 'risks' not 'risk_assessment'
    roadmap: Optional[ImplementationRoadmap] = None  # Note: JSON uses 'roadmap' not 'implementation_roadmap'
    funding: Optional[FundingStrategy] = None  # Note: JSON uses 'funding' not 'funding_strategy'


class StandardReportOutput(BaseModel):
    """
    Standard Tier Deliverable: Comprehensive 40-50 A4 pages (~20,000-25,000 words).
    Generated in 30 seconds but requires human review and approval.

    Output Constraints:
    - executive_summary: 5 pages (~2500 words)
    - 10 comprehensive modules with detailed analysis:
      * Business Model Canvas: 1-2 pages
      * Market Analysis: 5-7 pages
      * Competitive Intelligence: 4-6 pages
      * Financial Feasibility: 5-6 pages
      * Technical Requirements: 3-4 pages
      * Regulatory Compliance: 3-4 pages
      * Go-to-Market Strategy: 4-5 pages
      * Risk Assessment: 2-3 pages
      * Implementation Roadmap: 3-4 pages
      * Funding Strategy: 3-4 pages
    """

    tier: Literal["standard"] = "standard"

    title: str = Field(
        ..., description="Short, catchy title for the business idea (3-7 words)"
    )

    go_no_go_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Data-driven Go/No-Go Recommendation Score (0-100)",
    )

    score_breakdown: GoNoGoScores = Field(
        ..., description="Detailed breakdown of the 8 Go/No-Go scoring dimensions"
    )

    executive_summary: ExecutiveSummary = Field(
        ..., description="Structured executive summary object"
    )

    modules: StandardPremiumModules = Field(
        ..., description="All report modules wrapped in modules object"
    )
    
    investor_pitch_deck: Optional[InvestorPitchDeck] = Field(
        None, description="Optional Pitch Deck content if requested (Premium or Custom Module)"
    )


# ============================================
# PREMIUM TIER OUTPUT (Same as Standard)
# ============================================


class PremiumReportOutput(BaseModel):
    """
    Premium Tier Deliverable: Same report content as Standard tier.
    Premium features (consultation, pitch deck, community access) handled by frontend.
    """

    tier: Literal["premium"] = "premium"

    title: str = Field(
        ..., description="Short, catchy title for the business idea (3-7 words)"
    )

    go_no_go_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Data-driven Go/No-Go Recommendation Score (0-100)",
    )

    score_breakdown: GoNoGoScores = Field(
        ..., description="Detailed breakdown of the 8 Go/No-Go scoring dimensions"
    )

    executive_summary: ExecutiveSummary = Field(
        ..., description="Structured executive summary object"
    )

    modules: StandardPremiumModules = Field(
        ..., description="All report modules wrapped in modules object"
    )

    investor_pitch_deck: Optional[InvestorPitchDeck] = Field(
        None, description="Detailed 12-slide Pitch Deck content and instructions"
    )


# ============================================
# MODULE ALIASES (For backward compatibility)
# ============================================
BMCModule = EnhancedBusinessModelCanvas
MarketModule = MarketAnalysisReport
CompetitorModule = CompetitiveIntelligence
FinancialsModule = FinancialFeasibility
TechModule = TechnicalRequirements
RegulatoryModule = RegulatoryCompliance
GTMModule = GoToMarketStrategy
RiskModule = RiskAssessment
RoadmapModule = ImplementationRoadmap
FundingModule = FundingStrategy


# ============================================
# BASIC TIER GENERATION SCHEMA
# ============================================
class BasicTierGeneration(BaseModel):
    """Schema for basic tier LLM structured output generation"""

    title: str = Field(
        ..., description="Short, catchy title for the business idea (3-7 words)"
    )
    scores: GoNoGoScores
    executive_summary: BasicExecutiveSummary = Field(
        ..., description="2-paragraph structured executive summary"
    )
    business_model_canvas: BusinessModelCanvas