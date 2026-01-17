# Buyer's Inspection Guide - MVP Specification

## Overview

A lean HTML generator that creates actionable inspection guides for used car buyers. This MVP focuses on **direct, non-derived data** to avoid edge cases and misleading inferences.

**Target Audience:** Used car buyers researching before purchase

**Philosophy:**
- Only show high-value, actionable insights
- No inferred or derived data (edge case risks)
- No false reassurance ("no concerns identified")
- Honest framing - if data is from MOT history, say so
- Quality over quantity

---

## MVP Sections (3 total)

### 1. Top 5 Failure Points

**Purpose:** What components fail most often on this model

**Data Source:** `top_defects` table (direct query)

**Display:** Numbered list with percentage

**Query:**
```sql
SELECT
    defect_description,
    category_name,
    SUM(occurrence_count) as total_occurrences,
    ROUND(SUM(occurrence_count) * 100.0 /
        (SELECT SUM(occurrence_count)
         FROM top_defects
         WHERE make = ? AND model = ? AND defect_type = 'failure'), 1) as percentage
FROM top_defects
WHERE make = ? AND model = ? AND defect_type = 'failure'
GROUP BY defect_description, category_name
ORDER BY total_occurrences DESC
LIMIT 5
```

**Output Format:**
```
1. Front brake pads worn (18.3%)
   Category: Brakes

2. Rear lamp not working (12.1%)
   Category: Lamps, reflectors and electrical equipment

[etc.]
```

**Empty Handling:** Omit section if no failure data exists

---

### 2. Dangerous Defects (MOT History Check)

**Purpose:** Safety-critical issues to check in MOT history

**Data Source:** `dangerous_defects` table (direct query)

**Framing:**
> "Check the vehicle's MOT history for these safety-critical issues. These are 'dangerous' defects that cause immediate MOT failure. If present in recent tests, investigate further before purchasing."

**Query:**
```sql
SELECT
    defect_description,
    category_name,
    SUM(occurrence_count) as total_occurrences
FROM dangerous_defects
WHERE make = ? AND model = ?
GROUP BY defect_description, category_name
ORDER BY total_occurrences DESC
LIMIT 10
```

**Output Format:**
```
- Tyre tread depth below requirements (Category: Tyres)
- Brake hose excessively deteriorated (Category: Brakes)
- Steering rack insecure (Category: Steering)
[etc.]
```

**Empty Handling:** Omit section if no dangerous defects recorded

---

### 3. Pass Rates by Year

**Purpose:** Help buyers compare model years

**Data Source:** `vehicle_insights` table (direct query)

**Display:** Simple table sorted by pass rate (highest first)

**Query:**
```sql
SELECT
    model_year,
    SUM(total_tests) as total_tests,
    ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
FROM vehicle_insights
WHERE make = ? AND model = ?
GROUP BY model_year
HAVING total_tests >= 100
ORDER BY pass_rate DESC
```

**Output Format:**
| Year | Pass Rate | Tests |
|------|-----------|-------|
| 2019 | 78.2% | 41,191 |
| 2018 | 77.1% | 37,330 |
| 2017 | 75.8% | 35,420 |
| ... | ... | ... |

**Notes:**
- Minimum 100 tests required for inclusion (statistical validity)
- No "best/worst" labels - user interprets the data
- No recommendations like "target 2016+ models"

**Empty Handling:** Omit section if insufficient data

---

## Page Structure

```
┌─────────────────────────────────────────────────────────┐
│  Ford Focus - Buyer's Inspection Guide                  │
│  Based on 245,000 MOT tests                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TOP 5 FAILURE POINTS                                   │
│  ─────────────────────                                  │
│  The most common reasons this model fails its MOT       │
│                                                         │
│  1. [defect] (X.X%)                                     │
│  2. [defect] (X.X%)                                     │
│  ...                                                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  MOT HISTORY CHECK                                      │
│  ─────────────────                                      │
│  Check the vehicle's MOT history for these safety-      │
│  critical issues. These are 'dangerous' defects that    │
│  cause immediate MOT failure.                           │
│                                                         │
│  • [dangerous defect]                                   │
│  • [dangerous defect]                                   │
│  ...                                                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PASS RATES BY YEAR                                     │
│  ──────────────────                                     │
│  MOT pass rates for each model year                     │
│                                                         │
│  [Table: Year | Pass Rate | Tests]                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ABOUT THIS DATA                                        │
│  ────────────────                                       │
│  Analysis based on [X] MOT tests from DVSA records.     │
│  Pass rates reflect MOT test outcomes only.             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## What We're NOT Including (and why)

| Feature | Reason for Exclusion |
|---------|---------------------|
| Traffic light rating (good/average/poor) | Arbitrary thresholds, implies false precision |
| "Target 2016+ models" recommendations | Derived inference, edge cases |
| Mileage risk zones | Requires deriving "peak failure band" |
| Early failure warnings | Overlaps with Top 5, adds complexity |
| Advisory progression | Threshold calibration issues |
| "No concerns identified" messages | False reassurance |

---

## File Structure

```
scripts/model_report_generator/
├── generate_model_report.py      # EXISTING - comprehensive reports
├── generate_inspection_guide.py  # NEW - MVP inspection guide
├── db_queries.py                 # ADD: get_inspection_guide_data()
├── html_templates.py             # REUSE existing components
├── tailwind_classes.py           # REUSE existing classes
└── docs/
    ├── BUYER_INSPECTION_GUIDE_SPEC.md      # Original full spec
    └── BUYER_INSPECTION_GUIDE_MVP_SPEC.md  # THIS FILE
```

---

## New Database Function

### `get_inspection_guide_data(make: str, model: str) -> dict | None`

Single function returning all MVP data:

```python
def get_inspection_guide_data(make: str, model: str) -> dict | None:
    """
    Fetch all data needed for buyer's inspection guide.
    Returns None if insufficient data for the model.
    """
    return {
        "make": str,
        "model": str,
        "total_tests": int,

        "top_failures": [
            {
                "defect_description": str,
                "category_name": str,
                "occurrence_count": int,
                "percentage": float
            }
            # Up to 5 items, may be empty
        ],

        "dangerous_defects": [
            {
                "defect_description": str,
                "category_name": str,
                "occurrence_count": int
            }
            # Up to 10 items, may be empty
        ],

        "year_pass_rates": [
            {
                "model_year": int,
                "pass_rate": float,
                "total_tests": int
            }
            # Sorted by pass_rate DESC, min 100 tests each
        ]
    }
```

---

## Reusable Components from html_templates.py

| Component | Use |
|-----------|-----|
| `generate_head()` | Page head with SEO |
| `generate_breadcrumb()` | Navigation |
| `generate_article_header()` | Title (simplified) |
| `generate_article_section()` | Section wrappers |
| `generate_table()` | Year pass rates table |
| `generate_callout()` | MOT history check warning box |

---

## Output

**File naming:**
```
articles/inspection-guides/{make}-{model}-inspection-guide.html

Examples:
- ford-focus-inspection-guide.html
- volkswagen-golf-inspection-guide.html
```

**CLI:**
```bash
# Generate single guide
python generate_inspection_guide.py --make FORD --model FOCUS

# Generate for top N most tested models
python generate_inspection_guide.py --top 50
```

---

## Success Criteria

- [ ] All 3 sections render correctly when data exists
- [ ] Sections omitted silently when data missing
- [ ] No derived/inferred data used
- [ ] No misleading language ("no concerns", "avoid", "target")
- [ ] Mobile-friendly layout
- [ ] Can generate guides for top 100 models

---

## Future Enhancements (Post-MVP)

Once MVP is validated, consider adding:

1. **Advisory progression** - Ranked list, no threshold filtering
2. **Mileage context** - Average mileage per year (direct from DB)
3. **Link to full model report** - Cross-reference
4. **PDF export** - Printable checklist

---

## Data Validation Completed

From investigation on 2026-01-16:

| Table | Ford Focus Records | Status |
|-------|-------------------|--------|
| `top_defects` (failures) | 440 | Excellent |
| `dangerous_defects` | 438 | Excellent |
| `vehicle_insights` | 44 variants, 21 years | Excellent |

All queries tested and returning expected data.
