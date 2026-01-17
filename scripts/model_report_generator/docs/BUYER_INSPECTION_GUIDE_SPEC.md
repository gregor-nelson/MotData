# Buyer's Inspection Guide Generator - Specification

## Overview

A standalone HTML generator that creates actionable, mobile-friendly inspection guides for used car buyers. Unlike the comprehensive Model Report, this focuses purely on **what to check before purchasing** a specific make/model.

**Target Audience:** Used car buyers at the dealership or inspecting a private sale

**Key Differentiator:** Actionable checklist format vs data-heavy research document

---

## Goals

1. Help buyers know exactly what to inspect on a specific vehicle
2. Surface high-risk failure points that aren't obvious
3. Provide "walk away" red flags for safety-critical issues
4. Show mileage-based risk zones to set expectations
5. Identify best/worst model years to guide search

---

## File Structure

```
scripts/model_report_generator/
├── db_queries.py                    # ADD: _get_buyer_inspection_guide()
├── html_templates.py                # REUSE: existing components
├── tailwind_classes.py              # REUSE: existing classes
├── generate_model_report.py         # EXISTING: comprehensive reports
├── generate_inspection_guide.py     # NEW: lean inspection guide generator
└── docs/
    └── BUYER_INSPECTION_GUIDE_SPEC.md  # THIS FILE
```

---

## Data Requirements

All data already exists in `mot_insights.db`. New query function aggregates from:

| Source Table | Purpose in Guide |
|--------------|------------------|
| `top_defects` (type='failure') | Top 5 failure points to inspect |
| `component_mileage_thresholds` | Early failures (<60k) + mileage risk zones |
| `dangerous_defects` | Safety-critical "walk away" items |
| `advisory_progression` | Advisories likely to become failures |
| `vehicle_insights` | Year comparison for best/worst years |
| `failure_categories` | Category-level failure breakdown |

---

## New Database Query Function

### `_get_buyer_inspection_guide(conn, make: str, model: str) -> dict`

Returns a single dict with all inspection guide data:

```python
{
    "summary": {
        "total_tests": int,
        "pass_rate": float,
        "reliability_rating": str,  # "good" | "average" | "poor"
        "inspection_items_count": int
    },

    "top_failures": [
        {
            "defect_description": str,
            "category_name": str,
            "occurrence_count": int,
            "percentage_of_failures": float  # How common is this?
        }
        # Top 5 items
    ],

    "early_failures": [
        {
            "component": str,
            "failure_rate_0_30k": float,
            "failure_rate_30_60k": float,
            "risk_level": str  # "high" | "medium" | "low"
        }
        # Components with high failure rates under 60k miles
    ],

    "dangerous_defects": [
        {
            "defect_description": str,
            "category_name": str,
            "occurrence_count": int,
            "severity": "dangerous"
        }
        # All dangerous defects - safety critical
    ],

    "advisory_red_flags": [
        {
            "category_name": str,
            "advisory_count": int,
            "progression_rate": float,  # % that become failures
            "avg_days_to_failure": int,
            "avg_miles_to_failure": int
        }
        # Advisories with >30% progression rate
    ],

    "mileage_risk_zones": [
        {
            "mileage_band": str,  # "60k-90k"
            "components_at_risk": [str],  # ["Brakes", "Suspension"]
            "risk_description": str
        }
    ],

    "year_guidance": {
        "best_years": [
            {"year": int, "pass_rate": float, "total_tests": int}
        ],
        "worst_years": [
            {"year": int, "pass_rate": float, "total_tests": int}
        ],
        "years_to_avoid": [int],  # Pass rate significantly below model average
        "recommendation": str  # "Target 2017+ models"
    }
}
```

---

## HTML Output Structure

### Page Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Breadcrumb: Home > Guides > Ford > Focus]             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Ford Focus - Buyer's Inspection Guide                  │
│  ════════════════════════════════════════               │
│  Based on 245,000 MOT tests                             │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  AT A GLANCE                          🟢 GOOD   │   │
│  │                                                  │   │
│  │  Pass Rate: 74.2%    Items to Check: 12         │   │
│  │  Reliability: Above Average                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🔴 TOP 5 FAILURE POINTS                               │
│  ───────────────────────                               │
│  Check these first - most common reasons for failure    │
│                                                         │
│  1. Front brake pads worn                    (18.3%)   │
│  2. Rear lamp not working                    (12.1%)   │
│  3. Tyre tread below limit                   (9.8%)    │
│  4. Front suspension arm bush worn           (7.2%)    │
│  5. Windscreen wiper blade deteriorated      (5.4%)    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ⚠️ EARLY FAILURE WARNINGS                              │
│  ─────────────────────────                              │
│  Components that fail before 60,000 miles              │
│                                                         │
│  ┌──────────────────┬─────────────┬───────────────┐    │
│  │ Component        │ 0-30k Rate  │ 30-60k Rate   │    │
│  ├──────────────────┼─────────────┼───────────────┤    │
│  │ Brake pads       │ 4.2%        │ 12.8%         │    │
│  │ Suspension bush  │ 2.1%        │ 8.4%          │    │
│  │ Drive shaft boot │ 1.8%        │ 6.2%          │    │
│  └──────────────────┴─────────────┴───────────────┘    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🚨 SAFETY CRITICAL - WALK AWAY IF PRESENT             │
│  ──────────────────────────────────────────            │
│                                                         │
│  • Brake hose excessively deteriorated                 │
│  • Steering rack insecure                              │
│  • Structural corrosion affecting rigidity             │
│  • Suspension component fractured                       │
│                                                         │
│  These are dangerous defects - immediate fail items     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📉 ADVISORY RED FLAGS                                  │
│  ─────────────────────                                  │
│  If the vehicle has these advisories, budget for repair │
│                                                         │
│  • "Brake pipe corroded" → 68% become failures         │
│    Average 4,200 miles until failure                    │
│                                                         │
│  • "Suspension arm corroded" → 52% become failures     │
│    Average 8,100 miles until failure                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 MILEAGE RISK ZONES                                  │
│  ─────────────────────                                  │
│                                                         │
│  0-30k    Few issues expected                          │
│  30-60k   Watch: Brakes, tyres                         │
│  60-90k   Expect: Suspension bushes, brake discs       │
│  90-120k  Budget for: Exhaust, steering components     │
│  120k+    Major wear items likely needed               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📅 YEAR GUIDANCE                                       │
│  ────────────────                                       │
│                                                         │
│  ✅ Best Years: 2018 (78.2%), 2019 (77.8%), 2017      │
│  ❌ Avoid: 2012 (68.1%), 2013 (69.2%)                  │
│                                                         │
│  Recommendation: Target 2016+ models for best          │
│  reliability                                            │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ℹ️ About This Guide                                    │
│  Data from DVSA MOT tests. Analysis based on           │
│  245,000 tests across all Ford Focus variants.         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Sections Detail

### 1. At-a-Glance Summary

**Purpose:** Instant reliability verdict

**Visual:** Traffic light badge (🟢🟡🔴)
- 🟢 Good: Pass rate ≥75%
- 🟡 Average: Pass rate 65-74%
- 🔴 Poor: Pass rate <65%

**Data shown:**
- Overall pass rate
- Number of inspection items
- One-line reliability verdict

---

### 2. Top 5 Failure Points

**Purpose:** What to physically check first

**Data source:** `top_defects` WHERE `defect_type = 'failure'`

**Display:** Numbered list with percentage of all failures

**Logic:**
```sql
SELECT defect_description, category_name,
       SUM(occurrence_count) as total,
       SUM(occurrence_count) * 100.0 / (SELECT SUM(occurrence_count) FROM top_defects WHERE make=? AND model=? AND defect_type='failure') as percentage
FROM top_defects
WHERE make = ? AND model = ? AND defect_type = 'failure'
GROUP BY defect_description, category_name
ORDER BY total DESC
LIMIT 5
```

---

### 3. Early Failure Warnings

**Purpose:** Components that fail even on low-mileage vehicles

**Data source:** `component_mileage_thresholds`

**Display:** Table showing failure rates at 0-30k and 30-60k

**Filter:** Components where `failure_rate_0_30k > 2%` OR `failure_rate_30_60k > 5%`

**Logic:**
```sql
SELECT category_name,
       AVG(failure_rate_0_30k) as rate_0_30k,
       AVG(failure_rate_30_60k) as rate_30_60k
FROM component_mileage_thresholds
WHERE make = ? AND model = ?
GROUP BY category_name
HAVING rate_0_30k > 2 OR rate_30_60k > 5
ORDER BY rate_0_30k + rate_30_60k DESC
LIMIT 8
```

---

### 4. Safety Critical (Dangerous Defects)

**Purpose:** Immediate "walk away" red flags

**Data source:** `dangerous_defects`

**Display:** Bulleted list with warning styling

**Logic:**
```sql
SELECT defect_description, category_name, SUM(occurrence_count) as total
FROM dangerous_defects
WHERE make = ? AND model = ?
GROUP BY defect_description, category_name
ORDER BY total DESC
LIMIT 10
```

---

### 5. Advisory Red Flags

**Purpose:** Advisories that predict future failures

**Data source:** `advisory_progression`

**Display:** Advisory text + progression rate + estimated miles/days to failure

**Filter:** Progression rate > 30%

**Logic:**
```sql
SELECT category_name,
       SUM(advisory_count) as advisories,
       SUM(progressed_to_failure) as progressed,
       SUM(progressed_to_failure) * 100.0 / NULLIF(SUM(advisory_count), 0) as progression_rate,
       AVG(avg_days_to_failure) as avg_days,
       AVG(avg_miles_to_failure) as avg_miles
FROM advisory_progression
WHERE make = ? AND model = ?
GROUP BY category_name
HAVING progression_rate > 30
ORDER BY progression_rate DESC
LIMIT 6
```

---

### 6. Mileage Risk Zones

**Purpose:** Set expectations based on odometer reading

**Data source:** `component_mileage_thresholds`

**Display:** Horizontal timeline showing risk progression

**Logic:** Group components by which mileage band they most commonly fail in

```sql
-- Find peak failure band for each component
SELECT category_name,
       CASE
         WHEN failure_rate_150k_plus = MAX(failure_rate_0_30k, failure_rate_30_60k, failure_rate_60_90k, failure_rate_90_120k, failure_rate_120_150k, failure_rate_150k_plus) THEN '150k+'
         WHEN failure_rate_120_150k = MAX(...) THEN '120-150k'
         -- etc
       END as peak_failure_band
FROM component_mileage_thresholds
WHERE make = ? AND model = ?
GROUP BY category_name
```

---

### 7. Year Guidance

**Purpose:** Which model years to target/avoid

**Data source:** `vehicle_insights` via `_get_year_comparison()`

**Display:**
- Best 3 years with pass rates
- Worst 3 years with pass rates
- One-line recommendation

**Logic:**
```python
# Best years: Top 3 by pass rate (min 1000 tests)
# Worst years: Bottom 3 by pass rate (min 1000 tests)
# Years to avoid: Pass rate > 5% below model average
# Recommendation: "Target {year}+ models" based on when improvement started
```

---

## Reusable Components from html_templates.py

| Component | Use in Inspection Guide |
|-----------|------------------------|
| `generate_head()` | Page head with SEO |
| `generate_breadcrumb()` | Navigation |
| `generate_article_header()` | Title section |
| `generate_card()` | At-a-glance summary box |
| `generate_callout()` | Warning boxes (dangerous defects) |
| `generate_table()` | Early failures table |
| `generate_article_section()` | Section wrappers |

---

## New Components Needed

### 1. Traffic Light Badge

```python
def generate_reliability_badge(rating: str) -> str:
    """Generate traffic light reliability indicator."""
    # rating: "good" | "average" | "poor"
    colors = {
        "good": ("bg-emerald-100", "text-emerald-700", "🟢"),
        "average": ("bg-amber-100", "text-amber-700", "🟡"),
        "poor": ("bg-red-100", "text-red-700", "🔴")
    }
    # Returns styled badge HTML
```

### 2. Inspection Checklist Item

```python
def generate_checklist_item(rank: int, description: str, percentage: float) -> str:
    """Generate numbered checklist item with percentage."""
    # Returns: "1. Front brake pads worn (18.3%)"
```

### 3. Mileage Timeline

```python
def generate_mileage_timeline(risk_zones: list[dict]) -> str:
    """Generate horizontal mileage risk visualization."""
    # Visual timeline showing what to expect at each mileage band
```

### 4. Year Recommendation Card

```python
def generate_year_guidance_card(best: list, worst: list, recommendation: str) -> str:
    """Generate best/worst years with recommendation."""
```

---

## Output File Naming

```
articles/inspection-guides/{make}-{model}-inspection-guide.html

Examples:
- ford-focus-inspection-guide.html
- volkswagen-golf-inspection-guide.html
- vauxhall-corsa-inspection-guide.html
```

---

## CLI Interface

```bash
# Generate single guide
python generate_inspection_guide.py --make FORD --model FOCUS

# Generate for all models of a make
python generate_inspection_guide.py --make FORD --all

# Generate for top N most popular models
python generate_inspection_guide.py --top 50

# List available models
python generate_inspection_guide.py --list FORD
```

---

## Mobile Considerations

Since buyers may use this at a dealership:

1. **Single column layout** on mobile
2. **Large tap targets** for any interactive elements
3. **High contrast** text for outdoor readability
4. **Minimal scrolling** - most important info at top
5. **Print-friendly** - can print checklist to take along

---

## Implementation Steps

### Phase 1: Data Layer
1. Add `_get_buyer_inspection_guide()` to `db_queries.py`
2. Test with sample make/model
3. Verify all data sources return expected format

### Phase 2: Templates
1. Add new template functions to `html_templates.py`:
   - `generate_reliability_badge()`
   - `generate_checklist_item()`
   - `generate_mileage_timeline()`
   - `generate_year_guidance_card()`

### Phase 3: Generator
1. Create `generate_inspection_guide.py`
2. Implement section generators
3. Wire up CLI arguments
4. Test with Ford Focus, VW Golf, Vauxhall Corsa

### Phase 4: Polish
1. Mobile responsive testing
2. Print stylesheet
3. SEO metadata
4. Cross-link from model reports

---

## Success Criteria

- [ ] Guide loads in <1 second
- [ ] All sections render correctly
- [ ] Mobile-friendly layout
- [ ] Actionable information visible without scrolling
- [ ] Data matches source database
- [ ] Can generate guides for top 100 models

---

## Future Enhancements

1. **PDF export** - Downloadable checklist
2. **Interactive checklist** - Check items off as inspected
3. **Price context** - Average used prices from external source
4. **Comparison mode** - Side-by-side two models
5. **QR code** - Link to full model report

---

## Questions to Resolve

1. Should we include fuel type breakdown in the guide, or keep it simple?
2. Include regional data (some areas have more corrosion issues)?
3. Add estimated repair costs? (would need external data source)
4. Link to the full model report from each guide?

---

## Related Files

- [db_queries.py](../db_queries.py) - Data access layer
- [html_templates.py](../html_templates.py) - Reusable templates
- [tailwind_classes.py](../tailwind_classes.py) - Styling constants
- [generate_model_report.py](../generate_model_report.py) - Reference implementation
