# Review Request: Known Issues Baseline Grouping

## Context

Work was done to address defect fragmentation in the Known Issues algorithm. The MOT database has multiple wording variants for the same defect (e.g., 8 variants of "brake imbalance"), which was causing artificially inflated ratios.

## What Was Done

- Created pattern-based grouping system (77 component groups)
- Modified baseline calculation to use grouped baselines
- Individual defects now compared against combined baseline of all related variants

## Critical Decision Needed

The implementation compares each individual defect against a grouped baseline. This means:

- Corsa "Braking effort not recording" (4,231 occurrences) compared to ALL brake imbalance nationally (243,712)
- Result: 0.64x ratio (not elevated)

But if we aggregate Corsa's brake imbalance defects first:
- Corsa ALL brake imbalance (21,346) vs National ALL brake imbalance (243,712)
- Result: 3.25x ratio (major issue)

**Which approach is correct for a premium product?**

## Documents to Review

1. **Full implementation details:**
   `docs/KNOWN_ISSUES_BASELINE_GROUPING.md`

2. **Original problem analysis:**
   `scripts/inspection_guide/reports/CONFIDENCE_SCORING_ANALYSIS.md`

3. **Code changes:**
   - `scripts/inspection_guide/baseline_groups.py` (new file - grouping patterns)
   - `scripts/inspection_guide/known_issues.py` (modified - uses grouped baselines)

## Quick Test

```bash
cd "c:\Users\gregor\Downloads\Mot Data"
python -c "
from scripts.inspection_guide.known_issues import generate_known_issues_report
report = generate_known_issues_report('VAUXHALL', 'CORSA')
print(f'Major: {len(report.major_issues)}, Known: {len(report.known_issues)}')
for i in report.major_issues[:3]:
    print(f'  {i.ratio}x | {i.defect_description[:50]}')
"
```

## Questions for Reviewer

1. Should grouped defects show as component groups or individual defects?
2. Are the 77 pattern-based groups correctly defined?
3. Should we show both individual and grouped ratios for transparency?
