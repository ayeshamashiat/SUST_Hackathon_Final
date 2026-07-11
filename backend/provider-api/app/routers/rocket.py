from app.db import get_rocket_db
from app.routers.factory import build_provider_router

router = build_provider_router("rocket", get_rocket_db)
