
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from libs.models.User import User
from pydantic import BaseModel, Field

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

AuthRouter = APIRouter(
  prefix="/user",
  tags=["auth"], 
)

class UserRegistrationRequest(BaseModel):
  username: str
  email: str
  password: str = Field(..., min_length=8, max_length=128)


@AuthRouter.post("/register", response_model=User)
async def register_user(user_data: UserRegistrationRequest) -> User:
  return User(
    username=user_data.username,
    email=user_data.email,
    first_name=None,
    last_name=None
  )


class UserLoginRequest(BaseModel):
  username: str
  password: str = Field(..., min_length=8, max_length=128)

@AuthRouter.post("/login", response_model=User)
async def login_user(user_data: UserLoginRequest) -> User:
  # In a real application, you would verify the username and password here
  # For now, we will just return a dummy user object
  if user_data.username == "testuser" and user_data.password == "testpassword":
    return User(
      username=user_data.username,
      email="jdlsaksakdl@email.com",
      first_name="dsadad",
      last_name="weqadasfa"
    )
  else:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  

@AuthRouter.get("/", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # In a real application, you would decode the token and get the user information
    # For now, we will just return a dummy user object
    return User(
        username="testuser",
        email="jdlsaksakdl@email.com",
        first_name="adsadas",
        last_name="Vasqdasdauez"
    )