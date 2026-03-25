"""
Maintenance script for semantic user-memory reindex.

Safe defaults:
- by default reindexes exactly one user by `--telegram-id`
- bulk mode requires explicit `--all-users`
- supports `--dry-run` before real execution
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import init_db
from services import user_memory_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reindex semantic user memory from SQLite into LanceDB.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--telegram-id",
        type=int,
        help="Reindex exactly one Telegram user.",
    )
    target.add_argument(
        "--all-users",
        action="store_true",
        help="Reindex all known users. Use with care.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Batch size for iterating all users in bulk mode.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of users in bulk mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write anything, only show what would be processed.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result.",
    )
    return parser


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args()

    init_db()

    if args.telegram_id is not None:
        if args.dry_run:
            result = {
                "ok": True,
                "dry_run": True,
                "requested": 1,
                "processed": 1,
                "results": [{"telegram_id": args.telegram_id, "message": "dry-run"}],
            }
        else:
            item = user_memory_service.reindex_user_memory(args.telegram_id)
            result = {
                "ok": bool(item.get("ok")),
                "dry_run": False,
                "requested": 1,
                "processed": 1,
                "results": [{"telegram_id": args.telegram_id, **item}],
            }
    else:
        result = user_memory_service.reindex_many_users(
            telegram_ids=None,
            page_size=max(1, args.page_size),
            limit_users=args.limit,
            dry_run=args.dry_run,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    # Work around native finalization crashes observed in pyarrow/LanceDB
    # after successful completion of one-shot maintenance scripts.
    os._exit(exit_code)
