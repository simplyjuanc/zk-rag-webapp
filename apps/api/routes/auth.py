from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from passlib.context import CryptContext

from libs.models.User import RegisteredUser, UserCreateRequest
from libs.storage.repositories.user import UserRepository, get_user_repository

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


class Token(BaseModel):
    token_type: str
    access_token: str


AuthRouter = APIRouter(
    prefix="/user",
    tags=["auth"],
)

user_repo = Annotated[UserRepository, Depends(get_user_repository)]


@AuthRouter.post("/register", response_model=RegisteredUser)
async def register_user(
    user_data: UserCreateRequest,
    user_repository: user_repo,
) -> RegisteredUser:
    existing_user = user_repository.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return user_repository.create_user(user_data)


class UserLoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)


@AuthRouter.post("/login", response_model=RegisteredUser)
async def login_user(
    user_data: UserLoginRequest,
    user_repository: user_repo,
) -> RegisteredUser:
    user = user_repository.get_user_by_email(user_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@AuthRouter.get("/", response_model=RegisteredUser)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    # user_repository: user_repo
) -> RegisteredUser:
    # In a real application, you would decode the token and get the user information
    # For now, we will just return a dummy user object
    return RegisteredUser(
        id="1234567890abcdef",
        email="jdlsaksakdl@email.com",
        first_name="adsadas",
        last_name="Vasqdasdauez",
    )
