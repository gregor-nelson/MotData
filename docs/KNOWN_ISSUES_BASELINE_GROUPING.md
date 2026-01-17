# Known Issues: Baseline Grouping Implementation

**Date:** 17 January 2026
**Status:** Implementation Complete - Awaiting Review
**Author:** Claude Code Session
**Purpose:** Document changes for developer review before production deployment

---

## Executive Summary

This session implemented **baseline grouping** to address the defect fragmentation problem identified in the confidence scoring analysis. The solution prevents artificially inflated ratios by comparing defects against a combined baseline of all related variants.

**Critical Decision Required:** The current implementation compares each individual defect against a grouped baseline. An alternative approach would aggregate the model's defects by group before comparison. See [Design Decision](#design-decision-required) section.

---

## Problem Statement

### The Fragmentation Issue

MOT defect descriptions have multiple wording variants for the same underlying issue:

| Variant | National Occurrences |
|---------|---------------------|
| "Brakes imbalance...less than 70%...same axle" | 166,073 |
| "Brakes imbalance...less than 50%...steered axle" | 24,844 |
| "Braking effort not recording at a wheel" | 13,287 |
| "Braking effort inadequate at a wheel" | 13,696 |
| **Total (all brake imbalance/effort)** | **243,712** |

### Previous Behaviour

Each defect variant was compared against its own narrow baseline:

```
Corsa "Braking effort not recording" occurrences: 4,231
National "Braking effort not recording" occurrences: 13,287
Corsa rate: 0.479%
National rate: 0.041%
Ratio: 11.8× ← INFLATED
```

### Corrected Behaviour

Defects are now compared against the combined baseline of all variants in their component group:

```
Corsa "Braking effort not recording" occurrences: 4,231
National ALL brake imbalance/effort occurrences: 243,712
Corsa rate: 0.479%
National rate: 0.743%
Ratio: 0.64× ← ACCURATE (this variant is below average)
```

---

## Files Modified

### Created

| File | Purpose |
|------|---------|
| `scripts/inspection_guide/baseline_groups.py` | Pattern-based defect-to-group mapping |
| `docs/KNOWN_ISSUES_BASELINE_GROUPING.md` | This document |

### Modified

| File | Changes |
|------|---------|
| `scripts/inspection_guide/known_issues.py` | Added grouped baseline calculation and usage |

---

## Implementation Details

### 1. Baseline Groups (`baseline_groups.py`)

Defines 77 component groups using regex patterns:

```python
COMPONENT_PATTERNS = [
    (r'brake[s]?\s+imbalance|braking\s+effort', 'brake_imbalance_effort'),
    (r'shock\s+absorber', 'shock_absorber'),
    (r'wheel\s+bearing', 'wheel_bearing'),
    # ... 74 more patterns
]
```

**Key function:**
```python
def get_baseline_group(defect_description: str) -> str | None:
    """Returns group name if defect matches a pattern, else None."""
```

**Coverage:**
- 319 defects assigned to 77 groups
- 204 defects remain ungrouped (use individual baselines)

### 2. Grouped Baseline Calculation (`known_issues.py`)

New function aggregates individual baselines into group baselines:

```python
def compute_grouped_baselines(individual_baselines: dict) -> dict:
    """
    For each defect in a group, sums the rates.
    Returns: {group_name: combined_rate_percentage}
    """
```

### 3. Modified Composite Baseline (`known_issues.py`)

Updated to use grouped baselines when available:

```python
def compute_composite_baseline(
    defect: str,
    national_baselines: dict,
    year_baselines: dict,
    make_baselines: dict,
    grouped_national: dict = None,  # NEW
    grouped_year: dict = None,      # NEW
    grouped_make: dict = None       # NEW
) -> tuple[float, Optional[str]]:   # NOW RETURNS GROUP NAME
```

### 4. KnownIssue Dataclass

Added `baseline_group` field for transparency:

```python
@dataclass
class KnownIssue:
    # ... existing fields ...
    baseline_group: Optional[str] = None  # NEW
```

---

## Design Decision Required

### Current Behaviour

Each **individual defect** is compared against the **grouped baseline**:

```
Individual Corsa defect rate → Compare to → Grouped national baseline
```

**Result for Vauxhall Corsa brake imbalance:**

| Variant | Corsa Rate | Grouped Baseline | Ratio |
|---------|------------|------------------|-------|
| "...less than 50%..." | 0.99% | 0.74% | 1.34× |
| "...less than 70%..." | 0.74% | 0.74% | 1.00× |
| "...not recording..." | 0.48% | 0.74% | 0.64× |

**Outcome:** None exceed 1.5× threshold. Brake imbalance issues **do not appear** in report.

### Alternative Approach

**Aggregate model defects by group** before comparison:

```
Grouped Corsa defect rate → Compare to → Grouped national baseline
```

| Group | Corsa Total | Corsa Rate | National Rate | Ratio |
|-------|-------------|------------|---------------|-------|
| brake_imbalance_effort | 21,346 | 2.42% | 0.74% | **3.25×** |

**Outcome:** Brake imbalance would appear as a 3.25× major issue, displayed as "Brake imbalance/effort issues".

### Trade-offs

| Aspect | Current (Individual) | Alternative (Grouped) |
|--------|---------------------|----------------------|
| Granularity | Shows each defect wording | Shows component group |
| Accuracy | Accurate per-variant | Accurate per-group |
| Captures distributed elevation | No | Yes |
| User sees exact MOT wording | Yes | No (grouped label) |

### Recommendation

The **alternative (grouped display)** approach may be more useful because:

1. Users care about "does this car have brake problems?" not "is this specific wording elevated?"
2. The Corsa genuinely has 3.25× more brake imbalance issues overall
3. Current approach may miss valid insights where elevation is spread across variants

However, this changes the nature of the output from granular defects to component summaries.

---

## Verification

### Test the Current Implementation

```bash
cd "c:\Users\gregor\Downloads\Mot Data"
python -c "
from scripts.inspection_guide.known_issues import generate_known_issues_report

report = generate_known_issues_report('VAUXHALL', 'CORSA')
print(f'Major issues: {len(report.major_issues)}')
for issue in report.major_issues[:5]:
    print(f'  {issue.ratio}x | {issue.defect_description[:50]}')
"
```

### Verify Grouping Coverage

```bash
python -c "
from scripts.inspection_guide.baseline_groups import analyze_groupings
import sqlite3
from pathlib import Path

db = Path('data/source/data/mot_insights.db')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
cursor = conn.execute('SELECT DISTINCT defect_description FROM top_defects WHERE defect_type=\"failure\"')
defects = [r[0] for r in cursor.fetchall()]

stats = analyze_groupings(defects)
print(f'Grouped: {stats[\"grouped_count\"]}')
print(f'Ungrouped: {stats[\"ungrouped_count\"]}')
"
```

### Compare Before/After for Specific Vehicle

```bash
# Calculate what the brake imbalance ratio SHOULD be (grouped)
python -c "
import sqlite3
from pathlib import Path

db = Path('data/source/data/mot_insights.db')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row

# National totals
cursor = conn.execute('SELECT SUM(total_tests) FROM vehicle_insights')
national_tests = cursor.fetchone()[0]

cursor = conn.execute('''
    SELECT SUM(occurrence_count) FROM top_defects
    WHERE defect_type=\"failure\"
    AND (defect_description LIKE \"%imbalance%\" OR defect_description LIKE \"%braking effort%\")
''')
national_brake = cursor.fetchone()[0]

# Corsa totals
cursor = conn.execute('SELECT SUM(total_tests) FROM vehicle_insights WHERE make=\"VAUXHALL\" AND model=\"CORSA\"')
corsa_tests = cursor.fetchone()[0]

cursor = conn.execute('''
    SELECT SUM(occurrence_count) FROM top_defects
    WHERE make=\"VAUXHALL\" AND model=\"CORSA\" AND defect_type=\"failure\"
    AND (defect_description LIKE \"%imbalance%\" OR defect_description LIKE \"%braking effort%\")
''')
corsa_brake = cursor.fetchone()[0]

corsa_rate = corsa_brake / corsa_tests * 100
national_rate = national_brake / national_tests * 100
ratio = corsa_rate / national_rate

print(f'Corsa brake imbalance: {corsa_brake:,} ({corsa_rate:.2f}%)')
print(f'National brake imbalance: {national_brake:,} ({national_rate:.2f}%)')
print(f'Grouped ratio: {ratio:.2f}x')
"
```

---

## Key Groups Affected

The following fragmented defect groups are now consolidated:

| Group | Variants | National Total |
|-------|----------|----------------|
| brake_imbalance_effort | 8 | 243,712 |
| shock_absorber | 5 | 360,300 |
| wheel_bearing | 4 | 162,309 |
| brake_hose | 8 | 84,047 |
| suspension_bush_joint | 4 | 1,812,934 |
| headlamp | 12 | 1,969,897 |
| parking_brake | 10 | 734,183 |
| stop_lamp | 7 | 734,076 |

---

## Rollback Instructions

To revert to the previous (fragmented) behaviour:

1. Remove the import in `known_issues.py`:
   ```python
   # from .baseline_groups import get_baseline_group, get_all_groups
   ```

2. Remove grouped baseline computation in `generate_known_issues_report()`:
   ```python
   # grouped_national = compute_grouped_baselines(national_baselines)
   # grouped_year = compute_grouped_baselines(year_baselines)
   # grouped_make = compute_grouped_baselines(make_baselines)
   ```

3. Revert `compute_composite_baseline()` call to not pass grouped baselines:
   ```python
   baseline = compute_composite_baseline(
       desc, national_baselines, year_baselines, make_baselines
   )
   # Note: also revert function signature and return type
   ```

---

## Open Questions for Review

1. **Should grouped defects be displayed as component groups or individual defects?**
   - Current: Individual defects, each compared to grouped baseline
   - Alternative: Aggregate into groups, display as "Brake imbalance issues (8 variants)"

2. **Is the pattern-based grouping accurate?**
   - Review `COMPONENT_PATTERNS` in `baseline_groups.py`
   - Check for false positives/negatives

3. **Should the grouped ratio be shown alongside individual ratios?**
   - e.g., "This specific defect: 1.3× | All brake imbalance: 3.2×"

4. **Are there groups that should NOT be combined?**
   - e.g., "brake hose" vs "brake pipe" - same or different?

---

## References

- Original analysis: `scripts/inspection_guide/reports/CONFIDENCE_SCORING_ANALYSIS.md`
- Handover doc: `scripts/inspection_guide/specs/KNOWN_ISSUES_HANDOVER.md`
- Algorithm code: `scripts/inspection_guide/known_issues.py`
- Grouping patterns: `scripts/inspection_guide/baseline_groups.py`

---

*Document created 17 January 2026*
