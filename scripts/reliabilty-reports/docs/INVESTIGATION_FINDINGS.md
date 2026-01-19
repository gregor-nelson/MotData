# MOT Reliability Reports - Investigation Findings

**Date:** 2026-01-19
**Purpose:** Handoff document for fixing identified issues in the reliability report generator
**Reference Report:** `reports/reference_example.html` (Ford)

---

## Executive Summary

The reliability report generator has several critical issues causing inaccurate/misleading outputs:

1. **Manufacturer ranking displays incorrectly** - Shows "#5782 out of 75" when it should be "#37 out of 52"
2. **"Best Models" lists inappropriate vehicles** - Classic cars and motorhome brands appear instead of popular models
3. **Fuel type analysis shows invalid codes** - Garbage fuel codes like "ST", "LN", "FC" with 1-3 tests
4. **Minimum test thresholds too low** - 50 tests is insufficient for reliability claims

---

## Issue 1: Manufacturer Ranking Bug (CRITICAL)

### Problem
Report shows: "Ford ranks **#5782 out of 75** manufacturers"

### Root Cause
The `manufacturer_rankings` database table contains **7,628 entries** - a mix of:
- Actual manufacturer brands (FORD, BMW, etc.)
- Individual model variants ("BMW 330I SE MSPORT 3.0L")

The `rank` field stores Ford's position among ALL 7,628 entries, but `rank_total` is hardcoded as `75` in the parser.

### Database Evidence
```sql
-- Total entries in manufacturer_rankings
SELECT COUNT(*) FROM manufacturer_rankings;  -- Returns: 7628

-- Ford's actual data
SELECT id, make, rank, total_tests FROM manufacturer_rankings WHERE make='FORD';
-- Returns: id=5782, rank=5782, total_tests=4473074

-- Manufacturers with 10k+ tests (sensible threshold)
SELECT COUNT(*) FROM manufacturer_rankings WHERE total_tests >= 10000;  -- Returns: 52

-- Ford's CORRECT rank among major manufacturers
SELECT make, avg_pass_rate, ROW_NUMBER() OVER (ORDER BY avg_pass_rate DESC) as calculated_rank
FROM manufacturer_rankings WHERE total_tests >= 10000 ORDER BY avg_pass_rate DESC;
-- Ford is #37 out of 52
```

### Files to Modify

**`json_parser/parser.py`**
- Line 1002: `"rank_total": 75,` is hardcoded
- Need to calculate actual rank among filtered manufacturers

```python
# Current (wrong):
"summary": {
    ...
    "rank": overview["rank"],      # Uses DB value (5782)
    "rank_total": 75,              # Hardcoded!
}

# Fix approach:
# Calculate rank dynamically among manufacturers with total_tests >= 10000
```

### Recommended Fix
```python
def get_manufacturer_rank_filtered(conn, make: str, min_tests: int = 10000) -> tuple[int, int]:
    """Calculate rank among manufacturers with minimum test threshold."""
    cur = conn.execute("""
        SELECT make,
               ROW_NUMBER() OVER (ORDER BY avg_pass_rate DESC) as calc_rank,
               COUNT(*) OVER () as total_count
        FROM manufacturer_rankings
        WHERE total_tests >= ?
    """, (min_tests,))

    for row in cur.fetchall():
        if row['make'] == make:
            return row['calc_rank'], row['total_count']
    return None, None
```

---

## Issue 2: Classic Cars & Motorhome Brands in "Best Models"

### Problem
The "Best Ford Models" table shows:
| Model | Tests | Issue |
|-------|-------|-------|
| GT | 131 | Supercar/collector (1963-2021) |
| ANGLIA | 253 | Classic car (1946-2018) |
| BENIMAR | 633 | **Motorhome brand** |
| CONSUL | 80 | Classic (1955-2018) |
| ZEPHYR | 64 | Classic (1953-2017) |
| AUTO-TRAIL | 182 | **Motorhome brand** |
| CHAUSSON | 944 | **Motorhome brand** |

### Root Causes

**A) Survivorship Bias for Classics**
- Old cars still running are lovingly maintained by enthusiasts
- They pass MOTs because owners invest heavily in upkeep
- Not representative of original build quality

**B) Motorhome Brands Using Ford Chassis**
- BENIMAR, AUTO-TRAIL, CHAUSSON, ROLLER TEAM are motorhome manufacturers
- They build on Ford Transit chassis
- Listed as Ford "models" but aren't Ford products

**C) Sample Size Too Low**
- Current `min_tests: 50` in `parser.py:53`
- Models with 64-253 tests shouldn't be in "best models" list

### Database Evidence - Motorhome Brands
```sql
SELECT model, SUM(total_tests) as tests
FROM vehicle_insights
WHERE make='FORD'
  AND model LIKE 'BENIMAR%' OR model LIKE 'AUTO-TRAIL%'
  OR model LIKE 'CHAUSSON%' OR model LIKE 'ROLLER%'
GROUP BY model;

-- BENIMAR variants: 633 tests total
-- AUTO-TRAIL variants: 182 tests total
-- CHAUSSON variants: 944 tests total
-- ROLLER TEAM variants: 1066 tests total
```

### Database Evidence - Classic Cars
```sql
SELECT model, MIN(model_year) as earliest, SUM(total_tests) as tests
FROM vehicle_insights
WHERE make='FORD' AND model IN ('GT','ANGLIA','CONSUL','ZEPHYR','POPULAR','CORTINA')
GROUP BY model;

-- GT: earliest 1963, 131 tests
-- ANGLIA: earliest 1946, 253 tests
-- CONSUL: earliest 1955, 80 tests
-- ZEPHYR: earliest 1953, 64 tests
-- POPULAR: earliest 1934, 110 tests
```

### Files to Modify

**`json_parser/parser.py`**
- Line 460-502: `get_core_models_aggregated()` - add filtering
- Line 53: Increase `min_tests` from 50 to higher value for best models

### Recommended Fix - Add Exclusion Lists

```python
# Add to parser.py configuration section

# Motorhome brands that use manufacturer chassis (not actual car models)
MOTORHOME_BRANDS = {
    'AUTO-TRAIL', 'BENIMAR', 'CHAUSSON', 'ROLLER TEAM', 'ROLLERTEAM',
    'HOBBY', 'SWIFT', 'BESSACARR', 'CI', 'TRIGANO', 'RIMOR', 'LAIKA',
    'ADRIA', 'HYMER', 'BURSTNER', 'DETHLEFFS', 'BAILEY', 'ELDDIS',
    'RAPIDO', 'PILOTE', 'EURAMOBIL', 'SUNLIGHT', 'KNAUS', 'WEINSBERG',
    'AUTOSTAR', 'LUNAR', 'CARADO', 'MORELO', 'CARTHAGO'
}

# Classic/vintage models with survivorship bias
CLASSIC_CAR_MODELS = {
    'ANGLIA', 'CONSUL', 'ZEPHYR', 'POPULAR', 'PREFECT', 'MODEL T',
    'MODEL A', 'MODEL Y', 'MODEL B', 'TUDOR', 'SQUIRE'
}

# Minimum tests for "Best Models" section (higher than general min_tests)
MIN_TESTS_BEST_MODELS = 1000

def is_excluded_model(model_name: str, year_from: int = None) -> bool:
    """Check if model should be excluded from best models list."""
    first_word = model_name.split()[0] if model_name else ''

    # Exclude motorhome brands
    if first_word in MOTORHOME_BRANDS:
        return True

    # Exclude known classic car models
    if model_name in CLASSIC_CAR_MODELS:
        return True

    # Exclude very old models (pre-1980)
    if year_from and year_from < 1980:
        return True

    return False
```

**Apply filter in `get_core_models_aggregated()`:**
```python
def get_core_models_aggregated(conn, make: str, config: dict = None) -> list:
    # ... existing code ...

    results = []
    for core in sorted(core_names):
        # ... existing query ...

        if row and row["total_tests"]:
            data = dict_from_row(row)

            # NEW: Apply exclusion filter
            if is_excluded_model(data["core_model"], data.get("year_from")):
                continue

            results.append(data)
```

---

## Issue 3: Invalid Fuel Type Codes

### Problem
Fuel analysis table shows garbage fuel codes:
| Code | Tests | Pass Rate |
|------|-------|-----------|
| ST | 1 | 100% |
| LN | 2 | 100% |
| FC | 1 | 100% |
| CN | 3 | 100% |
| GD | 6 | 83.3% |
| GA | 23 | 65.2% |
| LP | 679 | 62.3% |

### Database Evidence
```sql
SELECT fuel_type, COUNT(*) as models, SUM(total_tests) as tests
FROM vehicle_insights WHERE make='FORD'
GROUP BY fuel_type ORDER BY tests DESC;

-- PE (Petrol): 2,547,911 tests
-- DI (Diesel): 1,917,341 tests
-- HY (Hybrid): 6,381 tests
-- LP: 679 tests          -- Unknown code
-- EL (Electric): 505 tests
-- ED (Plug-in Hybrid): 166 tests
-- GB (Gas Bi-fuel): 47 tests
-- GA: 23 tests           -- Unknown code
-- OT (Other): 8 tests
-- GD: 6 tests            -- Unknown code
-- CN: 3 tests            -- Unknown code
-- LN: 2 tests            -- Unknown code
-- ST: 1 test             -- Unknown code
-- FC: 1 test             -- Unknown code
```

### Valid Fuel Codes (defined in data_classes.py:19-27)
```python
FUEL_TYPE_NAMES = {
    'PE': 'Petrol',
    'DI': 'Diesel',
    'HY': 'Hybrid Electric',
    'EL': 'Electric',
    'ED': 'Plug-in Hybrid',
    'GB': 'Gas Bi-fuel',
    'OT': 'Other',
}
```

### Files to Modify

**`json_parser/parser.py`**
- Line 552-582: `get_fuel_type_breakdown()` - add validation

### Recommended Fix
```python
# Valid fuel type codes
VALID_FUEL_TYPES = {'PE', 'DI', 'HY', 'EL', 'ED', 'GB', 'OT'}
MIN_TESTS_FUEL_TYPE = 20  # Minimum tests to show a fuel type

def get_fuel_type_breakdown(conn, make: str) -> list:
    """Get pass rates by fuel type for this make."""
    cur = conn.execute("""
        SELECT fuel_type, COUNT(*) as model_count,
               SUM(total_tests) as total_tests,
               ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate
        FROM vehicle_insights
        WHERE make = ?
        GROUP BY fuel_type
        ORDER BY pass_rate DESC
    """, (make,))

    fuel_names = {
        "PE": "Petrol", "DI": "Diesel", "HY": "Hybrid Electric",
        "EL": "Electric", "ED": "Plug-in Hybrid", "GB": "Gas Bi-fuel", "OT": "Other"
    }

    results = []
    for row in cur.fetchall():
        data = dict_from_row(row)
        fuel_code = data["fuel_type"]

        # NEW: Filter invalid codes and low sample sizes
        if fuel_code not in VALID_FUEL_TYPES:
            continue
        if data["total_tests"] < MIN_TESTS_FUEL_TYPE:
            continue

        data["fuel_name"] = fuel_names.get(fuel_code, "Other")
        results.append(data)

    return results
```

---

## Issue 4: Minimum Test Thresholds

### Current Thresholds (inconsistent)

| Location | Value | Used For |
|----------|-------|----------|
| `parser.py:53` | 50 | `DEFAULT_CONFIG["min_tests"]` - general inclusion |
| `parser.py:54` | 100 | `min_tests_trajectory` - trajectory analysis |
| `parser.py:105` | 50 | `MIN_TESTS_DEFAULT` |
| `data_classes.py:37` | 100 | `MIN_TESTS_PROVEN_DURABILITY` |
| `data_classes.py:38` | 100 | `MIN_TESTS_EARLY_PERFORMER` |
| `sections.py:572` | 10000 | Model year breakdowns |
| `sections.py:972` | 50000 | Popular models for recommendations |

### Problem
- 50 tests is too low for "best models" claims (±15% statistical swing)
- Classic cars with 64-253 tests appear as "best models"
- Should use tiered thresholds based on prominence of display

### Recommended Thresholds

| Use Case | Recommended Min | Rationale |
|----------|-----------------|-----------|
| "Best Models" headline list | 1,000 | Featured prominently, needs confidence |
| General model inclusion | 100 | Basic analysis, with caveats |
| Fuel type display | 50 | Lower bar acceptable |
| "Models to Avoid" | 100 | Warnings need solid data |
| Meta description models | 10,000 | SEO-facing, must be popular models |
| Durability champions | 500 | Long-term claims need history |

---

## Issue 5: Meta Description Lists Wrong Models

### Problem
Meta description says: "GT, ANGLIA, BENIMAR, CONSUL and ZEPHYR"
Should say: "Focus, Fiesta, Mondeo, Kuga, Transit" (popular models)

### Root Cause
`layout.py:46-47` uses `insights.top_models[:5]` which is sorted by pass rate, picking highest-passing (but obscure) models.

```python
# Current (layout.py:46-47):
top_models = [m.name for m in insights.top_models[:5]]
```

### Recommended Fix
```python
# Use most-tested models instead (popularity over pass rate)
def get_popular_models_for_meta(insights, limit=5) -> list[str]:
    """Get most popular models by test count for meta description."""
    by_tests = sorted(insights.core_models, key=lambda m: m.total_tests, reverse=True)
    # Filter out motorhomes and classics
    filtered = [m for m in by_tests if not is_excluded_model(m.name, m.year_from)]
    return [m.name for m in filtered[:limit]]
```

---

## Issue 6: "Models to Avoid" Shows Average Performers

### Problem
Some "avoid" models have 70%+ pass rates (national average is 71.4%):
- TOURNEO CUSTOM 320 ZETEC EBLUE 2020: 70.8%
- TRANSIT CUSTOM 340 TREND EBLUE 2020: 70.8%

### Root Cause
The section mixes two data sources:
1. `proven_models_to_avoid` (age-band analysis, uses `vs_national < -3`)
2. `worst_models` (year-adjusted, may include near-average performers)

### Recommended Fix
Only show models that are **significantly** below average:
- Pass rate < 60%, OR
- vs_national < -10%

---

## Files Summary

### Primary Files to Modify

| File | Lines | Changes Needed |
|------|-------|----------------|
| `json_parser/parser.py` | 53-54, 460-502, 552-582, 1002 | Thresholds, filtering, rank calculation |
| `html_generator/components/data_classes.py` | 37-38 | Threshold constants |
| `html_generator/components/layout.py` | 46-47 | Meta description model selection |
| `html_generator/components/sections.py` | 268-343 | Best models section filtering |

### New Code to Add

1. **Exclusion lists** - Motorhome brands, classic car models
2. **Filtering function** - `is_excluded_model()`
3. **Rank calculation** - `get_manufacturer_rank_filtered()`
4. **Fuel type validation** - Valid codes list + minimum tests

---

## Testing After Fixes

1. Regenerate Ford report: `python main.py generate ford`
2. Verify:
   - Ranking shows "#37 out of 52" (or similar)
   - Best models shows Focus, Fiesta, Puma, Kuga, etc.
   - No motorhome brands (BENIMAR, CHAUSSON, etc.)
   - No classics (ANGLIA, GT, CONSUL, etc.)
   - Fuel types only show PE, DI, HY, EL, ED, GB
   - Meta description lists popular models

---

## Database Reference

**Path:** `C:\Users\gregor\Downloads\Mot Data\data\source\database\mot_insights.db`

**Key Tables:**
- `manufacturer_rankings` - Make-level stats (7,628 rows including variants)
- `vehicle_insights` - Model/year/fuel combinations with pass rates
- `national_averages` - Benchmark pass rates by year

**Useful Queries:**
```sql
-- Major manufacturers (10k+ tests)
SELECT make, avg_pass_rate, total_tests,
       ROW_NUMBER() OVER (ORDER BY avg_pass_rate DESC) as rank
FROM manufacturer_rankings
WHERE total_tests >= 10000
ORDER BY avg_pass_rate DESC;

-- Top models for a make (excluding low-volume)
SELECT model, SUM(total_tests) as tests,
       ROUND(SUM(total_passes)*100.0/SUM(total_tests),1) as pass_rate
FROM vehicle_insights
WHERE make='FORD'
GROUP BY model
HAVING tests >= 1000
ORDER BY pass_rate DESC
LIMIT 20;
```
