# Known Issues HTML Design Improvement - Kickoff Document

**Date:** 17 January 2026
**Purpose:** Brief for improving the Known Issues HTML pages from basic testing layout to premium insight presentation

---

## Context

The Known Issues system analyzes MOT test data to identify defects that occur at statistically elevated rates on specific vehicle models compared to national averages, same-age vehicles, and same-manufacturer vehicles.

This is a premium feature offering genuine statistical insight - not just raw data dumps. The HTML presentation should reflect this value.

---

## Current State

### Data Available Per Vehicle

The `KnownIssuesReport` provides:

1. **Grouped Component Issues** (primary insight)
   - Group name (e.g., "Brake Imbalance/Effort")
   - Category (e.g., "Brakes")
   - Ratio vs baseline (e.g., "3.4×")
   - Total occurrences across all variants
   - Number of MOT wording variants
   - List of actual MOT wording variants (expandable)
   - Typical mileage onset (optional)
   - Whether onset is premature for vehicle age
   - Affected model years (optional)

2. **Individual Ungrouped Issues** (secondary)
   - Same fields but for defects not matching component groups

3. **System Summary**
   - Category-level failure percentages
   - Comparison to national average
   - Flag if category is elevated

4. **Year Recommendations**
   - Best years to buy (highest pass rates)
   - Worst years to avoid (lowest pass rates)
   - Pass rate percentages and test counts

5. **Metadata**
   - Make/Model
   - Total MOT tests analyzed

### Current HTML Structure

Located in: `scripts/inspection_guide/known_issues_html.py`

Current sections in order:
1. Header with make/model and test count
2. Major Component Issues (red cards, 3×+ baseline)
3. Known Component Issues (amber cards, 2-3× baseline)
4. Elevated Components (collapsible list, 1.5-2× baseline)
5. Individual Major/Known/Elevated (for ungrouped defects)
6. System Summary (category bar chart)
7. Best/Worst Years
8. Methodology footer

### Current Styling

- Tailwind CSS via CDN
- Phosphor Icons
- Basic card layout with colored borders
- Expandable `<details>` for variant lists
- Simple responsive grid

---

## What Needs Improvement

### 1. Visual Hierarchy and Information Architecture

Current layout is flat - all sections appear equally important. Need clearer visual hierarchy that guides the user through:
- "What are the major concerns?" (immediate attention)
- "What else should I know?" (secondary)
- "How does this compare overall?" (context)
- "Which years are best?" (actionable recommendation)

### 2. Premium Feel

Current cards are functional but generic. Premium presentation should:
- Feel authoritative and data-driven
- Use whitespace effectively
- Have polished micro-interactions
- Present statistics in visually compelling ways

### 3. Data Visualization

Currently using basic text and simple bar widths. Opportunities:
- Ratio indicators that show severity visually
- Category comparison charts
- Year-over-year trend visualization
- Mileage onset timeline

### 4. Mobile Experience

Current responsive approach is basic. Need:
- Touch-friendly expandable sections
- Proper mobile card stacking
- Readable text at all sizes

### 5. User Journey

Consider the user's questions:
- "Is this car reliable?"
- "What will go wrong?"
- "When will it go wrong?"
- "Which year should I buy?"

Layout should answer these in logical order.

---

## Technical Constraints

1. **Static HTML** - No JavaScript frameworks, must work as standalone files
2. **Tailwind CDN** - Already in use, continue using
3. **Phosphor Icons** - Already in use for iconography
4. **No build process** - Generated HTML must be complete
5. **Print-friendly** - Users may print reports

---

## Reference Files

| File | Purpose |
|------|---------|
| `scripts/inspection_guide/specs/SPEC.md` | Full technical specification |
| `scripts/inspection_guide/known_issues.py` | Data structures and algorithm |
| `scripts/inspection_guide/known_issues_html.py` | Current HTML generator |
| `scripts/inspection_guide/baseline_groups.py` | Component grouping patterns |

---

## Example Data (Vauxhall Corsa)

```
Grouped Major Issues (3×+ baseline):
  4.7× | 789    | Passenger Seat
  4.0× | 21,288 | Steering Rack
  3.7× | 3,238  | Brake Pedal
  3.4× | 21,346 | Brake Imbalance/Effort (8 variants)
  3.1× | 971    | Brake Cable

Grouped Known Issues (2-3× baseline):
  2.8× | 3,281  | Tyre Mismatch
  2.8× | 3,200  | Brake Hydraulic
  2.5× | 3,991  | Fluid Leak
  2.4× | 24,940 | Shock Absorber
  2.3× | 67,521 | Spring

System Summary:
  Brakes: 12.3% (national: 8.1%) - ELEVATED
  Suspension: 18.7% (national: 14.2%) - ELEVATED
  Lights: 9.8% (national: 10.1%)

Best Years: 2019 (89%), 2020 (88%), 2018 (87%)
Worst Years: 2012 (71%), 2013 (73%), 2011 (74%)
```

---

## Deliverables Expected

1. **Design recommendations** - How to structure the page for maximum impact
2. **Visual treatment suggestions** - How to present ratios, comparisons, and recommendations
3. **Code changes to `known_issues_html.py`** - Updated generator functions

---

## Questions to Consider

1. Should grouped and ungrouped issues be visually distinct or integrated?
2. How prominent should the methodology/data source be?
3. Should there be a "summary verdict" at the top?
4. How to handle vehicles with few/no issues vs many issues?
5. What's the right balance between data density and readability?

---

*Document created 17 January 2026 for HTML design improvement session*
