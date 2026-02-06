"""
API package - FastAPI routes and middleware.
"""
from src.api.server import app
from src.api.routes import validation

__all__ = ["app", "validation"]
