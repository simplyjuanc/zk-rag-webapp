from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from fastapi import Depends
from sqlalchemy.orm import Session

from libs.storage.db import get_db_session
from libs.storage.models.user import User as DaoUser
from libs.models.User import User


class UserRepository:
    def __init__(self, session: Session = Depends(get_db_session)):
        """
        Accepts a SQLAlchemy session (usually scoped per request).
        """
        self.session = session

    def create_user(self, user: DaoUser) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self.__map_to_model(user)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = self.session.query(DaoUser).filter(DaoUser.id == user_id).first()
        return self.__map_to_model(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        user = self.session.query(DaoUser).filter(DaoUser.email == email).first()
        return self.__map_to_model(user) if user else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        user = self.session.query(DaoUser).filter(DaoUser.username == username).first()
        return self.__map_to_model(user) if user else None

    def __map_to_model(self, user: DaoUser) -> User:
        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
