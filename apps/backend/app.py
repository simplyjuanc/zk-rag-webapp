from collections.abc import AsyncGenerator
import logging

from config import settings
import sentry_sdk
from apps.backend.handler.github_handler import GithubHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager

from apps.backend.api.health import HealthRouter
from apps.backend.api.v1.auth import AuthRouter
from apps.backend.api.webhooks import WebhooksRouter
from libs.storage.db import init_db
from libs.di.container import container

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logging.basicConfig(
    level=logging.WARN, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    container.wire(
        modules=[
            "apps.backend.api.health",
            "apps.backend.api.webhooks",
            "apps.backend.api.v1.auth",
            "apps.backend.handler.github_handler",
            "apps.backend.services.document_service",
            "apps.backend.services.user",
        ]
    )

    # See https://docs.sentry.io/platforms/python/ for general documentation and
    # https://docs.sentry.io/platforms/python/data-management/data-collected/ for info on data collected
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        send_default_pii=True,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
    )

    sentry_sdk.set_level("info")

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Juan's Personal Librarian",
        description="A personal knowledge management system for Juan and his notes.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(AuthRouter)
    app.include_router(HealthRouter)
    app.include_router(WebhooksRouter)

    return app


app = create_app()
