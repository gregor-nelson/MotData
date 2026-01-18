# MOT Insights Parser Specification

**Version:** 3.0
**Last Updated:** 2026-01-18
**File:** `json_parser/parser.py`

---

## Version 3.0 Changes (2026-01-18)

### Breaking Changes
- Replaced subjective "durability" section with objective "age_band_analysis"
- Removed subjective labels ("durability champions", "models to avoid", ratings)
- Age bands restructured: 3-7, 8-10, 11-14, 15-17, 18-20, 21+ years
- Age bands now calculated dynamically from `vehicle_insights` (no `age_bands` table required)

### New Features
- `REFERENCE_YEAR = 2024` - MOT data source year for age calculations
- `calculate_age_band()` - Derives age band from model_year
- `get_sample_confidence()` - Returns objective confidence level based on sample size
- `get_age_band_performance()` - Make-level pass rates by age band vs national
- `get_model_age_band_breakdown()` - Per-model performance at each age band

### Philosophy Change
- **Objective data presentation** - No subjective labels or ratings
- **User draws conclusions** - Present facts, comparisons, and confidence levels
- **Transparency** - Always show sample sizes and confidence indicators

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Data Sources](#data-sources)
5. [Insights Generated](#insights-generated)
   - [Manufacturer Overview](#1-manufacturer-overview)
   - [Competitor Comparison](#2-competitor-comparison)
   - [Model Analysis](#3-model-analysis)
   - [Age Band Analysis](#4-age-band-analysis-new-in-v30)
   - [Failure Analysis](#5-failure-analysis)
   - [Mileage Impact](#6-mileage-impact)
6. [Output Structure](#output-structure)
7. [Methodology Notes](#methodology-notes)
8. [Usage](#usage)

---

## Overview

The MOT Insights Parser generates comprehensive reliability insights for a specific vehicle make from UK MOT (Ministry of Transport) test data. It processes raw test results and outputs structured JSON for article/report generation.

### Purpose

- Transform raw MOT data into actionable reliability insights
- Compare vehicle makes and models against national benchmarks
- Present objective data with confidence indicators
- Let users draw their own conclusions from the data

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Objectivity** | No subjective labels - present data with comparisons to national averages |
| **Transparency** | Always show sample sizes and confidence levels |
| **Age-adjusted comparisons** | Accounts for natural pass rate decline with age |
| **Statistical thresholds** | Minimum sample sizes prevent unreliable conclusions |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    generate_make_insights()                  │
│                    (Main Entry Point)                        │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Core Data      │  │  Scoring        │  │  Age Band       │
│  Retrieval      │  │  Functions      │  │  Analysis       │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ get_overview()  │  │ get_best_models │  │ get_age_band_   │
│ get_all_models()│  │ get_worst_models│  │   performance() │
│ get_core_models │  │                 │  │ get_model_age_  │
│ get_fuel_type() │  │                 │  │   band_breakdown│
│ get_failures()  │  │                 │  │                 │
│ get_mileage()   │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  SQLite DB      │
                    │  (Read-only)    │
                    │  vehicle_insights│
                    └─────────────────┘
```

---

## Configuration

### Reference Year

```python
REFERENCE_YEAR = 2024  # MOT data source year
```

The MOT data is from UK Gov 2024 release. Vehicle age is calculated as:
```
vehicle_age = REFERENCE_YEAR - model_year
```

### Age Band Definitions (v3.0)

| Band | Age Range | Description | Band Order |
|------|-----------|-------------|------------|
| 3-7 years | 2017-2021 models | New - most pass easily, limited differentiation | 0 |
| 8-10 years | 2014-2016 models | Maturing - issues start emerging | 1 |
| 11-14 years | 2010-2013 models | Established - solid long-term data | 2 |
| 15-17 years | 2007-2009 models | Long-term - smaller samples expected | 3 |
| 18-20 years | 2004-2006 models | Veteran - notable longevity | 4 |
| 21+ years | ≤2003 models | Classic - very small samples, collectors | 5 |

### Sample Confidence Thresholds

| Confidence | Min Tests | Note |
|------------|-----------|------|
| `high` | 1,000+ | Statistically robust |
| `medium` | 200-999 | Reasonable confidence |
| `low` | 50-199 | Interpret with caution |
| `insufficient` | <50 | Excluded from analysis |

### Statistical Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_TESTS_DEFAULT` | 50 | Minimum tests for inclusion in analyses |

---

## Data Sources

### Database Tables Used

| Table | Purpose |
|-------|---------|
| `manufacturer_rankings` | Make-level statistics and rankings |
| `vehicle_insights` | Per-model/year/fuel statistics (primary source) |
| `national_averages` | Benchmark rates by year and overall |
| `mileage_bands` | Pass rates segmented by mileage |
| `failure_categories` | Aggregated failure types |
| `top_defects` | Common failure/advisory items |
| `dangerous_defects` | Safety-critical defects |

**Note:** Age bands are now calculated dynamically from `vehicle_insights` using `model_year` and `REFERENCE_YEAR`. No `age_bands` table is required.

### Caching

The parser uses module-level caching for frequently accessed data:

| Cache Variable | Description |
|----------------|-------------|
| `_national_age_benchmarks` | National averages by age band (calculated from vehicle_insights) |
| `_yearly_national_averages` | National averages by model year |
| `_weighted_age_band_averages` | Weighted national averages by age band |

---

## Insights Generated

### 1. Manufacturer Overview

**Function:** `get_manufacturer_overview()` (line 232)

Returns brand-level statistics from `manufacturer_rankings`:

| Field | Description |
|-------|-------------|
| `total_tests` | Total MOT tests across all models |
| `avg_pass_rate` | Overall pass rate for the make |
| `rank` | Ranking among all manufacturers |
| `total_models` | Number of model variants |
| `best_model` | Highest performing model |
| `worst_model` | Lowest performing model |

---

### 2. Competitor Comparison

**Function:** `get_competitor_comparison()` (line 253)

Compares the make against relevant competitors by market segment:

| Segment | Example Makes |
|---------|---------------|
| Japanese Mainstream | Toyota, Honda, Mazda, Nissan, Suzuki |
| Korean | Hyundai, Kia |
| European Mainstream | Ford, Vauxhall, VW, Peugeot, Renault |
| German Premium | BMW, Mercedes, Audi |
| British Premium | Jaguar, Land Rover, Volvo |
| Luxury | Lexus, Porsche |

**Output:** Pass rates, total tests, and rankings for comparison group.

---

### 3. Model Analysis

#### 3.1 All Models
**Function:** `get_all_models()` (line 317)

Complete list of all model/year/fuel variants with:
- Total tests, passes, fails
- Pass rate
- Average mileage
- Performance vs national average

#### 3.2 Core Models Aggregated
**Function:** `get_core_models_aggregated()` (line 357)

Aggregates variants under base model names:

```
Example: "CIVIC SR VTEC", "CIVIC TYPE R", "CIVIC SE" → "CIVIC"
```

**Output Fields:**
- Combined test counts
- Year range (year_from, year_to)
- Variant count
- Overall pass rate

#### 3.3 Model Year Breakdown
**Function:** `get_model_family_year_breakdown()` (line 416)

Year-by-year performance for a model family using **year-specific** national averages.

**Key Feature:** Removes new-car bias by comparing 2020 models to 2020 averages.

**Output Fields:**
- `pass_rate` - Raw pass rate
- `pass_rate_vs_national` - Difference from same-year average
- `national_avg_for_year` - The benchmark used

#### 3.4 Fuel Type Breakdown
**Function:** `get_fuel_type_breakdown()` (line 449)

Pass rates segmented by fuel type:

| Code | Fuel Type |
|------|-----------|
| PE | Petrol |
| DI | Diesel |
| HY | Hybrid Electric |
| EL | Electric |
| ED | Plug-in Hybrid |
| GB | Gas Bi-fuel |
| OT | Other |

---

### 4. Year-Adjusted Scoring

**Functions:** `get_best_models()` (line 482), `get_worst_models()` (line 516)

#### How It Works

Compares each model's pass rate against the **national average for that model year**.

```
Year-Adjusted Score = Model Pass Rate - National Average for Same Year
```

#### Why This Matters

Raw pass rates favor newer vehicles because all vehicles pass MOT more often when new. Year-adjusted scoring eliminates this bias:

| Model | Raw Pass Rate | Year | National Avg for Year | Adjusted Score |
|-------|---------------|------|----------------------|----------------|
| 2022 Civic | 95% | 2022 | 92% | +3% |
| 2012 Civic | 78% | 2012 | 71% | +7% |

The 2012 Civic is actually performing better relative to peers despite lower raw pass rate.

#### Output Fields

- `pass_rate` - Raw pass rate
- `pass_rate_vs_national` - Difference from same-year national average
- `national_avg_for_year` - The benchmark used

#### Ranking

- **Best models**: Sorted by `pass_rate_vs_national` descending
- **Worst models**: Sorted by `pass_rate_vs_national` ascending

---

### 4. Age Band Analysis (NEW in v3.0)

**This is the primary methodology for understanding vehicle reliability by age.**

Presents objective data on pass rates at different vehicle ages, compared to national averages. No subjective labels - users draw their own conclusions.

#### 4.1 Make-Level Age Band Performance
**Function:** `get_age_band_performance()`

Returns the make's overall pass rate at each age band compared to national average.

**Output Fields:**
| Field | Description |
|-------|-------------|
| `make_pass_rate` | Make's pass rate at this age band |
| `national_pass_rate` | National average for this age band |
| `vs_national` | Difference (positive = above average) |
| `total_tests` | Sample size |
| `confidence` | "high", "medium", "low", or "insufficient" |
| `sample_note` | Caveat text if confidence is low |

**Example Output:**
```json
{
  "8-10 years": {
    "band_order": 1,
    "make_pass_rate": 72.61,
    "national_pass_rate": 75.42,
    "vs_national": -2.81,
    "total_tests": 1086941,
    "confidence": "high",
    "sample_note": null
  }
}
```

#### 4.2 Per-Model Age Band Breakdown
**Function:** `get_model_age_band_breakdown()`

Returns each model's performance at each age band, allowing users to compare specific models.

**Output Structure:**
```json
{
  "core_model": "FIESTA",
  "total_tests": 1440948,
  "confidence": "high",
  "age_bands_available": 6,
  "age_bands": [
    {
      "age_band": "8-10 years",
      "band_order": 1,
      "pass_rate": 68.99,
      "national_pass_rate": 75.42,
      "vs_national": -6.43,
      "total_tests": 325000,
      "confidence": "high",
      "sample_note": null
    }
  ]
}
```

#### 4.3 How Age Bands Are Calculated

Age bands are derived dynamically from `model_year` in `vehicle_insights`:

```python
vehicle_age = REFERENCE_YEAR - model_year  # REFERENCE_YEAR = 2024
```

| Age | Band Assigned |
|-----|---------------|
| 3-7 | "3-7 years" (band_order 0) |
| 8-10 | "8-10 years" (band_order 1) |
| 11-14 | "11-14 years" (band_order 2) |
| 15-17 | "15-17 years" (band_order 3) |
| 18-20 | "18-20 years" (band_order 4) |
| 21+ | "21+ years" (band_order 5) |

#### 4.4 Understanding the Data

**Key Points for Users:**
- **3-7 years**: Most vehicles pass easily at this age - limited differentiation
- **8-10 years**: Issues start emerging - this is where meaningful comparisons begin
- **11-14 years**: Solid long-term data - most relevant for durability assessment
- **15-17 years**: Smaller sample sizes expected - interpret with care
- **18-20+ years**: Very small samples, often collector/enthusiast vehicles

**Confidence Levels:**
| Level | Tests | Interpretation |
|-------|-------|----------------|
| high | 1,000+ | Statistically robust |
| medium | 200-999 | Reasonable confidence |
| low | 50-199 | Interpret with caution |
| insufficient | <50 | Excluded from output |

---

### 5. Failure Analysis

#### 5.1 Failure Categories
**Function:** `get_failure_categories()` (line 550)

Aggregated failure types:

| Output Field | Description |
|--------------|-------------|
| `category_name` | Category (e.g., "Brakes", "Lights") |
| `total_failures` | Total failure count |
| `vehicle_count` | Number of affected vehicles |

#### 5.2 Top Defects
**Function:** `get_top_defects()`

Most common failures or advisories:

| Parameter | Values |
|-----------|--------|
| `defect_type` | "failure" or "advisory" |

**Output Fields:**
- `defect_description` - Specific defect text
- `category_name` - Parent category
- `total_occurrences` - Count

#### 5.3 Dangerous Defects
**Function:** `get_dangerous_defects()`

Safety-critical defects only (brake failures, steering issues, structural problems).

---

### 6. Mileage Impact

**Function:** `get_mileage_impact()`

Pass rate breakdown by mileage band:

| Field | Description |
|-------|-------------|
| `mileage_band` | Range (e.g., "0-30k", "30-60k") |
| `band_order` | Ordering integer |
| `total_tests` | Tests in this band |
| `avg_pass_rate` | Weighted pass rate |

**Use Case:** Shows degradation curve with usage; helps identify high-mileage reliability.

---

## Output Structure

The main function `generate_make_insights()` returns:

```json
{
  "meta": {
    "make": "FORD",
    "generated_at": "2026-01-18T...",
    "database": "mot_insights.db",
    "methodology_version": "3.0",
    "data_source_year": 2024,
    "national_pass_rate": 71.45,
    "methodology_note": "Objective age band analysis..."
  },
  "overview": { /* manufacturer_rankings data */ },
  "competitors": [ /* competitor comparison */ ],
  "summary": {
    "total_tests": 4473074,
    "total_models": 5583,
    "avg_pass_rate": 68.48,
    "rank": 5782,
    "rank_total": 75,
    "best_model": "FREIDA 1995",
    "best_model_pass_rate": 100.0,
    "worst_model": "TRANIST 2012",
    "worst_model_pass_rate": null,
    "vs_national": -2.97,
    "vs_national_note": "..."
  },
  "core_models": [ /* aggregated models */ ],
  "model_year_breakdowns": {
    "FIESTA": [ /* year data */ ],
    "FOCUS": [ /* year data */ ]
  },
  "fuel_analysis": [ /* fuel type breakdown */ ],
  "best_models": [ /* year-adjusted best */ ],
  "worst_models": [ /* year-adjusted worst */ ],
  "failures": {
    "categories": [ /* failure categories */ ],
    "top_failures": [ /* common failures */ ],
    "top_advisories": [ /* common advisories */ ],
    "dangerous": [ /* safety defects */ ]
  },
  "mileage_impact": [ /* mileage bands */ ],
  "all_models": [ /* complete model list */ ],
  "age_band_analysis": {
    "description": "Pass rates by vehicle age compared to national averages...",
    "confidence_levels": {
      "high": "1,000+ tests - statistically robust",
      "medium": "200-999 tests - reasonable confidence",
      "low": "50-199 tests - interpret with caution"
    },
    "age_bands": {
      "3-7 years": "New vehicles - most pass easily",
      "8-10 years": "Maturing - issues start emerging",
      "11-14 years": "Established - solid long-term data",
      "15-17 years": "Long-term - smaller samples expected",
      "18-20 years": "Veteran - notable longevity",
      "21+ years": "Classic - very small samples"
    },
    "make_performance": {
      "methodology": "...",
      "reference_year": 2024,
      "national_benchmarks": { /* national averages per band */ },
      "make_performance": {
        "8-10 years": {
          "make_pass_rate": 72.61,
          "national_pass_rate": 75.42,
          "vs_national": -2.81,
          "total_tests": 1086941,
          "confidence": "high"
        }
      }
    },
    "model_breakdown": [
      {
        "core_model": "FIESTA",
        "total_tests": 1440948,
        "confidence": "high",
        "age_bands": [ /* per-band data */ ]
      }
    ]
  }
}
```

---

## Methodology Notes

### Why Age-Band Comparisons?

**Problem:** Raw pass rates favor newer vehicles because all vehicles pass MOT more often when new. A 95% pass rate for a 3-year-old car and 65% for a 15-year-old car don't mean the newer car is "more reliable" - it's just newer.

**Solution:** Compare each vehicle to the national average for vehicles of the **same age**.

**Example:**
| Vehicle Age | Pass Rate | National Avg | vs National |
|-------------|-----------|--------------|-------------|
| 8-10 years | 72.6% | 75.4% | -2.8% (below avg) |
| 15-17 years | 55.7% | 57.9% | -2.2% (below avg) |

Both age bands show below-average performance, revealing a consistent pattern.

### Why No Subjective Labels?

**v3.0 Philosophy:** Present objective data and let users draw conclusions.

| Old Approach (v2.x) | New Approach (v3.0) |
|---------------------|---------------------|
| "Durability Champion" | `vs_national: +5.2` with confidence level |
| "Model to Avoid" | `vs_national: -8.1` with confidence level |
| "Rating: Excellent" | Raw data + context for interpretation |

### Understanding Confidence Levels

| Level | Tests | What It Means |
|-------|-------|---------------|
| `high` | 1,000+ | Large sample, statistically robust |
| `medium` | 200-999 | Reasonable sample, interpret normally |
| `low` | 50-199 | Small sample, results may vary |
| `insufficient` | <50 | Too small, excluded from analysis |

### Data Caveats by Age Band

| Age Band | Sample Size | Notes |
|----------|-------------|-------|
| 3-7 years | Usually high | Most vehicles pass - limited differentiation |
| 8-10 years | High | Meaningful comparisons start here |
| 11-14 years | High | Best data for durability assessment |
| 15-17 years | Medium | Fewer vehicles, but solid data |
| 18-20 years | Lower | Smaller samples, interpret carefully |
| 21+ years | Very low | Often collector cars with different use patterns |

---

## Usage

### Command Line

```bash
# Generate insights for a make
python parser.py HONDA

# Custom output path
python parser.py TOYOTA --output ./data/toyota.json

# List all available makes
python parser.py --list

# Show top 20 makes by test count
python parser.py --list --top 20

# Pretty-print JSON output
python parser.py HONDA --pretty
```

### Programmatic

```python
from parser import generate_make_insights, list_available_makes

# List all makes
makes = list_available_makes()
print(f"Found {len(makes)} makes")

# Generate insights
insights = generate_make_insights("HONDA")

# Check for errors
if "error" in insights:
    print(f"Error: {insights['error']}")
else:
    # Access specific data
    rating = insights["durability"]["reliability_summary"]["durability_rating"]
    champions = insights["durability"]["durability_champions"]["vehicles"]

    print(f"Durability Rating: {rating}")
    print(f"Found {len(champions)} durability champions")
```

### Custom Configuration

Currently, configuration changes require modifying `DEFAULT_CONFIG` directly:

```python
from parser import DEFAULT_CONFIG

# Require more tests for reliability
DEFAULT_CONFIG["min_tests"] = 100

# Require 13+ years for "proven" status
DEFAULT_CONFIG["proven_min_band"] = 5
```

---

## Dependencies

- Python 3.8+
- SQLite3 (standard library)
- Database: `data/source/database/mot_insights.db`

---

## Related Files

| File | Purpose |
|------|---------|
| `html_generator/` | Converts JSON insights to HTML articles |
| `main.py` | Batch processing entry point |
| `docs/` | Additional documentation |
