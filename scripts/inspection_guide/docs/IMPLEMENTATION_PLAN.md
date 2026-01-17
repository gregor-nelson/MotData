# Buyer's Inspection Guide - Implementation Plan

> **For Coding Agent**: This is a complete implementation specification. Follow each step precisely. Do not deviate from the structure or add features not specified.

---

## Implementation Phases

This project is split into 4 phases. Each phase is self-contained and can be completed in a separate session.

| Phase | Description | Files Created | Checkpoint |
|-------|-------------|---------------|------------|
| **Phase 1** | Project setup & database layer | `__init__.py`, `db_queries.py` | Test queries return data |
| **Phase 2** | Tailwind classes & HTML templates | `tailwind_classes.py`, `html_generator.py` | Templates compile without error |
| **Phase 3** | CLI & main generator | `generate.py` | Can generate single file |
| **Phase 4** | Testing & validation | None (testing only) | All checklist items pass |

---

## Project Overview

Create a standalone HTML generator that produces actionable inspection guides for used car buyers based on MOT test data.

**Output**: Static HTML files at `articles/inspection-guides/{make}-{model}-inspection-guide.html`

**Philosophy**:
- Only show high-value, actionable insights
- No inferred or derived data
- No false reassurance ("no concerns identified")
- Quality over quantity

---

## File Structure to Create

```
scripts/inspection_guide/
├── __init__.py                 # Empty, makes it a package
├── generate.py                 # Main entry point with CLI
├── db_queries.py               # Database access functions
├── html_generator.py           # HTML generation functions
└── tailwind_classes.py         # Tailwind CSS class constants
```

**Output directory**: `articles/inspection-guides/` (create if not exists)

---

---

# PHASE 1: Project Setup & Database Layer

**Goal**: Create the project folder and database access functions.

**Files to create**:
- `scripts/inspection_guide/__init__.py`
- `scripts/inspection_guide/db_queries.py`

**Checkpoint**: Run the test script at the end of this phase to verify database queries work.

---

## Step 1.1: Create `__init__.py`

Create an empty package init file:

```python
"""Buyer's Inspection Guide Generator package."""
```

---

## Step 1.2: Create `db_queries.py`

**Database path**: `data/database/mot_insights.db` (relative to project root)

```python
"""Database queries for inspection guide generation."""

import sqlite3
from pathlib import Path

# Database path (relative to project root)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"


def get_db_connection():
    """Create read-only database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_inspection_guide_data(make: str, model: str) -> dict | None:
    """
    Fetch all data needed for buyer's inspection guide.
    Returns None if no data exists for the model.

    Args:
        make: Vehicle make (e.g., "FORD") - will be uppercased
        model: Vehicle model (e.g., "FOCUS") - will be uppercased

    Returns:
        Dict with keys: make, model, total_tests, top_failures,
        dangerous_defects, year_pass_rates
        Or None if model not found.
    """
    make = make.upper()
    model = model.upper()

    with get_db_connection() as conn:
        # Get total tests
        cursor = conn.execute("""
            SELECT SUM(total_tests) as total_tests
            FROM vehicle_insights
            WHERE make = ? AND model = ?
        """, (make, model))

        row = cursor.fetchone()
        if not row or row["total_tests"] is None:
            return None

        total_tests = row["total_tests"]

        # Get top 5 failures with percentage
        cursor = conn.execute("""
            SELECT
                defect_description,
                category_name,
                SUM(occurrence_count) as total_occurrences,
                ROUND(SUM(occurrence_count) * 100.0 /
                    (SELECT SUM(occurrence_count)
                     FROM top_defects
                     WHERE make = ? AND model = ? AND defect_type = 'failure'), 1) as percentage
            FROM top_defects
            WHERE make = ? AND model = ? AND defect_type = 'failure'
            GROUP BY defect_description, category_name
            ORDER BY total_occurrences DESC
            LIMIT 5
        """, (make, model, make, model))

        top_failures = [
            {
                "defect_description": r["defect_description"],
                "category_name": r["category_name"],
                "occurrence_count": r["total_occurrences"],
                "percentage": r["percentage"]
            }
            for r in cursor.fetchall()
        ]

        # Get dangerous defects (top 10)
        cursor = conn.execute("""
            SELECT
                defect_description,
                category_name,
                SUM(occurrence_count) as total_occurrences
            FROM dangerous_defects
            WHERE make = ? AND model = ?
            GROUP BY defect_description, category_name
            ORDER BY total_occurrences DESC
            LIMIT 10
        """, (make, model))

        dangerous_defects = [
            {
                "defect_description": r["defect_description"],
                "category_name": r["category_name"],
                "occurrence_count": r["total_occurrences"]
            }
            for r in cursor.fetchall()
        ]

        # Get year pass rates (sorted by pass_rate DESC, min 100 tests)
        cursor = conn.execute("""
            SELECT
                model_year,
                SUM(total_tests) as total_tests,
                ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
            FROM vehicle_insights
            WHERE make = ? AND model = ?
            GROUP BY model_year
            HAVING total_tests >= 100
            ORDER BY pass_rate DESC
        """, (make, model))

        year_pass_rates = [
            {
                "model_year": r["model_year"],
                "pass_rate": r["pass_rate"],
                "total_tests": r["total_tests"]
            }
            for r in cursor.fetchall()
        ]

        return {
            "make": make,
            "model": model,
            "total_tests": total_tests,
            "top_failures": top_failures,
            "dangerous_defects": dangerous_defects,
            "year_pass_rates": year_pass_rates
        }


def get_top_models(limit: int = 100) -> list[dict]:
    """
    Get top N models by total test count.

    Args:
        limit: Number of models to return

    Returns:
        List of dicts with make, model, total_tests
    """
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                make,
                model,
                SUM(total_tests) as total_tests
            FROM vehicle_insights
            GROUP BY make, model
            ORDER BY total_tests DESC
            LIMIT ?
        """, (limit,))

        return [
            {"make": r["make"], "model": r["model"], "total_tests": r["total_tests"]}
            for r in cursor.fetchall()
        ]
```

---

## Phase 1 Checkpoint

Run this test to verify the database layer works:

```bash
cd scripts/inspection_guide
python -c "
from db_queries import get_inspection_guide_data, get_top_models

# Test single model
data = get_inspection_guide_data('FORD', 'FOCUS')
print(f'Ford Focus: {data[\"total_tests\"]:,} tests')
print(f'  Top failures: {len(data[\"top_failures\"])}')
print(f'  Dangerous defects: {len(data[\"dangerous_defects\"])}')
print(f'  Year data: {len(data[\"year_pass_rates\"])} years')

# Test top models
top = get_top_models(5)
print(f'Top 5 models: {[m[\"make\"] + \" \" + m[\"model\"] for m in top]}')

print('PHASE 1 COMPLETE')
"
```

**Expected output**:
```
Ford Focus: 973,569 tests
  Top failures: 5
  Dangerous defects: 10
  Year data: 22 years
Top 5 models: ['FORD FOCUS', 'FORD FIESTA', 'VAUXHALL CORSA', ...]
PHASE 1 COMPLETE
```

**Stop here if needed. Phase 2 can be started in a new session.**

---
---

# PHASE 2: Tailwind Classes & HTML Templates

**Goal**: Create the styling constants and HTML generation functions.

**Files to create**:
- `scripts/inspection_guide/tailwind_classes.py`
- `scripts/inspection_guide/html_generator.py`

**Checkpoint**: Import html_generator and call functions without errors.

---

## Step 2.1: Create `tailwind_classes.py`

Copy the essential classes from `scripts/model_report_generator/tailwind_classes.py`. Only include what's needed for this simpler page:

```python
"""Tailwind CSS class constants for inspection guide generation."""

# Layout
CONTAINER = "max-w-4xl mx-auto px-4 py-6 sm:py-8 lg:py-12"

# Cards
CARD = "bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6"
CARD_HEADER = "px-5 py-4 border-b border-neutral-100 flex items-center justify-between"
CARD_TITLE = "text-lg font-semibold text-neutral-900"
CARD_BODY = "p-5"

# Tables
TABLE = "w-full text-sm"
TH = "py-3 px-4 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wide bg-neutral-50 border-b border-neutral-200"
TD = "py-3 px-4 border-b border-neutral-100 text-neutral-600"
TR_HOVER = "hover:bg-neutral-50 transition-colors duration-150"

# Typography
TEXT_MUTED = "text-sm text-neutral-500"

# Lists
LIST_ITEM = "flex justify-between py-2.5 border-b border-neutral-100 last:border-b-0 text-sm"
DEFECT_NAME = "flex-1 pr-4 text-neutral-700"
DEFECT_PERCENT = "font-semibold text-neutral-600"
DEFECT_CATEGORY = "text-xs text-neutral-400 mt-0.5"

# Numbered list for top failures
NUMBERED_ITEM = "flex gap-4 py-3 border-b border-neutral-100 last:border-b-0"
NUMBERED_BADGE = "flex-shrink-0 w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold"

# Callout (warning box for dangerous defects)
CALLOUT_WARNING = "rounded-xl p-4 bg-amber-50 border border-amber-200/50 mb-4"
CALLOUT_ICON = "text-amber-600 text-lg"
CALLOUT_TITLE = "font-semibold text-amber-800"
CALLOUT_TEXT = "text-sm text-amber-700 mt-1"

# Footer
FOOTER = "text-center py-6 text-neutral-400 text-xs border-t border-neutral-100 mt-8"

# Section divider
SECTION_HEADER = "flex items-center gap-3 mb-4"
SECTION_ICON_BOX = "w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center"
SECTION_ICON = "text-blue-600 text-lg"
SECTION_TITLE = "text-lg font-semibold text-neutral-900"
```

---

## Step 2.2: Create `html_generator.py`

```python
"""HTML generation functions for inspection guides."""

from datetime import date
from . import tailwind_classes as tw


def generate_head(make: str, model: str, safe_make: str, safe_model: str,
                  total_tests: str, today_iso: str) -> str:
    """Generate the complete <head> section with SEO metadata."""
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{make} {model} Buyer's Inspection Guide | Motorwise</title>
  <meta name="description" content="What to check before buying a used {make} {model}. Top MOT failure points and safety issues based on {total_tests} real test results.">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/articles/content/inspection-guides/{safe_make}-{safe_model}-inspection-guide.html">

  <!-- Open Graph -->
  <meta property="og:title" content="{make} {model} Buyer's Inspection Guide | Motorwise">
  <meta property="og:description" content="What to check before buying a used {make} {model}. Based on {total_tests} real MOT test results.">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Motorwise">

  <!-- Favicon -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            'sans': ['Jost', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>

  <!-- Phosphor Icons -->
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">

  <!-- Shared Styles -->
  <link rel="stylesheet" href="/articles/styles/articles.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <!-- Page Styles -->
  <style>
    @media (max-width: 767px) {{
      body {{
        background: linear-gradient(180deg, #EFF6FF 0%, #EFF6FF 60%, #FFFFFF 100%);
        min-height: 100vh;
      }}
    }}
  </style>

  <!-- JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} Buyer's Inspection Guide",
    "description": "What to check before buying a used {make} {model}",
    "author": {{ "@type": "Organization", "name": "Motorwise" }},
    "publisher": {{ "@type": "Organization", "name": "Motorwise" }},
    "datePublished": "{today_iso}",
    "dateModified": "{today_iso}"
  }}
  </script>
</head>"""


def generate_header(make: str, model: str, total_tests: str) -> str:
    """Generate page header with title and data source."""
    return f"""
    <header class="mb-8">
      <nav class="flex items-center gap-2 text-sm text-neutral-500 mb-6">
        <a href="/" class="hover:text-blue-600 transition-colors">Home</a>
        <i class="ph ph-caret-right text-xs"></i>
        <a href="/articles/content/index.html" class="hover:text-blue-600 transition-colors">Guides</a>
        <i class="ph ph-caret-right text-xs"></i>
        <span class="text-neutral-900">{make} {model}</span>
      </nav>

      <div class="flex flex-wrap items-center gap-3 mb-4">
        <span class="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-full border bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-600 border-blue-200/50">
          <i class="ph ph-magnifying-glass"></i>
          Buyer's Guide
        </span>
      </div>

      <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
        {make} {model} - Buyer's Inspection Guide
      </h1>
      <p class="text-lg text-neutral-600 leading-relaxed">
        Based on {total_tests} MOT tests
      </p>
    </header>"""


def generate_top_failures_section(failures: list[dict]) -> str:
    """Generate the Top 5 Failure Points section.

    Returns empty string if no failures data.
    """
    if not failures:
        return ""

    items_html = ""
    for i, f in enumerate(failures, 1):
        items_html += f"""
        <div class="{tw.NUMBERED_ITEM}">
          <span class="{tw.NUMBERED_BADGE}">{i}</span>
          <div class="flex-1">
            <div class="flex justify-between items-start">
              <span class="{tw.DEFECT_NAME}">{f['defect_description']}</span>
              <span class="{tw.DEFECT_PERCENT}">{f['percentage']}%</span>
            </div>
            <span class="{tw.DEFECT_CATEGORY}">Category: {f['category_name']}</span>
          </div>
        </div>"""

    return f"""
    <section class="{tw.CARD}">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-wrench {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Top 5 Failure Points</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        <p class="{tw.TEXT_MUTED} mb-4">The most common reasons this model fails its MOT</p>
        <div>{items_html}
        </div>
      </div>
    </section>"""


def generate_dangerous_defects_section(defects: list[dict]) -> str:
    """Generate the MOT History Check section for dangerous defects.

    Returns empty string if no dangerous defects data.
    """
    if not defects:
        return ""

    items_html = ""
    for d in defects:
        items_html += f"""
        <li class="{tw.LIST_ITEM}">
          <span class="{tw.DEFECT_NAME}">{d['defect_description']}</span>
          <span class="text-xs text-neutral-400">{d['category_name']}</span>
        </li>"""

    return f"""
    <section class="{tw.CARD}">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-warning {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">MOT History Check</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        <div class="{tw.CALLOUT_WARNING}">
          <div class="flex gap-3">
            <i class="ph ph-warning-circle {tw.CALLOUT_ICON}"></i>
            <div>
              <p class="{tw.CALLOUT_TITLE}">Check the vehicle's MOT history</p>
              <p class="{tw.CALLOUT_TEXT}">These are 'dangerous' defects that cause immediate MOT failure. If present in recent tests, investigate further before purchasing.</p>
            </div>
          </div>
        </div>
        <ul class="list-none">{items_html}
        </ul>
      </div>
    </section>"""


def generate_year_pass_rates_section(year_data: list[dict]) -> str:
    """Generate the Pass Rates by Year section.

    Returns empty string if no year data.
    """
    if not year_data:
        return ""

    rows_html = ""
    for y in year_data:
        tests_formatted = f"{y['total_tests']:,}"
        rows_html += f"""
        <tr class="{tw.TR_HOVER}">
          <td class="{tw.TD} font-medium text-neutral-900">{y['model_year']}</td>
          <td class="{tw.TD} font-semibold">{y['pass_rate']}%</td>
          <td class="{tw.TD}">{tests_formatted}</td>
        </tr>"""

    return f"""
    <section class="{tw.CARD}">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-calendar {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Pass Rates by Year</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        <p class="{tw.TEXT_MUTED} mb-4">MOT pass rates for each model year (sorted by best performance)</p>
        <div class="overflow-x-auto">
          <table class="{tw.TABLE}">
            <thead>
              <tr>
                <th class="{tw.TH}">Year</th>
                <th class="{tw.TH}">Pass Rate</th>
                <th class="{tw.TH}">Tests</th>
              </tr>
            </thead>
            <tbody>{rows_html}
            </tbody>
          </table>
        </div>
      </div>
    </section>"""


def generate_about_section(total_tests: str) -> str:
    """Generate the About This Data footer section."""
    return f"""
    <section class="bg-neutral-50 rounded-xl p-5 mt-8">
      <h2 class="text-sm font-semibold text-neutral-700 mb-2">About This Data</h2>
      <p class="text-sm text-neutral-500">
        Analysis based on {total_tests} MOT tests from DVSA records.
        Pass rates reflect MOT test outcomes only and may not represent overall vehicle reliability.
        Always conduct a thorough inspection and obtain a professional assessment before purchasing any used vehicle.
      </p>
    </section>"""


def generate_footer() -> str:
    """Generate page footer."""
    year = date.today().year
    return f"""
    <footer class="{tw.FOOTER}">
      <p>&copy; {year} Motorwise. Data sourced from DVSA MOT records.</p>
    </footer>"""


def generate_full_page(data: dict) -> str:
    """
    Generate the complete HTML page.

    Args:
        data: Dict from get_inspection_guide_data()

    Returns:
        Complete HTML string
    """
    make = data["make"].title()
    model = data["model"].title()
    safe_make = data["make"].lower().replace(" ", "-")
    safe_model = data["model"].lower().replace(" ", "-")
    total_tests = f"{data['total_tests']:,}"
    today_iso = date.today().isoformat()

    # Generate sections (empty string if no data)
    top_failures_html = generate_top_failures_section(data["top_failures"])
    dangerous_html = generate_dangerous_defects_section(data["dangerous_defects"])
    year_rates_html = generate_year_pass_rates_section(data["year_pass_rates"])

    # Check if we have ANY content
    has_content = any([top_failures_html, dangerous_html, year_rates_html])
    if not has_content:
        return ""  # Signal to skip this model

    return f"""<!DOCTYPE html>
<html lang="en">
{generate_head(make, model, safe_make, safe_model, total_tests, today_iso)}
<body class="bg-white font-sans text-neutral-900 antialiased">
  <div id="mw-header"></div>

  <main class="{tw.CONTAINER}">
    {generate_header(make, model, total_tests)}

    {top_failures_html}
    {dangerous_html}
    {year_rates_html}

    {generate_about_section(total_tests)}
  </main>

  {generate_footer()}

  <script src="/header/js/header.js"></script>
</body>
</html>"""
```

---

## Phase 2 Checkpoint

Run this test to verify the HTML generator works:

```bash
cd scripts/inspection_guide
python -c "
from db_queries import get_inspection_guide_data
from html_generator import generate_full_page

data = get_inspection_guide_data('FORD', 'FOCUS')
html = generate_full_page(data)

print(f'Generated HTML length: {len(html):,} characters')
print(f'Contains header: {\"Buyer\\'s Inspection Guide\" in html}')
print(f'Contains failures section: {\"Top 5 Failure Points\" in html}')
print(f'Contains dangerous section: {\"MOT History Check\" in html}')
print(f'Contains years section: {\"Pass Rates by Year\" in html}')

print('PHASE 2 COMPLETE')
"
```

**Expected output**:
```
Generated HTML length: ~15,000 characters
Contains header: True
Contains failures section: True
Contains dangerous section: True
Contains years section: True
PHASE 2 COMPLETE
```

**Stop here if needed. Phase 3 can be started in a new session.**

---
---

# PHASE 3: CLI & Main Generator

**Goal**: Create the command-line interface and file generation logic.

**Files to create**:
- `scripts/inspection_guide/generate.py`

**Checkpoint**: Generate a single HTML file successfully.

---

## Step 3.1: Create `generate.py` (Main Entry Point)

```python
#!/usr/bin/env python3
"""
Buyer's Inspection Guide Generator

Generates static HTML inspection guides for used car buyers.

Usage:
    python generate.py --top 100          # Generate for top 100 most-tested models
    python generate.py --make FORD --model FOCUS   # Generate for single model
"""

import argparse
from pathlib import Path

from .db_queries import get_inspection_guide_data, get_top_models
from .html_generator import generate_full_page

# Output directory (relative to project root)
OUTPUT_DIR = Path(__file__).parent.parent.parent / "articles" / "inspection-guides"


def generate_single_guide(make: str, model: str) -> bool:
    """
    Generate inspection guide for a single make/model.

    Returns:
        True if guide was generated, False if skipped (no data)
    """
    data = get_inspection_guide_data(make, model)

    if not data:
        print(f"  SKIP: No data for {make} {model}")
        return False

    html = generate_full_page(data)

    if not html:
        print(f"  SKIP: No content sections for {make} {model}")
        return False

    # Create output filename
    safe_make = make.lower().replace(" ", "-")
    safe_model = model.lower().replace(" ", "-")
    filename = f"{safe_make}-{safe_model}-inspection-guide.html"

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write file
    output_path = OUTPUT_DIR / filename
    output_path.write_text(html, encoding="utf-8")

    tests_formatted = f"{data['total_tests']:,}"
    print(f"  OK: {make} {model} ({tests_formatted} tests) -> {filename}")

    return True


def generate_top_n(n: int) -> None:
    """Generate guides for top N most-tested models."""
    print(f"Fetching top {n} models by test count...")
    models = get_top_models(n)

    print(f"Found {len(models)} models. Generating guides...\n")

    generated = 0
    skipped = 0

    for m in models:
        if generate_single_guide(m["make"], m["model"]):
            generated += 1
        else:
            skipped += 1

    print(f"\nComplete: {generated} generated, {skipped} skipped")
    print(f"Output: {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate buyer's inspection guides from MOT data"
    )

    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="Generate guides for top N most-tested models"
    )
    parser.add_argument(
        "--make",
        type=str,
        help="Vehicle make (e.g., FORD)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Vehicle model (e.g., FOCUS)"
    )

    args = parser.parse_args()

    # Validate args
    if args.top and (args.make or args.model):
        parser.error("Cannot use --top with --make/--model")

    if (args.make and not args.model) or (args.model and not args.make):
        parser.error("--make and --model must be used together")

    if not args.top and not args.make:
        parser.error("Must specify either --top N or --make/--model")

    # Execute
    if args.top:
        generate_top_n(args.top)
    else:
        print(f"Generating guide for {args.make} {args.model}...")
        if generate_single_guide(args.make, args.model):
            print("Done!")
        else:
            print("No guide generated (insufficient data)")


if __name__ == "__main__":
    main()
```

---

## Phase 3 Checkpoint

Run these tests to verify the CLI works:

```bash
cd scripts/inspection_guide

# Test 1: Generate single guide
python -m generate --make FORD --model FOCUS

# Verify file was created
dir ..\..\articles\inspection-guides\ford-focus-inspection-guide.html
```

**Expected output**:
```
Generating guide for FORD FOCUS...
  OK: FORD FOCUS (973,569 tests) -> ford-focus-inspection-guide.html
Done!
```

```bash
# Test 2: Test invalid model (should skip gracefully)
python -m generate --make FAKE --model NOTEXIST
```

**Expected output**:
```
Generating guide for FAKE NOTEXIST...
  SKIP: No data for FAKE NOTEXIST
No guide generated (insufficient data)
```

**Stop here if needed. Phase 4 can be started in a new session.**

---
---

# PHASE 4: Testing & Validation

**Goal**: Run full test suite and verify all success criteria.

**Files to create**: None (testing only)

**Checkpoint**: All checklist items pass.

---

## Step 4.1: Batch Generation Test

```bash
cd scripts/inspection_guide
python -m generate --top 10
```

- [ ] Generates 10 files (or fewer if some models lack data)
- [ ] Console output shows generated/skipped counts
- [ ] Files appear in `articles/inspection-guides/`

---

## Step 4.2: Visual Inspection

Open `articles/inspection-guides/ford-focus-inspection-guide.html` in a browser:

- [ ] Header shows "Ford Focus - Buyer's Inspection Guide"
- [ ] Header shows test count with comma formatting (e.g., "973,569")
- [ ] Top 5 Failure Points section renders with numbered list
- [ ] MOT History Check section renders with warning callout
- [ ] Pass Rates by Year table renders, sorted by pass rate (best first)
- [ ] About This Data footer section present

---

## Step 4.3: Mobile Responsiveness

Resize browser to mobile width (~375px):

- [ ] Layout remains readable
- [ ] Table scrolls horizontally if needed
- [ ] No horizontal page overflow

---

## Step 4.4: Content Validation

Check the generated HTML does NOT contain:

- [ ] No "no concerns" or "all clear" messages anywhere
- [ ] No "target" or "avoid" recommendations
- [ ] No traffic light colors (red/amber/green badges) on pass rates

Check the generated HTML DOES contain:

- [ ] Percentages shown for failures (e.g., "18.3%")
- [ ] Test counts formatted with commas (e.g., "973,569")
- [ ] Years sorted by pass rate descending (best first)

---

## Phase 4 Complete

All tests pass? Project is complete.

---
---

# REFERENCE SECTION

## Important Constraints

1. **Do NOT** add features not in this spec
2. **Do NOT** add traffic light ratings, recommendations, or derived insights
3. **Do NOT** import from `scripts/model_report_generator/` - this is standalone
4. **Do NOT** add comments like "no concerns" or "all clear" for empty data
5. **DO** skip file generation entirely if all 3 sections would be empty
6. **DO** format numbers with commas (e.g., "245,000")
7. **DO** use Title Case for make/model in display (e.g., "Ford Focus")
8. **DO** use lowercase-hyphenated for filenames (e.g., "ford-focus")

---

## Database Schema Reference

Tables used by this generator:

### `vehicle_insights`
```sql
- make TEXT
- model TEXT
- model_year INTEGER
- fuel_type TEXT
- total_tests INTEGER
- total_passes INTEGER
- pass_rate REAL
```

### `top_defects`
```sql
- make TEXT
- model TEXT
- defect_description TEXT
- category_name TEXT
- defect_type TEXT ('failure' or 'advisory')
- occurrence_count INTEGER
```

### `dangerous_defects`
```sql
- make TEXT
- model TEXT
- defect_description TEXT
- category_name TEXT
- occurrence_count INTEGER
```

---

## Final Success Criteria Summary

| Criteria | Phase to Verify |
|----------|-----------------|
| All 3 sections render correctly when data exists | Phase 4.2 |
| Sections omitted silently when data missing | Phase 3 checkpoint |
| No file generated if ALL sections empty | Phase 3 checkpoint |
| No derived/inferred data used | Phase 4.4 |
| No misleading language | Phase 4.4 |
| Mobile-friendly layout | Phase 4.3 |
| Can run `--top 100` without errors | Phase 4.1 |
| Output files appear in `articles/inspection-guides/` | Phase 4.1 |
