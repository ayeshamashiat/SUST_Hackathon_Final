from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bkash_database_url: str
    nagad_database_url: str
    rocket_database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
