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
