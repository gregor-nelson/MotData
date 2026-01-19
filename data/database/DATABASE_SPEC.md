# MOT Insights Database Specification

**Database:** `mot_insights.db`
**Type:** SQLite 3
**Size:** ~943 MB
**Total Records:** ~7.2 million rows across 18 tables

---

## Overview

This database contains comprehensive MOT (Ministry of Transport) test insights for UK vehicles. It provides aggregated statistics, failure patterns, and reliability metrics derived from official MOT test data.

### Key Statistics
- **Total Tests in Dataset:** 32,801,943
- **National Pass Rate:** 71.45%
- **National Average Mileage:** 73,107 miles
- **Vehicle Makes:** ~181 valid manufacturers (100+ tests, excluding UNCLASSIFIED)
- **Vehicle Models:** 27,742 distinct models
- **Model Years:** 1894 - 2023
- **Geographic Coverage:** 118 UK postcode areas

---

## Data Filtering Criteria

The database is generated from DVSA bulk data with the following filters applied:

| Filter | Value | Reason |
|--------|-------|--------|
| `test_type` | `= 'NT'` | Normal Tests only (excludes Re-Tests) |
| `test_result` | `IN ('P', 'F', 'PRS')` | Valid outcomes only |
| `test_class_id` | `= '4'` | Class 4 vehicles only (cars & light goods ≤3,000kg) |
| `first_use_date` | `!= '1971-01-01'` | Excludes placeholder/unknown registration dates |
| `make` | `NOT LIKE '%UNCLASSIFIED%'` | Excludes unidentified manufacturers (including variants) |
| `make` | `total_tests >= 100` | Excludes low-volume/garbage data entries |

**Note:** Re-Tests (RT) are only included in the `retest_success` analysis where they're explicitly tracked.

---

## Source Data Requirements

The generator script requires these pipe-delimited CSV files:

| File | Description |
|------|-------------|
| `test_result.csv` | Main MOT test records |
| `test_item.csv` | Defect items recorded per test |
| `item_detail.csv` | Defect descriptions and categories |
| `item_group.csv` | MOT test categories hierarchy |
| `mdr_fuel_types.csv` | Fuel type reference data |
| `mdr_rfr_location.csv` | Physical location reference (nearside/offside etc.) |
| `mdr_test_outcome.csv` | Test outcome reference data |
| `mdr_test_type.csv` | Test type reference data |

---

## Fuel Type Codes

| Code | Description | Pass Rate |
|------|-------------|-----------|
| `PE` | Petrol | 71.85% |
| `DI` | Diesel | 69.77% |
| `HY` | Hybrid | 84.88% |
| `EL` | Electric | 84.57% |
| `ED` | Electric Diesel (Plug-in Hybrid Diesel) | 85.32% |
| `GA` | Gas (CNG/LPG converted) | 68.66% |
| `GB` | Gas Bi-fuel | 76.59% |
| `GD` | Gas Diesel | 75.47% |
| `LP` | LPG | 63.16% |
| `LN` | LNG | 73.68% |
| `CN` | CNG | 74.19% |
| `FC` | Fuel Cell | 67.86% |
| `ST` | Steam | 58.33% |
| `OT` | Other | 74.56% |

---

## RFR Type Codes (Reason for Rejection)

Defect records use these type codes to classify the severity/outcome:

| Code | Name | Description | Causes Fail? |
|------|------|-------------|--------------|
| `F` | Failure | Defect causing immediate MOT failure | Yes |
| `P` | PRS | Pass with Rectification at Station - fixed during test | Yes (initially) |
| `A` | Advisory | Warning notice - item may fail in future | No |
| `M` | Minor | Minor defect recorded | No |
| `D` | Dangerous | Dangerous mark - immediate prohibition | Yes |

**Usage in tables:**
- `top_defects.defect_type = 'failure'` → rfr_type_code IN ('F', 'P')
- `top_defects.defect_type = 'advisory'` → rfr_type_code = 'A'
- `top_defects.defect_type = 'minor'` → rfr_type_code = 'M'
- `dangerous_defects` → rfr_deficiency_category = 'Dangerous' OR dangerous_mark = 'D'

---

## Calculation Definitions

Key metrics are calculated as follows:

| Metric | Formula | Notes |
|--------|---------|-------|
| `pass_rate` | `(total_passes / total_tests) × 100` | Only counts clean passes |
| `initial_failure_rate` | `((total_fails + total_prs) / total_tests) × 100` | Includes PRS as initial failures |
| `failure_percentage` | `(category_failures / total_tests) × 100` | Per-vehicle percentage |
| `occurrence_percentage` | `(defect_count / total_tests) × 100` | How often defect appears |
| `progression_rate` | `(progressed_to_failure / advisory_count) × 100` | Advisory → Failure conversion |
| `retest_rate` | `(retested_within_30_days / failed_tests) × 100` | % that returned for retest |
| `retest_success_rate` | `(passed_on_retest / retested_within_30_days) × 100` | % that passed retest |

**Vehicle Age Classification:**
- **First MOT:** `vehicle_age <= 4 years` (typically 3-year-old vehicles having first test)
- **Subsequent MOT:** `vehicle_age > 4 years`

**Retest Window:** 30 days from original failure date

---

## Table Reference

### 1. `vehicle_insights` (Primary Vehicle Data)

**Row Count:** 117,036
**Description:** Core vehicle statistics including pass rates, test counts, and national comparisons.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key (auto-increment) |
| `make` | TEXT | NO | Vehicle manufacturer (e.g., "FORD", "BMW") |
| `model` | TEXT | NO | Vehicle model (e.g., "FIESTA", "3 SERIES") |
| `model_year` | INTEGER | NO | Year of manufacture (94-2023) |
| `fuel_type` | TEXT | YES | Fuel type code (PE, DI, HY, etc.) |
| `total_tests` | INTEGER | NO | Total MOT tests conducted |
| `total_passes` | INTEGER | NO | Tests that passed |
| `total_fails` | INTEGER | NO | Tests that failed |
| `total_prs` | INTEGER | NO | Pass with Rectification at Station |
| `pass_rate` | REAL | NO | Percentage of tests passed (0-100) |
| `initial_failure_rate` | REAL | NO | Percentage of initial failures |
| `avg_mileage` | REAL | YES | Average odometer reading at test |
| `avg_age_years` | REAL | YES | Average vehicle age at test |
| `national_pass_rate` | REAL | YES | National average pass rate (71.45) |
| `pass_rate_vs_national` | REAL | YES | Difference from national average |

**Unique Constraint:** `(make, model, model_year, fuel_type)`
**Index:** `idx_vi_lookup` on `(make, model, model_year, fuel_type)`

**Example Query:**
```sql
SELECT make, model, model_year, pass_rate, total_tests
FROM vehicle_insights
WHERE make = 'FORD' AND model = 'FIESTA'
ORDER BY model_year DESC;
```

---

### 2. `available_vehicles` (Vehicle Lookup Table)

**Row Count:** 117,036
**Description:** Simple lookup table of all available vehicle combinations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `total_tests` | INTEGER | NO | Total tests for this vehicle |

**Unique Constraint:** `(make, model, model_year, fuel_type)`
**Index:** `idx_av_lookup` on `(make, model, model_year)`

---

### 3. `failure_categories` (Failure Analysis by Category)

**Row Count:** 263,045
**Description:** Breakdown of failures by MOT test category for each vehicle.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `category_id` | INTEGER | NO | MOT category identifier |
| `category_name` | TEXT | NO | Human-readable category name |
| `failure_count` | INTEGER | NO | Number of failures in this category |
| `failure_percentage` | REAL | NO | Percentage of total failures |
| `rank` | INTEGER | NO | Rank within vehicle (1 = most common) |

**MOT Categories:**
- Body, chassis, structure
- Brakes
- Buses and coaches supplementary tests
- Identification of the vehicle
- Lamps, reflectors and electrical equipment
- Noise, emissions and leaks
- Road Wheels
- Seat belt installation check
- Seat belts and supplementary restraint systems
- Speedometer and speed limiter
- Steering
- Suspension
- Tyres
- Visibility

**Index:** `idx_fc_lookup` on `(make, model, model_year, fuel_type)`

---

### 4. `top_defects` (Common Defects)

**Row Count:** 3,216,669
**Description:** Most frequently occurring defects for each vehicle.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `rfr_id` | INTEGER | NO | Reason for Rejection ID |
| `defect_description` | TEXT | NO | Full defect description text |
| `category_name` | TEXT | YES | Parent MOT category |
| `defect_type` | TEXT | NO | Type: `failure`, `advisory`, `minor` |
| `occurrence_count` | INTEGER | NO | Times this defect occurred |
| `occurrence_percentage` | REAL | NO | Percentage of all tests for this vehicle |
| `rank` | INTEGER | NO | Rank within vehicle and defect_type |

**Defect Types Explained:**
| defect_type | Source RFR Codes | Description |
|-------------|------------------|-------------|
| `failure` | F, P | Defects that caused MOT failure (includes PRS) |
| `advisory` | A | Warning notices - did not cause failure |
| `minor` | M | Minor defects recorded |

**Note:** Each defect_type is ranked separately. Rank 1 failure is the most common failure, rank 1 advisory is the most common advisory, etc.

**Index:** `idx_td_lookup` on `(make, model, model_year, fuel_type)`

---

### 5. `dangerous_defects` (Safety-Critical Defects)

**Row Count:** 407,530
**Description:** Defects classified as dangerous (immediate prohibition).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `rfr_id` | INTEGER | NO | Reason for Rejection ID |
| `defect_description` | TEXT | NO | Full defect description |
| `category_name` | TEXT | YES | Parent MOT category |
| `occurrence_count` | INTEGER | NO | Times this defect occurred |
| `occurrence_percentage` | REAL | NO | Percentage of dangerous defects |
| `rank` | INTEGER | NO | Rank within vehicle |

**Index:** `idx_dd_lookup` on `(make, model, model_year, fuel_type)`

---

### 6. `defect_locations` (Physical Defect Locations)

**Row Count:** 476,478
**Description:** Where on the vehicle defects occur.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `location_id` | INTEGER | NO | Location identifier |
| `lateral` | TEXT | YES | `Nearside`, `Offside`, `Central` |
| `longitudinal` | TEXT | YES | `Front`, `Rear` |
| `vertical` | TEXT | YES | `Upper`, `Lower`, `Inner`, `Outer` |
| `failure_count` | INTEGER | NO | Failures at this location |
| `failure_percentage` | REAL | NO | Percentage of location failures |

**Location Values:**
- **Lateral:** Nearside (left), Offside (right), Central
- **Longitudinal:** Front, Rear
- **Vertical:** Upper, Lower, Inner, Outer

---

### 7. `failure_severity` (Severity Distribution)

**Row Count:** 86,534
**Description:** Distribution of failures by severity level.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `severity` | TEXT | NO | `minor`, `major`, or `dangerous` |
| `failure_count` | INTEGER | NO | Count at this severity |
| `failure_percentage` | REAL | NO | Percentage of total failures |

**Severity Levels:**
- `minor` - Minor defect, does not cause failure
- `major` - Defect requiring repair (most common)
- `dangerous` - Immediate prohibition, unsafe to drive

**Severity Classification Logic:**
```
Dangerous  → rfr_deficiency_category = 'Dangerous' OR dangerous_mark = 'D'
Major      → rfr_deficiency_category = 'Major' (or default for unknown)
Minor      → rfr_deficiency_category = 'Minor'
```

**Index:** `idx_fs_lookup` on `(make, model, model_year, fuel_type)`

---

### 8. `mileage_bands` (Pass Rate by Mileage)

**Row Count:** 243,606
**Description:** How pass rates vary across mileage ranges.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `mileage_band` | TEXT | NO | Mileage range label |
| `band_order` | INTEGER | NO | Sort order (0-5) |
| `total_tests` | INTEGER | NO | Tests in this band |
| `pass_rate` | REAL | NO | Pass rate for this band |
| `avg_mileage` | REAL | YES | Average mileage in band |

**Mileage Bands:**
| band_order | mileage_band | Lower (inclusive) | Upper (inclusive) |
|------------|--------------|-------------------|-------------------|
| 0 | 0-30k | 0 | 30,000 |
| 1 | 30k-60k | 30,001 | 60,000 |
| 2 | 60k-90k | 60,001 | 90,000 |
| 3 | 90k-120k | 90,001 | 120,000 |
| 4 | 120k-150k | 120,001 | 150,000 |
| 5 | 150k+ | 150,001 | No upper limit |

**Note:** Vehicles with `test_mileage <= 0` are excluded from mileage band analysis.

**Index:** `idx_mb_lookup` on `(make, model, model_year, fuel_type)`

---

### 9. `component_mileage_thresholds` (Component Wear Patterns)

**Row Count:** 261,482
**Description:** Component failure rates across mileage bands, identifying wear patterns.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `category_id` | INTEGER | NO | MOT category identifier |
| `category_name` | TEXT | NO | Category name |
| `failure_rate_0_30k` | REAL | YES | Failure % at 0-30k miles |
| `failure_rate_30_60k` | REAL | YES | Failure % at 30-60k miles |
| `failure_rate_60_90k` | REAL | YES | Failure % at 60-90k miles |
| `failure_rate_90_120k` | REAL | YES | Failure % at 90-120k miles |
| `failure_rate_120_150k` | REAL | YES | Failure % at 120-150k miles |
| `failure_rate_150k_plus` | REAL | YES | Failure % at 150k+ miles |
| `spike_mileage_band` | TEXT | YES | Band where failures spike |
| `spike_increase_pct` | REAL | YES | Percentage increase at spike |

**Index:** `idx_cmt_lookup` on `(make, model, model_year, fuel_type)`

**Example:** Identifies when brake issues typically emerge for a specific vehicle.

---

### 10. `advisory_progression` (Advisory to Failure Tracking)

**Row Count:** 27,799
**Description:** Tracks how advisories progress to failures over time.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `category_id` | INTEGER | NO | MOT category identifier |
| `category_name` | TEXT | NO | Category name |
| `advisory_count` | INTEGER | NO | Total advisories issued |
| `progressed_to_failure` | INTEGER | NO | Advisories that became failures |
| `progression_rate` | REAL | NO | Percentage that progressed |
| `avg_days_to_failure` | REAL | YES | Average days until failure |
| `avg_miles_to_failure` | REAL | YES | Average miles until failure |

**Index:** `idx_ap_lookup` on `(make, model, model_year, fuel_type)`

---

### 11. `first_mot_insights` (First vs Subsequent MOT)

**Row Count:** 118,445
**Description:** Compares first MOT (3-year-old vehicle) performance vs subsequent tests.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `mot_type` | TEXT | NO | `first` or `subsequent` |
| `total_tests` | INTEGER | NO | Test count |
| `pass_rate` | REAL | NO | Pass rate percentage |
| `avg_mileage` | REAL | YES | Average mileage |
| `avg_defects_per_fail` | REAL | YES | Average defects when failing |

**Index:** `idx_fmi_lookup` on `(make, model, model_year, fuel_type)`

---

### 12. `retest_success` (Retest Patterns)

**Row Count:** 51,655
**Description:** Success rates for vehicles that failed and were retested.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `failed_tests` | INTEGER | NO | Total failed tests |
| `retested_within_30_days` | INTEGER | NO | Retests within 30 days |
| `passed_on_retest` | INTEGER | NO | Passed after retest |
| `retest_rate` | REAL | NO | % that got retested |
| `retest_success_rate` | REAL | NO | % that passed retest |

**Index:** `idx_rs_lookup` on `(make, model, model_year, fuel_type)`

---

### 13. `seasonal_patterns` (Monthly Test Patterns)

**Row Count:** 439,955
**Description:** How pass rates vary by month/quarter for each vehicle.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `month` | INTEGER | NO | Month (1-12) |
| `quarter` | INTEGER | NO | Quarter (1-4) |
| `total_tests` | INTEGER | NO | Tests in this period |
| `pass_rate` | REAL | NO | Pass rate for period |

**Index:** `idx_sp_lookup` on `(make, model, model_year, fuel_type)`

---

### 14. `geographic_insights` (Regional Pass Rates)

**Row Count:** 1,706,673
**Description:** Pass rates by UK postcode area.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `postcode_area` | TEXT | NO | UK postcode prefix (e.g., "SL", "MK") |
| `total_tests` | INTEGER | NO | Tests in this area |
| `pass_rate` | REAL | NO | Area pass rate |

**Index:** `idx_gi_lookup` on `(make, model, model_year, fuel_type)`

**Coverage:** 118 UK postcode areas

---

### 15. `manufacturer_rankings` (Brand Rankings)

**Row Count:** ~181 (valid makes with 100+ tests)
**Description:** Overall manufacturer reliability rankings.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Manufacturer name |
| `total_tests` | INTEGER | NO | Total tests for manufacturer |
| `total_models` | INTEGER | NO | Number of distinct models |
| `avg_pass_rate` | REAL | NO | Simple average pass rate |
| `weighted_pass_rate` | REAL | NO | Test-volume weighted pass rate |
| `best_model` | TEXT | YES | Highest pass rate model |
| `best_model_pass_rate` | REAL | YES | Best model's pass rate |
| `worst_model` | TEXT | YES | Lowest pass rate model |
| `worst_model_pass_rate` | REAL | YES | Worst model's pass rate |
| `rank` | INTEGER | NO | Overall ranking position |

**Unique Constraint:** `(make)`
**Index:** `idx_mr_lookup` on `(make)`

---

### 16. `vehicle_rankings` (Vehicle Rankings)

**Row Count:** 351,108
**Description:** Vehicle rankings within different categories.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `make` | TEXT | NO | Vehicle manufacturer |
| `model` | TEXT | NO | Vehicle model |
| `model_year` | INTEGER | NO | Year of manufacture |
| `fuel_type` | TEXT | YES | Fuel type code |
| `ranking_type` | TEXT | NO | Ranking category |
| `rank` | INTEGER | NO | Position in ranking |
| `total_in_category` | INTEGER | NO | Total vehicles in category |
| `pass_rate` | REAL | NO | Vehicle's pass rate |

**Ranking Types:**
- `overall` - Ranked against all vehicles
- `within_make` - Ranked against same manufacturer
- `within_year` - Ranked against same model year

---

### 17. `national_averages` (Benchmark Data)

**Row Count:** 154
**Description:** National benchmark statistics for comparisons.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `metric_name` | TEXT | NO | Name of the metric |
| `metric_value` | REAL | NO | Metric value |
| `model_year` | INTEGER | YES | Year (if year-specific) |
| `fuel_type` | TEXT | YES | Fuel type (if type-specific) |
| `description` | TEXT | YES | Human-readable description |

**Key Metrics:**
| Metric Name | Value | Description |
|-------------|-------|-------------|
| `overall_pass_rate` | 71.45 | National Class 4 pass rate |
| `overall_initial_failure_rate` | 28.55 | National failure rate |
| `overall_avg_mileage` | 73,107 | Average mileage at test |
| `total_tests` | 32,801,943 | Total tests in dataset |
| `yearly_pass_rate` | varies | Pass rate by model year |
| `fuel_type_pass_rate` | varies | Pass rate by fuel type |

---

### 18. `national_seasonal` (Monthly National Patterns)

**Row Count:** 12
**Description:** National pass rates by month.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `month` | INTEGER | NO | Month (1-12) |
| `quarter` | INTEGER | NO | Quarter (1-4) |
| `total_tests` | INTEGER | NO | Total tests that month |
| `pass_rate` | REAL | NO | Monthly pass rate |

**Unique Constraint:** `(month)`

**Monthly Data:**
| Month | Tests | Pass Rate |
|-------|-------|-----------|
| January | 2,956,036 | 70.42% |
| February | 2,713,624 | 71.25% |
| March | 3,409,925 | 72.92% |
| April | 1,920,656 | 71.03% |
| May | 2,187,189 | 71.59% |
| June | 2,594,165 | 72.57% |
| July | 2,561,516 | 71.61% |
| August | 2,813,043 | 71.43% |
| September | 3,253,839 | 72.67% |
| October | 3,244,109 | 70.26% |
| November | 3,003,419 | 70.03% |
| December | 2,144,422 | 71.39% |

---

## Index Reference

| Index Name | Table | Columns |
|------------|-------|---------|
| `idx_vi_lookup` | vehicle_insights | make, model, model_year, fuel_type |
| `idx_av_lookup` | available_vehicles | make, model, model_year |
| `idx_fc_lookup` | failure_categories | make, model, model_year, fuel_type |
| `idx_td_lookup` | top_defects | make, model, model_year, fuel_type |
| `idx_mb_lookup` | mileage_bands | make, model, model_year, fuel_type |
| `idx_ap_lookup` | advisory_progression | make, model, model_year, fuel_type |
| `idx_gi_lookup` | geographic_insights | make, model, model_year, fuel_type |
| `idx_dd_lookup` | dangerous_defects | make, model, model_year, fuel_type |
| `idx_fmi_lookup` | first_mot_insights | make, model, model_year, fuel_type |
| `idx_mr_lookup` | manufacturer_rankings | make |
| `idx_sp_lookup` | seasonal_patterns | make, model, model_year, fuel_type |
| `idx_fs_lookup` | failure_severity | make, model, model_year, fuel_type |
| `idx_rs_lookup` | retest_success | make, model, model_year, fuel_type |
| `idx_cmt_lookup` | component_mileage_thresholds | make, model, model_year, fuel_type |

---

## Common Query Patterns

### Get Complete Vehicle Profile
```sql
-- Basic stats
SELECT * FROM vehicle_insights
WHERE make = 'FORD' AND model = 'FIESTA' AND model_year = 2015;

-- Top failures
SELECT * FROM failure_categories
WHERE make = 'FORD' AND model = 'FIESTA' AND model_year = 2015
ORDER BY rank;

-- Common defects
SELECT * FROM top_defects
WHERE make = 'FORD' AND model = 'FIESTA' AND model_year = 2015
ORDER BY rank LIMIT 10;
```

### Compare Models Within Manufacturer
```sql
SELECT model, model_year, pass_rate, total_tests
FROM vehicle_insights
WHERE make = 'BMW' AND fuel_type = 'PE'
ORDER BY pass_rate DESC;
```

### Find Best/Worst Vehicles by Year
```sql
SELECT make, model, pass_rate, total_tests
FROM vehicle_insights
WHERE model_year = 2018 AND total_tests > 1000
ORDER BY pass_rate DESC
LIMIT 20;
```

### Mileage Impact Analysis
```sql
SELECT mileage_band, pass_rate, total_tests
FROM mileage_bands
WHERE make = 'TOYOTA' AND model = 'COROLLA' AND model_year = 2015
ORDER BY band_order;
```

### Regional Comparison
```sql
SELECT postcode_area, pass_rate, total_tests
FROM geographic_insights
WHERE make = 'VOLKSWAGEN' AND model = 'GOLF' AND model_year = 2015
ORDER BY pass_rate DESC;
```

---

## Data Quality Notes

1. **Make/Model Variations:** Manufacturer names may have variations (e.g., "MERCEDES-BENZ" vs "MERCEDES"). Models may include trim levels.

2. **Low Volume Data:** Some records have very few tests (< 10), resulting in unreliable statistics. Filter by `total_tests > 100` for reliable insights.

3. **Year Range:** Model years span 1894-2023, but older vehicles (pre-1960) have limited data.

4. **Null Values:** `fuel_type` can be NULL for some records. Mileage fields may be NULL if data unavailable.

5. **Percentages:** All percentage fields are stored as 0-100 values, not decimals.

---

## Top Manufacturers by Test Volume

| Rank | Make | Model Count |
|------|------|-------------|
| 1 | FORD | 5,583 |
| 2 | TOYOTA | 5,528 |
| 3 | MERCEDES-BENZ | 5,518 |
| 4 | VOLKSWAGEN | 5,132 |
| 5 | FIAT | 4,807 |
| 6 | BMW | 3,765 |
| 7 | LAND ROVER | 3,141 |
| 8 | NISSAN | 3,113 |
| 9 | PEUGEOT | 2,461 |
| 10 | AUDI | 2,456 |
| 11 | VAUXHALL | 2,299 |
| 12 | RENAULT | 2,268 |
| 13 | MERCEDES | 2,157 |
| 14 | MAZDA | 2,110 |
| 15 | CITROEN | 2,003 |
| 16 | HONDA | 1,797 |
| 17 | MITSUBISHI | 1,761 |
| 18 | VOLVO | 1,623 |
| 19 | PORSCHE | 1,499 |
| 20 | MINI | 1,459 |

---

## Data Generation Pipeline

The database is generated in 19 sequential steps by `generate_insights_optimized.py`:

| Step | Function | Output Table(s) | Dependencies |
|------|----------|-----------------|--------------|
| 1 | Import CSV files | DuckDB temp tables | Source CSVs |
| 2 | Create base_tests | Filtered test records | Step 1 |
| 3 | Create SQLite schema | All tables (empty) | None |
| 4 | National averages | `national_averages` | Step 2 |
| 5 | Vehicle insights | `vehicle_insights`, `available_vehicles` | Steps 2, 4 |
| 6 | Failure categories | `failure_categories` | Step 2 |
| 7 | Top defects | `top_defects` | Step 2 |
| 8 | Mileage bands | `mileage_bands` | Step 2 |
| 9 | Geographic insights | `geographic_insights` | Step 2 |
| 10 | Defect locations | `defect_locations` | Step 2 |
| 11 | Advisory progression | `advisory_progression` | Step 2 |
| 12 | Vehicle rankings | `vehicle_rankings` | Step 5 |
| 13 | Dangerous defects | `dangerous_defects` | Step 2 |
| 14 | First MOT insights | `first_mot_insights` | Step 2 |
| 15 | Manufacturer rankings | `manufacturer_rankings` | Step 2 |
| 16 | Seasonal patterns | `seasonal_patterns`, `national_seasonal` | Step 2 |
| 17 | Failure severity | `failure_severity` | Step 2 |
| 18 | Retest success | `retest_success` | Step 2 |
| 19 | Component thresholds | `component_mileage_thresholds` | Step 2 |

**Performance Notes:**
- Uses DuckDB for bulk SQL operations (faster than per-vehicle loops)
- Disk-backed DuckDB to manage memory (~8-10GB RAM usage)
- Expected runtime: 10-30 minutes on typical hardware
- Temporary DuckDB file is deleted after completion

---

## Entity Relationship Summary

```
vehicle_insights (1) ──── (N) failure_categories
                  ├──── (N) top_defects
                  ├──── (N) dangerous_defects
                  ├──── (N) defect_locations
                  ├──── (N) failure_severity
                  ├──── (N) mileage_bands
                  ├──── (N) component_mileage_thresholds
                  ├──── (N) advisory_progression
                  ├──── (N) first_mot_insights
                  ├──── (N) retest_success
                  ├──── (N) seasonal_patterns
                  ├──── (N) geographic_insights
                  └──── (N) vehicle_rankings

manufacturer_rankings (1) ──── (N) vehicle_insights (via make)

national_averages ──── Reference data (no FK)
national_seasonal ──── Reference data (no FK)
```

**Join Key:** All vehicle-specific tables share the composite key `(make, model, model_year, fuel_type)` for joining.

---

*Generated: January 2026*
*Source: UK DVSA MOT Test Data*
