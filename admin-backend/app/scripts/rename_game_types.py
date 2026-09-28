"""Renames the "Single" and "Jodi" game type display names to "Single Digit"
and "Jodi Digit" on an existing database. `seed_games.py` is get-or-create by
code, so it never touches the `name` of a row that already exists -- this
one-off fixes that for databases seeded before the rename. Idempotent: safe
to run any number of times. Run with:

    python -m app.scripts.rename_game_types
"""
from __future__ import annotations

from app.db.base import SessionLocal
from app.models.game_type import GameType

RENAMES = {
    "SINGLE": "Single Digit",
    "JODI": "Jodi Digit",
}


def run() -> None:
    db = SessionLocal()
    try:
        for code, new_name in RENAMES.items():
            game_type = db.query(GameType).filter_by(code=code).first()
            if not game_type:
                continue
            if game_type.name == new_name:
                continue
            print(f"  {code}: {game_type.name!r} -> {new_name!r}")
            game_type.name = new_name
        db.commit()
        print("Game type rename complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
