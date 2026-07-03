from fastapi import FastAPI

from app.config import settings
from app.exceptions import register_exception_handlers
from app.lifecycle import register_lifecycle_events
from app.logging import configure_logging


def create_application() -> FastAPI:
    configure_logging(debug=settings.debug)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    register_lifecycle_events(application)
    register_exception_handlers(application)

    return application


app = create_application()
