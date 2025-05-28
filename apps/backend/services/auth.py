from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from libs.models.User import JwtPayload, Token, User, UserCreateRequest
from libs.storage.repositories.user import user_repo_injection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserService:
    def __init__(self, user_repo: user_repo_injection):
        self.user_repo = user_repo

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_access_token(
        self, data: JwtPayload, expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        now = datetime.now()
        expiry = now + expires_delta

        to_encode = {"sub": data, "iat": now, "exp": expiry}

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def authenticate_user(
        self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    ) -> Token:
        user = self.user_repo.get_credentials_by_email(form_data.username)
        if not user or not self.verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return Token(
            token_type="bearer",
            access_token=self.create_access_token(JwtPayload(id=user.email)),
        )

    def get_user_by_id(self, user_id: str) -> User:
        user = self.user_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def get_user_by_email(self, email: str) -> User:
        user = self.user_repo.get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def get_current_user(self, token: str) -> User:
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            payload: JwtPayload = decoded_token.get("sub", None)
            if payload.id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user = self.get_user_by_id(payload.id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def login_user(self, email: str, password: str) -> User:
        user_credentials = self.user_repo.get_credentials_by_email(email)
        if not user_credentials or not self.verify_password(
            password, user_credentials.password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.get_user_by_email(user_credentials.email)

    def create_user(self, user_request: UserCreateRequest) -> User:
        existing_user = self.user_repo.get_user_by_email(user_request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        return self.user_repo.create_user(
            user_request, hashed_password=self.hash_password(user_request.password)
        )


def get_user_service(user_repo: user_repo_injection) -> UserService:
    return UserService(user_repo=user_repo)


user_service_injection = Annotated[UserService, Depends(get_user_service)]
