"""Create only the operator's local account and empty workspace; never seed media."""

import json
import os

from app.local_runtime import create_local_account
from app.main import app


def main():
    with app.state.database.session_factory() as db:
        result = create_local_account(
            db,
            app.state.settings,
            os.environ.get("LOCAL_ACCOUNT_EMAIL", ""),
            os.environ.get("LOCAL_ACCOUNT_PASSWORD", ""),
            os.environ.get("LOCAL_ACCOUNT_NAME", "Cuenta local"),
        )
        db.commit()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
