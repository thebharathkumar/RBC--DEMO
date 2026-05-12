"""FastAPI entrypoint.

The application is intentionally thin at this milestone: a health probe, a
metrics endpoint, and the configured logging pipeline. Agent routes are wired
up in later milestones.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.config import get_settings


def _configure_logging(level: str) -> None:
    logging.basicConfig(format="%(message)s", level=level.upper())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings.app_log_level)
    structlog.get_logger(__name__).info("api.startup", env=settings.app_env, port=settings.app_port)
    yield
    structlog.get_logger(__name__).info("api.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="rbc-research-agent-platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"])
    async def readyz() -> dict[str, str]:
        # Readiness is upgraded in milestone 2 once data adapters exist.
        return {"status": "ok"}

    @app.get("/metrics", tags=["meta"], response_class=PlainTextResponse)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
