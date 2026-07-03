import structlog
from fastapi import FastAPI

logger = structlog.get_logger()


def register_lifecycle_events(app: FastAPI) -> None:
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("application.started")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("application.stopped")
