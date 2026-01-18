# Frontend Components Specification

**Version:** 4.0
**Last Updated:** 2026-01-18
**Files:**
- `html_generator/components/sections.py`
- `html_generator/components/data_classes.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Version History](#version-history)
3. [Architecture](#architecture)
4. [Data Classes (data_classes.py)](#data-classes-data_classespy)
5. [Section Generators (sections.py)](#section-generators-sectionspy)
6. [v3.0 Compatibility: model_year=0 Handling](#v30-compatibility-model_year0-handling)
7. [Section Reference](#section-reference)
8. [CSS Classes & Styling](#css-classes--styling)
9. [Testing & Validation](#testing--validation)

---

## Overview

The frontend components transform parsed JSON insights into HTML article sections. The system consists of:

| Component | Purpose |
|-----------|---------|
| `data_classes.py` | Data structures and JSON parsing |
| `sections.py` | HTML generation for each article section |
| `layout.py` | Page layout and navigation |
| `generator.py` | Main orchestration |

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Objective Presentation** | Present data without subjective spin; let users draw conclusions |
| **Graceful Degradation** | Handle missing/empty data without errors |
| **v3.0 Compatibility** | Handle aggregated data where model_year=0 |
| **Responsive Design** | Tailwind CSS for mobile-first layouts |

---

## Version History

### v4.0 (2026-01-18) - Current

**Major Changes:**
- Complete rewrite of `generate_recommendations_section()` with two-panel layout
- Added helper functions for year validation and display formatting
- Visual progress bars for rankings
- Numbered ranking system for recommendations

**v3.0 Compatibility Fixes:**
- Fixed `generate_durability_section()` table to show "-" for model_year=0
- Fixed `generate_durability_section()` standout_note to omit year when 0
- Fixed `generate_early_performers_section()` table to show "-" for model_year=0
- Fixed `generate_avoid_section()` worst_ager display to omit year when 0
- `generate_key_findings_section()` already fixed in previous session

### v3.0 (2026-01-17)

**Breaking Changes:**
- Parser now outputs `age_band_analysis` instead of `durability` section
- `DurabilityVehicle` and `EarlyPerformer` objects may have `model_year=0`
- Data aggregated by core model name rather than specific model years

**New Features:**
- `_parse_age_band_analysis()` method in ArticleInsights
- Evidence-tiered durability with maturity tiers
- Confidence levels based on sample size
- `_calculate_reliability_summary()` from parsed data

### v2.2 (2026-01-16)

- Dynamic intro text based on durability_rating
- Reliability rating badge display
- Context tooltips for comparisons

### v2.1 (2026-01-15)

- Year-adjusted comparisons with national_avg_for_year
- Age-band weighted averages
- Comparison context properties

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      generator.py                            │
│                    (Main Entry Point)                        │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  data_classes.py│  │  sections.py    │  │  layout.py      │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ ArticleInsights │  │ generate_*()    │  │ generate_page() │
│ DurabilityVehicle│ │ 15+ section     │  │ generate_toc()  │
│ EarlyPerformer  │  │ generators      │  │ generate_nav()  │
│ CoreModel       │  │                 │  │                 │
│ BestWorstModel  │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  HTML Output    │
                    └─────────────────┘
```

---

## Data Classes (data_classes.py)

### Core Data Classes

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `ArticleInsights` | Main parser class | All parsed data |
| `CoreModel` | Aggregated model stats | name, pass_rate, year_breakdowns |
| `ModelYear` | Single model-year-fuel combo | model_year, pass_rate, vs_national |
| `BestWorstModel` | Best/worst rankings | model, model_year, vs_national |
| `DurabilityVehicle` | Proven durability (11+ years) | model, model_year, age_band, vs_national_at_age |
| `EarlyPerformer` | Early results (3-6 years) | model, model_year, age_band, caveat |
| `ReliabilitySummary` | Overall rating | durability_rating, tier_distribution |

### DurabilityVehicle Class

```python
@dataclass
class DurabilityVehicle:
    model: str
    model_year: int           # May be 0 in v3.0 (aggregated data)
    fuel_type: str
    fuel_name: str
    age_band: str             # e.g., "11-14 years"
    age_band_order: int       # 0-5 for sorting
    total_tests: int
    pass_rate: float
    vs_national_at_age: float # Key metric: +/- vs same-age avg
    avg_mileage: float
    maturity_tier: str        # "proven", "maturing", "early"
    evidence_quality: str     # "high", "medium", "limited"
    concern: Optional[str]    # For models to avoid
    national_avg_for_age: Optional[float]  # v2.1: context
```

### EarlyPerformer Class

```python
@dataclass
class EarlyPerformer:
    model: str
    model_year: int           # May be 0 in v3.0 (aggregated data)
    fuel_type: str
    fuel_name: str
    age_band: str
    age_band_order: int
    total_tests: int
    pass_rate: float
    vs_national_at_age: float
    avg_mileage: float
    maturity_tier: str
    evidence_quality: str
    caveat: str               # Always present - durability unproven
    national_avg_for_age: Optional[float]
```

### v3.0 Parsing: _parse_age_band_analysis()

The parser detects v3.0 format and creates objects with `model_year=0`:

```python
def _parse_age_band_analysis(self):
    """
    Parse v3.0 age_band_analysis structure into durability data.

    Converts model_breakdown with age_bands into:
    - proven_durability_champions (band_order >= 2, vs_national > 0)
    - proven_models_to_avoid (band_order >= 2, vs_national < -3)
    - early_performers (band_order <= 1, vs_national > 0)
    """
    # ...
    entry = DurabilityVehicle(
        model=core_model,
        model_year=0,  # v3.0 aggregates by core model, not year
        fuel_type='',
        fuel_name='All',
        # ...
    )
```

---

## Section Generators (sections.py)

### Function Reference

| Function | Section ID | Description |
|----------|------------|-------------|
| `generate_header_section()` | - | Article title, meta, data source callout |
| `generate_key_findings_section()` | - | 4 summary boxes |
| `generate_intro_section()` | - | Dynamic intro paragraph |
| `generate_competitors_section()` | `{make}-vs-competition` | Manufacturer comparison table |
| `generate_best_models_section()` | `best-models` | Top models by pass rate |
| `generate_durability_section()` | `durability` | Proven durability champions |
| `generate_early_performers_section()` | `early-performers` | Unproven early performers |
| `generate_model_breakdowns_section()` | `{model-slug}` | Year-by-year for top models |
| `generate_fuel_analysis_section()` | `fuel-types` | Hybrid vs Petrol vs Diesel |
| `generate_avoid_section()` | `avoid` | Models to avoid |
| `generate_failures_section()` | `failures` | Common MOT failures |
| `generate_faqs_section()` | `faqs` | FAQ accordion |
| `generate_recommendations_section()` | `recommendations` | Buying recommendations |
| `generate_methodology_section()` | `methodology` | About this data |
| `generate_cta_section()` | - | Call to action |

---

## v3.0 Compatibility: model_year=0 Handling

### The Problem

v3.0 JSON aggregates data by **core model name** rather than specific model years. This creates `DurabilityVehicle` and `EarlyPerformer` objects with `model_year=0`. Without handling, this displays as:

- Table cells: "0" in Year column
- Text: "The Fiesta 0 outperforms..."
- Year ranges: "0-0" or just "0"

### The Solution

Apply these patterns consistently throughout sections.py:

#### Pattern 1: Table Cell Display

```python
# v3.0: Show "-" if model_year is 0 (aggregated data)
year_display = str(m.model_year) if m.model_year and m.model_year > 0 else "-"

rows.append(f'''<tr>
    <td>{safe_html(m.model)}</td>
    <td>{year_display}</td>  <!-- Shows "-" instead of "0" -->
    ...
</tr>''')
```

#### Pattern 2: Text Display (Model Name)

```python
# v3.0: model_year may be 0 when aggregated by core model
if obj.model_year and obj.model_year > 0:
    name = f"{obj.model} {obj.model_year}"
else:
    name = obj.model

# Usage in text:
f"The {name} outperforms..."  # Shows "The Fiesta outperforms..." not "The Fiesta 0 outperforms..."
```

#### Pattern 3: Year Range from List

```python
# Filter out 0 values before computing range
years = sorted([x.model_year for x in similar if x.model_year and x.model_year > 0])
if years:
    year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
else:
    year_range = None  # Handle no-year case - show model name only
```

#### Pattern 4: Helper Functions (v4.0 Recommendations)

```python
def _is_valid_year(year: int) -> bool:
    """Check if year is valid (not 0 or unreasonable)."""
    return year and 1950 <= year <= 2030

def _format_year_display(model_year: int, age_band: str = None) -> str:
    """Format year for display, using age band as fallback."""
    if _is_valid_year(model_year):
        return str(model_year)
    elif age_band:
        return f"({age_band})"
    return ""
```

### Locations Fixed

| Function | Location | Fix Applied |
|----------|----------|-------------|
| `generate_key_findings_section()` | Lines 82-99 | Pattern 2 for durability_champ and early_performer |
| `generate_durability_section()` | Line 401 | Pattern 1 for table row |
| `generate_durability_section()` | Line 419 | Pattern 2 for standout_note |
| `generate_early_performers_section()` | Line 571 | Pattern 1 for table row |
| `generate_avoid_section()` | Line 936 | Pattern 2 for worst_ager_name |
| `generate_recommendations_section()` | Lines 1115-1125 | Pattern 4 helper functions |

---

## Section Reference

### generate_durability_section()

**Purpose:** Display proven durability champions (11+ years of data)

**Key Features:**
- Dynamic intro text based on durability_rating
- Reliability rating badge
- High-confidence data callout
- Table with Model, Year, Fuel, vs Same-Age Average, Tested At, Pass Rate
- Standout champion callout (if vs_national >= 15)

**v3.0 Handling:**
```python
# Table row
year_display = str(m.model_year) if m.model_year and m.model_year > 0 else "-"

# Standout note
top_name = f"{top.model} {top.model_year}" if top.model_year and top.model_year > 0 else top.model
```

### generate_early_performers_section()

**Purpose:** Display early performers (3-6 years) with caveat

**Key Features:**
- Prominent amber warning about unproven durability
- Table with same structure as durability section
- Recommendation to check older versions

**v3.0 Handling:**
```python
year_display = str(m.model_year) if m.model_year and m.model_year > 0 else "-"
```

### generate_recommendations_section() (v4.0)

**Purpose:** Buying recommendations with visual ranking

**v4.0 Redesign Features:**
- Two-panel layout (lg:grid-cols-5)
- Left panel: Ranked lists with progress bars
- Right panel: Summary stats + Avoid card
- Numbered rankings (1-4)
- Visual progress bars
- Helper functions for year validation

**Structure:**
```
┌─────────────────────────────────┬─────────────────┐
│ Best If Buying Nearly New       │ Summary Card    │
│ [1] Model A - 92%               │ Recommended: 8  │
│ [2] Model B - 90%               │ To Avoid: 4     │
│ [3] Model C - 89%               ├─────────────────┤
├─────────────────────────────────┤ Models to Avoid │
│ Best If Buying Used (Proven)    │ [1] Model X -8% │
│ [1] Model D - +12% vs avg       │ [2] Model Y -6% │
│ [2] Model E - +10% vs avg       │                 │
└─────────────────────────────────┴─────────────────┘
```

**v3.0 Handling:**
```python
def _format_year_display(model_year: int, age_band: str = None) -> str:
    """Format year for display, using age band as fallback."""
    if _is_valid_year(model_year):
        return str(model_year)
    elif age_band:
        return f"({age_band})"  # e.g., "(11-14 years)"
    return ""
```

### generate_avoid_section()

**Purpose:** Models to avoid with proven poor durability

**Key Features:**
- Table of worst models by pass rate
- Pattern detection for warning callout
- Proven durability context if worst_ager is significantly below average

**v3.0 Handling:**
```python
worst_ager_name = f"{worst_ager.model} {worst_ager.model_year}" if worst_ager.model_year and worst_ager.model_year > 0 else worst_ager.model
```

---

## CSS Classes & Styling

### Pass Rate Classes

| Class | Threshold | Color |
|-------|-----------|-------|
| `pass-rate-excellent` | >= 85% | Emerald |
| `pass-rate-good` | >= 70% | Green |
| `pass-rate-average` | >= 60% | Amber |
| `pass-rate-poor` | < 60% | Red |

### Callout Types

| Type | Use Case | Icon |
|------|----------|------|
| `.callout.tip` | Positive highlight | `ph-check-circle` |
| `.callout.warning` | Caution/avoid | `ph-warning` |

### Color Themes by Section

| Section | Primary Color | Background |
|---------|---------------|------------|
| Durability Champions | Emerald | `from-emerald-50` |
| Early Performers | Amber | `from-amber-50` |
| Models to Avoid | Red | `from-red-50` |
| Recommendations | Blue/Emerald/Red | Mixed |

---

## Testing & Validation

### Test Commands

```bash
# Navigate to script directory
cd scripts/reliabilty-reports

# Test with Ford v3.0 JSON
python html_generator/generator.py ../../data/json/reliability-reports/ford_insights.json --test

# Generate HTML output
python html_generator/generator.py ../../data/json/reliability-reports/ford_insights.json --output ./reports/

# Test multiple makes
python main.py --makes ford,honda,toyota --output ./reports/
```

### Validation Checklist

| Check | Expected Result |
|-------|-----------------|
| Durability table Year column | Shows "-" for aggregated data, not "0" |
| Durability standout note | Shows "The Fiesta outperforms..." not "The Fiesta 0 outperforms..." |
| Early performers Year column | Shows "-" for aggregated data |
| Recommendations | Shows age band context when year is 0 |
| Avoid section | Shows model name only when year is 0 |
| No "0" appearing in output | Verified in HTML source |
| No "0-0" year ranges | Verified in recommendations |

### Edge Cases to Test

| Scenario | Expected Behavior |
|----------|-------------------|
| All models have model_year=0 | Tables show "-", text shows model names only |
| Mixed model_year (some 0, some valid) | Each handled appropriately |
| Empty proven_durability_champions | Falls back to legacy section or empty |
| Empty early_performers | Section not rendered |
| No worst_ager data | Age context paragraph omitted |

---

## File Dependencies

```
html_generator/
├── __init__.py
├── generator.py           # Main entry point
├── components/
│   ├── __init__.py
│   ├── data_classes.py    # Data structures & parsing
│   ├── sections.py        # HTML section generators
│   └── layout.py          # Page layout & navigation
```

### Import Structure

```python
# sections.py imports from data_classes.py
from .data_classes import (
    ArticleInsights,
    DurabilityVehicle,
    EarlyPerformer,
    format_number,
    safe_html,
    slugify,
    get_pass_rate_class,
    MIN_TESTS_PROVEN_DURABILITY,
    MIN_TESTS_EARLY_PERFORMER,
    generate_faq_data,
)
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `PARSER_SPECIFICATION.md` | Parser (json_parser) documentation |
| `AUDIT_REPORT.md` | Database and parser audit findings |
| `HANDOVER_SECTIONS_PY_FIXES.md` | v3.0 compatibility fix tracking |

---

## Changelog Summary

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-18 | 4.0 | Recommendations v4.0 rewrite, all model_year=0 fixes |
| 2026-01-17 | 3.0 | v3.0 parser compatibility, age_band_analysis support |
| 2026-01-16 | 2.2 | Dynamic intro text, rating badges |
| 2026-01-15 | 2.1 | Year-adjusted comparisons, context tooltips |
