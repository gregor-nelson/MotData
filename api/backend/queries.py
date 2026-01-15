"""SQL query functions for MOT Insights API."""

from sqlite3 import Connection


# =============================================================================
# VEHICLE LOOKUP QUERIES (Cascading Dropdowns)
# =============================================================================

def get_all_makes(conn: Connection) -> list[dict]:
    """Get all available makes, sorted alphabetically."""
    cursor = conn.execute(
        "SELECT DISTINCT make FROM available_vehicles ORDER BY make"
    )
    return [row["make"] for row in cursor.fetchall()]


def get_models_for_make(conn: Connection, make: str) -> list[dict]:
    """Get all models for a given make."""
    cursor = conn.execute(
        "SELECT DISTINCT model FROM available_vehicles WHERE make = ? ORDER BY model",
        (make.upper(),)
    )
    return [row["model"] for row in cursor.fetchall()]


def get_variants_for_model(conn: Connection, make: str, model: str) -> list[dict]:
    """Get year/fuel combinations for a make+model."""
    cursor = conn.execute(
        """SELECT model_year, fuel_type, total_tests
           FROM available_vehicles
           WHERE make = ? AND model = ?
           ORDER BY model_year DESC, fuel_type""",
        (make.upper(), model.upper())
    )
    return cursor.fetchall()


# =============================================================================
# CORE VEHICLE DATA QUERIES
# =============================================================================

def get_vehicle_insights(conn: Connection, make: str, model: str, year: int, fuel: str) -> dict | None:
    """Get core vehicle insights from vehicle_insights table."""
    cursor = conn.execute(
        """SELECT * FROM vehicle_insights
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchone()


def get_failure_categories(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get top failure categories for a vehicle."""
    cursor = conn.execute(
        """SELECT category_name, failure_count, failure_percentage, rank
           FROM failure_categories
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY rank""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_top_defects(conn: Connection, make: str, model: str, year: int, fuel: str) -> dict:
    """Get top failure and advisory defects for a vehicle."""
    cursor = conn.execute(
        """SELECT defect_description, category_name, occurrence_count,
                  occurrence_percentage, rank, defect_type
           FROM top_defects
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY defect_type, rank""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    rows = cursor.fetchall()
    return {
        "failures": [r for r in rows if r["defect_type"] == "failure"],
        "advisories": [r for r in rows if r["defect_type"] == "advisory"]
    }


def get_dangerous_defects(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get dangerous defects for a vehicle."""
    cursor = conn.execute(
        """SELECT defect_description, category_name, occurrence_count,
                  occurrence_percentage, rank
           FROM dangerous_defects
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY rank""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_mileage_bands(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get pass rates by mileage band for a vehicle."""
    cursor = conn.execute(
        """SELECT mileage_band, band_order, total_tests, pass_rate, avg_mileage
           FROM mileage_bands
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY band_order""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_vehicle_rankings(conn: Connection, make: str, model: str, year: int, fuel: str) -> dict:
    """Get rankings for a vehicle (overall, within_make, within_year)."""
    cursor = conn.execute(
        """SELECT ranking_type, rank, total_in_category, pass_rate
           FROM vehicle_rankings
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    rows = cursor.fetchall()
    return {r["ranking_type"]: r for r in rows}


# =============================================================================
# ADDITIONAL VEHICLE DATA QUERIES
# =============================================================================

def get_geographic_insights(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get geographic breakdown by postcode area."""
    cursor = conn.execute(
        """SELECT postcode_area, total_tests, pass_rate
           FROM geographic_insights
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY pass_rate DESC""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_seasonal_patterns(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get seasonal/monthly patterns for a vehicle."""
    cursor = conn.execute(
        """SELECT *
           FROM seasonal_patterns
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY month""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_age_bands(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get pass rates by vehicle age band."""
    cursor = conn.execute(
        """SELECT *
           FROM age_bands
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY band_order""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_failure_severity(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get failure severity breakdown (major vs dangerous)."""
    cursor = conn.execute(
        """SELECT *
           FROM failure_severity
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_first_mot_insights(conn: Connection, make: str, model: str, year: int, fuel: str) -> dict | None:
    """Get first MOT vs subsequent comparison."""
    cursor = conn.execute(
        """SELECT *
           FROM first_mot_insights
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchone()


def get_retest_success(conn: Connection, make: str, model: str, year: int, fuel: str) -> dict | None:
    """Get retest success rates."""
    cursor = conn.execute(
        """SELECT *
           FROM retest_success
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchone()


def get_advisory_progression(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get advisory to failure progression data."""
    cursor = conn.execute(
        """SELECT *
           FROM advisory_progression
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_component_mileage_thresholds(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get component failure rates by mileage."""
    cursor = conn.execute(
        """SELECT *
           FROM component_mileage_thresholds
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY category_name, mileage_band""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


def get_defect_locations(conn: Connection, make: str, model: str, year: int, fuel: str) -> list[dict]:
    """Get defect location distribution."""
    cursor = conn.execute(
        """SELECT *
           FROM defect_locations
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
           ORDER BY occurrence_count DESC""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchall()


# =============================================================================
# NATIONAL / AGGREGATE QUERIES
# =============================================================================

def get_national_averages(conn: Connection) -> list[dict]:
    """Get all national average metrics."""
    cursor = conn.execute("SELECT * FROM national_averages ORDER BY id")
    return cursor.fetchall()


def get_national_seasonal(conn: Connection) -> list[dict]:
    """Get national seasonal/monthly data."""
    cursor = conn.execute("SELECT * FROM national_seasonal ORDER BY month")
    return cursor.fetchall()


def get_all_manufacturers(conn: Connection) -> list[dict]:
    """Get all manufacturer rankings."""
    cursor = conn.execute("SELECT * FROM manufacturer_rankings ORDER BY rank")
    return cursor.fetchall()


def get_manufacturer(conn: Connection, make: str) -> dict | None:
    """Get single manufacturer details."""
    cursor = conn.execute(
        "SELECT * FROM manufacturer_rankings WHERE make = ?",
        (make.upper(),)
    )
    return cursor.fetchone()


# =============================================================================
# MAKE-LEVEL AGGREGATION QUERIES
# =============================================================================

def get_make_models(conn: Connection, make: str) -> list[dict]:
    """Get all models for a make with their pass rates and test counts."""
    cursor = conn.execute(
        """SELECT model, model_year, fuel_type,
                  SUM(total_tests) as total_tests,
                  ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
                  ROUND(AVG(avg_mileage), 0) as avg_mileage
           FROM vehicle_insights
           WHERE make = ?
           GROUP BY model, model_year, fuel_type
           ORDER BY pass_rate DESC""",
        (make.upper(),)
    )
    return cursor.fetchall()


def get_make_failure_categories(conn: Connection, make: str) -> list[dict]:
    """Get aggregated failure categories across all models for a make."""
    cursor = conn.execute(
        """SELECT category_name,
                  SUM(failure_count) as failure_count,
                  ROUND(AVG(failure_percentage), 2) as failure_percentage
           FROM failure_categories
           WHERE make = ?
           GROUP BY category_name
           ORDER BY failure_count DESC
           LIMIT 10""",
        (make.upper(),)
    )
    return cursor.fetchall()


def get_make_top_defects(conn: Connection, make: str) -> dict:
    """Get aggregated top defects across all models for a make."""
    cursor = conn.execute(
        """SELECT defect_description, category_name, defect_type,
                  SUM(occurrence_count) as occurrence_count,
                  ROUND(AVG(occurrence_percentage), 2) as occurrence_percentage
           FROM top_defects
           WHERE make = ?
           GROUP BY defect_description, category_name, defect_type
           ORDER BY defect_type, occurrence_count DESC""",
        (make.upper(),)
    )
    rows = cursor.fetchall()
    return {
        "failures": [r for r in rows if r["defect_type"] == "failure"][:50],
        "advisories": [r for r in rows if r["defect_type"] == "advisory"][:50]
    }


def get_make_dangerous_defects(conn: Connection, make: str) -> list[dict]:
    """Get aggregated dangerous defects across all models for a make."""
    cursor = conn.execute(
        """SELECT defect_description, category_name,
                  SUM(occurrence_count) as occurrence_count,
                  ROUND(AVG(occurrence_percentage), 2) as occurrence_percentage
           FROM dangerous_defects
           WHERE make = ?
           GROUP BY defect_description, category_name
           ORDER BY occurrence_count DESC
           LIMIT 50""",
        (make.upper(),)
    )
    return cursor.fetchall()


def get_make_summary(conn: Connection, make: str) -> dict | None:
    """Get summary statistics for a make."""
    cursor = conn.execute(
        """SELECT COUNT(DISTINCT model) as total_models,
                  COUNT(DISTINCT model || model_year || fuel_type) as total_variants,
                  SUM(total_tests) as total_tests,
                  SUM(total_passes) as total_passes,
                  SUM(total_fails) as total_fails,
                  ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate,
                  ROUND(AVG(avg_mileage), 0) as avg_mileage,
                  ROUND(AVG(avg_age_years), 1) as avg_age_years
           FROM vehicle_insights
           WHERE make = ?""",
        (make.upper(),)
    )
    return cursor.fetchone()


# =============================================================================
# UTILITY QUERIES
# =============================================================================

def get_table_stats(conn: Connection) -> dict:
    """Get row counts for all tables."""
    tables = [
        "available_vehicles", "vehicle_insights", "failure_categories",
        "top_defects", "dangerous_defects", "mileage_bands", "vehicle_rankings",
        "manufacturer_rankings", "national_averages", "national_seasonal",
        "geographic_insights", "seasonal_patterns", "age_bands", "failure_severity",
        "first_mot_insights", "advisory_progression", "retest_success",
        "component_mileage_thresholds", "defect_locations"
    ]
    stats = {}
    for table in tables:
        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
        stats[table] = cursor.fetchone()["count"]
    return stats


def check_vehicle_exists(conn: Connection, make: str, model: str, year: int, fuel: str) -> bool:
    """Check if a vehicle exists in the database."""
    cursor = conn.execute(
        """SELECT 1 FROM available_vehicles
           WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?""",
        (make.upper(), model.upper(), year, fuel.upper())
    )
    return cursor.fetchone() is not None
