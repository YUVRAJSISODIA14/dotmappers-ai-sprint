"""
data.py — Loads support_tickets.csv into a local SQLite database.

Run this file directly once to build data/tickets.db:
    python -m app.data
"""

import sqlite3
from pathlib import Path
import pandas as pd

# Paths are relative to the project root, not this file, so this works
# no matter which folder you happen to run commands from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "support_tickets.csv"
DB_PATH = PROJECT_ROOT / "data" / "tickets.db"


def build_database() -> None:
    """Reads the CSV and (re)creates data/tickets.db from scratch."""
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("tickets", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Loaded {len(df)} rows into {DB_PATH}")


def get_connection() -> sqlite3.Connection:
    """Opens a fresh connection to the tickets database, building it first if needed."""
    if not DB_PATH.exists():
        build_database()
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    build_database()