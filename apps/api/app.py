from typing import Annotated

from fastapi import Depends, FastAPI
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

    @app.get("/")
    async def get_root(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
        return {"message": "Welcome to Juan's Personal Librarian API"}

    return app


app = create_app()

