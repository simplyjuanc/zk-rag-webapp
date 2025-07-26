from collections.abc import AsyncGenerator
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager

from apps.backend.api.health import HealthRouter
from apps.backend.api.v1.auth import AuthRouter
from apps.backend.api.webhooks import WebhooksRouter
from libs.storage.db import init_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
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
