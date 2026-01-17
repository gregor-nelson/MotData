# Session Kickoff: Complete MOT Data Filter Removal

## Context

You are continuing work on removing data filtering from `generate_insights_optimized.py`. The goal is to capture **maximum data fidelity** during CSV-to-SQLite conversion, with the philosophy that any filtering should happen downstream in the API/application layer.

## First Steps

1. **Read the spec document** to understand what has already been done:
   ```
   docs/DEFECT_DATA_CAPTURE_SPEC.md
   ```

2. **Review the current state** of the main script:
   ```
   main/generate_insights_optimized.py
   ```

3. **Ask any clarifying questions** before making changes.

---

## Remaining Tasks (8 items)

### Task 1: Remove HAVING from `generate_seasonal_patterns_bulk()`

**Location:** Lines ~1403-1431

**Changes required:**
- Line 1408: Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
- Line 1430: Remove `HAVING COUNT(*) >= 10` from final GROUP BY

**Note:** `MIN_SAMPLE_SIZE` constant was already deleted, so these lines will cause runtime errors until fixed.

---

### Task 2: Remove HAVING from `generate_failure_severity_bulk()`

**Location:** Lines ~1449-1455

**Changes required:**
- Line 1454: Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE

---

### Task 3: Remove HAVING from `generate_retest_success_bulk()`

**Location:** Lines ~1510-1564

**Changes required:**
- Line 1515: Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
- Line 1564: Remove `HAVING COUNT(DISTINCT ft.test_id) >= 10` from stats CTE

---

### Task 4: Remove HAVING/WHERE from `generate_component_mileage_thresholds_bulk()`

**Location:** Lines ~1591-1675

**Changes required:**
- Line 1596: Remove `HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}` from vehicle_combos CTE
- Line 1662: Remove `WHERE bt.total_tests >= 10` from failure_rates CTE
- Line 1675: Remove `HAVING COUNT(*) >= 3` from pivoted CTE

---

### Task 5: Add Minor Defects Query Block

**Location:** Inside `generate_top_defects_bulk()`, after the advisory defects section (around line 870)

**Purpose:** Capture `rfr_type_code = 'M'` (Minor defects, introduced May 2018)

**Pattern:** Follow the same pattern as advisory defects but with:
- `defect_type = 'minor'`
- `ti.rfr_type_code = 'M'`

**Full implementation template is in the spec document** - look for "Suggested implementation" under "Add Minor Defects Query Block".

---

### Task 6: Fix Step Numbering

**Issue:** Step numbers are inconsistent (mix of `/20` and `/19`) because `generate_age_bands_bulk()` was removed.

**Required:** Update all print statements to reflect 19 total steps:

| Current | Should Be | Function |
|---------|-----------|----------|
| `[1/20]` | `[1/19]` | CSV import |
| `[2/20]` | `[2/19]` | base_tests |
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
| `[13/19]` | `[13/19]` | first_mot_insights (OK) |
| `[14/19]` | `[14/19]` | manufacturer_rankings (OK) |
| `[16/20]` | `[15/19]` | seasonal_patterns |
| `[17/20]` | `[16/19]` | failure_severity |
| `[18/20]` | `[17/19]` | retest_success |
| `[19/20]` | `[18/19]` | component_mileage_thresholds |
| `[20/20]` | `[19/19]` | cleanup |

---

### Task 7: Test Script Execution

After all code changes, verify the script runs without errors:
```bash
python main/generate_insights_optimized.py
```

Note: Full execution takes 30-60 minutes with the ~4GB dataset.

---

### Task 8: Update Spec Document

After successful execution:
- Move remaining tasks to "Completed Changes" section
- Add actual row counts and database size
- Record any issues encountered

---

## Key Files

| File | Purpose |
|------|---------|
| `main/generate_insights_optimized.py` | Main script being modified |
| `docs/DEFECT_DATA_CAPTURE_SPEC.md` | Detailed spec with code snippets |
| `data/source/*.csv` | Source MOT data (~4GB total) |
| `data/source/data/mot_insights.db` | Output SQLite database |

---

## What Was Already Completed

1. Removed `MIN_SAMPLE_SIZE = 100` constant
2. Removed `YEAR(tr.first_use_date) >= 2000` filter from base_tests
3. Removed entire age bands feature (constant, table, index, function, call)
4. Changed mileage cap from `999999999` to `None` (unlimited)
5. Removed HAVING/rank limits from 10 functions (listed in spec)

---

## Data Quality Filters That Should STAY

These filters ensure data quality, not limit volume:

| Filter | Reason |
|--------|--------|
| `test_type = 'NT'` | Normal Tests only |
| `test_result IN ('P', 'F', 'PRS')` | Valid outcomes |
| `test_class_id = '4'` | Class 4 vehicles (cars) |
| `first_use_date != '1971-01-01'` | Placeholder date |
| `make != 'UNCLASSIFIED'` | Invalid make |
| `postcode_area != 'XX'` | Invalid postcode |
| `test_mileage > 0` | Valid mileage |
| `location_id > 0` | Valid location |

---

## Quick Verification Commands

After completing changes, these greps should return no results:

```bash
# Should find NO matches after fixing
grep -n "MIN_SAMPLE_SIZE" main/generate_insights_optimized.py
grep -n "HAVING COUNT" main/generate_insights_optimized.py
grep -n "total_tests >= 10" main/generate_insights_optimized.py
grep -n "/20\]" main/generate_insights_optimized.py
```

This grep SHOULD find matches (the new minor defects code):
```bash
grep -n "rfr_type_code = 'M'" main/generate_insights_optimized.py
```
