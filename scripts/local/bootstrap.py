"""Prepare public local scenarios transactionally, without importing server data."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.local_seed import enqueue_initial_media, seed_evaluation
from app.main import app
from refresh_local_police import refresh_local_police
from replace_local_hospital import replace_local_hospital


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", action="store_true")
    args = parser.parse_args()
    settings = app.state.settings
    if settings.environment != "local" or not settings.local_evaluation_enabled:
        raise SystemExit(
            "This command requires the isolated local evaluation environment."
        )
    with app.state.database.session_factory() as db:
        if not args.queue:
            replace_local_hospital(db, settings)
            refresh_local_police(db, settings)
        result = (
            enqueue_initial_media(db) if args.queue else seed_evaluation(db, settings)
        )
        db.commit()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
