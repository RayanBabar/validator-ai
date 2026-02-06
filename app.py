# Application entry point for Docker
# Re-exports the FastAPI app from src.api.server
import src.config.warnings  # Configure warning suppressions first
from src.api.server import app
