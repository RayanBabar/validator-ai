from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core API Keys
    DATABASE_URL: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    # Paid API keys
    OPENROUTER_API_KEY: str  # OpenRouter key — routes to Baidu Qianfan by default

    # Optional API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    
    # Supabase Settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Webhook Configuration
    WEBHOOK_URL: Optional[str] = None

    # LangSmith Tracing (Optional)
    LANGSMITH_TRACING: Optional[bool] = None
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "ai-startup-validation"

    # Production Settings
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "*"
    RATE_LIMIT_PER_MINUTE: int = 60

    # Loads from .env file in project root
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
