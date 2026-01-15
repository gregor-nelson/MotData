# Article Generation Pipeline - Changes Summary
**Date:** 2026-01-15

## Overview
Audit and improvement of the `scripts/article_generation` pipeline to ensure production-quality error handling and proper code alignment for a premium web app.

---

## Changes Made

### 1. Fixed Missing Imports in sections.py
**File:** `html_generator/components/sections.py`

Added missing type imports that were being used but not imported:
- `DurabilityVehicle` - Used in durability and recommendations sections
- `EarlyPerformer` - Used in early performers section

**Before:**
```python
from .data_classes import (
    ArticleInsights,
    format_number,
    ...
)
```

**After:**
```python
from .data_classes import (
    ArticleInsights,
    DurabilityVehicle,
    EarlyPerformer,
    format_number,
    ...
)
```

---

### 2. Added Logging Infrastructure to main.py
**File:** `main.py`

Added comprehensive logging system:
- New `logs/` directory for log file storage
- Timestamped log files: `article_gen_YYYYMMDD_HHMMSS.log`
- DEBUG level logging to file with detailed format
- Captures timing, subprocess output, and error tracebacks

**New imports added:**
- `logging`
- `time`
- `traceback`
- `datetime`

---

### 3. Improved Database Error Handling
**Function:** `get_available_makes()`

- Added try/except for `sqlite3.Error` and general exceptions
- Proper connection cleanup with `finally` block
- Errors logged with full traceback (`exc_info=True`)
- Graceful exit with user-friendly messages

---

### 4. Enhanced JSON Generation
**Function:** `generate_json()`

Improvements:
- Added 5-minute subprocess timeout
- Captures both stdout AND stderr (previously only stderr)
- Per-call timing logged
- Timeout exception handling
- Debug logging of subprocess output

---

### 5. Enhanced HTML Generation
**Function:** `generate_html()`

Improvements:
- Added 2-minute subprocess timeout
- Captures both stdout AND stderr
- Per-call timing logged
- Timeout exception handling
- Debug logging of subprocess output

---

### 6. Added Error Handling to Explore
**Function:** `run_explore()`

- Added script existence check
- Added `CalledProcessError` handling
- Logging of success/failure

---

### 7. Improved Batch Processing
**Function:** `generate_all_articles()`

Major improvements:
- **Detailed failure tracking:** Separate categories for JSON failures, HTML failures, and exceptions
- **Per-make timing:** Each make shows processing time
- **Full tracebacks:** Exceptions logged to file with complete stack traces
- **Summary breakdown:** Shows failure counts by category
- **Log file reference:** Prints log file path for debugging

**New results structure:**
```python
results = {
    "success": [],
    "failed_json": [],
    "failed_html": [],
    "failed_error": []
}
```

---

## Files Modified

| File | Changes |
|------|---------|
| `html_generator/components/sections.py` | Added 2 imports |
| `main.py` | Added logging, improved error handling in 6 functions |

---

## New Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/article_generation/logs/` | Stores timestamped log files |

---

## Testing Performed

1. **Import test** - Verified sections.py imports work
2. **Module import test** - Verified main.py loads and logging initializes
3. **List command** - Verified database connection and error handling
4. **Dry run** - Verified batch filtering works
5. **Single generation** - Generated HONDA article successfully
6. **Log verification** - Confirmed log file contains expected entries

---

## Usage Notes

### Log Files
Log files are created in `scripts/article_generation/logs/` with names like:
```
article_gen_20260115_110200.log
```

Each log entry includes:
- Timestamp
- Log level (INFO, DEBUG, WARNING, ERROR)
- Function name
- Message

### Batch Processing Output
After batch processing, the summary now shows:
```
Success: X
Failed:  Y
  - JSON failures: N
  - HTML failures: M
  - Exceptions:    Z
Time:    Xs total, Ys avg per make

Log file: scripts/article_generation/logs/article_gen_YYYYMMDD_HHMMSS.log
```

---

## Rollback Instructions

If issues arise, revert these two files:
1. `html_generator/components/sections.py` - Remove `DurabilityVehicle`, `EarlyPerformer` from imports
2. `main.py` - Restore from git

Delete `logs/` directory if needed.

---

## Audit Fixes (2026-01-15 - Session 2)

Following an independent audit ([AUDIT_REPORT_2026-01-15.md](AUDIT_REPORT_2026-01-15.md)), the following data accuracy issues were addressed:

### 8. Added Fallback Warning for Missing Year Averages (CRITICAL)
**File:** `json_parser/parser.py`

**Problem:** When a model year was missing from the `national_averages` table, the code silently used 71.51% as fallback, potentially producing incorrect "vs national" comparisons.

**Fix:**
- Added `logging` import and configured basic logging
- Added `FALLBACK_NATIONAL_AVG` constant (71.51) to centralize the fallback value
- Added `get_year_avg_safe()` helper function that:
  - Returns the year average if available
  - Logs a warning on first use of fallback for each year
  - Returns `(average, used_fallback)` tuple for transparency
- Replaced all 3 instances of `yearly_avgs.get(data["model_year"], 71.51)` with the new helper

**Lines changed:** 16-23 (imports), 131-153 (new function), 397, 457, 487 (usage)

---

### 9. Deduplicated Durability Champion Entries (HIGH)
**File:** `json_parser/parser.py`

**Problem:** A model/year/fuel combination could appear multiple times in durability tables if it had data at both "11-12 years" AND "13+ years" age bands (e.g., Jazz 2010 Petrol appeared twice).

**Fix:** Added deduplication logic to keep only the oldest age band (highest `band_order`) for each model/year/fuel combination. This shows the most proven durability evidence.

**Functions updated:**
- `get_durability_champions()` - lines 754-761
- `get_models_to_avoid_proven()` - lines 815-821

---

### 10. Aligned Recommendation Thresholds (HIGH)
**File:** `html_generator/components/sections.py`

**Problem:** The "Best Nearly New" recommendations required ≥88% pass rate, while the CSS "excellent" class threshold was 85%. A model with 87% would get green highlighting in tables but not appear in recommendations.

**Fix:** Changed recommendation threshold from `>= 88` to `>= 85` to align with `PASS_RATE_THRESHOLDS['excellent']`.

**Line changed:** 919

---

### 11. Added Baseline Comparison Footnote (HIGH)
**File:** `html_generator/components/sections.py`

**Problem:** The "Best Models" section compares against overall national average (71.5%), while year breakdown sections use year-adjusted averages. Both are valid but could confuse readers.

**Fix:** Added explanatory footnote below the Best Models table:
> "* Compared to overall {national}% national average across all years. For year-adjusted comparisons that account for newer cars passing more often, see individual model breakdowns below."

**Line changed:** 258

---

### 12. Made TOC Dynamic Based on Available Content (HIGH)
**Files:** `html_generator/components/data_classes.py`, `html_generator/components/layout.py`

**Problem:** The Table of Contents was static - it always showed "Proven Durability Champions" even for makes like Tesla, Polestar, and Dacia that have no 11+ year vehicles. This resulted in broken anchor links.

**Fix:**
1. Added `get_available_sections()` method to `ArticleInsights` class that returns section IDs with content
2. Updated `generate_toc_html()` to:
   - Skip sections without content
   - Renumber TOC entries correctly
   - Update section count to reflect actual displayed sections

**Lines changed:**
- `data_classes.py`: 756-779 (new method)
- `layout.py`: 248-283 (updated TOC generation)

---

## Files Modified (Session 2)

| File | Changes |
|------|---------|
| `json_parser/parser.py` | Added logging, fallback warning helper, deduplication logic |
| `html_generator/components/sections.py` | Aligned threshold (85%), added footnote |
| `html_generator/components/data_classes.py` | Added `get_available_sections()` method |
| `html_generator/components/layout.py` | Dynamic TOC generation |

---

## Verification

The critical issue (silent fallback) was verified as **not currently active** - the database has complete national averages for all years 2000-2023, matching the vehicle data range. The warning will catch any future data mismatches when new years are added.
