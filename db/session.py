from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase
from typing import Generator

from config.settings import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))


def get_session() -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


