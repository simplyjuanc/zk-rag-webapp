from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from uuid import uuid4
from fastapi import Depends
from sqlalchemy.orm import Session

from libs.storage.db import get_db_session
from libs.storage.models.user import User as DaoUser, UserStatus
from libs.models.User import UserCreateRequest, RegisteredUser, BaseUser


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, create_user_request: UserCreateRequest) -> RegisteredUser:
        mapped_new_user = self.__map_to_dao_user(create_user_request)
        self.session.add(mapped_new_user)
        self.session.commit()
        created_user = self.get_user_by_id(mapped_new_user.id)
        if not created_user:
            raise ValueError("Failed to create user")
        return created_user

    def get_user_by_id(self, user_id: str) -> Optional[RegisteredUser]:
        user = self.session.query(DaoUser).filter(DaoUser.id == user_id).first()
        return self.__map_to_model(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[RegisteredUser]:
        user = self.session.query(DaoUser).filter(DaoUser.email == email).first()
        return self.__map_to_model(user) if user else None

    def __map_to_model(self, user: DaoUser) -> RegisteredUser:
        return RegisteredUser(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    def __map_to_dao_user(self, user: UserCreateRequest) -> DaoUser:
        user_id = getattr(user, "id", None) or uuid4().hex
        return DaoUser(
            id=user_id,
            email=user.email,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
            status=UserStatus.UNVERIFIED,
        )


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)
