from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import validation
from src.api.middleware import setup_middleware
from src.graph.workflow import init_checkpointer, close_checkpointer
from src.config.settings import settings
from dotenv import load_dotenv
import sys
import asyncio
import logging

# Fix for Psycopg 3 on Windows (ProactorEventLoop not supported)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle for the app."""
    # Startup: Initialize PostgreSQL checkpointer
    logger.info(
        f"Starting AI Startup Validation API | Environment: {settings.ENVIRONMENT}"
    )
    await init_checkpointer()
    yield
    # Shutdown: Close connection pool
    logger.info("Shutting down API...")
    await close_checkpointer()


app = FastAPI(
    lifespan=lifespan,
    title="AI Startup Validation API",
    description="AI-powered startup idea validation platform",
    version="1.0.0",
)

# ===========================================
# CORS Configuration (from settings)
# ===========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# Production Middleware (rate limiting, logging, error handling)
# ===========================================
setup_middleware(app)

# ===========================================
# Routes
# ===========================================
app.include_router(validation)


# ===========================================
# Health Check Endpoint
# ===========================================
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    Returns API status, environment info, and external service metrics.
    """
    from src.utils.health_monitor import health_monitor
    
    service_metrics = await health_monitor.get_metrics()
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "services": service_metrics,
    }
