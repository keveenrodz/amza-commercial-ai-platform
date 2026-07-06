from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "amza-commercial-ai-platform"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "sqlite:///./data/amza.db"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    telegram_bot_token: str = ""

    working_memory_size: int = 20
    summary_trigger_messages: int = 30
    summarization_model: str = "openai/gpt-4.1-nano"


settings = Settings()
