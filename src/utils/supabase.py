import httpx
import logging
from typing import Optional, Dict, Any
from src.config.settings import settings

logger = logging.getLogger(__name__)

async def get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("Supabase credentials missing in environment")
    
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }
    return httpx.AsyncClient(base_url=settings.SUPABASE_URL, headers=headers, timeout=10.0)

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile from public.profiles table."""
    try:
        async with await get_supabase_client() as client:
            response = await client.get(f"/rest/v1/profiles?id=eq.{user_id}&select=*")
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
    except Exception as e:
        logger.error(f"Error fetching user profile for {user_id}: {e}")
        return None

async def update_user_tier(user_id: str, tier: str) -> bool:
    """Update user tier in public.profiles table."""
    try:
        async with await get_supabase_client() as client:
            response = await client.patch(
                f"/rest/v1/profiles?id=eq.{user_id}",
                json={"tier": tier}
            )
            return response.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Error updating user tier for {user_id}: {e}")
        return False

async def is_user_admin(user_id: str) -> bool:
    """Check if user has admin privileges."""
    profile = await get_user_profile(user_id)
    return profile.get("is_admin", False) if profile else False

async def update_session_status(thread_id: str, status: str) -> bool:
    """Update session status in validation_sessions table."""
    try:
        async with await get_supabase_client() as client:
            response = await client.patch(
                f"/rest/v1/validation_sessions?thread_id=eq.{thread_id}",
                json={"status": status}
            )
            return response.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Error updating session status for {thread_id}: {e}")
        return False


async def update_session_tier(thread_id: str, tier: str) -> bool:
    """Update session tier in validation_sessions table."""
    try:
        async with await get_supabase_client() as client:
            response = await client.patch(
                f"/rest/v1/validation_sessions?thread_id=eq.{thread_id}",
                json={"tier": tier}
            )
            return response.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Error updating session tier for {thread_id}: {e}")
        return False


async def get_report_from_db(thread_id: str, tier: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch report data from reports table, optionally filtered by tier."""
    try:
        url = f"/rest/v1/reports?thread_id=eq.{thread_id}"
        if tier:
            url += f"&tier=eq.{tier}"
        url += "&select=*"
        
        async with await get_supabase_client() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
    except Exception as e:
        logger.error(f"Error fetching report from DB for {thread_id}: {e}")
        return None


async def get_all_reports_for_thread(thread_id: str) -> list[Dict[str, Any]]:
    """Fetch all reports for a given thread_id."""
    try:
        async with await get_supabase_client() as client:
            response = await client.get(f"/rest/v1/reports?thread_id=eq.{thread_id}&select=*")
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        logger.error(f"Error fetching all reports for {thread_id}: {e}")
        return []
