from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .agent.pipeline import run_intel_collection
from .config import get_settings
from .database import SessionLocal

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job() -> None:
    db = SessionLocal()
    try:
        logger.info("定时采集任务开始执行")
        run_intel_collection(db)
        logger.info("定时采集任务执行完成")
    except Exception:  # noqa: BLE001
        logger.exception("定时采集任务执行失败")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        return None
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _job,
        "interval",
        minutes=settings.collection_interval_minutes,
        id="giftradar-collection",
        next_run_time=None,  # 首次运行由启动流程里的种子采集触发，这里只安排后续周期
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("采集调度器已启动，间隔 %s 分钟", settings.collection_interval_minutes)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
