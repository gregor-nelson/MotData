"""SQLite database connection helper for MOT Insights API."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database path relative to this file's parent directory
DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"

# Fuel type code to name mapping
FUEL_TYPES = {
    "PE": "Petrol",
    "DI": "Diesel",
    "HY": "Hybrid Electric",
    "EL": "Electric",
    "ED": "Plug-in Hybrid",
    "GB": "Gas Bi-fuel",
    "OT": "Other",
}


def dict_factory(cursor, row):
    """Convert SQLite rows to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_db():
    """Context manager for database connections.

    Opens in read-only mode for safety.
    Returns rows as dictionaries.
    """
    conn = sqlite3.connect(f"file:{DATABASE_PATH}?mode=ro", uri=True)
    conn.row_factory = dict_factory
    try:
        yield conn
    finally:
        conn.close()


def get_fuel_name(code: str) -> str:
    """Convert fuel type code to readable name."""
    return FUEL_TYPES.get(code, code)
