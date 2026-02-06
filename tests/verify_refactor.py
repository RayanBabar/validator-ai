
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock env vars for Settings validation
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tv-dummy"

try:
    print("Attempting to import modules...")
    from src.agents.search.topics import get_research_topics
    print("✓ Imported topics.py")
    
    from src.agents.search.strategy import get_research_topics as grt_strategy
    print("✓ Imported strategy.py (re-export check)")
    
    from src.agents.search.research import conduct_dynamic_research
    print("✓ Imported research.py")
    
    from src.agents.standard_modules import std_market
    print("✓ Imported standard_modules.py")
    
    # Test function
    topics = get_research_topics("US", "AI")
    assert "mod_market" in topics
    print("✓ get_research_topics works")
    
    print("\nSUCCESS: No circular imports detected.")
except ImportError as e:
    print(f"\nFAILURE: ImportError detected: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nFAILURE: Unexpected error: {e}")
    sys.exit(1)
