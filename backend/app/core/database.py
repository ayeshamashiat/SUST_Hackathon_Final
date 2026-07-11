from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    from app import models  # noqa: F401  (ensure models are registered)

    SQLModel.metadata.create_all(engine)
    # SQLite has no automatic ALTER support in SQLModel's create_all(). Keep
    # existing local demo databases usable while adding Banglish narration.
    columns = {column["name"] for column in inspect(engine).get_columns("alert")}
    if "message_banglish" not in columns:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE "alert" ADD COLUMN message_banglish TEXT NOT NULL DEFAULT \'\''))
    transaction_columns = {column["name"] for column in inspect(engine).get_columns("transaction")}
    if "is_injected_anomaly" not in transaction_columns:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE "transaction" ADD COLUMN is_injected_anomaly BOOLEAN NOT NULL DEFAULT 0'))


def get_session():
    with Session(engine) as session:
        yield session


def session_scope() -> Session:
    """For use outside of FastAPI's DI (background tasks, scripts)."""
    return Session(engine)
