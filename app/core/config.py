from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "AI Platform MVP"

    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = "sk-local-dev"
    llm_model: str = "qwen2.5:3b"
    llm_offline_fallback: bool = True
    llm_timeout_seconds: float = 180.0

    database_url: str = "postgresql://platform:platform@localhost:5432/platform"
    redis_url: str = "redis://localhost:6379/0"

    mssql_dsn: str | None = None
    mssql_query_timeout_seconds: int = 30
    confluence_base_url: str | None = None
    confluence_api_token: str | None = None
    jira_base_url: str | None = None
    jira_api_token: str | None = None
    gitlab_base_url: str | None = None
    gitlab_token: str | None = None


settings = Settings()
