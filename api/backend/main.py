"""MOT Insights API - FastAPI Application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import queries
from .database import get_db, get_fuel_name

app = FastAPI(
    title="MOT Insights API",
    description="API for UK MOT test insights data",
    version="1.0.0",
)

# Allow all origins for local dev (file:// and localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@app.get("/api/health")
def health_check():
    """Check API and database health."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.get("/api/stats")
def get_stats():
    """Get row counts for all tables."""
    with get_db() as conn:
        return queries.get_table_stats(conn)


# =============================================================================
# VEHICLE LOOKUP ENDPOINTS (Cascading Dropdowns)
# =============================================================================

@app.get("/api/makes")
def get_makes():
    """Get all available makes."""
    with get_db() as conn:
        return queries.get_all_makes(conn)


@app.get("/api/makes/{make}/models")
def get_models(make: str):
    """Get all models for a make."""
    with get_db() as conn:
        models = queries.get_models_for_make(conn, make)
        if not models:
            raise HTTPException(status_code=404, detail=f"Make '{make}' not found")
        return models


@app.get("/api/makes/{make}/models/{model}/variants")
def get_variants(make: str, model: str):
    """Get year/fuel variants for a make+model."""
    with get_db() as conn:
        variants = queries.get_variants_for_model(conn, make, model)
        if not variants:
            raise HTTPException(status_code=404, detail=f"Model '{make} {model}' not found")
        # Add fuel type names
        for v in variants:
            v["fuel_type_name"] = get_fuel_name(v["fuel_type"])
        return variants


# =============================================================================
# COMBINED VEHICLE REPORT
# =============================================================================

@app.get("/api/vehicle/{make}/{model}/{year}/{fuel}")
def get_vehicle_report(make: str, model: str, year: int, fuel: str):
    """Get complete vehicle report with all key data."""
    with get_db() as conn:
        # Check vehicle exists
        if not queries.check_vehicle_exists(conn, make, model, year, fuel):
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle not found: {make} {model} {year} {fuel}"
            )

        insights = queries.get_vehicle_insights(conn, make, model, year, fuel)
        defects = queries.get_top_defects(conn, make, model, year, fuel)
        rankings = queries.get_vehicle_rankings(conn, make, model, year, fuel)

        # Calculate percentiles for rankings
        for rank_type, rank_data in rankings.items():
            if rank_data and rank_data["total_in_category"] > 0:
                rank_data["percentile"] = round(
                    (1 - (rank_data["rank"] / rank_data["total_in_category"])) * 100
                )

        return {
            "vehicle": {
                "make": make.upper(),
                "model": model.upper(),
                "model_year": year,
                "fuel_type": fuel.upper(),
                "fuel_type_name": get_fuel_name(fuel.upper()),
            },
            "insights": insights,
            "rankings": rankings,
            "failure_categories": queries.get_failure_categories(conn, make, model, year, fuel),
            "top_failures": defects["failures"],
            "top_advisories": defects["advisories"],
            "dangerous_defects": queries.get_dangerous_defects(conn, make, model, year, fuel),
            "mileage_bands": queries.get_mileage_bands(conn, make, model, year, fuel),
        }


# =============================================================================
# INDIVIDUAL TABLE ENDPOINTS
# =============================================================================

@app.get("/api/insights/{make}/{model}/{year}/{fuel}")
def get_insights(make: str, model: str, year: int, fuel: str):
    """Get vehicle insights."""
    with get_db() as conn:
        data = queries.get_vehicle_insights(conn, make, model, year, fuel)
        if not data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return data


@app.get("/api/failures/{make}/{model}/{year}/{fuel}")
def get_failures(make: str, model: str, year: int, fuel: str):
    """Get failure categories."""
    with get_db() as conn:
        return queries.get_failure_categories(conn, make, model, year, fuel)


@app.get("/api/defects/{make}/{model}/{year}/{fuel}")
def get_defects(make: str, model: str, year: int, fuel: str):
    """Get top defects (failures and advisories)."""
    with get_db() as conn:
        return queries.get_top_defects(conn, make, model, year, fuel)


@app.get("/api/dangerous/{make}/{model}/{year}/{fuel}")
def get_dangerous(make: str, model: str, year: int, fuel: str):
    """Get dangerous defects."""
    with get_db() as conn:
        return queries.get_dangerous_defects(conn, make, model, year, fuel)


@app.get("/api/mileage/{make}/{model}/{year}/{fuel}")
def get_mileage(make: str, model: str, year: int, fuel: str):
    """Get mileage band breakdown."""
    with get_db() as conn:
        return queries.get_mileage_bands(conn, make, model, year, fuel)


@app.get("/api/rankings/{make}/{model}/{year}/{fuel}")
def get_rankings(make: str, model: str, year: int, fuel: str):
    """Get vehicle rankings."""
    with get_db() as conn:
        rankings = queries.get_vehicle_rankings(conn, make, model, year, fuel)
        # Add percentiles
        for rank_type, rank_data in rankings.items():
            if rank_data and rank_data["total_in_category"] > 0:
                rank_data["percentile"] = round(
                    (1 - (rank_data["rank"] / rank_data["total_in_category"])) * 100
                )
        return rankings


@app.get("/api/geographic/{make}/{model}/{year}/{fuel}")
def get_geographic(make: str, model: str, year: int, fuel: str):
    """Get geographic insights by postcode area."""
    with get_db() as conn:
        return queries.get_geographic_insights(conn, make, model, year, fuel)


@app.get("/api/seasonal/{make}/{model}/{year}/{fuel}")
def get_seasonal(make: str, model: str, year: int, fuel: str):
    """Get seasonal patterns."""
    with get_db() as conn:
        return queries.get_seasonal_patterns(conn, make, model, year, fuel)


@app.get("/api/age/{make}/{model}/{year}/{fuel}")
def get_age(make: str, model: str, year: int, fuel: str):
    """Get age band breakdown."""
    with get_db() as conn:
        return queries.get_age_bands(conn, make, model, year, fuel)


@app.get("/api/severity/{make}/{model}/{year}/{fuel}")
def get_severity(make: str, model: str, year: int, fuel: str):
    """Get failure severity breakdown."""
    with get_db() as conn:
        return queries.get_failure_severity(conn, make, model, year, fuel)


@app.get("/api/first-mot/{make}/{model}/{year}/{fuel}")
def get_first_mot(make: str, model: str, year: int, fuel: str):
    """Get first MOT insights."""
    with get_db() as conn:
        return queries.get_first_mot_insights(conn, make, model, year, fuel)


@app.get("/api/retest/{make}/{model}/{year}/{fuel}")
def get_retest(make: str, model: str, year: int, fuel: str):
    """Get retest success data."""
    with get_db() as conn:
        return queries.get_retest_success(conn, make, model, year, fuel)


@app.get("/api/advisory-progression/{make}/{model}/{year}/{fuel}")
def get_advisory_progression(make: str, model: str, year: int, fuel: str):
    """Get advisory progression data."""
    with get_db() as conn:
        return queries.get_advisory_progression(conn, make, model, year, fuel)


@app.get("/api/component-thresholds/{make}/{model}/{year}/{fuel}")
def get_component_thresholds(make: str, model: str, year: int, fuel: str):
    """Get component mileage threshold data."""
    with get_db() as conn:
        return queries.get_component_mileage_thresholds(conn, make, model, year, fuel)


@app.get("/api/defect-locations/{make}/{model}/{year}/{fuel}")
def get_defect_locations(make: str, model: str, year: int, fuel: str):
    """Get defect location distribution."""
    with get_db() as conn:
        return queries.get_defect_locations(conn, make, model, year, fuel)


# =============================================================================
# NATIONAL / AGGREGATE ENDPOINTS
# =============================================================================

@app.get("/api/national/averages")
def get_national_averages():
    """Get national average metrics."""
    with get_db() as conn:
        return queries.get_national_averages(conn)


@app.get("/api/national/seasonal")
def get_national_seasonal():
    """Get national seasonal data."""
    with get_db() as conn:
        return queries.get_national_seasonal(conn)


@app.get("/api/manufacturers")
def get_manufacturers():
    """Get all manufacturer rankings."""
    with get_db() as conn:
        return queries.get_all_manufacturers(conn)


@app.get("/api/manufacturers/{make}")
def get_manufacturer(make: str):
    """Get single manufacturer details."""
    with get_db() as conn:
        data = queries.get_manufacturer(conn, make)
        if not data:
            raise HTTPException(status_code=404, detail=f"Manufacturer '{make}' not found")
        return data
