"""CLI for the shared transactional workspace purge (dry run by default)."""

import argparse
import json

from app.config import get_settings
from app.db import Database
from app.workspaces.purge import purge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_ids", nargs="+")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    database = Database(get_settings().database_url)
    with database.session_factory() as db:
        print(json.dumps(purge(db, args.workspace_ids, args.apply), indent=2))


if __name__ == "__main__":
    main()
