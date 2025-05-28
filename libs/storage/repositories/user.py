from functools import wraps
from typing import Annotated, Optional
from uuid import uuid4
from fastapi import Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from libs.storage.db import get_db_session
from libs.storage.models.user import User as DaoUser, UserStatus
from libs.models.User import User, BaseUser, UserCreateRequest


class UserCredentials(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(..., min_length=8, max_length=128)]


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, new_user: BaseUser, hashed_password: str) -> User:
        try:
            mapped_new_user = self.__map_to_dao_user(new_user, hashed_password)
            self.session.add(mapped_new_user)
            self.session.commit()
            created_user = self.get_user_by_id(mapped_new_user.id)
            if not created_user:
                raise ValueError("Failed to create user")
            return created_user
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error creating user: {e}")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = self.session.query(DaoUser).filter(DaoUser.id == user_id).first()
        return self.__map_to_model(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        user = self.session.query(DaoUser).filter(DaoUser.email == email).first()
        return self.__map_to_model(user) if user else None

    def get_credentials_by_email(self, email: str) -> UserCredentials:
        user = self.session.query(DaoUser).filter(DaoUser.email == email).first()
        if not user:
            raise ValueError("User not found")
        return UserCredentials(email=user.email, password=user.password)

    def __map_to_model(self, user: DaoUser) -> User:
        return User(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            status=user.status,
        )

    def __map_to_dao_user(self, user: BaseUser, password: str) -> DaoUser:
        user_id = getattr(user, "id", None) or uuid4().hex
        return DaoUser(
            id=user_id,
            email=user.email,
            password=password,
            first_name=user.first_name,
            last_name=user.last_name,
            status=UserStatus.UNVERIFIED,
        )


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


user_repo_injection = Annotated[UserRepository, Depends(get_user_repository)]
