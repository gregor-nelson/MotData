# MOT Insights API - Implementation Guide

**Purpose**: Complete reference for implementing a Python FastAPI backend to serve MOT vehicle insights data.
**Database**: `mot_insights.db` (SQLite, 122.7 MB)
**Created**: 2026-01-01

---

## 1. Executive Summary

### What This API Will Serve
Pre-aggregated MOT test insights for 11,406 UK vehicle combinations (make/model/year/fuel), derived from 32.3 million MOT tests. The data is read-only and optimised for fast lookups.

### Primary Use Case
Vehicle report pages on motorwise.io showing:
- Pass rate vs national average (71.51%)
- Top failure categories and specific defects
- Mileage-based reliability breakdown
- Comparative rankings
- Safety-critical (dangerous) defects

### Key Lookup Pattern
All vehicle data uses a 4-part composite key:
```
make + model + model_year + fuel_type
Example: FORD + FOCUS + 2018 + PE
```

---

## 2. Database Overview

### Tables Summary (19 total)

| Table | Rows | Purpose | API Priority |
|-------|------|---------|--------------|
| `available_vehicles` | 11,406 | Index for dropdowns/search | HIGH |
| `vehicle_insights` | 11,406 | Core pass rates & stats | HIGH |
| `failure_categories` | 103,507 | Top 10 failure categories per vehicle | HIGH |
| `top_defects` | 225,881 | Top failures + advisories | HIGH |
| `dangerous_defects` | 105,879 | Safety-critical issues | HIGH |
| `mileage_bands` | 50,039 | Pass rate by mileage | HIGH |
| `vehicle_rankings` | 34,218 | Rankings (overall/make/year) | HIGH |
| `manufacturer_rankings` | 75 | Brand-level stats | MEDIUM |
| `national_averages` | 36 | Benchmark statistics | MEDIUM |
| `national_seasonal` | 12 | Monthly national averages | LOW |
| `geographic_insights` | 325,640 | Pass rate by postcode | LOW |
| `seasonal_patterns` | 122,368 | Monthly patterns per vehicle | LOW |
| `age_bands` | 13,892 | Pass rate by vehicle age | LOW |
| `failure_severity` | 22,707 | Major vs dangerous breakdown | LOW |
| `first_mot_insights` | 12,037 | First vs subsequent MOT | LOW |
| `advisory_progression` | 5,869 | Advisory-to-failure tracking | LOW |
| `retest_success` | 10,920 | Retest pass rates | LOW |
| `component_mileage_thresholds` | 77,475 | Component failure curves | LOW |
| `defect_locations` | 194,115 | Physical location of defects | LOW |

### Database Indexes
All tables have indexes on `(make, model, model_year, fuel_type)` for fast lookups.

---

## 3. Data Coverage

### Makes & Models
- **86 makes**: Ford, Vauxhall, VW, BMW, Audi, Mercedes, Tesla, etc.
- **11,406 vehicle combinations** with ≥100 tests each
- **Top makes by test volume**:
  - Ford: 4.4M tests (677 vehicles)
  - Vauxhall: 3.0M tests (521 vehicles)
  - Volkswagen: 2.9M tests (699 vehicles)

### Fuel Types
| Code | Name | Vehicles | Tests |
|------|------|----------|-------|
| PE | Petrol | 5,388 | 16.9M |
| DI | Diesel | 5,064 | 13.7M |
| HY | Hybrid Electric | 644 | 937K |
| EL | Electric | 218 | 228K |
| ED | Plug-in Hybrid | 71 | 28K |
| GB | Gas Bi-fuel | 2 | 341 |
| OT | Other | 19 | 7.5K |

### Year Range
Model years 2000-2023 (newer years have higher pass rates due to being newer cars)

### National Benchmarks
- **Overall pass rate**: 71.51%
- **Overall failure rate**: 28.49%
- **Average mileage at test**: 72,683 miles
- **Total tests analysed**: 32,265,974

---

## 4. Table Schemas & Sample Data

### 4.1 available_vehicles
**Purpose**: Index for cascading dropdowns (Make → Model → Year/Fuel)

```sql
CREATE TABLE available_vehicles (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    total_tests INTEGER NOT NULL,
    UNIQUE(make, model, model_year, fuel_type)
)
```

**Sample**:
```
FORD | FIESTA | 2015 | PE | 112,802 tests
FORD | FIESTA | 2014 | PE | 108,737 tests
VAUXHALL | CORSA | 2015 | PE | 83,417 tests
```

### 4.2 vehicle_insights
**Purpose**: Core statistics per vehicle

```sql
CREATE TABLE vehicle_insights (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    total_tests INTEGER NOT NULL,
    total_passes INTEGER NOT NULL,
    total_fails INTEGER NOT NULL,
    total_prs INTEGER NOT NULL,           -- Pass with Rectification at Station
    pass_rate REAL NOT NULL,              -- 0-100
    initial_failure_rate REAL NOT NULL,   -- 0-100 (= 100 - pass_rate)
    avg_mileage REAL,
    avg_age_years REAL,
    national_pass_rate REAL,              -- 71.51
    pass_rate_vs_national REAL            -- difference from national
)
```

**Sample** (Ford Focus 2018 PE):
```json
{
  "total_tests": 37330,
  "total_passes": 32102,
  "total_fails": 4078,
  "total_prs": 1150,
  "pass_rate": 86.0,
  "initial_failure_rate": 14.0,
  "avg_mileage": 34915,
  "avg_age_years": 4.3,
  "pass_rate_vs_national": 14.48
}
```

### 4.3 failure_categories
**Purpose**: Top 10 failure categories per vehicle

```sql
CREATE TABLE failure_categories (
    id INTEGER PRIMARY KEY,
    make TEXT, model TEXT, model_year INTEGER, fuel_type TEXT,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    failure_count INTEGER NOT NULL,
    failure_percentage REAL NOT NULL,
    rank INTEGER NOT NULL  -- 1-10
)
```

**Sample** (Ford Focus 2018 PE):
```
#1: Tyres - 2,088 failures (5.59%)
#2: Lamps, reflectors and electrical equipment - 1,559 (4.18%)
#3: Brakes - 963 (2.58%)
#4: Visibility - 636 (1.70%)
#5: Noise, emissions and leaks - 521 (1.40%)
```

**All 14 Categories**:
- Tyres
- Lamps, reflectors and electrical equipment
- Brakes
- Visibility
- Noise, emissions and leaks
- Suspension
- Body, chassis, structure
- Steering
- Road Wheels
- Identification of the vehicle
- Seat belts and supplementary restraint systems
- Towbars
- Driver Controls
- Other equipment

### 4.4 top_defects
**Purpose**: Top 10 failure defects + Top 10 advisory defects per vehicle

```sql
CREATE TABLE top_defects (
    id INTEGER PRIMARY KEY,
    make TEXT, model TEXT, model_year INTEGER, fuel_type TEXT,
    rfr_id INTEGER NOT NULL,              -- Reason for Rejection ID
    defect_description TEXT NOT NULL,
    category_name TEXT,
    defect_type TEXT NOT NULL,            -- 'failure' OR 'advisory'
    occurrence_count INTEGER NOT NULL,
    occurrence_percentage REAL NOT NULL,
    rank INTEGER NOT NULL                 -- 1-10 within each type
)
```

**Sample Failures** (Ford Focus 2018 PE):
```
#1: tread depth below requirements of 1.6mm (2.18%)
#2: less than 1.5 mm thick [brake disc] (2.14%)
#3: has a cut in excess of the requirements deep enough to reach the ply or cords (1.22%)
```

**Sample Advisories** (Ford Focus 2018 PE):
```
#1: worn close to legal limit/worn on edge [tyres] (15.35%)
#2: wearing thin [brakes] (11.42%)
#3: slightly damaged/cracking or perishing (8.75%)
```

**Important**: Filter by `defect_type = 'failure'` or `defect_type = 'advisory'`

### 4.5 dangerous_defects
**Purpose**: Top 10 safety-critical defects per vehicle

```sql
CREATE TABLE dangerous_defects (
    id INTEGER PRIMARY KEY,
    make TEXT, model TEXT, model_year INTEGER, fuel_type TEXT,
    rfr_id INTEGER NOT NULL,
    defect_description TEXT NOT NULL,
    category_name TEXT,
    occurrence_count INTEGER NOT NULL,
    occurrence_percentage REAL NOT NULL,
    rank INTEGER NOT NULL
)
```

**Sample** (Ford Focus 2018 PE):
```
#1: tread depth below requirements of 1.6mm (16.71%)
#2: less than 1.5 mm thick [brake disc] (13.02%)
#3: has a tear, caused by separation or partial failure of its structure (9.01%)
```

### 4.6 mileage_bands
**Purpose**: Pass rate breakdown by mileage

```sql
CREATE TABLE mileage_bands (
    id INTEGER PRIMARY KEY,
    make TEXT, model TEXT, model_year INTEGER, fuel_type TEXT,
    mileage_band TEXT NOT NULL,    -- '0-30k', '30k-60k', etc.
    band_order INTEGER NOT NULL,   -- 0-5 for sorting
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_mileage REAL
)
```

**Bands**:
| band_order | mileage_band | Range |
|------------|--------------|-------|
| 0 | 0-30k | 0-30,000 miles |
| 1 | 30k-60k | 30,001-60,000 |
| 2 | 60k-90k | 60,001-90,000 |
| 3 | 90k-120k | 90,001-120,000 |
| 4 | 120k-150k | 120,001-150,000 |
| 5 | 150k+ | 150,001+ |

**Sample** (Ford Focus 2018 PE):
```
0-30k:    89.9% pass (15,251 tests)
30k-60k:  84.1% pass (19,702 tests)
60k-90k:  76.9% pass (2,150 tests)
90k-120k: 72.2% pass (187 tests)
```

### 4.7 vehicle_rankings
**Purpose**: Comparative rankings

```sql
CREATE TABLE vehicle_rankings (
    id INTEGER PRIMARY KEY,
    make TEXT, model TEXT, model_year INTEGER, fuel_type TEXT,
    ranking_type TEXT NOT NULL,      -- 'overall', 'within_make', 'within_year'
    rank INTEGER NOT NULL,
    total_in_category INTEGER NOT NULL,
    pass_rate REAL NOT NULL
)
```

**Sample** (Ford Focus 2018 PE):
```
overall:     #2,815 of 11,406 (top 75%)
within_make: #134 of 677 (top 80%)
within_year: #281 of 641 (top 56%)
```

### 4.8 manufacturer_rankings
**Purpose**: Brand-level aggregated rankings

```sql
CREATE TABLE manufacturer_rankings (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL UNIQUE,
    total_tests INTEGER NOT NULL,
    total_models INTEGER NOT NULL,
    avg_pass_rate REAL NOT NULL,
    weighted_pass_rate REAL NOT NULL,
    best_model TEXT,
    best_model_pass_rate REAL,
    worst_model TEXT,
    worst_model_pass_rate REAL,
    rank INTEGER NOT NULL
)
```

**Top 5**:
```
#1: Rolls Royce - 94.72%
#2: Lamborghini - 94.70%
#3: Ferrari - 94.55%
#4: McLaren - 94.31%
#5: Bentley - 91.64%
```

**Bottom 5**:
```
#71: Rover - 58.86%
#72: Proton - 54.70%
#73: LDV - 54.54%
#74: Chevrolet - 54.36%
#75: Daewoo - 49.41%
```

### 4.9 national_averages
**Purpose**: Benchmark statistics

```sql
CREATE TABLE national_averages (
    id INTEGER PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    model_year INTEGER,        -- NULL for overall
    fuel_type TEXT,            -- NULL for overall
    description TEXT
)
```

**Key Metrics**:
- `overall_pass_rate`: 71.51%
- `overall_initial_failure_rate`: 28.49%
- `overall_avg_mileage`: 72,683
- `total_tests`: 32,265,974
- `yearly_pass_rate` (per year 2000-2023)
- `fuel_type_pass_rate` (per fuel type)

**Pass Rate by Fuel Type**:
- Plug-in Hybrid: 85.32%
- Hybrid: 84.88%
- Electric: 84.59%
- Petrol: 71.90%
- Diesel: 69.85%

### 4.10 Other Tables (Lower Priority)

#### geographic_insights
Pass rates by UK postcode area (118 areas). Example: Birmingham (B) has different rates than Glasgow (G).

#### seasonal_patterns
Monthly pass rates per vehicle. March typically highest, November lowest.

#### age_bands
Pass rate by vehicle age at test (3-4 years, 5-6 years, etc.). Only for vehicles with enough age spread.

#### failure_severity
Breakdown of failure items by severity ('major' vs 'dangerous'). Note: 'minor' defects don't cause failures.

#### first_mot_insights
Compares first MOT (3-4 year old car) vs subsequent MOTs. First MOTs typically pass more.

#### retest_success
Tracks retest outcomes. Key finding: 99.3% of retests pass.

#### advisory_progression
Tracks when advisories become failures. Very low progression rate (~0.2%).

#### component_mileage_thresholds
Shows when specific components (brakes, lamps, etc.) start failing more at different mileages.

#### defect_locations
Physical location distribution (Nearside Front, Offside Rear, etc.).

---

## 5. Recommended API Endpoints

### 5.1 Core Endpoints (MVP)

```
GET /api/makes
  Returns: List of all 86 makes, sorted alphabetically
  Example: ["ABARTH", "ALFA ROMEO", "ASTON MARTIN", ...]

GET /api/makes/{make}/models
  Returns: List of models for a make
  Example: GET /api/makes/FORD/models → ["ECOSPORT", "FIESTA", "FOCUS", ...]

GET /api/makes/{make}/models/{model}/years
  Returns: Available year/fuel combinations with test counts
  Example: GET /api/makes/FORD/models/FOCUS/years →
  [
    {"year": 2023, "fuel_type": "PE", "fuel_name": "Petrol", "total_tests": 1234},
    {"year": 2023, "fuel_type": "DI", "fuel_name": "Diesel", "total_tests": 567},
    {"year": 2022, "fuel_type": "PE", "fuel_name": "Petrol", "total_tests": 8901},
    ...
  ]

GET /api/vehicle/{make}/{model}/{year}/{fuel}
  Returns: Complete vehicle report (see Section 6)
  Example: GET /api/vehicle/FORD/FOCUS/2018/PE
```

### 5.2 Additional Endpoints

```
GET /api/national/averages
  Returns: National benchmark statistics

GET /api/manufacturers
  Returns: All manufacturer rankings

GET /api/manufacturers/{make}
  Returns: Single manufacturer details

GET /api/vehicle/{make}/{model}/{year}/{fuel}/geographic
  Returns: Geographic breakdown (optional, large response)

GET /api/vehicle/{make}/{model}/{year}/{fuel}/seasonal
  Returns: Seasonal patterns (optional)
```

---

## 6. Vehicle Report Response Structure

The main vehicle endpoint should return a combined response:

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
    "total_tests": 37330,
    "total_passes": 32102,
    "total_fails": 4078,
    "total_prs": 1150,
    "pass_rate": 86.0,
    "initial_failure_rate": 14.0,
    "avg_mileage": 34915,
    "avg_age_years": 4.3,
    "national_pass_rate": 71.51,
    "pass_rate_vs_national": 14.48
  },

  "rankings": {
    "overall": {"rank": 2815, "total": 11406, "percentile": 75},
    "within_make": {"rank": 134, "total": 677, "percentile": 80},
    "within_year": {"rank": 281, "total": 641, "percentile": 56}
  },

  "failure_categories": [
    {"rank": 1, "name": "Tyres", "count": 2088, "percentage": 5.59},
    {"rank": 2, "name": "Lamps, reflectors and electrical equipment", "count": 1559, "percentage": 4.18},
    ...
  ],

  "top_failures": [
    {"rank": 1, "description": "tread depth below requirements of 1.6mm", "category": "Tyres", "percentage": 2.18},
    ...
  ],

  "top_advisories": [
    {"rank": 1, "description": "worn close to legal limit/worn on edge", "category": "Tyres", "percentage": 15.35},
    ...
  ],

  "dangerous_defects": [
    {"rank": 1, "description": "tread depth below requirements of 1.6mm", "category": "Tyres", "percentage": 16.71},
    ...
  ],

  "mileage_bands": [
    {"band": "0-30k", "order": 0, "tests": 15251, "pass_rate": 89.9, "avg_mileage": 21044},
    {"band": "30k-60k", "order": 1, "tests": 19702, "pass_rate": 84.1, "avg_mileage": 41141},
    ...
  ]
}
```

---

## 7. Query Patterns

### Get All Makes
```sql
SELECT DISTINCT make FROM available_vehicles ORDER BY make
```

### Get Models for Make
```sql
SELECT DISTINCT model FROM available_vehicles
WHERE make = ? ORDER BY model
```

### Get Years/Fuels for Make+Model
```sql
SELECT model_year, fuel_type, total_tests
FROM available_vehicles
WHERE make = ? AND model = ?
ORDER BY model_year DESC, fuel_type
```

### Get Complete Vehicle Data
```sql
-- Core insights
SELECT * FROM vehicle_insights
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?

-- Failure categories
SELECT category_name, failure_count, failure_percentage, rank
FROM failure_categories
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY rank

-- Top failures
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM top_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
  AND defect_type = 'failure'
ORDER BY rank

-- Top advisories
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM top_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
  AND defect_type = 'advisory'
ORDER BY rank

-- Dangerous defects
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM dangerous_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY rank

-- Mileage bands
SELECT mileage_band, band_order, total_tests, pass_rate, avg_mileage
FROM mileage_bands
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY band_order

-- Rankings
SELECT ranking_type, rank, total_in_category, pass_rate
FROM vehicle_rankings
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
```

---

## 8. Implementation Notes

### Technology Stack
- **Framework**: FastAPI (Python)
- **Database**: sqlite3 (built-in, synchronous is fine for read-only)
- **Deployment**: Uvicorn, behind nginx in production

### URL Encoding
Model names may contain spaces and special characters:
- "GOLF GTI" → needs URL encoding
- "C-HR" → hyphen is fine
- Consider URL-safe slugs or query params as alternative

### Error Handling
```python
# 404 if vehicle not found
if not vehicle_data:
    raise HTTPException(
        status_code=404,
        detail="Vehicle not found. Minimum 100 tests required for inclusion."
    )
```

### CORS
For MVP (different ports), enable CORS:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

### Connection Pooling
For SQLite, a simple approach:
```python
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "mot_insights.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

### Fuel Type Mapping
```python
FUEL_TYPES = {
    "PE": "Petrol",
    "DI": "Diesel",
    "HY": "Hybrid Electric",
    "EL": "Electric",
    "ED": "Plug-in Hybrid",
    "GB": "Gas Bi-fuel",
    "OT": "Other"
}
```

### Percentile Calculation
```python
def calculate_percentile(rank: int, total: int) -> int:
    return round((1 - (rank / total)) * 100)
```

---

## 9. Key Data Insights

### Pass Rate Patterns
- **Newer cars pass more**: 2023 models: 97.8% vs 2000 models: 60.6%
- **Hybrids/EVs outperform**: 85% vs Petrol: 72% vs Diesel: 70%
- **Mileage degrades pass rate**: 0-30k: ~90% vs 150k+: ~55%
- **March best month**: 73% vs November worst: 70%

### Best/Worst Performers (≥1000 tests)
**Best**:
- Honda Jazz Crosstar EX (2020 Hybrid): 96.1%
- Porsche Cayman (2019 Petrol): 96.0%
- Lexus RX (2020 Hybrid): 96.0%

**Worst**:
- Nissan Qashqai (2008 Diesel): 41.9%
- Nissan Qashqai (2009 Diesel): 42.3%
- Renault Megane (2006 Diesel): 42.8%

### Retest Success
- 99.3% of retests within 30 days pass
- About 60% of failed vehicles return for retest

### Common Failure Categories
1. Tyres (most common)
2. Lamps/electrical
3. Brakes
4. Visibility (wipers, washers)
5. Emissions

---

## 10. Frontend Integration Notes

### Cascading Dropdown Flow
```
1. Load page → GET /api/makes → populate Make dropdown
2. Select make → GET /api/makes/{make}/models → populate Model dropdown
3. Select model → GET /api/makes/{make}/models/{model}/years → populate Year dropdown
4. Select year → Show fuel type options if multiple
5. Submit → GET /api/vehicle/{make}/{model}/{year}/{fuel} → display report
```

### Colour Coding Pass Rates
```javascript
function getPassRateColour(passRate, national = 71.51) {
  const diff = passRate - national;
  if (diff >= 10) return 'emerald';  // Excellent
  if (diff >= 0) return 'green';     // Good
  if (diff >= -5) return 'amber';    // Average
  if (diff >= -10) return 'orange';  // Below Average
  return 'red';                       // Poor
}
```

### Display Rankings as Percentiles
"Top 25%" is more intuitive than "#2815 of 11406"

---

## 11. File Locations

```
/mot_data_2023/
├── mot_insights.db              # SQLite database (122.7 MB)
├── MOT_INSIGHTS_REFERENCE.md    # Original technical reference
├── API_IMPLEMENTATION_GUIDE.md  # This document
└── (source CSVs and scripts)
```

---

## 12. Next Steps for Implementation

1. **Create FastAPI app** with basic structure
2. **Implement core endpoints** (makes, models, years, vehicle report)
3. **Test with sample queries** (Ford Focus 2018 PE is a good test case)
4. **Add error handling** (404 for missing vehicles)
5. **Create simple frontend** (static HTML + vanilla JS)
6. **Test end-to-end** with cascading dropdowns

---

*Document created: 2026-01-01*
*Ready for implementation in a new session*
