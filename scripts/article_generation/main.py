#!/usr/bin/env python3
"""
Article Generation Pipeline - Main Entry Point
===============================================
Unified interface for generating MOT insights JSON and HTML articles.

Usage:
    python main.py                    # Interactive mode
    python main.py generate HONDA     # Generate JSON + HTML for HONDA
    python main.py generate-all       # Generate JSON + HTML for ALL makes
    python main.py list               # List all available makes
    python main.py explore            # Explore article opportunities
"""

import argparse
import subprocess
import sys
from pathlib import Path


# Project paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "database" / "mot_insights.db"
JSON_OUTPUT_DIR = DATA_DIR / "generated"
HTML_OUTPUT_DIR = PROJECT_ROOT / "articles" / "generated"


def get_available_makes() -> list[dict]:
    """Get list of available makes from database."""
    import sqlite3

    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    cur = conn.execute("""
        SELECT make, total_tests, avg_pass_rate, rank
        FROM manufacturer_rankings
        ORDER BY total_tests DESC
    """)

    makes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return makes


def display_makes(makes: list[dict], limit: int = 20):
    """Display available makes in a formatted table."""
    print(f"\n{'='*60}")
    print("  AVAILABLE VEHICLE MAKES")
    print(f"{'='*60}\n")
    print(f"  {'#':<4} {'Make':<20} {'Tests':>12} {'Pass Rate':>10}")
    print(f"  {'-'*48}")

    for i, m in enumerate(makes[:limit], 1):
        print(f"  {i:<4} {m['make']:<20} {m['total_tests']:>12,} {m['avg_pass_rate']:>9.1f}%")

    if len(makes) > limit:
        print(f"\n  ... and {len(makes) - limit} more makes available")
    print()


def prompt_for_make(makes: list[dict]) -> str:
    """Interactively prompt user to select a make."""
    display_makes(makes, limit=25)

    while True:
        try:
            choice = input("Enter make name or number (or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                print("Cancelled.")
                sys.exit(0)

            # Check if it's a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(makes):
                    return makes[idx]['make']
                else:
                    print(f"Invalid number. Please enter 1-{len(makes)}")
                    continue

            # Check if it's a valid make name
            make_upper = choice.upper()
            valid_makes = [m['make'] for m in makes]

            if make_upper in valid_makes:
                return make_upper

            # Try partial match
            matches = [m for m in valid_makes if make_upper in m]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"Multiple matches: {', '.join(matches)}")
                print("Please be more specific.")
                continue
            else:
                print(f"Make '{choice}' not found. Try again.")
                continue

        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def generate_json(make: str) -> Path:
    """Generate JSON insights for a make."""
    output_file = JSON_OUTPUT_DIR / f"{make.lower()}_insights.json"
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    script = SCRIPT_DIR / "json_parser" / "parser.py"

    print(f"\n  Generating JSON for {make}...")
    result = subprocess.run(
        [sys.executable, str(script), make, "--output", str(output_file), "--pretty"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return None

    if output_file.exists():
        print(f"  JSON saved: {output_file.name} ({output_file.stat().st_size:,} bytes)")
        return output_file

    return None


def generate_html(json_file: Path) -> Path:
    """Generate HTML article from JSON file."""
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    script = SCRIPT_DIR / "html_generator" / "generator.py"

    print(f"  Generating HTML article...")
    result = subprocess.run(
        [sys.executable, str(script), str(json_file), "--output", str(HTML_OUTPUT_DIR)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return None

    # Find the generated HTML file
    make = json_file.stem.replace("_insights", "")
    html_file = HTML_OUTPUT_DIR / f"{make}-most-reliable-models.html"

    if html_file.exists():
        print(f"  HTML saved: {html_file.name} ({html_file.stat().st_size:,} bytes)")
        return html_file

    # Try to find any recently created HTML
    html_files = sorted(HTML_OUTPUT_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        print(f"  HTML saved: {html_files[0].name}")
        return html_files[0]

    return None


def generate_article(make: str):
    """Generate both JSON and HTML for a make."""
    print(f"\n{'='*60}")
    print(f"  GENERATING ARTICLE: {make}")
    print(f"{'='*60}")

    # Step 1: Generate JSON
    json_file = generate_json(make)
    if not json_file:
        print("\n  Failed to generate JSON. Aborting.")
        return False

    # Step 2: Generate HTML
    html_file = generate_html(json_file)
    if not html_file:
        print("\n  Failed to generate HTML.")
        return False

    # Success summary
    print(f"\n{'='*60}")
    print(f"  SUCCESS!")
    print(f"{'='*60}")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")
    print(f"{'='*60}\n")

    return True


def run_explore():
    """Run the exploration script."""
    script = SCRIPT_DIR / "explore_article_opportunities.py"
    subprocess.run([sys.executable, str(script)])


def clean_output_folders():
    """Remove all generated JSON and HTML files from output folders."""
    import shutil

    cleaned = {"json": 0, "html": 0}

    # Clean JSON folder
    if JSON_OUTPUT_DIR.exists():
        for f in JSON_OUTPUT_DIR.glob("*_insights.json"):
            f.unlink()
            cleaned["json"] += 1

    # Clean HTML folder
    if HTML_OUTPUT_DIR.exists():
        for f in HTML_OUTPUT_DIR.glob("*-most-reliable-models.html"):
            f.unlink()
            cleaned["html"] += 1

    return cleaned


def generate_all_articles(min_tests: int = 0, dry_run: bool = False, no_clean: bool = False):
    """
    Generate JSON and HTML for all makes in the database.

    Args:
        min_tests: Minimum test count to include a make (default: 0 = all makes)
        dry_run: If True, only show what would be generated
        no_clean: If True, skip cleaning output folders before generation
    """
    import time

    makes = get_available_makes()

    # Filter by minimum tests if specified
    if min_tests > 0:
        makes = [m for m in makes if m['total_tests'] >= min_tests]

    total = len(makes)

    print(f"\n{'='*60}")
    print(f"  BATCH GENERATION: {total} MAKES")
    if min_tests > 0:
        print(f"  (filtered to makes with >= {min_tests:,} tests)")
    print(f"{'='*60}\n")

    if dry_run:
        print("  DRY RUN - No files will be generated\n")
        for i, m in enumerate(makes, 1):
            print(f"  {i:3}. {m['make']:<20} ({m['total_tests']:>10,} tests)")
        print(f"\n  Total: {total} makes would be generated")
        return

    # Clean output folders before generation (unless --no-clean specified)
    if not no_clean:
        print("  Cleaning output folders...")
        cleaned = clean_output_folders()
        print(f"  Removed {cleaned['json']} JSON files, {cleaned['html']} HTML files\n")

    # Track results
    results = {"success": [], "failed": []}
    start_time = time.time()

    for i, m in enumerate(makes, 1):
        make = m['make']
        print(f"\n[{i}/{total}] {make} ({m['total_tests']:,} tests)")
        print("-" * 40)

        try:
            # Generate JSON
            json_file = generate_json(make)
            if not json_file:
                print(f"  FAILED: Could not generate JSON")
                results["failed"].append(make)
                continue

            # Generate HTML
            html_file = generate_html(json_file)
            if not html_file:
                print(f"  FAILED: Could not generate HTML")
                results["failed"].append(make)
                continue

            results["success"].append(make)
            print(f"  OK")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["failed"].append(make)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  BATCH GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Success: {len(results['success'])}")
    print(f"  Failed:  {len(results['failed'])}")
    print(f"  Time:    {elapsed:.1f} seconds ({elapsed/total:.1f}s per make)")
    print(f"{'='*60}")

    if results["failed"]:
        print(f"\n  Failed makes:")
        for make in results["failed"]:
            print(f"    - {make}")

    print(f"\n  JSON output: {JSON_OUTPUT_DIR}")
    print(f"  HTML output: {HTML_OUTPUT_DIR}\n")

    return results


def interactive_mode():
    """Run in interactive mode with prompts."""
    print("\n" + "="*60)
    print("  MOT ARTICLE GENERATION PIPELINE")
    print("="*60)
    print("  This tool generates reliability articles from MOT data.")
    print("  It will create both JSON insights and an HTML article.")
    print("="*60)

    makes = get_available_makes()
    make = prompt_for_make(makes)

    print(f"\nYou selected: {make}")
    confirm = input("Generate article? [Y/n]: ").strip().lower()

    if confirm in ('', 'y', 'yes'):
        generate_article(make)
    else:
        print("Cancelled.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate MOT reliability articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Interactive mode
    python main.py generate HONDA     # Generate article for Honda
    python main.py generate TOYOTA    # Generate article for Toyota
    python main.py generate-all       # Generate ALL makes (cleans folders first)
    python main.py generate-all --min-tests 100000   # Only makes with 100k+ tests
    python main.py generate-all --dry-run            # Preview what would be generated
    python main.py generate-all --no-clean           # Keep existing files
    python main.py list               # List all available makes
    python main.py list --top 50      # List top 50 makes by test volume
    python main.py explore            # Explore article opportunities
        """
    )

    subparsers = parser.add_subparsers(dest="command")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate article for a make")
    gen_parser.add_argument("make", help="Vehicle make (e.g., HONDA, TOYOTA)")

    # generate-all command
    gen_all_parser = subparsers.add_parser("generate-all", help="Generate articles for ALL makes")
    gen_all_parser.add_argument("--min-tests", type=int, default=0,
                                help="Minimum test count to include a make (default: 0 = all)")
    gen_all_parser.add_argument("--dry-run", action="store_true",
                                help="Preview what would be generated without creating files")
    gen_all_parser.add_argument("--no-clean", action="store_true",
                                help="Skip cleaning output folders before generation")

    # list command
    list_parser = subparsers.add_parser("list", help="List available makes")
    list_parser.add_argument("--top", type=int, default=20, help="Number of makes to show")

    # explore command
    subparsers.add_parser("explore", help="Explore article opportunities")

    args = parser.parse_args()

    if args.command == "generate":
        generate_article(args.make.upper())
    elif args.command == "generate-all":
        generate_all_articles(min_tests=args.min_tests, dry_run=args.dry_run, no_clean=args.no_clean)
    elif args.command == "list":
        makes = get_available_makes()
        display_makes(makes, limit=args.top)
    elif args.command == "explore":
        run_explore()
    else:
        # No command - run interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
