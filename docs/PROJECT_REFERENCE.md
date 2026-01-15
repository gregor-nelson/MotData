# MOT Failure Pattern Analysis - Project Reference

> **Project**: motorwise.io MOT Insights Feature
> **Status**: Phase 1 Complete (Data Processing Pipeline)
> **Last Updated**: January 2025

---

## Executive Summary

This project extracts actionable vehicle reliability insights from the official DVSA MOT bulk dataset (2023) to power motorwise.io's vehicle reports and SEO content strategy.

### Business Goals

1. **SEO Content Pages** - Generate "Ford Focus 2017 common faults" style articles for top ~100 make/models
2. **Traffic Generation** - Create aggregate content like "Top 10 most unreliable cars according to UK gov data"
3. **Premium Report Enhancement** - Add predictive insights to £6.99 vehicle reports (future phase)
4. **Revenue Growth** - Drive traffic to vehicle check reports via organic search

---

## Source Dataset

### Files (5.5GB total)

| File | Size | Records | Purpose |
|------|------|---------|---------|
| `test_result.csv` | 3.4 GB | ~42M | MOT test outcomes with vehicle details |
| `test_item.csv` | 1.9 GB | ~89M | Individual defects/advisories per test |
| `item_detail.csv` | 3.5 MB | ~3,700 | Defect code descriptions |
| `item_group.csv` | 143 KB | ~2,500 | Hierarchical component groupings |
| `mdr_*.csv` | Small | Various | Lookup tables (fuel types, locations, outcomes) |

### Data Format
- **Delimiter**: Pipe character `|`
- **Encoding**: UTF-8
- **Date Format**: `YYYY-MM-DD`

### Key Relationships
```
test_result.test_id → test_item.test_id (one test has many defects)
test_item.rfr_id → item_detail.rfr_id (defect code to description)
item_detail.test_item_set_section_id → item_group.test_item_id (defect to category)
vehicle_id tracks same vehicle across tests (enables progression analysis)
```

### Data Filters Applied
- **Vehicle Class**: 4 only (cars/light vehicles)
- **Test Type**: NT (Normal Test) only
- **Test Results**: P, F, PRS (completed tests only)
- **Year Range**: first_use_date >= 2000
- **Excluded**: UNCLASSIFIED makes, 1971-01-01 dates (unknown)
- **Minimum Sample**: 100 tests per make/model/year/fuel combination

---

## Implementation Complete

### Technology Stack
- **Processing**: DuckDB (columnar analytics database)
- **Output**: SQLite database (`mot_insights.db`)
- **Language**: Python 3.8+

### Script Created
`generate_insights.py` - Processes raw CSVs and outputs aggregated SQLite database

**Original version**: `generate_insights.py.bak` (per-vehicle loop approach - slow)
**Optimized version needed**: Bulk SQL operations for performance

### Processing Approach
1. Import CSVs into DuckDB
2. Create filtered base table (Class 4, Normal Tests only)
3. Generate all insights via bulk SQL GROUP BY operations
4. Export to SQLite for deployment

---

## Output Database Schema

### `mot_insights.db` Tables

#### 1. `vehicle_insights` (Core Stats)
| Column | Description |
|--------|-------------|
| make, model, model_year, fuel_type | Vehicle identifier |
| total_tests | Sample size |
| pass_rate | % of tests passed |
| initial_failure_rate | % failed on first attempt (F + PRS) |
| avg_mileage | Average odometer at test |
| avg_age_years | Average vehicle age at test |
| national_pass_rate | Benchmark for comparison |
| pass_rate_vs_national | Difference from national average |

#### 2. `failure_categories` (Top 10 per vehicle)
| Column | Description |
|--------|-------------|
| category_name | e.g., "Brakes", "Suspension", "Lamps" |
| failure_count | Number of tests with this category failure |
| failure_percentage | % of total tests |
| rank | 1-10 ranking |

#### 3. `top_defects` (Top 10 failures + Top 10 advisories per vehicle)
| Column | Description |
|--------|-------------|
| defect_description | Human-readable defect text |
| category_name | Parent category |
| defect_type | 'failure' or 'advisory' |
| occurrence_count | Raw count |
| occurrence_percentage | % of total tests |
| rank | 1-10 ranking |

#### 4. `mileage_bands` (Pass rates by mileage)
| Column | Description |
|--------|-------------|
| mileage_band | '0-30k', '30k-60k', '60k-90k', '90k-120k', '120k-150k', '150k+' |
| band_order | 0-5 for sorting |
| total_tests | Sample size in band |
| pass_rate | % passed in this mileage range |

#### 5. `advisory_progression` (Advisory → Failure tracking)
| Column | Description |
|--------|-------------|
| category_name | Component category |
| advisory_count | Vehicles with advisory |
| progressed_to_failure | Vehicles that later failed same component |
| progression_rate | % that progressed |
| avg_days_to_failure | Average days between advisory and failure |
| avg_miles_to_failure | Average miles between advisory and failure |

#### 6. `geographic_insights` (Regional breakdown)
| Column | Description |
|--------|-------------|
| postcode_area | UK postcode prefix (e.g., 'NW', 'B', 'SE') |
| total_tests | Sample size in region |
| pass_rate | Regional pass rate |

#### 7. `defect_locations` (Where on vehicle)
| Column | Description |
|--------|-------------|
| lateral | 'Nearside', 'Offside', 'Centre' |
| longitudinal | 'Front', 'Rear' |
| vertical | 'Upper', 'Lower' |
| failure_count | Count at this location |
| failure_percentage | % of location-tagged failures |

#### 8. `vehicle_rankings` (Comparative positions)
| Column | Description |
|--------|-------------|
| ranking_type | 'overall', 'within_make', 'within_year' |
| rank | Position in ranking |
| total_in_category | Total vehicles in comparison set |

#### 9. `national_averages` (Benchmarks)
| Column | Description |
|--------|-------------|
| metric_name | 'overall_pass_rate', 'yearly_pass_rate', 'fuel_type_pass_rate' |
| metric_value | The benchmark value |
| model_year | Year (for yearly benchmarks) |
| fuel_type | Fuel type (for fuel benchmarks) |

#### 10. `available_vehicles` (Index)
| Column | Description |
|--------|-------------|
| make, model, model_year, fuel_type | Available combinations |
| total_tests | Sample size |

---

## Configuration Decisions Made

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Min sample size | 100 tests | Statistical significance |
| Model handling | Exact match | "FOCUS ST" ≠ "FOCUS" (different cars) |
| Year source | first_use_date | Standard model year proxy |
| Mileage bands | 30k increments | Industry standard buckets |
| Fuel type split | Yes | Diesel vs petrol have different failure patterns |
| Geographic split | Yes | Regional variations interesting |
| Advisory progression | Yes | High-value predictive insight |

---

## Architecture

### Current (Local Processing)
```
┌─────────────────────────┐
│     LOCAL MACHINE       │
├─────────────────────────┤
│ CSV Files (5.5GB)       │
│     ↓                   │
│ DuckDB Processing       │
│     ↓                   │
│ mot_insights.db (~XMB)  │
└─────────────────────────┘
```

### Target (Production)
```
┌─────────────────────────┐           ┌─────────────────────────┐
│     LOCAL MACHINE       │           │    VPS (Production)     │
├─────────────────────────┤           ├─────────────────────────┤
│ mot_insights.db         │──deploy──▶│ mot_insights.db         │
│                         │           │     ↓                   │
│                         │           │ Python API (Flask/Fast) │
│                         │           │     ↓                   │
│                         │           │ React Frontend          │
└─────────────────────────┘           └─────────────────────────┘
```

---

## Next Steps

### Immediate (Phase 2)

1. **Create Optimized Script**
   - New file: `generate_insights_optimized.py`
   - Use bulk SQL operations instead of per-vehicle loops
   - Expected runtime: 10-30 minutes (vs hours)

2. **Run Processing**
   - Execute script to generate `mot_insights.db`
   - Validate output row counts and sample queries

3. **Build API Endpoint**
   - Python API on VPS: `GET /api/insights/{make}/{model}/{year}`
   - Query SQLite, return JSON
   - Handle fuel_type as optional parameter

### Short-term (Phase 3)

4. **Create SEO Pages**
   - Static HTML generation for top 100 make/models
   - Template: "Ford Focus 2017 MOT Common Faults"
   - Content: Pass rate, top failures, advisories, mileage analysis

5. **Create Traffic Content**
   - "Top 10 Most Reliable Used Cars (Official UK Gov Data)"
   - "Top 10 Least Reliable Cars"
   - "Most Common MOT Failures by Brand"
   - Query `vehicle_rankings` table for data

### Medium-term (Phase 4)

6. **Premium Report Integration**
   - Add insights to £6.99 vehicle reports
   - API takes registration → lookup make/model/year → return insights
   - Display: "Based on 8,432 similar vehicles, 62% developed brake issues by 80k miles"

7. **Frontend Integration**
   - React component to display insights
   - Fetch from API based on vehicle data prop

---

## Sample Queries

### Get insights for a specific vehicle
```sql
SELECT * FROM vehicle_insights
WHERE make = 'FORD' AND model = 'FOCUS' AND model_year = 2017 AND fuel_type = 'PE';
```

### Get top failure categories
```sql
SELECT category_name, failure_percentage, rank
FROM failure_categories
WHERE make = 'FORD' AND model = 'FOCUS' AND model_year = 2017 AND fuel_type = 'PE'
ORDER BY rank;
```

### Get most reliable cars overall
```sql
SELECT make, model, model_year, fuel_type, pass_rate, total_tests
FROM vehicle_insights
WHERE total_tests >= 500
ORDER BY pass_rate DESC
LIMIT 10;
```

### Get least reliable cars
```sql
SELECT make, model, model_year, fuel_type, pass_rate, total_tests
FROM vehicle_insights
WHERE total_tests >= 500
ORDER BY pass_rate ASC
LIMIT 10;
```

### Get advisory progression data
```sql
SELECT category_name, progression_rate, avg_miles_to_failure
FROM advisory_progression
WHERE make = 'FORD' AND model = 'FOCUS' AND model_year = 2017
ORDER BY progression_rate DESC;
```

---

## Files in Project Directory

| File | Purpose |
|------|---------|
| `test_result.csv` | Raw MOT test data |
| `test_item.csv` | Raw defect records |
| `item_detail.csv` | Defect descriptions |
| `item_group.csv` | Category hierarchy |
| `mdr_*.csv` | Lookup tables |
| `MOT_DATA_REFERENCE.md` | Technical data documentation |
| `PROJECT_REFERENCE.md` | This file - project overview |
| `generate_insights.py.bak` | Original script (slow, per-vehicle loops) |
| `generate_insights_optimized.py` | **TO CREATE** - Optimized bulk SQL version |
| `mot_insights.db` | **TO GENERATE** - Output SQLite database |

---

## Key Technical Notes

1. **DuckDB** is used for processing because it handles analytical queries on large CSVs efficiently (columnar storage, parallel execution)

2. **SQLite** is used for output because it's simple to deploy (single file), queries are fast for lookups, and Python has built-in support

3. **Fuel type splitting** means each make/model/year may have multiple entries (e.g., Ford Focus 2017 Petrol AND Ford Focus 2017 Diesel)

4. **Advisory progression** tracks the same physical vehicle (`vehicle_id`) across multiple MOT tests to see if advisories become failures

5. **Performance tip**: The optimized script should use bulk `GROUP BY` operations, not per-vehicle loops. One query computing all vehicles is 100x faster than thousands of individual queries.

---

## Reference Documentation

- `MOT_DATA_REFERENCE.md` - Detailed technical schema documentation
- `mot-testing-data-user-guide-v5.1.odt` - Official DVSA user guide
