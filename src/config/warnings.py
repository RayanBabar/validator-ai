"""
Warning suppression configuration.
Import this module at the very top of the application entry point.
"""
import warnings

# Suppress LangChain's Pydantic V1 compatibility warning for Python 3.14
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14",
    category=UserWarning,
    module="langchain_core._api.deprecation"
)

# Suppress LangChain Tavily's field shadowing warning
warnings.filterwarnings(
    "ignore",
    message='Field name "output_schema" in "TavilyResearch" shadows an attribute in parent "BaseTool"',
    category=UserWarning,
    module="langchain_tavily.tavily_research"
)
warnings.filterwarnings(
    "ignore",
    message='Field name "stream" in "TavilyResearch" shadows an attribute in parent "BaseTool"',
    category=UserWarning,
    module="langchain_tavily.tavily_research"
)
