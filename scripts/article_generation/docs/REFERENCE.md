# Article Generation Pipeline Reference

> Comprehensive developer reference for the MOT article generation system.
> This document provides everything a new developer or Claude session needs to understand, modify, and extend the article generation pipeline.

---

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Script Reference](#script-reference)
6. [Database Schema](#database-schema)
7. [JSON Output Structure](#json-output-structure)
8. [HTML Generation](#html-generation)
9. [Data Flow](#data-flow)
10. [Common Patterns](#common-patterns)
11. [Extending the Pipeline](#extending-the-pipeline)

---

## Overview

### Purpose

This pipeline generates data-driven vehicle reliability articles from UK MOT (Ministry of Transport) test data. The articles are designed for a premium vehicle report application (Motorwise) and include:

- Per-manufacturer reliability rankings
- Model-by-model pass rate analysis
- Evidence-tiered durability scoring
- SEO-optimized HTML with JSON-LD structured data

### Key Features

| Feature | Description |
|---------|-------------|
| **Evidence-Tiered Durability** | Only vehicles with 11+ years of data receive "proven durability" claims |
| **Age-Adjusted Scoring** | Compares vehicles against national averages for their age band |
| **Competitor Analysis** | Automatic comparison with segment competitors |
| **SEO-Ready HTML** | Complete with JSON-LD, Open Graph, and FAQ schema |
| **Batch Processing** | Generate articles for multiple makes in one run |

### Data Source

- **Source**: DVSA (Driver and Vehicle Standards Agency) MOT test results
- **Coverage**: 2000-2023 model years
- **Volume**: 32+ million MOT tests across 75 manufacturers
- **Database**: SQLite (`data/database/mot_insights.db`)

---

## Folder Structure

```
scripts/article_generation/
├── __init__.py                        # Package marker
├── main.py                            # Unified CLI entry point
├── explore_article_opportunities.py   # Data exploration tool
├── REFERENCE.md                       # This document
│
├── json_parser/                       # JSON insights generation
│   ├── __init__.py
│   └── parser.py                      # Core JSON generator (queries DB)
│
├── html_generator/                    # HTML article generation
│   ├── __init__.py
│   ├── generator.py                   # Main orchestrator
│   └── components/                    # Modular HTML components
│       ├── __init__.py                # Component exports
│       ├── data_classes.py            # Dataclasses, constants, utilities
│       ├── sections.py                # Individual section generators
│       └── layout.py                  # Page structure, JSON-LD, TOC
│
└── archive/                           # Archived/deprecated scripts
    └── generate_all_priority_makes.py # Legacy batch script (use main.py generate-all)
```

### Related Directories

```
project_root/
├── data/
│   ├── database/
│   │   └── mot_insights.db            # Source database (read-only)
│   └── generated/
│       └── {make}_insights.json       # Generated JSON files
├── articles/
│   └── generated/
│       └── {make}-most-reliable-models.html  # Generated HTML articles
```

---

## Quick Start

### Generate a Single Article

```bash
# Interactive mode (prompts for make selection)
python scripts/article_generation/main.py

# Direct generation
python scripts/article_generation/main.py generate HONDA

# List available makes
python scripts/article_generation/main.py list --top 20

# Explore article opportunities
python scripts/article_generation/main.py explore
```

### Generate Batch Articles

```bash
# Generate all makes (cleans output folders first)
python scripts/article_generation/main.py generate-all

# Only generate makes with 100k+ tests
python scripts/article_generation/main.py generate-all --min-tests 100000

# Preview what would be generated (no files created)
python scripts/article_generation/main.py generate-all --dry-run

# Keep existing files (skip folder cleanup)
python scripts/article_generation/main.py generate-all --no-clean
```

### Direct Script Usage

```bash
# Generate JSON only
python scripts/article_generation/json_parser/parser.py TOYOTA --output data/generated/toyota_insights.json --pretty

# Generate HTML from existing JSON
python scripts/article_generation/html_generator/generator.py data/generated/toyota_insights.json --output articles/generated/

# Test parser output without generating HTML
python scripts/article_generation/html_generator/generator.py data/generated/toyota_insights.json --test
```

---

## Core Concepts

### 1. Evidence-Tiered Durability Methodology (v2.1)

The pipeline uses a rigorous approach to durability claims based on data maturity:

| Tier | Age Band | Evidence Quality | Usage |
|------|----------|------------------|-------|
| **Proven** | 11+ years | High | Can claim "durability champion" |
| **Maturing** | 7-10 years | Medium | Emerging patterns, needs caveat |
| **Early** | 3-6 years | Limited | Strong early results, durability unproven |

**Key Principle**: Only vehicles with 11+ years of MOT data can be labeled as "durability champions" or "models to avoid" with high confidence.

### 2. Year-Adjusted Scoring (v2.1)

Raw pass rates favor newer vehicles. The pipeline uses **two complementary comparison methods**:

#### Model-Level Comparisons: Same-Year Average

For best/worst models and year breakdowns, each vehicle is compared against the **national average for all vehicles of the same model year**:

```
National Average by Model Year (from database):
  2020: 87.67%    2015: 75.49%    2010: 60.50%
  2019: 86.21%    2014: 71.71%    2009: 59.01%
  2018: 84.24%    2013: 68.29%    2008: 57.39%
  ...
```

**Example**: A 2020 Range Rover with 88% pass rate is only +0.3% above the 2020 average (87.67%), not +16.5% above the overall average (71.5%).

#### Age-Band Comparisons: Weighted Averages

For durability scoring, vehicles are compared against **weighted national averages by age band** (computed from database, not hardcoded):

```
Weighted National Average by Age Band (approximate):
  3-4 years:  ~86%     9-10 years: ~70%
  5-6 years:  ~81%     11-12 years: ~63%
  7-8 years:  ~76%     13+ years:  ~57%
```

A vehicle's `vs_national_at_age` score shows how it performs relative to typical vehicles of the same age. Positive = better than average, negative = worse.

### 3. Maturity Tiers

```python
MATURITY_TIERS = {
    "proven": {"min_band": 4, "label": "Proven Durability"},      # 11+ years
    "maturing": {"min_band": 2, "max_band": 3, "label": "Maturing"},  # 7-10 years
    "early": {"max_band": 1, "label": "Early"}                    # 3-6 years
}
```

### 4. Minimum Test Thresholds

| Context | Minimum Tests | Constant | Rationale |
|---------|---------------|----------|-----------|
| Proven durability | 500 | `MIN_TESTS_PROVEN_DURABILITY` | Statistical significance at old ages |
| Early performers | 1,000 | `MIN_TESTS_EARLY_PERFORMER` | Higher bar since less meaningful |
| Core model aggregation | 500 | - | Sufficient for model-level claims |
| Year-by-year breakdown | 100 | - | Indicative patterns |

These constants are defined in `html_generator/components/data_classes.py` and used consistently throughout the HTML generation.

---

## Script Reference

### main.py - Unified Entry Point

**Purpose**: Single CLI interface for all article generation tasks.

**Location**: `scripts/article_generation/main.py`

**Commands**:

| Command | Description | Example |
|---------|-------------|---------|
| (none) | Interactive mode | `python main.py` |
| `generate <MAKE>` | Generate JSON + HTML | `python main.py generate BMW` |
| `generate-all` | Batch generate all makes | `python main.py generate-all` |
| `list [--top N]` | List available makes | `python main.py list --top 50` |
| `explore` | Run exploration script | `python main.py explore` |

**generate-all Options**:

| Option | Description |
|--------|-------------|
| `--min-tests N` | Only include makes with N+ tests (default: 0 = all) |
| `--dry-run` | Preview what would be generated without creating files |
| `--no-clean` | Skip cleaning output folders before generation |

**Key Functions**:

```python
get_available_makes() -> list[dict]     # Query database for all makes
display_makes(makes, limit=20)          # Format and print makes table
prompt_for_make(makes) -> str           # Interactive make selection
generate_json(make) -> Path             # Generate JSON insights
generate_html(json_file) -> Path        # Generate HTML from JSON
generate_article(make) -> bool          # Full pipeline: JSON + HTML
generate_all_articles(min_tests, dry_run, no_clean)  # Batch generation
clean_output_folders() -> dict          # Remove generated files before batch run
interactive_mode()                      # Run interactive flow with prompts
```

**Path Resolution**:
```python
SCRIPT_DIR = Path(__file__).parent                    # article_generation/
PROJECT_ROOT = SCRIPT_DIR.parent.parent               # project root
DB_PATH = PROJECT_ROOT / "data" / "database" / "mot_insights.db"
JSON_OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"
HTML_OUTPUT_DIR = PROJECT_ROOT / "articles" / "generated"
```

---

### json_parser/parser.py - JSON Generator

**Purpose**: Extract comprehensive reliability data for a vehicle make and output as structured JSON.

**Location**: `scripts/article_generation/json_parser/parser.py`

**CLI Usage**:
```bash
python json_parser/parser.py HONDA                    # Basic usage
python json_parser/parser.py HONDA --output out.json  # Custom output
python json_parser/parser.py HONDA --pretty           # Formatted JSON
python json_parser/parser.py --list                   # List all makes
python json_parser/parser.py --list --top 20          # Top N makes
```

**Key Functions**:

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_connection()` | Read-only DB connection | `sqlite3.Connection` |
| `list_available_makes()` | All makes with stats | `list[dict]` |
| `get_yearly_national_averages(conn)` | **Year-specific national averages (cached)** | `dict[int, float]` |
| `get_weighted_age_band_averages(conn)` | **Weighted age-band averages (cached)** | `dict[int, float]` |
| `get_manufacturer_overview(conn, make)` | Make-level stats | `dict` |
| `get_competitor_comparison(conn, make)` | Segment competitors | `list[dict]` |
| `get_core_models_aggregated(conn, make)` | Models grouped by family | `list[dict]` |
| `get_fuel_type_breakdown(conn, make)` | Pass rates by fuel | `list[dict]` |
| `get_best_models(conn, make, limit)` | Top performers **(year-adjusted ranking)** | `list[dict]` |
| `get_worst_models(conn, make, limit)` | Bottom performers **(year-adjusted ranking)** | `list[dict]` |
| `get_failure_categories(conn, make)` | MOT failure categories | `list[dict]` |
| `get_mileage_impact(conn, make)` | Pass rate by mileage band | `list[dict]` |
| `get_age_adjusted_scores(conn, make)` | Age-normalized scores | `list[dict]` |
| `get_durability_champions(conn, make)` | **Proven** high performers (weighted avg) | `list[dict]` |
| `get_models_to_avoid_proven(conn, make)` | **Proven** poor performers (weighted avg) | `list[dict]` |
| `get_early_performers(conn, make)` | New vehicles, early results (weighted avg) | `list[dict]` |
| `get_model_family_trajectory(conn, make, model)` | Aging curve data (weighted avg) | `dict` |
| `get_reliability_summary(conn, make)` | Overall durability rating (weighted avg) | `dict` |
| `generate_make_insights(make)` | **Main entry point** | `dict` |

**Competitor Segments** (30+ makes defined):
```python
segments = {
    # Japanese mainstream
    "HONDA": ["TOYOTA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
    "TOYOTA": ["HONDA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
    "MAZDA": ["HONDA", "TOYOTA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],

    # Korean
    "HYUNDAI": ["KIA", "TOYOTA", "HONDA", "MAZDA", "NISSAN", "SKODA"],
    "KIA": ["HYUNDAI", "TOYOTA", "HONDA", "MAZDA", "NISSAN", "SKODA"],

    # European mainstream
    "FORD": ["VAUXHALL", "VOLKSWAGEN", "PEUGEOT", "RENAULT", "CITROEN"],
    "VOLKSWAGEN": ["FORD", "VAUXHALL", "SKODA", "SEAT", "PEUGEOT"],

    # German premium
    "BMW": ["MERCEDES-BENZ", "AUDI", "LEXUS", "JAGUAR", "VOLVO"],
    "MERCEDES-BENZ": ["BMW", "AUDI", "LEXUS", "JAGUAR", "VOLVO"],
    "AUDI": ["BMW", "MERCEDES-BENZ", "LEXUS", "JAGUAR", "VOLVO"],

    # Luxury SUV / British premium
    "LAND ROVER": ["BMW", "MERCEDES-BENZ", "AUDI", "VOLVO", "JAGUAR", "PORSCHE"],
    "JAGUAR": ["BMW", "MERCEDES-BENZ", "AUDI", "LAND ROVER", "LEXUS", "VOLVO"],
    "VOLVO": ["BMW", "MERCEDES-BENZ", "AUDI", "LEXUS", "JAGUAR", "LAND ROVER"],

    # Premium Japanese
    "LEXUS": ["BMW", "MERCEDES-BENZ", "AUDI", "JAGUAR", "VOLVO", "INFINITI"],

    # Sports / Performance
    "PORSCHE": ["BMW", "MERCEDES-BENZ", "AUDI", "JAGUAR", "LEXUS", "ALFA ROMEO"],

    # Premium compact
    "MINI": ["AUDI", "BMW", "VOLKSWAGEN", "FIAT", "DS"],
    # ... and more
}
```

---

### html_generator/ - HTML Generation Module

**Purpose**: Transform JSON insights into SEO-optimized, styled HTML articles.

**Location**: `scripts/article_generation/html_generator/`

**Structure**:
```
html_generator/
├── __init__.py           # Module exports
├── generator.py          # Main orchestrator & CLI
└── components/
    ├── __init__.py       # Component exports
    ├── data_classes.py   # Dataclasses, constants, utilities
    ├── sections.py       # Individual section generators (1035 lines)
    └── layout.py         # Page structure, JSON-LD, TOC (433 lines)
```

**CLI Usage** (via `generator.py`):
```bash
python html_generator/generator.py data/generated/honda_insights.json
python html_generator/generator.py data/generated/honda_insights.json --output articles/
python html_generator/generator.py --all  # Process all JSON in data/generated/
python html_generator/generator.py data/generated/honda_insights.json --test  # Test parser only
```

**Architecture**:

The module uses **dataclasses** to parse JSON into typed structures:

| Class | Purpose | Location |
|-------|---------|----------|
| `ArticleInsights` | Main container, parses all JSON sections | `data_classes.py` |
| `CoreModel` | Aggregated model statistics | `data_classes.py` |
| `ModelYear` | Single year/fuel variant stats | `data_classes.py` |
| `Competitor` | Competitor manufacturer data | `data_classes.py` |
| `FuelAnalysis` | Fuel type breakdown | `data_classes.py` |
| `BestWorstModel` | Entries in best/worst lists | `data_classes.py` |
| `DurabilityVehicle` | **Proven** durability data (11+ years) | `data_classes.py` |
| `EarlyPerformer` | Early results with caveat | `data_classes.py` |
| `AgeBand` | Age band statistics | `data_classes.py` |
| `ReliabilitySummary` | Overall durability rating | `data_classes.py` |
| `SectionConfig` | Configuration for article sections | `data_classes.py` |

**Key Properties on ArticleInsights**:

```python
insights.make                    # "HONDA"
insights.title_make              # "Honda"
insights.total_tests             # 927815
insights.avg_pass_rate           # 71.7
insights.vs_national             # +0.2
insights.rank                    # 31
insights.top_models              # CoreModel list, sorted by pass rate
insights.durability_champions    # DurabilityVehicle list (proven, 11+)
insights.early_performers        # EarlyPerformer list (3-6 years)
insights.has_proven_durability_data()  # bool
```

**Layout Functions** (in `layout.py`):

| Function | Generates |
|----------|-----------|
| `generate_html_head()` | `<head>` with SEO meta, JSON-LD schemas |
| `generate_html_body()` | Complete `<body>` with two-column layout |
| `generate_toc_html()` | Table of contents sidebar |
| `generate_faq_jsonld()` | FAQ JSON-LD schema items |

**Section Generators** (in `sections.py`):

| Function | Generates |
|----------|-----------|
| `generate_header_section()` | Title, badges, data callout |
| `generate_key_findings_section()` | Summary cards |
| `generate_intro_section()` | Introduction prose |
| `generate_competitors_section()` | Comparison table |
| `generate_best_models_section()` | Top performers table |
| `generate_durability_section()` | **Proven** durability champions |
| `generate_early_performers_section()` | Early results with caveats |
| `generate_model_breakdowns_section()` | Year-by-year tables |
| `generate_fuel_analysis_section()` | Hybrid vs Petrol vs Diesel |
| `generate_avoid_section()` | Models to avoid |
| `generate_failures_section()` | Common MOT failures |
| `generate_faqs_section()` | FAQ accordion |
| `generate_recommendations_section()` | Buying recommendations |
| `generate_methodology_section()` | Data methodology explanation |
| `generate_cta_section()` | Call-to-action |

**Pass Rate CSS Classes**:
```python
def get_pass_rate_class(rate: float) -> str:
    if rate >= 85.0: return 'pass-rate-excellent'  # Green
    if rate >= 70.0: return 'pass-rate-good'       # Light green
    if rate >= 60.0: return 'pass-rate-average'    # Yellow
    return 'pass-rate-poor'                        # Red
```

**Utility Functions** (in `data_classes.py`):

| Function | Purpose |
|----------|---------|
| `safe_html(text)` | HTML-escape user data to prevent XSS (uses `html.escape`) |
| `slugify(text)` | Convert text to valid HTML ID (removes special chars, ensures letter start) |
| `format_number(n)` | Format numbers with thousands separator |
| `get_fuel_name(code)` | Convert fuel code to readable name |
| `get_pass_rate_class(rate)` | Return CSS class based on pass rate threshold |
| `parse_insights(json_path)` | Load JSON and parse into ArticleInsights object |
| `generate_faq_data(insights)` | Generate FAQ content from insights data |

**Security**: All user-provided data (model names, make names, category names) is escaped via `safe_html()` before HTML interpolation. The `slugify()` function ensures model names create valid HTML IDs (e.g., "CR-V" → "cr-v", "Type-R+" → "type-r").

**Constants** (in `data_classes.py`):

```python
FUEL_TYPE_NAMES = {'PE': 'Petrol', 'DI': 'Diesel', 'HY': 'Hybrid Electric', ...}
PASS_RATE_THRESHOLDS = {'excellent': 85.0, 'good': 70.0, 'average': 60.0}
MIN_TESTS_PROVEN_DURABILITY = 500    # Minimum for proven durability
MIN_TESTS_EARLY_PERFORMER = 1000     # Minimum for early performers
ARTICLE_SECTIONS = [...]             # Section order and config for TOC
```

---

### explore_article_opportunities.py - Data Explorer

**Purpose**: Discover article ideas and interesting data patterns.

**Location**: `scripts/article_generation/explore_article_opportunities.py`

**CLI Usage**:
```bash
python explore_article_opportunities.py           # Full exploration
python explore_article_opportunities.py --focus reliability
python explore_article_opportunities.py --focus problems
python explore_article_opportunities.py --focus trends
python explore_article_opportunities.py --focus evs
```

**Exploration Functions**:

| Function | Output |
|----------|--------|
| `explore_article_ideas()` | Content ideas with hooks |
| `explore_best_manufacturers()` | Top 15 by pass rate |
| `explore_worst_manufacturers()` | Bottom 15 by pass rate |
| `explore_problem_vehicles()` | Worst 25 model/years |
| `explore_best_vehicles()` | Best 25 model/years |
| `explore_hybrid_advantage()` | Hybrid vs ICE by make |
| `explore_ev_reliability()` | Electric vehicle rankings |
| `explore_year_trends()` | Pass rates by model year |
| `explore_diesels_to_avoid()` | Worst diesel models |
| `explore_first_cars()` | Best first cars (small, 2015+) |

---

### archive/generate_all_priority_makes.py - Legacy Batch Generator

> **Note**: This script has been superseded by `main.py generate-all`. It is kept in the `archive/` folder for reference only.

**Purpose**: Pre-generate JSON for high-traffic article candidates.

**Location**: `scripts/article_generation/archive/generate_all_priority_makes.py`

**Replacement**: Use `python main.py generate-all` instead, which:
- Generates both JSON and HTML (not just JSON)
- Supports `--min-tests` filtering
- Supports `--dry-run` preview mode
- Cleans output folders before generation (unless `--no-clean`)

**Legacy Priority Makes** (for reference):

```python
PRIORITY_MAKES = [
    # Tier 1: High search volume
    "TOYOTA", "HONDA", "BMW", "FORD", "VOLKSWAGEN", "AUDI", "MERCEDES-BENZ",

    # Tier 2: Good volume, interesting stories
    "MAZDA", "KIA", "HYUNDAI", "NISSAN", "VAUXHALL",

    # Tier 3: Niche but engaged audiences
    "MINI", "VOLVO", "SUZUKI", "SKODA", "LAND ROVER", "JAGUAR", "LEXUS", "PORSCHE"
]
```

---

## Database Schema

The pipeline reads from these key tables in `mot_insights.db`:

### manufacturer_rankings

```sql
CREATE TABLE manufacturer_rankings (
    make TEXT PRIMARY KEY,
    total_tests INTEGER,
    avg_pass_rate REAL,
    rank INTEGER,
    total_models INTEGER,
    best_model TEXT,
    best_model_pass_rate REAL,
    worst_model TEXT,
    worst_model_pass_rate REAL
);
```

### vehicle_insights

```sql
CREATE TABLE vehicle_insights (
    make TEXT,
    model TEXT,
    model_year INTEGER,
    fuel_type TEXT,           -- PE, DI, HY, EL, OT
    total_tests INTEGER,
    total_passes INTEGER,
    total_fails INTEGER,
    pass_rate REAL,
    avg_mileage REAL,
    avg_age_years REAL,
    pass_rate_vs_national REAL,
    PRIMARY KEY (make, model, model_year, fuel_type)
);
```

### age_bands

```sql
CREATE TABLE age_bands (
    make TEXT,
    model TEXT,
    model_year INTEGER,
    fuel_type TEXT,
    age_band TEXT,           -- "3-4 years", "5-6 years", etc.
    band_order INTEGER,      -- 0-5 for sorting
    total_tests INTEGER,
    pass_rate REAL,
    avg_mileage REAL,
    PRIMARY KEY (make, model, model_year, fuel_type, age_band)
);
```

### failure_categories

```sql
CREATE TABLE failure_categories (
    make TEXT,
    model TEXT,
    model_year INTEGER,
    fuel_type TEXT,
    category_name TEXT,
    failure_count INTEGER
);
```

### national_averages

```sql
CREATE TABLE national_averages (
    metric_name TEXT,
    metric_value REAL,
    model_year INTEGER,      -- NULL for overall
    fuel_type TEXT           -- NULL for overall
);
```

---

## JSON Output Structure

The JSON generated by `generate_make_insights.py` has this structure:

```json
{
  "meta": {
    "make": "HONDA",
    "generated_at": "2026-01-02T12:00:00",
    "database": "mot_insights.db",
    "national_pass_rate": 71.51,
    "methodology_version": "2.1",
    "methodology_note": "Year-adjusted scoring: model comparisons use same-year national averages. Age-band comparisons use weighted national averages. Only vehicles with 11+ years of data are classified as 'proven' durability."
  },

  "overview": { /* from manufacturer_rankings */ },

  "competitors": [
    {"make": "TOYOTA", "avg_pass_rate": 74.0, "total_tests": 1606300, "rank": 31}
  ],

  "summary": {
    "total_tests": 927815,
    "total_models": 156,
    "avg_pass_rate": 71.7,
    "rank": 31,
    "rank_total": 75,
    "best_model": "JAZZ CROSSTAR EX",
    "best_model_pass_rate": 96.1,
    "worst_model": "FR-V",
    "worst_model_pass_rate": 52.3,
    "vs_national": 0.19,
    "vs_national_note": "Manufacturer average vs overall national average (for brand-level comparison)"
  },

  "core_models": [
    {
      "core_model": "JAZZ",
      "total_tests": 245000,
      "pass_rate": 75.2,
      "avg_mileage": 42000,
      "year_from": 2002,
      "year_to": 2023,
      "variant_count": 45
    }
  ],

  "model_year_breakdowns": {
    "JAZZ": [
      {
        "model_year": 2020,
        "fuel_type": "HY",
        "pass_rate": 96.1,
        "total_tests": 1665,
        "pass_rate_vs_national": 8.4,
        "national_avg_for_year": 87.67
      }
    ]
  },

  "fuel_analysis": [
    {"fuel_type": "HY", "fuel_name": "Hybrid Electric", "pass_rate": 86.7, "total_tests": 45000}
  ],

  "best_models": [
    {
      "model": "JAZZ",
      "model_year": 2008,
      "fuel_type": "PE",
      "total_tests": 5420,
      "pass_rate": 72.5,
      "pass_rate_vs_national": 15.1,
      "national_avg_for_year": 57.4
    }
    /* top 15 ranked by pass_rate_vs_national (year-adjusted) */
  ],
  "worst_models": [/* bottom 10 ranked by pass_rate_vs_national (year-adjusted) */],

  "failures": {
    "categories": [{"category_name": "Brakes", "total_failures": 125000}],
    "top_failures": [{"defect_description": "Brake pad worn...", "occurrence_count": 8500}],
    "dangerous": [/* dangerous defects */]
  },

  "mileage_impact": [
    {"mileage_band": "0-30k", "band_order": 0, "avg_pass_rate": 85.2}
  ],

  "age_adjusted": {
    "methodology": "Compares each model's pass rate against national average for same age",
    "best_models": [/* AgeAdjustedModel objects */],
    "worst_models": [/* AgeAdjustedModel objects */]
  },

  "durability": {
    "methodology": {
      "description": "Evidence-tiered durability scoring",
      "proven_threshold": "11+ years of MOT data required",
      "early_caveat": "Vehicles under 7 years have not proven durability"
    },
    "reliability_summary": {
      "durability_rating": "Good",           // Excellent/Good/Average/Below Average
      "proven_vehicles_tested": 45,
      "proven_above_average_pct": 72.5,
      "proven_avg_vs_national": 3.2
    },
    "durability_champions": {
      "description": "Vehicles with PROVEN durability - 11+ years, above average",
      "evidence_quality": "high",
      "vehicles": [
        {
          "model": "JAZZ",
          "model_year": 2008,
          "fuel_type": "PE",
          "age_band": "13+ years",
          "pass_rate": 68.5,
          "vs_national_at_age": 11.2,
          "national_avg_for_age": 57.3,
          "maturity_tier": "proven",
          "evidence_quality": "high"
        }
      ]
    },
    "models_to_avoid": {
      "description": "Vehicles with PROVEN poor durability",
      "vehicles": [
        {
          "model": "STREAM",
          "model_year": 2001,
          "concern": "Below average durability at 11-12 years",  // Displayed in recommendations
          /* ...other fields same as durability_champions... */
        }
      ]
    },
    "early_performers": {
      "description": "Newer vehicles showing strong early results",
      "evidence_quality": "limited",
      "caveat": "Durability NOT yet proven",
      "vehicles": [/* similar structure */]
    },
    "model_trajectories": {
      "JAZZ": {
        "core_model": "JAZZ",
        "years_covered": [2002, 2003, ...],
        "trajectory_by_age": {/* aging curves */},
        "best_proven_year": {"year": 2008, "vs_national": 8.6},
        "has_proven_data": true
      }
    }
  }
}
```

---

## HTML Generation

### Output Structure

Generated HTML includes:

1. **SEO Meta Tags**: Title, description, canonical URL
2. **Open Graph**: Social sharing metadata
3. **JSON-LD Schemas**: Article, BreadcrumbList, FAQPage
4. **Tailwind CSS**: Via CDN with custom config
5. **Phosphor Icons**: Icon library
6. **Responsive Layout**: Mobile-first design

### Article Sections

| Section | Content |
|---------|---------|
| Header | Title, badges, data callout |
| Key Findings | 4 summary cards |
| Competitor Comparison | Ranked table with highlighting |
| Best Models | Top 10 by overall pass rate |
| **Durability Champions** | Proven 11+ year performers |
| **Early Performers** | Recent models with caveats |
| Model Breakdowns | Year-by-year tables for top models |
| Fuel Analysis | Hybrid/Petrol/Diesel comparison |
| Models to Avoid | Proven poor performers |
| Common Failures | MOT failure categories |
| FAQs | Accordion with structured data |
| Methodology | Evidence-tiered explanation |
| CTA | Call-to-action |

### Styling Classes

```css
.pass-rate-excellent { color: #059669; background: #d1fae5; }  /* >= 85% */
.pass-rate-good      { color: #16a34a; background: #dcfce7; }  /* >= 70% */
.pass-rate-average   { color: #ca8a04; background: #fef9c3; }  /* >= 60% */
.pass-rate-poor      { color: #dc2626; background: #fee2e2; }  /* < 60% */
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                           │
└─────────────────────────────────────────────────────────────────────┘

   DVSA CSV Files
        │
        ▼
┌───────────────────┐
│ generate_insights │  (separate preprocessing script)
│ _optimized.py     │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ mot_insights.db   │  SQLite Database
│ (read-only)       │
└───────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    ARTICLE GENERATION PIPELINE                     │
│                                                                    │
│  ┌─────────────────────┐                                          │
│  │ explore_article_    │ ◄── Discover opportunities               │
│  │ opportunities.py    │                                          │
│  └─────────────────────┘                                          │
│                                                                    │
│  ┌─────────────────────┐     ┌──────────────────────┐             │
│  │ json_parser/        │ ──► │ {make}_insights.json │             │
│  │ parser.py           │     │ (data/generated/)    │             │
│  └─────────────────────┘     └──────────────────────┘             │
│            │                           │                          │
│            │                           ▼                          │
│            │                 ┌──────────────────────┐             │
│            │                 │ html_generator/      │             │
│            │                 │ ├─ generator.py      │             │
│            │                 │ └─ components/       │             │
│            │                 │    ├─ data_classes   │             │
│            │                 │    ├─ sections.py    │             │
│            │                 │    └─ layout.py      │             │
│            │                 └──────────────────────┘             │
│            │                           │                          │
│            │                           ▼                          │
│            │                 ┌──────────────────────┐             │
│            │                 │ {make}-most-reliable │             │
│            │                 │ -models.html         │             │
│            │                 │ (articles/generated/)│             │
│            │                 └──────────────────────┘             │
│            │                                                      │
│            ▼                                                      │
│  ┌─────────────────────┐                                          │
│  │ main.py             │ ◄── Unified entry point                  │
│  │ (orchestrates both) │     Commands: generate, generate-all,    │
│  │                     │     list, explore                        │
│  └─────────────────────┘                                          │
└───────────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Database Connection

```python
from pathlib import Path
import sqlite3

# From json_parser/parser.py (3 levels up to project root):
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "database" / "mot_insights.db"

def get_connection():
    """Create read-only database connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn
```

### Path Resolution

Scripts use relative paths from `__file__`. Note the depth varies by file location:

```python
# From scripts/article_generation/main.py (2 levels up):
SCRIPT_DIR = Path(__file__).parent                    # article_generation/
PROJECT_ROOT = SCRIPT_DIR.parent.parent               # project root
DB_PATH = PROJECT_ROOT / "data" / "database" / "mot_insights.db"

# From scripts/article_generation/json_parser/parser.py (3 levels up):
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "database" / "mot_insights.db"

# From scripts/article_generation/html_generator/generator.py (2 levels up from html_generator/):
SCRIPT_DIR = Path(__file__).parent                    # html_generator/
PROJECT_DIR = SCRIPT_DIR.parent.parent                # scripts/ -> project root
DATA_DIR = PROJECT_DIR / "data" / "generated"
OUTPUT_DIR = PROJECT_DIR / "articles" / "generated"
```

### Fuel Type Mapping

```python
FUEL_TYPE_NAMES = {
    'PE': 'Petrol',
    'DI': 'Diesel',
    'HY': 'Hybrid Electric',
    'EL': 'Electric',
    'ED': 'Plug-in Hybrid',
    'GB': 'Gas Bi-fuel',
    'OT': 'Other'
}
```

### Age Band Constants

```python
# In json_parser/parser.py:
AGE_BAND_ORDER = {
    "3-4 years": 0,
    "5-6 years": 1,
    "7-8 years": 2,
    "9-10 years": 3,
    "11-12 years": 4,
    "13+ years": 5
}

# Minimum test thresholds (also in html_generator/components/data_classes.py):
MIN_TESTS_PROVEN = 500           # For proven durability rankings
MIN_TESTS_EARLY = 1000           # For early performer rankings

# DEPRECATED: Hardcoded constants (kept for reference only)
# These are now computed dynamically from the database using
# get_weighted_age_band_averages() for more accurate weighted calculations.
# NATIONAL_AVG_BY_BAND = {
#     0: 86.43,  # 3-4 years
#     1: 82.13,  # 5-6 years
#     ...
# }

# v2.1: Use dynamic lookup functions instead:
# - get_yearly_national_averages(conn) -> {year: avg_pass_rate}
# - get_weighted_age_band_averages(conn) -> {band_order: weighted_avg}
```

---

## Extending the Pipeline

### Adding a New Metric

1. **Database Query** (`json_parser/parser.py`):
   ```python
   def get_new_metric(conn, make: str) -> list:
       cur = conn.execute("SELECT ... FROM ... WHERE make = ?", (make,))
       return [dict_from_row(row) for row in cur.fetchall()]
   ```

2. **Add to Output** (`generate_make_insights()` in `parser.py`):
   ```python
   return {
       # ... existing fields ...
       "new_metric": get_new_metric(conn, make)
   }
   ```

3. **Create Dataclass** (`html_generator/components/data_classes.py`):
   ```python
   @dataclass
   class NewMetric:
       field1: str
       field2: float
       # ...
   ```

4. **Parse in ArticleInsights** (`data_classes.py`):
   ```python
   def _parse_new_metric(self, data: list):
       self.new_metric = [NewMetric(**item) for item in data]
   ```

5. **Generate HTML Section** (`html_generator/components/sections.py`):
   ```python
   def generate_new_metric_section(insights: ArticleInsights) -> str:
       return f'''<section id="new-metric">...</section>'''
   ```

6. **Add to Body** (`html_generator/components/layout.py`):
   ```python
   # In generate_html_body():
   main_sections.append(wrap_scroll_reveal(
       sections.generate_new_metric_section(insights), reveal_index
   ))
   ```

7. **Add to TOC** (`data_classes.py`):
   ```python
   ARTICLE_SECTIONS = [
       # ... existing sections ...
       SectionConfig("new-metric", "New Metric", "ph-icon-name", "blue"),
   ]
   ```

### Adding a New Article Type

1. Create new parser (e.g., `json_parser/comparison_parser.py`)
2. Create new HTML generator (e.g., `html_generator/comparison_generator.py`)
3. Add command to `main.py`
4. Create corresponding dataclasses and section generators

### Customizing Competitor Groups

Edit the `segments` dict in `get_competitor_comparison()` (`json_parser/parser.py`):

```python
segments = {
    "YOUR_MAKE": ["COMPETITOR1", "COMPETITOR2", "COMPETITOR3"],
    # ...
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Database not found" | Wrong path resolution | Check `DB_PATH` uses correct `.parent` chain for file depth |
| "Make not found" | Case sensitivity | Ensure make is uppercase |
| Empty durability data | No 11+ year vehicles | Expected for newer makes |
| HTML missing sections | JSON structure changed | Verify JSON has required fields |
| "ModuleNotFoundError" | Running from wrong directory | Run from `article_generation/` or use full path |
| Import errors in generator | Missing components | Check `components/__init__.py` exports |

### Debugging Tips

```python
# Print JSON structure (from json_parser/)
import json
from parser import generate_make_insights
data = generate_make_insights("HONDA")
print(json.dumps(data, indent=2)[:5000])

# Check database path
from pathlib import Path
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "database" / "mot_insights.db"
print(f"DB exists: {DB_PATH.exists()}")
print(f"DB path: {DB_PATH.absolute()}")

# Test HTML generator parser (from html_generator/)
python generator.py data/generated/honda_insights.json --test
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.3 | 2026-01-15 | **Codebase refactoring**: Reorganized into `json_parser/` and `html_generator/components/` subdirectories. Added `main.py generate-all` command with `--min-tests`, `--dry-run`, and `--no-clean` options. Moved `generate_all_priority_makes.py` to `archive/`. Split HTML generator into modular components (`data_classes.py`, `sections.py`, `layout.py`). |
| 2.2 | 2026-01-02 | **Security & robustness fixes**: Added `safe_html()` for HTML escaping of user data. Added `slugify()` for valid HTML IDs. Added `MIN_TESTS_PROVEN_DURABILITY` and `MIN_TESTS_EARLY_PERFORMER` constants. Display `concern` field for models to avoid in recommendations section. |
| 2.1 | 2026-01-02 | **Year-adjusted scoring**: Best/worst models now ranked by performance vs same-year national average. Age-band comparisons use weighted (not simple) averages from database. Expanded competitor segments (30+ makes). Added `national_avg_for_year` and `national_avg_for_age` fields to JSON output. |
| 2.0 | 2026-01-01 | Evidence-tiered durability methodology |
| 1.0 | Initial | Basic pass rate analysis |

---

## Contact

For questions about this pipeline, refer to:
- `docs/DEVELOPER_REFERENCE.md` - Project-wide documentation
- Database schema in `data/database/`
- Generated examples in `articles/generated/`
