# Known Issues Feature: Handover Document

**Date:** 17 January 2026
**Status:** Proof of Concept Complete
**Purpose:** Transform MOT defect data from "data dumps" into actionable "known issues" intelligence

---

## Problem Statement

Current inspection guides list defects ranked by occurrence. This buries model-specific insights under universal wear items (tyres, bulbs, brake pads) that affect all vehicles equally.

**Goal:** Identify defects that represent design flaws, manufacturing weaknesses, or premature wear patterns unique to specific vehicles — essentially creating TSB-equivalent insights from MOT pattern analysis.

---

## Solution Implemented

### Core Algorithm

**Composite Baseline Comparison:**
```
Model Rate = defect_occurrences / model_total_tests × 100

Composite Baseline = (National rate × 50%) + (Same year rate × 30%) + (Same make rate × 20%)

Ratio = Model Rate / Composite Baseline
```

**Why these weights:**
- National (50%): Anchors to "all vehicles" as broadest reference
- Same Year (30%): Controls for age-related wear (fair comparison)
- Same Make (20%): Accounts for brand-level quality norms

**Severity Thresholds:**
| Ratio | Classification | Treatment |
|-------|---------------|-----------|
| < 1.5× | Normal | Not shown |
| 1.5× - 2× | Elevated | Collapsible "Worth Noting" |
| 2× - 3× | Known Issue | Amber cards |
| 3×+ | Major Known Issue | Red cards |

### Key Insight

The original code used `occurrence_percentage` from the database (percentage of failures), not percentage of tests. This made everything look average. **Fixed by calculating: occurrences ÷ total_tests × 100**

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/inspection_guide/known_issues.py` | Data processing, baseline calculation, scoring |
| `scripts/inspection_guide/known_issues_html.py` | HTML generation for new format |
| `articles/known-issues/*.html` | Sample output (Ford Focus, Vauxhall Corsa, BMW 3 Series) |

---

## Database Tables Used

| Table | Usage |
|-------|-------|
| `vehicle_insights` | Total tests per vehicle |
| `top_defects` | Defect occurrences and descriptions |
| `failure_categories` | Category-level breakdown |
| `component_mileage_thresholds` | Mileage spike detection |

### Underutilised Tables (Potential Value)

| Table | Potential |
|-------|-----------|
| `advisory_progression` | How advisories become failures — could predict future issues |
| `first_mot_insights` | Early-life failures — manufacturing quality signals |
| `mileage_bands` | Degradation curves — reliability over time |

---

## Current Output Structure

1. **Major Known Issues** — Red cards, 3×+ baseline
2. **Known Issues** — Amber cards, 2-3× baseline
3. **Worth Noting** — Collapsible list, 1.5-2× baseline
4. **System Summary** — Bar chart of category breakdown vs national
5. **Years to Consider** — Best/worst model years
6. **Methodology Footer** — Transparency for curious users

---

## Validated Results

| Vehicle | Major | Known | Elevated | Sample Issues |
|---------|-------|-------|----------|---------------|
| Ford Focus | 8 | 10 | 10 | Suspension fractures (6.2×), switch function (9.3×) |
| Vauxhall Corsa | 10 | 10 | 10 | Brake effort recording (8.9×), actuator corrosion (5.8×) |
| VW Golf | 3 | 10 | 10 | Bonnet latch (4.2×), EPS malfunction (3.6×) |
| BMW 3 Series | 10 | 10 | 10 | Brake hose deterioration (6.2×), wheel fractures (4.8×) |

---

## Known Limitations & Open Questions

### 1. Affected Years Logic
Currently flags years where defect rate is 20% above model average. May need refinement — some defects show single-year spikes that might be noise.

### 2. Mileage Context
Uses `component_mileage_thresholds.spike_mileage_band` for "typical onset" but this is category-level, not defect-specific. Some defects have no mileage data.

### 3. Defect Grouping
Related defects (e.g., "suspension arm worn", "suspension arm likely to detach") aren't grouped. Could consolidate for cleaner output.

### 4. Confidence Scoring
No sample-size weighting currently. A defect with 50 occurrences is treated same as 5,000. Could add confidence bands.

### 5. Universal Item Detection
Current approach filters by ratio (universal items stay ~1.0×). Works well but could be enhanced with statistical variance analysis.

### 6. Premium Value-Add Ideas
- Repair cost estimates (external data needed)
- "Fixed in year X" detection (compare early vs late model years)
- Cross-reference with actual recalls/TSBs
- Predictive: "If you see advisory X, expect failure in Y miles"

---

## Quick Start for Next Session

**Run the proof of concept:**
```bash
cd "c:\Users\gregor\Downloads\Mot Data"
python -m scripts.inspection_guide.known_issues
```

**Generate HTML for a vehicle:**
```python
from scripts.known_issues.known_issues import generate_known_issues_report
from scripts.known_issues.known_issues_html import generate_known_issues_page

report = generate_known_issues_report("FORD", "FOCUS")
html = generate_known_issues_page(report)
```

**Key data structures:**
- `KnownIssue` — Single issue with ratio, mileage, affected years
- `KnownIssuesReport` — Complete report with major/known/elevated lists
- `SystemSummary` — Category-level breakdown

---

## Reference Documents

- `main/specs/SPEC.md` — Full database schema (18 tables)
- `scripts/inspection_guide/db_queries.py` — Original query approach
- `scripts/inspection_guide/html_generator.py` — Original HTML generation

---

## Priority Questions for Next Session

1. **Threshold tuning** — Are 1.5×/2×/3× the right breakpoints?
2. **Defect consolidation** — Should related defects be grouped?
3. **Confidence indicators** — Show reliability of findings?
4. **Integration approach** — Replace existing guides or supplement?
5. **Premium differentiation** — What makes this "premium" vs free tier?
