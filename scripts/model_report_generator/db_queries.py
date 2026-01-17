"""
Direct database queries for model report generation.
Replaces HTTP API calls with optimized SQLite queries.
"""

import sqlite3
from pathlib import Path

# Database path (hardcoded for local use)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "source" / "data" / "mot_insights.db"

# Fuel type display names (DVSA codes)
FUEL_NAMES = {
    "PE": "Petrol",
    "DI": "Diesel",
    "HY": "Hybrid Electric",
    "EL": "Electric",
    "ED": "Plug-in Hybrid",
    "GB": "Gas Bi-fuel",
    "GD": "Gas Diesel",
    "LP": "LPG",
    "LN": "LNG",
    "CN": "CNG",
    "FC": "Fuel Cell",
    "ST": "Steam",
    "OT": "Other"
}


def get_fuel_name(code: str) -> str:
    """Convert fuel code to display name."""
    if not code:
        return "Unknown"
    return FUEL_NAMES.get(code.upper(), code)


def get_db_connection():
    """Create read-only database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_variants(conn, make: str, model: str) -> list[dict]:
    """Get list of all year/fuel variants for this model."""
    cursor = conn.execute("""
        SELECT model_year, fuel_type, total_tests
        FROM available_vehicles
        WHERE make = ? AND model = ?
        ORDER BY model_year DESC, fuel_type
    """, (make, model))

    return [dict(row) for row in cursor.fetchall()]


def _get_summary(conn, make: str, model: str) -> dict:
    """Aggregate summary stats across all variants."""
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total_variants,
            SUM(total_tests) as total_tests,
            SUM(total_passes) as total_passes,
            SUM(total_fails) as total_fails,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
            ROUND(SUM(avg_mileage * total_tests) / SUM(total_tests), 0) as avg_mileage,
            ROUND(SUM(avg_age_years * total_tests) / SUM(total_tests), 1) as avg_age_years,
            MIN(model_year) as min_year,
            MAX(model_year) as max_year
        FROM vehicle_insights
        WHERE make = ? AND model = ?
    """, (make, model))

    row = cursor.fetchone()
    if not row or row["total_tests"] is None:
        return {}

    return {
        "total_variants": row["total_variants"],
        "total_tests": row["total_tests"],
        "total_passes": row["total_passes"],
        "total_fails": row["total_fails"],
        "pass_rate": row["pass_rate"] or 0,
        "avg_mileage": row["avg_mileage"],
        "avg_age_years": row["avg_age_years"],
        "year_range": f"{row['min_year']}-{row['max_year']}" if row["min_year"] else "N/A"
    }


def _get_fuel_comparison(conn, make: str, model: str) -> list[dict]:
    """Pass rates grouped by fuel type."""
    cursor = conn.execute("""
        SELECT
            fuel_type,
            COUNT(*) as variants,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate
        FROM vehicle_insights
        WHERE make = ? AND model = ?
        GROUP BY fuel_type
        ORDER BY pass_rate DESC
    """, (make, model))

    result = []
    for row in cursor.fetchall():
        result.append({
            "fuel_type": row["fuel_type"],
            "fuel_type_name": get_fuel_name(row["fuel_type"]),
            "variants": row["variants"],
            "total_tests": row["total_tests"],
            "pass_rate": row["pass_rate"] or 0
        })
    return result


def _get_year_comparison(conn, make: str, model: str) -> list[dict]:
    """Pass rates grouped by model year."""
    cursor = conn.execute("""
        SELECT
            model_year as year,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate
        FROM vehicle_insights
        WHERE make = ? AND model = ?
        GROUP BY model_year
        ORDER BY model_year
    """, (make, model))

    return [{"year": row["year"], "total_tests": row["total_tests"], "pass_rate": row["pass_rate"] or 0}
            for row in cursor.fetchall()]


def _get_best_worst_variants(conn, make: str, model: str) -> tuple[dict | None, dict | None]:
    """Find best and worst performing variants."""
    # Best (highest pass rate, min 100 tests)
    cursor = conn.execute("""
        SELECT model_year, fuel_type, total_tests, pass_rate, avg_mileage
        FROM vehicle_insights
        WHERE make = ? AND model = ? AND total_tests >= 100
        ORDER BY pass_rate DESC, total_tests DESC
        LIMIT 1
    """, (make, model))

    best_row = cursor.fetchone()
    best = None
    if best_row:
        best = {
            "year": best_row["model_year"],
            "fuel_type": best_row["fuel_type"],
            "fuel_type_name": get_fuel_name(best_row["fuel_type"]),
            "total_tests": best_row["total_tests"],
            "pass_rate": best_row["pass_rate"],
            "avg_mileage": best_row["avg_mileage"]
        }

    # Worst (lowest pass rate, min 100 tests)
    cursor = conn.execute("""
        SELECT model_year, fuel_type, total_tests, pass_rate, avg_mileage
        FROM vehicle_insights
        WHERE make = ? AND model = ? AND total_tests >= 100
        ORDER BY pass_rate ASC, total_tests DESC
        LIMIT 1
    """, (make, model))

    worst_row = cursor.fetchone()
    worst = None
    if worst_row:
        worst = {
            "year": worst_row["model_year"],
            "fuel_type": worst_row["fuel_type"],
            "fuel_type_name": get_fuel_name(worst_row["fuel_type"]),
            "total_tests": worst_row["total_tests"],
            "pass_rate": worst_row["pass_rate"],
            "avg_mileage": worst_row["avg_mileage"]
        }

    return best, worst


def _get_aggregated_failures(conn, make: str, model: str) -> dict:
    """Aggregated failure_categories, top_failures, top_advisories, dangerous_defects."""

    # Failure categories (top 10)
    cursor = conn.execute("""
        SELECT
            category_name,
            SUM(failure_count) as failure_count
        FROM failure_categories
        WHERE make = ? AND model = ?
        GROUP BY category_name
        ORDER BY failure_count DESC
        LIMIT 10
    """, (make, model))
    categories = [{"category_name": row["category_name"], "failure_count": row["failure_count"]}
                  for row in cursor.fetchall()]

    # Top failures (top 30)
    cursor = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as occurrence_count
        FROM top_defects
        WHERE make = ? AND model = ? AND defect_type = 'failure'
        GROUP BY defect_description, category_name
        ORDER BY occurrence_count DESC
        LIMIT 30
    """, (make, model))
    failures = [{"defect_description": row["defect_description"],
                 "category_name": row["category_name"],
                 "occurrence_count": row["occurrence_count"]}
                for row in cursor.fetchall()]

    # Top advisories (top 30)
    cursor = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as occurrence_count
        FROM top_defects
        WHERE make = ? AND model = ? AND defect_type = 'advisory'
        GROUP BY defect_description, category_name
        ORDER BY occurrence_count DESC
        LIMIT 30
    """, (make, model))
    advisories = [{"defect_description": row["defect_description"],
                   "category_name": row["category_name"],
                   "occurrence_count": row["occurrence_count"]}
                  for row in cursor.fetchall()]

    # Dangerous defects (top 20)
    cursor = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as occurrence_count
        FROM dangerous_defects
        WHERE make = ? AND model = ?
        GROUP BY defect_description, category_name
        ORDER BY occurrence_count DESC
        LIMIT 20
    """, (make, model))
    dangerous = [{"defect_description": row["defect_description"],
                  "category_name": row["category_name"],
                  "occurrence_count": row["occurrence_count"]}
                 for row in cursor.fetchall()]

    return {
        "categories": categories,
        "failures": failures,
        "advisories": advisories,
        "dangerous": dangerous
    }


def _get_aggregated_mileage_bands(conn, make: str, model: str) -> list[dict]:
    """Mileage bands aggregated across variants."""
    cursor = conn.execute("""
        SELECT
            mileage_band,
            band_order,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate,
            ROUND(SUM(avg_mileage * total_tests) / SUM(total_tests), 0) as avg_mileage
        FROM mileage_bands
        WHERE make = ? AND model = ?
        GROUP BY mileage_band, band_order
        ORDER BY band_order
    """, (make, model))

    return [{"mileage_band": row["mileage_band"],
             "band_order": row["band_order"],
             "total_tests": row["total_tests"],
             "pass_rate": row["pass_rate"] or 0,
             "avg_mileage": row["avg_mileage"]}
            for row in cursor.fetchall()]


def _get_aggregated_rankings(conn, make: str, model: str) -> dict:
    """Best rankings achieved across all variants."""
    # Get best rank for each ranking_type (using subquery approach from plan)
    cursor = conn.execute("""
        SELECT r1.ranking_type, r1.rank, r1.total_in_category, r1.pass_rate
        FROM vehicle_rankings r1
        INNER JOIN (
            SELECT ranking_type, MIN(rank) as best_rank
            FROM vehicle_rankings
            WHERE make = ? AND model = ?
            GROUP BY ranking_type
        ) r2 ON r1.ranking_type = r2.ranking_type AND r1.rank = r2.best_rank
        WHERE r1.make = ? AND r1.model = ?
    """, (make, model, make, model))

    result = {}
    for row in cursor.fetchall():
        rank = row["rank"]
        total = row["total_in_category"]
        percentile = round((1 - rank / total) * 100, 1) if total > 0 else 0
        result[row["ranking_type"]] = {
            "rank": rank,
            "total_in_category": total,
            "pass_rate": row["pass_rate"],
            "percentile": percentile
        }
    return result


def _get_aggregated_severity(conn, make: str, model: str) -> list[dict]:
    """Failure severity breakdown."""
    cursor = conn.execute("""
        SELECT
            severity,
            SUM(failure_count) as failure_count
        FROM failure_severity
        WHERE make = ? AND model = ?
        GROUP BY severity
        ORDER BY
            CASE severity
                WHEN 'dangerous' THEN 1
                WHEN 'major' THEN 2
                WHEN 'minor' THEN 3
            END
    """, (make, model))

    rows = cursor.fetchall()
    total = sum(row["failure_count"] for row in rows)

    result = []
    for row in rows:
        count = row["failure_count"]
        pct = (count / total * 100) if total > 0 else 0
        result.append({
            "severity": row["severity"],
            "failure_count": count,
            "failure_percentage": round(pct, 1)
        })
    return result


def _get_aggregated_first_mot(conn, make: str, model: str) -> list[dict]:
    """First MOT vs subsequent comparison."""
    cursor = conn.execute("""
        SELECT
            mot_type,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate,
            ROUND(SUM(avg_mileage * total_tests) / SUM(total_tests), 0) as avg_mileage,
            ROUND(SUM(avg_defects_per_fail * total_tests) / SUM(total_tests), 2) as avg_defects_per_fail
        FROM first_mot_insights
        WHERE make = ? AND model = ?
        GROUP BY mot_type
    """, (make, model))

    return [{"mot_type": row["mot_type"],
             "total_tests": row["total_tests"],
             "pass_rate": row["pass_rate"] or 0,
             "avg_mileage": row["avg_mileage"],
             "avg_defects_per_fail": row["avg_defects_per_fail"]}
            for row in cursor.fetchall()]


def _get_aggregated_retest(conn, make: str, model: str) -> dict | None:
    """Retest success statistics."""
    cursor = conn.execute("""
        SELECT
            SUM(failed_tests) as failed_tests,
            SUM(retested_within_30_days) as retested_within_30_days,
            SUM(passed_on_retest) as passed_on_retest,
            ROUND(SUM(retested_within_30_days) * 100.0 / NULLIF(SUM(failed_tests), 0), 2) as retest_rate,
            ROUND(SUM(passed_on_retest) * 100.0 / NULLIF(SUM(retested_within_30_days), 0), 2) as retest_success_rate
        FROM retest_success
        WHERE make = ? AND model = ?
    """, (make, model))

    row = cursor.fetchone()
    if not row or row["failed_tests"] is None or row["failed_tests"] == 0:
        return None

    return {
        "failed_tests": row["failed_tests"],
        "retested_within_30_days": row["retested_within_30_days"],
        "passed_on_retest": row["passed_on_retest"],
        "retest_rate": row["retest_rate"] or 0,
        "retest_success_rate": row["retest_success_rate"] or 0
    }


def _get_aggregated_age_bands(conn, make: str, model: str) -> list[dict]:
    """Pass rates by vehicle age. Returns empty list if table doesn't exist."""
    try:
        cursor = conn.execute("""
            SELECT
                age_band,
                band_order,
                SUM(total_tests) as total_tests,
                ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate,
                ROUND(SUM(avg_mileage * total_tests) / SUM(total_tests), 0) as avg_mileage
            FROM age_bands
            WHERE make = ? AND model = ?
            GROUP BY age_band, band_order
            ORDER BY band_order
        """, (make, model))

        return [{"age_band": row["age_band"],
                 "band_order": row["band_order"],
                 "total_tests": row["total_tests"],
                 "pass_rate": row["pass_rate"] or 0,
                 "avg_mileage": row["avg_mileage"]}
                for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def _get_aggregated_geographic(conn, make: str, model: str) -> list[dict]:
    """Pass rates by postcode area."""
    cursor = conn.execute("""
        SELECT
            postcode_area,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate
        FROM geographic_insights
        WHERE make = ? AND model = ?
        GROUP BY postcode_area
        ORDER BY pass_rate DESC
    """, (make, model))

    return [{"postcode_area": row["postcode_area"],
             "total_tests": row["total_tests"],
             "pass_rate": row["pass_rate"] or 0}
            for row in cursor.fetchall()]


def _get_aggregated_seasonal(conn, make: str, model: str) -> list[dict]:
    """Pass rates by month."""
    cursor = conn.execute("""
        SELECT
            month,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate
        FROM seasonal_patterns
        WHERE make = ? AND model = ?
        GROUP BY month
        ORDER BY month
    """, (make, model))

    return [{"month": row["month"],
             "total_tests": row["total_tests"],
             "pass_rate": row["pass_rate"] or 0}
            for row in cursor.fetchall()]


def _get_aggregated_advisory_progression(conn, make: str, model: str) -> list[dict]:
    """Top advisory-to-failure progression risks."""
    cursor = conn.execute("""
        SELECT
            category_name,
            SUM(advisory_count) as advisory_count,
            SUM(progressed_to_failure) as progressed_to_failure,
            ROUND(SUM(progressed_to_failure) * 100.0 / NULLIF(SUM(advisory_count), 0), 2) as progression_rate,
            ROUND(SUM(avg_days_to_failure * progressed_to_failure) / NULLIF(SUM(progressed_to_failure), 0), 0) as avg_days_to_failure,
            ROUND(SUM(avg_miles_to_failure * progressed_to_failure) / NULLIF(SUM(progressed_to_failure), 0), 0) as avg_miles_to_failure
        FROM advisory_progression
        WHERE make = ? AND model = ?
        GROUP BY category_name
        ORDER BY progression_rate DESC
        LIMIT 10
    """, (make, model))

    return [{"advisory_text": row["category_name"],
             "category_name": row["category_name"],
             "advisory_count": row["advisory_count"],
             "progressed_to_failure": row["progressed_to_failure"],
             "progression_rate": row["progression_rate"] or 0,
             "avg_days_to_failure": row["avg_days_to_failure"],
             "avg_miles_to_failure": row["avg_miles_to_failure"]}
            for row in cursor.fetchall()]


def _get_aggregated_component_thresholds(conn, make: str, model: str) -> list[dict]:
    """Component failure thresholds by mileage."""
    cursor = conn.execute("""
        SELECT
            category_name,
            COUNT(*) as variant_count,
            ROUND(AVG(failure_rate_0_30k), 2) as failure_rate_0_30k,
            ROUND(AVG(failure_rate_30_60k), 2) as failure_rate_30_60k,
            ROUND(AVG(failure_rate_60_90k), 2) as failure_rate_60_90k,
            ROUND(AVG(failure_rate_90_120k), 2) as failure_rate_90_120k,
            ROUND(AVG(failure_rate_120_150k), 2) as failure_rate_120_150k,
            ROUND(AVG(failure_rate_150k_plus), 2) as failure_rate_150k_plus
        FROM component_mileage_thresholds
        WHERE make = ? AND model = ?
        GROUP BY category_name
        ORDER BY failure_rate_150k_plus DESC
        LIMIT 10
    """, (make, model))

    result = []
    for row in cursor.fetchall():
        # Calculate approximate average failure mileage based on rate progression
        rates = [
            (15000, row["failure_rate_0_30k"] or 0),
            (45000, row["failure_rate_30_60k"] or 0),
            (75000, row["failure_rate_60_90k"] or 0),
            (105000, row["failure_rate_90_120k"] or 0),
            (135000, row["failure_rate_120_150k"] or 0),
            (175000, row["failure_rate_150k_plus"] or 0),
        ]

        # Weighted average mileage based on failure rates
        total_rate = sum(r[1] for r in rates)
        if total_rate > 0:
            avg_failure_mileage = sum(r[0] * r[1] for r in rates) / total_rate
        else:
            avg_failure_mileage = 0

        result.append({
            "component": row["category_name"],
            "category_name": row["category_name"],
            "avg_failure_mileage": round(avg_failure_mileage, 0),
            "failure_count": row["variant_count"],
            "failure_rate_0_30k": row["failure_rate_0_30k"],
            "failure_rate_30_60k": row["failure_rate_30_60k"],
            "failure_rate_60_90k": row["failure_rate_60_90k"],
            "failure_rate_90_120k": row["failure_rate_90_120k"],
            "failure_rate_120_150k": row["failure_rate_120_150k"],
            "failure_rate_150k_plus": row["failure_rate_150k_plus"]
        })

    # Sort by avg_failure_mileage for display
    result.sort(key=lambda x: x["avg_failure_mileage"])
    return result


def _get_all_variants_data(conn, make: str, model: str) -> list[dict]:
    """Detailed data for each variant (for variants table)."""

    # Core insights - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM vehicle_insights WHERE make = ? AND model = ?
    """, (make, model))
    insights_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        insights_by_key[key] = dict(row)

    # Rankings - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM vehicle_rankings WHERE make = ? AND model = ?
    """, (make, model))
    rankings_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in rankings_by_key:
            rankings_by_key[key] = {}
        rank_type = row["ranking_type"]
        rankings_by_key[key][rank_type] = {
            "rank": row["rank"],
            "total_in_category": row["total_in_category"],
            "pass_rate": row["pass_rate"],
            "percentile": round((1 - row["rank"] / row["total_in_category"]) * 100, 1) if row["total_in_category"] > 0 else 0
        }

    # Mileage bands - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM mileage_bands WHERE make = ? AND model = ?
        ORDER BY band_order
    """, (make, model))
    mileage_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in mileage_by_key:
            mileage_by_key[key] = []
        mileage_by_key[key].append({
            "mileage_band": row["mileage_band"],
            "band_order": row["band_order"],
            "total_tests": row["total_tests"],
            "pass_rate": row["pass_rate"],
            "avg_mileage": row["avg_mileage"]
        })

    # Failure categories - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM failure_categories WHERE make = ? AND model = ?
        ORDER BY failure_count DESC
    """, (make, model))
    categories_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in categories_by_key:
            categories_by_key[key] = []
        categories_by_key[key].append({
            "category_name": row["category_name"],
            "failure_count": row["failure_count"]
        })

    # Top defects - failures - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM top_defects WHERE make = ? AND model = ? AND defect_type = 'failure'
        ORDER BY occurrence_count DESC
    """, (make, model))
    failures_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in failures_by_key:
            failures_by_key[key] = []
        failures_by_key[key].append({
            "defect_description": row["defect_description"],
            "category_name": row["category_name"],
            "occurrence_count": row["occurrence_count"]
        })

    # Top defects - advisories - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM top_defects WHERE make = ? AND model = ? AND defect_type = 'advisory'
        ORDER BY occurrence_count DESC
    """, (make, model))
    advisories_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in advisories_by_key:
            advisories_by_key[key] = []
        advisories_by_key[key].append({
            "defect_description": row["defect_description"],
            "category_name": row["category_name"],
            "occurrence_count": row["occurrence_count"]
        })

    # Dangerous defects - indexed by (year, fuel)
    cursor = conn.execute("""
        SELECT * FROM dangerous_defects WHERE make = ? AND model = ?
        ORDER BY occurrence_count DESC
    """, (make, model))
    dangerous_by_key = {}
    for row in cursor.fetchall():
        key = (row["model_year"], row["fuel_type"])
        if key not in dangerous_by_key:
            dangerous_by_key[key] = []
        dangerous_by_key[key].append({
            "defect_description": row["defect_description"],
            "category_name": row["category_name"],
            "occurrence_count": row["occurrence_count"]
        })

    # Build variant list
    variants = []
    for key, insights in insights_by_key.items():
        year, fuel = key
        tests = insights["total_tests"]
        passes = insights["total_passes"]
        pass_rate = (passes / tests * 100) if tests > 0 else 0

        variants.append({
            "year": year,
            "fuel_type": fuel,
            "fuel_type_name": get_fuel_name(fuel),
            "total_tests": tests,
            "pass_rate": round(pass_rate, 2),
            "avg_mileage": insights.get("avg_mileage"),
            "insights": {
                "total_tests": tests,
                "total_passes": passes,
                "total_fails": insights["total_fails"],
                "pass_rate": insights["pass_rate"],
                "avg_mileage": insights.get("avg_mileage"),
                "avg_age_years": insights.get("avg_age_years"),
            },
            "rankings": rankings_by_key.get(key, {}),
            "mileage_bands": mileage_by_key.get(key, []),
            "failure_categories": categories_by_key.get(key, [])[:10],
            "top_failures": failures_by_key.get(key, [])[:15],
            "top_advisories": advisories_by_key.get(key, [])[:15],
            "dangerous_defects": dangerous_by_key.get(key, [])[:10],
        })

    # Sort by pass rate descending (best first)
    variants.sort(key=lambda x: x["pass_rate"], reverse=True)
    return variants


# =============================================================================
# DISCOVERY FUNCTIONS (for --list and --top features)
# =============================================================================

def get_all_makes() -> list[str]:
    """Get list of all makes in the database."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT make FROM available_vehicles ORDER BY make
        """)
        return [row["make"] for row in cursor.fetchall()]


def get_models_for_make(make: str) -> list[str]:
    """Get list of models for a specific make."""
    make = make.upper()
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT model FROM available_vehicles
            WHERE make = ?
            ORDER BY model
        """, (make,))
        return [row["model"] for row in cursor.fetchall()]


def get_top_models(limit: int = 100) -> list[dict]:
    """Get top N models by total test count across all makes."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                make,
                model,
                SUM(total_tests) as total_tests,
                COUNT(*) as variants
            FROM available_vehicles
            GROUP BY make, model
            ORDER BY total_tests DESC
            LIMIT ?
        """, (limit,))

        return [{"make": row["make"],
                 "model": row["model"],
                 "total_tests": row["total_tests"],
                 "variants": row["variants"]}
                for row in cursor.fetchall()]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def get_complete_model_data(make: str, model: str) -> dict | None:
    """
    Main entry point. Returns complete data dict for a make/model.
    Returns None if model not found in database.
    """
    make = make.upper()
    model = model.upper()

    with get_db_connection() as conn:
        # Check if model exists
        variants = _get_variants(conn, make, model)
        if not variants:
            return None

        # Get summary stats
        summary = _get_summary(conn, make, model)

        # Get comparisons
        fuel_comparison = _get_fuel_comparison(conn, make, model)
        year_comparison = _get_year_comparison(conn, make, model)

        # Get best/worst
        best_variant, worst_variant = _get_best_worst_variants(conn, make, model)

        # Get all variants detailed data
        all_variants = _get_all_variants_data(conn, make, model)

        # Get aggregated data
        failures = _get_aggregated_failures(conn, make, model)
        mileage_bands = _get_aggregated_mileage_bands(conn, make, model)
        rankings = _get_aggregated_rankings(conn, make, model)
        severity = _get_aggregated_severity(conn, make, model)
        first_mot = _get_aggregated_first_mot(conn, make, model)
        retest = _get_aggregated_retest(conn, make, model)
        age_bands = _get_aggregated_age_bands(conn, make, model)
        geographic = _get_aggregated_geographic(conn, make, model)
        seasonal = _get_aggregated_seasonal(conn, make, model)
        advisory_progression = _get_aggregated_advisory_progression(conn, make, model)
        component_thresholds = _get_aggregated_component_thresholds(conn, make, model)

        return {
            "make": make,
            "model": model,
            "summary": summary,
            "best_variant": best_variant,
            "worst_variant": worst_variant,
            "fuel_comparison": fuel_comparison,
            "year_comparison": year_comparison,
            "all_variants": all_variants,
            "failure_categories": failures["categories"],
            "top_failures": failures["failures"],
            "top_advisories": failures["advisories"],
            "dangerous_defects": failures["dangerous"],
            "mileage_bands": mileage_bands,
            "rankings": rankings,
            "severity": severity,
            "first_mot": first_mot,
            "retest": retest,
            "age_bands": age_bands,
            "geographic": geographic,
            "seasonal": seasonal,
            "advisory_progression": advisory_progression,
            "component_thresholds": component_thresholds,
        }
