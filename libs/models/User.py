from typing import Annotated, Optional
from uuid import uuid4
from pydantic import BaseModel, EmailStr, Field

from libs.storage.models.user import UserStatus


class BaseUser(BaseModel):
    email: EmailStr
    first_name: Annotated[Optional[str], Field(default=None)]
    last_name: Annotated[Optional[str], Field(default=None)]


class UserCreateRequest(BaseUser):
    password: Annotated[str, Field(..., min_length=8, max_length=128)]


class User(BaseUser):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    status: Annotated[
        str,
        Field(
            default="unverified",
            examples=["unverified", "active", "inactive"],
            description="User's account status",
        ),
    ] = UserStatus.UNVERIFIED


class Token(BaseModel):
    token_type: str
    access_token: str


class JwtPayload(BaseModel):
    id: str
