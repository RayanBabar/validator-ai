from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Example usage
results = client.search(query="What is the capital of France?", max_results=1)
print(results)
