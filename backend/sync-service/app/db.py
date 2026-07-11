from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.config import settings

# sync-service uses its OWN Postgres role (sync_service) for every
# connection here - never provider-api's bkash_service/nagad_service/
# rocket_service credentials. That role is read-only against the three
# provider databases and the sole writer of shared_db (see
# db-init/init-databases.sh) - so even if this service were compromised, it
# cannot corrupt provider data, and no other service can write shared_db.

bkash_engine = create_engine(settings.sync_bkash_database_url)
nagad_engine = create_engine(settings.sync_nagad_database_url)
rocket_engine = create_engine(settings.sync_rocket_database_url)
shared_engine = create_engine(settings.sync_shared_database_url)

PROVIDER_ENGINES = {"bkash": bkash_engine, "nagad": nagad_engine, "rocket": rocket_engine}


def init_shared_schema() -> None:
    """Creates ONLY this service's own shared_db tables - never a provider
    engine (provider-api owns that schema) and never the whole global
    SQLModel metadata (which would also include provider_models.py's
    Balance/Transaction, registered in the same process)."""
    from app.models import ProviderBalance, SyncState, TransactionProjection

    SQLModel.metadata.create_all(
        shared_engine,
        tables=[ProviderBalance.__table__, TransactionProjection.__table__, SyncState.__table__],
    )


def provider_session(provider: str) -> Session:
    return Session(PROVIDER_ENGINES[provider])


def shared_session() -> Session:
    return Session(shared_engine)
