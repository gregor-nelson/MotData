#!/usr/bin/env python3
"""
MOT Insights Generator - Per-Make Analysis
==========================================
Generates comprehensive reliability insights for a specific vehicle make.
Outputs clean JSON for article generation in a separate session.

Usage:
    python generate_make_insights.py HONDA
    python generate_make_insights.py TOYOTA --output ./data/toyota.json
    python generate_make_insights.py --list  # Show all available makes
"""

import argparse
import json
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Database path (relative to script location)
# From json_parser/parser.py -> article_generation/ -> scripts/ -> mot_data_2023/
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "database" / "mot_insights.db"


def get_connection():
    """Create read-only database connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert sqlite3.Row to dict."""
    return dict(zip(row.keys(), row)) if row else None


# Constants for age bands and maturity classification
AGE_BAND_ORDER = {
    "3-4 years": 0,
    "5-6 years": 1,
    "7-8 years": 2,
    "9-10 years": 3,
    "11-12 years": 4,
    "13+ years": 5
}

# National average pass rates by age band (pre-calculated from full dataset)
NATIONAL_AVG_BY_BAND = {
    0: 86.43,  # 3-4 years
    1: 82.13,  # 5-6 years
    2: 77.24,  # 7-8 years
    3: 71.23,  # 9-10 years
    4: 66.54,  # 11-12 years
    5: 59.87   # 13+ years
}

# Maturity tier thresholds
MATURITY_TIERS = {
    "proven": {"min_band": 4, "label": "Proven Durability", "description": "11+ years of real-world data"},
    "maturing": {"min_band": 2, "max_band": 3, "label": "Maturing", "description": "7-10 years of data"},
    "early": {"max_band": 1, "label": "Early", "description": "3-6 years only - durability unproven"}
}

# Minimum tests required for inclusion
MIN_TESTS_PROVEN = 500
MIN_TESTS_EARLY = 1000  # Higher bar for early vehicles since less meaningful


# Cache for national age benchmarks
_national_age_benchmarks = None


def get_national_age_benchmarks(conn) -> dict:
    """Get national average pass rates by age band (cached)."""
    global _national_age_benchmarks
    if _national_age_benchmarks is not None:
        return _national_age_benchmarks

    cur = conn.execute("""
        SELECT
            age_band,
            band_order,
            AVG(pass_rate) as national_pass_rate,
            SUM(total_tests) as total_tests
        FROM age_bands
        GROUP BY age_band, band_order
        ORDER BY band_order
    """)
    _national_age_benchmarks = {
        row["age_band"]: {
            "pass_rate": row["national_pass_rate"],
            "band_order": row["band_order"],
            "total_tests": row["total_tests"]
        }
        for row in cur.fetchall()
    }
    return _national_age_benchmarks


# Cache for yearly national averages
_yearly_national_averages = None


def get_yearly_national_averages(conn) -> dict:
    """Get national average pass rates by model year (cached).

    This allows comparing a vehicle's pass rate against the national
    average for vehicles of the SAME MODEL YEAR - removing the bias
    that makes newer vehicles appear more reliable simply because
    all new cars pass more often.
    """
    global _yearly_national_averages
    if _yearly_national_averages is not None:
        return _yearly_national_averages

    cur = conn.execute("""
        SELECT model_year, metric_value
        FROM national_averages
        WHERE metric_name = 'yearly_pass_rate' AND model_year IS NOT NULL
    """)
    _yearly_national_averages = {row["model_year"]: row["metric_value"] for row in cur.fetchall()}
    return _yearly_national_averages


# Default fallback for missing year averages
FALLBACK_NATIONAL_AVG = 71.51
_fallback_warnings_logged = set()  # Track warnings to avoid spam


def get_year_avg_safe(yearly_avgs: dict, year: int) -> tuple:
    """Get year average with fallback warning.

    Returns (average, used_fallback) tuple. Logs warning on first use of fallback
    for each year to alert about missing data.
    """
    if year in yearly_avgs:
        return yearly_avgs[year], False

    # Log warning only once per year per session
    if year not in _fallback_warnings_logged:
        logging.warning(
            f"No national average for model year {year}, using fallback {FALLBACK_NATIONAL_AVG}%. "
            f"Results for this year may be inaccurate."
        )
        _fallback_warnings_logged.add(year)

    return FALLBACK_NATIONAL_AVG, True


# Cache for weighted age-band averages
_weighted_age_band_averages = None


def get_weighted_age_band_averages(conn) -> dict:
    """Get WEIGHTED national average pass rates by age band (cached).

    Uses weighted average (by test count) rather than simple average,
    so models with more tests have proportionally more influence on
    the benchmark. This is more statistically accurate.
    """
    global _weighted_age_band_averages
    if _weighted_age_band_averages is not None:
        return _weighted_age_band_averages

    cur = conn.execute("""
        SELECT band_order,
            SUM(pass_rate * total_tests) / SUM(total_tests) as weighted_avg
        FROM age_bands
        GROUP BY band_order
        ORDER BY band_order
    """)
    _weighted_age_band_averages = {row["band_order"]: row["weighted_avg"] for row in cur.fetchall()}
    return _weighted_age_band_averages


def list_available_makes():
    """List all makes with test counts."""
    conn = get_connection()
    cur = conn.execute("""
        SELECT make, total_tests, avg_pass_rate, rank
        FROM manufacturer_rankings
        ORDER BY total_tests DESC
    """)
    makes = [dict_from_row(row) for row in cur.fetchall()]
    conn.close()
    return makes


def get_manufacturer_overview(conn, make: str) -> dict:
    """Get manufacturer-level statistics."""
    cur = conn.execute("""
        SELECT * FROM manufacturer_rankings WHERE make = ?
    """, (make,))
    row = cur.fetchone()
    if not row:
        return None
    return dict_from_row(row)


def get_national_averages(conn) -> dict:
    """Get national benchmark statistics."""
    cur = conn.execute("""
        SELECT metric_name, metric_value
        FROM national_averages
        WHERE model_year IS NULL AND fuel_type IS NULL
    """)
    return {row["metric_name"]: row["metric_value"] for row in cur.fetchall()}


def get_competitor_comparison(conn, make: str) -> list:
    """Get competitor brands for comparison."""
    # Define competitor groups by segment
    segments = {
        # Japanese mainstream
        "HONDA": ["TOYOTA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
        "TOYOTA": ["HONDA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
        "MAZDA": ["HONDA", "TOYOTA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
        "NISSAN": ["HONDA", "TOYOTA", "MAZDA", "HYUNDAI", "KIA", "MITSUBISHI"],
        "SUZUKI": ["HONDA", "TOYOTA", "MAZDA", "HYUNDAI", "KIA", "DACIA"],

        # Korean
        "HYUNDAI": ["KIA", "TOYOTA", "HONDA", "MAZDA", "NISSAN", "SKODA"],
        "KIA": ["HYUNDAI", "TOYOTA", "HONDA", "MAZDA", "NISSAN", "SKODA"],

        # European mainstream
        "FORD": ["VAUXHALL", "VOLKSWAGEN", "PEUGEOT", "RENAULT", "CITROEN"],
        "VAUXHALL": ["FORD", "VOLKSWAGEN", "PEUGEOT", "RENAULT", "CITROEN"],
        "VOLKSWAGEN": ["FORD", "VAUXHALL", "SKODA", "SEAT", "PEUGEOT"],
        "PEUGEOT": ["FORD", "VAUXHALL", "RENAULT", "CITROEN", "VOLKSWAGEN"],
        "RENAULT": ["PEUGEOT", "CITROEN", "FORD", "VAUXHALL", "DACIA"],
        "CITROEN": ["PEUGEOT", "RENAULT", "FORD", "VAUXHALL", "FIAT"],
        "SKODA": ["VOLKSWAGEN", "SEAT", "HYUNDAI", "KIA", "FORD"],
        "SEAT": ["SKODA", "VOLKSWAGEN", "HYUNDAI", "KIA", "FORD"],
        "FIAT": ["CITROEN", "PEUGEOT", "RENAULT", "VAUXHALL", "DACIA"],

        # German premium
        "BMW": ["MERCEDES-BENZ", "AUDI", "LEXUS", "JAGUAR", "VOLVO"],
        "MERCEDES-BENZ": ["BMW", "AUDI", "LEXUS", "JAGUAR", "VOLVO"],
        "AUDI": ["BMW", "MERCEDES-BENZ", "LEXUS", "JAGUAR", "VOLVO"],

        # Luxury SUV / British premium
        "LAND ROVER": ["BMW", "MERCEDES-BENZ", "AUDI", "VOLVO", "JAGUAR", "PORSCHE"],
        "JAGUAR": ["BMW", "MERCEDES-BENZ", "AUDI", "LAND ROVER", "LEXUS", "VOLVO"],
        "VOLVO": ["BMW", "MERCEDES-BENZ", "AUDI", "LEXUS", "JAGUAR", "LAND ROVER"],

        # Premium Japanese
        "LEXUS": ["BMW", "MERCEDES-BENZ", "AUDI", "JAGUAR", "VOLVO", "INFINITI"],

        # Sports / Performance
        "PORSCHE": ["BMW", "MERCEDES-BENZ", "AUDI", "JAGUAR", "LEXUS", "ALFA ROMEO"],

        # Premium compact
        "MINI": ["AUDI", "BMW", "VOLKSWAGEN", "FIAT", "DS"],
    }

    # Default competitors if make not in predefined groups
    default_competitors = ["FORD", "VAUXHALL", "VOLKSWAGEN", "TOYOTA", "NISSAN"]
    competitors = segments.get(make, default_competitors)

    # Always include the make itself
    all_makes = [make] + [c for c in competitors if c != make]

    placeholders = ",".join("?" * len(all_makes))
    cur = conn.execute(f"""
        SELECT make, avg_pass_rate, total_tests, rank, total_models
        FROM manufacturer_rankings
        WHERE make IN ({placeholders})
        ORDER BY avg_pass_rate DESC
    """, all_makes)

    return [dict_from_row(row) for row in cur.fetchall()]


def get_all_models(conn, make: str) -> list:
    """Get all vehicle variants with full statistics."""
    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            total_tests, total_passes, total_fails,
            pass_rate, avg_mileage, avg_age_years,
            pass_rate_vs_national
        FROM vehicle_insights
        WHERE make = ?
        ORDER BY pass_rate DESC
    """, (make,))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_models_aggregated(conn, make: str) -> list:
    """Get models aggregated across all years/variants."""
    cur = conn.execute("""
        SELECT
            model,
            SUM(total_tests) as total_tests,
            SUM(total_passes) as total_passes,
            SUM(total_fails) as total_fails,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
            ROUND(AVG(avg_mileage), 0) as avg_mileage,
            MIN(model_year) as year_from,
            MAX(model_year) as year_to,
            COUNT(*) as variant_count
        FROM vehicle_insights
        WHERE make = ?
        GROUP BY model
        HAVING SUM(total_tests) >= 500
        ORDER BY pass_rate DESC
    """, (make,))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_core_models_aggregated(conn, make: str) -> list:
    """Get core model names aggregated (strips variants like 'CIVIC SR VTEC')."""
    # First get all models to identify core names
    cur = conn.execute("""
        SELECT DISTINCT model FROM vehicle_insights WHERE make = ?
    """, (make,))
    all_models = [row["model"] for row in cur.fetchall()]

    # Identify core model names (shortest version of each family)
    core_names = set()
    for model in sorted(all_models, key=len):
        # Check if this is a base for any existing core name
        is_variant = any(model.startswith(core + " ") for core in core_names)
        if not is_variant:
            core_names.add(model)

    # Now aggregate by core name
    results = []
    for core in sorted(core_names):
        cur = conn.execute("""
            SELECT
                ? as core_model,
                SUM(total_tests) as total_tests,
                SUM(total_passes) as total_passes,
                SUM(total_fails) as total_fails,
                ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
                ROUND(AVG(avg_mileage), 0) as avg_mileage,
                MIN(model_year) as year_from,
                MAX(model_year) as year_to,
                COUNT(*) as variant_count,
                GROUP_CONCAT(DISTINCT model) as variants
            FROM vehicle_insights
            WHERE make = ? AND (model = ? OR model LIKE ? || ' %')
            HAVING SUM(total_tests) >= 500
        """, (core, make, core, core))
        row = cur.fetchone()
        if row and row["total_tests"]:
            results.append(dict_from_row(row))

    return sorted(results, key=lambda x: x["pass_rate"], reverse=True)


def get_model_year_breakdown(conn, make: str, model: str) -> list:
    """Get year-by-year breakdown for a specific model."""
    cur = conn.execute("""
        SELECT
            model_year, fuel_type,
            total_tests, pass_rate, avg_mileage,
            pass_rate_vs_national
        FROM vehicle_insights
        WHERE make = ? AND model = ?
        ORDER BY model_year DESC, fuel_type
    """, (make, model))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_model_family_year_breakdown(conn, make: str, core_model: str) -> list:
    """Get year-by-year breakdown for a model family (including variants).

    Uses YEAR-SPECIFIC national averages for comparison, so a 2020 model
    is compared against other 2020 vehicles, not the overall average.
    """
    yearly_avgs = get_yearly_national_averages(conn)

    cur = conn.execute("""
        SELECT
            model_year, fuel_type,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
            ROUND(AVG(avg_mileage), 0) as avg_mileage
        FROM vehicle_insights
        WHERE make = ? AND (model = ? OR model LIKE ? || ' %')
        GROUP BY model_year, fuel_type
        HAVING SUM(total_tests) >= 100
        ORDER BY model_year DESC, fuel_type
    """, (make, core_model, core_model))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"])[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)
    return results


def get_fuel_type_breakdown(conn, make: str) -> list:
    """Get pass rates by fuel type for this make."""
    cur = conn.execute("""
        SELECT
            fuel_type,
            COUNT(*) as model_count,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate
        FROM vehicle_insights
        WHERE make = ?
        GROUP BY fuel_type
        ORDER BY pass_rate DESC
    """, (make,))

    fuel_names = {
        "PE": "Petrol",
        "DI": "Diesel",
        "HY": "Hybrid Electric",
        "EL": "Electric",
        "ED": "Plug-in Hybrid",
        "GB": "Gas Bi-fuel",
        "OT": "Other"
    }

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        data["fuel_name"] = fuel_names.get(data["fuel_type"], data["fuel_type"])
        results.append(data)

    return results


def get_best_models(conn, make: str, limit: int = 15) -> list:
    """Get best performing models using YEAR-ADJUSTED scoring (min 500 tests).

    Ranks models by how much they exceed the national average for their
    model year, not by raw pass rate. This prevents newer vehicles from
    dominating simply because all new cars pass more often.
    """
    yearly_avgs = get_yearly_national_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            total_tests, pass_rate
        FROM vehicle_insights
        WHERE make = ? AND total_tests >= 500
    """, (make,))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"])[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)

    # Sort by performance vs year average (not raw pass rate)
    results.sort(key=lambda x: x["pass_rate_vs_national"], reverse=True)
    return results[:limit]


def get_worst_models(conn, make: str, limit: int = 10) -> list:
    """Get worst performing models using YEAR-ADJUSTED scoring (min 500 tests).

    Ranks models by how much they fall below the national average for their
    model year. This identifies genuinely problematic vehicles, not just
    old ones that naturally have lower pass rates.
    """
    yearly_avgs = get_yearly_national_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            total_tests, pass_rate
        FROM vehicle_insights
        WHERE make = ? AND total_tests >= 500
    """, (make,))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"])[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)

    # Sort by performance vs year average (worst first)
    results.sort(key=lambda x: x["pass_rate_vs_national"])
    return results[:limit]


def get_failure_categories(conn, make: str) -> list:
    """Get aggregated failure categories for this make."""
    cur = conn.execute("""
        SELECT
            category_name,
            SUM(failure_count) as total_failures,
            COUNT(DISTINCT model || model_year || fuel_type) as vehicle_count
        FROM failure_categories
        WHERE make = ?
        GROUP BY category_name
        ORDER BY total_failures DESC
    """, (make,))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_top_defects(conn, make: str, defect_type: str = "failure", limit: int = 10) -> list:
    """Get top defects (failures or advisories) for this make."""
    cur = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE make = ? AND defect_type = ?
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
        LIMIT ?
    """, (make, defect_type, limit))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_dangerous_defects(conn, make: str, limit: int = 10) -> list:
    """Get top dangerous defects for this make."""
    cur = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences
        FROM dangerous_defects
        WHERE make = ?
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
        LIMIT ?
    """, (make, limit))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_mileage_impact(conn, make: str) -> list:
    """Get pass rate by mileage band for this make."""
    cur = conn.execute("""
        SELECT
            mileage_band,
            band_order,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as avg_pass_rate
        FROM mileage_bands
        WHERE make = ?
        GROUP BY mileage_band, band_order
        ORDER BY band_order
    """, (make,))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_age_adjusted_scores(conn, make: str) -> list:
    """
    Calculate age-adjusted reliability scores for each model/year.

    Compares each model's pass rate at each age band against the national
    average for that same age band. This removes age bias from comparisons.

    Returns list of models with:
    - avg_vs_national: average performance vs national across all age bands
    - age_bands: detailed breakdown by age band
    - durability_trend: whether model improves or degrades relative to peers over time
    """
    national = get_national_age_benchmarks(conn)

    # Get all age band data for this make
    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            age_band, band_order,
            pass_rate, total_tests, avg_mileage
        FROM age_bands
        WHERE make = ?
        ORDER BY model, model_year, fuel_type, band_order
    """, (make,))

    # Group by model/year/fuel
    model_data = defaultdict(lambda: {"bands": [], "total_tests": 0})

    for row in cur.fetchall():
        key = (row["model"], row["model_year"], row["fuel_type"])
        national_rate = national.get(row["age_band"], {}).get("pass_rate", 71.5)
        vs_national = row["pass_rate"] - national_rate

        model_data[key]["bands"].append({
            "age_band": row["age_band"],
            "band_order": row["band_order"],
            "pass_rate": row["pass_rate"],
            "national_pass_rate": round(national_rate, 2),
            "vs_national": round(vs_national, 2),
            "total_tests": row["total_tests"],
            "avg_mileage": row["avg_mileage"]
        })
        model_data[key]["total_tests"] += row["total_tests"]

    # Calculate aggregate scores
    results = []
    for (model, model_year, fuel_type), data in model_data.items():
        if data["total_tests"] < 500:  # Minimum sample size
            continue

        bands = data["bands"]

        # Weighted average vs_national (weighted by test count in each band)
        total_weight = sum(b["total_tests"] for b in bands)
        avg_vs_national = sum(
            b["vs_national"] * b["total_tests"] for b in bands
        ) / total_weight if total_weight > 0 else 0

        # Calculate durability trend (slope of vs_national over age)
        # Positive = getting relatively better with age
        # Negative = degrading faster than average
        durability_trend = 0
        if len(bands) >= 2:
            sorted_bands = sorted(bands, key=lambda x: x["band_order"])
            first_vs = sorted_bands[0]["vs_national"]
            last_vs = sorted_bands[-1]["vs_national"]
            # Change in vs_national per age band
            durability_trend = (last_vs - first_vs) / (len(sorted_bands) - 1)

        results.append({
            "model": model,
            "model_year": model_year,
            "fuel_type": fuel_type,
            "total_tests": data["total_tests"],
            "avg_vs_national": round(avg_vs_national, 2),
            "durability_trend": round(durability_trend, 2),
            "age_bands": bands
        })

    # Sort by avg_vs_national (best performers first)
    results.sort(key=lambda x: x["avg_vs_national"], reverse=True)
    return results


def get_best_models_age_adjusted(conn, make: str, limit: int = 15) -> list:
    """
    Get best performing models using age-adjusted scoring.

    This answers: "Which models perform best compared to the average car
    of the same age?" - removing the bias towards newer vehicles.
    """
    age_scores = get_age_adjusted_scores(conn, make)

    # Return top performers with simplified structure
    return [
        {
            "model": m["model"],
            "model_year": m["model_year"],
            "fuel_type": m["fuel_type"],
            "total_tests": m["total_tests"],
            "avg_vs_national": m["avg_vs_national"],
            "durability_trend": m["durability_trend"],
            # Include best and worst age band for context
            "best_age_band": max(m["age_bands"], key=lambda x: x["vs_national"]) if m["age_bands"] else None,
            "worst_age_band": min(m["age_bands"], key=lambda x: x["vs_national"]) if m["age_bands"] else None
        }
        for m in age_scores[:limit]
    ]


def get_worst_models_age_adjusted(conn, make: str, limit: int = 10) -> list:
    """
    Get worst performing models using age-adjusted scoring.

    These are models that perform below average for their age -
    genuinely problematic vehicles, not just old ones.
    """
    age_scores = get_age_adjusted_scores(conn, make)

    # Return worst performers (from end of sorted list)
    worst = age_scores[-limit:] if len(age_scores) >= limit else age_scores
    worst.reverse()  # Worst first

    return [
        {
            "model": m["model"],
            "model_year": m["model_year"],
            "fuel_type": m["fuel_type"],
            "total_tests": m["total_tests"],
            "avg_vs_national": m["avg_vs_national"],
            "durability_trend": m["durability_trend"],
            "best_age_band": max(m["age_bands"], key=lambda x: x["vs_national"]) if m["age_bands"] else None,
            "worst_age_band": min(m["age_bands"], key=lambda x: x["vs_national"]) if m["age_bands"] else None
        }
        for m in worst
    ]


# =============================================================================
# EVIDENCE-TIERED DURABILITY SCORING (New Methodology)
# =============================================================================
# These functions implement a more rigorous approach to durability claims:
# - Only vehicles with 11+ years of data can be called "durability champions"
# - Newer vehicles are classified as "early performers" with appropriate caveats
# - Models to avoid are only flagged if they have proven poor performance at old age
# =============================================================================


def get_durability_champions(conn, make: str, limit: int = 15) -> list:
    """
    Get vehicles with PROVEN durability - those that have reached 11+ years
    and still perform above national average for their age.

    This is the highest-quality durability insight: these cars have genuinely
    demonstrated they age well compared to average vehicles.

    Uses WEIGHTED national averages by age band from the database.
    """
    age_band_avgs = get_weighted_age_band_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            age_band, band_order,
            total_tests,
            pass_rate,
            avg_mileage
        FROM age_bands
        WHERE make = ?
          AND band_order >= 4  -- 11+ years only (proven tier)
          AND total_tests >= ?
    """, (make, MIN_TESTS_PROVEN))

    results = []
    for row in cur.fetchall():
        band_avg = age_band_avgs.get(row["band_order"], 60.0)
        vs_national_at_age = round(row["pass_rate"] - band_avg, 2)

        if vs_national_at_age > 0:  # Only above-average performers
            results.append({
                "model": row["model"],
                "model_year": row["model_year"],
                "fuel_type": row["fuel_type"],
                "age_band": row["age_band"],
                "age_band_order": row["band_order"],
                "total_tests": row["total_tests"],
                "pass_rate": row["pass_rate"],
                "vs_national_at_age": vs_national_at_age,
                "national_avg_for_age": round(band_avg, 2),
                "avg_mileage": row["avg_mileage"],
                "maturity_tier": "proven",
                "evidence_quality": "high"
            })

    # Deduplicate: keep only the oldest age band (highest band_order) for each model/year/fuel
    # This shows the most proven durability evidence for each vehicle
    seen = {}
    for r in results:
        key = (r["model"], r["model_year"], r["fuel_type"])
        if key not in seen or r["age_band_order"] > seen[key]["age_band_order"]:
            seen[key] = r
    results = list(seen.values())

    # Sort by vs_national_at_age descending (best performers first)
    results.sort(key=lambda x: x["vs_national_at_age"], reverse=True)
    return results[:limit]


def get_models_to_avoid_proven(conn, make: str, limit: int = 10) -> list:
    """
    Get models that have PROVEN poor durability - those that have reached 11+ years
    and perform BELOW national average for their age.

    These are genuinely problematic vehicles, not just old cars.
    A car performing below average at 13+ years means it ages worse than typical.

    Uses WEIGHTED national averages by age band from the database.
    """
    age_band_avgs = get_weighted_age_band_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            age_band, band_order,
            total_tests,
            pass_rate,
            avg_mileage
        FROM age_bands
        WHERE make = ?
          AND band_order >= 4  -- 11+ years only
          AND total_tests >= ?
    """, (make, MIN_TESTS_PROVEN))

    results = []
    for row in cur.fetchall():
        band_avg = age_band_avgs.get(row["band_order"], 60.0)
        vs_national_at_age = round(row["pass_rate"] - band_avg, 2)

        if vs_national_at_age < 0:  # Only below-average performers
            results.append({
                "model": row["model"],
                "model_year": row["model_year"],
                "fuel_type": row["fuel_type"],
                "age_band": row["age_band"],
                "age_band_order": row["band_order"],
                "total_tests": row["total_tests"],
                "pass_rate": row["pass_rate"],
                "vs_national_at_age": vs_national_at_age,
                "national_avg_for_age": round(band_avg, 2),
                "avg_mileage": row["avg_mileage"],
                "maturity_tier": "proven",
                "evidence_quality": "high",
                "concern": "Below average durability at " + row["age_band"]
            })

    # Deduplicate: keep only the oldest age band (highest band_order) for each model/year/fuel
    seen = {}
    for r in results:
        key = (r["model"], r["model_year"], r["fuel_type"])
        if key not in seen or r["age_band_order"] > seen[key]["age_band_order"]:
            seen[key] = r
    results = list(seen.values())

    # Sort by vs_national_at_age ascending (worst performers first)
    results.sort(key=lambda x: x["vs_national_at_age"])
    return results[:limit]


def get_early_performers(conn, make: str, limit: int = 10) -> list:
    """
    Get newer vehicles (3-6 years) that show strong early performance.

    IMPORTANT: These have NOT proven durability. The caveat must be clear
    that these are early results only - older versions of the same model
    may tell a different story at 11+ years.

    Uses WEIGHTED national averages by age band from the database.
    """
    age_band_avgs = get_weighted_age_band_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            age_band, band_order,
            total_tests,
            pass_rate,
            avg_mileage
        FROM age_bands
        WHERE make = ?
          AND band_order <= 1  -- 3-6 years only (early tier)
          AND total_tests >= ?
    """, (make, MIN_TESTS_EARLY))

    results = []
    for row in cur.fetchall():
        band_avg = age_band_avgs.get(row["band_order"], 85.0)
        vs_national_at_age = round(row["pass_rate"] - band_avg, 2)

        if vs_national_at_age > 0:  # Only above-average performers
            results.append({
                "model": row["model"],
                "model_year": row["model_year"],
                "fuel_type": row["fuel_type"],
                "age_band": row["age_band"],
                "age_band_order": row["band_order"],
                "total_tests": row["total_tests"],
                "pass_rate": row["pass_rate"],
                "vs_national_at_age": vs_national_at_age,
                "national_avg_for_age": round(band_avg, 2),
                "avg_mileage": row["avg_mileage"],
                "maturity_tier": "early",
                "evidence_quality": "limited",
                "caveat": "Durability not yet proven - too early to assess long-term reliability"
            })

    # Sort by vs_national_at_age descending (best performers first)
    results.sort(key=lambda x: x["vs_national_at_age"], reverse=True)
    return results[:limit]


def get_model_family_trajectory(conn, make: str, core_model: str) -> dict:
    """
    Get the full aging trajectory for a model family.

    Shows how different model years perform at each age band,
    helping identify which years are most durable and any
    quality inflection points (e.g., when manufacturing improved).

    Uses WEIGHTED national averages by age band from the database.
    """
    age_band_avgs = get_weighted_age_band_averages(conn)

    cur = conn.execute("""
        SELECT
            model_year,
            age_band,
            band_order,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate,
            ROUND(AVG(avg_mileage), 0) as avg_mileage
        FROM age_bands
        WHERE make = ? AND (model = ? OR model LIKE ? || ' %')
        GROUP BY model_year, age_band, band_order
        HAVING SUM(total_tests) >= 200
        ORDER BY band_order, model_year
    """, (make, core_model, core_model))

    # Organize by age band
    trajectory = {}
    all_years = set()

    for row in cur.fetchall():
        band = row["age_band"]
        band_avg = age_band_avgs.get(row["band_order"], 71.5)

        if band not in trajectory:
            trajectory[band] = {
                "band_order": row["band_order"],
                "national_avg": round(band_avg, 2),
                "model_years": []
            }

        vs_national = round(row["pass_rate"] - band_avg, 2)

        trajectory[band]["model_years"].append({
            "year": row["model_year"],
            "pass_rate": row["pass_rate"],
            "vs_national": vs_national,
            "total_tests": row["total_tests"],
            "avg_mileage": row["avg_mileage"]
        })
        all_years.add(row["model_year"])

    # Identify best/worst years at proven ages (11+ years)
    proven_performance = []
    for band_name, band_data in trajectory.items():
        if band_data["band_order"] >= 4:  # 11+ years
            for my in band_data["model_years"]:
                proven_performance.append({
                    "year": my["year"],
                    "vs_national": my["vs_national"],
                    "age_band": band_name
                })

    best_proven_year = None
    worst_proven_year = None
    if proven_performance:
        proven_performance.sort(key=lambda x: x["vs_national"], reverse=True)
        best_proven_year = proven_performance[0]
        worst_proven_year = proven_performance[-1]

    return {
        "core_model": core_model,
        "years_covered": sorted(all_years),
        "trajectory_by_age": trajectory,
        "best_proven_year": best_proven_year,
        "worst_proven_year": worst_proven_year,
        "has_proven_data": any(b["band_order"] >= 4 for b in trajectory.values())
    }


def get_reliability_summary(conn, make: str) -> dict:
    """
    Generate a high-level reliability summary based on proven data.

    This provides trustworthy statements about the make's durability
    based only on vehicles with sufficient age data.

    Uses WEIGHTED national averages by age band from the database.
    """
    age_band_avgs = get_weighted_age_band_averages(conn)

    # Count vehicles in each maturity tier
    cur = conn.execute("""
        SELECT
            CASE
                WHEN band_order >= 4 THEN 'proven'
                WHEN band_order >= 2 THEN 'maturing'
                ELSE 'early'
            END as tier,
            COUNT(DISTINCT model || model_year || fuel_type) as vehicle_count,
            SUM(total_tests) as total_tests
        FROM age_bands
        WHERE make = ?
        GROUP BY tier
    """, (make,))

    tier_counts = {row["tier"]: {"vehicles": row["vehicle_count"], "tests": row["total_tests"]}
                   for row in cur.fetchall()}

    # Get proven durability stats - calculate vs_national in Python
    cur = conn.execute("""
        SELECT band_order, pass_rate, total_tests
        FROM age_bands
        WHERE make = ? AND band_order >= 4 AND total_tests >= ?
    """, (make, MIN_TESTS_PROVEN))

    total_proven = 0
    above_avg = 0
    below_avg = 0
    total_vs_national = 0.0

    for row in cur.fetchall():
        band_avg = age_band_avgs.get(row["band_order"], 60.0)
        vs_national = row["pass_rate"] - band_avg
        total_proven += 1
        total_vs_national += vs_national
        if vs_national > 0:
            above_avg += 1
        else:
            below_avg += 1

    # Calculate durability rating
    if total_proven > 0:
        pct_above_avg = (above_avg / total_proven) * 100
        avg_vs_national = round(total_vs_national / total_proven, 2)

        if pct_above_avg >= 80 and avg_vs_national >= 5:
            durability_rating = "Excellent"
        elif pct_above_avg >= 60 and avg_vs_national >= 2:
            durability_rating = "Good"
        elif pct_above_avg >= 40:
            durability_rating = "Average"
        else:
            durability_rating = "Below Average"
    else:
        durability_rating = "Insufficient Data"
        pct_above_avg = None
        avg_vs_national = None

    return {
        "tier_distribution": tier_counts,
        "proven_vehicles_tested": total_proven,
        "proven_above_average_pct": round(pct_above_avg, 1) if pct_above_avg else None,
        "proven_avg_vs_national": avg_vs_national,
        "durability_rating": durability_rating,
        "methodology_note": "Rating based only on vehicles with 11+ years of MOT data"
    }


def generate_make_insights(make: str) -> dict:
    """Generate complete insights for a make."""
    make = make.upper()
    conn = get_connection()

    # Get manufacturer overview
    overview = get_manufacturer_overview(conn, make)
    if not overview:
        conn.close()
        return {"error": f"Make '{make}' not found in database"}

    # Get national averages for context
    national = get_national_averages(conn)

    # Get competitor comparison
    competitors = get_competitor_comparison(conn, make)

    # Get all models (detailed)
    all_models = get_all_models(conn, make)

    # Get aggregated by core model name
    core_models = get_core_models_aggregated(conn, make)

    # Get year breakdowns for top core models
    model_breakdowns = {}
    for cm in core_models[:10]:  # Top 10 core models
        breakdown = get_model_family_year_breakdown(conn, make, cm["core_model"])
        if breakdown:
            model_breakdowns[cm["core_model"]] = breakdown

    # Get fuel type analysis
    fuel_analysis = get_fuel_type_breakdown(conn, make)

    # Get best and worst
    best_models = get_best_models(conn, make)
    worst_models = get_worst_models(conn, make)

    # Get failure data
    failure_categories = get_failure_categories(conn, make)
    top_failures = get_top_defects(conn, make, "failure")
    top_advisories = get_top_defects(conn, make, "advisory")
    dangerous_defects = get_dangerous_defects(conn, make)

    # Get mileage impact
    mileage_impact = get_mileage_impact(conn, make)

    # Get age-adjusted scores (legacy methodology - kept for backwards compatibility)
    best_age_adjusted = get_best_models_age_adjusted(conn, make)
    worst_age_adjusted = get_worst_models_age_adjusted(conn, make)

    # =================================================================
    # NEW: Evidence-Tiered Durability Analysis
    # =================================================================
    # This is the high-quality methodology that separates proven
    # durability from early/unproven performance
    # =================================================================

    # Get reliability summary based on proven data
    reliability_summary = get_reliability_summary(conn, make)

    # Get durability champions (proven 11+ years, above average)
    durability_champions = get_durability_champions(conn, make)

    # Get models to avoid (proven 11+ years, below average)
    models_to_avoid_proven = get_models_to_avoid_proven(conn, make)

    # Get early performers (3-6 years, with caveats)
    early_performers = get_early_performers(conn, make)

    # Get model family trajectories for key models
    # Prioritize models with the most data and proven durability data
    model_trajectories = {}
    key_models = set()

    # Include unique models from durability champions (proven good)
    for m in durability_champions[:10]:
        core = m["model"].split()[0] if " " in m["model"] else m["model"]
        key_models.add(core)

    # Include unique models from models to avoid (proven bad)
    for m in models_to_avoid_proven[:5]:
        core = m["model"].split()[0] if " " in m["model"] else m["model"]
        key_models.add(core)

    # Include top core models by test count (most popular)
    top_by_tests = sorted(core_models, key=lambda x: x["total_tests"], reverse=True)
    for cm in top_by_tests[:8]:
        key_models.add(cm["core_model"])

    for core_model in key_models:
        trajectory = get_model_family_trajectory(conn, make, core_model)
        if trajectory["trajectory_by_age"]:  # Only include if we have data
            model_trajectories[core_model] = trajectory

    conn.close()

    # Build output structure
    return {
        "meta": {
            "make": make,
            "generated_at": datetime.now().isoformat(),
            "database": str(DB_PATH.name),
            "national_pass_rate": national.get("overall_pass_rate", 71.51),
            "methodology_version": "2.1",
            "methodology_note": "Year-adjusted scoring: model comparisons use same-year national averages. "
                               "Age-band comparisons use weighted national averages. "
                               "Only vehicles with 11+ years of data are classified as 'proven' durability."
        },
        "overview": overview,
        "competitors": competitors,
        "summary": {
            "total_tests": overview["total_tests"],
            "total_models": overview["total_models"],
            "avg_pass_rate": overview["avg_pass_rate"],
            "rank": overview["rank"],
            "rank_total": 75,
            "best_model": overview["best_model"],
            "best_model_pass_rate": overview["best_model_pass_rate"],
            "worst_model": overview["worst_model"],
            "worst_model_pass_rate": overview["worst_model_pass_rate"],
            "vs_national": round(overview["avg_pass_rate"] - national.get("overall_pass_rate", 71.51), 2),
            "vs_national_note": "Manufacturer average vs overall national average (for brand-level comparison)"
        },
        "core_models": core_models,
        "model_year_breakdowns": model_breakdowns,
        "fuel_analysis": fuel_analysis,
        "best_models": best_models,
        "worst_models": worst_models,
        "failures": {
            "categories": failure_categories,
            "top_failures": top_failures,
            "top_advisories": top_advisories,
            "dangerous": dangerous_defects
        },
        "mileage_impact": mileage_impact,
        "all_models": all_models,
        # Legacy age-adjusted scoring (kept for backwards compatibility)
        "age_adjusted": {
            "methodology": "Compares each model's pass rate against the national average for cars of the same age. A positive score means the model performs better than average for its age.",
            "best_models": best_age_adjusted,
            "worst_models": worst_age_adjusted
        },
        # NEW: Evidence-tiered durability analysis (high-quality insights)
        "durability": {
            "methodology": {
                "description": "Evidence-tiered durability scoring based on proven long-term data",
                "proven_threshold": "11+ years of MOT data required for 'proven' durability claims",
                "early_caveat": "Vehicles under 7 years old have not yet proven long-term durability",
                "scoring": "Performance vs national average for vehicles of the same age"
            },
            "reliability_summary": reliability_summary,
            "durability_champions": {
                "description": "Vehicles with PROVEN durability - 11+ years old and still performing above average",
                "evidence_quality": "high",
                "vehicles": durability_champions
            },
            "models_to_avoid": {
                "description": "Vehicles with PROVEN poor durability - 11+ years old and performing below average",
                "evidence_quality": "high",
                "vehicles": models_to_avoid_proven
            },
            "early_performers": {
                "description": "Newer vehicles showing strong early results (3-6 years)",
                "evidence_quality": "limited",
                "caveat": "Durability NOT yet proven - these vehicles have not been tested at older ages",
                "vehicles": early_performers
            },
            "model_trajectories": model_trajectories
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate MOT reliability insights for a vehicle make",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_make_insights.py HONDA
    python generate_make_insights.py TOYOTA --output ./toyota_insights.json
    python generate_make_insights.py --list
    python generate_make_insights.py --list --top 20
        """
    )
    parser.add_argument("make", nargs="?", help="Vehicle make (e.g., HONDA, TOYOTA, FORD)")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: {make}_insights.json)")
    parser.add_argument("--list", "-l", action="store_true", help="List all available makes")
    parser.add_argument("--top", type=int, default=10, help="Number of makes to show with --list")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON output")

    args = parser.parse_args()

    # List mode
    if args.list:
        makes = list_available_makes()
        print(f"\n{'Make':<20} {'Tests':>12} {'Pass Rate':>10} {'Rank':>6}")
        print("-" * 52)
        for m in makes[:args.top]:
            print(f"{m['make']:<20} {m['total_tests']:>12,} {m['avg_pass_rate']:>9.1f}% #{m['rank']:>4}")
        print(f"\n{len(makes)} makes available. Use --top N to see more.")
        return

    # Require make for insights
    if not args.make:
        parser.print_help()
        return

    make = args.make.upper()
    print(f"Generating insights for {make}...")

    # Generate insights
    insights = generate_make_insights(make)

    if "error" in insights:
        print(f"Error: {insights['error']}")
        return

    # Determine output path
    output_path = args.output or f"{make.lower()}_insights.json"
    output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    indent = 2 if args.pretty else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=indent, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  {make} MOT INSIGHTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Tests:     {insights['summary']['total_tests']:,}")
    print(f"  Models/Variants: {insights['summary']['total_models']}")
    print(f"  Pass Rate:       {insights['summary']['avg_pass_rate']:.1f}%")
    print(f"  vs National:     {insights['summary']['vs_national']:+.1f}%")
    print(f"  Rank:            #{insights['summary']['rank']} of {insights['summary']['rank_total']}")
    print(f"{'='*60}")
    best_rate = insights['summary']['best_model_pass_rate']
    worst_rate = insights['summary']['worst_model_pass_rate']
    best_str = f"{insights['summary']['best_model']} ({best_rate:.1f}%)" if best_rate else "N/A (insufficient data)"
    worst_str = f"{insights['summary']['worst_model']} ({worst_rate:.1f}%)" if worst_rate else "N/A (insufficient data)"
    print(f"  Best:  {best_str}")
    print(f"  Worst: {worst_str}")
    print(f"{'='*60}")
    print(f"\n  Output: {output_path.absolute()}")
    print(f"  Size:   {output_path.stat().st_size:,} bytes")
    print()


if __name__ == "__main__":
    main()
