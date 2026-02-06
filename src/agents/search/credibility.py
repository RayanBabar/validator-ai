"""
Source Credibility Scoring for Research Results.

Scores URLs based on domain reputation to filter low-quality sources.
"""
import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# High credibility sources (score: 9-10)
# High credibility sources (score: 9-10)
HIGH_CREDIBILITY_DOMAINS = {
    # Consulting & Research (Tier 1)
    "statista.com": 10,
    "gartner.com": 10,
    "mckinsey.com": 10,
    "bcg.com": 10,
    "bain.com": 10,
    "deloitte.com": 9,
    "pwc.com": 9,
    "kpmg.com": 9,
    "ey.com": 9,
    "forrester.com": 10,
    "idc.com": 9,
    "nielsen.com": 9,
    "accenture.com": 9,
    "capgemini.com": 9,
    
    # Government & International Orgs
    "europa.eu": 10,
    "ec.europa.eu": 10,
    "gov.uk": 10,
    "usa.gov": 10,
    "census.gov": 10,
    "bls.gov": 10,  # Bureau of Labor Statistics
    "sba.gov": 10,  # Small Business Admin
    "worldbank.org": 10,
    "imf.org": 10,
    "oecd.org": 10,
    "weforum.org": 9,
    "who.int": 10,
    "un.org": 10,
    "bundesregierung.de": 9,
    "insee.fr": 9,
    "destatis.de": 9,
    
    # Financial & Business News (Tier 1)
    "bloomberg.com": 9,
    "ft.com": 9,
    "wsj.com": 9,
    "economist.com": 9,
    "reuters.com": 9,
    "cnbc.com": 8,
    "hbr.org": 9,  # Harvard Business Review
    "mit.edu": 10, # MIT Sloan etc
    "stanford.edu": 10,
    "morningstar.com": 9,
    "investopedia.com": 8,
    "marketwatch.com": 8,
    "finance.yahoo.com": 8,
    
    # Tech/Startup/VC
    "techcrunch.com": 8,
    "crunchbase.com": 9,
    "pitchbook.com": 9,
    "cbinsights.com": 9,
    "sifted.eu": 8,
    "ycombinator.com": 9,
    "a16z.com": 9,
    "sequoiacap.com": 9,
    "news.ycombinator.com": 7, # Hacker News (good for sentiment, not facts)
    "producthunt.com": 7,
    "g2.com": 8,
    "capterra.com": 8,
    "trustradius.com": 8,
    "stackoverflow.com": 7,
    "github.com": 8,
    "tldr.tech": 7,
    "venturebeat.com": 8,
    "wired.com": 8,
    "arstechnica.com": 8,
    "verge.com": 7,
}

# Medium credibility sources (score: 6-8)
MEDIUM_CREDIBILITY_DOMAINS = {
    "forbes.com": 7,
    "businessinsider.com": 7,
    "venturebeat.com": 7,
    "wired.com": 7,
    "theinformation.com": 8,
    "theregister.com": 7,
    "zdnet.com": 7,
    "medium.com": 5,  # Varies by author
    "linkedin.com": 6,
    "wikipedia.org": 6,  # Good for background, not primary source
}

# Low credibility patterns (score: 1-4)
LOW_CREDIBILITY_PATTERNS = [
    r"blog\.",
    r"\.blogspot\.",
    r"medium\.com/@",
    r"quora\.com",
    r"reddit\.com",
    r"facebook\.com",
    r"twitter\.com",
    r"pinterest\.com",
]


def score_source_credibility(url: str) -> Tuple[int, str]:
    """
    Score the credibility of a source URL.
    
    Args:
        url: The source URL to score
        
    Returns:
        Tuple of (score 1-10, credibility_level)
    """
    if not url:
        return (5, "unknown")
    
    url_lower = url.lower()
    
    # 1. Exact Domain Match (High)
    for domain, score in HIGH_CREDIBILITY_DOMAINS.items():
        if domain in url_lower:
            return (score, "high")
    
    # 2. Exact Domain Match (Medium)
    for domain, score in MEDIUM_CREDIBILITY_DOMAINS.items():
        if domain in url_lower:
            return (score, "medium")
    
    # 3. Pattern Match (Low)
    for pattern in LOW_CREDIBILITY_PATTERNS:
        if re.search(pattern, url_lower):
            return (3, "low")
            
    # 4. Heuristic Analysis for Unknown Domains
    return _score_unknown_domain_heuristics(url_lower)


def _score_unknown_domain_heuristics(url: str) -> Tuple[int, str]:
    """Apply heuristics to score unknown domains."""
    
    # TLD Trust
    if ".gov" in url or ".mil" in url:
        return (9, "high")
    if ".edu" in url or ".ac.uk" in url:
        return (9, "high")
    if ".org" in url:
         # Non-profits are generally decent but can be biased
        return (7, "medium")
        
    # Keyword Hints (Positive)
    positive_keywords = ["journal", "research", "university", "institute", "official", "statistics"]
    if any(keyword in url for keyword in positive_keywords):
        return (7, "medium")
        
    # Keyword Hints (Negative/Spammy)
    negative_keywords = ["best-", "top-", "review", "scam", "cheap", "coupon", "promo"]
    if any(keyword in url for keyword in negative_keywords):
        return (2, "low")
        
    # Formatting Checks (Low quality indicators)
    # E.g. too many hyphens: www.best-cheap-software-reviews.com
    if url.count("-") > 3:
        return (4, "low")
    
    # Default for completely unknown compliant domains
    return (5, "unknown")



