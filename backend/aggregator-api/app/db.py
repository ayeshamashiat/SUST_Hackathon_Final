from sqlalchemy import create_engine
from sqlmodel import Session

from app.config import settings

# shared_service is a SELECT-only Postgres role (see
# db-init/init-databases.sh) - this engine physically cannot write to
# shared_db, and there is no provider database credential anywhere in this
# service. "Aggregator must never query provider databases" is therefore
# not just a coding convention here; there is no connection string to do it
# with even if a bug tried to.

engine = create_engine(settings.shared_database_url)


def get_shared_db():
    with Session(engine) as session:
        yield session


def shared_session() -> Session:
    """For use outside FastAPI's DI (e.g. a future offline evaluation script)."""
    return Session(engine)
