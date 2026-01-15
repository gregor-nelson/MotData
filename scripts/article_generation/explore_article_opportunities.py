#!/usr/bin/env python3
"""
MOT Insights Explorer - Find Article Opportunities
===================================================
Identifies makes/models with interesting data stories for articles.

Usage:
    python explore_article_opportunities.py
    python explore_article_opportunities.py --focus reliability
    python explore_article_opportunities.py --focus problems
"""

import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"


def get_connection():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def explore_best_manufacturers():
    """Find most reliable manufacturers."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  TOP 15 MOST RELIABLE MANUFACTURERS")
    print("="*60)

    cur = conn.execute("""
        SELECT make, avg_pass_rate, total_tests, total_models, rank,
               best_model, best_model_pass_rate
        FROM manufacturer_rankings
        WHERE total_tests >= 50000
        ORDER BY avg_pass_rate DESC
        LIMIT 15
    """)

    print(f"\n{'Make':<18} {'Pass %':>8} {'Tests':>12} {'Rank':>6}  Best Model")
    print("-"*75)
    for row in cur:
        print(f"{row['make']:<18} {row['avg_pass_rate']:>7.1f}% {row['total_tests']:>11,} #{row['rank']:>4}  {row['best_model'][:20]}")

    conn.close()


def explore_worst_manufacturers():
    """Find least reliable manufacturers."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  BOTTOM 15 MANUFACTURERS (min 10k tests)")
    print("="*60)

    cur = conn.execute("""
        SELECT make, avg_pass_rate, total_tests, rank,
               worst_model, worst_model_pass_rate
        FROM manufacturer_rankings
        WHERE total_tests >= 10000
        ORDER BY avg_pass_rate ASC
        LIMIT 15
    """)

    print(f"\n{'Make':<18} {'Pass %':>8} {'Tests':>12} {'Rank':>6}  Worst Model")
    print("-"*75)
    for row in cur:
        print(f"{row['make']:<18} {row['avg_pass_rate']:>7.1f}% {row['total_tests']:>11,} #{row['rank']:>4}  {row['worst_model'][:20]}")

    conn.close()


def explore_problem_vehicles():
    """Find vehicles with worst pass rates."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  WORST 25 VEHICLES (min 1000 tests)")
    print("="*60)

    cur = conn.execute("""
        SELECT make, model, model_year, fuel_type, pass_rate, total_tests
        FROM vehicle_insights
        WHERE total_tests >= 1000
        ORDER BY pass_rate ASC
        LIMIT 25
    """)

    print(f"\n{'Make':<12} {'Model':<20} {'Year':>5} {'Fuel':>4} {'Pass %':>8} {'Tests':>10}")
    print("-"*70)
    for row in cur:
        print(f"{row['make']:<12} {row['model'][:20]:<20} {row['model_year']:>5} {row['fuel_type']:>4} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}")

    conn.close()


def explore_best_vehicles():
    """Find vehicles with best pass rates."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  BEST 25 VEHICLES (min 1000 tests)")
    print("="*60)

    cur = conn.execute("""
        SELECT make, model, model_year, fuel_type, pass_rate, total_tests
        FROM vehicle_insights
        WHERE total_tests >= 1000
        ORDER BY pass_rate DESC
        LIMIT 25
    """)

    print(f"\n{'Make':<12} {'Model':<20} {'Year':>5} {'Fuel':>4} {'Pass %':>8} {'Tests':>10}")
    print("-"*70)
    for row in cur:
        print(f"{row['make']:<12} {row['model'][:20]:<20} {row['model_year']:>5} {row['fuel_type']:>4} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}")

    conn.close()


def explore_hybrid_advantage():
    """Compare hybrid vs petrol vs diesel by make."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  HYBRID ADVANTAGE BY MAKE")
    print("="*60)

    cur = conn.execute("""
        SELECT
            make,
            SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END) as hybrid_tests,
            ROUND(SUM(CASE WHEN fuel_type = 'HY' THEN total_passes ELSE 0 END) * 100.0 /
                  NULLIF(SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END), 0), 1) as hybrid_rate,
            ROUND(SUM(CASE WHEN fuel_type = 'PE' THEN total_passes ELSE 0 END) * 100.0 /
                  NULLIF(SUM(CASE WHEN fuel_type = 'PE' THEN total_tests ELSE 0 END), 0), 1) as petrol_rate,
            ROUND(SUM(CASE WHEN fuel_type = 'DI' THEN total_passes ELSE 0 END) * 100.0 /
                  NULLIF(SUM(CASE WHEN fuel_type = 'DI' THEN total_tests ELSE 0 END), 0), 1) as diesel_rate
        FROM vehicle_insights
        GROUP BY make
        HAVING hybrid_tests >= 1000
        ORDER BY hybrid_rate DESC
    """)

    print(f"\n{'Make':<18} {'Hybrid %':>10} {'Petrol %':>10} {'Diesel %':>10} {'HY Adv':>8}")
    print("-"*60)
    for row in cur:
        hybrid = row['hybrid_rate'] or 0
        petrol = row['petrol_rate'] or 0
        advantage = hybrid - petrol if petrol else 0
        print(f"{row['make']:<18} {hybrid:>9.1f}% {petrol:>9.1f}% {row['diesel_rate'] or 0:>9.1f}% {advantage:>+7.1f}%")

    conn.close()


def explore_ev_reliability():
    """Electric vehicle reliability."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  ELECTRIC VEHICLE RELIABILITY")
    print("="*60)

    cur = conn.execute("""
        SELECT make, model, model_year, pass_rate, total_tests
        FROM vehicle_insights
        WHERE fuel_type = 'EL' AND total_tests >= 100
        ORDER BY pass_rate DESC
        LIMIT 20
    """)

    print(f"\n{'Make':<12} {'Model':<25} {'Year':>5} {'Pass %':>8} {'Tests':>8}")
    print("-"*65)
    for row in cur:
        print(f"{row['make']:<12} {row['model'][:25]:<25} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>7,}")

    conn.close()


def explore_year_trends():
    """Pass rates by model year."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  PASS RATES BY MODEL YEAR (all makes)")
    print("="*60)

    cur = conn.execute("""
        SELECT
            model_year,
            SUM(total_tests) as tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
        FROM vehicle_insights
        GROUP BY model_year
        ORDER BY model_year DESC
    """)

    print(f"\n{'Year':>6} {'Pass Rate':>10} {'Tests':>14}")
    print("-"*35)
    for row in cur:
        bar = "#" * int(row['pass_rate'] / 5)
        print(f"{row['model_year']:>6} {row['pass_rate']:>9.1f}% {row['tests']:>13,}  {bar}")

    conn.close()


def explore_diesels_to_avoid():
    """Worst diesel models (common search)."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  WORST DIESEL MODELS (min 2000 tests)")
    print("="*60)

    cur = conn.execute("""
        SELECT make, model, model_year, pass_rate, total_tests
        FROM vehicle_insights
        WHERE fuel_type = 'DI' AND total_tests >= 2000
        ORDER BY pass_rate ASC
        LIMIT 20
    """)

    print(f"\n{'Make':<12} {'Model':<22} {'Year':>5} {'Pass %':>8} {'Tests':>10}")
    print("-"*65)
    for row in cur:
        print(f"{row['make']:<12} {row['model'][:22]:<22} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}")

    conn.close()


def explore_first_cars():
    """Best first cars (common search)."""
    conn = get_connection()
    print("\n" + "="*60)
    print("  BEST FIRST CARS (small cars, 2015+, high volume)")
    print("="*60)

    # Common first car models
    first_car_models = [
        ('FORD', 'FIESTA'), ('VAUXHALL', 'CORSA'), ('VOLKSWAGEN', 'POLO'),
        ('TOYOTA', 'YARIS'), ('HONDA', 'JAZZ'), ('PEUGEOT', '208'),
        ('RENAULT', 'CLIO'), ('CITROEN', 'C1'), ('HYUNDAI', 'I10'),
        ('KIA', 'PICANTO'), ('SUZUKI', 'SWIFT'), ('MINI', 'MINI'),
        ('FIAT', '500'), ('SEAT', 'IBIZA'), ('SKODA', 'FABIA')
    ]

    print(f"\n{'Make':<12} {'Model':<15} {'Year':>5} {'Pass %':>8} {'Tests':>10}")
    print("-"*55)

    for make, model in first_car_models:
        cur = conn.execute("""
            SELECT model_year, pass_rate, total_tests
            FROM vehicle_insights
            WHERE make = ? AND model = ? AND fuel_type = 'PE'
              AND model_year >= 2015 AND total_tests >= 1000
            ORDER BY pass_rate DESC
            LIMIT 1
        """, (make, model))
        row = cur.fetchone()
        if row:
            print(f"{make:<12} {model:<15} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}")

    conn.close()


def explore_article_ideas():
    """Generate article ideas based on data patterns."""
    print("\n" + "="*60)
    print("  ARTICLE IDEAS BASED ON DATA PATTERNS")
    print("="*60)

    ideas = [
        ("Most Reliable [MAKE] Models", "Per-make deep dives, do Toyota, Honda, BMW first"),
        ("Worst Cars to Buy: MOT Failure Data", "Nissan Qashqai 2007-09, Vauxhall Zafira, etc."),
        ("Best First Cars by MOT Pass Rate", "Jazz, Yaris, Polo comparison"),
        ("Diesel vs Petrol vs Hybrid: Which Lasts?", "Fuel type reliability comparison"),
        ("SUVs That Fail MOTs Most Often", "Qashqai, Sportage, Tucson analysis"),
        ("Electric Cars: Are They Reliable?", "Tesla, Leaf, Zoe, e-Golf data"),
        ("The Mileage Sweet Spot", "When do cars start failing?"),
        ("Best Used Cars Under 10 Years Old", "2015+ high pass rate vehicles"),
        ("Premium vs Budget: Who's More Reliable?", "BMW/Audi vs Ford/Vauxhall"),
        ("Japanese vs German vs Korean", "Brand origin reliability comparison"),
        ("The Hybrid Advantage: Real Data", "Hybrid pass rates vs ICE"),
        ("Avoid These Model Years", "Specific year/model problem combos"),
    ]

    print()
    for title, description in ideas:
        print(f"  * {title}")
        print(f"    {description}\n")


def main():
    parser = argparse.ArgumentParser(description="Explore MOT data for article opportunities")
    parser.add_argument("--focus", choices=["reliability", "problems", "trends", "evs", "all"],
                       default="all", help="Focus area to explore")

    args = parser.parse_args()

    if args.focus == "all":
        explore_article_ideas()
        explore_best_manufacturers()
        explore_worst_manufacturers()
        explore_problem_vehicles()
        explore_best_vehicles()
        explore_hybrid_advantage()
        explore_diesels_to_avoid()
        explore_first_cars()
        explore_year_trends()
    elif args.focus == "reliability":
        explore_best_manufacturers()
        explore_best_vehicles()
        explore_hybrid_advantage()
    elif args.focus == "problems":
        explore_worst_manufacturers()
        explore_problem_vehicles()
        explore_diesels_to_avoid()
    elif args.focus == "trends":
        explore_year_trends()
        explore_hybrid_advantage()
    elif args.focus == "evs":
        explore_ev_reliability()


if __name__ == "__main__":
    main()
