from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://taskpilot:taskpilot@localhost:5432/taskpilot"
    redis_url: str = "redis://localhost:6379"
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    e2b_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
