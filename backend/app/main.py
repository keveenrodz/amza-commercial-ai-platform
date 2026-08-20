from fastapi import FastAPI

from app.api.routers.advisors import router as advisors_router
from app.api.routers.auth import router as auth_router
from app.api.routers.contacts import router as contacts_router
from app.api.routers.health import router as health_router
from app.api.routers.internal_users import router as internal_users_router
from app.api.routers.opportunities import router as opportunities_router
from app.api.routers.telegram_webhook import router as telegram_webhook_router
from app.api.routers.whatsapp_webhook import router as whatsapp_webhook_router
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

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(telegram_webhook_router)
    application.include_router(whatsapp_webhook_router)
    application.include_router(opportunities_router)
    application.include_router(contacts_router)
    application.include_router(advisors_router)
    application.include_router(internal_users_router)

    return application


app = create_application()
