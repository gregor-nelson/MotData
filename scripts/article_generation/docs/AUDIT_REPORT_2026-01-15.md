# Article Generation Pipeline Audit Report
**Date:** 2026-01-15
**Focus:** Output Accuracy & Data Correctness
**Scope:** `scripts/article_generation/` - JSON parser and HTML generator

---

## Executive Summary

The article generation pipeline was audited with focus on **data accuracy and correctness of generated articles**. The core methodology (v2.1 year-adjusted scoring, evidence-tiered durability) is sound and produces accurate results for typical cases. The main risks are edge cases where data is missing and fallbacks are silently applied.

| Category | Issues Found | Impact |
|----------|-------------|--------|
| Critical | 1 | Could show wrong comparisons for edge-case years |
| High | 4 | Empty sections, threshold inconsistencies |
| Medium | 3 | Hardcoded dates, unused data |
| Verified correct | Core methodology | Year-adjusted and age-band scoring working correctly |

---

## Critical Issues

### 1. Silent Fallback to Hardcoded National Average May Produce Incorrect Comparisons

**File:** `json_parser/parser.py` lines 368, 428-429, 458-459

```python
year_avg = yearly_avgs.get(data["model_year"], 71.51)
```

**Problem:** If a model year is missing from the `national_averages` table (e.g., 2024 data added later, or edge years), the code silently uses 71.51% instead. This would show vehicles as performing better/worse than they actually are relative to their year cohort.

**Example Impact:** A 2024 model with 85% pass rate would show "+13.5% vs national" even though the actual 2024 national average might be 88% (meaning it's actually -3% vs national).

**Affected Functions:**
- `get_model_family_year_breakdown()` - line 368
- `get_best_models()` - line 428
- `get_worst_models()` - line 458

**Recommendation:**
- Log a warning when fallback is used
- Include `fallback_used: true` in output JSON to make it visible
- Or raise an error for unexpected year ranges

**Verification Query:**
```sql
-- Check which years have national averages
SELECT DISTINCT model_year FROM national_averages
WHERE metric_name = 'yearly_pass_rate'
ORDER BY model_year;
```

---

## High Priority Issues

### 2. Durability Champions May Include Duplicate Entries for Same Model

**File:** `json_parser/parser.py` lines 679-727

```python
def get_durability_champions(conn, make: str, limit: int = 15) -> list:
    cur = conn.execute("""
        SELECT model, model_year, fuel_type, age_band, band_order, ...
        FROM age_bands
        WHERE make = ? AND band_order >= 4 AND total_tests >= ?
    """, (make, MIN_TESTS_PROVEN))
```

**Problem:** A single model/year/fuel combination can appear multiple times if it has data in both "11-12 years" (band_order=4) AND "13+ years" (band_order=5).

**Example Output:**
| Model | Year | vs National | Age Band |
|-------|------|-------------|----------|
| Jazz | 2010 | +12.3% | 11-12 years |
| Jazz | 2010 | +14.1% | 13+ years |

**Impact:** The "Proven Durability Champions" table shows what appears to be duplicate entries. This is technically correct (shows performance at different ages) but could confuse readers.

**Recommendation:** Either:
- Aggregate by model/year/fuel, showing best or average score
- Add explanatory text that models may appear at multiple age bands
- Group visually in the HTML output

---

### 3. Empty Sections Generated When No Data Available

**File:** `html_generator/components/sections.py` lines 272-276

```python
def generate_durability_section(insights: ArticleInsights) -> str:
    if not insights.has_proven_durability_data():
        if not insights.age_adjusted_best:
            return ""
        return _generate_durability_section_legacy(insights)
```

**Problem:** For makes with no proven durability data (newer brands like Tesla, Dacia with limited 11+ year history), the section either returns empty string or falls back to legacy methodology. The TOC still shows "Proven Durability Champions" link but it points to nothing.

**Affected Makes:** Any make without vehicles that have reached 11+ years in significant numbers.

**Impact:**
- Broken internal anchor links in TOC
- Confusing user experience (clicking link scrolls nowhere)

**Recommendation:**
- Hide TOC entries for empty sections dynamically
- Or show "Insufficient data for this make" message in the section
- Check in `layout.py generate_toc_html()` whether section has content

---

### 4. "vs National" in Best Models Section Uses Different Baseline Than Year-Adjusted Sections

**Files:**
- `html_generator/components/data_classes.py` line 459
- `html_generator/components/sections.py` line 205

**In Core Models parsing:**
```python
vs_nat = m.get('pass_rate', 0) - self.national_pass_rate  # Overall national avg (71.51%)
```

**In Best Models table header:**
```python
<th>vs National ({insights.national_pass_rate:.1f}%)</th>  # Shows 71.5%
```

**Problem:** The "Best Models by Pass Rate" section compares against the **overall** national average (71.5%), while year breakdown sections use **year-adjusted** averages. Both are correct but seem contradictory to readers.

**Example Confusion:**
- Best Models table: "Jazz 2020 Petrol: +16.5% vs national"
- Year Breakdown table: "Jazz 2020 Petrol: +0.3% vs same-year avg"

**Current Mitigation:** Headers are labeled differently ("vs National" vs "vs Same-Year Avg") and methodology section explains this.

**Recommendation:** Add a brief footnote to the Best Models section:
> "This comparison uses the overall 71.5% national average. For year-adjusted comparisons, see model breakdowns below."

---

### 5. Recommendations Section Uses Different Thresholds Than Other Sections

**File:** `html_generator/components/sections.py` lines 918, 930, 947

```python
# Nearly new threshold: >= 88% pass rate
if m.model not in seen_models and m.pass_rate >= 88:

# Used proven threshold: > 5% vs national at age
if m.model not in seen_models and m.vs_national_at_age > 5:

# Avoid threshold: < -5% vs national at age
if m.model not in seen_models and m.vs_national_at_age < -5:
```

**Other thresholds in codebase:**
- `data_classes.py`: 85% for "excellent" CSS class
- `data_classes.py`: 55% for "years to avoid" FAQ generation

**Problem:** A model could appear highlighted in "Best Models" table (85%+ gets green background) but not make the "Best Nearly New" recommendation list (requires 88%+).

**Impact:** Honda Jazz 2019 with 87% pass rate:
- ✅ Appears in Best Models table with green highlight
- ❌ Does NOT appear in "Best Nearly New" recommendations

**Recommendation:** Either:
- Align thresholds across sections
- Document the stricter criteria in recommendations section text
- Add explanatory note: "Only models exceeding 88% pass rate are recommended"

---

## Medium Priority Issues

### 6. Date Range "2000-2023" Is Hardcoded

**Files:**
- `html_generator/components/sections.py` line 51
- `html_generator/components/layout.py` lines 179, 201

```python
# sections.py
<p class="savings-text">Real DVSA data covering every {insights.title_make} model from 2000-2023</p>

# layout.py
"temporalCoverage": "2000/2023",
```

**Problem:** If database is updated with 2024+ data, articles will still display "2000-2023".

**Recommendation:**
- Derive date range from database metadata or JSON insights
- Add `year_range_start` and `year_range_end` to parser output
- Or create a config constant that's updated with database refreshes

---

### 7. Competitor Lists Are Manually Curated

**File:** `json_parser/parser.py` lines 188-231

```python
segments = {
    "HONDA": ["TOYOTA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
    "TOYOTA": ["HONDA", "MAZDA", "NISSAN", "HYUNDAI", "KIA", "SUZUKI"],
    # ... etc
}
default_competitors = ["FORD", "VAUXHALL", "VOLKSWAGEN", "TOYOTA", "NISSAN"]
```

**Problem:**
- New brands (MG, Cupra, Polestar, Genesis) fall back to default competitors
- Default competitors (mainstream European) may not be appropriate for all segments
- A luxury EV brand would be compared against Ford and Vauxhall

**Affected Makes:** Any make not in the `segments` dictionary.

**Recommendation:**
- Add missing makes to appropriate segments
- Or implement segment detection based on price/category data
- At minimum, add: MG, DACIA, CUPRA, DS, GENESIS, POLESTAR

---

### 8. Mileage Impact Data Is Collected But Never Displayed

**Files:**
- `json_parser/parser.py` lines 515-528 (generates data)
- `html_generator/components/data_classes.py` lines 540-542 (parses data)

```python
# Parser generates:
def get_mileage_impact(conn, make: str) -> list:
    """Get pass rate by mileage band for this make."""
    ...

# Data class stores:
def _parse_mileage(self, mileage_data: list):
    self.mileage_impact = mileage_data

# But NO section generator uses insights.mileage_impact
```

**Problem:** Useful data showing how mileage affects pass rates is calculated and stored but never rendered in articles.

**Sample Data Structure:**
```json
{
  "mileage_band": "60,000-80,000",
  "band_order": 3,
  "total_tests": 45000,
  "avg_pass_rate": 72.3
}
```

**Recommendation:** Either:
- Add a "Mileage Impact" section to articles
- Remove the unused code to reduce complexity
- Document why it's collected but not displayed

---

## Verified Correct

### Methodology v2.1 Implementation ✅

| Feature | Implementation | Status |
|---------|---------------|--------|
| Year-adjusted scoring | Uses `get_yearly_national_averages()` from database | ✅ Correct |
| Age-band comparisons | Uses `get_weighted_age_band_averages()` for durability | ✅ Correct |
| Evidence tiering | Separates proven (11+ years) from early (3-6 years) | ✅ Correct |
| Minimum test thresholds | 500 for proven, 1000 for early performers | ✅ Correct |
| Weighted averages | Correctly weights by test count in SQL | ✅ Correct |

### Data Flow Integrity ✅

| Stage | Verification |
|-------|-------------|
| Parser → JSON | All expected fields generated |
| JSON → DataClasses | All fields correctly mapped |
| DataClasses → Sections | Data accessed via proper properties |
| HTML escaping | `safe_html()` applied to user-visible text |

### Calculation Accuracy ✅

```python
# Pass rate calculation - CORRECT
ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 2) as pass_rate

# Weighted average - CORRECT
SUM(pass_rate * total_tests) / SUM(total_tests) as weighted_avg

# vs_national - CORRECT
data["pass_rate"] - year_avg  # or age_band_avg
```

---

## Additional Notes

### Model Family Aggregation Edge Cases

**File:** `json_parser/parser.py` lines 291-327

The logic for grouping model variants assumes variants start with base name + space:
```python
is_variant = any(model.startswith(core + " ") for core in core_names)
```

**Known behaviors:**
- ✅ "CIVIC TYPE R" correctly grouped under "CIVIC"
- ✅ "3 SERIES" correctly uses "3" as core (BMW)
- ⚠️ "320D" would NOT group under "3" (doesn't start with "3 ")
- ⚠️ "CR-V" vs "CRV" treated as separate (if both exist)

**Recommendation:** Verify output for BMW, Mercedes, Audi where alphanumeric model names are common.

### Hardcoded Constants to Review

| Constant | Location | Value | Purpose |
|----------|----------|-------|---------|
| `MIN_TESTS_PROVEN` | parser.py:67 | 500 | Minimum tests for proven durability |
| `MIN_TESTS_EARLY` | parser.py:68 | 1000 | Minimum tests for early performers |
| National avg fallback | parser.py:368 | 71.51 | Used when year avg missing |
| Excellent threshold | data_classes.py:30 | 85.0 | CSS class threshold |
| Recommendation threshold | sections.py:918 | 88.0 | Nearly-new recommendation cutoff |

---

## Investigation Checklist for Next Session

- [ ] Query database to verify which model years have national averages
- [ ] Test article generation for a newer make (Tesla, Polestar) to verify empty section handling
- [ ] Review generated HTML for BMW to check model family grouping
- [ ] Verify no actual incorrect data in sample generated articles
- [ ] Decide whether to add mileage impact section or remove unused code
- [ ] Update competitor lists with missing makes
- [ ] Consider adding date range to JSON metadata

---

## Files Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| `json_parser/parser.py` | 1247 | Database queries, JSON generation |
| `html_generator/generator.py` | 215 | Main orchestrator |
| `html_generator/components/data_classes.py` | 926 | Data structures, JSON parsing |
| `html_generator/components/sections.py` | 1038 | HTML section generators |
| `html_generator/components/layout.py` | 434 | HTML head, body, TOC, JSON-LD |
| `main.py` | 562 | CLI entry point |
