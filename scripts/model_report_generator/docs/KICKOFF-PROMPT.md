# Model Report Generator: Continue Articles Pattern Implementation

## Task

Continue updating the Model Report Generator to use the **articles** styling pattern.

## Current Status

**Completed:** Stylesheet, scripts, footer, reading progress bar, body class, CTA section, container width, data badge CSS.

**Remaining:** Breadcrumb, article header, data source callout, key findings card, two-column layout with TOC, section wrappers, table classes.

## Read These Files

1. **Plan (with checklist):**
   `C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\PLAN-align-with-articles.md`

2. **HTML Reference:**
   `C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\REFERENCE-html-structure.md`

3. **Production Example:**
   `C:\Users\gregor\Downloads\Dev\motorwise.io\frontend\public\articles\content\reliability\aston-martin-most-reliable-models.html`

## Files to Modify

```
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\html_templates.py
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\generate_model_report.py
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\tailwind_classes.py
```

## Test Command

```bash
cd C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator
python generate_model_report.py BMW "3 SERIES"
```

## Instructions

1. Read the plan file to see completed vs remaining items
2. Reference the HTML structure doc for current→target patterns
3. Implement remaining items, testing after each change
