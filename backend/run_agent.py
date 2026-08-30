#!/usr/bin/env python3
"""命令行手动触发一次采集，便于本地调试或用 cron / GitHub Actions 定时调用。

用法:
    python run_agent.py                 # 采集全部（价格+活动+社媒）
    python run_agent.py --scope price   # 只采集价格
    python run_agent.py --country NG    # 只采集尼日利亚
"""
from __future__ import annotations

import argparse
import sys

from app import models
from app.agent.pipeline import (
    run_activity_collection,
    run_all_collections,
    run_price_collection,
    run_social_collection,
)
from app.database import SessionLocal, init_db
from app.seed import run_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="GiftRadar 采集 Agent 手动触发器")
    parser.add_argument("--scope", choices=["price", "activity", "social", "all"], default="all")
    parser.add_argument("--country", default=None, help="国家代码，例如 NG / GH / CM，不填则处理所有国家")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
        platform_ids = None
        if args.country:
            platform_ids = [
                p.id
                for p in db.query(models.Platform)
                .join(models.Country)
                .filter(models.Country.code == args.country.upper())
                .all()
            ]
            if not platform_ids:
                print(f"未找到国家代码 {args.country} 对应的平台", file=sys.stderr)
                return 1

        if args.scope == "price":
            runs = [run_price_collection(db, platform_ids)]
        elif args.scope == "activity":
            runs = [run_activity_collection(db, platform_ids)]
        elif args.scope == "social":
            runs = [run_social_collection(db, platform_ids)]
        else:
            runs = run_all_collections(db, platform_ids)

        for run in runs:
            print(
                f"[{run.scope}] mode={run.mode} status={run.status} "
                f"targets={run.targets_processed} records={run.records_created}"
            )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
