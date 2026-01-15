"""
MOT Insights Generator - OPTIMIZED VERSION
===========================================
Processes DVSA MOT bulk data (2023) and generates aggregated insights
for motorwise.io vehicle reports.

OPTIMIZATION: Uses bulk SQL GROUP BY operations instead of per-vehicle loops.
Expected runtime: 10-30 minutes (vs hours for original)
Expected memory: ~10-12GB (vs exhausting 16GB)

Usage:
    pip install duckdb
    python generate_insights_optimized.py

Output:
    mot_insights.db (SQLite database with all aggregated insights)
"""

import duckdb
import sqlite3
import os
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent
OUTPUT_DB = DATA_DIR / "mot_insights.db"
DUCKDB_FILE = DATA_DIR / "mot_processing.duckdb"  # Disk-backed for lower RAM
MIN_SAMPLE_SIZE = 100

# Performance tuning - optimized for 8GB VPS
DUCKDB_THREADS = 2            # Fewer threads = less memory pressure
DUCKDB_MEMORY_LIMIT = '4GB'   # Leave ~3.5GB for OS, Python, disk spillover

# Mileage bands (in miles)
MILEAGE_BANDS = [
    (0, 30000, "0-30k", 0),
    (30001, 60000, "30k-60k", 1),
    (60001, 90000, "60k-90k", 2),
    (90001, 120000, "90k-120k", 3),
    (120001, 150000, "120k-150k", 4),
    (150001, 999999999, "150k+", 5),
]

# Age bands (in years)
AGE_BANDS = [
    (3, 4, "3-4 years", 0),
    (5, 6, "5-6 years", 1),
    (7, 8, "7-8 years", 2),
    (9, 10, "9-10 years", 3),
    (11, 12, "11-12 years", 4),
    (13, 99, "13+ years", 5),
]


# =============================================================================
# DATABASE SETUP
# =============================================================================

def create_duckdb_connection():
    """Create disk-backed DuckDB connection and import CSV files."""
    print("=" * 60)
    print("MOT INSIGHTS GENERATOR - OPTIMIZED")
    print("=" * 60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Output database: {OUTPUT_DB}")
    print(f"Minimum sample size: {MIN_SAMPLE_SIZE}")
    print(f"DuckDB threads: {DUCKDB_THREADS}")
    print(f"DuckDB memory limit: {DUCKDB_MEMORY_LIMIT}")

    # Remove old DuckDB file if exists
    if DUCKDB_FILE.exists():
        os.remove(DUCKDB_FILE)

    # Create disk-backed connection (not in-memory) for lower RAM usage
    conn = duckdb.connect(str(DUCKDB_FILE))

    # Configure performance settings
    conn.execute(f"SET threads = {DUCKDB_THREADS}")
    conn.execute(f"SET memory_limit = '{DUCKDB_MEMORY_LIMIT}'")

    print("\n[1/20] Importing CSV files into DuckDB...")

    # Import main tables
    csv_files = {
        "test_result": "test_result.csv",
        "test_item": "test_item.csv",
        "item_detail": "item_detail.csv",
        "item_group": "item_group.csv",
        "mdr_fuel_types": "mdr_fuel_types.csv",
        "mdr_rfr_location": "mdr_rfr_location.csv",
        "mdr_test_outcome": "mdr_test_outcome.csv",
        "mdr_test_type": "mdr_test_type.csv",
    }

    for table_name, filename in csv_files.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            print(f"  Importing {filename}...", end=" ", flush=True)
            # Use single quotes for Windows path compatibility
            filepath_str = str(filepath).replace('\\', '/')
            conn.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{filepath_str}', delim='|', header=true)
            """)
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"({count:,} rows)")
        else:
            print(f"  WARNING: {filename} not found, skipping...")

    return conn


def create_base_tests_table(conn):
    """Create a filtered base table for reuse in all queries."""
    print("\n[2/20] Creating filtered base_tests table...")

    conn.execute("""
        CREATE TABLE base_tests AS
        SELECT
            tr.test_id,
            tr.vehicle_id,
            tr.test_date,
            tr.test_result,
            tr.test_mileage,
            tr.postcode_area,
            tr.make,
            tr.model,
            tr.fuel_type,
            tr.first_use_date,
            YEAR(tr.first_use_date) as model_year,
            FLOOR(DATEDIFF('day', tr.first_use_date, tr.test_date) / 365.25) as vehicle_age
        FROM test_result tr
        WHERE tr.test_type = 'NT'
          AND tr.test_result IN ('P', 'F', 'PRS')
          AND CAST(tr.test_class_id AS VARCHAR) = '4'
          AND tr.first_use_date != '1971-01-01'
          AND YEAR(tr.first_use_date) >= 2000
          AND tr.make != 'UNCLASSIFIED'
    """)

    count = conn.execute("SELECT COUNT(*) FROM base_tests").fetchone()[0]
    print(f"  Created base_tests with {count:,} filtered records")

    # Create index for faster joins
    conn.execute("CREATE INDEX idx_base_tests_id ON base_tests(test_id)")
    conn.execute("CREATE INDEX idx_base_tests_vehicle ON base_tests(make, model, model_year, fuel_type)")
    print("  Created indexes on base_tests")

    return count


def create_output_database():
    """Create SQLite output database with schema."""
    if OUTPUT_DB.exists():
        os.remove(OUTPUT_DB)

    sqlite_conn = sqlite3.connect(OUTPUT_DB)
    cursor = sqlite_conn.cursor()

    # Core vehicle insights table
    cursor.execute("""
        CREATE TABLE vehicle_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            total_tests INTEGER NOT NULL,
            total_passes INTEGER NOT NULL,
            total_fails INTEGER NOT NULL,
            total_prs INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            initial_failure_rate REAL NOT NULL,
            avg_mileage REAL,
            avg_age_years REAL,
            national_pass_rate REAL,
            pass_rate_vs_national REAL,
            UNIQUE(make, model, model_year, fuel_type)
        )
    """)

    # Top failure categories
    cursor.execute("""
        CREATE TABLE failure_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            category_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            failure_count INTEGER NOT NULL,
            failure_percentage REAL NOT NULL,
            rank INTEGER NOT NULL
        )
    """)

    # Top specific defects
    cursor.execute("""
        CREATE TABLE top_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            rfr_id INTEGER NOT NULL,
            defect_description TEXT NOT NULL,
            category_name TEXT,
            defect_type TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            occurrence_percentage REAL NOT NULL,
            rank INTEGER NOT NULL
        )
    """)

    # Mileage band analysis
    cursor.execute("""
        CREATE TABLE mileage_bands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            mileage_band TEXT NOT NULL,
            band_order INTEGER NOT NULL,
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            avg_mileage REAL
        )
    """)

    # Advisory to failure progression
    cursor.execute("""
        CREATE TABLE advisory_progression (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            category_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            advisory_count INTEGER NOT NULL,
            progressed_to_failure INTEGER NOT NULL,
            progression_rate REAL NOT NULL,
            avg_days_to_failure REAL,
            avg_miles_to_failure REAL
        )
    """)

    # Geographic insights
    cursor.execute("""
        CREATE TABLE geographic_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            postcode_area TEXT NOT NULL,
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL
        )
    """)

    # Defect locations
    cursor.execute("""
        CREATE TABLE defect_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            location_id INTEGER NOT NULL,
            lateral TEXT,
            longitudinal TEXT,
            vertical TEXT,
            failure_count INTEGER NOT NULL,
            failure_percentage REAL NOT NULL
        )
    """)

    # Dangerous defects - serious safety issues
    cursor.execute("""
        CREATE TABLE dangerous_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            rfr_id INTEGER NOT NULL,
            defect_description TEXT NOT NULL,
            category_name TEXT,
            occurrence_count INTEGER NOT NULL,
            occurrence_percentage REAL NOT NULL,
            rank INTEGER NOT NULL
        )
    """)

    # Age band analysis (complement to mileage bands)
    cursor.execute("""
        CREATE TABLE age_bands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            age_band TEXT NOT NULL,
            band_order INTEGER NOT NULL,
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            avg_mileage REAL
        )
    """)

    # First MOT vs subsequent MOT comparison
    cursor.execute("""
        CREATE TABLE first_mot_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            mot_type TEXT NOT NULL,  -- 'first' or 'subsequent'
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            avg_mileage REAL,
            avg_defects_per_fail REAL
        )
    """)

    # Manufacturer-level rankings (aggregate by make only)
    cursor.execute("""
        CREATE TABLE manufacturer_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            total_tests INTEGER NOT NULL,
            total_models INTEGER NOT NULL,
            avg_pass_rate REAL NOT NULL,
            weighted_pass_rate REAL NOT NULL,
            best_model TEXT,
            best_model_pass_rate REAL,
            worst_model TEXT,
            worst_model_pass_rate REAL,
            rank INTEGER NOT NULL,
            UNIQUE(make)
        )
    """)

    # Seasonal patterns (monthly/quarterly pass rates)
    cursor.execute("""
        CREATE TABLE seasonal_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            month INTEGER NOT NULL,  -- 1-12
            quarter INTEGER NOT NULL,  -- 1-4
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL
        )
    """)

    # Failure severity breakdown (Minor/Major/Dangerous)
    cursor.execute("""
        CREATE TABLE failure_severity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            severity TEXT NOT NULL,  -- 'minor', 'major', 'dangerous'
            failure_count INTEGER NOT NULL,
            failure_percentage REAL NOT NULL
        )
    """)

    # Retest success rates
    cursor.execute("""
        CREATE TABLE retest_success (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            failed_tests INTEGER NOT NULL,
            retested_within_30_days INTEGER NOT NULL,
            passed_on_retest INTEGER NOT NULL,
            retest_rate REAL NOT NULL,
            retest_success_rate REAL NOT NULL
        )
    """)

    # Component failure mileage thresholds
    cursor.execute("""
        CREATE TABLE component_mileage_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            category_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            failure_rate_0_30k REAL,
            failure_rate_30_60k REAL,
            failure_rate_60_90k REAL,
            failure_rate_90_120k REAL,
            failure_rate_120_150k REAL,
            failure_rate_150k_plus REAL,
            spike_mileage_band TEXT,  -- band where failures increase significantly
            spike_increase_pct REAL   -- percentage increase at spike
        )
    """)

    # National seasonal averages (for comparison)
    cursor.execute("""
        CREATE TABLE national_seasonal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            total_tests INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            UNIQUE(month)
        )
    """)

    # National averages
    cursor.execute("""
        CREATE TABLE national_averages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            model_year INTEGER,
            fuel_type TEXT,
            description TEXT
        )
    """)

    # Comparative rankings
    cursor.execute("""
        CREATE TABLE vehicle_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            ranking_type TEXT NOT NULL,
            rank INTEGER NOT NULL,
            total_in_category INTEGER NOT NULL,
            pass_rate REAL NOT NULL
        )
    """)

    # Metadata for available vehicles
    cursor.execute("""
        CREATE TABLE available_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            model_year INTEGER NOT NULL,
            fuel_type TEXT,
            total_tests INTEGER NOT NULL,
            UNIQUE(make, model, model_year, fuel_type)
        )
    """)

    # Create indexes for fast lookups
    cursor.execute("CREATE INDEX idx_vi_lookup ON vehicle_insights(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_fc_lookup ON failure_categories(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_td_lookup ON top_defects(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_mb_lookup ON mileage_bands(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_ap_lookup ON advisory_progression(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_gi_lookup ON geographic_insights(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_av_lookup ON available_vehicles(make, model, model_year)")
    cursor.execute("CREATE INDEX idx_dd_lookup ON dangerous_defects(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_ab_lookup ON age_bands(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_fmi_lookup ON first_mot_insights(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_mr_lookup ON manufacturer_rankings(make)")
    cursor.execute("CREATE INDEX idx_sp_lookup ON seasonal_patterns(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_fs_lookup ON failure_severity(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_rs_lookup ON retest_success(make, model, model_year, fuel_type)")
    cursor.execute("CREATE INDEX idx_cmt_lookup ON component_mileage_thresholds(make, model, model_year, fuel_type)")

    sqlite_conn.commit()
    return sqlite_conn


# =============================================================================
# BULK INSIGHT GENERATION FUNCTIONS
# =============================================================================

def generate_national_averages(duck_conn, sqlite_conn):
    """Calculate national averages for benchmarking - BULK operation."""
    print("\n[3/20] Calculating national averages...")
    cursor = sqlite_conn.cursor()

    # Overall pass rate
    result = duck_conn.execute("""
        SELECT
            COUNT(*) as total_tests,
            SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) as passes,
            SUM(CASE WHEN test_result IN ('F', 'PRS') THEN 1 ELSE 0 END) as initial_failures,
            AVG(CASE WHEN test_mileage > 0 THEN test_mileage END) as avg_mileage
        FROM base_tests
    """).fetchone()

    total, passes, initial_failures, avg_mileage = result
    pass_rate = (passes / total) * 100 if total > 0 else 0
    initial_failure_rate = (initial_failures / total) * 100 if total > 0 else 0

    cursor.execute("INSERT INTO national_averages (metric_name, metric_value, description) VALUES (?, ?, ?)",
                   ("overall_pass_rate", pass_rate, "National pass rate for Class 4 vehicles"))
    cursor.execute("INSERT INTO national_averages (metric_name, metric_value, description) VALUES (?, ?, ?)",
                   ("overall_initial_failure_rate", initial_failure_rate, "National initial failure rate"))
    cursor.execute("INSERT INTO national_averages (metric_name, metric_value, description) VALUES (?, ?, ?)",
                   ("overall_avg_mileage", avg_mileage or 0, "National average mileage at test"))
    cursor.execute("INSERT INTO national_averages (metric_name, metric_value, description) VALUES (?, ?, ?)",
                   ("total_tests", total, "Total Class 4 normal tests in dataset"))

    print(f"  National pass rate: {pass_rate:.1f}%")
    print(f"  National initial failure rate: {initial_failure_rate:.1f}%")
    print(f"  Average mileage: {avg_mileage:,.0f} miles")
    print(f"  Total tests: {total:,}")

    # Pass rate by year - BULK
    yearly = duck_conn.execute("""
        SELECT
            model_year,
            COUNT(*) as total,
            100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
        FROM base_tests
        GROUP BY model_year
        HAVING COUNT(*) >= 1000
        ORDER BY model_year
    """).fetchall()

    for year, count, yr_pass_rate in yearly:
        cursor.execute(
            "INSERT INTO national_averages (metric_name, metric_value, model_year, description) VALUES (?, ?, ?, ?)",
            ("yearly_pass_rate", yr_pass_rate, year, f"National pass rate for {year} vehicles")
        )

    # Pass rate by fuel type - BULK
    by_fuel = duck_conn.execute("""
        SELECT
            fuel_type,
            COUNT(*) as total,
            100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
        FROM base_tests
        GROUP BY fuel_type
        HAVING COUNT(*) >= 1000
    """).fetchall()

    for fuel, count, fuel_pass_rate in by_fuel:
        cursor.execute(
            "INSERT INTO national_averages (metric_name, metric_value, fuel_type, description) VALUES (?, ?, ?, ?)",
            ("fuel_type_pass_rate", fuel_pass_rate, fuel, f"National pass rate for {fuel} vehicles")
        )

    sqlite_conn.commit()
    print(f"  Generated {len(yearly)} yearly benchmarks, {len(by_fuel)} fuel type benchmarks")

    return pass_rate  # Return for use in other calculations


def generate_vehicle_insights_bulk(duck_conn, sqlite_conn, national_pass_rate):
    """Generate core statistics for ALL vehicles in one bulk query."""
    print("\n[4/20] Generating core vehicle statistics (BULK)...")

    # Single bulk query for all vehicle combinations
    results = duck_conn.execute(f"""
        SELECT
            make,
            model,
            model_year,
            fuel_type,
            COUNT(*) as total_tests,
            SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) as passes,
            SUM(CASE WHEN test_result = 'F' THEN 1 ELSE 0 END) as fails,
            SUM(CASE WHEN test_result = 'PRS' THEN 1 ELSE 0 END) as prs,
            AVG(CASE WHEN test_mileage > 0 THEN test_mileage END) as avg_mileage,
            AVG(vehicle_age) as avg_age
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ORDER BY total_tests DESC
    """).fetchall()

    cursor = sqlite_conn.cursor()
    count = 0

    for row in results:
        make, model, year, fuel_type, tests, passes, fails, prs, avg_mileage, avg_age = row
        pass_rate = (passes / tests) * 100 if tests > 0 else 0
        initial_failure_rate = ((fails + prs) / tests) * 100 if tests > 0 else 0

        cursor.execute("""
            INSERT INTO vehicle_insights
            (make, model, model_year, fuel_type, total_tests, total_passes, total_fails,
             total_prs, pass_rate, initial_failure_rate, avg_mileage, avg_age_years,
             national_pass_rate, pass_rate_vs_national)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, tests, passes, fails, prs,
              round(pass_rate, 2), round(initial_failure_rate, 2),
              round(avg_mileage, 0) if avg_mileage else None,
              round(avg_age, 1) if avg_age else None,
              round(national_pass_rate, 2),
              round(pass_rate - national_pass_rate, 2)))

        # Also add to available_vehicles
        cursor.execute("""
            INSERT OR IGNORE INTO available_vehicles (make, model, model_year, fuel_type, total_tests)
            VALUES (?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, tests))

        count += 1

    sqlite_conn.commit()
    print(f"  Generated stats for {count:,} vehicle combinations")
    return count


def generate_failure_categories_bulk(duck_conn, sqlite_conn):
    """Generate top 10 failure categories per vehicle using window functions."""
    print("\n[5/20] Generating failure category breakdowns (BULK)...")

    # First, get vehicle totals for percentage calculation
    duck_conn.execute(f"""
        CREATE TEMP TABLE vehicle_totals AS
        SELECT make, model, model_year, fuel_type, COUNT(*) as total_tests
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
    """)

    # Bulk query with window function for top 10 per vehicle
    results = duck_conn.execute("""
        WITH category_counts AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                ig.test_item_set_section_id as category_id,
                ig.item_name as category_name,
                COUNT(DISTINCT bt.test_id) as failure_count
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                              AND CAST(ig.test_class_id AS VARCHAR) = '4'
            WHERE bt.test_result IN ('F', 'PRS')
              AND ti.rfr_type_code IN ('F', 'P')
              AND ig.parent_id = 0
              AND ig.test_item_id != 0
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type,
                     ig.test_item_set_section_id, ig.item_name
        ),
        ranked AS (
            SELECT
                cc.*,
                vt.total_tests,
                ROW_NUMBER() OVER (
                    PARTITION BY cc.make, cc.model, cc.model_year, cc.fuel_type
                    ORDER BY cc.failure_count DESC
                ) as rank
            FROM category_counts cc
            JOIN vehicle_totals vt ON cc.make = vt.make
                                   AND cc.model = vt.model
                                   AND cc.model_year = vt.model_year
                                   AND cc.fuel_type = vt.fuel_type
        )
        SELECT make, model, model_year, fuel_type, category_id, category_name,
               failure_count, total_tests, rank
        FROM ranked
        WHERE rank <= 10
        ORDER BY make, model, model_year, fuel_type, rank
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, cat_id, cat_name, count, total_tests, rank = row
        pct = (count / total_tests) * 100 if total_tests > 0 else 0
        cursor.execute("""
            INSERT INTO failure_categories
            (make, model, model_year, fuel_type, category_id, category_name,
             failure_count, failure_percentage, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, cat_id, cat_name, count, round(pct, 2), rank))

    duck_conn.execute("DROP TABLE IF EXISTS vehicle_totals")
    sqlite_conn.commit()
    print(f"  Generated {len(results):,} failure category entries")


def generate_top_defects_bulk(duck_conn, sqlite_conn):
    """Generate top 10 failures + top 10 advisories per vehicle using memory-efficient approach."""
    print("\n[6/20] Generating top specific defects (BULK)...")

    # Get vehicle totals
    duck_conn.execute(f"""
        CREATE TEMP TABLE vehicle_totals AS
        SELECT make, model, model_year, fuel_type, COUNT(*) as total_tests
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
    """)

    cursor = sqlite_conn.cursor()
    total_inserted = 0

    # =========================================================================
    # FAILURE DEFECTS - Memory-efficient approach using intermediate table
    # =========================================================================
    print("  Processing failure defects...", end=" ", flush=True)

    # Step 1: Create deduplicated intermediate table (can spill to disk)
    duck_conn.execute("""
        CREATE TEMP TABLE failure_test_defects AS
        SELECT DISTINCT
            bt.test_id,
            bt.make,
            bt.model,
            bt.model_year,
            bt.fuel_type,
            ti.rfr_id
        FROM base_tests bt
        JOIN test_item ti ON bt.test_id = ti.test_id
        WHERE ti.rfr_type_code IN ('F', 'P')
    """)

    # Step 2: Now count from the deduplicated table (much less memory)
    failures = duck_conn.execute("""
        WITH defect_counts AS (
            SELECT
                ftd.make,
                ftd.model,
                ftd.model_year,
                ftd.fuel_type,
                ftd.rfr_id,
                COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
                ig.item_name as category_name,
                COUNT(*) as occurrence_count
            FROM failure_test_defects ftd
            LEFT JOIN item_detail id ON ftd.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            LEFT JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                                   AND CAST(ig.test_class_id AS VARCHAR) = '4' AND ig.parent_id = 0
            GROUP BY ftd.make, ftd.model, ftd.model_year, ftd.fuel_type,
                     ftd.rfr_id, id.rfr_desc, ig.item_name
        ),
        ranked AS (
            SELECT
                dc.*,
                vt.total_tests,
                ROW_NUMBER() OVER (
                    PARTITION BY dc.make, dc.model, dc.model_year, dc.fuel_type
                    ORDER BY dc.occurrence_count DESC
                ) as rank
            FROM defect_counts dc
            JOIN vehicle_totals vt ON dc.make = vt.make
                                   AND dc.model = vt.model
                                   AND dc.model_year = vt.model_year
                                   AND dc.fuel_type = vt.fuel_type
        )
        SELECT make, model, model_year, fuel_type, rfr_id, defect_desc,
               category_name, occurrence_count, total_tests, rank
        FROM ranked
        WHERE rank <= 10
    """).fetchall()

    duck_conn.execute("DROP TABLE IF EXISTS failure_test_defects")

    for row in failures:
        make, model, year, fuel_type, rfr_id, desc, cat, count, total_tests, rank = row
        pct = (count / total_tests) * 100 if total_tests > 0 else 0
        cursor.execute("""
            INSERT INTO top_defects
            (make, model, model_year, fuel_type, rfr_id, defect_description, category_name,
             defect_type, occurrence_count, occurrence_percentage, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'failure', ?, ?, ?)
        """, (make, model, year, fuel_type, rfr_id, desc, cat, count, round(pct, 2), rank))
        total_inserted += 1

    print(f"{len(failures):,} entries")

    # =========================================================================
    # ADVISORY DEFECTS - Memory-efficient approach using intermediate table
    # =========================================================================
    print("  Processing advisory defects...", end=" ", flush=True)

    # Step 1: Create deduplicated intermediate table (can spill to disk)
    duck_conn.execute("""
        CREATE TEMP TABLE advisory_test_defects AS
        SELECT DISTINCT
            bt.test_id,
            bt.make,
            bt.model,
            bt.model_year,
            bt.fuel_type,
            ti.rfr_id
        FROM base_tests bt
        JOIN test_item ti ON bt.test_id = ti.test_id
        WHERE ti.rfr_type_code = 'A'
    """)

    # Step 2: Now count from the deduplicated table (much less memory)
    advisories = duck_conn.execute("""
        WITH defect_counts AS (
            SELECT
                atd.make,
                atd.model,
                atd.model_year,
                atd.fuel_type,
                atd.rfr_id,
                COALESCE(id.rfr_advisory_text, id.rfr_desc, 'Unknown') as defect_desc,
                ig.item_name as category_name,
                COUNT(*) as occurrence_count
            FROM advisory_test_defects atd
            LEFT JOIN item_detail id ON atd.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            LEFT JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                                   AND CAST(ig.test_class_id AS VARCHAR) = '4' AND ig.parent_id = 0
            GROUP BY atd.make, atd.model, atd.model_year, atd.fuel_type,
                     atd.rfr_id, defect_desc, ig.item_name
        ),
        ranked AS (
            SELECT
                dc.*,
                vt.total_tests,
                ROW_NUMBER() OVER (
                    PARTITION BY dc.make, dc.model, dc.model_year, dc.fuel_type
                    ORDER BY dc.occurrence_count DESC
                ) as rank
            FROM defect_counts dc
            JOIN vehicle_totals vt ON dc.make = vt.make
                                   AND dc.model = vt.model
                                   AND dc.model_year = vt.model_year
                                   AND dc.fuel_type = vt.fuel_type
        )
        SELECT make, model, model_year, fuel_type, rfr_id, defect_desc,
               category_name, occurrence_count, total_tests, rank
        FROM ranked
        WHERE rank <= 10
    """).fetchall()

    duck_conn.execute("DROP TABLE IF EXISTS advisory_test_defects")

    for row in advisories:
        make, model, year, fuel_type, rfr_id, desc, cat, count, total_tests, rank = row
        pct = (count / total_tests) * 100 if total_tests > 0 else 0
        cursor.execute("""
            INSERT INTO top_defects
            (make, model, model_year, fuel_type, rfr_id, defect_description, category_name,
             defect_type, occurrence_count, occurrence_percentage, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'advisory', ?, ?, ?)
        """, (make, model, year, fuel_type, rfr_id, desc, cat, count, round(pct, 2), rank))
        total_inserted += 1

    print(f"{len(advisories):,} entries")

    duck_conn.execute("DROP TABLE IF EXISTS vehicle_totals")
    sqlite_conn.commit()
    print(f"  Generated {total_inserted:,} total defect entries")


def generate_mileage_bands_bulk(duck_conn, sqlite_conn):
    """Generate pass rates by mileage band for all vehicles in bulk."""
    print("\n[7/20] Generating mileage band analysis (BULK)...")

    # Build CASE expression for mileage bands
    case_expr = "CASE "
    for low, high, label, order in MILEAGE_BANDS:
        case_expr += f"WHEN test_mileage >= {low} AND test_mileage <= {high} THEN '{label}' "
    case_expr += "END"

    order_expr = "CASE "
    for low, high, label, order in MILEAGE_BANDS:
        case_expr2 = f"WHEN test_mileage >= {low} AND test_mileage <= {high} THEN {order} "
        order_expr += case_expr2
    order_expr += "END"

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        mileage_stats AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                {case_expr} as mileage_band,
                {order_expr} as band_order,
                COUNT(*) as total_tests,
                SUM(CASE WHEN bt.test_result = 'P' THEN 1 ELSE 0 END) as passes,
                AVG(bt.test_mileage) as avg_mileage
            FROM base_tests bt
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE bt.test_mileage > 0
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, mileage_band, band_order
            HAVING COUNT(*) >= 10
        )
        SELECT make, model, model_year, fuel_type, mileage_band, band_order,
               total_tests, passes, avg_mileage
        FROM mileage_stats
        WHERE mileage_band IS NOT NULL
        ORDER BY make, model, model_year, fuel_type, band_order
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, band, order, tests, passes, avg_mileage = row
        pass_rate = (passes / tests) * 100 if tests > 0 else 0
        cursor.execute("""
            INSERT INTO mileage_bands
            (make, model, model_year, fuel_type, mileage_band, band_order,
             total_tests, pass_rate, avg_mileage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, band, order,
              tests, round(pass_rate, 2), round(avg_mileage, 0) if avg_mileage else None))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} mileage band entries")


def generate_geographic_insights_bulk(duck_conn, sqlite_conn):
    """Generate pass rates by postcode area for all vehicles in bulk."""
    print("\n[8/20] Generating geographic insights (BULK)...")

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        )
        SELECT
            bt.make,
            bt.model,
            bt.model_year,
            bt.fuel_type,
            bt.postcode_area,
            COUNT(*) as total_tests,
            100.0 * SUM(CASE WHEN bt.test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
        FROM base_tests bt
        JOIN vehicle_combos vc ON bt.make = vc.make
                               AND bt.model = vc.model
                               AND bt.model_year = vc.model_year
                               AND bt.fuel_type = vc.fuel_type
        WHERE bt.postcode_area != 'XX'
        GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, bt.postcode_area
        HAVING COUNT(*) >= 20
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, postcode, tests, pass_rate = row
        cursor.execute("""
            INSERT INTO geographic_insights
            (make, model, model_year, fuel_type, postcode_area, total_tests, pass_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, postcode, tests, round(pass_rate, 2)))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} geographic entries")


def generate_defect_locations_bulk(duck_conn, sqlite_conn):
    """Generate defect location breakdown for all vehicles in bulk."""
    print("\n[9/20] Generating defect location analysis (BULK)...")

    # Get location data with percentages using window functions
    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        location_counts AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                ti.location_id,
                loc."lateral" as lateral_pos,
                loc.longitudinal,
                loc.vertical,
                COUNT(*) as failure_count
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            LEFT JOIN mdr_rfr_location loc ON ti.location_id = loc.id
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE ti.rfr_type_code IN ('F', 'P')
              AND ti.location_id IS NOT NULL
              AND ti.location_id > 0
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type,
                     ti.location_id, loc."lateral", loc.longitudinal, loc.vertical
        ),
        with_totals AS (
            SELECT
                lc.*,
                SUM(lc.failure_count) OVER (
                    PARTITION BY lc.make, lc.model, lc.model_year, lc.fuel_type
                ) as vehicle_total,
                ROW_NUMBER() OVER (
                    PARTITION BY lc.make, lc.model, lc.model_year, lc.fuel_type
                    ORDER BY lc.failure_count DESC
                ) as rank
            FROM location_counts lc
        )
        SELECT make, model, model_year, fuel_type, location_id, lateral_pos,
               longitudinal, vertical, failure_count, vehicle_total
        FROM with_totals
        WHERE rank <= 20
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, loc_id, lateral, longitudinal, vertical, count, total = row
        pct = (count / total) * 100 if total > 0 else 0
        cursor.execute("""
            INSERT INTO defect_locations
            (make, model, model_year, fuel_type, location_id, lateral, longitudinal,
             vertical, failure_count, failure_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, loc_id, lateral, longitudinal,
              vertical, count, round(pct, 2)))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} location entries")


def generate_advisory_progression_bulk(duck_conn, sqlite_conn):
    """Track advisory to failure progression using bulk operations."""
    print("\n[10/20] Analyzing advisory-to-failure progression (BULK)...")
    print("  (This is the most complex analysis - may take several minutes)")

    # This is computationally intensive but still uses bulk operations
    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        advisory_tests AS (
            SELECT DISTINCT
                bt.vehicle_id,
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                bt.test_date AS advisory_date,
                bt.test_mileage AS advisory_mileage,
                id.test_item_set_section_id AS category_id,
                ig.item_name AS category_name
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                              AND CAST(ig.test_class_id AS VARCHAR) = '4'
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE ti.rfr_type_code = 'A'
              AND ig.parent_id = 0
              AND ig.test_item_id != 0
        ),
        failure_tests AS (
            SELECT DISTINCT
                bt.vehicle_id,
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                bt.test_date AS failure_date,
                bt.test_mileage AS failure_mileage,
                id.test_item_set_section_id AS category_id
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE ti.rfr_type_code IN ('F', 'P')
        ),
        progressions AS (
            SELECT
                a.make,
                a.model,
                a.model_year,
                a.fuel_type,
                a.category_id,
                a.category_name,
                a.vehicle_id,
                a.advisory_mileage,
                DATEDIFF('day', a.advisory_date, MIN(f.failure_date)) as days_to_failure,
                MIN(f.failure_mileage) - a.advisory_mileage as miles_to_failure
            FROM advisory_tests a
            JOIN failure_tests f ON a.vehicle_id = f.vehicle_id
                                AND a.category_id = f.category_id
                                AND a.make = f.make
                                AND a.model = f.model
                                AND a.model_year = f.model_year
                                AND a.fuel_type = f.fuel_type
                                AND f.failure_date > a.advisory_date
            GROUP BY a.make, a.model, a.model_year, a.fuel_type, a.category_id,
                     a.category_name, a.vehicle_id, a.advisory_mileage, a.advisory_date
        ),
        advisory_counts AS (
            SELECT make, model, model_year, fuel_type, category_id, category_name,
                   COUNT(DISTINCT vehicle_id) as advisory_count
            FROM advisory_tests
            GROUP BY make, model, model_year, fuel_type, category_id, category_name
        ),
        progression_stats AS (
            SELECT
                p.make,
                p.model,
                p.model_year,
                p.fuel_type,
                p.category_id,
                p.category_name,
                COUNT(DISTINCT p.vehicle_id) as progressed_count,
                AVG(p.days_to_failure) as avg_days,
                AVG(CASE WHEN p.miles_to_failure > 0 THEN p.miles_to_failure END) as avg_miles
            FROM progressions p
            GROUP BY p.make, p.model, p.model_year, p.fuel_type, p.category_id, p.category_name
            HAVING COUNT(DISTINCT p.vehicle_id) >= 5
        )
        SELECT
            ps.make,
            ps.model,
            ps.model_year,
            ps.fuel_type,
            ps.category_id,
            ps.category_name,
            ac.advisory_count,
            ps.progressed_count,
            ps.avg_days,
            ps.avg_miles
        FROM progression_stats ps
        JOIN advisory_counts ac ON ps.make = ac.make
                                AND ps.model = ac.model
                                AND ps.model_year = ac.model_year
                                AND ps.fuel_type = ac.fuel_type
                                AND ps.category_id = ac.category_id
        WHERE ac.advisory_count > 0
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, cat_id, cat_name, adv_count, prog_count, avg_days, avg_miles = row
        prog_rate = (prog_count / adv_count) * 100 if adv_count > 0 else 0
        cursor.execute("""
            INSERT INTO advisory_progression
            (make, model, model_year, fuel_type, category_id, category_name,
             advisory_count, progressed_to_failure, progression_rate,
             avg_days_to_failure, avg_miles_to_failure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, cat_id, cat_name,
              adv_count, prog_count, round(prog_rate, 2),
              round(avg_days, 0) if avg_days else None,
              round(avg_miles, 0) if avg_miles else None))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} progression entries")


def generate_rankings(sqlite_conn):
    """Generate comparative rankings from the computed data."""
    print("\n[11/20] Generating comparative rankings...")
    cursor = sqlite_conn.cursor()

    # Overall ranking (all vehicles by pass rate)
    cursor.execute("""
        INSERT INTO vehicle_rankings (make, model, model_year, fuel_type, ranking_type, rank, total_in_category, pass_rate)
        SELECT
            make, model, model_year, fuel_type, 'overall',
            ROW_NUMBER() OVER (ORDER BY pass_rate DESC) as rank,
            (SELECT COUNT(*) FROM vehicle_insights) as total,
            pass_rate
        FROM vehicle_insights
        WHERE total_tests >= 100
    """)

    # Ranking within same make
    cursor.execute("""
        INSERT INTO vehicle_rankings (make, model, model_year, fuel_type, ranking_type, rank, total_in_category, pass_rate)
        SELECT
            make, model, model_year, fuel_type, 'within_make',
            ROW_NUMBER() OVER (PARTITION BY make ORDER BY pass_rate DESC) as rank,
            COUNT(*) OVER (PARTITION BY make) as total,
            pass_rate
        FROM vehicle_insights
        WHERE total_tests >= 100
    """)

    # Ranking within same model year
    cursor.execute("""
        INSERT INTO vehicle_rankings (make, model, model_year, fuel_type, ranking_type, rank, total_in_category, pass_rate)
        SELECT
            make, model, model_year, fuel_type, 'within_year',
            ROW_NUMBER() OVER (PARTITION BY model_year ORDER BY pass_rate DESC) as rank,
            COUNT(*) OVER (PARTITION BY model_year) as total,
            pass_rate
        FROM vehicle_insights
        WHERE total_tests >= 100
    """)

    sqlite_conn.commit()

    total_rankings = cursor.execute("SELECT COUNT(*) FROM vehicle_rankings").fetchone()[0]
    print(f"  Generated {total_rankings:,} ranking entries")


def generate_dangerous_defects_bulk(duck_conn, sqlite_conn):
    """Generate dangerous defect tracking - serious safety issues."""
    print("\n[12/20] Generating dangerous defects analysis (BULK)...")

    # Get vehicle totals
    duck_conn.execute(f"""
        CREATE TEMP TABLE IF NOT EXISTS vehicle_totals AS
        SELECT make, model, model_year, fuel_type, COUNT(*) as total_tests
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
    """)

    # Step 1: Create deduplicated intermediate table (same pattern as top_defects)
    # This prevents counting the same dangerous defect multiple times per test
    # when it appears at different locations
    duck_conn.execute("""
        CREATE TEMP TABLE dangerous_test_defects AS
        SELECT DISTINCT
            bt.test_id,
            bt.make,
            bt.model,
            bt.model_year,
            bt.fuel_type,
            ti.rfr_id
        FROM base_tests bt
        JOIN test_item ti ON bt.test_id = ti.test_id
        LEFT JOIN item_detail id ON ti.rfr_id = id.rfr_id
            AND CAST(id.test_class_id AS VARCHAR) = '4'
        WHERE (id.rfr_deficiency_category = 'Dangerous' OR ti.dangerous_mark = 'D')
    """)

    # Step 2: Count from deduplicated table (COUNT(*) now equals distinct tests per defect)
    results = duck_conn.execute("""
        WITH dangerous_counts AS (
            SELECT
                dtd.make,
                dtd.model,
                dtd.model_year,
                dtd.fuel_type,
                dtd.rfr_id,
                COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
                ig.item_name as category_name,
                COUNT(*) as occurrence_count
            FROM dangerous_test_defects dtd
            LEFT JOIN item_detail id ON dtd.rfr_id = id.rfr_id
                AND CAST(id.test_class_id AS VARCHAR) = '4'
            LEFT JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                AND CAST(ig.test_class_id AS VARCHAR) = '4' AND ig.parent_id = 0
            GROUP BY dtd.make, dtd.model, dtd.model_year, dtd.fuel_type,
                     dtd.rfr_id, id.rfr_desc, ig.item_name
        ),
        ranked AS (
            SELECT
                dc.*,
                vt.total_tests,
                ROW_NUMBER() OVER (
                    PARTITION BY dc.make, dc.model, dc.model_year, dc.fuel_type
                    ORDER BY dc.occurrence_count DESC
                ) as rank
            FROM dangerous_counts dc
            JOIN vehicle_totals vt ON dc.make = vt.make
                                   AND dc.model = vt.model
                                   AND dc.model_year = vt.model_year
                                   AND dc.fuel_type = vt.fuel_type
        )
        SELECT make, model, model_year, fuel_type, rfr_id, defect_desc,
               category_name, occurrence_count, total_tests, rank
        FROM ranked
        WHERE rank <= 10
    """).fetchall()

    duck_conn.execute("DROP TABLE IF EXISTS dangerous_test_defects")

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, rfr_id, desc, cat, count, total_tests, rank = row
        pct = (count / total_tests) * 100 if total_tests > 0 else 0
        cursor.execute("""
            INSERT INTO dangerous_defects
            (make, model, model_year, fuel_type, rfr_id, defect_description,
             category_name, occurrence_count, occurrence_percentage, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, rfr_id, desc, cat, count, round(pct, 2), rank))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} dangerous defect entries")


def generate_age_bands_bulk(duck_conn, sqlite_conn):
    """Generate pass rates by vehicle age band."""
    print("\n[13/20] Generating age band analysis (BULK)...")

    # Build CASE expression for age bands
    case_expr = "CASE "
    for low, high, label, order in AGE_BANDS:
        case_expr += f"WHEN vehicle_age >= {low} AND vehicle_age <= {high} THEN '{label}' "
    case_expr += "END"

    order_expr = "CASE "
    for low, high, label, order in AGE_BANDS:
        order_expr += f"WHEN vehicle_age >= {low} AND vehicle_age <= {high} THEN {order} "
    order_expr += "END"

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        age_stats AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                {case_expr} as age_band,
                {order_expr} as band_order,
                COUNT(*) as total_tests,
                SUM(CASE WHEN bt.test_result = 'P' THEN 1 ELSE 0 END) as passes,
                AVG(CASE WHEN bt.test_mileage > 0 THEN bt.test_mileage END) as avg_mileage
            FROM base_tests bt
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE bt.vehicle_age >= 3
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, age_band, band_order
            HAVING COUNT(*) >= 10
        )
        SELECT make, model, model_year, fuel_type, age_band, band_order,
               total_tests, passes, avg_mileage
        FROM age_stats
        WHERE age_band IS NOT NULL
        ORDER BY make, model, model_year, fuel_type, band_order
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, band, order, tests, passes, avg_mileage = row
        pass_rate = (passes / tests) * 100 if tests > 0 else 0
        cursor.execute("""
            INSERT INTO age_bands
            (make, model, model_year, fuel_type, age_band, band_order,
             total_tests, pass_rate, avg_mileage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, band, order,
              tests, round(pass_rate, 2), round(avg_mileage, 0) if avg_mileage else None))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} age band entries")


def generate_first_mot_insights_bulk(duck_conn, sqlite_conn):
    """Generate first MOT vs subsequent MOT comparison."""
    print("\n[14/20] Generating first MOT insights (BULK)...")

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        mot_stats AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                CASE WHEN bt.vehicle_age <= 4 THEN 'first' ELSE 'subsequent' END as mot_type,
                COUNT(*) as total_tests,
                SUM(CASE WHEN bt.test_result = 'P' THEN 1 ELSE 0 END) as passes,
                AVG(CASE WHEN bt.test_mileage > 0 THEN bt.test_mileage END) as avg_mileage
            FROM base_tests bt
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, mot_type
            HAVING COUNT(*) >= 20
        ),
        defect_counts AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                CASE WHEN bt.vehicle_age <= 4 THEN 'first' ELSE 'subsequent' END as mot_type,
                COUNT(*) as total_defects,
                COUNT(DISTINCT bt.test_id) as failed_tests
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE bt.test_result IN ('F', 'PRS')
              AND ti.rfr_type_code IN ('F', 'P')
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, mot_type
        )
        SELECT
            ms.make, ms.model, ms.model_year, ms.fuel_type, ms.mot_type,
            ms.total_tests, ms.passes, ms.avg_mileage,
            CASE WHEN dc.failed_tests > 0 THEN 1.0 * dc.total_defects / dc.failed_tests ELSE 0 END as avg_defects
        FROM mot_stats ms
        LEFT JOIN defect_counts dc ON ms.make = dc.make
                                   AND ms.model = dc.model
                                   AND ms.model_year = dc.model_year
                                   AND ms.fuel_type = dc.fuel_type
                                   AND ms.mot_type = dc.mot_type
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, mot_type, tests, passes, avg_mileage, avg_defects = row
        pass_rate = (passes / tests) * 100 if tests > 0 else 0
        cursor.execute("""
            INSERT INTO first_mot_insights
            (make, model, model_year, fuel_type, mot_type, total_tests,
             pass_rate, avg_mileage, avg_defects_per_fail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, mot_type, tests,
              round(pass_rate, 2), round(avg_mileage, 0) if avg_mileage else None,
              round(avg_defects, 2) if avg_defects else None))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} first MOT insight entries")


def generate_manufacturer_rankings(duck_conn, sqlite_conn):
    """Generate manufacturer-level rankings."""
    print("\n[15/20] Generating manufacturer rankings (BULK)...")

    results = duck_conn.execute(f"""
        WITH make_stats AS (
            SELECT
                make,
                COUNT(*) as total_tests,
                COUNT(DISTINCT model || '_' || model_year || '_' || fuel_type) as total_models,
                AVG(CASE WHEN test_result = 'P' THEN 100.0 ELSE 0 END) as avg_pass_rate,
                100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as weighted_pass_rate
            FROM base_tests
            GROUP BY make
            HAVING COUNT(*) >= 1000
        ),
        model_pass_rates AS (
            SELECT
                make,
                model || ' ' || model_year as model_desc,
                100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate,
                COUNT(*) as tests
            FROM base_tests
            GROUP BY make, model, model_year
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        best_models AS (
            SELECT make, model_desc, pass_rate,
                   ROW_NUMBER() OVER (PARTITION BY make ORDER BY pass_rate DESC) as rn
            FROM model_pass_rates
        ),
        worst_models AS (
            SELECT make, model_desc, pass_rate,
                   ROW_NUMBER() OVER (PARTITION BY make ORDER BY pass_rate ASC) as rn
            FROM model_pass_rates
        )
        SELECT
            ms.make,
            ms.total_tests,
            ms.total_models,
            ms.avg_pass_rate,
            ms.weighted_pass_rate,
            bm.model_desc as best_model,
            bm.pass_rate as best_pass_rate,
            wm.model_desc as worst_model,
            wm.pass_rate as worst_pass_rate,
            ROW_NUMBER() OVER (ORDER BY ms.weighted_pass_rate DESC) as rank
        FROM make_stats ms
        LEFT JOIN best_models bm ON ms.make = bm.make AND bm.rn = 1
        LEFT JOIN worst_models wm ON ms.make = wm.make AND wm.rn = 1
        ORDER BY rank
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        (make, total_tests, total_models, avg_pr, weighted_pr,
         best_model, best_pr, worst_model, worst_pr, rank) = row
        cursor.execute("""
            INSERT INTO manufacturer_rankings
            (make, total_tests, total_models, avg_pass_rate, weighted_pass_rate,
             best_model, best_model_pass_rate, worst_model, worst_model_pass_rate, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, total_tests, total_models, round(avg_pr, 2), round(weighted_pr, 2),
              best_model, round(best_pr, 2) if best_pr else None,
              worst_model, round(worst_pr, 2) if worst_pr else None, rank))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} manufacturer ranking entries")


def generate_seasonal_patterns_bulk(duck_conn, sqlite_conn):
    """Generate seasonal/monthly pass rate patterns."""
    print("\n[16/20] Generating seasonal patterns (BULK)...")

    # First, generate national seasonal averages
    national_seasonal = duck_conn.execute("""
        SELECT
            MONTH(test_date) as month,
            CASE
                WHEN MONTH(test_date) IN (1,2,3) THEN 1
                WHEN MONTH(test_date) IN (4,5,6) THEN 2
                WHEN MONTH(test_date) IN (7,8,9) THEN 3
                ELSE 4
            END as quarter,
            COUNT(*) as total_tests,
            100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
        FROM base_tests
        GROUP BY month, quarter
        ORDER BY month
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for month, quarter, tests, pass_rate in national_seasonal:
        cursor.execute("""
            INSERT INTO national_seasonal (month, quarter, total_tests, pass_rate)
            VALUES (?, ?, ?, ?)
        """, (month, quarter, tests, round(pass_rate, 2)))

    # Now per-vehicle seasonal patterns
    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        )
        SELECT
            bt.make,
            bt.model,
            bt.model_year,
            bt.fuel_type,
            MONTH(bt.test_date) as month,
            CASE
                WHEN MONTH(bt.test_date) IN (1,2,3) THEN 1
                WHEN MONTH(bt.test_date) IN (4,5,6) THEN 2
                WHEN MONTH(bt.test_date) IN (7,8,9) THEN 3
                ELSE 4
            END as quarter,
            COUNT(*) as total_tests,
            100.0 * SUM(CASE WHEN bt.test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
        FROM base_tests bt
        JOIN vehicle_combos vc ON bt.make = vc.make
                               AND bt.model = vc.model
                               AND bt.model_year = vc.model_year
                               AND bt.fuel_type = vc.fuel_type
        GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, month, quarter
        HAVING COUNT(*) >= 10
    """).fetchall()

    for row in results:
        make, model, year, fuel_type, month, quarter, tests, pass_rate = row
        cursor.execute("""
            INSERT INTO seasonal_patterns
            (make, model, model_year, fuel_type, month, quarter, total_tests, pass_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, month, quarter, tests, round(pass_rate, 2)))

    sqlite_conn.commit()
    print(f"  Generated {len(national_seasonal)} national + {len(results):,} vehicle seasonal entries")


def generate_failure_severity_bulk(duck_conn, sqlite_conn):
    """Generate failure severity breakdown (Minor/Major/Dangerous)."""
    print("\n[17/20] Generating failure severity breakdown (BULK)...")

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        severity_counts AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                CASE
                    WHEN id.rfr_deficiency_category = 'Dangerous' OR ti.dangerous_mark = 'D' THEN 'dangerous'
                    WHEN id.rfr_deficiency_category = 'Major' THEN 'major'
                    WHEN id.rfr_deficiency_category = 'Minor' THEN 'minor'
                    WHEN id.rfr_deficiency_category = 'Pre-EU Directive' AND ti.rfr_type_code = 'F' THEN 'major'
                    WHEN id.rfr_deficiency_category = 'Pre-EU Directive' THEN 'minor'
                    ELSE 'major'  -- Default unknown to major for safety
                END as severity,
                COUNT(*) as failure_count
            FROM base_tests bt
            JOIN test_item ti ON bt.test_id = ti.test_id
            LEFT JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE ti.rfr_type_code IN ('F', 'P')
            GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, severity
        ),
        with_totals AS (
            SELECT
                sc.*,
                SUM(failure_count) OVER (PARTITION BY make, model, model_year, fuel_type) as total_failures
            FROM severity_counts sc
        )
        SELECT make, model, model_year, fuel_type, severity, failure_count, total_failures
        FROM with_totals
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, severity, count, total = row
        pct = (count / total) * 100 if total > 0 else 0
        cursor.execute("""
            INSERT INTO failure_severity
            (make, model, model_year, fuel_type, severity, failure_count, failure_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, severity, count, round(pct, 2)))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} severity breakdown entries")


def generate_retest_success_bulk(duck_conn, sqlite_conn):
    """Generate retest success rate tracking."""
    print("\n[18/20] Generating retest success rates (BULK)...")
    print("  (Analyzing vehicle retests within 30 days - may take a few minutes)")

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        failed_tests AS (
            SELECT
                bt.vehicle_id,
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                bt.test_date as fail_date,
                bt.test_id
            FROM base_tests bt
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE bt.test_result = 'F'
        ),
        retests AS (
            -- Join to test_result directly to include RT (Re-Test) types, not just NT
            SELECT
                ft.make,
                ft.model,
                ft.model_year,
                ft.fuel_type,
                ft.test_id as failed_test_id,
                MIN(tr2.test_date) as retest_date,
                MAX(CASE WHEN tr2.test_result = 'P' THEN 1 ELSE 0 END) as passed_retest
            FROM failed_tests ft
            JOIN test_result tr2 ON ft.vehicle_id = tr2.vehicle_id
                                AND tr2.test_type IN ('NT', 'RT')
                                AND tr2.test_result IN ('P', 'F', 'PRS')
                                AND CAST(tr2.test_class_id AS VARCHAR) = '4'
                                AND tr2.test_date > ft.fail_date
                                AND tr2.test_date <= ft.fail_date + INTERVAL 30 DAY
            GROUP BY ft.make, ft.model, ft.model_year, ft.fuel_type, ft.test_id
        ),
        stats AS (
            SELECT
                ft.make,
                ft.model,
                ft.model_year,
                ft.fuel_type,
                COUNT(DISTINCT ft.test_id) as failed_tests,
                COUNT(DISTINCT rt.failed_test_id) as retested,
                SUM(COALESCE(rt.passed_retest, 0)) as passed_on_retest
            FROM failed_tests ft
            LEFT JOIN retests rt ON ft.test_id = rt.failed_test_id
            GROUP BY ft.make, ft.model, ft.model_year, ft.fuel_type
            HAVING COUNT(DISTINCT ft.test_id) >= 10
        )
        SELECT * FROM stats
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        make, model, year, fuel_type, failed, retested, passed = row
        retest_rate = (retested / failed) * 100 if failed > 0 else 0
        success_rate = (passed / retested) * 100 if retested > 0 else 0
        cursor.execute("""
            INSERT INTO retest_success
            (make, model, model_year, fuel_type, failed_tests, retested_within_30_days,
             passed_on_retest, retest_rate, retest_success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, failed, retested, passed,
              round(retest_rate, 2), round(success_rate, 2)))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} retest success entries")


def generate_component_mileage_thresholds_bulk(duck_conn, sqlite_conn):
    """Generate component failure rates by mileage band to identify failure thresholds."""
    print("\n[19/20] Generating component mileage thresholds (BULK)...")
    print("  (Analyzing when each component starts failing - may take several minutes)")

    results = duck_conn.execute(f"""
        WITH vehicle_combos AS (
            SELECT make, model, model_year, fuel_type
            FROM base_tests
            GROUP BY make, model, model_year, fuel_type
            HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ),
        mileage_band_tests AS (
            SELECT
                bt.make,
                bt.model,
                bt.model_year,
                bt.fuel_type,
                CASE
                    WHEN bt.test_mileage <= 30000 THEN '0-30k'
                    WHEN bt.test_mileage <= 60000 THEN '30-60k'
                    WHEN bt.test_mileage <= 90000 THEN '60-90k'
                    WHEN bt.test_mileage <= 120000 THEN '90-120k'
                    WHEN bt.test_mileage <= 150000 THEN '120-150k'
                    ELSE '150k+'
                END as mileage_band,
                bt.test_id
            FROM base_tests bt
            JOIN vehicle_combos vc ON bt.make = vc.make
                                   AND bt.model = vc.model
                                   AND bt.model_year = vc.model_year
                                   AND bt.fuel_type = vc.fuel_type
            WHERE bt.test_mileage > 0
        ),
        band_totals AS (
            SELECT make, model, model_year, fuel_type, mileage_band, COUNT(*) as total_tests
            FROM mileage_band_tests
            GROUP BY make, model, model_year, fuel_type, mileage_band
        ),
        component_failures AS (
            SELECT
                mbt.make,
                mbt.model,
                mbt.model_year,
                mbt.fuel_type,
                mbt.mileage_band,
                ig.test_item_set_section_id as category_id,
                ig.item_name as category_name,
                COUNT(DISTINCT mbt.test_id) as failure_count
            FROM mileage_band_tests mbt
            JOIN test_item ti ON mbt.test_id = ti.test_id
            JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
            JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                              AND CAST(ig.test_class_id AS VARCHAR) = '4'
            WHERE ti.rfr_type_code IN ('F', 'P')
              AND ig.parent_id = 0
              AND ig.test_item_id != 0
            GROUP BY mbt.make, mbt.model, mbt.model_year, mbt.fuel_type,
                     mbt.mileage_band, ig.test_item_set_section_id, ig.item_name
        ),
        failure_rates AS (
            SELECT
                cf.make,
                cf.model,
                cf.model_year,
                cf.fuel_type,
                cf.category_id,
                cf.category_name,
                cf.mileage_band,
                100.0 * cf.failure_count / bt.total_tests as failure_rate
            FROM component_failures cf
            JOIN band_totals bt ON cf.make = bt.make
                               AND cf.model = bt.model
                               AND cf.model_year = bt.model_year
                               AND cf.fuel_type = bt.fuel_type
                               AND cf.mileage_band = bt.mileage_band
            WHERE bt.total_tests >= 10
        ),
        pivoted AS (
            SELECT
                make, model, model_year, fuel_type, category_id, category_name,
                MAX(CASE WHEN mileage_band = '0-30k' THEN failure_rate END) as rate_0_30k,
                MAX(CASE WHEN mileage_band = '30-60k' THEN failure_rate END) as rate_30_60k,
                MAX(CASE WHEN mileage_band = '60-90k' THEN failure_rate END) as rate_60_90k,
                MAX(CASE WHEN mileage_band = '90-120k' THEN failure_rate END) as rate_90_120k,
                MAX(CASE WHEN mileage_band = '120-150k' THEN failure_rate END) as rate_120_150k,
                MAX(CASE WHEN mileage_band = '150k+' THEN failure_rate END) as rate_150k_plus
            FROM failure_rates
            GROUP BY make, model, model_year, fuel_type, category_id, category_name
            HAVING COUNT(*) >= 3  -- At least 3 bands with data
        )
        SELECT * FROM pivoted
    """).fetchall()

    cursor = sqlite_conn.cursor()
    for row in results:
        (make, model, year, fuel_type, cat_id, cat_name,
         r1, r2, r3, r4, r5, r6) = row

        # Find the spike (largest increase between consecutive bands)
        rates = [
            ('0-30k', r1 or 0),
            ('30-60k', r2 or 0),
            ('60-90k', r3 or 0),
            ('90-120k', r4 or 0),
            ('120-150k', r5 or 0),
            ('150k+', r6 or 0)
        ]

        max_increase = 0
        spike_band = None
        for i in range(1, len(rates)):
            if rates[i][1] > 0 and rates[i-1][1] > 0:
                increase = rates[i][1] - rates[i-1][1]
                if increase > max_increase:
                    max_increase = increase
                    spike_band = rates[i][0]

        cursor.execute("""
            INSERT INTO component_mileage_thresholds
            (make, model, model_year, fuel_type, category_id, category_name,
             failure_rate_0_30k, failure_rate_30_60k, failure_rate_60_90k,
             failure_rate_90_120k, failure_rate_120_150k, failure_rate_150k_plus,
             spike_mileage_band, spike_increase_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (make, model, year, fuel_type, cat_id, cat_name,
              round(r1, 2) if r1 else None,
              round(r2, 2) if r2 else None,
              round(r3, 2) if r3 else None,
              round(r4, 2) if r4 else None,
              round(r5, 2) if r5 else None,
              round(r6, 2) if r6 else None,
              spike_band,
              round(max_increase, 2) if max_increase > 0 else None))

    sqlite_conn.commit()
    print(f"  Generated {len(results):,} component threshold entries")


def cleanup(duck_conn):
    """Clean up temporary DuckDB file."""
    print("\n[20/20] Cleaning up...")
    duck_conn.close()

    if DUCKDB_FILE.exists():
        try:
            os.remove(DUCKDB_FILE)
            print(f"  Removed temporary file: {DUCKDB_FILE}")
        except Exception as e:
            print(f"  Warning: Could not remove {DUCKDB_FILE}: {e}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_output():
    """Validate output database for known issues."""
    print("\nValidating output database...")
    conn = sqlite3.connect(OUTPUT_DB)
    issues_found = False

    # Check 1: No occurrence_percentage > 100% in top_defects
    result = conn.execute("""
        SELECT COUNT(*) FROM top_defects
        WHERE occurrence_percentage > 100
    """).fetchone()[0]
    if result > 0:
        print(f"  WARNING: {result} top_defects entries exceed 100%")
        issues_found = True

    # Check 1b: No occurrence_percentage > 100% in dangerous_defects
    result = conn.execute("""
        SELECT COUNT(*) FROM dangerous_defects
        WHERE occurrence_percentage > 100
    """).fetchone()[0]
    if result > 0:
        print(f"  WARNING: {result} dangerous_defects entries exceed 100%")
        issues_found = True

    # Check 2: Pass rate sanity
    result = conn.execute("""
        SELECT COUNT(*) FROM vehicle_insights
        WHERE pass_rate < 0 OR pass_rate > 100
    """).fetchone()[0]
    if result > 0:
        print(f"  WARNING: {result} vehicle_insights have invalid pass_rate")
        issues_found = True

    # Check 3: Initial failure rate sanity
    result = conn.execute("""
        SELECT COUNT(*) FROM vehicle_insights
        WHERE initial_failure_rate < 0 OR initial_failure_rate > 100
    """).fetchone()[0]
    if result > 0:
        print(f"  WARNING: {result} vehicle_insights have invalid initial_failure_rate")
        issues_found = True

    # Check 4: All tables populated
    tables = ['national_averages', 'vehicle_insights', 'failure_categories',
              'top_defects', 'mileage_bands', 'geographic_insights',
              'defect_locations', 'advisory_progression', 'vehicle_rankings',
              'available_vehicles', 'dangerous_defects', 'age_bands',
              'first_mot_insights', 'manufacturer_rankings', 'seasonal_patterns',
              'national_seasonal', 'failure_severity', 'retest_success',
              'component_mileage_thresholds']

    empty_tables = []
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            empty_tables.append(table)

    if empty_tables:
        print(f"  WARNING: Empty tables: {', '.join(empty_tables)}")
        issues_found = True

    if not issues_found:
        print("  All validation checks passed")

    conn.close()
    return not issues_found


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    start_time = datetime.now()

    # Step 1: Set up DuckDB and import data
    duck_conn = create_duckdb_connection()

    # Step 2: Create filtered base table for all subsequent queries
    create_base_tests_table(duck_conn)

    # Step 3: Create output SQLite database
    sqlite_conn = create_output_database()

    # Step 4: Generate national averages first (needed for comparisons)
    national_pass_rate = generate_national_averages(duck_conn, sqlite_conn)

    # Step 5-19: Generate all insights using BULK operations
    vehicle_count = generate_vehicle_insights_bulk(duck_conn, sqlite_conn, national_pass_rate)
    generate_failure_categories_bulk(duck_conn, sqlite_conn)
    generate_top_defects_bulk(duck_conn, sqlite_conn)
    generate_mileage_bands_bulk(duck_conn, sqlite_conn)
    generate_geographic_insights_bulk(duck_conn, sqlite_conn)
    generate_defect_locations_bulk(duck_conn, sqlite_conn)
    generate_advisory_progression_bulk(duck_conn, sqlite_conn)
    generate_rankings(sqlite_conn)

    # New enhanced insights
    generate_dangerous_defects_bulk(duck_conn, sqlite_conn)
    generate_age_bands_bulk(duck_conn, sqlite_conn)
    generate_first_mot_insights_bulk(duck_conn, sqlite_conn)
    generate_manufacturer_rankings(duck_conn, sqlite_conn)
    generate_seasonal_patterns_bulk(duck_conn, sqlite_conn)
    generate_failure_severity_bulk(duck_conn, sqlite_conn)
    generate_retest_success_bulk(duck_conn, sqlite_conn)
    generate_component_mileage_thresholds_bulk(duck_conn, sqlite_conn)

    # Cleanup
    cleanup(duck_conn)
    sqlite_conn.close()

    # Validate output
    validate_output()

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Output file: {OUTPUT_DB}")
    print(f"File size: {OUTPUT_DB.stat().st_size / (1024*1024):.1f} MB")
    print(f"Total time: {duration}")
    print(f"Vehicles processed: {vehicle_count:,}")

    # Quick validation
    conn = sqlite3.connect(OUTPUT_DB)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"\nTables created: {len(tables)}")
    for (table,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} rows")
    conn.close()


if __name__ == "__main__":
    main()
