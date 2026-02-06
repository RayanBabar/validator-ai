"""
Production middleware for the AI Startup Validation API.
Includes: Rate Limiting, Request Logging, Global Exception Handling.
"""

import time
import logging
import traceback
from uuid import uuid4
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config.settings import settings


# ===========================================
# Logging Configuration
# ===========================================

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("api")


# ===========================================
# Rate Limiter Setup
# ===========================================


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key - uses client IP address."""
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        f"Rate limit exceeded | IP: {get_remote_address(request)} | Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "retry_after_seconds": 60,
        },
    )


# ===========================================
# Request Logging Middleware
# ===========================================


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware that logs all incoming requests and outgoing responses.
    Includes request ID for tracing, timing, and status codes.
    """
    # Generate unique request ID for tracing
    request_id = str(uuid4())[:8]
    request.state.request_id = request_id

    # Extract request info
    client_ip = get_remote_address(request)
    method = request.method
    path = request.url.path
    query = str(request.query_params) if request.query_params else ""

    # Log incoming request
    logger.info(
        f"[{request_id}] --> {method} {path} "
        f"| IP: {client_ip} | Query: {query or 'none'}"
    )

    # Process request and time it
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

        # Log outgoing response
        logger.info(
            f"[{request_id}] <-- {method} {path} "
            f"| Status: {response.status_code} | Duration: {process_time:.2f}ms"
        )

        # Add custom headers for debugging
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response

    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"[{request_id}] !!! {method} {path} "
            f"| Error: {str(e)} | Duration: {process_time:.2f}ms"
        )
        raise


# ===========================================
# Global Exception Handler
# ===========================================


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that catches all unhandled exceptions.
    Returns a consistent JSON error response and logs the full traceback.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Log full traceback for debugging
    logger.error(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {str(exc)}\n"
        f"{traceback.format_exc()}"
    )

    # In production, hide internal error details
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
            },
        )
    else:
        # In development, include more details for debugging
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc),
                "exception_type": type(exc).__name__,
                "request_id": request_id,
            },
        )


# ===========================================
# Setup Function
# ===========================================


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all production middleware on the FastAPI app.
    Call this function after creating the FastAPI app instance.
    """
    # Add rate limiter state and exception handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Add global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    # Add logging middleware
    app.middleware("http")(logging_middleware)

    logger.info(
        f"Middleware configured | Environment: {settings.ENVIRONMENT} | "
        f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE}/min"
    )
