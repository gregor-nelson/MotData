# MOT Insights Database Reference

**Database:** `data/source/data/mot_insights.db`
**Records:** 117,036 vehicles | 32.8M tests | 3.2M defect rows

---

## Quick Reference

### Vehicle Lookup Key
All tables use: `(make, model, model_year, fuel_type)`
- `make`: Uppercase (e.g., "FORD", "BMW")
- `model`: Uppercase (e.g., "FIESTA", "3 SERIES")
- `model_year`: Integer (e.g., 2015)
- `fuel_type`: "PE" (petrol), "DI" (diesel), "EL" (electric), "HY" (hybrid), or NULL

### Defect Types
| Type | Meaning | Rows |
|------|---------|------|
| `failure` | Caused MOT failure | 1,767,217 |
| `advisory` | Warning, not failure | 1,139,162 |
| `minor` | Minor defect (post-May 2018) | 310,290 |

---

## Tables

### vehicle_insights
Core pass/fail statistics per vehicle.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| total_tests | INT | Total MOT tests |
| total_passes, total_fails, total_prs | INT | Outcome counts |
| pass_rate | REAL | Pass percentage (0-100) |
| initial_failure_rate | REAL | Failure percentage (0-100) |
| avg_mileage | REAL | Average test mileage |
| avg_age_years | REAL | Average vehicle age at test |
| national_pass_rate | REAL | National benchmark |
| pass_rate_vs_national | REAL | Difference from national |

### top_defects
All defects with occurrence counts and rankings.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| rfr_id | INT | Defect reference ID |
| defect_description | TEXT | Full defect text |
| category_name | TEXT | Component category |
| defect_type | TEXT | 'failure', 'advisory', or 'minor' |
| occurrence_count | INT | Times this defect occurred |
| occurrence_percentage | REAL | Percentage of failed tests |
| rank | INT | Rank within vehicle+defect_type |

### failure_categories
Failures grouped by component category.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| category_id | INT | Category reference |
| category_name | TEXT | e.g., "Suspension", "Brakes" |
| failure_count | INT | Failures in this category |
| failure_percentage | REAL | Percentage of total failures |
| rank | INT | Rank by failure count |

### mileage_bands
Pass rates segmented by mileage.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| mileage_band | TEXT | '0-30k', '30k-60k', '60k-90k', '90k-120k', '120k-150k', '150k+' |
| band_order | INT | Sort order (0-5) |
| total_tests | INT | Tests in this band |
| pass_rate | REAL | Pass percentage |
| avg_mileage | REAL | Average mileage in band |

### geographic_insights
Pass rates by UK postcode area.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| postcode_area | TEXT | e.g., "B", "M", "SW" |
| total_tests | INT | Tests in this area |
| pass_rate | REAL | Pass percentage |

### dangerous_defects
Serious safety defects only.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| rfr_id | INT | Defect reference ID |
| defect_description | TEXT | Full defect text |
| category_name | TEXT | Component category |
| occurrence_count | INT | Times occurred |
| occurrence_percentage | REAL | Percentage of tests |
| rank | INT | Rank by occurrence |

### manufacturer_rankings
Aggregate statistics by manufacturer.

| Column | Type | Description |
|--------|------|-------------|
| make | TEXT | Manufacturer name |
| total_tests | INT | Total tests across all models |
| total_models | INT | Number of distinct models |
| avg_pass_rate | REAL | Simple average |
| weighted_pass_rate | REAL | Weighted by test volume |
| best_model, best_model_pass_rate | TEXT/REAL | Top performing model |
| worst_model, worst_model_pass_rate | TEXT/REAL | Lowest performing model |
| rank | INT | Overall ranking |

### first_mot_insights
First MOT (3 years) vs subsequent MOTs.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| mot_type | TEXT | 'first' or 'subsequent' |
| total_tests | INT | Test count |
| pass_rate | REAL | Pass percentage |
| avg_mileage | REAL | Average mileage |
| avg_defects_per_fail | REAL | Defects per failed test |

### component_mileage_thresholds
When components start failing by mileage.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| category_id, category_name | INT/TEXT | Component category |
| failure_rate_0_30k through failure_rate_150k_plus | REAL | Failure rate per band |
| spike_mileage_band | TEXT | Band where failures increase |
| spike_increase_pct | REAL | Percentage increase at spike |

### seasonal_patterns
Monthly pass rate patterns per vehicle.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| month | INT | 1-12 |
| quarter | INT | 1-4 |
| total_tests | INT | Tests this month |
| pass_rate | REAL | Pass percentage |

### advisory_progression
How advisories become failures over time.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| category_id, category_name | INT/TEXT | Component category |
| advisory_count | INT | Total advisories |
| progressed_to_failure | INT | Became failures |
| progression_rate | REAL | Percentage progressed |
| avg_days_to_failure | REAL | Average days until failure |
| avg_miles_to_failure | REAL | Average miles until failure |

### failure_severity
Breakdown by severity level.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| severity | TEXT | 'minor', 'major', 'dangerous' |
| failure_count | INT | Count at this severity |
| failure_percentage | REAL | Percentage of failures |

### retest_success
Retest outcomes within 30 days.

| Column | Type | Description |
|--------|------|-------------|
| make, model, model_year, fuel_type | TEXT/INT | Vehicle identifier |
| failed_tests | INT | Initial failures |
| retested_within_30_days | INT | Retests attempted |
| passed_on_retest | INT | Passed on retest |
| retest_rate | REAL | Percentage retested |
| retest_success_rate | REAL | Percentage passed retest |

### Supporting Tables

| Table | Purpose |
|-------|---------|
| `available_vehicles` | All vehicle combinations (for dropdowns/validation) |
| `vehicle_rankings` | Comparative rankings by category |
| `defect_locations` | Physical location breakdown (lateral/longitudinal/vertical) |
| `national_averages` | Benchmark metrics (overall_pass_rate, total_tests, etc.) |
| `national_seasonal` | Monthly national pass rates |

---

## Example Queries

```sql
-- Get vehicle overview
SELECT * FROM vehicle_insights
WHERE make = 'FORD' AND model = 'FIESTA' AND model_year = 2015;

-- Top 10 failure defects for a vehicle
SELECT defect_description, occurrence_count, occurrence_percentage
FROM top_defects
WHERE make = 'FORD' AND model = 'FIESTA' AND model_year = 2015
  AND defect_type = 'failure'
ORDER BY rank LIMIT 10;

-- Compare fuel types
SELECT fuel_type, pass_rate, total_tests
FROM vehicle_insights
WHERE make = 'VOLKSWAGEN' AND model = 'GOLF' AND model_year = 2015;

-- Best/worst manufacturers (min 10k tests)
SELECT make, weighted_pass_rate, total_tests, rank
FROM manufacturer_rankings
WHERE total_tests >= 10000
ORDER BY rank LIMIT 10;

-- Mileage degradation pattern
SELECT mileage_band, pass_rate
FROM mileage_bands
WHERE make = 'BMW' AND model = '3 SERIES' AND model_year = 2012
ORDER BY band_order;

-- Components that fail at high mileage
SELECT category_name, failure_rate_0_30k, failure_rate_150k_plus,
       spike_mileage_band, spike_increase_pct
FROM component_mileage_thresholds
WHERE make = 'FORD' AND model = 'FOCUS' AND model_year = 2010
ORDER BY spike_increase_pct DESC NULLS LAST;
```

---

## Notes

- All percentage columns are 0-100 scale
- NULL fuel_type means aggregated across all fuel types
- Use `total_tests >= N` for statistical significance filtering
- All tables indexed on `(make, model, model_year, fuel_type)`
