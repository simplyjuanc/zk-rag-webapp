from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from passlib.context import CryptContext

from apps.backend.services.auth import user_service_injection
from libs.models.User import User, UserCreateRequest, Token
from libs.storage.repositories.user import user_repo_injection


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

AuthRouter = APIRouter(
    prefix="/v1/user",
    tags=["auth"],
)


class UserLoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)


@AuthRouter.get("/", response_model=User)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: user_service_injection,
) -> User:
    return user_service.get_current_user(token)


@AuthRouter.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreateRequest,
    user_service: user_service_injection,
) -> User:
    return user_service.create_user(user_data)


@AuthRouter.post("/login", response_model=User)
async def login_user(
    login_request: UserLoginRequest,
    user_service: user_service_injection,
) -> User:
    return user_service.login_user(login_request.email, login_request.password)


@AuthRouter.post("/token", response_model=Token, include_in_schema=False)
def authenticate_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: user_service_injection,
) -> Token:
    return user_service.authenticate_user(form_data)
