"""
Webhook utilities for sending report data to external systems.
"""

import logging
import httpx
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

WEBHOOK_BASE_URL = "http://localhost:5173"
WEBHOOK_TIMEOUT = 30.0  # seconds


async def send_report_webhook(
    thread_id: str,
    report_score: float,
    report_metadata: Dict[str, Any],
) -> bool:
    """
    Send report data to the external webhook endpoint.
    
    PUT http://localhost:5173/webhook/report/{thread_id}
    
    Args:
        thread_id: The unique thread identifier for this validation journey
        report_score: The viability or go/no-go score from the report
        report_metadata: Additional metadata about the report (tier, title, etc.)
        
    Returns:
        True if webhook was sent successfully, False otherwise
    """
    webhook_url = f"{WEBHOOK_BASE_URL}/webhook/report/{thread_id}"
    
    # User requested payload format: report_score (str), report_metadata (str)
    # Metadata should be a JSON string
    
    payload = {
        "report_score": str(report_score),
        "report_metadata": json.dumps(report_metadata),
    }
    
    
    # Log the payload for debugging
    logger.info(f"Sending webhook payload for thread {thread_id}: {json.dumps(payload, default=str)}")

    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            response = await client.put(webhook_url, json=payload)
            
            if response.status_code in (200, 201, 202, 204):
                logger.info(f"Webhook sent successfully for thread {thread_id}: status={response.status_code}")
                return True
            else:
                logger.warning(
                    f"Webhook returned non-success status for thread {thread_id}: "
                    f"status={response.status_code}, response={response.text[:200]}"
                )
                return False
                
    except httpx.TimeoutException:
        logger.error(f"Webhook timeout for thread {thread_id}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Webhook request error for thread {thread_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected webhook error for thread {thread_id}: {e}")
        return False
