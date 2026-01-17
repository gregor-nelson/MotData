#!/usr/bin/env python3
"""
Known Issues Article Generator

Generates static HTML known issues pages for used car buyers.

Usage:
    python main.py --top 100                    # Generate for top 100 most-tested models
    python main.py --make FORD --model FOCUS   # Generate for single model
"""

import argparse
import shutil
import sqlite3
from pathlib import Path

from known_issues import generate_known_issues_report, DB_PATH
from known_issues_html import generate_known_issues_page

# Output directory (upstream web app)
OUTPUT_DIR = Path(r"C:\Users\gregor\Downloads\Dev\motorwise.io\frontend\public\articles\content\known-issues")


def get_top_models(limit: int) -> list[dict]:
    """Get top N models by total test count."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

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

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def generate_single_article(make: str, model: str) -> bool:
    """
    Generate known issues article for a single make/model.

    Returns:
        True if article was generated, False if skipped (no data)
    """
    report = generate_known_issues_report(make, model)

    if not report:
        print(f"  SKIP: No data for {make} {model}")
        return False

    html = generate_known_issues_page(report)

    # Create output filename
    safe_make = make.lower().replace(" ", "-")
    safe_model = model.lower().replace(" ", "-")
    filename = f"{safe_make}-{safe_model}-known-issues.html"

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write file
    output_path = OUTPUT_DIR / filename
    output_path.write_text(html, encoding="utf-8")

    tests_formatted = f"{report.total_tests:,}"
    issues_count = len(report.grouped_major_issues) + len(report.grouped_known_issues)
    print(f"  OK: {make} {model} ({tests_formatted} tests, {issues_count} issues) -> {filename}")

    return True


def clear_output_folder() -> int:
    """Fully empty the output folder. Returns count of items removed."""
    if not OUTPUT_DIR.exists():
        return 0

    removed = 0
    for item in OUTPUT_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        removed += 1
    return removed


def generate_top_n(n: int) -> None:
    """Generate articles for top N most-tested models."""
    # Clear existing files for clean run
    removed = clear_output_folder()
    if removed:
        print(f"Cleared {removed} existing files from {OUTPUT_DIR}\n")

    print(f"Fetching top {n} models by test count...")
    models = get_top_models(n)

    print(f"Found {len(models)} models. Generating known issues articles...\n")

    generated = 0
    skipped = 0

    for m in models:
        if generate_single_article(m["make"], m["model"]):
            generated += 1
        else:
            skipped += 1

    print(f"\nComplete: {generated} generated, {skipped} skipped")
    print(f"Output: {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate known issues articles from MOT data"
    )

    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="Generate articles for top N most-tested models"
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
        print(f"Generating known issues article for {args.make} {args.model}...")
        if generate_single_article(args.make, args.model):
            print("Done!")
        else:
            print("No article generated (insufficient data)")


if __name__ == "__main__":
    main()
