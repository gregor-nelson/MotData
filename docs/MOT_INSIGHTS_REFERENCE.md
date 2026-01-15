# MOT Insights Database - Complete Technical Reference

## Document Purpose

This document provides a complete technical reference for integrating the MOT Insights database (`mot_insights.db`) with a backend API and frontend application for motorwise.io vehicle reports.

**Created:** 2026-01-01
**Data Source:** DVSA MOT Bulk Data 2023
**Database Format:** SQLite
**Database Size:** ~122.7 MB

---

## Table of Contents

1. [Overview](#1-overview)
2. [Database Schema](#2-database-schema)
3. [Data Summary](#3-data-summary)
4. [Table Reference](#4-table-reference)
5. [Query Patterns](#5-query-patterns)
6. [API Design Recommendations](#6-api-design-recommendations)
7. [TypeScript Interfaces](#7-typescript-interfaces)
8. [Frontend Integration Guide](#8-frontend-integration-guide)
9. [Important Notes & Caveats](#9-important-notes--caveats)
10. [Verification Queries](#10-verification-queries)

---

## 1. Overview

### What This Database Contains

Pre-aggregated MOT test insights for UK vehicles, derived from 42+ million MOT tests and 89+ million defect records. The data has been processed to provide:

- Pass rates and failure statistics per vehicle (make/model/year/fuel)
- Top failure categories and specific defects
- Dangerous defect tracking
- Mileage and age-based analysis
- Geographic insights by postcode area
- Manufacturer rankings
- Seasonal patterns
- Retest success rates
- Advisory-to-failure progression tracking

### Key Lookup Pattern

All vehicle-specific data is keyed by four fields:
```
make + model + model_year + fuel_type
```

Example: `FORD` + `FOCUS` + `2018` + `PE` (Petrol)

### Minimum Sample Size

All statistics require a minimum of **100 tests** per vehicle combination to ensure statistical validity. Smaller sample sizes are excluded.

---

## 2. Database Schema

### Entity Relationship Overview

```
available_vehicles (index)
    │
    └─── vehicle_insights (core stats)
            │
            ├─── failure_categories (top 10 per vehicle)
            ├─── top_defects (top 10 failures + top 10 advisories)
            ├─── dangerous_defects (top 10 safety issues)
            ├─── mileage_bands (pass rates by mileage)
            ├─── age_bands (pass rates by vehicle age)
            ├─── vehicle_rankings (comparative rankings)
            ├─── geographic_insights (by postcode area)
            ├─── seasonal_patterns (monthly pass rates)
            ├─── failure_severity (major/dangerous breakdown)
            ├─── first_mot_insights (first vs subsequent MOT)
            ├─── advisory_progression (advisory→failure tracking)
            ├─── retest_success (retest pass rates)
            └─── component_mileage_thresholds (failure rate curves)

national_averages (benchmarks - not vehicle-specific)
national_seasonal (monthly national averages)
manufacturer_rankings (brand-level stats)
```

### All 19 Tables

| Table | Rows | Description |
|-------|------|-------------|
| available_vehicles | 11,406 | Index of all queryable vehicle combinations |
| vehicle_insights | 11,406 | Core statistics per vehicle |
| failure_categories | 103,507 | Top 10 failure categories per vehicle |
| top_defects | 225,881 | Top 10 failures + top 10 advisories per vehicle |
| dangerous_defects | 105,879 | Top 10 dangerous defects per vehicle |
| mileage_bands | 50,039 | Pass rates by mileage band |
| age_bands | 13,892 | Pass rates by vehicle age band |
| vehicle_rankings | 34,218 | Rankings (overall, within_make, within_year) |
| geographic_insights | 325,640 | Pass rates by postcode area |
| seasonal_patterns | 122,368 | Monthly pass rates per vehicle |
| failure_severity | 22,707 | Major vs dangerous breakdown |
| first_mot_insights | 12,037 | First MOT vs subsequent comparison |
| advisory_progression | 5,869 | Advisory→failure progression stats |
| retest_success | 10,920 | Retest pass rates |
| component_mileage_thresholds | 77,475 | Component failure rates by mileage |
| national_averages | 36 | National benchmark statistics |
| national_seasonal | 12 | National monthly averages |
| manufacturer_rankings | 75 | Brand-level rankings |
| defect_locations | 194,115 | Defect distribution by location |

---

## 3. Data Summary

### Coverage

| Dimension | Count | Range/Values |
|-----------|-------|--------------|
| Makes | 86 | ABARTH to YAMAHA |
| Models | 2,182 | Various |
| Years | 24 | 2000 - 2023 |
| Fuel Types | 7 | PE, DI, HY, EL, ED, GB, OT |
| Vehicle Combinations | 11,406 | With ≥100 tests each |
| Total Tests Analyzed | 32,265,974 | Class 4, Normal Tests only |

### Fuel Type Codes

| Code | Meaning |
|------|---------|
| PE | Petrol |
| DI | Diesel |
| HY | Hybrid Electric (Clean) |
| EL | Electric |
| ED | Electric Diesel (Plug-in Hybrid Diesel) |
| GB | Gas Bi-fuel |
| OT | Other |

### National Benchmarks

| Metric | Value |
|--------|-------|
| National Pass Rate | 71.51% |
| National Initial Failure Rate | 28.49% |
| Average Mileage at Test | 72,683 miles |
| Total Tests in Dataset | 32,265,974 |

---

## 4. Table Reference

### 4.1 available_vehicles

**Purpose:** Index of all queryable vehicle combinations. Use this for search/autocomplete.

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

**Sample Data:**
```
FORD | FIESTA | 2015 | PE | 112,802
FORD | FIESTA | 2014 | PE | 108,737
FORD | FIESTA | 2016 | PE | 104,024
```

---

### 4.2 vehicle_insights

**Purpose:** Core statistics for each vehicle combination.

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
    pass_rate REAL NOT NULL,              -- Percentage (0-100)
    initial_failure_rate REAL NOT NULL,   -- Percentage (0-100)
    avg_mileage REAL,                     -- Average mileage at test
    avg_age_years REAL,                   -- Average vehicle age at test
    national_pass_rate REAL,              -- 71.51 (constant for comparison)
    pass_rate_vs_national REAL,           -- Difference from national average
    UNIQUE(make, model, model_year, fuel_type)
)
```

**Key Formulas:**
- `pass_rate = (total_passes / total_tests) * 100`
- `initial_failure_rate = ((total_fails + total_prs) / total_tests) * 100`
- `pass_rate + initial_failure_rate = 100`

**Sample Data:**
```
FORD | FOCUS | 2018 | PE
  total_tests: 37,330
  total_passes: 32,102
  total_fails: 4,078
  total_prs: 1,150
  pass_rate: 86.0%
  initial_failure_rate: 14.0%
  avg_mileage: 34,915
  avg_age_years: 4.3
  pass_rate_vs_national: +14.48%
```

---

### 4.3 failure_categories

**Purpose:** Top 10 failure categories per vehicle, ranked by frequency.

```sql
CREATE TABLE failure_categories (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    failure_count INTEGER NOT NULL,      -- Distinct tests with this category failure
    failure_percentage REAL NOT NULL,    -- % of total tests
    rank INTEGER NOT NULL                -- 1-10
)
```

**Available Categories (14):**
- Brakes
- Suspension
- Tyres
- Lamps, reflectors and electrical equipment
- Body, chassis, structure
- Visibility
- Noise, emissions and leaks
- Steering
- Road Wheels
- Seat belts and supplementary restraint systems
- Identification of the vehicle
- Towbars
- Driver Controls
- Other equipment

**Sample Data:**
```
FORD | FOCUS | 2018 | PE
  #1: Tyres - 2,088 failures (5.59%)
  #2: Lamps, reflectors and electrical equipment - 1,559 failures (4.18%)
  #3: Brakes - 963 failures (2.58%)
```

---

### 4.4 top_defects

**Purpose:** Top 10 failure defects AND top 10 advisory defects per vehicle.

```sql
CREATE TABLE top_defects (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    rfr_id INTEGER NOT NULL,             -- Reason for Rejection ID
    defect_description TEXT NOT NULL,
    category_name TEXT,
    defect_type TEXT NOT NULL,           -- 'failure' or 'advisory'
    occurrence_count INTEGER NOT NULL,   -- Distinct tests with this defect
    occurrence_percentage REAL NOT NULL, -- % of total tests
    rank INTEGER NOT NULL                -- 1-10 within defect_type
)
```

**Important:** Filter by `defect_type` when querying:
- `defect_type = 'failure'` → Items that caused test failures
- `defect_type = 'advisory'` → Warning items (monitor for future issues)

**Sample Data:**
```
FORD | FOCUS | 2018 | PE | failure
  #1: tread depth below requirements of 1.6mm (Tyres) - 892 (2.39%)
  #2: not working (Lamps) - 612 (1.64%)

FORD | FOCUS | 2018 | PE | advisory
  #1: worn close to legal limit/worn on edge (Tyres) - 5,730 (15.35%)
  #2: wearing thin (Brakes) - 4,263 (11.42%)
```

---

### 4.5 dangerous_defects

**Purpose:** Top 10 dangerous/safety-critical defects per vehicle.

```sql
CREATE TABLE dangerous_defects (
    id INTEGER PRIMARY KEY,
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
```

**Most Common Dangerous Defects (across all vehicles):**
1. Tread depth below requirements of 1.6mm (Tyres)
2. Brake disc less than 1.5mm thick (Brakes)
3. Brake disc seriously weakened (Brakes)
4. Tyre has tear/separation (Tyres)
5. Tread pattern not visible (Tyres)

---

### 4.6 mileage_bands

**Purpose:** Pass rates broken down by mileage band.

```sql
CREATE TABLE mileage_bands (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    mileage_band TEXT NOT NULL,    -- '0-30k', '30k-60k', etc.
    band_order INTEGER NOT NULL,   -- 0-5 for sorting
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_mileage REAL
)
```

**Mileage Bands:**
| band_order | mileage_band | Range |
|------------|--------------|-------|
| 0 | 0-30k | 0 - 30,000 miles |
| 1 | 30k-60k | 30,001 - 60,000 miles |
| 2 | 60k-90k | 60,001 - 90,000 miles |
| 3 | 90k-120k | 90,001 - 120,000 miles |
| 4 | 120k-150k | 120,001 - 150,000 miles |
| 5 | 150k+ | 150,001+ miles |

**Sample Data:**
```
FORD | FOCUS | 2018 | PE
  0-30k: 15,251 tests, 89.92% pass rate
  30k-60k: 19,702 tests, 84.14% pass rate
  60k-90k: 2,150 tests, 76.93% pass rate
  90k-120k: 187 tests, 72.19% pass rate
```

---

### 4.7 age_bands

**Purpose:** Pass rates broken down by vehicle age at test.

```sql
CREATE TABLE age_bands (
    id INTEGER PRIMARY KEY,
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
```

**Age Bands:**
| band_order | age_band |
|------------|----------|
| 0 | 3-4 years |
| 1 | 5-6 years |
| 2 | 7-8 years |
| 3 | 9-10 years |
| 4 | 11-12 years |
| 5 | 13+ years |

---

### 4.8 vehicle_rankings

**Purpose:** Comparative rankings for each vehicle.

```sql
CREATE TABLE vehicle_rankings (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    ranking_type TEXT NOT NULL,      -- 'overall', 'within_make', 'within_year'
    rank INTEGER NOT NULL,
    total_in_category INTEGER NOT NULL,
    pass_rate REAL NOT NULL
)
```

**Ranking Types:**
- `overall` - Rank among all 11,406 vehicle combinations
- `within_make` - Rank among same manufacturer's vehicles
- `within_year` - Rank among same model year vehicles

**Sample Data:**
```
FORD | FOCUS | 2018 | PE
  overall: #2,815 of 11,406 (86.0%)
  within_make: #134 of 677 (86.0%)
  within_year: #281 of 641 (86.0%)
```

---

### 4.9 manufacturer_rankings

**Purpose:** Brand-level aggregated rankings.

```sql
CREATE TABLE manufacturer_rankings (
    id INTEGER PRIMARY KEY,
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
```

**Top 10 Manufacturers by Pass Rate:**
1. Rolls Royce - 94.72%
2. Lamborghini - 94.70%
3. Ferrari - 94.55%
4. McLaren - 94.31%
5. Bentley - 91.64%
6. Aston Martin - 91.33%
7. Yamaha - 89.96%
8. Polestar - 89.32%
9. TVR - 89.18%
10. LEVC - 88.59%

---

### 4.10 geographic_insights

**Purpose:** Pass rates by UK postcode area.

```sql
CREATE TABLE geographic_insights (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    postcode_area TEXT NOT NULL,   -- e.g., 'B', 'M', 'SW', 'EH'
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL
)
```

**Note:** 118 unique postcode areas in dataset.

---

### 4.11 seasonal_patterns

**Purpose:** Monthly pass rate patterns per vehicle.

```sql
CREATE TABLE seasonal_patterns (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    month INTEGER NOT NULL,        -- 1-12
    quarter INTEGER NOT NULL,      -- 1-4
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL
)
```

---

### 4.12 national_seasonal

**Purpose:** National monthly averages for comparison.

```sql
CREATE TABLE national_seasonal (
    id INTEGER PRIMARY KEY,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    UNIQUE(month)
)
```

**Data:**
| Month | Tests | Pass Rate |
|-------|-------|-----------|
| Jan | 2,919,900 | 70.50% |
| Feb | 2,676,832 | 71.35% |
| Mar | 3,361,656 | 73.01% |
| ... | ... | ... |

---

### 4.13 failure_severity

**Purpose:** Breakdown of failures by severity level.

```sql
CREATE TABLE failure_severity (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    severity TEXT NOT NULL,           -- 'major' or 'dangerous'
    failure_count INTEGER NOT NULL,   -- Count of defect items
    failure_percentage REAL NOT NULL  -- % of total failure items
)
```

**Important Note:** Only contains 'major' and 'dangerous' - no 'minor'. This is correct because Minor defects don't cause MOT failures in the UK system.

---

### 4.14 first_mot_insights

**Purpose:** Compare first MOT (3-4 years old) vs subsequent MOTs.

```sql
CREATE TABLE first_mot_insights (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    mot_type TEXT NOT NULL,           -- 'first' or 'subsequent'
    total_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_mileage REAL,
    avg_defects_per_fail REAL
)
```

---

### 4.15 advisory_progression

**Purpose:** Track how often advisories become failures on subsequent tests.

```sql
CREATE TABLE advisory_progression (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    advisory_count INTEGER NOT NULL,        -- Vehicles with advisory in this category
    progressed_to_failure INTEGER NOT NULL, -- Of those, how many later failed
    progression_rate REAL NOT NULL,         -- Percentage
    avg_days_to_failure REAL,
    avg_miles_to_failure REAL
)
```

---

### 4.16 retest_success

**Purpose:** Track retest pass rates within 30 days.

```sql
CREATE TABLE retest_success (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    failed_tests INTEGER NOT NULL,
    retested_within_30_days INTEGER NOT NULL,
    passed_on_retest INTEGER NOT NULL,
    retest_rate REAL NOT NULL,         -- % who came back for retest
    retest_success_rate REAL NOT NULL  -- % of retests that passed
)
```

**Key Finding:** Average retest success rate is 99.27% - very high!

---

### 4.17 component_mileage_thresholds

**Purpose:** Show when specific components start failing more frequently.

```sql
CREATE TABLE component_mileage_thresholds (
    id INTEGER PRIMARY KEY,
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
    spike_mileage_band TEXT,     -- Band where failures increase significantly
    spike_increase_pct REAL      -- Percentage increase at spike
)
```

---

### 4.18 defect_locations

**Purpose:** Physical location distribution of defects.

```sql
CREATE TABLE defect_locations (
    id INTEGER PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    location_id INTEGER NOT NULL,
    lateral TEXT,          -- 'Nearside', 'Offside', 'Central', NULL
    longitudinal TEXT,     -- 'Front', 'Rear', NULL
    vertical TEXT,         -- 'Inner', 'Outer', 'Upper', 'Lower', NULL
    failure_count INTEGER NOT NULL,
    failure_percentage REAL NOT NULL
)
```

---

### 4.19 national_averages

**Purpose:** National benchmark statistics.

```sql
CREATE TABLE national_averages (
    id INTEGER PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    model_year INTEGER,        -- NULL for overall metrics
    fuel_type TEXT,            -- NULL for overall metrics
    description TEXT
)
```

**Metric Names:**
- `overall_pass_rate` - 71.51%
- `overall_initial_failure_rate` - 28.49%
- `overall_avg_mileage` - 72,683
- `total_tests` - 32,265,974
- `yearly_pass_rate` - One per year (2000-2023)
- `fuel_type_pass_rate` - One per fuel type

---

## 5. Query Patterns

### 5.1 Get Available Vehicles by Make

```sql
SELECT DISTINCT model, model_year, fuel_type, total_tests
FROM available_vehicles
WHERE make = 'FORD'
ORDER BY model, model_year DESC;
```

### 5.2 Get All Makes (for dropdown)

```sql
SELECT DISTINCT make
FROM available_vehicles
ORDER BY make;
```

### 5.3 Get Models for a Make

```sql
SELECT DISTINCT model
FROM available_vehicles
WHERE make = 'FORD'
ORDER BY model;
```

### 5.4 Get Years for Make/Model

```sql
SELECT DISTINCT model_year, fuel_type, total_tests
FROM available_vehicles
WHERE make = 'FORD' AND model = 'FOCUS'
ORDER BY model_year DESC;
```

### 5.5 Get Complete Vehicle Profile

```sql
-- Core insights
SELECT * FROM vehicle_insights
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?;

-- Failure categories (top 10)
SELECT category_name, failure_count, failure_percentage, rank
FROM failure_categories
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY rank;

-- Top failure defects
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM top_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
  AND defect_type = 'failure'
ORDER BY rank;

-- Top advisory defects
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM top_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
  AND defect_type = 'advisory'
ORDER BY rank;

-- Dangerous defects
SELECT defect_description, category_name, occurrence_count, occurrence_percentage, rank
FROM dangerous_defects
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY rank;

-- Mileage bands
SELECT mileage_band, total_tests, pass_rate, avg_mileage
FROM mileage_bands
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY band_order;

-- Age bands
SELECT age_band, total_tests, pass_rate, avg_mileage
FROM age_bands
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?
ORDER BY band_order;

-- Rankings
SELECT ranking_type, rank, total_in_category, pass_rate
FROM vehicle_rankings
WHERE make = ? AND model = ? AND model_year = ? AND fuel_type = ?;
```

### 5.6 Get Top/Bottom Vehicles by Pass Rate

```sql
-- Top 10 for a given year
SELECT make, model, fuel_type, pass_rate, total_tests
FROM vehicle_insights
WHERE model_year = 2020
ORDER BY pass_rate DESC
LIMIT 10;

-- Bottom 10 for a given year
SELECT make, model, fuel_type, pass_rate, total_tests
FROM vehicle_insights
WHERE model_year = 2020
ORDER BY pass_rate ASC
LIMIT 10;
```

### 5.7 Compare Vehicles

```sql
SELECT
    make, model, model_year, fuel_type,
    pass_rate, initial_failure_rate, avg_mileage, pass_rate_vs_national
FROM vehicle_insights
WHERE (make = 'FORD' AND model = 'FOCUS' AND model_year = 2018 AND fuel_type = 'PE')
   OR (make = 'VAUXHALL' AND model = 'ASTRA' AND model_year = 2018 AND fuel_type = 'PE')
   OR (make = 'VOLKSWAGEN' AND model = 'GOLF' AND model_year = 2018 AND fuel_type = 'PE');
```

### 5.8 Get Manufacturer Rankings

```sql
SELECT make, weighted_pass_rate, total_tests, total_models,
       best_model, best_model_pass_rate, worst_model, worst_model_pass_rate, rank
FROM manufacturer_rankings
ORDER BY rank;
```

---

## 6. API Design Recommendations

### Suggested REST Endpoints

```
# Vehicle Search & Discovery
GET /api/makes                              → List all makes
GET /api/makes/{make}/models                → List models for a make
GET /api/makes/{make}/models/{model}/years  → List years for make/model
GET /api/vehicles/search?make=&model=&year= → Search vehicles

# Vehicle Insights (main endpoint)
GET /api/vehicles/{make}/{model}/{year}/{fuel}
    → Returns: vehicle_insights + failure_categories + top_defects +
               dangerous_defects + mileage_bands + age_bands + rankings

# Specific Insight Tables
GET /api/vehicles/{make}/{model}/{year}/{fuel}/defects?type=failure|advisory
GET /api/vehicles/{make}/{model}/{year}/{fuel}/mileage
GET /api/vehicles/{make}/{model}/{year}/{fuel}/geographic
GET /api/vehicles/{make}/{model}/{year}/{fuel}/seasonal

# Rankings & Comparisons
GET /api/rankings/manufacturers
GET /api/rankings/vehicles?year=2020&sort=pass_rate&order=desc&limit=10
GET /api/compare?vehicles=FORD/FOCUS/2018/PE,VAUXHALL/ASTRA/2018/PE

# National Statistics
GET /api/national/averages
GET /api/national/seasonal
GET /api/national/yearly

# Dangerous Defects (safety focus)
GET /api/defects/dangerous/common  → Most common across all vehicles
GET /api/defects/dangerous/{make}  → For a specific manufacturer
```

### Response Structure Example

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
    "overall": { "rank": 2815, "total": 11406 },
    "within_make": { "rank": 134, "total": 677 },
    "within_year": { "rank": 281, "total": 641 }
  },
  "failure_categories": [
    { "name": "Tyres", "count": 2088, "percentage": 5.59, "rank": 1 },
    { "name": "Lamps", "count": 1559, "percentage": 4.18, "rank": 2 }
  ],
  "top_failures": [...],
  "top_advisories": [...],
  "dangerous_defects": [...],
  "mileage_bands": [...],
  "age_bands": [...]
}
```

---

## 7. TypeScript Interfaces

```typescript
// Core vehicle identifier
export interface VehicleKey {
  make: string;
  model: string;
  model_year: number;
  fuel_type: string;
}

// Fuel type mapping
export const FUEL_TYPES: Record<string, string> = {
  PE: 'Petrol',
  DI: 'Diesel',
  HY: 'Hybrid Electric',
  EL: 'Electric',
  ED: 'Plug-in Hybrid',
  GB: 'Gas Bi-fuel',
  OT: 'Other'
};

// Available vehicles index
export interface AvailableVehicle extends VehicleKey {
  id: number;
  total_tests: number;
}

// Core vehicle insights
export interface VehicleInsights extends VehicleKey {
  id: number;
  total_tests: number;
  total_passes: number;
  total_fails: number;
  total_prs: number;
  pass_rate: number;
  initial_failure_rate: number;
  avg_mileage: number | null;
  avg_age_years: number | null;
  national_pass_rate: number;
  pass_rate_vs_national: number;
}

// Failure categories
export interface FailureCategory extends VehicleKey {
  id: number;
  category_id: number;
  category_name: string;
  failure_count: number;
  failure_percentage: number;
  rank: number;
}

// Defects (failures and advisories)
export interface Defect extends VehicleKey {
  id: number;
  rfr_id: number;
  defect_description: string;
  category_name: string | null;
  defect_type: 'failure' | 'advisory';
  occurrence_count: number;
  occurrence_percentage: number;
  rank: number;
}

// Dangerous defects
export interface DangerousDefect extends VehicleKey {
  id: number;
  rfr_id: number;
  defect_description: string;
  category_name: string | null;
  occurrence_count: number;
  occurrence_percentage: number;
  rank: number;
}

// Mileage bands
export interface MileageBand extends VehicleKey {
  id: number;
  mileage_band: string;
  band_order: number;
  total_tests: number;
  pass_rate: number;
  avg_mileage: number | null;
}

// Age bands
export interface AgeBand extends VehicleKey {
  id: number;
  age_band: string;
  band_order: number;
  total_tests: number;
  pass_rate: number;
  avg_mileage: number | null;
}

// Vehicle rankings
export interface VehicleRanking extends VehicleKey {
  id: number;
  ranking_type: 'overall' | 'within_make' | 'within_year';
  rank: number;
  total_in_category: number;
  pass_rate: number;
}

// Manufacturer rankings
export interface ManufacturerRanking {
  id: number;
  make: string;
  total_tests: number;
  total_models: number;
  avg_pass_rate: number;
  weighted_pass_rate: number;
  best_model: string | null;
  best_model_pass_rate: number | null;
  worst_model: string | null;
  worst_model_pass_rate: number | null;
  rank: number;
}

// Geographic insights
export interface GeographicInsight extends VehicleKey {
  id: number;
  postcode_area: string;
  total_tests: number;
  pass_rate: number;
}

// Seasonal patterns
export interface SeasonalPattern extends VehicleKey {
  id: number;
  month: number;
  quarter: number;
  total_tests: number;
  pass_rate: number;
}

// National averages
export interface NationalAverage {
  id: number;
  metric_name: string;
  metric_value: number;
  model_year: number | null;
  fuel_type: string | null;
  description: string | null;
}

// Failure severity
export interface FailureSeverity extends VehicleKey {
  id: number;
  severity: 'major' | 'dangerous';
  failure_count: number;
  failure_percentage: number;
}

// First MOT insights
export interface FirstMotInsight extends VehicleKey {
  id: number;
  mot_type: 'first' | 'subsequent';
  total_tests: number;
  pass_rate: number;
  avg_mileage: number | null;
  avg_defects_per_fail: number | null;
}

// Advisory progression
export interface AdvisoryProgression extends VehicleKey {
  id: number;
  category_id: number;
  category_name: string;
  advisory_count: number;
  progressed_to_failure: number;
  progression_rate: number;
  avg_days_to_failure: number | null;
  avg_miles_to_failure: number | null;
}

// Retest success
export interface RetestSuccess extends VehicleKey {
  id: number;
  failed_tests: number;
  retested_within_30_days: number;
  passed_on_retest: number;
  retest_rate: number;
  retest_success_rate: number;
}

// Component mileage thresholds
export interface ComponentMileageThreshold extends VehicleKey {
  id: number;
  category_id: number;
  category_name: string;
  failure_rate_0_30k: number | null;
  failure_rate_30_60k: number | null;
  failure_rate_60_90k: number | null;
  failure_rate_90_120k: number | null;
  failure_rate_120_150k: number | null;
  failure_rate_150k_plus: number | null;
  spike_mileage_band: string | null;
  spike_increase_pct: number | null;
}

// Defect locations
export interface DefectLocation extends VehicleKey {
  id: number;
  location_id: number;
  lateral: string | null;
  longitudinal: string | null;
  vertical: string | null;
  failure_count: number;
  failure_percentage: number;
}

// Complete vehicle report (combined response)
export interface VehicleReport {
  vehicle: VehicleKey & { fuel_type_name: string };
  insights: VehicleInsights;
  rankings: {
    overall: VehicleRanking;
    within_make: VehicleRanking;
    within_year: VehicleRanking;
  };
  failure_categories: FailureCategory[];
  top_failures: Defect[];
  top_advisories: Defect[];
  dangerous_defects: DangerousDefect[];
  mileage_bands: MileageBand[];
  age_bands: AgeBand[];
}
```

---

## 8. Frontend Integration Guide

### 8.1 Vehicle Search Flow

```
1. User lands on page
   → Fetch GET /api/makes
   → Populate make dropdown

2. User selects make (e.g., "FORD")
   → Fetch GET /api/makes/FORD/models
   → Populate model dropdown

3. User selects model (e.g., "FOCUS")
   → Fetch GET /api/makes/FORD/models/FOCUS/years
   → Returns: [{ year: 2018, fuel_types: ["PE", "DI"] }, ...]
   → Populate year dropdown

4. User selects year (e.g., 2018)
   → If multiple fuel types, show fuel type selector
   → Otherwise auto-select the only fuel type

5. User confirms selection
   → Fetch GET /api/vehicles/FORD/FOCUS/2018/PE
   → Display full vehicle report
```

### 8.2 Key UI Components

**Pass Rate Display:**
```tsx
// Color code based on performance vs national average
const getPassRateColor = (passRate: number, national: number) => {
  const diff = passRate - national;
  if (diff >= 10) return 'green';   // Excellent
  if (diff >= 0) return 'lime';     // Good
  if (diff >= -5) return 'yellow';  // Average
  if (diff >= -10) return 'orange'; // Below Average
  return 'red';                      // Poor
};
```

**Ranking Display:**
```tsx
// Show percentile instead of raw rank
const getPercentile = (rank: number, total: number) => {
  return Math.round((1 - (rank / total)) * 100);
};
// "Top 25%" is more intuitive than "#2815 of 11406"
```

**Mileage Band Chart:**
- Line chart showing pass_rate vs mileage_band
- Helps users understand reliability at different mileages

**Failure Category Breakdown:**
- Pie/donut chart of top failure categories
- Bar chart for comparison

### 8.3 Caching Strategy

```typescript
// Suggested caching durations
const CACHE_DURATIONS = {
  makes: '24h',           // List of makes rarely changes
  models: '24h',          // Models for a make
  vehicleInsights: '1h',  // Core data
  rankings: '1h',         // Rankings
  national: '24h',        // National averages
};
```

### 8.4 Error Handling

```typescript
// Vehicle not found (likely below MIN_SAMPLE_SIZE threshold)
if (response.status === 404) {
  return {
    error: 'VEHICLE_NOT_FOUND',
    message: 'This vehicle combination does not have enough test data (minimum 100 tests required).'
  };
}
```

---

## 9. Important Notes & Caveats

### 9.1 Data Scope

- **Only Class 4 vehicles** (cars and light goods vehicles up to 3,000kg)
- **Only Normal Tests (NT)** - excludes retests, partial retests
- **Only 2023 data** - represents tests conducted in calendar year 2023
- **Minimum 100 tests** required per vehicle combination

### 9.2 Pass Rate Definition

```
Pass Rate = Tests with result 'P' / Total Tests with result in ('P', 'F', 'PRS')

Where:
- P = Passed
- F = Failed
- PRS = Pass with Rectification at Station (initially failed, fixed same day)
```

**Important:** PRS tests count as initial failures, NOT passes, because the vehicle initially failed inspection.

### 9.3 Failure Severity

The `failure_severity` table only contains 'major' and 'dangerous' - **no 'minor'**. This is correct because:
- In the UK MOT system, Minor defects don't cause test failures
- Minor defects are advisory/informational only
- The table tracks severity of items that actually caused failures

### 9.4 Defect Counting

Most defect tables use **COUNT(DISTINCT test_id)** - counting the number of tests affected, not the number of individual defect occurrences. This prevents inflated percentages from multiple similar defects on one test.

**Exception:** The `defect_locations` table uses `COUNT(*)` to show the distribution of all defect occurrences by physical location, rather than distinct tests.

### 9.5 Model Names

Model names come directly from DVSA data and may include:
- Trim levels (e.g., "FOCUS ZETEC", "FOCUS TITANIUM")
- Engine variants (e.g., "FOCUS 1.6 TDCI")
- Special editions

Consider grouping or fuzzy matching for better UX.

### 9.6 First Use Date

Vehicles with `first_use_date = 1971-01-01` are excluded (placeholder for unknown dates).

---

## 10. Verification Queries

Run these queries to verify database integrity:

```sql
-- 1. Pass rate sanity check (should return 0)
SELECT COUNT(*) as invalid FROM vehicle_insights
WHERE pass_rate < 0 OR pass_rate > 100
   OR initial_failure_rate < 0 OR initial_failure_rate > 100;

-- 2. Pass rate + failure rate = 100 (should return 0)
SELECT COUNT(*) as mismatches FROM vehicle_insights
WHERE ABS(pass_rate + initial_failure_rate - 100) > 0.1;

-- 3. No percentages over 100% (should all return 0)
SELECT 'top_defects' as tbl, COUNT(*) FROM top_defects WHERE occurrence_percentage > 100
UNION ALL
SELECT 'failure_categories', COUNT(*) FROM failure_categories WHERE failure_percentage > 100
UNION ALL
SELECT 'dangerous_defects', COUNT(*) FROM dangerous_defects WHERE occurrence_percentage > 100;

-- 4. Sample size verified (min should be >= 100)
SELECT MIN(total_tests) as min_tests FROM vehicle_insights;

-- 5. All tables populated
SELECT name,
       (SELECT COUNT(*) FROM sqlite_master m2 WHERE m2.tbl_name = m.name AND m2.type='table')
FROM sqlite_master m WHERE type='table' AND name != 'sqlite_sequence';

-- 6. Verify fuel types
SELECT DISTINCT fuel_type FROM vehicle_insights ORDER BY fuel_type;
-- Expected: DI, ED, EL, GB, HY, OT, PE
```

---

## Appendix: File Locations

```
/mot_data_2023/
├── mot_insights.db                    # The SQLite database (122.7 MB)
├── generate_insights_optimized.py     # Script that generated the database
├── inspect_insights_db.py             # Database inspection utility
├── MOT_INSIGHTS_REFERENCE.md          # This document
│
├── test_result.csv                    # Source: 42M test records
├── test_item.csv                      # Source: 89M defect records
├── item_detail.csv                    # Source: 21K defect definitions
├── item_group.csv                     # Source: 4K category definitions
├── mdr_*.csv                          # Source: Lookup tables
```

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-01 | Claude | Initial creation |

---

*End of Reference Document*
