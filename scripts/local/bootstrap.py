"""Prepare public local scenarios transactionally, without importing server data."""
import argparse
import json

from app.local_seed import enqueue_initial_media, seed_evaluation
from app.main import app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", action="store_true")
    args = parser.parse_args()
    settings = app.state.settings
    if settings.environment != "local" or not settings.local_evaluation_enabled:
        raise SystemExit("This command requires the isolated local evaluation environment.")
    with app.state.database.session_factory() as db:
        result = enqueue_initial_media(db) if args.queue else seed_evaluation(db, settings)
        db.commit()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
