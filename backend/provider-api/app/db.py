from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.config import settings

# Three fully independent engines/sessions - one per provider. There is no
# shared engine or session factory here on purpose: a router for one
# provider only ever has access to its own SessionLocal, so it has no way to
# construct a query against another provider's database even by mistake.

bkash_engine = create_engine(settings.bkash_database_url)
nagad_engine = create_engine(settings.nagad_database_url)
rocket_engine = create_engine(settings.rocket_database_url)

_ENGINES = {"bkash": bkash_engine, "nagad": nagad_engine, "rocket": rocket_engine}


def init_db() -> None:
    from app import models  # noqa: F401  (ensure models are registered)

    for engine in _ENGINES.values():
        SQLModel.metadata.create_all(engine)


def get_bkash_db():
    with Session(bkash_engine) as session:
        yield session


def get_nagad_db():
    with Session(nagad_engine) as session:
        yield session


def get_rocket_db():
    with Session(rocket_engine) as session:
        yield session


def session_for(provider: str) -> Session:
    """For use outside of FastAPI's DI (seed script, background tasks)."""
    return Session(_ENGINES[provider])
