# MOT Insights API - Developer Reference

> Master reference documentation for the MOT Insights API project.
> Generated: January 2025

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Database Schema](#3-database-schema)
4. [API Endpoints Reference](#4-api-endpoints-reference)
5. [Query Functions](#5-query-functions)
6. [Frontend Features](#6-frontend-features)
7. [Setup & Running](#7-setup--running)
8. [Data Dictionary](#8-data-dictionary)

---

## 1. Project Overview

### What This Project Does

MOT Insights is a data API and explorer for UK MOT (Ministry of Transport) vehicle test data. It provides comprehensive analytics on vehicle reliability based on historical MOT test results, including:

- **Pass/fail rates** for 11,406 vehicle combinations (make + model + year + fuel type)
- **Failure analysis** by category, specific defect, and location
- **Mileage impact** on test outcomes
- **Manufacturer rankings** and comparisons
- **Geographic and seasonal patterns**
- **Dangerous defect tracking**

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.10+ with FastAPI |
| **Database** | SQLite (read-only, 19 tables) |
| **Frontend** | Single-page HTML/CSS/JavaScript |
| **Server** | Uvicorn ASGI |
| **Data Source** | UK DVSA MOT test records |

### Project Statistics

- **86** manufacturers
- **2,182** distinct models
- **11,406** vehicle variants (make/model/year/fuel combinations)
- **32.2 million** total MOT tests in dataset
- **71.5%** national average pass rate

---

## 2. Architecture

### Directory Structure

```
C:\Users\gregor\Downloads\Mot Data\
├── api/
│   ├── app.py                    # Entry point - starts server & mounts frontend
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app with all endpoint definitions
│   │   ├── database.py           # SQLite connection helper
│   │   └── queries.py            # SQL query functions
│   ├── frontend/
│   │   └── index.html            # Single-page dev explorer UI
│   └── docs/
│       └── API_REFERENCE.md      # This file
└── data/
    └── database/
        └── mot_insights.db       # SQLite database (~pre-computed analytics)
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                            │
│                    http://localhost:8010                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Uvicorn Server                              │
│                           (Port 8010)                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              ▼                                       ▼
┌─────────────────────────┐             ┌─────────────────────────────┐
│  Static Files Mount     │             │       FastAPI App           │
│  "/" → frontend/        │             │      "/api/*" routes        │
│  (index.html)           │             │                             │
└─────────────────────────┘             └─────────────────────────────┘
                                                      │
                                                      ▼
                                        ┌─────────────────────────────┐
                                        │       queries.py            │
                                        │    (SQL query functions)    │
                                        └─────────────────────────────┘
                                                      │
                                                      ▼
                                        ┌─────────────────────────────┐
                                        │     database.py             │
                                        │  (SQLite connection pool)   │
                                        │     Read-only mode          │
                                        └─────────────────────────────┘
                                                      │
                                                      ▼
                                        ┌─────────────────────────────┐
                                        │    mot_insights.db          │
                                        │  (SQLite - 19 tables)       │
                                        └─────────────────────────────┘
```

### Data Flow

1. **Request**: Client sends HTTP GET to `/api/*` endpoint
2. **Routing**: FastAPI routes to appropriate endpoint handler in `main.py`
3. **Query**: Handler calls function(s) from `queries.py`
4. **Connection**: Query function gets connection via `database.py` context manager
5. **Execute**: SQL executed against read-only SQLite database
6. **Transform**: Results returned as Python dicts (via `dict_factory`)
7. **Response**: FastAPI serializes to JSON and returns to client

### Key Design Decisions

- **Read-only database**: Connection opened with `?mode=ro` for safety
- **Pre-computed analytics**: All insights are pre-calculated and stored (no runtime aggregations)
- **Context manager pattern**: Database connections properly closed via `with get_db() as conn:`
- **Single entry point**: `app.py` consolidates API and frontend serving
- **Uppercase normalization**: All make/model/fuel lookups normalized to uppercase

---

## 3. Database Schema

### Tables Overview

| Table | Description | Row Count (typical) |
|-------|-------------|---------------------|
| `available_vehicles` | Master list of vehicle variants | 11,406 |
| `vehicle_insights` | Core stats per vehicle | 11,406 |
| `failure_categories` | Top failure categories per vehicle | ~114,000 |
| `top_defects` | Top failures & advisories per vehicle | ~228,000 |
| `dangerous_defects` | Dangerous defects per vehicle | ~57,000 |
| `mileage_bands` | Pass rates by mileage band | ~68,000 |
| `vehicle_rankings` | Rankings (overall, within-make, within-year) | ~34,000 |
| `geographic_insights` | Pass rates by postcode area | ~1.1M |
| `seasonal_patterns` | Monthly pass rates | ~137,000 |
| `age_bands` | Pass rates by vehicle age | ~68,000 |
| `failure_severity` | Major vs dangerous breakdown | ~34,000 |
| `first_mot_insights` | First MOT vs subsequent comparison | ~22,000 |
| `retest_success` | Retest rates and success | ~11,400 |
| `advisory_progression` | Advisory-to-failure progression | ~114,000 |
| `component_mileage_thresholds` | Component failure by mileage | ~114,000 |
| `defect_locations` | Physical defect locations | ~68,000 |
| `manufacturer_rankings` | Manufacturer comparison | 86 |
| `national_averages` | Benchmark metrics | ~30 |
| `national_seasonal` | National monthly data | 12 |

### Table Definitions

#### `available_vehicles`
Master index of all queryable vehicle combinations.

```sql
CREATE TABLE available_vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    total_tests INTEGER NOT NULL,
    UNIQUE(make, model, model_year, fuel_type)
);
```

#### `vehicle_insights`
Core statistics for each vehicle variant.

```sql
CREATE TABLE vehicle_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    total_tests INTEGER NOT NULL,
    total_passes INTEGER NOT NULL,
    total_fails INTEGER NOT NULL,
    total_prs INTEGER NOT NULL,           -- Pass with Rectification at Station
    pass_rate REAL NOT NULL,              -- Percentage (0-100)
    initial_failure_rate REAL NOT NULL,   -- 100 - pass_rate
    avg_mileage REAL,                     -- Average odometer at test
    avg_age_years REAL,                   -- Average vehicle age
    national_pass_rate REAL,              -- Benchmark (71.51%)
    pass_rate_vs_national REAL,           -- Difference from national
    UNIQUE(make, model, model_year, fuel_type)
);
```

#### `failure_categories`
Top 10 failure categories for each vehicle.

```sql
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
    rank INTEGER NOT NULL                 -- 1-10
);
```

#### `top_defects`
Top 10 specific failure and advisory items.

```sql
CREATE TABLE top_defects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    rfr_id INTEGER NOT NULL,              -- Reason for Rejection ID
    defect_description TEXT NOT NULL,
    category_name TEXT,
    defect_type TEXT NOT NULL,            -- 'failure' or 'advisory'
    occurrence_count INTEGER NOT NULL,
    occurrence_percentage REAL NOT NULL,
    rank INTEGER NOT NULL
);
```

#### `dangerous_defects`
Defects classified as dangerous (immediate prohibition).

```sql
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
);
```

#### `mileage_bands`
Pass rates segmented by odometer reading.

```sql
CREATE TABLE mileage_bands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    mileage_band TEXT NOT NULL,           -- '0-30k', '30k-60k', etc.
    band_order INTEGER NOT NULL,          -- 0-5
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_mileage REAL
);
```

#### `vehicle_rankings`
Comparative rankings across different scopes.

```sql
CREATE TABLE vehicle_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    ranking_type TEXT NOT NULL,           -- 'overall', 'within_make', 'within_year'
    rank INTEGER NOT NULL,
    total_in_category INTEGER NOT NULL,
    pass_rate REAL NOT NULL
);
```

#### `geographic_insights`
Pass rates by UK postcode area.

```sql
CREATE TABLE geographic_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    postcode_area TEXT NOT NULL,          -- 'AB', 'B', 'BA', etc.
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL
);
```

#### `seasonal_patterns`
Monthly test patterns for each vehicle.

```sql
CREATE TABLE seasonal_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    month INTEGER NOT NULL,               -- 1-12
    quarter INTEGER NOT NULL,             -- 1-4
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL
);
```

#### `age_bands`
Pass rates by vehicle age at test time.

```sql
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
);
```

#### `failure_severity`
Breakdown of failure severity levels.

```sql
CREATE TABLE failure_severity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    severity TEXT NOT NULL,               -- 'minor', 'major', 'dangerous'
    failure_count INTEGER NOT NULL,
    failure_percentage REAL NOT NULL
);
```

#### `first_mot_insights`
Comparison of first MOT vs subsequent tests.

```sql
CREATE TABLE first_mot_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    mot_type TEXT NOT NULL,               -- 'first' or 'subsequent'
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_mileage REAL,
    avg_defects_per_fail REAL
);
```

#### `retest_success`
Retest behavior after failures.

```sql
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
);
```

#### `advisory_progression`
Tracking advisories that later become failures.

```sql
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
);
```

#### `component_mileage_thresholds`
Component failure rates across mileage bands.

```sql
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
    spike_mileage_band TEXT,              -- Band with significant increase
    spike_increase_pct REAL
);
```

#### `defect_locations`
Physical location of defects on vehicle.

```sql
CREATE TABLE defect_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    location_id INTEGER NOT NULL,
    lateral TEXT,                         -- 'nearside', 'offside', 'central'
    longitudinal TEXT,                    -- 'front', 'rear'
    vertical TEXT,                        -- 'upper', 'lower'
    failure_count INTEGER NOT NULL,
    failure_percentage REAL NOT NULL
);
```

#### `manufacturer_rankings`
Aggregate rankings by make/brand.

```sql
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
);
```

#### `national_averages`
Benchmark metrics for comparison.

```sql
CREATE TABLE national_averages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    model_year INTEGER,                   -- NULL for overall, year for yearly
    fuel_type TEXT,
    description TEXT
);
```

#### `national_seasonal`
National monthly pass rate data.

```sql
CREATE TABLE national_seasonal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    UNIQUE(month)
);
```

### Database Indexes

All vehicle-specific tables have a composite index on `(make, model, model_year, fuel_type)` for efficient lookups:

```sql
CREATE INDEX idx_vi_lookup ON vehicle_insights(make, model, model_year, fuel_type);
CREATE INDEX idx_fc_lookup ON failure_categories(make, model, model_year, fuel_type);
-- ... (similar for all vehicle tables)
```

---

## 4. API Endpoints Reference

**Base URL**: `http://localhost:8010/api`

### Utility Endpoints

#### `GET /api/health`
Check API and database connectivity.

**Response**:
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

#### `GET /api/stats`
Get row counts for all tables in the database.

**Response**:
```json
{
  "available_vehicles": 11406,
  "vehicle_insights": 11406,
  "failure_categories": 114060,
  "top_defects": 228120,
  ...
}
```

---

### Vehicle Lookup Endpoints (Cascading Dropdowns)

These endpoints support the cascading dropdown pattern: Make → Model → Year/Fuel.

#### `GET /api/makes`
Get all available vehicle makes.

**Response**:
```json
["ABARTH", "AC", "ALFA ROMEO", "ASTON MARTIN", "AUDI", "BMW", ...]
```

---

#### `GET /api/makes/{make}/models`
Get all models for a specific make.

**Parameters**:
| Name | Type | In | Description |
|------|------|-----|-------------|
| `make` | string | path | Vehicle make (case-insensitive) |

**Example**: `GET /api/makes/FORD/models`

**Response**:
```json
["B-MAX", "C-MAX", "ECOSPORT", "EDGE", "FIESTA", "FOCUS", ...]
```

**Errors**:
- `404`: Make not found

---

#### `GET /api/makes/{make}/models/{model}/variants`
Get year/fuel type combinations for a make and model.

**Parameters**:
| Name | Type | In | Description |
|------|------|-----|-------------|
| `make` | string | path | Vehicle make |
| `model` | string | path | Vehicle model |

**Example**: `GET /api/makes/FORD/models/FOCUS/variants`

**Response**:
```json
[
  {
    "model_year": 2020,
    "fuel_type": "PE",
    "fuel_type_name": "Petrol",
    "total_tests": 45231
  },
  {
    "model_year": 2020,
    "fuel_type": "DI",
    "fuel_type_name": "Diesel",
    "total_tests": 12453
  },
  ...
]
```

**Errors**:
- `404`: Model not found

---

### Combined Vehicle Report

#### `GET /api/vehicle/{make}/{model}/{year}/{fuel}`
Get complete vehicle report with all key insights in a single request.

**Parameters**:
| Name | Type | In | Description |
|------|------|-----|-------------|
| `make` | string | path | Vehicle make |
| `model` | string | path | Vehicle model |
| `year` | integer | path | Model year (e.g., 2018) |
| `fuel` | string | path | Fuel type code (PE, DI, HY, EL, ED, GB, OT) |

**Example**: `GET /api/vehicle/FORD/FOCUS/2018/PE`

**Response**:
```json
{
  "vehicle": {
    "make": "FORD",
    "model": "FOCUS",
    "model_year": 2018,
    "fuel_type": "PE",
    "fuel_type_name": "Petrol"
  },
  "insights": {
    "total_tests": 89234,
    "total_passes": 68291,
    "total_fails": 15432,
    "total_prs": 5511,
    "pass_rate": 76.54,
    "initial_failure_rate": 23.46,
    "avg_mileage": 42156.0,
    "avg_age_years": 4.8,
    "national_pass_rate": 71.51,
    "pass_rate_vs_national": 5.03
  },
  "rankings": {
    "overall": {
      "ranking_type": "overall",
      "rank": 2341,
      "total_in_category": 11406,
      "pass_rate": 76.54,
      "percentile": 79
    },
    "within_make": {
      "ranking_type": "within_make",
      "rank": 12,
      "total_in_category": 156,
      "pass_rate": 76.54,
      "percentile": 92
    },
    "within_year": {
      "ranking_type": "within_year",
      "rank": 89,
      "total_in_category": 542,
      "pass_rate": 76.54,
      "percentile": 84
    }
  },
  "failure_categories": [
    {
      "category_name": "Lamps, reflectors and electrical equipment",
      "failure_count": 4521,
      "failure_percentage": 29.3,
      "rank": 1
    },
    ...
  ],
  "top_failures": [
    {
      "defect_description": "Headlamp aim too high",
      "category_name": "Lamps, reflectors and electrical equipment",
      "occurrence_count": 1234,
      "occurrence_percentage": 8.0,
      "rank": 1,
      "defect_type": "failure"
    },
    ...
  ],
  "top_advisories": [...],
  "dangerous_defects": [...],
  "mileage_bands": [
    {
      "mileage_band": "0-30k",
      "band_order": 0,
      "total_tests": 23451,
      "pass_rate": 82.3,
      "avg_mileage": 18234.0
    },
    ...
  ]
}
```

**Errors**:
- `404`: Vehicle not found

---

### Individual Data Endpoints

All endpoints below follow the pattern `/api/{resource}/{make}/{model}/{year}/{fuel}`:

#### `GET /api/insights/{make}/{model}/{year}/{fuel}`
Get core vehicle insights only.

**Response**: Single `vehicle_insights` row as JSON object.

---

#### `GET /api/failures/{make}/{model}/{year}/{fuel}`
Get failure categories (top 10).

**Response**: Array of `failure_categories` rows.

---

#### `GET /api/defects/{make}/{model}/{year}/{fuel}`
Get top defects, split by type.

**Response**:
```json
{
  "failures": [...],
  "advisories": [...]
}
```

---

#### `GET /api/dangerous/{make}/{model}/{year}/{fuel}`
Get dangerous defects only.

**Response**: Array of `dangerous_defects` rows.

---

#### `GET /api/mileage/{make}/{model}/{year}/{fuel}`
Get pass rates by mileage band.

**Response**: Array of `mileage_bands` rows.

---

#### `GET /api/rankings/{make}/{model}/{year}/{fuel}`
Get vehicle rankings with percentiles.

**Response**:
```json
{
  "overall": { "rank": 123, "total_in_category": 11406, "pass_rate": 76.5, "percentile": 89 },
  "within_make": { ... },
  "within_year": { ... }
}
```

---

#### `GET /api/geographic/{make}/{model}/{year}/{fuel}`
Get pass rates by UK postcode area.

**Response**: Array of `geographic_insights` rows, ordered by pass rate descending.

---

#### `GET /api/seasonal/{make}/{model}/{year}/{fuel}`
Get monthly pass rate patterns.

**Response**: Array of `seasonal_patterns` rows (12 months).

---

#### `GET /api/age/{make}/{model}/{year}/{fuel}`
Get pass rates by vehicle age band.

**Response**: Array of `age_bands` rows.

---

#### `GET /api/severity/{make}/{model}/{year}/{fuel}`
Get failure severity breakdown (minor/major/dangerous).

**Response**: Array of `failure_severity` rows.

---

#### `GET /api/first-mot/{make}/{model}/{year}/{fuel}`
Get first MOT vs subsequent comparison.

**Response**: Single `first_mot_insights` row or array with 'first' and 'subsequent' entries.

---

#### `GET /api/retest/{make}/{model}/{year}/{fuel}`
Get retest success metrics.

**Response**: Single `retest_success` row.

---

#### `GET /api/advisory-progression/{make}/{model}/{year}/{fuel}`
Get advisory-to-failure progression data.

**Response**: Array of `advisory_progression` rows.

---

#### `GET /api/component-thresholds/{make}/{model}/{year}/{fuel}`
Get component failure rates by mileage band.

**Response**: Array of `component_mileage_thresholds` rows.

---

#### `GET /api/defect-locations/{make}/{model}/{year}/{fuel}`
Get physical defect location distribution.

**Response**: Array of `defect_locations` rows.

---

### National/Aggregate Endpoints

#### `GET /api/national/averages`
Get national benchmark metrics.

**Response**:
```json
[
  {
    "id": 1,
    "metric_name": "overall_pass_rate",
    "metric_value": 71.51,
    "model_year": null,
    "fuel_type": null,
    "description": "National pass rate for Class 4 vehicles"
  },
  ...
]
```

---

#### `GET /api/national/seasonal`
Get national monthly pass rate data.

**Response**: Array of 12 `national_seasonal` rows.

---

#### `GET /api/manufacturers`
Get all manufacturer rankings.

**Response**: Array of `manufacturer_rankings` rows, ordered by rank.

---

#### `GET /api/manufacturers/{make}`
Get single manufacturer details.

**Parameters**:
| Name | Type | In | Description |
|------|------|-----|-------------|
| `make` | string | path | Manufacturer name |

**Example**: `GET /api/manufacturers/BMW`

**Response**:
```json
{
  "id": 15,
  "make": "BMW",
  "total_tests": 1234567,
  "total_models": 42,
  "avg_pass_rate": 74.2,
  "weighted_pass_rate": 73.8,
  "best_model": "1 SERIES",
  "best_model_pass_rate": 78.4,
  "worst_model": "X5",
  "worst_model_pass_rate": 68.2,
  "rank": 23
}
```

**Errors**:
- `404`: Manufacturer not found

---

## 5. Query Functions

All query functions are in `api/backend/queries.py`. Each function takes a database connection and returns dictionaries or lists.

### Vehicle Lookup Functions

#### `get_all_makes(conn)`
Returns list of all distinct makes, alphabetically sorted.

```python
# SQL: SELECT DISTINCT make FROM available_vehicles ORDER BY make
# Returns: ["ABARTH", "AC", "ALFA ROMEO", ...]
```

---

#### `get_models_for_make(conn, make)`
Returns list of models for a given make.

```python
# SQL: SELECT DISTINCT model FROM available_vehicles WHERE make = ? ORDER BY model
# Input normalized to uppercase
# Returns: ["FIESTA", "FOCUS", "MONDEO", ...]
```

---

#### `get_variants_for_model(conn, make, model)`
Returns year/fuel combinations with test counts.

```python
# SQL: SELECT model_year, fuel_type, total_tests FROM available_vehicles
#      WHERE make = ? AND model = ? ORDER BY model_year DESC, fuel_type
# Returns: [{"model_year": 2020, "fuel_type": "PE", "total_tests": 45231}, ...]
```

---

### Core Data Functions

#### `get_vehicle_insights(conn, make, model, year, fuel)`
Returns core statistics for a vehicle variant.

```python
# SQL: SELECT * FROM vehicle_insights WHERE make = ? AND model = ?
#      AND model_year = ? AND fuel_type = ?
# Returns: dict with pass_rate, total_tests, avg_mileage, etc. or None
```

---

#### `get_failure_categories(conn, make, model, year, fuel)`
Returns top 10 failure categories ranked by occurrence.

```python
# SQL: SELECT category_name, failure_count, failure_percentage, rank
#      FROM failure_categories WHERE ... ORDER BY rank
# Returns: list of dicts with category_name, failure_percentage, rank
```

---

#### `get_top_defects(conn, make, model, year, fuel)`
Returns top failures and advisories, split by type.

```python
# SQL: SELECT ... FROM top_defects WHERE ... ORDER BY defect_type, rank
# Returns: {"failures": [...], "advisories": [...]}
```

---

#### `get_dangerous_defects(conn, make, model, year, fuel)`
Returns dangerous defects only (safety-critical issues).

```python
# SQL: SELECT ... FROM dangerous_defects WHERE ... ORDER BY rank
# Returns: list of dicts with defect_description, occurrence_percentage
```

---

#### `get_mileage_bands(conn, make, model, year, fuel)`
Returns pass rates across 6 mileage bands.

```python
# SQL: SELECT mileage_band, band_order, total_tests, pass_rate, avg_mileage
#      FROM mileage_bands WHERE ... ORDER BY band_order
# Returns: list of 6 dicts (0-30k through 150k+)
```

---

#### `get_vehicle_rankings(conn, make, model, year, fuel)`
Returns rankings dictionary keyed by ranking type.

```python
# SQL: SELECT ranking_type, rank, total_in_category, pass_rate
#      FROM vehicle_rankings WHERE ...
# Returns: {"overall": {...}, "within_make": {...}, "within_year": {...}}
```

---

### Additional Analysis Functions

#### `get_geographic_insights(conn, make, model, year, fuel)`
Returns pass rates by UK postcode area, sorted best to worst.

---

#### `get_seasonal_patterns(conn, make, model, year, fuel)`
Returns monthly pass rates (1-12).

---

#### `get_age_bands(conn, make, model, year, fuel)`
Returns pass rates by vehicle age at test time.

---

#### `get_failure_severity(conn, make, model, year, fuel)`
Returns breakdown of minor/major/dangerous failures.

---

#### `get_first_mot_insights(conn, make, model, year, fuel)`
Returns comparison of first MOT vs subsequent tests.

---

#### `get_retest_success(conn, make, model, year, fuel)`
Returns retest rates and success percentages.

---

#### `get_advisory_progression(conn, make, model, year, fuel)`
Returns data on advisories that became failures.

---

#### `get_component_mileage_thresholds(conn, make, model, year, fuel)`
Returns component-level failure rates by mileage band.

---

#### `get_defect_locations(conn, make, model, year, fuel)`
Returns physical location distribution of defects.

---

### National/Aggregate Functions

#### `get_national_averages(conn)`
Returns all national benchmark metrics.

---

#### `get_national_seasonal(conn)`
Returns national monthly pass rates (12 rows).

---

#### `get_all_manufacturers(conn)`
Returns all manufacturers ranked by pass rate.

---

#### `get_manufacturer(conn, make)`
Returns single manufacturer details or None.

---

### Utility Functions

#### `get_table_stats(conn)`
Returns row counts for all 19 tables.

---

#### `check_vehicle_exists(conn, make, model, year, fuel)`
Returns boolean indicating if vehicle exists in database.

---

## 6. Frontend Features

The frontend (`api/frontend/index.html`) is a single-page developer explorer UI for testing and browsing API data.

### Tabs

1. **Vehicle Lookup** - Primary exploration interface
   - Cascading dropdowns: Make → Model → Year/Fuel
   - Quick-select buttons for common vehicles (Ford Focus, VW Golf, Tesla Model 3, etc.)
   - Full vehicle report display with cards and raw JSON

2. **Table Explorer** - Browse individual tables
   - Requires vehicle selection from Tab 1
   - 15 table buttons (Insights, Failures, Defects, Mileage, Rankings, etc.)
   - Shows endpoint URL and raw JSON response

3. **National Data** - Benchmark data
   - National averages button
   - National seasonal button
   - Raw JSON display

4. **Manufacturers** - Brand comparison
   - Load all manufacturers with card grid
   - Shows rank, pass rate, total tests, best/worst models

### Features

- **API Health Indicator**: Shows connection status in header
- **JSON Syntax Highlighting**: Color-coded keys, strings, numbers, booleans
- **Pass Rate Coloring**: Green (80%+), amber (65-80%), red (<65%)
- **Endpoint URL Display**: Shows exact API route for each request
- **Error Handling**: Displays error messages for failed requests
- **Responsive Design**: Works on various screen sizes

### Quick Vehicle Buttons

Pre-configured for testing:
- Ford Focus 2018 (Petrol)
- Vauxhall Corsa 2015 (Petrol)
- VW Golf 2017 (Diesel)
- BMW 3 Series 2018 (Diesel)
- Tesla Model 3 2020 (Electric)

---

## 7. Setup & Running

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone/download the project**:
   ```bash
   cd C:\Users\gregor\Downloads\Mot Data
   ```

2. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn
   ```

3. **Verify database exists**:
   ```bash
   ls data/database/mot_insights.db
   ```

### Running the Server

From the `api/` directory:

```bash
cd C:\Users\gregor\Downloads\Mot Data\api
python app.py
```

**Output**:
```
Starting MOT Insights...
  API:      http://localhost:8010/api
  Frontend: http://localhost:8010

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8010
```

### Access Points

| URL | Description |
|-----|-------------|
| http://localhost:8010 | Frontend explorer UI |
| http://localhost:8010/api/health | API health check |
| http://localhost:8010/api/docs | FastAPI auto-generated docs (Swagger) |
| http://localhost:8010/redoc | ReDoc API documentation |

### Alternative: Uvicorn Direct

```bash
cd C:\Users\gregor\Downloads\Mot Data\api
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

The `--reload` flag enables hot-reloading during development.

---

## 8. Data Dictionary

### Fuel Type Codes

| Code | Name | Description |
|------|------|-------------|
| `PE` | Petrol | Petrol/gasoline vehicles |
| `DI` | Diesel | Diesel vehicles |
| `HY` | Hybrid Electric | Conventional hybrid (not plug-in) |
| `EL` | Electric | Battery electric vehicles (BEV) |
| `ED` | Plug-in Hybrid | Plug-in hybrid electric (PHEV) |
| `GB` | Gas Bi-fuel | LPG or CNG bi-fuel |
| `OT` | Other | Other fuel types |

### Pass Rate Interpretation

| Range | Classification | Meaning |
|-------|----------------|---------|
| 80%+ | Good | Above average reliability |
| 65-80% | Average | Within normal range |
| <65% | Poor | Below average, potential issues |

**Note**: National average is **71.5%** (as of the dataset).

### Pass Rate vs National

The `pass_rate_vs_national` field shows the difference from the national average:

- **Positive values**: Vehicle performs better than average
- **Negative values**: Vehicle performs worse than average
- **Example**: `+5.03` means 5.03 percentage points above national

### Mileage Bands

| Band | Odometer Range (miles) |
|------|------------------------|
| 0-30k | 0 - 30,000 |
| 30k-60k | 30,001 - 60,000 |
| 60k-90k | 60,001 - 90,000 |
| 90k-120k | 90,001 - 120,000 |
| 120k-150k | 120,001 - 150,000 |
| 150k+ | Over 150,000 |

### Failure Categories

Standard MOT test categories:

| Category | Common Issues |
|----------|---------------|
| Lamps, reflectors and electrical equipment | Headlight aim, bulbs, indicators |
| Brakes | Pads, discs, brake lines, efficiency |
| Suspension | Shock absorbers, springs, bushings |
| Tyres | Tread depth, damage, pressure sensors |
| Steering | Joints, gaiters, play |
| Body, chassis, structure | Corrosion, damage |
| Noise, emissions and leaks | Exhaust, oil leaks, emissions |
| Visibility | Wipers, washer, windscreen |
| Road Wheels | Bearings, security, damage |
| Seat belts and supplementary restraint systems | Belts, airbag warning lights |

### Test Result Types

| Type | Description |
|------|-------------|
| **Pass** | Vehicle met all standards |
| **Fail** | One or more dangerous/major defects |
| **PRS** | Pass with Rectification at Station (minor issue fixed during test) |

### Defect Severity Levels

| Severity | Description | Outcome |
|----------|-------------|---------|
| **Minor** | Defect with no significant effect on safety | Advisory only |
| **Major** | Defect that may affect safety or environment | Test failure |
| **Dangerous** | Direct and immediate risk to road safety | Immediate prohibition |

### Ranking Types

| Type | Scope | Comparison |
|------|-------|------------|
| `overall` | All vehicles | Rank among all 11,406 variants |
| `within_make` | Same manufacturer | Rank among same brand's models |
| `within_year` | Same model year | Rank among vehicles of same age |

### Percentile Calculation

Percentile indicates position relative to others:

```
percentile = (1 - (rank / total_in_category)) * 100
```

- **90th percentile** = Better than 90% of vehicles in category
- **50th percentile** = Middle of the pack
- **10th percentile** = Bottom 10%

---

## Appendix: Example API Calls

### cURL Examples

```bash
# Health check
curl http://localhost:8010/api/health

# Get all makes
curl http://localhost:8010/api/makes

# Get models for Ford
curl http://localhost:8010/api/makes/FORD/models

# Get variants for Ford Focus
curl http://localhost:8010/api/makes/FORD/models/FOCUS/variants

# Get full vehicle report
curl http://localhost:8010/api/vehicle/FORD/FOCUS/2018/PE

# Get mileage bands only
curl http://localhost:8010/api/mileage/FORD/FOCUS/2018/PE

# Get manufacturer rankings
curl http://localhost:8010/api/manufacturers

# Get single manufacturer
curl http://localhost:8010/api/manufacturers/BMW
```

### JavaScript Fetch Examples

```javascript
// Get vehicle report
const response = await fetch('http://localhost:8010/api/vehicle/FORD/FOCUS/2018/PE');
const data = await response.json();
console.log(`Pass rate: ${data.insights.pass_rate}%`);

// Get all makes for dropdown
const makes = await fetch('http://localhost:8010/api/makes').then(r => r.json());
// makes = ["ABARTH", "AC", "ALFA ROMEO", ...]
```

### Python Requests Examples

```python
import requests

BASE = "http://localhost:8010/api"

# Get vehicle report
vehicle = requests.get(f"{BASE}/vehicle/FORD/FOCUS/2018/PE").json()
print(f"Pass rate: {vehicle['insights']['pass_rate']}%")

# Compare manufacturers
manufacturers = requests.get(f"{BASE}/manufacturers").json()
top_5 = manufacturers[:5]
for m in top_5:
    print(f"{m['rank']}. {m['make']}: {m['weighted_pass_rate']:.1f}%")
```

---

*End of Documentation*
