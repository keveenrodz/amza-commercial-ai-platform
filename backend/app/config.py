from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env vive en la raíz del repo, no en backend/. Resuelto contra este archivo (no contra el cwd)
# para que funcione igual con `cd backend && python main.py` que desde cualquier otro directorio.
# Docker Compose no depende de esto: inyecta las variables directamente vía `env_file:`.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "amza-commercial-ai-platform"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "sqlite:///./data/amza.db"

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_path(cls, v: str) -> str:
        # Mismo problema que _ENV_FILE arriba: una ruta sqlite relativa ("./data/amza.db")
        # depende del cwd en el momento de ejecutar, no de dónde vive el proyecto. Se resuelve
        # contra backend/ sin importar si el valor viene del default, de .env o de una variable
        # de entorno real. URLs no-sqlite (Postgres en producción) pasan sin tocar.
        prefix = "sqlite:///"
        if v.startswith(prefix):
            path = v.removeprefix(prefix)
            if not path.startswith("/"):
                return f"{prefix}{(_BACKEND_DIR / path).resolve()}"
        return v

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    working_memory_size: int = 20
    summary_trigger_messages: int = 30
    summarization_model: str = "openai/gpt-4.1-nano"

    google_client_id: str = ""
    google_client_secret: str = ""
    # Debe coincidir exactamente con el redirect URI registrado en Google Cloud Console. Cambia
    # cada vez que cambia la URL pública de desarrollo (ngrok) -- mismo patrón que el webhook de
    # Telegram, no hay forma de evitarlo sin un dominio fijo.
    google_redirect_uri: str = ""

    jwt_secret: str = ""
    jwt_ttl_hours: int = 24


settings = Settings()
