import os

from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime settings for the local development backend."""

    app_name: str = "Insight Agent API"
    api_prefix: str = "/api"
    postgres_uri: str = os.getenv("POSTGRES_URI", "postgresql:///enterprise_data_ai")
    ai_agent_base_url: str = os.getenv("AI_AGENT_BASE_URL", "http://127.0.0.1:8010")
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


settings = Settings()
