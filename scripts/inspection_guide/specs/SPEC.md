# Inspection Guide Generator - Technical Specification

**Version:** 2.1
**Updated:** 2026-01-17

---

## Overview

Generates HTML buyer's guides from MOT insights data. The system has two main components:

1. **Inspection Guides** - Common failures, advisories, and year-by-year pass rates
2. **Known Issues** - Model-specific defects that occur at statistically elevated rates

---

## Module: Known Issues Detection

### Purpose

Identifies defects that occur significantly more often on a specific vehicle model compared to comparable vehicles (same age, same manufacturer, national average).

### Problem Solved: Defect Fragmentation (v2.0)

MOT defect descriptions have multiple wording variants for the same underlying issue:

| Variant | National Occurrences |
|---------|---------------------|
| "Brakes imbalance...less than 70%...same axle" | 166,073 |
| "Brakes imbalance...less than 50%...steered axle" | 24,844 |
| "Braking effort not recording at a wheel" | 13,287 |
| "Braking effort inadequate at a wheel" | 13,696 |
| **Total (all brake imbalance/effort)** | **243,712** |

**Previous behaviour (broken):** Each variant compared against its own narrow baseline, causing artificially inflated ratios (11.8x instead of 3.25x).

**New behaviour (v2.0):** Defects are aggregated by component group before comparison. The Vauxhall Corsa brake imbalance issue now correctly appears as a 3.4x major issue with 21,346 occurrences.

### Files

| File | Purpose |
|------|---------|
| `known_issues.py` | Core algorithm - generates KnownIssuesReport |
| `known_issues_html.py` | HTML page generator |
| `baseline_groups.py` | Pattern-based defect-to-group mapping (77 groups) |

### Data Structures

#### GroupedKnownIssue (NEW in v2.0)

```python
@dataclass
class GroupedKnownIssue:
    group_id: str                    # e.g., "brake_imbalance_effort"
    group_name: str                  # e.g., "Brake Imbalance/Effort"
    category_name: str               # e.g., "Brakes"
    model_rate: float                # Combined rate for all variants
    composite_baseline: float        # Grouped baseline rate
    ratio: float                     # model_rate / composite_baseline
    total_occurrences: int           # Sum of all variant occurrences
    variant_count: int               # Number of MOT wording variants
    variant_descriptions: list[str]  # Individual MOT wordings
    typical_mileage: Optional[str]
    is_premature: bool
    affected_years: Optional[list[int]]
```

#### KnownIssue (for ungrouped defects)

```python
@dataclass
class KnownIssue:
    defect_description: str
    category_name: str
    model_rate: float
    composite_baseline: float
    ratio: float
    occurrence_count: int
    baseline_group: Optional[str]    # Always None for ungrouped
    typical_mileage: Optional[str]
    is_premature: bool
    affected_years: Optional[list[int]]
```

#### KnownIssuesReport

```python
@dataclass
class KnownIssuesReport:
    make: str
    model: str
    total_tests: int

    # Grouped component issues (primary - v2.0)
    grouped_major_issues: list[GroupedKnownIssue]    # 3x+ baseline
    grouped_known_issues: list[GroupedKnownIssue]    # 2x-3x baseline
    grouped_elevated_items: list[GroupedKnownIssue]  # 1.5x-2x baseline

    # Individual issues (for ungrouped defects only)
    major_issues: list[KnownIssue]      # 3x+ baseline
    known_issues: list[KnownIssue]      # 2x-3x baseline
    elevated_items: list[KnownIssue]    # 1.5x-2x baseline

    # System-level summary
    system_summary: list[SystemSummary]

    # Year recommendations
    best_years: list[dict]
    worst_years: list[dict]
```

### Algorithm (v2.0)

```
1. Compute individual baselines (national, year, make)
2. Compute grouped baselines (sum rates by component group)
3. Get model defects from database
4. GROUPED DEFECTS:
   a. Aggregate model defects by component group
   b. For each group: compare grouped model rate vs grouped baseline
   c. Create GroupedKnownIssue for elevated groups (ratio >= 1.5)
5. UNGROUPED DEFECTS:
   a. For defects not matching any group pattern
   b. Compare individual model rate vs individual baseline
   c. Create KnownIssue for elevated items
6. Sort by ratio, return top 10 per tier
```

### Composite Baseline Formula

```
composite = (national_rate * 0.5) + (year_rate * 0.3) + (make_rate * 0.2)
```

- **50% National:** Overall frequency of this defect/group
- **30% Same Year:** Accounts for age-related wear
- **20% Same Make:** Accounts for manufacturer patterns

### Severity Thresholds

| Tier | Ratio | Description |
|------|-------|-------------|
| Major | 3.0x+ | Significantly above average |
| Known | 2.0x - 3.0x | Above average |
| Elevated | 1.5x - 2.0x | Slightly above average |

### Baseline Groups (baseline_groups.py)

Pattern-based mapping using regex:

```python
COMPONENT_PATTERNS = [
    (r'brake[s]?\s+imbalance|braking\s+effort', 'brake_imbalance_effort'),
    (r'shock\s+absorber', 'shock_absorber'),
    (r'wheel\s+bearing', 'wheel_bearing'),
    # ... 74 more patterns
]
```

**Coverage:**
- 317 defects (61%) assigned to 77 component groups
- 204 defects (39%) remain ungrouped (use individual baselines)

**Key groups:**

| Group ID | Variants | Description |
|----------|----------|-------------|
| brake_imbalance_effort | 8 | All brake imbalance/effort wording |
| shock_absorber | 5 | Shock absorber defects |
| wheel_bearing | 4 | Wheel bearing defects |
| suspension_bush_joint | 4 | Suspension bushes and joints |
| headlamp | 12 | Headlamp defects |
| parking_brake | 10 | Parking brake defects |

### HTML Output (known_issues_html.py)

Generates Tailwind CSS styled pages with:

1. **Grouped Major Issues** - Red cards with component name, ratio, occurrence count
2. **Grouped Known Issues** - Amber cards
3. **Grouped Elevated** - Collapsible list
4. **Other Major/Known Issues** - For ungrouped defects only (renamed from "Major/Known Issues" to distinguish from grouped)
5. **System Summary** - Category-level bar chart
6. **Best/Worst Years** - Pass rate recommendations

#### Card Layout (v2.1)

Each issue card shows data-driven insights in plain English:

```
┌─────────────────────────────────────────────────────────┐
│ [Icon] Brake Imbalance/Effort                    3.4×   │
│         Brakes                                          │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 1 in 41 Vauxhall Corsa MOT tests fail on this.     │ │
│ │ This is 3.4× the rate seen on comparable vehicles. │ │
│ │ 21,346 recorded failures in total                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 🔧 Usually occurs around 90,000 - 120,000 miles        │
│ 📅 Most affected years: 2004 - 2010                    │
├─────────────────────────────────────────────────────────┤
│ Recorded MOT failures (8 related types)                 │
│ • Brakes imbalance...less than 50%...steered axle      │
│ • Brakes imbalance...less than 70%...same axle         │
│ • Braking effort not recording at a wheel              │
│ + 5 more MOT failure descriptions [expandable]         │
└─────────────────────────────────────────────────────────┘
```

**Key presentation principles:**
- **"1 in X" format** - Converts percentage rate to intuitive frequency (e.g., 2.42% → "1 in 41")
- **Model context** - Uses vehicle name in explanation (e.g., "Vauxhall Corsa MOT tests")
- **Plain English comparison** - "This is X× the rate seen on comparable vehicles"
- **Variant visibility** - First 3 MOT failure descriptions shown, rest expandable
- **No inferred data** - Only displays data from database, no repair cost estimates or advice

### Usage

```python
from scripts.inspection_guide.known_issues import generate_known_issues_report
from scripts.inspection_guide.known_issues_html import generate_known_issues_page

report = generate_known_issues_report('VAUXHALL', 'CORSA')
html = generate_known_issues_page(report)
```

### Example Output (Vauxhall Corsa)

```
Grouped Major Issues:
  4.7x | 789    | Passenger Seat (1 variants)
  4.0x | 21,288 | Steering Rack (1 variants)
  3.7x | 3,238  | Brake Pedal (1 variants)
  3.4x | 21,346 | Brake Imbalance/Effort (8 variants)
  3.1x | 971    | Brake Cable (1 variants)

Grouped Known Issues:
  2.8x | 3,281  | Tyre Mismatch
  2.8x | 3,200  | Brake Hydraulic
  2.5x | 3,991  | Fluid Leak
  2.4x | 24,940 | Shock Absorber
  2.3x | 67,521 | Spring
```

---

## Module: Inspection Guides

### Scripts

| File | Purpose |
|------|---------|
| `generate.py` | CLI entry point, batch generation |
| `db_queries.py` | Database queries for guide data |
| `templates/` | Jinja2 HTML templates |

### Database Compatibility

**Required database:** `data/source/data/mot_insights.db`

**Version:** 2.1 (post-filter removal)

### Tables Used

| Table | Purpose |
|-------|---------|
| `vehicle_insights` | Total tests, pass rates by year |
| `top_defects` | Failures and advisories with counts |
| `dangerous_defects` | Safety-critical defects |
| `failure_categories` | Category-level failure percentages |
| `component_mileage_thresholds` | Mileage spike data |

### Key Schema Fields

```sql
-- top_defects
defect_description TEXT  -- Human-readable defect text
category_name TEXT       -- Component category
occurrence_count INTEGER -- Number of occurrences
defect_type TEXT        -- 'failure', 'advisory', 'minor'

-- dangerous_defects
defect_description TEXT
category_name TEXT
occurrence_count INTEGER
```

---

## Changes History

### v2.1 (2026-01-17) - HTML Presentation Improvements

**Problem:** Card layout displayed raw data without clear context. Users couldn't easily understand what "21,346 occurrences" meant or why "3.4×" was significant.

**Solution:** Rewrote card generators to present data in plain English:

1. Added `format_rate_as_one_in()` helper function
   - Converts percentage rate to "1 in X" format (e.g., 2.42% → "1 in 41")

2. Updated card layout with contextual explanation box:
   - "1 in 41 Vauxhall Corsa MOT tests fail on this issue"
   - "This is 3.4× the rate seen on comparable vehicles"
   - Total occurrence count as supporting detail

3. Made MOT variant descriptions prominent:
   - First 3 variants shown directly (not collapsed)
   - Remaining variants in expandable section

4. Renamed individual defect sections:
   - "Major Known Issues" → "Other Major Issues"
   - "Known Issues" → "Other Known Issues"
   - Prevents confusion with grouped component sections

5. Added make/model parameters to section generators for contextual text

**Files modified:**
- `known_issues_html.py` - Card layout and helper functions

**Design principle:** Only display data from database. No inferred repair costs, no fabricated advice, no abstract visualizations.

---

### v2.0 (2026-01-17) - Grouped Baseline Fix

**Problem:** Defect fragmentation caused genuine elevated issues to disappear. The Corsa had 21,346 brake imbalance occurrences (3.25x national average) but none appeared in output because each individual variant was compared against the grouped baseline.

**Solution:**
1. Added `GroupedKnownIssue` dataclass
2. Added `aggregate_model_defects_by_group()` function
3. Modified `generate_known_issues_report()` to process grouped defects first
4. Updated `KnownIssuesReport` with grouped issue fields
5. Added HTML generators for grouped issue cards
6. Updated page generator to show grouped issues prominently

**Files modified:**
- `known_issues.py` - Algorithm fix
- `known_issues_html.py` - HTML generation
- `baseline_groups.py` - Already existed, imported `get_group_display_name`

### v1.1 (2026-01-17)

**Removed:** `rfr_descriptions` JOIN that no longer exists in v2.1 database.

**Before (broken):**
```sql
SELECT COALESCE(rd.full_description, td.defect_description) ...
FROM top_defects td
LEFT JOIN rfr_descriptions rd ON td.rfr_id = rd.rfr_id
```

**After (working):**
```sql
SELECT td.defect_description ...
FROM top_defects td
```

---

## Usage

### Inspection Guides

```bash
# Generate guides for top N models by test count
python -m scripts.inspection_guide.generate --top 10

# Generate guide for specific vehicle
python -m scripts.inspection_guide.generate --make FORD --model FOCUS
```

Output: `articles/inspection-guides/{make}-{model}-inspection-guide.html`

### Known Issues

```bash
# Quick test
python -m scripts.inspection_guide.known_issues

# Generate HTML for specific vehicle
python -c "
from scripts.inspection_guide.known_issues import generate_known_issues_report
from scripts.inspection_guide.known_issues_html import generate_known_issues_page
from pathlib import Path

report = generate_known_issues_report('VAUXHALL', 'CORSA')
html = generate_known_issues_page(report)
Path('articles/known-issues/vauxhall-corsa-known-issues.html').write_text(html)
"
```

Output: `articles/known-issues/{make}-{model}-known-issues.html`

---

## Data Flow

### Inspection Guides

```
mot_insights.db
      |
      v
db_queries.py (get_inspection_guide_data)
      |
      v
generate.py (render template)
      |
      v
HTML file
```

### Known Issues

```
mot_insights.db
      |
      v
known_issues.py
  |-- compute_national_baselines()
  |-- compute_grouped_baselines()
  |-- aggregate_model_defects_by_group()
  |-- generate_known_issues_report()
      |
      v
KnownIssuesReport
      |
      v
known_issues_html.py
  |-- generate_grouped_issue_card()
  |-- generate_grouped_major_section()
  |-- generate_known_issues_page()
      |
      v
HTML file
```

---

## Related Documents

| Document | Location |
|----------|----------|
| Database spec | `main/specs/MOT_INSIGHTS_GENERATOR_SPEC.md` |
| Source data reference | `docs/MOT_DATA_REFERENCE.md` |
| Baseline grouping details | `docs/KNOWN_ISSUES_BASELINE_GROUPING.md` |
| Original problem analysis | `scripts/inspection_guide/reports/CONFIDENCE_SCORING_ANALYSIS.md` |
