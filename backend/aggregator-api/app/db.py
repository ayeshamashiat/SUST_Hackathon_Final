from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.config import settings

# Two separate engines, two separate roles, two separate purposes:
#
# - shared_engine (shared_service, SELECT-only): the provider-sync
#   projection. "Aggregator must never query provider databases" is not
#   just a coding convention here - there is no provider DB connection
#   string anywhere in this service, and this engine's own role cannot
#   write even to shared_db itself.
# - aggregator_engine (aggregator_service, full read-write): aggregator-api's
#   OWN data - users, alerts, cases - none of which is provider-sync
#   projection data, so it lives in a database aggregator-api actually owns
#   rather than needing an exception to shared_db's read-only rule.

shared_engine = create_engine(settings.shared_database_url)
aggregator_engine = create_engine(settings.aggregator_database_url)


def get_shared_db():
    with Session(shared_engine) as session:
        yield session


def shared_session() -> Session:
    """For use outside FastAPI's DI (e.g. a future offline evaluation script)."""
    return Session(shared_engine)


def get_aggregator_db():
    with Session(aggregator_engine) as session:
        yield session


def aggregator_session() -> Session:
    return Session(aggregator_engine)


def init_aggregator_schema() -> None:
    """Creates ONLY this service's own aggregator_db tables - never the
    shared engine (that schema belongs to sync-service) and never the whole
    global SQLModel metadata."""
    from app.auth.models import User
    from app.cases.models import Alert, CaseEvent

    SQLModel.metadata.create_all(aggregator_engine, tables=[User.__table__, Alert.__table__, CaseEvent.__table__])
