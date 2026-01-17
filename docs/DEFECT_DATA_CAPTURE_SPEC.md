# MOT Defect Data Capture - Technical Reference Spec

**Created:** 2026-01-17
**Last Updated:** 2026-01-17
**Purpose:** Document changes to remove filtering from `generate_insights_optimized.py` to capture maximum data fidelity.

---

## Executive Summary

The MOT insights database was applying multiple filters that reduced data capture during CSV-to-SQLite conversion. The user requested removal of ALL filtering that alters the conversion, with the philosophy that **any filtering should happen downstream in the API/application layer where it's needed**.

**Status:** Work in progress - see "Completed Changes" and "Remaining Work" sections below.

---

## Source Data Structure

### Key Files (in `data/source/`)

| File | Size | Rows | Purpose |
|------|------|------|---------|
| `test_result.csv` | ~4GB | ~30M | Individual MOT test records |
| `test_item.csv` | ~1.9GB | ~89M | Defect/advisory items linked to tests |
| `item_detail.csv` | ~3.4MB | ~7,505 | Defect code definitions (rfr_id lookup) |
| `item_group.csv` | Small | ~934 | Category groupings for class 4 vehicles |

### test_item.csv - rfr_type_code Distribution

```
Code | Count       | Meaning
-----|-------------|------------------------------------------
A    | 58,089,063  | Advisory - warnings, not failures
F    | 21,543,744  | Failure - caused MOT to fail
M    |  6,599,101  | Minor defects (post-May 2018 category)
P    |  3,070,724  | PRS - Pass with Rectification at Station
```

**Total:** ~89.3 million defect/advisory records

### Distinct Defect Types

- **Defined in item_detail.csv:** 7,505 unique `rfr_id` values
- **Actually used in test_item.csv:** 2,424 unique `rfr_id` values
- **Previously captured in database:** ~30 unique descriptions (due to top-10 limit per variant)

---

## Completed Changes

### 1. Removed MIN_SAMPLE_SIZE Constant

**Location:** Line ~33 (was)
**Change:** Deleted `MIN_SAMPLE_SIZE = 100` constant entirely

**Impact:** This constant was used in 7 HAVING clauses throughout the code. Now references to `{MIN_SAMPLE_SIZE}` will cause errors until those HAVING clauses are removed.

### 2. Removed Year 2000 Filter from base_tests

**Location:** `create_duckdb_connection()` function, base_tests creation (line ~146)
**Change:** Removed `AND YEAR(tr.first_use_date) >= 2000` from WHERE clause

**Before:**
```python
WHERE tr.test_type = 'NT'
  AND tr.test_result IN ('P', 'F', 'PRS')
  AND CAST(tr.test_class_id AS VARCHAR) = '4'
  AND tr.first_use_date != '1971-01-01'
  AND tr.make != 'UNCLASSIFIED'
  AND YEAR(tr.first_use_date) >= 2000  -- REMOVED
```

**After:**
```python
WHERE tr.test_type = 'NT'
  AND tr.test_result IN ('P', 'F', 'PRS')
  AND CAST(tr.test_class_id AS VARCHAR) = '4'
  AND tr.first_use_date != '1971-01-01'
  AND tr.make != 'UNCLASSIFIED'
```

**Rationale:** Captures all vehicles regardless of model year.

### 3. Removed Age Bands Feature Entirely

**Locations removed:**
- `AGE_BANDS` constant (was after MILEAGE_BANDS)
- `age_bands` table creation in SQLite schema
- `idx_ab_lookup` index creation
- `generate_age_bands_bulk()` function (entire function removed)
- Function call from `main()`

**Rationale:** MOT testing isn't required for vehicles under 3 years old anyway, so age filtering is unnecessary at the database level.

### 4. Removed Mileage Upper Cap

**Location:** `MILEAGE_BANDS` constant (lines 38-46)

**Before:**
```python
MILEAGE_BANDS = [
    (0, 30000, "0-30k", 0),
    (30001, 60000, "30k-60k", 1),
    (60001, 90000, "60k-90k", 2),
    (90001, 120000, "90k-120k", 3),
    (120001, 150000, "120k-150k", 4),
    (150001, 999999999, "150k+", 5),  # Had artificial cap
]
```

**After:**
```python
MILEAGE_BANDS = [
    (0, 30000, "0-30k", 0),
    (30001, 60000, "30k-60k", 1),
    (60001, 90000, "60k-90k", 2),
    (90001, 120000, "90k-120k", 3),
    (120001, 150000, "120k-150k", 4),
    (150001, None, "150k+", 5),  # No upper limit
]
```

**Also updated:** `generate_mileage_bands_bulk()` function now handles `None` upper limit:
```python
for low, high, label, order in MILEAGE_BANDS:
    if high is None:
        case_expr += f"WHEN test_mileage >= {low} THEN '{label}' "
    else:
        case_expr += f"WHEN test_mileage >= {low} AND test_mileage <= {high} THEN '{label}' "
```

### 5. Removed HAVING Clauses (Partial - Functions Completed)

The following functions have had their HAVING clauses and rank limits removed:

| Function | Changes Made |
|----------|--------------|
| `generate_vehicle_insights_bulk()` | Removed `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` |
| `generate_failure_categories_bulk()` | Removed `WHERE rank <= 10` |
| `generate_top_defects_bulk()` | Removed `WHERE rank <= 10` from failure defects, advisory defects sections |
| `generate_geographic_insights_bulk()` | Removed HAVING clause |
| `generate_defect_locations_bulk()` | Removed rank limit |
| `generate_advisory_progression_bulk()` | Removed HAVING clauses |
| `generate_rankings_bulk()` | No filtering changes needed (uses window functions) |
| `generate_dangerous_defects_bulk()` | Removed `WHERE rank <= 10` and `WHERE rank <= 20` |
| `generate_first_mot_insights_bulk()` | Removed HAVING clauses |
| `generate_manufacturer_rankings()` | Removed `WHERE total_tests >= 100` |

### 6. Partial Step Number Updates

Some step numbers have been partially updated (from 20 to 19 steps due to age_bands removal), but this is inconsistent and needs full correction.

---

## Remaining Work

### 1. Remove Remaining HAVING Clauses

The following functions still contain HAVING clauses that need removal:

#### a) `generate_seasonal_patterns_bulk()` - Lines 1403-1431

**Line 1408:** Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
**Line 1430:** Remove `HAVING COUNT(*) >= 10` from final GROUP BY

**Current code to fix:**
```python
results = duck_conn.execute(f"""
    WITH vehicle_combos AS (
        SELECT make, model, model_year, fuel_type
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}  -- REMOVE THIS
    )
    ...
    GROUP BY bt.make, bt.model, bt.model_year, bt.fuel_type, month, quarter
    HAVING COUNT(*) >= 10  -- REMOVE THIS
""").fetchall()
```

#### b) `generate_failure_severity_bulk()` - Lines 1449-1455

**Line 1454:** Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE

**Current code to fix:**
```python
results = duck_conn.execute(f"""
    WITH vehicle_combos AS (
        SELECT make, model, model_year, fuel_type
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}  -- REMOVE THIS
    ),
    ...
```

#### c) `generate_retest_success_bulk()` - Lines 1510-1564

**Line 1515:** Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
**Line 1564:** Remove `HAVING COUNT(DISTINCT ft.test_id) >= 10` from stats CTE

**Current code to fix:**
```python
results = duck_conn.execute(f"""
    WITH vehicle_combos AS (
        SELECT make, model, model_year, fuel_type
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}  -- REMOVE THIS
    ),
    ...
    stats AS (
        ...
        GROUP BY ft.make, ft.model, ft.model_year, ft.fuel_type
        HAVING COUNT(DISTINCT ft.test_id) >= 10  -- REMOVE THIS
    )
```

#### d) `generate_component_mileage_thresholds_bulk()` - Lines 1591-1675

**Line 1596:** Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
**Line 1662:** Remove `WHERE bt.total_tests >= 10` from failure_rates CTE
**Line 1675:** Remove `HAVING COUNT(*) >= 3` from pivoted CTE

**Current code to fix:**
```python
results = duck_conn.execute(f"""
    WITH vehicle_combos AS (
        SELECT make, model, model_year, fuel_type
        FROM base_tests
        GROUP BY make, model, model_year, fuel_type
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}  -- REMOVE THIS
    ),
    ...
    failure_rates AS (
        ...
        WHERE bt.total_tests >= 10  -- REMOVE THIS
    ),
    pivoted AS (
        ...
        GROUP BY make, model, model_year, fuel_type, category_id, category_name
        HAVING COUNT(*) >= 3  -- REMOVE THIS (At least 3 bands with data comment)
    )
```

### 2. Add Minor Defects Query Block

**Purpose:** Capture `rfr_type_code = 'M'` (Minor defects, post-May 2018)

**Location:** Add new section in `generate_top_defects_bulk()` after advisory defects block

**Pattern to follow:** Same as advisory defects block but with:
- `defect_type = 'minor'`
- `ti.rfr_type_code = 'M'`

**Suggested implementation:**
```python
# =========================================================================
# MINOR DEFECTS - Same pattern as advisories, rfr_type_code = 'M'
# =========================================================================
print("  Processing minor defects...")

duck_conn.execute("""
    CREATE TEMP TABLE minor_test_defects AS
    SELECT DISTINCT
        bt.make,
        bt.model,
        bt.model_year,
        bt.fuel_type,
        bt.test_id,
        ti.rfr_id,
        id.rfr_desc_english as defect_description,
        ig.item_name as category_name
    FROM base_tests bt
    JOIN test_item ti ON bt.test_id = ti.test_id
    LEFT JOIN item_detail id ON ti.rfr_id = id.rfr_id AND CAST(id.test_class_id AS VARCHAR) = '4'
    LEFT JOIN item_group ig ON id.test_item_set_section_id = ig.test_item_id
                           AND CAST(ig.test_class_id AS VARCHAR) = '4'
                           AND ig.parent_id = 0
    WHERE ti.rfr_type_code = 'M'
""")

# Count and rank minor defects
minor_results = duck_conn.execute("""
    WITH defect_counts AS (
        SELECT
            make, model, model_year, fuel_type,
            rfr_id, defect_description, category_name,
            COUNT(DISTINCT test_id) as occurrence_count
        FROM minor_test_defects
        GROUP BY make, model, model_year, fuel_type, rfr_id, defect_description, category_name
    ),
    ranked AS (
        SELECT
            dc.*,
            vt.total_tests,
            ROW_NUMBER() OVER (
                PARTITION BY dc.make, dc.model, dc.model_year, dc.fuel_type
                ORDER BY dc.occurrence_count DESC
            ) as rank
        FROM defect_counts dc
        JOIN vehicle_totals vt ON dc.make = vt.make
                               AND dc.model = vt.model
                               AND dc.model_year = vt.model_year
                               AND dc.fuel_type = vt.fuel_type
    )
    SELECT make, model, model_year, fuel_type, rfr_id, defect_description,
           category_name, occurrence_count, total_tests, rank
    FROM ranked
    ORDER BY make, model, model_year, fuel_type, rank
""").fetchall()

for row in minor_results:
    make, model, year, fuel_type, rfr_id, desc, cat, count, total_tests, rank = row
    pct = (count / total_tests) * 100 if total_tests > 0 else 0
    cursor.execute("""
        INSERT INTO top_defects
        (make, model, model_year, fuel_type, rfr_id, defect_description, defect_type,
         category_name, occurrence_count, occurrence_percentage, rank)
        VALUES (?, ?, ?, ?, ?, ?, 'minor', ?, ?, ?, ?)
    """, (make, model, year, fuel_type, rfr_id, desc, cat, count, round(pct, 2), rank))
total_inserted += len(minor_results)

duck_conn.execute("DROP TABLE minor_test_defects")
print(f"  Inserted {len(minor_results):,} minor defect entries")
```

### 3. Fix Step Numbering

**Current state:** Step numbers are inconsistent (mix of /20 and /19)

**Required changes:** Update all print statements to reflect 19 total steps:

| Current | Should Be | Function |
|---------|-----------|----------|
| `[1/20]` | `[1/19]` | CSV import |
| `[2/20]` | `[2/19]` | base_tests creation |
| `[3/20]` | `[3/19]` | national_averages |
| `[4/20]` | `[4/19]` | vehicle_insights |
| `[5/20]` | `[5/19]` | failure_categories |
| `[6/20]` | `[6/19]` | top_defects |
| `[7/20]` | `[7/19]` | mileage_bands |
| `[8/20]` | `[8/19]` | geographic_insights |
| `[9/20]` | `[9/19]` | defect_locations |
| `[10/20]` | `[10/19]` | advisory_progression |
| `[11/20]` | `[11/19]` | rankings |
| `[12/20]` | `[12/19]` | dangerous_defects |
| `[13/19]` | `[13/19]` | first_mot_insights (already correct) |
| `[14/19]` | `[14/19]` | manufacturer_rankings (already correct) |
| `[16/20]` | `[15/19]` | seasonal_patterns |
| `[17/20]` | `[16/19]` | failure_severity |
| `[18/20]` | `[17/19]` | retest_success |
| `[19/20]` | `[18/19]` | component_mileage_thresholds |
| `[20/20]` | `[19/19]` | cleanup |

### 4. Update Spec Document

After all code changes complete, update this document to:
- Move "Remaining Work" items to "Completed Changes"
- Update "Post-Fix Expected Results" with actual results
- Add validation query results

---

## Data Quality Filters Retained

These filters remain because they ensure data quality, not limit data volume:

| Filter | Purpose | Location |
|--------|---------|----------|
| `test_type = 'NT'` | Normal Tests only (excludes incomplete) | base_tests |
| `test_result IN ('P', 'F', 'PRS')` | Valid outcomes only | base_tests |
| `test_class_id = '4'` | Class 4 vehicles (cars) only | base_tests |
| `first_use_date != '1971-01-01'` | Placeholder date removal | base_tests |
| `make != 'UNCLASSIFIED'` | Invalid make removal | base_tests |
| `postcode_area != 'XX'` | Invalid postcode removal | geographic_insights |
| `test_mileage > 0` | Valid mileage only | mileage_bands |
| `location_id > 0` | Valid location only | defect_locations |

---

## Database Schema Notes

### Current `top_defects` Table Schema

```sql
CREATE TABLE top_defects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    fuel_type TEXT,
    rfr_id INTEGER NOT NULL,
    defect_description TEXT NOT NULL,
    category_name TEXT,
    defect_type TEXT NOT NULL,  -- 'failure', 'advisory', or 'minor' (NEW)
    occurrence_count INTEGER NOT NULL,
    occurrence_percentage REAL NOT NULL,
    rank INTEGER NOT NULL
)
```

---

## Post-Fix Expected Results

After completing all changes and regenerating database:

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Unique defects per model | ~30 | Up to 2,424 |
| `top_defects` table rows | ~500K | ~5-10M+ |
| Database size | ~200MB | ~500MB-1GB |
| Generation time | ~30 min | ~45-60 min |
| Minor defects captured | 0 | ~6.6M |

---

## Validation Steps

After regenerating database:

1. **Check unique defect count:**
   ```sql
   SELECT COUNT(DISTINCT defect_description)
   FROM top_defects
   WHERE make = 'AUDI' AND model = 'A3';
   ```
   Expected: Hundreds, not ~30

2. **Check total rows:**
   ```sql
   SELECT COUNT(*) FROM top_defects;
   ```
   Expected: Millions, not hundreds of thousands

3. **Verify defect types:**
   ```sql
   SELECT defect_type, COUNT(*) FROM top_defects GROUP BY defect_type;
   ```
   Expected: Three types - failure, advisory, minor

4. **Verify no MIN_SAMPLE_SIZE filtering:**
   ```sql
   SELECT COUNT(*) FROM vehicle_insights WHERE total_tests < 100;
   ```
   Expected: Some rows (previously would be 0)

---

## Files Modified

| File | Status | Changes |
|------|--------|---------|
| `main/generate_insights_optimized.py` | Partial | See "Completed Changes" section |
| `docs/DEFECT_DATA_CAPTURE_SPEC.md` | Updated | This document |

---

## Quick Reference: Line Numbers for Remaining Changes

All line numbers in `main/generate_insights_optimized.py`:

| Line | Change Required |
|------|-----------------|
| 1408 | Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` |
| 1430 | Remove `HAVING COUNT(*) >= 10` |
| 1454 | Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` |
| 1515 | Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` |
| 1564 | Remove `HAVING COUNT(DISTINCT ft.test_id) >= 10` |
| 1596 | Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` |
| 1662 | Remove `WHERE bt.total_tests >= 10` |
| 1675 | Remove `HAVING COUNT(*) >= 3` |
| ~780-870 | Add minor defects block after advisory defects |
| Multiple | Update step numbers to /19 format |

---

## Session Continuation Checklist

For the next session, work through in this order:

1. [ ] Remove HAVING from `generate_seasonal_patterns_bulk()` (lines 1408, 1430)
2. [ ] Remove HAVING from `generate_failure_severity_bulk()` (line 1454)
3. [ ] Remove HAVING from `generate_retest_success_bulk()` (lines 1515, 1564)
4. [ ] Remove HAVING/WHERE from `generate_component_mileage_thresholds_bulk()` (lines 1596, 1662, 1675)
5. [ ] Add minor defects query block in `generate_top_defects_bulk()`
6. [ ] Fix all step numbers to /19 format
7. [ ] Test that script runs without errors
8. [ ] Update this spec document with final results

---

## Contact / Questions

For clarification on this spec or the MOT data structure, reference:
- DVSA MOT Testing Data User Guide (in `docs/`)
- Source CSV column definitions in data files
