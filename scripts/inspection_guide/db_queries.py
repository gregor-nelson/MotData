"""Database queries for inspection guide generation."""

import sqlite3
from pathlib import Path

# Database path (relative to project root)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"


def get_db_connection():
    """Create read-only database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_inspection_guide_data(make: str, model: str) -> dict | None:
    """
    Fetch all data needed for buyer's inspection guide.
    Returns None if no data exists for the model.

    Args:
        make: Vehicle make (e.g., "FORD") - will be uppercased
        model: Vehicle model (e.g., "FOCUS") - will be uppercased

    Returns:
        Dict with keys: make, model, total_tests, top_failures,
        advisories, dangerous_defects, year_pass_rates
        Or None if model not found.
    """
    make = make.upper()
    model = model.upper()

    with get_db_connection() as conn:
        # Get total tests
        cursor = conn.execute("""
            SELECT SUM(total_tests) as total_tests
            FROM vehicle_insights
            WHERE make = ? AND model = ?
        """, (make, model))

        row = cursor.fetchone()
        if not row or row["total_tests"] is None:
            return None

        total_tests = row["total_tests"]

        # Get all failures with percentage and full descriptions
        # JOIN with rfr_descriptions to get human-readable text
        cursor = conn.execute("""
            SELECT
                COALESCE(rd.full_description, td.defect_description) as defect_description,
                td.category_name,
                SUM(td.occurrence_count) as total_occurrences,
                ROUND(SUM(td.occurrence_count) * 100.0 /
                    (SELECT SUM(occurrence_count)
                     FROM top_defects
                     WHERE make = ? AND model = ? AND defect_type = 'failure'), 1) as percentage
            FROM top_defects td
            LEFT JOIN rfr_descriptions rd ON td.rfr_id = rd.rfr_id
            WHERE td.make = ? AND td.model = ? AND td.defect_type = 'failure'
            GROUP BY COALESCE(rd.full_description, td.defect_description), td.category_name
            ORDER BY total_occurrences DESC
        """, (make, model, make, model))

        top_failures = [
            {
                "defect_description": r["defect_description"],
                "category_name": r["category_name"],
                "occurrence_count": r["total_occurrences"],
                "percentage": r["percentage"]
            }
            for r in cursor.fetchall()
        ]

        # Get all advisories with percentage and full descriptions
        cursor = conn.execute("""
            SELECT
                COALESCE(rd.full_description, td.defect_description) as defect_description,
                td.category_name,
                SUM(td.occurrence_count) as total_occurrences,
                ROUND(SUM(td.occurrence_count) * 100.0 /
                    (SELECT SUM(occurrence_count)
                     FROM top_defects
                     WHERE make = ? AND model = ? AND defect_type = 'advisory'), 1) as percentage
            FROM top_defects td
            LEFT JOIN rfr_descriptions rd ON td.rfr_id = rd.rfr_id
            WHERE td.make = ? AND td.model = ? AND td.defect_type = 'advisory'
            GROUP BY COALESCE(rd.full_description, td.defect_description), td.category_name
            ORDER BY total_occurrences DESC
        """, (make, model, make, model))

        advisories = [
            {
                "defect_description": r["defect_description"],
                "category_name": r["category_name"],
                "occurrence_count": r["total_occurrences"],
                "percentage": r["percentage"]
            }
            for r in cursor.fetchall()
        ]

        # Get all dangerous defects with full descriptions
        cursor = conn.execute("""
            SELECT
                COALESCE(rd.full_description, dd.defect_description) as defect_description,
                dd.category_name,
                SUM(dd.occurrence_count) as total_occurrences
            FROM dangerous_defects dd
            LEFT JOIN rfr_descriptions rd ON dd.rfr_id = rd.rfr_id
            WHERE dd.make = ? AND dd.model = ?
            GROUP BY COALESCE(rd.full_description, dd.defect_description), dd.category_name
            ORDER BY total_occurrences DESC
        """, (make, model))

        dangerous_defects = [
            {
                "defect_description": r["defect_description"],
                "category_name": r["category_name"],
                "occurrence_count": r["total_occurrences"]
            }
            for r in cursor.fetchall()
        ]

        # Get year pass rates (sorted by pass_rate DESC, min 100 tests)
        cursor = conn.execute("""
            SELECT
                model_year,
                SUM(total_tests) as total_tests,
                ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
            FROM vehicle_insights
            WHERE make = ? AND model = ?
            GROUP BY model_year
            HAVING total_tests >= 100
            ORDER BY pass_rate DESC
        """, (make, model))

        year_pass_rates = [
            {
                "model_year": r["model_year"],
                "pass_rate": r["pass_rate"],
                "total_tests": r["total_tests"]
            }
            for r in cursor.fetchall()
        ]

        return {
            "make": make,
            "model": model,
            "total_tests": total_tests,
            "top_failures": top_failures,
            "advisories": advisories,
            "dangerous_defects": dangerous_defects,
            "year_pass_rates": year_pass_rates
        }


def get_top_models(limit: int = 100) -> list[dict]:
    """
    Get top N models by total test count.

    Args:
        limit: Number of models to return

    Returns:
        List of dicts with make, model, total_tests
    """
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                make,
                model,
                SUM(total_tests) as total_tests
            FROM vehicle_insights
            GROUP BY make, model
            ORDER BY total_tests DESC
            LIMIT ?
        """, (limit,))

        return [
            {"make": r["make"], "model": r["model"], "total_tests": r["total_tests"]}
            for r in cursor.fetchall()
        ]
