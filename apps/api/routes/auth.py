from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from libs.models.User import User
from libs.storage.models.user import User as RepoUser
from libs.storage.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

AuthRouter = APIRouter(
    prefix="/user",
    tags=["auth"],
)


def get_user_repository() -> UserRepository:
    return UserRepository()


class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str = Field(..., min_length=8, max_length=128)


@AuthRouter.post("/register", response_model=User)
async def register_user(
    user_data: UserRegistrationRequest,
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    return user_repository.create_user(
        RepoUser(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name="",
            last_name="",
        )
    )


class UserLoginRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=8, max_length=128)


@AuthRouter.post("/login", response_model=User)
async def login_user(
    user_data: UserLoginRequest,
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    user = user_repository.get_user_by_username(user_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@AuthRouter.get("/", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # In a real application, you would decode the token and get the user information
    # For now, we will just return a dummy user object
    return User(
        username="testuser",
        email="jdlsaksakdl@email.com",
        first_name="adsadas",
        last_name="Vasqdasdauez",
    )
