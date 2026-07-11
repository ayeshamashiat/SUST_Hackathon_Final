from app.db import get_bkash_db
from app.routers.factory import build_provider_router

router = build_provider_router("bkash", get_bkash_db)
