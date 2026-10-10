import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vivagrade.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
