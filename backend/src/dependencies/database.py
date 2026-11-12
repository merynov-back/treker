from typing import Generator
from sqlalchemy.orm import Session
from src.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
