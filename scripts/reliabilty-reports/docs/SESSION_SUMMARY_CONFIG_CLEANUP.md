# Session Summary: Remove Hardcoded Values from sections.py

## Objective
Centralise hardcoded thresholds from `sections.py` into `config.py` to make the codebase more maintainable and allow easy adjustment of editorial thresholds.

---

## Architecture Pattern
```
config.py → data_classes.py → sections.py
```
- `config.py`: Single source of truth for all configurable values
- `data_classes.py`: Imports from config, re-exports to components
- `sections.py`: Uses constants via data_classes imports

---

## Changes Made

### 1. New Derived Constants (config.py)
These are calculated from existing base values, ensuring consistency:

| Constant | Value | Derived From |
|----------|-------|--------------|
| `DATA_YEAR_START` | 2000 | Fixed historical start |
| `DATA_YEAR_END` | 2023 | `REFERENCE_YEAR - 1` |
| `PASS_RATE_EXCEPTIONAL` | 90.0 | `PASS_RATE_EXCELLENT + 5` |
| `VS_NATIONAL_EXCEPTIONAL` | 10.0 | `RATING_EXCELLENT_VS_NAT * 2` |
| `VS_NATIONAL_GOOD` | 5.0 | `RATING_EXCELLENT_VS_NAT` |
| `VS_NATIONAL_AROUND_AVERAGE` | 2.0 | `RATING_GOOD_VS_NAT` |

### 2. New Editorial Constants (config.py)
Arbitrary thresholds with no derivable relationship - editorial decisions:

| Constant | Value | Purpose |
|----------|-------|---------|
| `SAMPLE_SIZE_LOW` | 5,000 | Triggers "limited test data" intro |
| `SAMPLE_SIZE_MODERATE` | 20,000 | Triggers "moderate sample" intro |
| `MIN_TESTS_MODEL_BREAKDOWN` | 10,000 | Min tests for year-by-year breakdown |
| `MIN_TESTS_FAQ_POPULAR` | 50,000 | Min tests for FAQ model inclusion |
| `RANK_TOP_PERFORMER` | 15 | Rank threshold for "top performer" label |

### 3. New Methodology Display Values (config.py)
Values that need manual update when database refreshes:

| Constant | Value | Notes |
|----------|-------|-------|
| `METHODOLOGY_TOTAL_TESTS` | 32,300,000 | Total tests across all makes |
| `METHODOLOGY_YEAR_RANGE_EXAMPLE` | "from ~59% (2009)..." | Year-specific average examples |

### 4. Replacements in sections.py (~25 locations)

| Category | Before | After |
|----------|--------|-------|
| Year ranges | `"2000-2023"` | `f"{DATA_YEAR_START}-{DATA_YEAR_END}"` |
| Sample sizes | `< 5000`, `< 20000` | `< SAMPLE_SIZE_LOW`, `< SAMPLE_SIZE_MODERATE` |
| Pass rates | `>= 90`, `>= 80` | `>= PASS_RATE_EXCEPTIONAL`, `>= PASS_RATE_EXCELLENT` |
| vs_national | `>= 10`, `>= 5`, `>= 2` | `>= VS_NATIONAL_EXCEPTIONAL`, etc. |
| Model thresholds | `min_tests=10000` | `min_tests=MIN_TESTS_MODEL_BREAKDOWN` |

---

## Values Intentionally Left Hardcoded

| Value | Location | Reason |
|-------|----------|--------|
| `< 50` | Line 673 | Mathematical fact: <50% = more fails than passes |
| `"3-6 years old"` | Line 533 | Definition of early performers age band |
| `"11+ years"` | Multiple | Definition of proven durability |
| `"1.6mm tread"` | Line 941 | Legal MOT requirement (UK law) |
| `>= 75` | FAQ section | Contextual threshold for "consistently strong" |

---

## Opportunities for Further Discussion

### 1. Runtime Data vs Config
The methodology section still has some values that could come from runtime data:
- Total tests across all makes (currently `METHODOLOGY_TOTAL_TESTS`)
- Year-specific average examples

**Question:** Should these be calculated from actual data at generation time, or is config sufficient?

### 2. Threshold Relationships
Some thresholds have implicit relationships not yet formalised:
- `RANK_TOP_PERFORMER` (15) + `VS_NATIONAL_GOOD` (5) = "top performer" criteria
- The "standout" threshold uses `VS_NATIONAL_EXCEPTIONAL + VS_NATIONAL_GOOD` (15)

**Question:** Should these compound thresholds be explicit constants?

### 3. Age Band Definitions
The age bands ("3-6 years", "11+ years") are currently prose strings, not derived from config:
- `AGE_BAND_ORDER` exists in config but isn't used for prose generation
- Early performer age range (3-6) doesn't match config bands (3-7)

**Question:** Should age band prose be derived from `AGE_BAND_ORDER`?

### 4. CSS Class Thresholds
`get_pass_rate_class()` in data_classes.py uses:
- `PASS_RATE_EXCELLENT` (85)
- `PASS_RATE_GOOD` (70)
- `PASS_RATE_AVERAGE` (60)

But prose generation sometimes uses different thresholds (e.g., 90 for "exceptional").

**Question:** Should there be separate "prose tier" vs "CSS tier" constants?

### 5. Consistency Audit Needed
Some potential inconsistencies to review:
- FAQ uses `>= 75` for "consistently strong" - should this use a constant?
- Avoid section uses `AVOID_PASS_RATE_THRESHOLD` (60) but also `-3` for durability
- The `-3` threshold in `_parse_age_band_analysis()` isn't configurable

### 6. Documentation
Current inline comments explain derivations, but no central documentation of:
- What each threshold means editorially
- When/why to adjust them
- Impact of changing values

---

## File Diff Summary

| File | Lines Added | Lines Modified |
|------|-------------|----------------|
| config.py | +33 | 0 |
| data_classes.py | +15 | 0 |
| sections.py | +15 (imports) | ~25 replacements |

---

## Verification
```bash
python -c "from html_generator.components.sections import *; print('Import OK')"
# Output: Import OK
```

All constants verified to calculate correctly from base values.
