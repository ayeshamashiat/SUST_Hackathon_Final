from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sync_bkash_database_url: str
    sync_nagad_database_url: str
    sync_rocket_database_url: str
    sync_shared_database_url: str
    sync_poll_interval_seconds: int = 10
    sync_stale_after_seconds: float = 60.0

    class Config:
        env_file = ".env"


settings = Settings()
