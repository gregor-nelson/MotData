# Parser & HTML Generator Audit Report

**Date:** 2026-01-18
**Auditor:** Claude Code
**Scope:** Comparison of PARSER_SPEC.md, HTML_SPEC.md, and their implementations
**Files Reviewed:**
- `specs/PARSER_SPEC.md`
- `specs/HTML_SPEC.md`
- `json_parser/parser.py`
- `html_generator/components/data_classes.py`
- `html_generator/components/sections.py`
- `data/json/reliability-reports/ford_insights.json` (sample output)

---

## Executive Summary

The v3.0 migration introduced structural changes to the parser output that were not fully synchronized with the HTML generator's expectations. While the system functions due to fallback mechanisms, several features are silently broken or producing incomplete output.

**Critical Issues:** 2
**Medium Issues:** 2
**Minor Issues:** 3

---

## Critical Issues

### 1. Missing `age_adjusted` Key in Parser Output

**Severity:** Critical
**Status:** Confirmed via code trace and JSON inspection

#### Problem

The HTML generator expects an `age_adjusted` object in the JSON, but the v3.0 parser doesn't produce it.

| What Parser Outputs | What HTML Generator Expects |
|---------------------|----------------------------|
| `best_models` (root level) | `age_adjusted.best_models` |
| `worst_models` (root level) | `age_adjusted.worst_models` |
| `age_band_analysis` | *(not used by `_parse_age_adjusted`)* |

#### Code Trace

**Parser** (`parser.py:1557-1558`):
```python
return {
    ...
    "best_models": best_models,      # At root level
    "worst_models": worst_models,    # At root level
    "age_band_analysis": {...}
}
```

**HTML Generator** (`data_classes.py:438`):
```python
self._parse_age_adjusted(data.get('age_adjusted', {}))  # Key doesn't exist!
```

**Result** (`data_classes.py:578-579`):
```python
self.age_adjusted_best = parse_models(age_data.get('best_models', []))   # Always []
self.age_adjusted_worst = parse_models(age_data.get('worst_models', []))  # Always []
```

#### Verified with Real Data

`ford_insights.json` confirmed:
- Line 89321: `"age_band_analysis": {` exists
- No `"age_adjusted"` key anywhere in file

#### Impact

| Location | Function | Effect |
|----------|----------|--------|
| `sections.py:887` | `generate_avoid_section()` | `age_adjusted_lookup` always empty; age-adjusted context annotations (`vs same-age`) never appear |
| `sections.py:390-392` | `generate_durability_section()` | Legacy fallback never triggers (masked by v3.0 path) |
| `data_classes.py:1019` | `get_best_used_proven()` | Always returns `[]` (dead code) |
| `data_classes.py:1029` | `get_worst_age_adjusted()` | Always returns `[]` (dead code) |

#### Why It Doesn't Completely Break

The v3.0 code path in `generate_durability_section()` checks `has_proven_durability_data()` first, which uses `proven_durability_champions` populated from `age_band_analysis`. This path works correctly, masking the broken legacy path.

---

### 2. Age Band Configuration Mismatch

**Severity:** Critical
**Status:** Confirmed

#### Problem

The parser config and HTML generator use different thresholds for "proven" durability.

**Parser Config** (`parser.py:56-60`):
```python
DEFAULT_CONFIG = {
    "proven_min_band": 4,    # Comment says "11+ years" but band 4 = 18-20 years
    "maturing_min_band": 2,  # Band 2-3 = 7-10 years (comment) but actually 11-17 years
    "early_max_band": 1,     # Band 0-1 = 3-10 years
}
```

**Age Band Definitions** (`parser.py:80-87`):
```python
AGE_BAND_ORDER = {
    "3-7 years": 0,
    "8-10 years": 1,
    "11-14 years": 2,  # ← This is band 2
    "15-17 years": 3,
    "18-20 years": 4,  # ← This is band 4 (what config calls "proven")
    "21+ years": 5
}
```

**HTML Generator** (`data_classes.py:751`):
```python
if band_order >= 2:  # 11+ years = proven
```

#### Discrepancy

| Component | "Proven" Threshold | Actual Age Range |
|-----------|-------------------|------------------|
| Parser Config | `band_order >= 4` | 18-20+ years |
| HTML Generator | `band_order >= 2` | 11-14+ years |
| Comments in Parser | "11+ years" | Incorrect |

#### Impact

The legacy parser functions (`get_durability_champions()`, etc.) would use 18+ years as "proven" if the `age_bands` table existed. The HTML generator correctly uses 11+ years, matching the spec's intent but not the parser's config.

---

## Medium Issues

### 3. Legacy Functions Query Non-Existent Database Table

**Severity:** Medium
**Status:** Confirmed

#### Problem

PARSER_SPEC.md (line 160) states:
> No `age_bands` table is required.

However, these functions still query the `age_bands` table:

| Function | Line | Table Queried |
|----------|------|---------------|
| `get_age_adjusted_scores()` | 739 | `age_bands` |
| `get_durability_champions()` | 1095 | `age_bands` |
| `get_models_to_avoid_proven()` | 1162 | `age_bands` |
| `get_early_performers()` | 1229 | `age_bands` |
| `get_model_family_trajectory()` | 1288 | `age_bands` |
| `get_reliability_summary()` | 1374 | `age_bands` |

#### Impact

All functions return empty results (have try/except returning `[]` or empty dict). They are effectively dead code but remain in the codebase.

---

### 4. Hardcoded Reference Year in HTML Generator

**Severity:** Medium
**Status:** Confirmed

#### Problem

`data_classes.py:1007`:
```python
def get_best_nearly_new(self, max_age: int = 5, limit: int = 10):
    min_year = 2023 - max_age + 1  # Hardcoded 2023
```

Parser uses `REFERENCE_YEAR = 2024`.

#### Impact

"Nearly new" range is calculated as 2019+ instead of 2020+, causing off-by-one year in recommendations section.

---

## Minor Issues

### 5. Outdated Programmatic Usage Example in PARSER_SPEC

**Severity:** Low

PARSER_SPEC.md lines 624-629 show:
```python
rating = insights["durability"]["reliability_summary"]["durability_rating"]
champions = insights["durability"]["durability_champions"]["vehicles"]
```

**Reality:** v3.0 output has `age_band_analysis`, not `durability`. This example will cause KeyError.

---

### 6. Incorrect Line Number References in PARSER_SPEC

**Severity:** Low

All function line references in the spec are outdated:

| Function | Spec Says | Actual |
|----------|-----------|--------|
| `get_manufacturer_overview()` | 232 | ~354 |
| `get_competitor_comparison()` | 253 | ~375 |
| `get_all_models()` | 317 | ~439 |

---

### 7. Helper Functions Not at Module Level

**Severity:** Low

HTML_SPEC.md documents `_is_valid_year()` and `_format_year_display()` as reusable Pattern 4 helpers. In implementation, they're defined **inside** `generate_recommendations_section()` only, limiting reuse.

---

## What's Working Correctly

1. **v3.0 Age Band Analysis Parsing:** `_parse_age_band_analysis()` correctly reads from `self.raw.get('age_band_analysis', {})` and constructs `DurabilityVehicle` and `EarlyPerformer` objects.

2. **model_year=0 Handling:** All documented v3.0 fixes for displaying "-" instead of "0" are present and working.

3. **Primary Code Path:** The v3.0 durability section renders correctly because `has_proven_durability_data()` triggers the new code path before the broken legacy path can execute.

4. **Best/Worst Models (BestWorstModel class):** `_parse_best_worst()` correctly reads root-level `best_models`/`worst_models` into `BestWorstModel` objects (different from `AgeAdjustedModel`).

---

## Summary Table

| # | Issue | Severity | Files Affected |
|---|-------|----------|----------------|
| 1 | Missing `age_adjusted` output key | Critical | parser.py, data_classes.py, sections.py |
| 2 | Age band config vs implementation mismatch | Critical | parser.py, data_classes.py |
| 3 | Legacy functions query non-existent table | Medium | parser.py |
| 4 | Hardcoded 2023 reference year | Medium | data_classes.py |
| 5 | Outdated programmatic usage example | Low | PARSER_SPEC.md |
| 6 | Wrong line number references | Low | PARSER_SPEC.md |
| 7 | Helper functions not module-level | Low | sections.py |

---

## Recommendations for Resolution

### Option A: Update HTML Generator to Match Parser v3.0

1. Remove or deprecate `_parse_age_adjusted()` method
2. Remove `age_adjusted_best`, `age_adjusted_worst` properties
3. Update `generate_avoid_section()` to use `proven_models_to_avoid` for age context
4. Update `get_best_nearly_new()` to read `REFERENCE_YEAR` from JSON meta
5. Remove dead code: `get_best_used_proven()`, `get_worst_age_adjusted()`

### Option B: Update Parser to Produce Expected Structure

1. Add `age_adjusted` key to output with `best_models`/`worst_models` inside
2. Fix config comments to match actual band definitions
3. Remove legacy functions or update to use dynamic age band calculation

### Option C: Hybrid Approach (Recommended)

1. Fix critical issues in HTML generator (Option A items 1-4)
2. Clean up parser by removing dead legacy functions
3. Update both spec files to reflect current reality
4. Add integration tests that validate JSON structure against parser expectations

---

## Appendix: Key File Locations

```
scripts/reliabilty-reports/
├── specs/
│   ├── PARSER_SPEC.md          # Parser documentation
│   ├── HTML_SPEC.md            # HTML generator documentation
│   └── AUDIT_REPORT_2026-01-18.md  # This report
├── json_parser/
│   └── parser.py               # JSON generation from database
└── html_generator/
    ├── generator.py            # Main entry point
    └── components/
        ├── data_classes.py     # Data structures and JSON parsing
        ├── sections.py         # HTML section generators
        └── layout.py           # Page layout
```

---

*Report generated by Claude Code audit session*
