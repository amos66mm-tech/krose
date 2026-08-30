#!/usr/bin/env python3
"""命令行手动触发一次情报采集。

用法:
    python run_agent.py                      # 全量宽网
    python run_agent.py --scope rates        # 只跑行情网
    python run_agent.py --country NG         # 只处理尼日利亚相关网
"""
from __future__ import annotations

import argparse
import sys

from app.agent.pipeline import run_intel_collection
from app.database import SessionLocal, init_db
from app.seed import run_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="GiftRadar 情报采集")
    parser.add_argument(
        "--scope",
        choices=["intel", "rates", "community", "news_risk", "competitor_discovery", "platform_watch", "market_scan", "all"],
        default="intel",
    )
    parser.add_argument("--country", default=None, help="国家代码，例如 NG / GH / CM")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
        stream = "intel" if args.scope == "all" else args.scope
        run = run_intel_collection(db, country_code=args.country, stream=stream)
        print(
            f"[{run.scope}] mode={run.mode} status={run.status} "
            f"targets={run.targets_processed} records={run.records_created}"
        )
        if run.error_message:
            print(run.error_message, file=sys.stderr)
        return 0 if run.status != "failed" else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
