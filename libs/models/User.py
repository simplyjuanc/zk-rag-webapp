from uuid import uuid4
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    username: str = Field(..., min_length=3, max_length=50) 
    email: str = Field(...,description="User's email address", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", examples=["john.doe@example.mail"])
    first_name: str | None = None
    last_name: str | None = None


class RegisteredUser(User):
    hashed_password: str
