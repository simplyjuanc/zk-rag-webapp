from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from apps.api.routes.auth import AuthRouter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Juan's Personal Librarian",
        description="A personal knowledge management system for Juan and his notes.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(AuthRouter)

    return app


app = create_app()
