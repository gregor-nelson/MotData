# Handover: Dangerous Defects Article - HTML Generator

> **Task**: Create an HTML generator script that transforms the dangerous defects JSON insights into a styled article.

---

## Context

### What Was Created This Session

1. **Folder**: `scripts/dangerous_defects/`

2. **JSON Generator**: `generate_dangerous_defects_insights.py`
   - Generates comprehensive insights for "Most Dangerous Cars on UK Roads" article
   - Outputs `dangerous_defects_insights.json` (~280KB)
   - Run with: `python generate_dangerous_defects_insights.py --pretty`

3. **Sample Output**: `dangerous_defects_insights.json`
   - Already generated and ready to use as input

---

## Files to Reference

### Existing HTML Generator Pattern
```
C:\Users\gregor\Downloads\mot_data_2023\scripts\article_generation\generate_article_html.py
```
This is the existing HTML generator for per-make reliability articles. Review this file to understand:
- How JSON is parsed into dataclasses
- How HTML sections are generated
- Styling approach (Tailwind CSS)
- SEO meta tags and JSON-LD structure

### JSON Input Structure
```
C:\Users\gregor\Downloads\mot_data_2023\scripts\dangerous_defects\dangerous_defects_insights.json
```

Top-level keys in the JSON:
```
meta
key_findings
overall_statistics
category_breakdown
top_dangerous_defects
rankings
  - by_make
  - by_model
  - popular_cars_full_ranking
fuel_type_analysis
  - comparison
  - diesel_vs_petrol_same_model
age_controlled_analysis
used_car_buyer_guide
  - worst_to_avoid (2015_2017, 2018_2020)
  - safest_choices (2015_2017, 2018_2020)
category_deep_dives
  - brakes
  - steering
  - suspension
  - tyres
vehicle_deep_dives
  - NISSAN_QASHQAI
  - VAUXHALL_ZAFIRA
  - FORD_S-MAX
  - FORD_FOCUS
  - TOYOTA_PRIUS
  - MAZDA_MX-5
  - PORSCHE_911
  - LAND ROVER_DEFENDER
```

### Database Reference (if needed)
```
C:\Users\gregor\Downloads\mot_data_2023\docs\MOT_INSIGHTS_REFERENCE.md
```

### Project Overview
```
C:\Users\gregor\Downloads\mot_data_2023\docs\PROJECT_REFERENCE.md
```

---

## Key Data Points Available

From the investigation session:

- **16.1 million** dangerous defect occurrences
- **31.8 million** MOT tests analysed
- **330 models** ranked (100k+ tests each)
- **50 manufacturers** ranked (50k+ tests each)
- Rate range: **1.89%** (Jaguar I-PACE) to **7.81%** (Ford Focus C-MAX)
- Diesel vs Petrol gap: **+0.48%** higher for diesels
- Tyres account for **61.6%** of dangerous defects
- Brakes account for **37.2%**

---

## Task Requirements

Create: `generate_dangerous_defects_html.py`

The script should:
1. Read `dangerous_defects_insights.json` as input
2. Generate a styled HTML article
3. Output to `articles/generated/` or configurable path

The article content should provide detailed insights including drill-downs into defects, failures, and the various breakdowns available in the JSON.

---

## Running the JSON Generator

```bash
cd "C:\Users\gregor\Downloads\mot_data_2023"

# Generate fresh JSON (if needed)
python scripts/dangerous_defects/generate_dangerous_defects_insights.py --pretty

# View output summary
python -c "
import json
with open('scripts/dangerous_defects/dangerous_defects_insights.json') as f:
    data = json.load(f)
print('Keys:', list(data.keys()))
print('Makes ranked:', len(data['rankings']['by_make']))
print('Models ranked:', len(data['rankings']['popular_cars_full_ranking']))
"
```

---

## Session Updates

### 2026-01-03: HTML Generator Refactor + Insights Generator Fixes

**HTML Generator Refactored:**
- Original `generate_dangerous_defects_html.py` (1,447 lines) refactored into modular components
- Main script now 179 lines, imports from `components/` folder
- See `components/__init__.py` for all exports

**Insights Generator Fixes:**
- Fixed survivorship bias in all SQL queries (INNER JOIN -> LEFT JOIN)
- Fixed vehicle variant count to include fuel_type
- Fixed duplicate model years in deep dive
- Fixed diesel vs petrol gap calculation robustness
- See `CHANGELOG_2026-01-03.md` for full details

### 2026-01-03 (Session 2): Feature Alignment Audit & Fixes

**Audit Performed:** Verified bidirectional alignment between JSON generator and HTML components

**Issues Fixed (6 total):**
1. `by_model_year` - Added CSS bar chart to vehicle deep dives showing year-over-year rates
2. Hardcoded hybrid rate (`3.48%`) - Now calculated from `fuel_comparison` data
3. Hardcoded category percentages (`61.6%/37.2%`) - Now pulled from `insights.categories`
4. Hardcoded Prius rate (`3.24%`) - Now uses `prius.dangerous_rate`
5. Hardcoded difference factor (`4 times`) - Now uses `rate_difference_factor`
6. Missing `affected_models` column - Added to top defects table

**Result:** Reduced orphaned fields from 12 to 6, eliminated all hardcoded statistics

See `CHANGELOG_2026-01-03.md` for full details and remaining lower-priority items

**Component Structure:**
```
components/
  __init__.py          - Package exports
  utils.py             - Shared utilities (get_rate_class, format_number, safe_html, title_case)
  data_parser.py       - Dataclasses and DangerousDefectsInsights parser
  html_head.py         - HTML head with SEO meta tags and JSON-LD
  section_header.py    - Header, key findings, intro sections
  section_categories.py - Category breakdown section
  section_rankings.py  - Worst/safest models and manufacturer rankings
  section_fuel.py      - Fuel type analysis section
  section_buyer_guide.py - Used car buyer guide
  section_deep_dives.py - Vehicle deep dives, category deep dives, age-controlled analysis
  section_defects.py   - Top defects section
  section_faq.py       - FAQ section
  section_methodology.py - Methodology section
```

---

*End of Handover*
