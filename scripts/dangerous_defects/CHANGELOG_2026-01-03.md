# Dangerous Defects Insights Generator - Session Changes

**Date:** 2026-01-03
**Scope:** Critical accuracy fixes for `generate_dangerous_defects_insights.py`

---

## Summary

Fixed survivorship bias in all SQL queries by converting INNER JOINs to LEFT JOINs. The original queries only included vehicles that had at least one dangerous defect, which systematically excluded defect-free vehicles from calculations.

---

## Problem Identified

### Root Cause
The `dangerous_defects` table only contains records for vehicles **with** dangerous defects. The original queries used:

```sql
FROM dangerous_defects dd
JOIN vehicle_insights vi ON ...
```

This pattern excluded vehicles with zero dangerous defects from:
- Overall rate calculations
- Make/model rankings
- "Safest vehicles" lists
- Fuel type comparisons

### Impact Assessment
After analysis, only **2 out of 11,406 variants (0.0%)** have zero dangerous defects, so practical impact was minimal. However, the fix ensures:
1. **Technical correctness** - queries now semantically accurate
2. **Future-proofing** - new data with zero-defect vehicles will be handled correctly
3. **Proper methodology** - denominator includes ALL tests

---

## Changes Made

### 1. Core Query Pattern Change

**Before:**
```sql
FROM dangerous_defects dd
JOIN vehicle_insights vi
    ON dd.make = vi.make
    AND dd.model = vi.model
    AND dd.model_year = vi.model_year
    AND dd.fuel_type = vi.fuel_type
```

**After:**
```sql
FROM vehicle_insights vi
LEFT JOIN dangerous_defects dd
    ON vi.make = dd.make
    AND vi.model = dd.model
    AND vi.model_year = dd.model_year
    AND vi.fuel_type = dd.fuel_type
-- Use COALESCE(SUM(dd.occurrence_count), 0) for counts
```

### 2. Functions Fixed

| Function | Lines | Change |
|----------|-------|--------|
| `get_overall_statistics()` | 67-78 | LEFT JOIN, COALESCE |
| `get_rankings_by_make()` | 131-147 | LEFT JOIN, COALESCE, fuel_type in variant count |
| `get_rankings_by_model()` | 160-177 | LEFT JOIN, COALESCE |
| `get_worst_vehicles_by_year_range()` | 188-204 | LEFT JOIN, COALESCE |
| `get_safest_vehicles_by_year_range()` | 215-231 | LEFT JOIN, COALESCE |
| `get_fuel_type_comparison()` | 242-257 | LEFT JOIN, COALESCE |
| `get_diesel_vs_petrol_same_model()` | 270-298 | LEFT JOIN in CTE, COALESCE |
| `get_age_controlled_comparison()` | 305-321 | LEFT JOIN, COALESCE |
| `get_category_rates_by_make()` | 333-370 | LEFT JOIN, category filter moved to JOIN condition |
| `get_vehicle_deep_dive()` | 378-443 | LEFT JOIN, fixed GROUP BY (removed vi.total_tests) |
| `get_popular_cars_ranked()` | 455-470 | LEFT JOIN, COALESCE |

### 3. Additional Fixes

#### Vehicle Variant Count (lines 96)
**Before:** `COUNT(DISTINCT make || model || model_year)`
**After:** `COUNT(DISTINCT make || model || model_year || fuel_type)`

Petrol and Diesel variants of the same model year are now counted separately.

#### Duplicate Model Years in Deep Dive (line 439)
**Before:** `GROUP BY dd.model_year, vi.total_tests`
**After:** `GROUP BY vi.model_year` with `SUM(vi.total_tests)`

Fixes duplicate year entries caused by multiple fuel types.

#### Diesel vs Petrol Gap Calculation (line 578)
**Before:** Assumed array index order (fragile)
```python
f"+{fuel_comparison[0]['rate'] - fuel_comparison[1]['rate']}"
```

**After:** Explicitly finds fuel types
```python
def _calculate_diesel_petrol_gap(fuel_comparison: list) -> str | None:
    diesel = next((f for f in fuel_comparison if f.get('fuel_type') == 'DI'), None)
    petrol = next((f for f in fuel_comparison if f.get('fuel_type') == 'PE'), None)
    if diesel and petrol:
        gap = diesel['dangerous_rate'] - petrol['dangerous_rate']
        sign = '+' if gap >= 0 else ''
        return f"{sign}{round(gap, 2)}%"
    return None
```

---

## Verification Results

### Before vs After Comparison
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Overall Rate | 5.11% | 5.11% | No change |
| Worst Model | Ford Focus C-MAX (7.81%) | Ford Focus C-MAX (7.81%) | No change |
| Safest Model | Jaguar I-PACE (1.89%) | Jaguar I-PACE (1.89%) | No change |
| Diesel Test Count | 136,598,392 | 136,598,497 | +105 tests |
| Hybrid Test Count | 9,075,160 | 9,075,309 | +149 tests |

### Why Minimal Change?
- Only 2 variants out of 11,406 (0.0%) have zero dangerous defects
- These 2 variants don't meet the minimum test thresholds (100k for models, 2k for buyer guide)
- Virtually all vehicles in the database have at least one dangerous defect recorded

---

## Files Modified

| File | Status |
|------|--------|
| `scripts/dangerous_defects/generate_dangerous_defects_insights.py` | Updated |
| `scripts/dangerous_defects/dangerous_defects_insights.json` | Regenerated |
| `articles/generated/most-dangerous-cars-uk.html` | Regenerated |

### Backup Created
- `dangerous_defects_insights_BEFORE.json` - Original insights before fixes

---

## Testing

1. Generator runs successfully
2. HTML generator produces valid output (123,237 bytes)
3. All data fields populated correctly
4. No zero-defect vehicles currently meet ranking thresholds

---

## Database Schema Reference

### Key Tables
- `vehicle_insights`: 11,406 rows - ALL vehicles with >=100 tests
- `dangerous_defects`: 105,879 rows - Only vehicles WITH dangerous defects (2-10 rows per vehicle)

### Relationship
`dangerous_defects` is a **subset** of `vehicle_insights`. Not all vehicle_insights entries have corresponding dangerous_defects entries.

---

## Future Considerations

1. If new MOT data includes vehicles with zero dangerous defects at scale, these fixes will ensure they appear correctly in rankings
2. Consider adding statistical confidence indicators for low-sample-size rankings
3. The `get_category_breakdown()` function still queries only from `dangerous_defects` (intentional - shows breakdown of actual defects, not rate per vehicle)

---

## Feature Alignment Audit & Fixes (Session 2)

**Scope:** Audit of JSON generator vs HTML components to identify orphaned fields and hardcoded values

### Audit Summary

| Metric | Before | After |
|--------|--------|-------|
| Orphaned fields (parsed but unused) | 12 | 6 |
| Hardcoded values needing dynamic data | 5 | 0 |
| Unparsed JSON fields | 1 | 1 |

---

### Issues Fixed

#### 1. `by_model_year` Data Not Rendered
**Problem:** Vehicle deep dives had rich year-over-year rate data (`by_model_year`) that was generated and parsed but never displayed.

**Fix:** Added CSS mini bar chart in `section_deep_dives.py`
- Shows 6 most recent years, sorted descending
- Bar width proportional to max rate
- Displays year, visual bar, and percentage

#### 2. Hardcoded Hybrid/Diesel Percentages
**File:** `section_fuel.py:64`

| Before | After |
|--------|-------|
| `"3.48% dangerous defect rate - 36% lower"` | Dynamic calculation from `fuel_comparison` data |

#### 3. Hardcoded FAQ Category Percentages
**File:** `html_head.py:25`

| Before | After |
|--------|-------|
| `"Tyres account for 61.6%...Brakes account for 37.2%"` | Dynamic lookup from `insights.categories` |

#### 4. Hardcoded Prius Rate
**File:** `section_rankings.py:120`

| Before | After |
|--------|-------|
| `"3.24% dangerous defect rate"` | `{prius.dangerous_rate:.2f}%` |

#### 5. Hardcoded Difference Factor
**File:** `section_header.py:106`

| Before | After |
|--------|-------|
| `"more than 4 times higher"` | `{insights.rate_difference_factor}x higher` |

#### 6. Missing `affected_models` Column
**File:** `section_defects.py`

**Change:** Added 4th column "Models Affected" to top defects table showing how widespread each defect is across different vehicles.

---

### Files Modified

| File | Change |
|------|--------|
| `components/section_fuel.py` | Dynamic hybrid/diesel rate calculation |
| `components/html_head.py` | Dynamic category percentages in FAQ schema |
| `components/section_rankings.py` | Dynamic Prius rate |
| `components/section_header.py` | Dynamic difference factor |
| `components/section_defects.py` | Added "Models Affected" column |
| `components/section_deep_dives.py` | Added by_model_year bar chart |

---

### Remaining Lower-Priority Items

Fields parsed but not displayed (future enhancements):

| Field | Location | Potential Use |
|-------|----------|---------------|
| `fuel_type_analysis.insight` | `data_parser.py:229` | Display as dynamic callout |
| `age_controlled_analysis.description` | `data_parser.py:286` | Display as section intro |
| `category_breakdown[*].vehicle_variants` | `data_parser.py:164` | Show variant count per category |
| `category_breakdown[*].unique_defects` | `data_parser.py:165` | Show defect diversity |
| `rankings.by_make[*].variants_with_data` | `data_parser.py:190` | Show sample coverage |
| `overall_statistics.total_records` | Not parsed | Show total defect records |

---

### Testing Checklist

- [ ] Fuel section: Hybrid percentage matches JSON data
- [ ] Fuel section: "X% lower than diesels" calculated correctly
- [ ] FAQ schema: Category percentages match `category_breakdown`
- [ ] Rankings: Prius rate matches actual data
- [ ] Header: Difference factor matches `key_findings.rate_range.difference_factor`
- [ ] Defects table: Shows 4 columns with "Models Affected"
- [ ] Vehicle deep dives: Each shows bar chart with year-over-year rates
