import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions.domain import (
    DomainError,
    InternalUserNotFoundError,
    InvalidStatusTransitionError,
    NoActiveAgentError,
    OpportunityAlreadyClosedError,
    OpportunityNotFoundError,
    OrganizationNotFoundError,
    OrganizationSlugNotFoundError,
)

logger = structlog.get_logger()

_NOT_FOUND_ERRORS = (
    OpportunityNotFoundError,
    OrganizationNotFoundError,
    OrganizationSlugNotFoundError,
    InternalUserNotFoundError,
    NoActiveAgentError,
)

_UNPROCESSABLE_ERRORS = (
    InvalidStatusTransitionError,
    OpportunityAlreadyClosedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "unhandled.exception",
            error=str(exc),
            path=str(request.url.path),
            method=request.method,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred."},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        if isinstance(exc, _NOT_FOUND_ERRORS):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        if isinstance(exc, _UNPROCESSABLE_ERRORS):
            return JSONResponse(status_code=422, content={"detail": str(exc)})
        logger.warning(
            "domain.error.unhandled",
            error=str(exc),
            path=str(request.url.path),
        )
        return JSONResponse(status_code=400, content={"detail": str(exc)})
