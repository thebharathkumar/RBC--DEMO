"""FastAPI entrypoint.

The application is intentionally thin at this milestone: meta endpoints, a
metrics endpoint, request-id middleware, CORS, and JSON error handlers. Agent
routes are wired up in later milestones.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from src import __version__
from src.config import get_settings
from src.observability.logging import RequestContextMiddleware, configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    log = structlog.get_logger(__name__)
    log.info(
        "api.startup",
        env=settings.app_env,
        port=settings.app_port,
        version=settings.app_version,
    )
    try:
        yield
    finally:
        log.info("api.shutdown")


def _install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"type": "http_error", "message": exc.detail}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "request payload failed validation",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces over the wire. The structured log carries
        # the traceback because structlog has ``dict_tracebacks`` configured.
        structlog.get_logger(__name__).exception("api.unhandled_exception")
        return JSONResponse(
            status_code=500,
            content={"error": {"type": "internal_error", "message": "internal error"}},
        )


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="rbc-research-agent-platform",
        version=__version__,
        summary="Hierarchical multi-agent equity research synthesis platform.",
        contact={
            "name": "Bharath Kumar Rajesh",
            "email": "bharath.kr702@gmail.com",
            "url": "https://thebharath.co",
        },
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["authorization", "content-type", "x-request-id"],
            allow_credentials=False,
            max_age=600,
        )

    _install_error_handlers(app)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"])
    async def readyz() -> dict[str, str]:
        # Readiness is upgraded in milestone 2 once data adapters exist; for
        # now liveness and readiness coincide.
        return {"status": "ok"}

    @app.get("/version", tags=["meta"])
    async def version() -> dict[str, str]:
        return {
            "version": __version__,
            "env": settings.app_env,
        }

    @app.get("/metrics", tags=["meta"], response_class=PlainTextResponse)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
