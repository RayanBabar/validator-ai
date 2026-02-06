"""
Research Topics Module.

Separates topic definitions from strategy logic to avoid circular imports.
"""
from typing import Dict

def get_research_topics(geography: str, industry: str) -> Dict[str, str]:
    """
    Get the single source of truth for research prompt instructions.
    
    Centralizes all prompt engineering for search queries to ensure consistency
    across Basic, Standard, and Premium tiers.
    
    Args:
        geography: Target geography
        industry: Target industry
        
    Returns:
        Dict mapping module nodes (e.g. 'mod_market') to detailed instructions
    """
    return {
        "mod_market": (
            f"Detailed market sizing for {industry} in {geography}: "
            f"Calculate TAM, SAM, and SOM. Search for recent industry reports (Gartner, Forrester, Statista 2024-2025), "
            f"market CAGR, growth drivers, and specific market trends."
        ),
        "mod_comp": (
            f"Deep competitive landscape for {industry} in {geography}: "
            f"Identify top 3-5 direct competitors and their pricing models. "
            f"Search for '{industry} alternatives', 'vs' comparisons, and user reviews on G2/Capterra to find weaknesses."
        ),
        "mod_finance": (
            f"Financial benchmarks for {industry} startups: "
            f"Search for standard Unit Economics (CAC, LTV, Churn, ARPU), typical gross margins, "
            f"burn rate benchmarks, and Series A revenue milestones."
        ),
        "mod_reg": (
            f"Regulatory compliance landscape for {industry} in {geography}: "
            f"Identify required licenses, data privacy laws (GDPR/CCPA), industry-specific regulations, "
            f"and compliance costs."
        ),
        "mod_risk": (
            f"Critical risk analysis for {industry} startups: "
            f"Identify common failure modes, operational risks, and market threats. "
            f"Look for post-mortems of failed startups in this sector."
        ),
        "mod_gtm": (
            f"Go-to-Market strategies for {industry} in {geography}: "
            f"Best channels for customer acquisition (B2B vs B2C), successful marketing playbooks, "
            f"and sales cycle benchmarks."
        ),
        "mod_funding": (
            f"Investment landscape for {industry} in {geography}: "
            f"Recent VC deals, active investors, grant opportunities, and seed round valuation benchmarks."
        ),
        "mod_tech": (
            f"Technical architecture and stack for {industry}: "
            f"Standard technologies, MVP requirements, build vs buy decisions, and technical challenges."
        ),
        "mod_roadmap": (
            f"Product development roadmap for {industry}: "
            f"Typical MVP features, development timeline milestones, and time-to-market benchmarks."
        )
    }
