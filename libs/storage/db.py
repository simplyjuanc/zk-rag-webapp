from uuid import uuid4

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from libs.storage.models.base import Base

db = create_engine("sqlite+pysqlite:///:memory:", echo=True, poolclass=StaticPool)

get_db_session = sessionmaker(bind=db)

Base.metadata.create_all(db)
