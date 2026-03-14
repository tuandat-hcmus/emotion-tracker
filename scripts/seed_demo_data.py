import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.services.demo_seed_service import (
    DEFAULT_DEMO_EMAIL,
    DEFAULT_DEMO_PASSWORD,
    reset_demo_data,
    seed_demo_data,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed deterministic demo data for local/manual testing.")
    parser.add_argument("--days", type=int, default=30, help="How many days of demo history to create.")
    parser.add_argument("--email", default=DEFAULT_DEMO_EMAIL, help="Demo login email.")
    parser.add_argument("--password", default=DEFAULT_DEMO_PASSWORD, help="Demo login password.")
    parser.add_argument("--reset", action="store_true", help="Reset the demo user before seeding.")
    parser.add_argument("--reset-only", action="store_true", help="Delete the demo user/data and exit.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset_only:
            removed_user = reset_demo_data(db, args.email)
            print(f"removed_user={removed_user} email={args.email.lower()}")
            return

        if args.reset:
            reset_demo_data(db, args.email)

        result = seed_demo_data(
            db,
            days=args.days,
            email=args.email,
            password=args.password,
            reset=args.reset,
        )
        print(
            "seeded "
            f"user_id={result.user_id} "
            f"email={result.email} "
            f"days={result.days} "
            f"entry_count={result.entry_count} "
            f"weekly_wrapup_id={result.weekly_wrapup_id} "
            f"monthly_wrapup_id={result.monthly_wrapup_id}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
