from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core API Keys
    DATABASE_URL: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    # Optional API Keys
    ANTHROPIC_API_KEY: Optional[str] = None

    # LangSmith Tracing (Optional)
    LANGSMITH_TRACING: Optional[bool] = None
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "validator-ai"

    # Production Settings
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "*"
    RATE_LIMIT_PER_MINUTE: int = 60

    # 🚀 IMPORTANT: Docker envs only (no .env loading here)
    model_config = SettingsConfigDict()

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
