
# ===========================================
# MODEL PRICING (Per 1 Million Tokens) - 2026 RATES
# ===========================================
# Structure: {model_name: {input, cache_read, output}}
# Prices in USD
MODEL_PRICING = {
    # OpenAI Models
    "gpt-5.2": {
        "input": 1.75,
        "output": 14.00
    },
    "gpt-5-nano-2025-08-07": {
        "input": 0.05,
        "output": 0.40
    },
    "gpt-5-mini-2025-08-07": {
        "input": 0.25,
        "output": 2.00
    },
    # Anthropic Models
    "claude-opus-4-6": {
        "input": 5.00,
        "output": 25.00
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.00,
        "output": 15.00
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.00,
        "output": 5.00
    }
}

TAVILY_COST_PER_QUERY = 0.0008
