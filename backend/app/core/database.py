from sqlmodel import SQLModel, Session, create_engine

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    from app import models  # noqa: F401  (ensure models are registered)

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def session_scope() -> Session:
    """For use outside of FastAPI's DI (background tasks, scripts)."""
    return Session(engine)
