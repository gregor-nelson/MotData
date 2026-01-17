# Known Issues Module - Folder Migration

## Objective

Consolidate all Known Issues components into a single dedicated folder.

## Target Location

`scripts/known-issues/`

## Files to Move

From `scripts/inspection_guide/`:
- `known_issues.py` - Core algorithm and data structures
- `known_issues_html.py` - HTML page generator
- `baseline_groups.py` - Defect-to-group pattern mapping

From `scripts/inspection_guide/specs/`:
- `SPEC.md` - Technical specification (Known Issues sections)

## Output Location

Articles will continue to output to:
`articles/known-issues/{make}-{model}-known-issues.html`

## Import Updates Required

After move, update imports in any files that reference:
- `from scripts.inspection_guide.known_issues import ...`
- `from scripts.inspection_guide.known_issues_html import ...`
- `from scripts.inspection_guide.baseline_groups import ...`

New imports will be:
- `from scripts.known_issues.known_issues import ...`
- `from scripts.known_issues.known_issues_html import ...`
- `from scripts.known_issues.baseline_groups import ...`

## New Folder Structure

```
scripts/known-issues/
  __init__.py
  known_issues.py
  known_issues_html.py
  baseline_groups.py
  specs/
    SPEC.md
```

## Notes

- Database path references remain unchanged (`data/source/data/mot_insights.db`)
- Inspection Guide module remains in `scripts/inspection_guide/` (separate concern)
