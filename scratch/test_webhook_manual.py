import asyncio
import json
from src.utils.webhook import send_report_webhook

async def test_webhook():
    thread_id = "18f8b19d-4aeb-433e-91fd-a4bd08055a91"
    score = 59.0
    metadata = {
        "tier": "free",
        "title": "Hydration AI Coach",
        "viability_score": 59.0,
        "gauge_status": "Healthy",
        "scores": {
            "problem_severity": 7,
            "market_opportunity": 6,
            "competition_intensity": 5,
            "execution_complexity": 6,
            "founder_alignment": 8
        }
    }
    print(f"Testing webhook for {thread_id}...")
    success = await send_report_webhook(thread_id, score, metadata)
    print(f"Webhook success: {success}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
