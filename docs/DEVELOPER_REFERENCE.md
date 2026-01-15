# MOT Insights - Developer Reference

> Reference document for LLMs and developers working on this codebase.

## Project Overview

This project analyses UK MOT test data to generate reliability insights for vehicle manufacturers. It processes ~32 million MOT test results to produce per-make JSON insights and HTML articles.

### Key Output
- **JSON insights** per manufacturer (e.g., `honda_insights.json`)
- **HTML articles** for web publication (e.g., `honda-most-reliable-models.html`)

---

## Architecture

```
mot_insights.db                    # SQLite database with pre-processed MOT data
    │
    ▼
scripts/generate_make_insights.py  # Extracts data, calculates scores, outputs JSON
    │
    ▼
{make}_insights.json               # Intermediate JSON with all metrics
    │
    ▼
scripts/generate_article_html.py   # Parses JSON, generates styled HTML articles
    │
    ▼
articles/generated/{make}.html     # Final HTML output
```

---

## Core Concept: Age-Adjusted Reliability Scoring

### The Problem with Raw Pass Rates

Raw MOT pass rates create **age bias**:
- A 2021 car at 95% pass rate looks "more reliable" than a 2010 car at 75%
- But the 2021 car is only 2-3 years old; the 2010 car is 13+ years old
- Comparing them directly is meaningless

### The Solution: Age-Cohort Comparison

Compare each model's pass rate against the **national average for cars of the same age**:

```
vs_national = model_pass_rate - national_average_for_same_age_band
```

Example:
- 2012 Honda Jazz at 80% pass rate
- National average for 9-10 year old cars: 71%
- **Age-adjusted score: +9%** (genuinely durable)

This reveals "true durability" - how well a model ages relative to peers.

### Age Bands

The database uses these age bands:
- `3-4 years` (first MOT eligible)
- `5-6 years`
- `7-8 years`
- `9-10 years`
- `11-12 years`
- `13+ years`

---

## Data Structures

### In `generate_make_insights.py`

#### `get_best_models()` - Raw Rankings
```python
# Sorted by raw pass_rate DESC
# Used for: "Best Single Year" in Key Findings, Nearly New recommendations
# Bias: Favours 2019-2021 models
```

#### `get_age_adjusted_scores()` - Durability Rankings
```python
# Returns:
{
    "model": "JAZZ",
    "model_year": 2012,
    "fuel_type": "HY",
    "total_tests": 5000,
    "avg_vs_national": 17.3,      # Weighted average across age bands
    "durability_trend": 8.2,       # Change in vs_national per age band
    "age_bands": [...]             # Detailed per-band breakdown
}
```

#### `durability_trend` Interpretation
- **Positive**: Model gets relatively better with age (rare, valuable)
- **Zero**: Maintains relative position (good)
- **Negative**: Degrades faster than average (concerning)

### In `generate_article_html.py`

#### `ArticleInsights` Class
Parses JSON into typed dataclasses for template generation:

| Property | Type | Description |
|----------|------|-------------|
| `best_models` | `list[BestWorstModel]` | Raw pass rate rankings |
| `worst_models` | `list[BestWorstModel]` | Raw worst rankings |
| `age_adjusted_best` | `list[AgeAdjustedModel]` | Durability champions |
| `age_adjusted_worst` | `list[AgeAdjustedModel]` | Worst agers |

#### Key Helper Methods
```python
get_best_nearly_new(max_age=5)    # 2019+ models, raw pass rates
get_best_used_proven(limit=10)    # Age-adjusted best performers
get_worst_age_adjusted(limit=5)   # Genuinely problematic models
```

---

## Article Sections & Data Sources

| Section | Data Source | Rationale |
|---------|-------------|-----------|
| Key Findings - Best Single Year | `best_models[0]` (raw) | Recent buyers want current pass rates |
| Key Findings - Durability Champion | `age_adjusted_best[0]` | Highlights proven long-term reliability |
| Best Models by Pass Rate | `core_models` (aggregated) | Overall model comparison |
| Durability Champions | `age_adjusted_best` | Age-adjusted rankings table |
| Recommendations - Nearly New | `get_best_nearly_new()` | Raw rates for recent cars |
| Recommendations - Best Used | `get_best_used_proven()` | Age-adjusted for older cars |
| Models to Avoid | `get_worst_age_adjusted()` | Genuinely problematic, not just old |

---

## Design Decisions

### 1. Why Stratified Recommendations?

Different buyers have different needs:
- Buying nearly new (1-4 years): Raw pass rate is meaningful
- Buying used (5+ years): Age-adjusted score matters more
- Long-term ownership: Durability trend is key

The recommendations section now has two columns reflecting this.

### 2. Minimum Sample Sizes

```python
# In get_age_adjusted_scores():
if data["total_tests"] < 500:  # Skip low-volume models
    continue

# In get_best_models():
WHERE total_tests >= 500
```

This prevents statistical noise from low-volume models.

### 3. Year Cutoffs

```python
# "Nearly new" = last 5 years of data
min_year = 2023 - max_age + 1  # = 2019 for max_age=5
```

Data ends at 2023, so 2019+ covers the most recent complete years.

---

## Database Schema (Key Tables)

### `age_bands`
```sql
make, model, model_year, fuel_type,
age_band,           -- '3-4 years', '5-6 years', etc.
band_order,         -- 1, 2, 3... for sorting
pass_rate,
total_tests,
avg_mileage
```

### `vehicle_insights`
```sql
make, model, model_year, fuel_type,
total_tests, total_passes, total_fails,
pass_rate,
avg_mileage,
avg_age_years,
pass_rate_vs_national  -- Simple comparison, not age-adjusted
```

### `manufacturer_rankings`
```sql
make,
total_tests,
avg_pass_rate,
rank,
best_model, best_model_pass_rate,
worst_model, worst_model_pass_rate
```

---

## Common Pitfalls

### 1. Confusing `pass_rate_vs_national` with Age-Adjusted Score

- `pass_rate_vs_national` in `vehicle_insights`: Simple `pass_rate - 71.51%`
- `avg_vs_national` in age-adjusted: Compares to same-age national average

They are NOT the same. Use age-adjusted for durability analysis.

### 2. Forgetting to Regenerate JSON

The HTML generator reads from JSON files. If you change `generate_make_insights.py`, you must regenerate the JSON:

```bash
python scripts/generate_make_insights.py HONDA
python scripts/generate_article_html.py honda_insights.json
```

### 3. Limited Age Data for Recent Models

2020-2021 models only have data for the 3-4 year age band. They cannot have meaningful durability trends. The code handles this by:
- Requiring 500+ total tests (not per-band)
- Durability trend = 0 if only one age band

### 4. Model Name Variants

The database contains many variants: `JAZZ`, `JAZZ SR`, `JAZZ SR VTEC`, etc.

- `get_all_models()`: Returns all variants separately
- `get_core_models_aggregated()`: Groups by base name
- `get_model_family_year_breakdown()`: Aggregates variants by year

Use the appropriate function for your needs.

---

## Potential Future Improvements

### 1. Confidence Indicators
Flag models with limited age data so readers know the durability score is less certain. Could add a `confidence` field based on:
- Number of age bands with data
- Total test count
- Consistency of vs_national across bands

### 2. Mileage-Adjusted Scoring
Similar to age-adjustment, compare to national average at same mileage band. High-mileage cars that still pass well are interesting.

### 3. Trend Visualisation
The `durability_trend` data could power sparkline charts showing how vs_national changes over age bands.

### 4. Model Family Aggregation for Durability
Currently age-adjusted scores are per model/year/fuel. Could aggregate to model family level for simpler recommendations.

### 5. FAQ Generation Using Age-Adjusted Data
The `generate_faq_data()` function still uses some raw data. Could incorporate durability insights for richer answers.

---

## Testing Commands

```bash
# Generate insights for a make
python scripts/generate_make_insights.py HONDA --pretty

# List all available makes
python scripts/generate_make_insights.py --list

# Generate HTML article
python scripts/generate_article_html.py honda_insights.json --output articles/generated/

# Test parser without generating HTML
python scripts/generate_article_html.py honda_insights.json --test

# Quick comparison of raw vs age-adjusted
python -c "
import json
with open('honda_insights.json') as f:
    data = json.load(f)
print('RAW:', [(m['model'], m['model_year'], m['pass_rate']) for m in data['best_models'][:5]])
print('AGE-ADJ:', [(m['model'], m['model_year'], m['avg_vs_national']) for m in data['age_adjusted']['best_models'][:5]])
"
```

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/generate_make_insights.py` | Data extraction, age-adjusted scoring |
| `scripts/generate_article_html.py` | HTML article generation |
| `mot_insights.db` | Source SQLite database |
| `data/` | Generated JSON insight files |
| `articles/generated/` | Generated HTML articles |
| `articles/js/` | Shared JavaScript for articles |

---

## Contact / History

- **Age-adjusted methodology**: Implemented to solve age bias in recommendations
- **Stratified recommendations**: Added to provide context-appropriate buying advice
- **Last major update**: January 2026 - Full integration of age-adjusted scoring into all article sections
