# MOT Insights Database Filtering Logic

**Purpose:** Documents how raw MOT test data is filtered before analysis.

---

## Overview

The filtering happens in two stages within `generate_insights_optimized.py`:

1. **Stage 1:** Identify valid manufacturers (makes with sufficient data)
2. **Stage 2:** Create the filtered test dataset using only those manufacturers

This two-stage approach ensures that all 18 insight tables contain only statistically meaningful data.

---

## Stage 1: Valid Makes Identification

**Function:** `create_base_tests_table()` (lines 114-126)

```sql
CREATE TEMP TABLE valid_makes AS
SELECT make
FROM test_result
WHERE test_type = 'NT'
  AND test_result IN ('P', 'F', 'PRS')
  AND CAST(test_class_id AS VARCHAR) = '4'
  AND first_use_date != '1971-01-01'
  AND make NOT LIKE '%UNCLASSIFIED%'
GROUP BY make
HAVING COUNT(*) >= 100
```

### Filters Applied

| Filter | Condition | Purpose |
|--------|-----------|---------|
| Test Type | `= 'NT'` | Normal Tests only (excludes Re-Tests) |
| Test Result | `IN ('P', 'F', 'PRS')` | Valid outcomes only |
| Vehicle Class | `= '4'` | Class 4 vehicles (cars & light goods) |
| Registration Date | `!= '1971-01-01'` | Excludes placeholder dates |
| Manufacturer Name | `NOT LIKE '%UNCLASSIFIED%'` | Excludes unidentified/unknown makes |
| Test Volume | `COUNT(*) >= 100` | Minimum 100 tests per make |

### Why Pattern Matching for UNCLASSIFIED?

The original filter used exact match (`make != 'UNCLASSIFIED'`), which missed variants:
- `UNCLASSIFIED UNCLASSIFIED`
- `IVECO-FORD UNCLASSIFIED`
- `UNCLASSIFIED (various)`

Using `NOT LIKE '%UNCLASSIFIED%'` catches all variants.

### Why 100-Test Minimum?

Without this threshold, the database contained 7,628 "manufacturers" including garbage entries like:
- `BMW 330I SE MSPORT 3.0L` (model name misrecorded as make)
- `FORD FOCUS 1.6 ZETEC` (trim level in make field)
- Various typos and data entry errors

With the threshold: ~181 legitimate manufacturers remain.

---

## Stage 2: Base Tests Table Creation

**Function:** `create_base_tests_table()` (lines 131-153)

```sql
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
  AND tr.make IN (SELECT make FROM valid_makes)
```

### Key Points

- Applies the same base filters as Stage 1
- Joins to `valid_makes` to include only qualified manufacturers
- Adds computed columns: `model_year` and `vehicle_age`
- Creates indexes for query performance

---

## Data Flow Diagram

```
Raw CSV Files (32.8M tests)
         │
         ▼
    ┌─────────────────────────────────────┐
    │  Stage 1: Filter Valid Makes        │
    │  - Apply base criteria              │
    │  - Exclude UNCLASSIFIED variants    │
    │  - Require 100+ tests per make      │
    │  Result: ~181 valid manufacturers   │
    └─────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────┐
    │  Stage 2: Create base_tests         │
    │  - Apply base criteria              │
    │  - Filter to valid_makes only       │
    │  - Add computed columns             │
    │  Result: Filtered test dataset      │
    └─────────────────────────────────────┘
         │
         ▼
    18 Insight Tables
    (vehicle_insights, manufacturer_rankings, etc.)
```

---

## Filter Summary Table

| Filter | Value | Records Removed |
|--------|-------|-----------------|
| Re-Tests | `test_type != 'NT'` | ~5M |
| Invalid Results | Not in `('P', 'F', 'PRS')` | ~100K |
| Non-Class 4 | `test_class_id != '4'` | ~2M |
| Placeholder Dates | `= '1971-01-01'` | ~50K |
| UNCLASSIFIED Makes | `LIKE '%UNCLASSIFIED%'` | ~200K |
| Low-Volume Makes | `< 100 tests` | ~500K |

---

## Impact on Output

| Metric | Before Filtering | After Filtering |
|--------|------------------|-----------------|
| Distinct Manufacturers | 7,628 | ~181 |
| Makes with <100 tests | 7,447 | 0 |
| UNCLASSIFIED variants | Present | None |

---

## Related Files

| File | Purpose |
|------|---------|
| `generate_insights_optimized.py` | Main generator script |
| `DATABASE_SPEC.md` | Full database schema documentation |
| `mot_insights.db` | Output SQLite database |

---

*Last updated: January 2026*
