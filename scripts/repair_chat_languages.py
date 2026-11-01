"""Repair recognized local assistant replies; preserve originals and never call Meta."""

import argparse
import json

from app.config import get_settings
from app.db import Database
from app.social_features.chat_localization import recognize_template, seed_translations
from app.social_features.models import ChatMessage
from sqlalchemy import select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    count = 0
    database = Database(get_settings().database_url)
    with database.session_factory() as db:
        cursor = 0
        while True:
            messages = list(
                db.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.role == "ai", ChatMessage.id > cursor)
                    .order_by(ChatMessage.id)
                    .limit(100)
                )
            )
            if not messages:
                break
            for message in messages:
                if recognize_template(message.text):
                    count += 1
                    if args.apply:
                        seed_translations(db, message)
            cursor = messages[-1].id
            if args.apply:
                db.commit()
        print(
            json.dumps(
                {
                    "recognized_messages": count,
                    "applied": args.apply,
                    "originals_preserved": True,
                }
            )
        )


if __name__ == "__main__":
    main()
