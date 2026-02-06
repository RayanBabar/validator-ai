import pytest
from src.agents.search.credibility import score_source_credibility
from src.agents.search.query_generator import _fallback_queries

def test_credibility_known_high():
    # Test new high credibility domain
    score, level = score_source_credibility("https://www.statista.com/statistics/123")
    assert score == 10
    assert level == "high"

def test_credibility_known_medium():
    # Test medium credibility
    score, level = score_source_credibility("https://www.forbes.com/sites/someone/article")
    assert score == 7
    assert level == "medium"

def test_credibility_heuristic_gov():
    # Test .gov heuristic
    score, level = score_source_credibility("https://www.transport.gov/data")
    assert score == 9
    assert level == "high"

def test_credibility_heuristic_edu():
    # Test .edu heuristic (unknown university)
    score, level = score_source_credibility("https://www.local-college.edu/research")
    assert score == 9
    assert level == "high"

def test_credibility_heuristic_positive_keyword():
    # Test positive keyword heuristic
    score, level = score_source_credibility("https://www.science-journal-research.com")
    assert score == 7
    assert level == "medium"

def test_credibility_heuristic_negative_keyword():
    # Test negative keyword heuristic
    score, level = score_source_credibility("https://www.best-cheap-review-scam.com")
    assert score <= 4
    assert level == "low"

def test_fallback_queries():
    desc = "A startup for AI driven invoice processing for small businesses"
    objective = "market size"
    year = 2026
    
    queries = _fallback_queries(desc, objective, year)
    
    assert len(queries) >= 3
    # Check if stop words are removed (e.g. "for", "a")
    first_query = queries[0]
    assert "for" not in first_query.split()[:4] 
    assert "invoice" in first_query
    assert str(year) in first_query
