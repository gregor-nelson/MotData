# Article Generation Component - PRD Specification

**Version:** 2.1
**Last Updated:** 2026-01-15
**Component Path:** `scripts/article_generation/`

---

## 1. Executive Summary

The Article Generation component transforms raw MOT test data from SQLite into structured JSON insights and styled HTML articles. It uses evidence-tiered methodology to separate proven durability claims from early-stage observations, with year-adjusted scoring to remove age bias from comparisons.

---

## 2. Architecture Overview

```
article_generation/
├── main.py                    # Pipeline orchestrator
├── json_parser/
│   └── parser.py              # Database extraction & insight generation
└── html_generator/
    ├── generator.py           # HTML orchestration
    └── components/
        ├── data_classes.py    # Data structures & JSON parser
        ├── sections.py        # Section HTML generators
        └── layout.py          # Page structure & TOC
```

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   main.py   │ ──▶ │  parser.py  │ ──▶ │    JSON     │ ──▶ │ generator.py│
│ (orchestrate)│     │ (DB queries)│     │   output    │     │ (HTML build)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ mot_insights│
                    │    .db      │
                    └─────────────┘
```

---

## 3. Database Configuration

### Connection Details

| Parameter | Value |
|-----------|-------|
| Database Path | `data/database/mot_insights.db` |
| Connection Mode | Read-only (`?mode=ro`) |
| Database Type | SQLite |

### Tables Queried

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `manufacturer_rankings` | Make-level statistics | `make`, `rank`, `total_tests`, `avg_pass_rate` |
| `vehicle_insights` | Model/year/fuel breakdown | `model`, `model_year`, `fuel_type`, `pass_rate`, `total_tests` |
| `age_bands` | Age-related performance | `band_order`, `pass_rate`, `total_tests` |
| `national_averages` | Benchmark data | `model_year`, `avg_pass_rate` |
| `failure_categories` | MOT failure categories | `category_name`, `total_failures` |
| `top_defects` | Specific defect data | `defect_description`, `occurrence_count` |
| `dangerous_defects` | Safety-critical failures | Dangerous defect details |
| `mileage_bands` | Mileage impact analysis | `mileage_band`, `pass_rate` |

---

## 4. Data Fetching Bounds & Thresholds

### Minimum Test Thresholds

| Threshold | Value | Application |
|-----------|-------|-------------|
| `MIN_TESTS_PROVEN` | 500 | Durability champions (11+ years) |
| `MIN_TESTS_EARLY` | 1,000 | Early performers (3-6 years) |
| `MIN_TESTS_CORE_MODEL` | 500 | Aggregated model inclusion |
| `MIN_TESTS_BREAKDOWN` | 100 | Year/fuel combination inclusion |

### Age Band Classification

| Band Order | Age Range | Maturity Tier |
|------------|-----------|---------------|
| 0 | 3-4 years | Early |
| 1 | 5-6 years | Early |
| 2 | 7-8 years | Maturing |
| 3 | 9-10 years | Maturing |
| 4 | 11-12 years | Proven |
| 5 | 13+ years | Proven |

### Pass Rate Display Thresholds

| Rating | Threshold | CSS Class |
|--------|-----------|-----------|
| Excellent | >= 85.0% | Green |
| Good | >= 70.0% | Light Green |
| Average | >= 60.0% | Yellow |
| Poor | < 60.0% | Red |

### Other Bounds

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `YEARS_TO_AVOID_THRESHOLD` | 55.0% | Flag models below this rate |
| `TOP_MODELS_DISPLAY` | 10 | Maximum models shown in tables |
| `CORE_MODELS_BREAKDOWN` | 5 | Models included in detailed breakdowns |
| `BEST_PROVEN_SCORE_THRESHOLD` | +5.0% vs national | "Standout" durability label |

---

## 5. Insights Generated

### 5.1 Manufacturer Overview

**Source:** `manufacturer_rankings` table

```json
{
  "total_tests": 927815,
  "total_models": 145,
  "avg_pass_rate": 76.5,
  "rank": 5,
  "rank_total": 75,
  "best_model": "ACCORD",
  "best_model_pass_rate": 82.3
}
```

### 5.2 Core Models Aggregation

**Source:** `vehicle_insights` grouped by model

**Calculation:**
```sql
SELECT model,
       SUM(total_tests) as total_tests,
       ROUND(SUM(total_passes)*100.0/SUM(total_tests), 2) as pass_rate
FROM vehicle_insights
WHERE make = ?
GROUP BY model
HAVING SUM(total_tests) >= 500
ORDER BY pass_rate DESC
```

**Output Fields:**
- `core_model`: Model name
- `total_tests`: Aggregated test count
- `pass_rate`: Weighted average pass rate
- `avg_mileage`: Mean odometer reading
- `year_from` / `year_to`: Model year range
- `variant_count`: Number of trim variants
- `variants`: Comma-separated variant list

### 5.3 Model Year Breakdowns

**Source:** `vehicle_insights` for top 5 models by test volume

**Calculation:**
```python
pass_rate_vs_national = vehicle_pass_rate - year_specific_national_avg
```

**Output Fields:**
- `model_year`: Production year
- `fuel_type`: PE/DI/HY/EL/ED/GB/OT
- `total_tests`: Test count for this combination
- `pass_rate`: Actual pass rate
- `pass_rate_vs_national`: Delta from same-year national average
- `national_avg_for_year`: The benchmark used (v2.1 addition)

### 5.4 Best/Worst Models (Year-Adjusted)

**Methodology (v2.1):**
Each model's pass rate is compared against the national average for vehicles of the same model year, not the overall national average.

**Example:**
- 2020 Honda Accord: 89.2% pass rate
- 2020 National Average: 87.1%
- `pass_rate_vs_national`: +2.1%

**Deduplication Rule:**
When a model appears at multiple age bands, keep only the oldest (highest `band_order`) for proven durability assessment.

### 5.5 Durability Analysis

#### 5.5.1 Evidence Tiers

| Tier | Criteria | Evidence Quality |
|------|----------|------------------|
| Proven | `band_order >= 4` (11+ years) | High |
| Maturing | `band_order 2-3` (7-10 years) | Medium |
| Early | `band_order <= 1` (3-6 years) | Low |

#### 5.5.2 Durability Champions

**Selection Criteria:**
1. Age band >= 4 (11+ years old)
2. Total tests >= 500
3. `vs_national_at_age > 0` (above average for age)

**Calculation:**
```python
# Weighted national average for age band
weighted_avg = SUM(pass_rate * total_tests) / SUM(total_tests)
               GROUP BY band_order

vs_national_at_age = vehicle_pass_rate - weighted_avg_for_band
```

#### 5.5.3 Models to Avoid

**Selection Criteria:**
1. Age band >= 4 (11+ years old)
2. Total tests >= 500
3. `vs_national_at_age < 0` (below average for age)

#### 5.5.4 Early Performers (Caveat Required)

**Selection Criteria:**
1. Age band <= 1 (3-6 years old)
2. Total tests >= 1,000 (higher threshold)
3. `vs_national_at_age > 0`

**Mandatory Caveat:**
> "Durability NOT yet proven - these vehicles have not been tested at older ages"

#### 5.5.5 Durability Rating

**Calculation:**
```python
pct_above_avg = (vehicles_above_national / total_proven_vehicles) * 100
avg_vs_national = mean(all proven vehicles' vs_national scores)

if pct_above_avg >= 80 and avg_vs_national >= 5:
    rating = "Excellent"
elif pct_above_avg >= 60 and avg_vs_national >= 2:
    rating = "Good"
elif pct_above_avg >= 40:
    rating = "Average"
else:
    rating = "Below Average"
```

#### 5.5.6 Model Trajectories

**Purpose:** Track how each model ages relative to national benchmarks

**Structure:**
```json
{
  "JAZZ": {
    "trajectory_by_age": {
      "3-4 years": {
        "national_avg": 86.4,
        "model_years": [
          {"year": 2023, "pass_rate": 88.2, "vs_national": +1.8}
        ]
      },
      "13+ years": {
        "national_avg": 60.3,
        "model_years": [
          {"year": 2008, "pass_rate": 65.5, "vs_national": +5.2}
        ]
      }
    },
    "best_proven_year": {"year": 2010, "vs_national": +7.2},
    "has_proven_data": true
  }
}
```

### 5.6 Failure Analysis

**Categories Extracted:**
- Top failure categories (by total failures)
- Top specific defects (by occurrence)
- Top advisories (warnings, not failures)
- Dangerous defects (safety-critical)

### 5.7 Fuel Type Analysis

**Aggregation:**
```sql
GROUP BY fuel_type
```

**Fuel Type Codes:**
| Code | Description |
|------|-------------|
| PE | Petrol |
| DI | Diesel |
| HY | Hybrid |
| EL | Electric |
| ED | Electric Diesel |
| GB | Gas Bi-fuel |
| OT | Other |

---

## 6. Edge Case Handling

### 6.1 Missing Year-Specific National Average

**Scenario:** No national average exists for a specific model year

**Handling:**
```python
FALLBACK_NATIONAL_AVG = 71.51

def get_year_avg_safe(yearly_avgs: dict, year: int) -> tuple:
    if year in yearly_avgs:
        return yearly_avgs[year], False

    # Log warning once per year per session
    if year not in _fallback_warnings_logged:
        logging.warning(f"No national average for year {year}, using fallback")
        _fallback_warnings_logged.add(year)

    return FALLBACK_NATIONAL_AVG, True
```

### 6.2 Null/Empty Query Results

**Handling:**
```python
row = cur.fetchone()
if not row:
    return None  # For single results
    return []    # For list results
```

### 6.3 Insufficient Test Data

**Handling:** Queries enforce minimum thresholds via `HAVING` clause
```sql
HAVING SUM(total_tests) >= 500
```

### 6.4 Age Band Gaps

**Scenario:** Model has data for some age bands but not others

**Handling:** Only include bands with actual data; do not interpolate or fill gaps

### 6.5 Duplicate Model Entries

**Scenario:** Same model/year/fuel appears at multiple age bands

**Handling:** Keep only the oldest instance (highest `band_order`)
```python
seen = {}
for r in results:
    key = (model, model_year, fuel_type)
    if key not in seen or r["age_band_order"] > seen[key]["age_band_order"]:
        seen[key] = r
```

### 6.6 Make Not Found

**Scenario:** Requested manufacturer doesn't exist in database

**Handling:** Exit with error message
```python
if not manufacturer_data:
    sys.exit(f"ERROR: Make '{make}' not found in database")
```

### 6.7 Empty Sections

**Handling:** Skip section generation if no data available
```python
if not insights.fuel_analysis:
    return ""  # Return empty string, section not rendered
```

### 6.8 HTML Safety

**Handling:** All text content escaped before rendering
```python
def safe_html(text: str) -> str:
    return html.escape(str(text)) if text else ""
```

### 6.9 Numeric Display

**Handling:**
- Round to 1 decimal place for percentages
- Format large numbers with thousands separators
- Replace `None` with "N/A" in display

---

## 7. Missing Data Handling Summary

| Data Type | Handling Method |
|-----------|-----------------|
| Missing year average | Use fallback 71.51%, log warning |
| Null query result | Return None or empty list |
| Below threshold tests | Exclude from results |
| Missing age bands | Include only available bands |
| Duplicate entries | Keep oldest (highest band_order) |
| Missing make | Exit with error |
| Empty section data | Skip section rendering |
| Null display values | Show "N/A" |

---

## 8. Output Specifications

### 8.1 JSON Output

**Location:** `data/json/insights/{make}_insights.json`

**Top-Level Structure:**
```json
{
  "meta": {
    "make": "HONDA",
    "generated_at": "ISO timestamp",
    "database": "mot_insights.db",
    "national_pass_rate": 71.51,
    "methodology_version": "2.1"
  },
  "overview": { ... },
  "summary": { ... },
  "core_models": [ ... ],
  "model_year_breakdowns": { ... },
  "best_models": [ ... ],
  "worst_models": [ ... ],
  "failures": {
    "categories": [ ... ],
    "top_failures": [ ... ],
    "top_advisories": [ ... ],
    "dangerous": [ ... ]
  },
  "durability": {
    "methodology": { ... },
    "reliability_summary": { ... },
    "durability_champions": { ... },
    "models_to_avoid": [ ... ],
    "early_performers": [ ... ],
    "model_trajectories": { ... }
  }
}
```

### 8.2 HTML Output

**Location:** `articles/generated/{make}-most-reliable-models.html`

**Sections Generated:**
1. Header & key findings summary
2. Breadcrumb navigation
3. Table of contents (sticky sidebar)
4. Competitor comparison table
5. Best models by pass rate (top 10)
6. Durability champions (proven 11+ years)
7. Early performers (with caveat)
8. Model breakdowns (year-by-year)
9. Fuel type analysis
10. Models to avoid
11. Common failures
12. FAQs (data-generated)
13. Buying recommendations
14. Methodology explanation
15. JSON-LD structured data (Article, FAQ, Breadcrumb, Dataset)

---

## 9. Methodology Versioning

### v2.1 (Current)
- Year-adjusted scoring: Compare against same model year national average
- Weighted age-band averages for durability comparison
- `national_avg_for_year` field added to output

### v2.0
- Evidence-tiered durability system introduced
- Separate proven/maturing/early classifications
- Minimum test thresholds differentiated by tier

### v1.x (Legacy)
- Overall national average (71.51%) used for all comparisons
- No age-band weighting
- No evidence tiers

---

## 10. Performance Characteristics

| Operation | Typical Duration |
|-----------|------------------|
| JSON generation (single make) | 5-10 seconds |
| HTML generation (single JSON) | 1-3 seconds |
| Batch generation (100+ makes) | ~30 minutes |
| Individual DB query | 100-500ms |

### Optimizations Applied
- Global caching for national averages and benchmarks
- Single database connection per execution
- Section skipping for empty data
- Read-only database mode

---

## 11. Usage

### Generate Single Make
```bash
python main.py generate HONDA
```

### Generate Multiple Makes
```bash
python main.py generate HONDA TOYOTA FORD
```

### Generate HTML Only (from existing JSON)
```bash
python html_generator/generator.py data/json/insights/honda_insights.json
```

---

## 12. Error Codes & Logging

| Scenario | Log Level | Action |
|----------|-----------|--------|
| Missing year average | WARNING | Use fallback, continue |
| Make not found | ERROR | Exit |
| Database connection failed | ERROR | Exit |
| Empty query result | DEBUG | Continue with empty data |
| Fallback average used | WARNING | Log once per year |

---

## 13. Validation Rules

1. **Test Count Validation:** All displayed data must meet minimum threshold
2. **Pass Rate Range:** Must be 0-100%
3. **Rank Validation:** Must be within 1 to total_manufacturers
4. **Year Validation:** Must be reasonable (1990-current)
5. **Fuel Code Validation:** Must be in allowed set (PE/DI/HY/EL/ED/GB/OT)

---

## 14. Dependencies

- Python 3.8+
- SQLite3 (standard library)
- No external packages required for core functionality

---

## 15. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `parser.py` | ~760 | Database queries, insight calculations |
| `generator.py` | ~215 | HTML orchestration |
| `data_classes.py` | ~950 | Data structures, JSON parsing |
| `sections.py` | ~1,000 | Section HTML generation |
| `layout.py` | ~450 | Page structure, TOC, head/body |
| `main.py` | ~150 | Pipeline orchestration |

**Total:** ~3,525 lines
