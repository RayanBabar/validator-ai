"""
Webhook utilities for sending report data to external systems.
"""

import logging
import httpx
import json
import os
from typing import Dict, Any
from src.config import settings

logger = logging.getLogger(__name__)

# Supabase Edge Function URL for report webhook
# REQUIRED: Set WEBHOOK_URL in .env file
WEBHOOK_BASE_URL = settings.WEBHOOK_URL
if not WEBHOOK_BASE_URL:
    raise ValueError("WEBHOOK_URL environment variable is required")
WEBHOOK_TIMEOUT = 30.0  # seconds


async def init_thread_supabase(thread_id: str) -> bool:
    """
    Initialize the thread in Supabase to avoid FK constraint errors.
    POST {SUPABASE_URL}/rest/v1/threads
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.warning("Supabase credentials missing. Skipping thread initialization.")
        return False

    supabase_url = f"{settings.SUPABASE_URL}/rest/v1/validation_sessions"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    # Only try to create if it doesn't exist, though it should always exist
    payload = {"thread_id": thread_id}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First check if it exists
            check_url = f"{supabase_url}?thread_id=eq.{thread_id}"
            check_res = await client.get(check_url, headers=headers)
            if check_res.status_code == 200 and len(check_res.json()) > 0:
                logger.info(f"Thread {thread_id} already exists in validation_sessions")
                return True

            # If not, try to create it (though this shouldn't happen in normal flow)
            response = await client.post(supabase_url, json=payload, headers=headers)
            if response.status_code in (200, 201, 204):
                logger.info(f"Thread {thread_id} initialized in validation_sessions")
                return True
            else:
                logger.error(f"Failed to initialize thread {thread_id} in validation_sessions: {response.status_code} {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error initializing thread in Supabase: {e}")
        return False


async def send_report_webhook(
    thread_id: str,
    report_score: float,
    report_metadata: Dict[str, Any],
) -> bool:
    """
    Send report data to the external webhook endpoint.
    
    PUT {WEBHOOK_BASE_URL}/{thread_id}
    
    Args:
        thread_id: The unique thread identifier for this validation journey
        report_score: The viability or go/no-go score from the report
        report_metadata: Additional metadata about the report (tier, title, etc.)
        
    Returns:
        True if webhook was sent successfully, False otherwise
    """
    # 1. Ensure thread exists in Supabase first
    await init_thread_supabase(thread_id)

    # 2. Send the actual report webhook
    webhook_url = f"{WEBHOOK_BASE_URL}/{thread_id}"
    
    # User requested payload format: report_score (str), report_metadata (str)
    # Metadata should be a JSON string
    
    payload = {
        "report_score": str(report_score),
        "tier": report_metadata.get("tier", "free"),
        "report_metadata": json.dumps(report_metadata),
    }
    
    # Log the payload for debugging
    logger.info(f"Sending webhook payload for thread {thread_id}")

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
