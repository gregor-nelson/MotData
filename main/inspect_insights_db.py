"""
MOT Insights Database Inspector
===============================
Inspects the mot_insights.db to understand table structures and data formats
for frontend integration planning.

Usage:
    python inspect_insights_db.py
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent / "mot_insights.db"


def get_table_schema(cursor, table_name):
    """Get column names and types for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [(row[1], row[2], "NOT NULL" if row[3] else "", "PK" if row[5] else "")
            for row in cursor.fetchall()]


def get_sample_rows(cursor, table_name, limit=3):
    """Get sample rows from a table."""
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    return cursor.fetchall()


def get_table_stats(cursor, table_name):
    """Get basic statistics for a table."""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    return count


def get_column_stats(cursor, table_name, column_name, column_type):
    """Get statistics for a specific column."""
    stats = {}

    try:
        # For numeric columns
        if any(t in column_type.upper() for t in ['INT', 'REAL', 'FLOAT', 'NUMERIC']):
            cursor.execute(f"SELECT MIN({column_name}), MAX({column_name}), AVG({column_name}) FROM {table_name}")
            min_val, max_val, avg_val = cursor.fetchone()
            stats['min'] = min_val
            stats['max'] = max_val
            stats['avg'] = round(avg_val, 2) if avg_val else None

        # For text columns - get distinct count and sample values
        if 'TEXT' in column_type.upper() or 'VARCHAR' in column_type.upper():
            cursor.execute(f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name}")
            stats['distinct_count'] = cursor.fetchone()[0]

            cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT 10")
            stats['sample_values'] = [row[0] for row in cursor.fetchall()]

        # Null count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            stats['null_count'] = null_count

    except Exception as e:
        stats['error'] = str(e)

    return stats


def inspect_vehicle_lookup_example(cursor):
    """Show example of how to look up a specific vehicle."""
    print("\n" + "=" * 80)
    print("EXAMPLE: Looking up a specific vehicle (FORD FOCUS 2018 Petrol)")
    print("=" * 80)

    make, model, year, fuel = "FORD", "FOCUS", 2018, "PE"

    # Core insights
    cursor.execute("""
        SELECT * FROM vehicle_insights
        WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
    """, (make, model, year, fuel))
    row = cursor.fetchone()

    if row:
        columns = [desc[0] for desc in cursor.description]
        print("\n[vehicle_insights]")
        for col, val in zip(columns, row):
            print(f"  {col}: {val}")
    else:
        print("  No data found for this combination")
        # Try to find similar
        cursor.execute("""
            SELECT make, model, model_year, fuel_type, total_tests
            FROM vehicle_insights
            WHERE make = ? AND model LIKE ?
            ORDER BY total_tests DESC LIMIT 5
        """, (make, f"%{model}%"))
        print("  Similar vehicles found:")
        for row in cursor.fetchall():
            print(f"    {row}")
        return

    # Top failure categories
    cursor.execute("""
        SELECT category_name, failure_count, failure_percentage, rank
        FROM failure_categories
        WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
        ORDER BY rank LIMIT 5
    """, (make, model, year, fuel))
    print("\n[failure_categories] Top 5:")
    for row in cursor.fetchall():
        print(f"  #{row[3]}: {row[0]} - {row[1]} failures ({row[2]}%)")

    # Top defects
    cursor.execute("""
        SELECT defect_description, defect_type, occurrence_count, occurrence_percentage, rank
        FROM top_defects
        WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
        ORDER BY defect_type, rank LIMIT 10
    """, (make, model, year, fuel))
    print("\n[top_defects] Top failures and advisories:")
    for row in cursor.fetchall():
        print(f"  [{row[1]}] #{row[4]}: {row[0][:50]}... - {row[2]} ({row[3]}%)")

    # Rankings
    cursor.execute("""
        SELECT ranking_type, rank, total_in_category, pass_rate
        FROM vehicle_rankings
        WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
    """, (make, model, year, fuel))
    print("\n[vehicle_rankings]:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: #{row[1]} of {row[2]} (pass rate: {row[3]}%)")

    # Mileage bands
    cursor.execute("""
        SELECT mileage_band, total_tests, pass_rate, avg_mileage
        FROM mileage_bands
        WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
        ORDER BY band_order
    """, (make, model, year, fuel))
    print("\n[mileage_bands]:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} tests, {row[2]}% pass rate, avg {row[3]:,.0f} miles" if row[3] else f"  {row[0]}: {row[1]} tests, {row[2]}% pass rate")


def inspect_api_query_examples(cursor):
    """Show example queries that would be useful for an API."""
    print("\n" + "=" * 80)
    print("USEFUL API QUERY PATTERNS")
    print("=" * 80)

    # 1. Search for available vehicles
    print("\n1. Search available vehicles by make:")
    print("   Query: SELECT DISTINCT model, model_year, fuel_type, total_tests")
    print("          FROM available_vehicles WHERE make = ? ORDER BY model, model_year")
    cursor.execute("""
        SELECT DISTINCT model, model_year, fuel_type, total_tests
        FROM available_vehicles
        WHERE make = 'BMW'
        ORDER BY model, model_year DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   -> {row[0]} {row[1]} ({row[2]}): {row[3]:,} tests")

    # 2. Compare vehicles by pass rate
    print("\n2. Top 10 vehicles by pass rate (2020 models):")
    cursor.execute("""
        SELECT make, model, fuel_type, pass_rate, total_tests
        FROM vehicle_insights
        WHERE model_year = 2020
        ORDER BY pass_rate DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} {row[1]} ({row[2]}): {row[3]}% ({row[4]:,} tests)")

    # 3. Worst vehicles by pass rate
    print("\n3. Bottom 10 vehicles by pass rate (2020 models):")
    cursor.execute("""
        SELECT make, model, fuel_type, pass_rate, total_tests
        FROM vehicle_insights
        WHERE model_year = 2020
        ORDER BY pass_rate ASC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} {row[1]} ({row[2]}): {row[3]}% ({row[4]:,} tests)")

    # 4. Manufacturer rankings
    print("\n4. Top 10 manufacturers by weighted pass rate:")
    cursor.execute("""
        SELECT make, weighted_pass_rate, total_tests, total_models, best_model, worst_model
        FROM manufacturer_rankings
        ORDER BY rank
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}% (tests: {row[2]:,}, models: {row[3]})")
        print(f"      Best: {row[4]}, Worst: {row[5]}")

    # 5. Common dangerous defects
    print("\n5. Most common dangerous defects (all vehicles):")
    cursor.execute("""
        SELECT defect_description, category_name, SUM(occurrence_count) as total
        FROM dangerous_defects
        GROUP BY rfr_id, defect_description, category_name
        ORDER BY total DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   {row[0][:60]}... [{row[1]}]: {row[2]:,}")


def generate_typescript_interfaces(cursor):
    """Generate TypeScript interfaces for the database tables."""
    print("\n" + "=" * 80)
    print("TYPESCRIPT INTERFACES FOR FRONTEND")
    print("=" * 80)

    type_mapping = {
        'INTEGER': 'number',
        'REAL': 'number',
        'TEXT': 'string',
        'BLOB': 'Uint8Array',
    }

    # Key tables for frontend
    key_tables = [
        'vehicle_insights',
        'failure_categories',
        'top_defects',
        'mileage_bands',
        'vehicle_rankings',
        'manufacturer_rankings',
        'dangerous_defects',
        'available_vehicles',
        'national_averages',
    ]

    print("\n// Auto-generated TypeScript interfaces from mot_insights.db\n")

    for table in key_tables:
        schema = get_table_schema(cursor, table)

        # Convert to PascalCase
        interface_name = ''.join(word.capitalize() for word in table.split('_'))

        print(f"export interface {interface_name} {{")
        for col_name, col_type, nullable, pk in schema:
            ts_type = type_mapping.get(col_type.upper(), 'unknown')
            optional = '?' if not nullable and not pk else ''
            # Handle nullable columns
            if not nullable and not pk:
                ts_type += ' | null'
            print(f"  {col_name}: {ts_type};")
        print("}\n")


def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print("=" * 80)
    print("MOT INSIGHTS DATABASE INSPECTION REPORT")
    print("=" * 80)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Tables: {len(tables)}")
    print(f"Tables: {', '.join(tables)}")

    # Detailed inspection of each table
    for table in tables:
        print("\n" + "-" * 80)
        print(f"TABLE: {table}")
        print("-" * 80)

        # Schema
        schema = get_table_schema(cursor, table)
        print("\nSchema:")
        for col_name, col_type, nullable, pk in schema:
            flags = ' '.join(filter(None, [pk, nullable]))
            print(f"  {col_name}: {col_type} {flags}".strip())

        # Stats
        row_count = get_table_stats(cursor, table)
        print(f"\nRow count: {row_count:,}")

        # Sample data
        print("\nSample data (first 3 rows):")
        columns = [s[0] for s in schema]
        samples = get_sample_rows(cursor, table, 3)
        for i, row in enumerate(samples):
            print(f"\n  Row {i+1}:")
            for col, val in zip(columns, row):
                val_str = str(val)[:60] + "..." if len(str(val)) > 60 else str(val)
                print(f"    {col}: {val_str}")

        # Column statistics for key columns
        print("\nColumn statistics:")
        for col_name, col_type, _, _ in schema:
            if col_name == 'id':
                continue
            stats = get_column_stats(cursor, table, col_name, col_type)
            if stats:
                stats_str = ', '.join(f"{k}={v}" for k, v in stats.items() if k != 'sample_values')
                print(f"  {col_name}: {stats_str}")
                if 'sample_values' in stats and len(stats['sample_values']) <= 10:
                    print(f"    values: {stats['sample_values']}")

    # Example vehicle lookup
    inspect_vehicle_lookup_example(cursor)

    # API query examples
    inspect_api_query_examples(cursor)

    # TypeScript interfaces
    generate_typescript_interfaces(cursor)

    # Summary of what's available for frontend
    print("\n" + "=" * 80)
    print("FRONTEND DATA AVAILABILITY SUMMARY")
    print("=" * 80)

    cursor.execute("SELECT COUNT(DISTINCT make) FROM vehicle_insights")
    makes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT model) FROM vehicle_insights")
    models = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(model_year), MAX(model_year) FROM vehicle_insights")
    min_year, max_year = cursor.fetchone()

    cursor.execute("SELECT DISTINCT fuel_type FROM vehicle_insights")
    fuel_types = [row[0] for row in cursor.fetchall()]

    print(f"""
Available Data:
  - Makes: {makes}
  - Models: {models}
  - Years: {min_year} - {max_year}
  - Fuel types: {fuel_types}
  - Vehicle combinations: {len(tables)} insight types per vehicle

Key Lookup Tables:
  - available_vehicles: Index of all queryable make/model/year/fuel combinations
  - vehicle_insights: Core pass rates and statistics
  - failure_categories: Top 10 failure categories per vehicle
  - top_defects: Top 10 failures + top 10 advisories per vehicle
  - dangerous_defects: Safety-critical issues
  - mileage_bands: Pass rates by mileage
  - age_bands: Pass rates by vehicle age
  - vehicle_rankings: Comparative rankings (overall, within make, within year)
  - manufacturer_rankings: Brand-level comparisons

Suggested API Endpoints:
  GET /api/vehicles?make=FORD                    -> available_vehicles
  GET /api/vehicle/FORD/FOCUS/2018/PE           -> vehicle_insights + related
  GET /api/rankings/manufacturers               -> manufacturer_rankings
  GET /api/rankings/vehicles?year=2020          -> vehicle_insights sorted
  GET /api/defects/dangerous?make=FORD          -> dangerous_defects
  GET /api/national/averages                    -> national_averages
""")

    conn.close()
    print("\nInspection complete!")


if __name__ == "__main__":
    main()
