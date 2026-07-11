import importlib


def test_database_url_prefers_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://shared_service:shared_pw@localhost:5433/shared_db")

    import app.core.config as config

    importlib.reload(config)

    assert config.DATABASE_URL == "postgresql://shared_service:shared_pw@localhost:5433/shared_db"
