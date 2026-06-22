from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from recruitment_agent.api.router import api_router
from recruitment_agent.core.config import get_settings
from recruitment_agent.core.logging import configure_logging
from recruitment_agent.schemas.common import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app.log_level)

    app = FastAPI(title=settings.app.name, debug=settings.app.debug)
    if settings.api.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.api.prefix)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.app.name)

    return app


app = create_app()
