from app.db import get_nagad_db
from app.routers.factory import build_provider_router

router = build_provider_router("nagad", get_nagad_db)
