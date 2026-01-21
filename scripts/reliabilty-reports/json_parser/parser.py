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
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    REFERENCE_YEAR,
    MIN_TESTS_DEFAULT,
    MIN_TESTS_BEST_MODELS,
    MIN_TESTS_FUEL_TYPE,
    MIN_TESTS_META_DESCRIPTION,
    MOTORHOME_BRANDS,
    EXCLUSION_YEAR_CUTOFF,
    VALID_FUEL_TYPES,
    AGE_BAND_ORDER,
    NATIONAL_AVG_BY_BAND,
    SAMPLE_CONFIDENCE,
    FUEL_TYPE_NAMES,
    FALLBACK_NATIONAL_AVG,
    RATING_EXCELLENT_PCT,
    RATING_EXCELLENT_VS_NAT,
    RATING_GOOD_PCT,
    RATING_GOOD_VS_NAT,
    RATING_AVERAGE_PCT,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Database path (relative to script location)
# From json_parser/parser.py -> reliabilty-reports/ -> scripts/ -> Mot Data/
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "source" / "database" / "mot_insights.db"


def get_connection():
    """Create read-only database connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert sqlite3.Row to dict."""
    return dict(zip(row.keys(), row)) if row else None


# =============================================================================
# CONFIGURATION
# =============================================================================
# Runtime configuration dict for functions that accept config overrides.
# Values reference the central config.py constants.
# =============================================================================

DEFAULT_CONFIG = {
    "min_tests": MIN_TESTS_DEFAULT,
    "min_tests_trajectory": 100,
    "rating_excellent_pct": RATING_EXCELLENT_PCT,
    "rating_excellent_vs_nat": RATING_EXCELLENT_VS_NAT,
    "rating_good_pct": RATING_GOOD_PCT,
    "rating_good_vs_nat": RATING_GOOD_VS_NAT,
    "rating_average_pct": RATING_AVERAGE_PCT,
    "fallback_national_avg": FALLBACK_NATIONAL_AVG,
}


def is_excluded_model(model_name: str, year_from: int = None, model_year: int = None) -> bool:
    """
    Check if model should be excluded from best models list.

    Excludes:
    - Motorhomes (identified by first word being a motorhome brand)
    - Vehicles older than EXCLUSION_YEAR_CUTOFF (40-year rolling exemption)

    Args:
        model_name: The model name to check
        year_from: Optional earliest year for this model (for aggregated data)
        model_year: Optional specific model year (for per-variant data)

    Returns:
        True if model should be excluded, False otherwise
    """
    if not model_name:
        return True

    # Check if first word is a motorhome brand
    first_word = model_name.split()[0].upper()
    if first_word in MOTORHOME_BRANDS:
        return True

    # Exclude vehicles older than cutoff year (use year_from or model_year)
    check_year = year_from if year_from is not None else model_year
    if check_year is not None and check_year < EXCLUSION_YEAR_CUTOFF:
        return True

    return False


# =============================================================================
# HELPER FUNCTIONS - Age Band Calculation
# =============================================================================

def calculate_age_band(model_year: int, reference_year: int = None) -> tuple:
    """
    Calculate age band from model year.

    Args:
        model_year: The vehicle's model year (e.g., 2015)
        reference_year: Year to calculate age from (default: REFERENCE_YEAR = 2024)

    Returns:
        Tuple of (age_band_name, band_order)

    Age bands:
        0: 3-7 years   - New vehicles, most pass, limited differentiation
        1: 8-10 years  - Maturing, issues start emerging
        2: 11-14 years - Established, solid durability data
        3: 15-17 years - Long-term, smaller samples expected
        4: 18-20 years - Veteran, notable durability
        5: 21+ years   - Classic, very small samples
    """
    if reference_year is None:
        reference_year = REFERENCE_YEAR

    if model_year is None:
        return (None, None)

    age = reference_year - model_year

    # Vehicles under 3 years don't need MOT
    if age < 3:
        return (None, None)
    elif age <= 7:
        return ("3-7 years", 0)
    elif age <= 10:
        return ("8-10 years", 1)
    elif age <= 14:
        return ("11-14 years", 2)
    elif age <= 17:
        return ("15-17 years", 3)
    elif age <= 20:
        return ("18-20 years", 4)
    else:
        return ("21+ years", 5)


def get_sample_confidence(total_tests: int) -> dict:
    """
    Get objective confidence indicator based on sample size.

    Args:
        total_tests: Number of MOT tests in sample

    Returns:
        Dict with 'level' and 'note' keys
    """
    if total_tests >= SAMPLE_CONFIDENCE["high"]["min_tests"]:
        return {"level": "high", "note": None}
    elif total_tests >= SAMPLE_CONFIDENCE["medium"]["min_tests"]:
        return {"level": "medium", "note": None}
    elif total_tests >= SAMPLE_CONFIDENCE["low"]["min_tests"]:
        return {"level": "low", "note": SAMPLE_CONFIDENCE["low"]["note"]}
    else:
        return {"level": "insufficient", "note": SAMPLE_CONFIDENCE["insufficient"]["note"]}


# =============================================================================
# CACHING
# =============================================================================

# Cache for national age benchmarks
_national_age_benchmarks = None


def get_national_age_benchmarks(conn) -> dict:
    """
    Calculate national average pass rates by age band from vehicle_insights (cached).

    Derives age bands dynamically from model_year using REFERENCE_YEAR (2024).
    Uses weighted average (by test count) for statistical accuracy.

    Returns:
        Dict keyed by age_band name with pass_rate, band_order, total_tests, confidence
    """
    global _national_age_benchmarks
    if _national_age_benchmarks is not None:
        return _national_age_benchmarks

    # Query all vehicles with model_year from vehicle_insights
    cur = conn.execute("""
        SELECT
            model_year,
            SUM(total_tests) as total_tests,
            SUM(total_passes) as total_passes
        FROM vehicle_insights
        WHERE model_year IS NOT NULL
        GROUP BY model_year
    """)

    # Aggregate by calculated age band
    band_data = defaultdict(lambda: {"total_tests": 0, "total_passes": 0})

    for row in cur.fetchall():
        age_band, band_order = calculate_age_band(row["model_year"])
        if age_band is None:
            continue  # Skip vehicles too new for MOT

        band_data[band_order]["total_tests"] += row["total_tests"]
        band_data[band_order]["total_passes"] += row["total_passes"]
        band_data[band_order]["age_band"] = age_band

    # Calculate weighted pass rates
    _national_age_benchmarks = {}
    for band_order, data in band_data.items():
        if data["total_tests"] > 0:
            pass_rate = (data["total_passes"] / data["total_tests"]) * 100
            confidence = get_sample_confidence(data["total_tests"])
            _national_age_benchmarks[data["age_band"]] = {
                "pass_rate": round(pass_rate, 2),
                "band_order": band_order,
                "total_tests": data["total_tests"],
                "confidence": confidence["level"]
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


# Track warnings to avoid spam
_fallback_warnings_logged = set()


def get_year_avg_safe(yearly_avgs: dict, year: int, config: dict = None) -> tuple:
    """Get year average with fallback warning.

    Returns (average, used_fallback) tuple. Logs warning on first use of fallback
    for each year to alert about missing data.
    """
    if year in yearly_avgs:
        return yearly_avgs[year], False

    cfg = config or DEFAULT_CONFIG
    fallback = cfg["fallback_national_avg"]

    # Log warning only once per year per session
    if year not in _fallback_warnings_logged:
        logging.warning(
            f"No national average for model year {year}, using fallback {fallback}%. "
            f"Results for this year may be inaccurate."
        )
        _fallback_warnings_logged.add(year)

    return fallback, True


# Cache for weighted age-band averages
_weighted_age_band_averages = None


def get_weighted_age_band_averages(conn) -> dict:
    """
    Get weighted national average pass rates by age band (cached).

    Derives from get_national_age_benchmarks() which calculates from vehicle_insights.
    Returns dict keyed by band_order for easy lookup.

    Returns:
        Dict mapping band_order (int) to weighted pass_rate (float)
    """
    global _weighted_age_band_averages
    if _weighted_age_band_averages is not None:
        return _weighted_age_band_averages

    # Get benchmarks (already weighted by test count)
    benchmarks = get_national_age_benchmarks(conn)

    if benchmarks:
        _weighted_age_band_averages = {
            data["band_order"]: data["pass_rate"]
            for data in benchmarks.values()
        }
    else:
        # Fallback to estimated values if no data
        _weighted_age_band_averages = NATIONAL_AVG_BY_BAND.copy()

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


def get_manufacturer_rank_filtered(conn, make: str, min_tests: int = 10000) -> tuple:
    """
    Calculate rank among manufacturers with minimum test threshold.

    Fixes Issue 1: Returns accurate rank/total by only counting manufacturers
    that meet the minimum test threshold.

    Args:
        conn: Database connection
        make: Vehicle make to get rank for
        min_tests: Minimum total tests to be included in ranking

    Returns:
        Tuple of (rank, total_count) where rank is 1-indexed position
        and total_count is number of qualifying manufacturers.
        Returns (None, None) if make doesn't meet threshold.
    """
    cur = conn.execute("""
        WITH ranked AS (
            SELECT make,
                   ROW_NUMBER() OVER (ORDER BY avg_pass_rate DESC) as calc_rank,
                   COUNT(*) OVER () as total_count
            FROM manufacturer_rankings
            WHERE total_tests >= ?
        )
        SELECT calc_rank, total_count FROM ranked WHERE make = ?
    """, (min_tests, make))
    row = cur.fetchone()
    return (row['calc_rank'], row['total_count']) if row else (None, None)


def get_total_manufacturer_count(conn) -> int:
    """
    Get total count of manufacturers in the database.

    Returns the count of all manufacturers in manufacturer_rankings table.
    This reflects the actual number of valid makes after filtering.
    """
    cur = conn.execute("SELECT COUNT(*) as total FROM manufacturer_rankings")
    row = cur.fetchone()
    return row['total'] if row else 0


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


def get_models_aggregated(conn, make: str, config: dict = None) -> list:
    """Get models aggregated across all years/variants."""
    cfg = config or DEFAULT_CONFIG
    min_tests = cfg["min_tests"]

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
        HAVING SUM(total_tests) >= ?
        ORDER BY pass_rate DESC
    """, (make, min_tests))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_core_models_aggregated(conn, make: str, config: dict = None) -> list:
    """Get core model names aggregated (strips variants like 'CIVIC SR VTEC').

    Fixes Issue 2: Uses higher minimum test threshold (MIN_TESTS_BEST_MODELS)
    and filters out motorhomes, classic cars, and pre-1980 vehicles.
    """
    # Use higher threshold for best models list
    min_tests = MIN_TESTS_BEST_MODELS

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
            HAVING SUM(total_tests) >= ?
        """, (core, make, core, core, min_tests))
        row = cur.fetchone()
        if row and row["total_tests"]:
            data = dict_from_row(row)
            # Filter out motorhomes, classic cars, and pre-1980 vehicles
            if is_excluded_model(data["core_model"], data.get("year_from")):
                continue
            results.append(data)

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


def get_model_family_year_breakdown(conn, make: str, core_model: str, config: dict = None) -> list:
    """Get year-by-year breakdown for a model family (including variants).

    Uses YEAR-SPECIFIC national averages for comparison, so a 2020 model
    is compared against other 2020 vehicles, not the overall average.
    """
    cfg = config or DEFAULT_CONFIG
    min_tests = cfg["min_tests"]
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
        HAVING SUM(total_tests) >= ?
        ORDER BY model_year DESC, fuel_type
    """, (make, core_model, core_model, min_tests))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"])[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)
    return results


def get_fuel_type_breakdown(conn, make: str) -> list:
    """Get pass rates by fuel type for this make.

    Fixes Issue 3: Filters out invalid fuel codes (ST, LN, FC etc) and
    fuel types with insufficient test data.
    """
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

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        fuel_code = data["fuel_type"]

        # Filter out invalid fuel codes
        if fuel_code not in VALID_FUEL_TYPES:
            continue

        # Filter out fuel types with insufficient test data
        if data["total_tests"] < MIN_TESTS_FUEL_TYPE:
            continue

        data["fuel_name"] = FUEL_TYPE_NAMES.get(fuel_code, fuel_code)
        results.append(data)

    return results


def get_best_models(conn, make: str, config: dict = None) -> list:
    """Get best performing models using YEAR-ADJUSTED scoring.

    Ranks models by how much they exceed the national average for their
    model year, not by raw pass rate. This prevents newer vehicles from
    dominating simply because all new cars pass more often.

    Returns ALL qualifying models (no limit) - downstream can slice as needed.
    """
    cfg = config or DEFAULT_CONFIG
    min_tests = cfg["min_tests"]
    yearly_avgs = get_yearly_national_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            total_tests, pass_rate
        FROM vehicle_insights
        WHERE make = ? AND total_tests >= ?
    """, (make, min_tests))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        # Filter out motorhomes and vehicles older than cutoff year
        if is_excluded_model(data["model"], model_year=data["model_year"]):
            continue
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"], cfg)[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)

    # Sort by performance vs year average (not raw pass rate)
    results.sort(key=lambda x: x["pass_rate_vs_national"], reverse=True)
    return results


def get_worst_models(conn, make: str, config: dict = None) -> list:
    """Get worst performing models using YEAR-ADJUSTED scoring.

    Ranks models by how much they fall below the national average for their
    model year. This identifies genuinely problematic vehicles, not just
    old ones that naturally have lower pass rates.

    Returns ALL qualifying models (no limit) - downstream can slice as needed.
    """
    cfg = config or DEFAULT_CONFIG
    min_tests = cfg["min_tests"]
    yearly_avgs = get_yearly_national_averages(conn)

    cur = conn.execute("""
        SELECT
            model, model_year, fuel_type,
            total_tests, pass_rate
        FROM vehicle_insights
        WHERE make = ? AND total_tests >= ?
    """, (make, min_tests))

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        # Filter out motorhomes and vehicles older than cutoff year
        if is_excluded_model(data["model"], model_year=data["model_year"]):
            continue
        year_avg = get_year_avg_safe(yearly_avgs, data["model_year"], cfg)[0]
        data["pass_rate_vs_national"] = round(data["pass_rate"] - year_avg, 2)
        data["national_avg_for_year"] = round(year_avg, 2)
        results.append(data)

    # Sort by performance vs year average (worst first)
    results.sort(key=lambda x: x["pass_rate_vs_national"])
    return results


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


def get_top_defects(conn, make: str, defect_type: str = "failure") -> list:
    """Get top defects (failures or advisories) for this make.

    Returns ALL defects sorted by occurrence - downstream can slice as needed.
    """
    cur = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE make = ? AND defect_type = ?
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
    """, (make, defect_type))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_dangerous_defects(conn, make: str) -> list:
    """Get dangerous defects for this make.

    Returns ALL dangerous defects sorted by occurrence - downstream can slice as needed.
    """
    cur = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences
        FROM dangerous_defects
        WHERE make = ?
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
    """, (make,))
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


# =============================================================================
# OBJECTIVE AGE BAND ANALYSIS
# =============================================================================
# These functions provide objective, data-driven age band analysis without
# subjective labels or ratings. Users can draw their own conclusions.
#
# Key principles:
# - Present data objectively with comparisons to national averages
# - Always show sample sizes and confidence indicators
# - No subjective labels like "champion", "avoid", "excellent"
# - Appropriate caveats for smaller sample sizes in older bands
# =============================================================================


def get_age_band_performance(conn, make: str, min_tests: int = None) -> dict:
    """
    Get objective pass rate performance by age band for a make.

    Compares make's pass rate at each age band against national average
    for the same age band. Returns data with confidence indicators.

    Args:
        conn: Database connection
        make: Vehicle make (e.g., "FORD")
        min_tests: Minimum tests to include (default: MIN_TESTS_DEFAULT)

    Returns:
        Dict with methodology, national_benchmarks, and make_performance by band
    """
    if min_tests is None:
        min_tests = MIN_TESTS_DEFAULT

    # Get national benchmarks
    national = get_national_age_benchmarks(conn)

    # Query all vehicles for this make
    cur = conn.execute("""
        SELECT
            model_year,
            SUM(total_tests) as total_tests,
            SUM(total_passes) as total_passes
        FROM vehicle_insights
        WHERE make = ? AND model_year IS NOT NULL
        GROUP BY model_year
    """, (make,))

    # Aggregate by age band
    band_data = defaultdict(lambda: {"total_tests": 0, "total_passes": 0})

    for row in cur.fetchall():
        age_band, band_order = calculate_age_band(row["model_year"])
        if age_band is None:
            continue

        band_data[band_order]["total_tests"] += row["total_tests"]
        band_data[band_order]["total_passes"] += row["total_passes"]
        band_data[band_order]["age_band"] = age_band

    # Build results
    bands = {}
    for band_order in sorted(band_data.keys()):
        data = band_data[band_order]
        age_band = data["age_band"]

        if data["total_tests"] < min_tests:
            continue

        make_pass_rate = (data["total_passes"] / data["total_tests"]) * 100
        national_data = national.get(age_band, {})
        national_pass_rate = national_data.get("pass_rate", NATIONAL_AVG_BY_BAND.get(band_order, 70.0))

        confidence = get_sample_confidence(data["total_tests"])

        bands[age_band] = {
            "band_order": band_order,
            "make_pass_rate": round(make_pass_rate, 2),
            "national_pass_rate": round(national_pass_rate, 2),
            "vs_national": round(make_pass_rate - national_pass_rate, 2),
            "total_tests": data["total_tests"],
            "confidence": confidence["level"],
            "sample_note": confidence["note"]
        }

    return {
        "methodology": "Pass rates compared to national average for vehicles of the same age. "
                       "Positive vs_national indicates above-average performance for that age band.",
        "reference_year": REFERENCE_YEAR,
        "national_benchmarks": national,
        "make_performance": bands
    }


def get_model_age_band_breakdown(conn, make: str, min_tests: int = None) -> list:
    """
    Get per-model performance breakdown by age band.

    For each model, shows pass rate at each age band compared to national average.
    Allows users to see which specific models perform well/poorly at different ages.

    Args:
        conn: Database connection
        make: Vehicle make (e.g., "FORD")
        min_tests: Minimum tests per model/band to include (default: MIN_TESTS_DEFAULT)

    Returns:
        List of models with their age band performance data
    """
    if min_tests is None:
        min_tests = MIN_TESTS_DEFAULT

    # Get national benchmarks
    national = get_national_age_benchmarks(conn)
    national_by_order = get_weighted_age_band_averages(conn)

    # Query all vehicles for this make, grouped by core model and model_year
    # First, get unique models
    cur = conn.execute("""
        SELECT DISTINCT model FROM vehicle_insights WHERE make = ?
    """, (make,))
    all_models = [row["model"] for row in cur.fetchall()]

    # Identify core model names (shortest version of each family)
    core_names = set()
    for model in sorted(all_models, key=len):
        is_variant = any(model.startswith(core + " ") for core in core_names)
        if not is_variant:
            core_names.add(model)

    results = []

    for core_model in sorted(core_names):
        # Check if model is a motorhome (by name)
        first_word = core_model.split()[0].upper()
        if first_word in MOTORHOME_BRANDS:
            continue

        # Get data for this model family
        cur = conn.execute("""
            SELECT
                model_year,
                SUM(total_tests) as total_tests,
                SUM(total_passes) as total_passes
            FROM vehicle_insights
            WHERE make = ? AND (model = ? OR model LIKE ? || ' %')
              AND model_year IS NOT NULL
              AND model_year >= ?
            GROUP BY model_year
        """, (make, core_model, core_model, EXCLUSION_YEAR_CUTOFF))

        # Aggregate by age band
        band_data = defaultdict(lambda: {"total_tests": 0, "total_passes": 0})
        total_model_tests = 0

        for row in cur.fetchall():
            age_band, band_order = calculate_age_band(row["model_year"])
            if age_band is None:
                continue

            band_data[band_order]["total_tests"] += row["total_tests"]
            band_data[band_order]["total_passes"] += row["total_passes"]
            band_data[band_order]["age_band"] = age_band
            total_model_tests += row["total_tests"]

        # Skip models with insufficient total data
        if total_model_tests < min_tests:
            continue

        # Build band breakdown for this model
        age_bands = []
        for band_order in sorted(band_data.keys()):
            data = band_data[band_order]

            if data["total_tests"] < min_tests:
                continue

            pass_rate = (data["total_passes"] / data["total_tests"]) * 100
            national_rate = national_by_order.get(band_order, NATIONAL_AVG_BY_BAND.get(band_order, 70.0))
            confidence = get_sample_confidence(data["total_tests"])

            age_bands.append({
                "age_band": data["age_band"],
                "band_order": band_order,
                "pass_rate": round(pass_rate, 2),
                "national_pass_rate": round(national_rate, 2),
                "vs_national": round(pass_rate - national_rate, 2),
                "total_tests": data["total_tests"],
                "confidence": confidence["level"],
                "sample_note": confidence["note"]
            })

        if age_bands:
            # Calculate overall model confidence
            model_confidence = get_sample_confidence(total_model_tests)

            results.append({
                "core_model": core_model,
                "total_tests": total_model_tests,
                "confidence": model_confidence["level"],
                "age_bands_available": len(age_bands),
                "age_bands": age_bands
            })

    # Sort by total tests (most data first)
    results.sort(key=lambda x: x["total_tests"], reverse=True)
    return results


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

    # =================================================================
    # OBJECTIVE AGE BAND ANALYSIS
    # =================================================================
    # Provides objective data on pass rates by vehicle age, compared
    # to national averages. No subjective labels - users draw conclusions.
    # =================================================================

    # Get make-level age band performance vs national
    age_band_performance = get_age_band_performance(conn, make)

    # Get per-model age band breakdown
    model_age_breakdown = get_model_age_band_breakdown(conn, make)

    # Get filtered rank among major manufacturers (min 10,000 tests)
    # Fixes Issue 1: Returns accurate rank/total by only counting qualifying manufacturers
    filtered_rank, filtered_total = get_manufacturer_rank_filtered(conn, make, min_tests=10000)

    # Get actual total manufacturer count (all valid makes in database)
    total_manufacturers = get_total_manufacturer_count(conn)

    conn.close()

    # Build output structure
    return {
        "meta": {
            "make": make,
            "generated_at": datetime.now().isoformat(),
            "database": str(DB_PATH.name),
            "national_pass_rate": national.get("overall_pass_rate", 71.51),
            "methodology_version": "3.0",
            "data_source_year": REFERENCE_YEAR,
            "methodology_note": "Objective age band analysis: pass rates compared to national averages "
                               "for vehicles of the same age. No subjective ratings - data presented "
                               "with confidence indicators based on sample size."
        },
        "overview": overview,
        "competitors": competitors,
        "summary": {
            "total_tests": overview["total_tests"],
            "total_models": overview["total_models"],
            "avg_pass_rate": overview["avg_pass_rate"],
            "rank": overview["rank"],
            "rank_total": total_manufacturers,
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
        # Objective age band analysis - no subjective labels
        "age_band_analysis": {
            "description": "Pass rates by vehicle age compared to national averages. "
                           "Positive vs_national values indicate above-average performance for that age band.",
            "confidence_levels": {
                "high": "1,000+ tests - statistically robust",
                "medium": "200-999 tests - reasonable confidence",
                "low": "50-199 tests - interpret with caution",
                "insufficient": "<50 tests - excluded from analysis"
            },
            "age_bands": {
                "3-7 years": "New vehicles - most pass easily, limited differentiation",
                "8-10 years": "Maturing - issues start emerging, meaningful comparisons",
                "11-14 years": "Established - solid long-term data",
                "15-17 years": "Long-term - smaller samples expected",
                "18-20 years": "Veteran - notable longevity, sample caveats apply",
                "21+ years": "Classic - very small samples, often collector vehicles"
            },
            "make_performance": age_band_performance,
            "model_breakdown": model_age_breakdown
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
