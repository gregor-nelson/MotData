#!/usr/bin/env python3
"""
Dangerous Defects Article Insights Generator
=============================================
Generates comprehensive insights for "Most Dangerous Cars on UK Roads" article.
Uses the dangerous_defects table to identify vehicles with highest safety-critical failure rates.

Usage:
    python generate_dangerous_defects_insights.py
    python generate_dangerous_defects_insights.py --output ./custom_path.json
    python generate_dangerous_defects_insights.py --pretty
"""

import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime


# Database path (relative to script location)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"


def get_connection():
    """Create read-only database connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert sqlite3.Row to dict."""
    return dict(zip(row.keys(), row)) if row else None


# Fuel type display names
FUEL_NAMES = {
    "PE": "Petrol",
    "DI": "Diesel",
    "HY": "Hybrid",
    "EL": "Electric",
    "ED": "Plug-in Hybrid",
    "GB": "Gas Bi-fuel",
    "OT": "Other"
}


def _calculate_diesel_petrol_gap(fuel_comparison: list) -> str | None:
    """Calculate diesel vs petrol gap by explicitly finding each fuel type."""
    diesel = next((f for f in fuel_comparison if f.get('fuel_type') == 'DI'), None)
    petrol = next((f for f in fuel_comparison if f.get('fuel_type') == 'PE'), None)
    if diesel and petrol:
        gap = diesel['dangerous_rate'] - petrol['dangerous_rate']
        sign = '+' if gap >= 0 else ''
        return f"{sign}{round(gap, 2)}%"
    return None


def get_overall_statistics(conn) -> dict:
    """Get high-level statistics about dangerous defects."""
    # Total dangerous defect occurrences
    cur = conn.execute("""
        SELECT
            COUNT(*) as total_records,
            SUM(occurrence_count) as total_occurrences,
            COUNT(DISTINCT make) as unique_makes,
            COUNT(DISTINCT make || model) as unique_models,
            COUNT(DISTINCT make || model || model_year || fuel_type) as unique_variants
        FROM dangerous_defects
    """)
    totals = dict_from_row(cur.fetchone())

    # Total MOT tests for context
    cur = conn.execute("SELECT SUM(total_tests) as total_tests FROM vehicle_insights")
    totals["total_mot_tests"] = cur.fetchone()["total_tests"]

    # Overall dangerous defect rate (LEFT JOIN to include all vehicles)
    cur = conn.execute("""
        SELECT
            COALESCE(SUM(dd.occurrence_count), 0) as dangerous,
            SUM(vi.total_tests) as tests
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
    """)
    row = cur.fetchone()
    totals["overall_dangerous_rate"] = round(row["dangerous"] * 100.0 / row["tests"], 2) if row["tests"] else 0

    return totals


def get_category_breakdown(conn) -> list:
    """Get dangerous defects broken down by category."""
    # Get total occurrences first
    total_occurrences = conn.execute(
        "SELECT SUM(occurrence_count) as total FROM dangerous_defects"
    ).fetchone()["total"] or 0

    # Include fuel_type in variant count for accuracy
    cur = conn.execute("""
        SELECT
            category_name,
            COUNT(DISTINCT make || model || model_year || fuel_type) as vehicle_variants,
            SUM(occurrence_count) as total_occurrences,
            COUNT(DISTINCT defect_description) as unique_defects
        FROM dangerous_defects
        GROUP BY category_name
        ORDER BY total_occurrences DESC
    """)

    results = []
    for row in cur:
        data = dict_from_row(row)
        data["percentage_of_all"] = round(data["total_occurrences"] * 100.0 / total_occurrences, 1)
        results.append(data)

    return results


def get_top_defect_descriptions(conn, limit: int = 20) -> list:
    """Get the most common specific dangerous defects."""
    cur = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences,
            COUNT(DISTINCT make || model) as affected_models
        FROM dangerous_defects
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
        LIMIT ?
    """, (limit,))
    return [dict_from_row(row) for row in cur.fetchall()]


def get_rankings_by_make(conn, min_tests: int = 50000) -> list:
    """Get dangerous defect rates by manufacturer (includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.make,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 3) as dangerous_rate,
            COUNT(DISTINCT vi.model || vi.model_year || vi.fuel_type) as variants_with_data
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        GROUP BY vi.make
        HAVING SUM(vi.total_tests) >= ?
        ORDER BY dangerous_rate DESC
    """, (min_tests,))

    results = [dict_from_row(row) for row in cur.fetchall()]

    # Add rank
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results


def get_rankings_by_model(conn, min_tests: int = 100000) -> list:
    """Get dangerous defect rates by model (aggregated across years, includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.make, vi.model,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 2) as dangerous_rate,
            MIN(vi.model_year) as year_from,
            MAX(vi.model_year) as year_to
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        GROUP BY vi.make, vi.model
        HAVING SUM(vi.total_tests) >= ?
        ORDER BY dangerous_rate DESC
    """, (min_tests,))

    results = [dict_from_row(row) for row in cur.fetchall()]
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results


def get_worst_vehicles_by_year_range(conn, year_from: int, year_to: int, min_tests: int = 2000, limit: int = 25) -> list:
    """Get worst vehicles within a specific model year range (includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.make, vi.model, vi.model_year, vi.fuel_type,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            vi.total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / vi.total_tests, 1) as dangerous_rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.total_tests >= ? AND vi.model_year BETWEEN ? AND ?
        GROUP BY vi.make, vi.model, vi.model_year, vi.fuel_type, vi.total_tests
        ORDER BY dangerous_rate DESC
        LIMIT ?
    """, (min_tests, year_from, year_to, limit))

    results = [dict_from_row(row) for row in cur.fetchall()]
    for r in results:
        r["fuel_name"] = FUEL_NAMES.get(r["fuel_type"], r["fuel_type"])

    return results


def get_safest_vehicles_by_year_range(conn, year_from: int, year_to: int, min_tests: int = 2000, limit: int = 25) -> list:
    """Get safest vehicles within a specific model year range (includes vehicles with zero defects)."""
    cur = conn.execute("""
        SELECT
            vi.make, vi.model, vi.model_year, vi.fuel_type,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            vi.total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / vi.total_tests, 1) as dangerous_rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.total_tests >= ? AND vi.model_year BETWEEN ? AND ?
        GROUP BY vi.make, vi.model, vi.model_year, vi.fuel_type, vi.total_tests
        ORDER BY dangerous_rate ASC
        LIMIT ?
    """, (min_tests, year_from, year_to, limit))

    results = [dict_from_row(row) for row in cur.fetchall()]
    for r in results:
        r["fuel_name"] = FUEL_NAMES.get(r["fuel_type"], r["fuel_type"])

    return results


def get_fuel_type_comparison(conn) -> list:
    """Get dangerous defect rates by fuel type (includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.fuel_type,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 2) as dangerous_rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.fuel_type IN ('PE', 'DI', 'HY', 'EL')
        GROUP BY vi.fuel_type
        ORDER BY dangerous_rate DESC
    """)

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        data["fuel_name"] = FUEL_NAMES.get(data["fuel_type"], data["fuel_type"])
        results.append(data)

    return results


def get_diesel_vs_petrol_same_model(conn, min_tests: int = 1000, limit: int = 25) -> list:
    """Compare diesel vs petrol rates for the same make/model/year (includes all vehicles)."""
    cur = conn.execute("""
        WITH rates AS (
            SELECT
                vi.make, vi.model, vi.model_year, vi.fuel_type,
                COALESCE(SUM(dd.occurrence_count), 0) as dangerous,
                vi.total_tests,
                ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / vi.total_tests, 1) as rate
            FROM vehicle_insights vi
            LEFT JOIN dangerous_defects dd
                ON vi.make = dd.make
                AND vi.model = dd.model
                AND vi.model_year = dd.model_year
                AND vi.fuel_type = dd.fuel_type
            WHERE vi.total_tests >= ? AND vi.fuel_type IN ('PE', 'DI')
            GROUP BY vi.make, vi.model, vi.model_year, vi.fuel_type, vi.total_tests
        )
        SELECT
            p.make, p.model, p.model_year,
            p.rate as petrol_rate,
            p.total_tests as petrol_tests,
            d.rate as diesel_rate,
            d.total_tests as diesel_tests,
            ROUND(d.rate - p.rate, 1) as diesel_difference
        FROM rates p
        JOIN rates d ON p.make = d.make AND p.model = d.model AND p.model_year = d.model_year
        WHERE p.fuel_type = 'PE' AND d.fuel_type = 'DI'
        ORDER BY diesel_difference DESC
        LIMIT ?
    """, (min_tests, limit))

    return [dict_from_row(row) for row in cur.fetchall()]


def get_age_controlled_comparison(conn, model_year: int, min_tests: int = 10000) -> list:
    """Get make rankings for a specific model year (controls for age, includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.make,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 2) as dangerous_rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.model_year = ?
        GROUP BY vi.make
        HAVING SUM(vi.total_tests) >= ?
        ORDER BY dangerous_rate DESC
    """, (model_year, min_tests))

    results = [dict_from_row(row) for row in cur.fetchall()]
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results


def get_category_rates_by_make(conn, category: str, model_year: int = None, min_tests: int = 10000, limit: int = 20) -> list:
    """Get rates for a specific defect category by make (includes all vehicles)."""
    if model_year:
        cur = conn.execute("""
            SELECT
                vi.make,
                COALESCE(SUM(dd.occurrence_count), 0) as category_dangerous,
                SUM(vi.total_tests) as total_tests,
                ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 3) as category_rate
            FROM vehicle_insights vi
            LEFT JOIN dangerous_defects dd
                ON vi.make = dd.make
                AND vi.model = dd.model
                AND vi.model_year = dd.model_year
                AND vi.fuel_type = dd.fuel_type
                AND dd.category_name = ?
            WHERE vi.model_year = ?
            GROUP BY vi.make
            HAVING SUM(vi.total_tests) >= ?
            ORDER BY category_rate DESC
            LIMIT ?
        """, (category, model_year, min_tests, limit))
    else:
        cur = conn.execute("""
            SELECT
                vi.make,
                COALESCE(SUM(dd.occurrence_count), 0) as category_dangerous,
                SUM(vi.total_tests) as total_tests,
                ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 3) as category_rate
            FROM vehicle_insights vi
            LEFT JOIN dangerous_defects dd
                ON vi.make = dd.make
                AND vi.model = dd.model
                AND vi.model_year = dd.model_year
                AND vi.fuel_type = dd.fuel_type
                AND dd.category_name = ?
            GROUP BY vi.make
            HAVING SUM(vi.total_tests) >= ?
            ORDER BY category_rate DESC
            LIMIT ?
        """, (category, min_tests, limit))

    return [dict_from_row(row) for row in cur.fetchall()]


def get_vehicle_deep_dive(conn, make: str, model: str) -> dict:
    """Get detailed dangerous defect breakdown for a specific vehicle (includes all variants)."""
    # Overall stats (LEFT JOIN to include variants with zero defects)
    cur = conn.execute("""
        SELECT
            vi.make, vi.model,
            COALESCE(SUM(dd.occurrence_count), 0) as total_dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 2) as dangerous_rate,
            MIN(vi.model_year) as year_from,
            MAX(vi.model_year) as year_to
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.make = ? AND vi.model = ?
        GROUP BY vi.make, vi.model
    """, (make, model))

    overview = dict_from_row(cur.fetchone())
    if not overview:
        return None

    # By category
    cur = conn.execute("""
        SELECT
            category_name,
            SUM(occurrence_count) as occurrences
        FROM dangerous_defects
        WHERE make = ? AND model = ?
        GROUP BY category_name
        ORDER BY occurrences DESC
    """, (make, model))
    categories = [dict_from_row(row) for row in cur.fetchall()]

    # Top specific defects
    cur = conn.execute("""
        SELECT
            defect_description, category_name,
            SUM(occurrence_count) as occurrences
        FROM dangerous_defects
        WHERE make = ? AND model = ?
        GROUP BY defect_description, category_name
        ORDER BY occurrences DESC
        LIMIT 15
    """, (make, model))
    top_defects = [dict_from_row(row) for row in cur.fetchall()]

    # By model year (aggregate across fuel types, includes zero-defect years)
    cur = conn.execute("""
        SELECT
            vi.model_year,
            COALESCE(SUM(dd.occurrence_count), 0) as dangerous,
            SUM(vi.total_tests) as total_tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 1) as rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        WHERE vi.make = ? AND vi.model = ?
        GROUP BY vi.model_year
        HAVING SUM(vi.total_tests) >= 500
        ORDER BY vi.model_year DESC
    """, (make, model))
    by_year = [dict_from_row(row) for row in cur.fetchall()]

    return {
        "overview": overview,
        "by_category": categories,
        "top_defects": top_defects,
        "by_model_year": by_year
    }


def get_popular_cars_ranked(conn, min_tests: int = 100000) -> list:
    """Get popular cars ranked by dangerous defect rate (includes all vehicles)."""
    cur = conn.execute("""
        SELECT
            vi.make, vi.model,
            COALESCE(SUM(dd.occurrence_count), 0) as dangerous,
            SUM(vi.total_tests) as tests,
            ROUND(COALESCE(SUM(dd.occurrence_count), 0) * 100.0 / SUM(vi.total_tests), 2) as rate
        FROM vehicle_insights vi
        LEFT JOIN dangerous_defects dd
            ON vi.make = dd.make
            AND vi.model = dd.model
            AND vi.model_year = dd.model_year
            AND vi.fuel_type = dd.fuel_type
        GROUP BY vi.make, vi.model
        HAVING SUM(vi.total_tests) >= ?
        ORDER BY rate DESC
    """, (min_tests,))

    results = [dict_from_row(row) for row in cur.fetchall()]
    for i, r in enumerate(results, 1):
        r["rank"] = i
        r["rank_total"] = len(results)

    return results


def generate_dangerous_defects_insights() -> dict:
    """Generate complete insights for the dangerous defects article."""
    conn = get_connection()

    # Overall statistics
    overall = get_overall_statistics(conn)

    # Category breakdown
    categories = get_category_breakdown(conn)

    # Top specific defects
    top_defects = get_top_defect_descriptions(conn, limit=20)

    # Rankings by make
    rankings_by_make = get_rankings_by_make(conn)

    # Rankings by model (popular cars)
    rankings_by_model = get_rankings_by_model(conn)

    # Popular cars full ranking
    popular_cars_ranked = get_popular_cars_ranked(conn)

    # Fuel type comparison
    fuel_comparison = get_fuel_type_comparison(conn)

    # Diesel vs Petrol direct comparison
    diesel_vs_petrol = get_diesel_vs_petrol_same_model(conn)

    # Age-controlled comparisons (2015 is a good reference year - 10 years old)
    age_controlled_2015 = get_age_controlled_comparison(conn, 2015)

    # Worst vehicles by year range (used car buyer focus)
    worst_2015_2017 = get_worst_vehicles_by_year_range(conn, 2015, 2017)
    worst_2018_2020 = get_worst_vehicles_by_year_range(conn, 2018, 2020)

    # Safest vehicles by year range
    safest_2015_2017 = get_safest_vehicles_by_year_range(conn, 2015, 2017)
    safest_2018_2020 = get_safest_vehicles_by_year_range(conn, 2018, 2020)

    # Category-specific rankings (most safety-critical)
    brakes_by_make = get_category_rates_by_make(conn, "Brakes")
    steering_by_make = get_category_rates_by_make(conn, "Steering")
    suspension_by_make = get_category_rates_by_make(conn, "Suspension")
    tyres_by_make = get_category_rates_by_make(conn, "Tyres")

    # Deep dives into notable vehicles
    deep_dives = {}

    # Worst performers
    notable_vehicles = [
        ("NISSAN", "QASHQAI"),  # Very popular, high rate
        ("VAUXHALL", "ZAFIRA"),  # Family car, high rate
        ("FORD", "S-MAX"),  # Family MPV
        ("FORD", "FOCUS"),  # Most popular car
    ]

    # Safest performers
    safe_vehicles = [
        ("TOYOTA", "PRIUS"),  # Safest mainstream
        ("MAZDA", "MX-5"),  # Sports car
        ("PORSCHE", "911"),  # Premium
        ("LAND ROVER", "DEFENDER"),  # Surprisingly safe
    ]

    for make, model in notable_vehicles + safe_vehicles:
        dive = get_vehicle_deep_dive(conn, make, model)
        if dive:
            deep_dives[f"{make}_{model}"] = dive

    conn.close()

    # Build output structure
    return {
        "meta": {
            "article_type": "dangerous_defects",
            "title": "The Most Dangerous Cars on UK Roads",
            "subtitle": "Official DVSA MOT Data Analysis",
            "generated_at": datetime.now().isoformat(),
            "database": str(DB_PATH.name),
            "methodology": {
                "description": "Analysis of dangerous defects recorded during MOT tests",
                "dangerous_defects_definition": "Defects classified as 'Dangerous' by DVSA - vehicle should not be driven until fixed",
                "rate_calculation": "Number of dangerous defect occurrences / Total MOT tests * 100",
                "note": "A single test can have multiple dangerous defects"
            }
        },
        "key_findings": {
            "total_dangerous_occurrences": overall["total_occurrences"],
            "total_mot_tests_analysed": overall["total_mot_tests"],
            "overall_dangerous_rate": overall["overall_dangerous_rate"],
            "rate_range": {
                "lowest": popular_cars_ranked[-1] if popular_cars_ranked else None,
                "highest": popular_cars_ranked[0] if popular_cars_ranked else None,
                "difference_factor": round(popular_cars_ranked[0]["rate"] / popular_cars_ranked[-1]["rate"], 1) if popular_cars_ranked else None
            },
            "headline_stats": {
                "worst_make": rankings_by_make[0] if rankings_by_make else None,
                "safest_make": rankings_by_make[-1] if rankings_by_make else None,
                "diesel_vs_petrol_gap": _calculate_diesel_petrol_gap(fuel_comparison)
            }
        },
        "overall_statistics": overall,
        "category_breakdown": categories,
        "top_dangerous_defects": top_defects,
        "rankings": {
            "by_make": rankings_by_make,
            "by_model": rankings_by_model,
            "popular_cars_full_ranking": popular_cars_ranked
        },
        "fuel_type_analysis": {
            "comparison": fuel_comparison,
            "diesel_vs_petrol_same_model": diesel_vs_petrol,
            "insight": "Diesel vehicles consistently show higher dangerous defect rates than petrol equivalents"
        },
        "age_controlled_analysis": {
            "description": "Comparing vehicles of the same model year removes age as a confounding factor",
            "model_year_2015": age_controlled_2015
        },
        "used_car_buyer_guide": {
            "worst_to_avoid": {
                "2015_2017": worst_2015_2017,
                "2018_2020": worst_2018_2020
            },
            "safest_choices": {
                "2015_2017": safest_2015_2017,
                "2018_2020": safest_2018_2020
            }
        },
        "category_deep_dives": {
            "brakes": {
                "description": "Brake-related dangerous defects by make",
                "rankings": brakes_by_make
            },
            "steering": {
                "description": "Steering-related dangerous defects by make",
                "rankings": steering_by_make
            },
            "suspension": {
                "description": "Suspension-related dangerous defects by make",
                "rankings": suspension_by_make
            },
            "tyres": {
                "description": "Tyre-related dangerous defects by make",
                "rankings": tyres_by_make
            }
        },
        "vehicle_deep_dives": deep_dives
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate dangerous defects insights for article",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--output", "-o", help="Output JSON file path",
                        default=str(Path(__file__).parent / "dangerous_defects_insights.json"))
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON output")

    args = parser.parse_args()

    print("Generating dangerous defects insights...")
    print(f"Database: {DB_PATH}")

    # Generate insights
    insights = generate_dangerous_defects_insights()

    # Determine output path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    indent = 2 if args.pretty else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=indent, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print("  DANGEROUS DEFECTS INSIGHTS GENERATED")
    print(f"{'='*60}")
    print(f"  Total Dangerous Occurrences: {insights['overall_statistics']['total_occurrences']:,}")
    print(f"  Total MOT Tests:             {insights['overall_statistics']['total_mot_tests']:,}")
    print(f"  Overall Rate:                {insights['overall_statistics']['overall_dangerous_rate']}%")
    print(f"{'='*60}")
    print(f"  Categories:                  {len(insights['category_breakdown'])}")
    print(f"  Makes Ranked:                {len(insights['rankings']['by_make'])}")
    print(f"  Models Ranked:               {len(insights['rankings']['by_model'])}")
    print(f"  Popular Cars Full Ranking:   {len(insights['rankings']['popular_cars_full_ranking'])}")
    print(f"  Vehicle Deep Dives:          {len(insights['vehicle_deep_dives'])}")
    print(f"{'='*60}")

    kf = insights['key_findings']
    if kf['rate_range']['highest'] and kf['rate_range']['lowest']:
        print(f"  Worst Model:  {kf['rate_range']['highest']['make']} {kf['rate_range']['highest']['model']} ({kf['rate_range']['highest']['rate']}%)")
        print(f"  Safest Model: {kf['rate_range']['lowest']['make']} {kf['rate_range']['lowest']['model']} ({kf['rate_range']['lowest']['rate']}%)")
        print(f"  Difference:   {kf['rate_range']['difference_factor']}x")

    print(f"{'='*60}")
    print(f"\n  Output: {output_path.absolute()}")
    print(f"  Size:   {output_path.stat().st_size:,} bytes")
    print()


if __name__ == "__main__":
    main()
