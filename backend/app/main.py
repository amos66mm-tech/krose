from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401
from .agent.pipeline import run_all_collections
from .config import get_settings
from .database import SessionLocal, init_db
from .routers import activities, collect, countries, dashboard, ideas, platforms, prices, social
from .scheduler import shutdown_scheduler, start_scheduler
from .seed import run_seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
        has_any_price = db.query(models.PriceQuote).first() is not None
        if not has_any_price:
            logger.info("首次启动，未发现历史数据，触发一次初始采集（%s 模式）", "LIVE" if settings.is_live_mode else "DEMO")
            run_all_collections(db)
    finally:
        db.close()
    start_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    origins = ["*"] if settings.cors_origins == "*" else [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(countries.router)
    app.include_router(platforms.router)
    app.include_router(prices.router)
    app.include_router(activities.router)
    app.include_router(social.router)
    app.include_router(dashboard.router)
    app.include_router(collect.router)
    app.include_router(ideas.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
