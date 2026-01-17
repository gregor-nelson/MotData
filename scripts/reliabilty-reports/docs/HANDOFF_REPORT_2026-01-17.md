# Reliability Reports Parser - Session Handoff Report

**Date:** 2026-01-17
**Status:** INCOMPLETE - REQUIRES VALIDATION BEFORE USE
**Priority:** HIGH - Contains runtime error that will crash the script

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Issue - Must Fix First](#critical-issue---must-fix-first)
3. [Changes Completed This Session](#changes-completed-this-session)
4. [Changes NOT Completed](#changes-not-completed)
5. [Files Modified](#files-modified)
6. [Reference Files](#reference-files)
7. [Database Validation Requirements](#database-validation-requirements)
8. [Validation SQL Queries](#validation-sql-queries)
9. [Spec Compliance Checklist](#spec-compliance-checklist)
10. [Recommendations for Next Session](#recommendations-for-next-session)

---

## Executive Summary

This session began refactoring the MOT insights parser (`scripts/reliabilty-reports/json_parser/parser.py`) to:

1. **Centralize configuration** - Move all magic numbers into a `DEFAULT_CONFIG` dictionary
2. **Remove presentation limits** - Functions should return ALL qualifying data, not arbitrary top N
3. **Keep statistical filters** - Minimum test thresholds remain for data validity
4. **Prepare for MOT-exempt year filtering** - Not yet implemented

**The refactoring is INCOMPLETE and the code WILL NOT RUN due to a reference to a deleted constant.**

---

## Critical Issue - Must Fix First

### Runtime Error: `MIN_TESTS_PROVEN` is Undefined

**Location:** `parser.py` line 1051

**Error:** The constant `MIN_TESTS_PROVEN` was removed when migrating to the config dict, but `get_reliability_summary()` still references it:

```python
# Line 1051 - WILL CRASH
""", (make, MIN_TESTS_PROVEN))
```

**Fix Required:**
```python
# Replace with:
""", (make, cfg["min_tests"]))

# And add config parameter to function signature:
def get_reliability_summary(conn, make: str, config: dict = None) -> dict:
    cfg = config or DEFAULT_CONFIG
```

---

## Changes Completed This Session

### 1. DEFAULT_CONFIG Dictionary Added (Lines 50-71)

```python
DEFAULT_CONFIG = {
    # Statistical minimum thresholds
    "min_tests": 100,
    "min_tests_trajectory": 200,

    # Age band methodology
    "proven_min_band": 4,      # 11+ years
    "maturing_min_band": 2,    # 7-10 years
    "early_max_band": 1,       # 3-6 years

    # Durability rating thresholds
    "rating_excellent_pct": 80,
    "rating_excellent_vs_nat": 5,
    "rating_good_pct": 60,
    "rating_good_vs_nat": 2,
    "rating_average_pct": 40,

    # Fallback value
    "fallback_national_avg": 71.51,
}
```

### 2. Functions Updated to Use Config

| Function | Line | Changes |
|----------|------|---------|
| `get_year_avg_safe()` | 162 | Added `config` parameter, uses `cfg["fallback_national_avg"]` |
| `get_best_models()` | 466 | Added `config` parameter, uses `cfg["min_tests"]`, **LIMIT REMOVED** |
| `get_worst_models()` | 500 | Added `config` parameter, uses `cfg["min_tests"]`, **LIMIT REMOVED** |
| `get_top_defects()` | 549 | **LIMIT REMOVED** from SQL |
| `get_dangerous_defects()` | 567 | **LIMIT REMOVED** from SQL |
| `get_best_models_age_adjusted()` | 685 | **LIMIT REMOVED** - returns all |
| `get_worst_models_age_adjusted()` | 713 | **LIMIT REMOVED** - returns all |
| `get_durability_champions()` | 752 | Added `config` parameter, uses `cfg["min_tests"]` and `cfg["proven_min_band"]`, **LIMIT REMOVED** |
| `get_models_to_avoid_proven()` | 816 | Added `config` parameter, uses `cfg["min_tests"]` and `cfg["proven_min_band"]`, **LIMIT REMOVED** |
| `get_early_performers()` | 880 | Added `config` parameter, uses `cfg["min_tests"]` and `cfg["early_max_band"]`, **LIMIT REMOVED** |

### 3. Constants Removed

- `MIN_TESTS_PROVEN` - Removed (was 100, now in config)
- `MIN_TESTS_EARLY` - Removed (was 100, now in config)
- `FALLBACK_NATIONAL_AVG` - Moved into config

---

## Changes NOT Completed

### 1. Functions Still Using Hardcoded Values

| Function | Line | Hardcoded Value | Should Use |
|----------|------|-----------------|------------|
| `get_reliability_summary()` | 1051 | `MIN_TESTS_PROVEN` | `cfg["min_tests"]` - **CAUSES CRASH** |
| `get_model_family_trajectory()` | 959 | `>= 200` in HAVING | `cfg["min_tests_trajectory"]` |
| `get_age_adjusted_scores()` | 648 | `< 100` check | `cfg["min_tests"]` |
| `get_models_aggregated()` | 340 | `>= 100` in HAVING | `cfg["min_tests"]` |
| `get_core_models_aggregated()` | 379 | `>= 100` in HAVING | `cfg["min_tests"]` |
| `get_model_family_year_breakdown()` | 419 | `>= 100` in HAVING | `cfg["min_tests"]` |

### 2. Slicing Still Present in `generate_make_insights()`

The main output function still slices results, defeating the purpose of removing limits from the getter functions:

| Line | Code | Purpose |
|------|------|---------|
| 1121 | `core_models[:10]` | Limits model breakdowns to 10 |
| 1171 | `durability_champions[:10]` | Limits key models set |
| 1177 | `models_to_avoid_proven[:5]` | Limits key models set |
| 1182 | `top_by_tests[:8]` | Limits key models set |

**Decision needed:** Should these be configurable or removed entirely?

### 3. Year Filtering NOT Implemented

User requested dynamic year filtering to exclude MOT-exempt vehicles (40+ years old from start of year).

**Proposed config addition (not yet added):**
```python
"min_model_year": None,  # Set dynamically: datetime.now().year - 40
"mot_exempt_years": 40,  # Vehicles 40+ years old are MOT exempt
```

### 4. CLI Config Override NOT Added

No `--min-tests` CLI argument was added to allow runtime configuration.

---

## Files Modified

| File | Status | Notes |
|------|--------|-------|
| `scripts/reliabilty-reports/json_parser/parser.py` | Modified | Main refactoring - INCOMPLETE |
| `scripts/reliabilty-reports/json_parser/PARSER_REFACTOR_REPORT.md` | Created | Session notes (this was created earlier) |

---

## Reference Files

These files define the expected behavior and data structures:

| File | Purpose |
|------|---------|
| `main/specs/SPEC.md` | Database schema specification |
| `scripts/reliabilty-reports/docs/REFERENCE.md` | Pipeline documentation |
| `data/database/mot_insights.db` | Source database for validation |

---

## Database Validation Requirements

The next session must verify that the parser generates accurate insights by cross-referencing against the raw database.

### Database Location
```
data/database/mot_insights.db
```

### Database Statistics (from SPEC.md)
- **Records:** 117,036 vehicles
- **Tests:** 32.8M MOT tests
- **Defect rows:** 3.2M

### Vehicle Lookup Key
All tables use: `(make, model, model_year, fuel_type)`

### Key Tables for Validation

| Table | Purpose | Used By Parser |
|-------|---------|----------------|
| `vehicle_insights` | Core pass/fail stats | Yes |
| `age_bands` | Pass rates by vehicle age | Yes |
| `national_averages` | Benchmark metrics | Yes |
| `manufacturer_rankings` | Make-level aggregates | Yes |
| `top_defects` | Defect occurrences | Yes |
| `dangerous_defects` | Safety defects | Yes |
| `mileage_bands` | Pass rates by mileage | Yes |
| `failure_categories` | Failures by component | Yes |

### Tables NOT Used (Verify Intentional)

| Table | Status | Notes |
|-------|--------|-------|
| `geographic_insights` | Not used | Regional analysis - future feature |
| `first_mot_insights` | Not used | First MOT vs subsequent |
| `component_mileage_thresholds` | Not used | Predictive maintenance |
| `seasonal_patterns` | Not used | Monthly patterns |
| `advisory_progression` | Not used | Advisory to failure tracking |
| `failure_severity` | Not used | Severity breakdown |
| `retest_success` | Not used | Retest statistics |
| `defect_locations` | Not used | Physical defect mapping |
| `vehicle_rankings` | Not used | Cross-vehicle comparison |
| `national_seasonal` | Not used | Monthly national benchmarks |

---

## Validation SQL Queries

Run these queries against `mot_insights.db` to verify parser output accuracy.

### 1. Verify Yearly National Averages

```sql
-- Check what the parser should return from get_yearly_national_averages()
SELECT model_year, metric_value as national_avg
FROM national_averages
WHERE metric_name = 'yearly_pass_rate' AND model_year IS NOT NULL
ORDER BY model_year DESC
LIMIT 20;
```

### 2. Verify Weighted Age Band Averages

```sql
-- Check weighted national averages by age band
-- This is what get_weighted_age_band_averages() should return
SELECT
    band_order,
    ROUND(SUM(pass_rate * total_tests) / SUM(total_tests), 2) as weighted_avg,
    SUM(total_tests) as total_tests
FROM age_bands
GROUP BY band_order
ORDER BY band_order;
```

### 3. Verify min_tests Filter

```sql
-- For a given make, count vehicles meeting min_tests threshold
-- Should match count from get_best_models()
SELECT COUNT(*) as qualifying_vehicles
FROM vehicle_insights
WHERE make = 'HONDA' AND total_tests >= 100;
```

### 4. Verify Year-Adjusted Scoring

```sql
-- Check a specific vehicle's year-adjusted score
-- Parser should calculate: pass_rate - national_avg_for_year
WITH nat AS (
    SELECT metric_value as national_avg
    FROM national_averages
    WHERE metric_name = 'yearly_pass_rate' AND model_year = 2015
)
SELECT
    model,
    pass_rate,
    (SELECT national_avg FROM nat) as national_avg_for_year,
    pass_rate - (SELECT national_avg FROM nat) as vs_national
FROM vehicle_insights
WHERE make = 'HONDA' AND model_year = 2015 AND total_tests >= 100
ORDER BY vs_national DESC
LIMIT 10;
```

### 5. Verify Durability Champions Logic

```sql
-- Get weighted national average for band_order 4 (11-12 years)
SELECT
    ROUND(SUM(pass_rate * total_tests) / SUM(total_tests), 2) as weighted_avg
FROM age_bands
WHERE band_order = 4;

-- Then verify durability champions for a make
-- Parser should return vehicles with pass_rate > weighted_avg
SELECT
    ab.model,
    ab.model_year,
    ab.pass_rate,
    ab.total_tests,
    ab.age_band,
    ab.pass_rate - (
        SELECT ROUND(SUM(pass_rate * total_tests) / SUM(total_tests), 2)
        FROM age_bands WHERE band_order = ab.band_order
    ) as vs_national_at_age
FROM age_bands ab
WHERE ab.make = 'HONDA'
  AND ab.band_order >= 4
  AND ab.total_tests >= 100
  AND ab.pass_rate > (
      SELECT SUM(pass_rate * total_tests) / SUM(total_tests)
      FROM age_bands WHERE band_order = ab.band_order
  )
ORDER BY vs_national_at_age DESC;
```

### 6. Verify Best Models (Year-Adjusted)

```sql
-- Top 10 best models for HONDA by year-adjusted score
WITH yearly_avg AS (
    SELECT model_year, metric_value as avg
    FROM national_averages
    WHERE metric_name = 'yearly_pass_rate'
)
SELECT
    v.model,
    v.model_year,
    v.fuel_type,
    v.total_tests,
    v.pass_rate,
    COALESCE(y.avg, 71.51) as national_avg_for_year,
    ROUND(v.pass_rate - COALESCE(y.avg, 71.51), 2) as vs_national
FROM vehicle_insights v
LEFT JOIN yearly_avg y ON v.model_year = y.model_year
WHERE v.make = 'HONDA' AND v.total_tests >= 100
ORDER BY vs_national DESC
LIMIT 10;
```

### 7. Verify Reliability Summary Calculation

```sql
-- Calculate durability rating for a make
-- Count proven vehicles (11+ years) above/below average
WITH age_avgs AS (
    SELECT band_order,
           SUM(pass_rate * total_tests) / SUM(total_tests) as weighted_avg
    FROM age_bands
    GROUP BY band_order
)
SELECT
    COUNT(*) as total_proven,
    SUM(CASE WHEN ab.pass_rate > aa.weighted_avg THEN 1 ELSE 0 END) as above_avg,
    SUM(CASE WHEN ab.pass_rate <= aa.weighted_avg THEN 1 ELSE 0 END) as below_avg,
    ROUND(100.0 * SUM(CASE WHEN ab.pass_rate > aa.weighted_avg THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_above
FROM age_bands ab
JOIN age_avgs aa ON ab.band_order = aa.band_order
WHERE ab.make = 'HONDA'
  AND ab.band_order >= 4
  AND ab.total_tests >= 100;
```

---

## Spec Compliance Checklist

Cross-reference parser behavior against `main/specs/SPEC.md`:

### Vehicle Key Columns
- [x] `make` - Uppercase (e.g., "HONDA")
- [x] `model` - Uppercase (e.g., "CIVIC")
- [x] `model_year` - Integer
- [x] `fuel_type` - PE/DI/EL/HY/NULL

### Defect Types
- [x] `failure` - Used in `get_top_defects()`
- [x] `advisory` - Used in `get_top_defects()`
- [ ] `minor` - Not explicitly used (post-May 2018)

### National Averages
- [x] Yearly pass rates from `national_averages` table
- [x] Fallback value when year missing (71.51%)
- [x] Weighted age band averages calculated from `age_bands`

### Pass Rate Calculations
- [x] Year-adjusted: `pass_rate - national_avg_for_year`
- [x] Age-adjusted: `pass_rate - weighted_avg_for_band`

---

## Recommendations for Next Session

### Priority 1: Fix Runtime Error
1. Add `config` parameter to `get_reliability_summary()`
2. Replace `MIN_TESTS_PROVEN` with `cfg["min_tests"]` on line 1051

### Priority 2: Complete Config Migration
Update these functions to accept and use `config` parameter:
- `get_model_family_trajectory()`
- `get_age_adjusted_scores()`
- `get_models_aggregated()`
- `get_core_models_aggregated()`
- `get_model_family_year_breakdown()`

### Priority 3: Database Validation
1. Run all validation queries above
2. Compare parser output against manual SQL results
3. Document any discrepancies

### Priority 4: Decide on Slicing in generate_make_insights()
Options:
- A) Remove all slicing (return full datasets)
- B) Make slice sizes configurable via DEFAULT_CONFIG
- C) Keep slicing for memory/performance reasons

### Priority 5: Add CLI Config Override
```python
parser.add_argument("--min-tests", type=int, default=100, help="Minimum tests for inclusion")
```

### Priority 6: Add Year Filtering (MOT Exempt)
Implement rolling 40-year filter to exclude MOT-exempt vehicles.

---

## Test Commands

After fixing the runtime error, test with:

```bash
# Generate insights for Honda (good test case - lots of data)
cd scripts/reliabilty-reports
python json_parser/parser.py HONDA --output ./test_honda.json --pretty

# List available makes
python json_parser/parser.py --list --top 20

# Test multiple makes
python json_parser/parser.py TOYOTA --output ./test_toyota.json
python json_parser/parser.py "LAND ROVER" --output ./test_landrover.json
```

---

## Appendix: Full DEFAULT_CONFIG Reference

```python
DEFAULT_CONFIG = {
    # Statistical minimum thresholds
    # Below these values, data is statistically unreliable
    "min_tests": 100,                  # Minimum tests for most analyses
    "min_tests_trajectory": 200,       # Higher for trajectory analysis

    # Age band methodology (defines maturity tiers)
    "proven_min_band": 4,              # Band order >= 4 = 11+ years (proven)
    "maturing_min_band": 2,            # Band order 2-3 = 7-10 years
    "early_max_band": 1,               # Band order <= 1 = 3-6 years (early)

    # Durability rating calculation thresholds
    "rating_excellent_pct": 80,        # >= 80% above avg AND vs_national >= 5
    "rating_excellent_vs_nat": 5,
    "rating_good_pct": 60,             # >= 60% above avg AND vs_national >= 2
    "rating_good_vs_nat": 2,
    "rating_average_pct": 40,          # >= 40% above avg

    # Fallback when year data missing
    "fallback_national_avg": 71.51,
}
```

---

*Report generated for handoff to validation/completion session*
*Next session should start by fixing the MIN_TESTS_PROVEN error on line 1051*