# Handover: Dynamic Text Audit for Reliability Reports

**Date:** 2026-01-17
**Status:** Partially Complete
**File:** `scripts/reliabilty-reports/html_generator/components/sections.py`

---

## Summary of Problem

The reliability report generator was using **static, generic statements** that don't apply to all manufacturers. For example:

> "{Make} has built its reputation on reliability, but does the data back it up?"

This is **misleading** for brands like Lamborghini (exotic/performance brand), Ferrari, or Land Rover (known reliability issues). Premium reports require accuracy - every claim must be backed by data.

---

## Changes Completed

### 1. `generate_intro_section` - REFACTORED ✅

**Before:** Static text claiming all brands "built their reputation on reliability"

**After:** New `_get_dynamic_intro()` helper function that generates intro based on:
- **Sample size** (<5,000 tests = "limited data" caveat)
- **Moderate volume** (<20,000 tests = contextual positioning)
- **Rank position** (top 15 vs middle vs bottom)
- **vs_national** (above/below average determines tone)

**Examples of new output:**
- Lamborghini (2,905 tests): "With 2,905 MOT tests in the DVSA database, Lamborghini has limited test data..."
- Toyota (1.6M tests, above avg): "How reliable are Toyotas really? We analysed 1,606,300 real MOT tests..."
- Ford (below avg): "Ford ranks #51 out of 75 manufacturers, below the national average..."

### 2. `generate_competitors_section` - FIXED ✅

**Before:** Always ended with "However, newer {Make} models significantly outperform this average."

**After:** Removed this unverified claim. Verdict now ends after the factual comparison.

### 3. `generate_best_models_section` - FIXED ✅

**Before:** Any model ≥85% got "putting it among the most reliable cars in the database"

**After:**
- ≥90%: States actual pass rate and percentage points above national average
- ≥85% AND ≥10% vs national: "Leads {Make}'s lineup with an X% pass rate"
- Otherwise: No callout (avoids overclaiming)

### 4. `generate_fuel_analysis_section` - FIXED ✅

**Before:** "shows clear differences in reliability" (even with 1 fuel type or minimal differences)

**After:** New `_get_fuel_intro_text()` helper:
- 1 fuel type: "Here's how {Make} {fuel} models perform:"
- Multiple fuels, >5% difference: "Reliability varies by fuel type..."
- Multiple fuels, <5% difference: "Here's how {Make}'s fuel types compare:"

### 5. `generate_avoid_section` - FIXED ✅

**Before:** Always said "These vehicles fail MOTs more often than they pass"

**After:** New `_get_avoid_severity_text()` helper:
- <50% pass rate: "fail MOTs more often than they pass" (factually accurate)
- <60% pass rate: "significantly higher failure rates than average"
- ≥60%: "weakest performers in the lineup" (accurate for brands like Lamborghini where "worst" is still 92%)

---

## Audit Instructions for Next Session

### Objective
Complete a full audit of `sections.py` to ensure **all text is data-driven** with zero static blanket statements.

### Files to Review
- `scripts/reliabilty-reports/html_generator/components/sections.py`
- `scripts/reliabilty-reports/html_generator/components/data_classes.py` (for available data fields)

### Audit Checklist

For each section generator function, verify:

| Function | Status | Notes |
|----------|--------|-------|
| `generate_header_section` | 🔍 NEEDS AUDIT | Check "12 min read" - should be dynamic? |
| `generate_key_findings_section` | 🔍 NEEDS AUDIT | Review fallback text for missing data |
| `generate_intro_section` | ✅ DONE | Refactored with `_get_dynamic_intro()` |
| `generate_competitors_section` | ✅ DONE | Removed "newer models outperform" |
| `generate_best_models_section` | ✅ DONE | Tiered callout logic |
| `generate_durability_section` | 🔍 NEEDS AUDIT | Check "proven their durability" claims |
| `_generate_durability_section_legacy` | 🔍 NEEDS AUDIT | Legacy fallback - review claims |
| `generate_early_performers_section` | 🔍 NEEDS AUDIT | Verify caveat accuracy |
| `generate_model_breakdowns_section` | 🔍 NEEDS AUDIT | Check verdict generation logic |
| `generate_fuel_analysis_section` | ✅ DONE | Added `_get_fuel_intro_text()` |
| `generate_avoid_section` | ✅ DONE | Added `_get_avoid_severity_text()` |
| `generate_failures_section` | 🔍 NEEDS AUDIT | Check pre-MOT checklist generation |
| `generate_faqs_section` | 🔍 NEEDS AUDIT | Review FAQ answer generation |
| `generate_recommendations_section` | 🔍 NEEDS AUDIT | Check "Best If Buying" claims |
| `generate_methodology_section` | 🔍 NEEDS AUDIT | Static content - acceptable? |
| `generate_cta_section` | ⚪ STATIC OK | Marketing CTA - static is fine |

### Red Flags to Look For

1. **Superlatives without thresholds**: "dramatically outperforms", "among the best", "excellent"
2. **Assumptions about brand reputation**: Any text implying expected reliability
3. **Universal claims**: "all {Make} models", "every year", "always"
4. **Comparative claims without data**: "better than", "more reliable than" without checking
5. **Static text that should vary**: Same text regardless of actual data values

### Data Available for Dynamic Text

From `ArticleInsights`:
```python
insights.rank                    # Position 1-75
insights.rank_total              # Total manufacturers (75)
insights.vs_national             # Difference from 71.5% national avg
insights.avg_pass_rate           # Brand average
insights.total_tests             # Sample size
insights.reliability_summary.durability_rating  # "Excellent"/"Good"/"Average"/"Below Average"/"Insufficient Data"
insights.has_proven_durability_data()  # Boolean - has 11+ year data
```

### Testing Approach

After making changes, generate reports for these edge cases:
1. **Lamborghini** - Low volume, exotic, high pass rate
2. **Toyota** - High volume, above average, reliability reputation
3. **Land Rover** - High volume, below average, poor reputation
4. **Tesla** - Limited data, electric only
5. **Daewoo** - Discontinued brand, older data only

### Output Format for Changes

For each fix, document:
```
### [Function Name]
**Line:** X-Y
**Issue:** Static text that claims X
**Fix:** Dynamic logic based on [data field]
**Before:** "static text here"
**After:** Conditional logic description
```

---

## Key Principles

1. **Never assume reputation** - Let the data speak
2. **Acknowledge limitations** - Low sample sizes, missing data
3. **Use appropriate thresholds** - 90% is exceptional, 85% is good, 70% is average
4. **Context matters** - Lamborghini's "worst" at 92% is different from Ford's "worst" at 47%
5. **Avoid superlatives** - Unless data genuinely supports them

---

## Related Files

- `data/json/reliability-reports/*.json` - Sample insight files for testing
- `main/specs/SPEC.md` - Database schema reference
- `scripts/reliabilty-reports/main.py` - Entry point for generation
