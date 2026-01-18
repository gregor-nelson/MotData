#!/usr/bin/env python3
"""
HTML Article Generator - Main Orchestrator
==========================================
Generates styled HTML articles from MOT insights JSON data.

Usage:
    python generator.py honda_insights.json
    python generator.py honda_insights.json --output ./articles/
    python generator.py --all
    python generator.py honda_insights.json --test
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Handle imports for both module and script execution
if __name__ == "__main__":
    # Running as script - add parent directories to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from html_generator.components import (
        ArticleInsights,
        parse_insights,
        format_number,
        generate_html_head,
        generate_html_body,
    )
else:
    # Running as module
    from .components import (
        ArticleInsights,
        parse_insights,
        format_number,
        generate_html_head,
        generate_html_body,
    )


# =============================================================================
# Path Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_DIR / "data" / "json" / "reliability-reports"  # JSON insights files
OUTPUT_DIR = PROJECT_DIR / "articles" / "reliability-reports"  # HTML output


# =============================================================================
# Article Generation
# =============================================================================

def generate_article(insights: ArticleInsights) -> str:
    """
    Generate styled HTML article from parsed insights.

    Args:
        insights: Parsed ArticleInsights object

    Returns:
        Complete HTML string for the article matching the reference template
    """
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    # Windows doesn't support %-d, so we format and strip leading zero manually
    day = str(now.day)
    month_year = now.strftime("%b %Y")
    time_str = now.strftime("%H:%M")
    today_display = f"{day} {month_year} at {time_str}"

    # Build the complete HTML document
    html = generate_html_head(insights, today)
    html += generate_html_body(insights, today_display)

    return html


def generate_filename(make: str) -> str:
    """Generate SEO-friendly filename."""
    slug = make.lower().replace(' ', '-').replace('_', '-')
    return f"{slug}-most-reliable-models.html"


# =============================================================================
# Testing & CLI
# =============================================================================

def test_parser(json_path: Path):
    """Test the parser and print key insights."""
    print(f"\n{'='*60}")
    print(f"Testing parser with: {json_path.name}")
    print('='*60)

    insights = parse_insights(json_path)

    # Summary stats
    stats = insights.summary_stats()
    print(f"\n[Summary]")
    print(f"  Make: {stats['title_make']}")
    print(f"  Total Tests: {stats['total_tests_formatted']}")
    print(f"  Pass Rate: {stats['avg_pass_rate']:.1f}%")
    print(f"  Rank: #{stats['rank']} of {stats['rank_total']}")
    print(f"  vs National: {stats['vs_national_formatted']}")
    best_rate = stats['best_model_pass_rate']
    worst_rate = stats['worst_model_pass_rate']
    best_display = f"{best_rate:.1f}%" if best_rate is not None else "N/A"
    worst_display = f"{worst_rate:.1f}%" if worst_rate is not None else "N/A"
    print(f"  Best Model: {stats['best_model']} ({best_display})")
    print(f"  Worst Model: {stats['worst_model']} ({worst_display})")

    # Competitors
    print(f"\n[Competitors] ({len(insights.competitors)} total)")
    for c in insights.competitors[:5]:
        marker = " <--" if c.is_current else ""
        print(f"  #{c.rank} {c.make}: {c.pass_rate:.1f}% ({format_number(c.total_tests)} tests){marker}")

    # Top models
    print(f"\n[Top Models by Pass Rate]")
    for m in insights.top_models[:5]:
        print(f"  {m.name}: {m.pass_rate:.1f}% ({format_number(m.total_tests)} tests, {m.year_from}-{m.year_to})")

    # Models for breakdown
    print(f"\n[Models for Year-by-Year Breakdown] (>10k tests)")
    breakdown_models = insights.get_models_for_breakdown(min_tests=10000, limit=5)
    for m in breakdown_models:
        print(f"  {m.name}: {format_number(m.total_tests)} tests, {len(m.year_breakdowns)} year entries")
        # Show a few year entries
        for y in m.year_breakdowns[:3]:
            print(f"    - {y.model_year} {y.fuel_name}: {y.pass_rate:.1f}%")
        if len(m.year_breakdowns) > 3:
            print(f"    ... and {len(m.year_breakdowns) - 3} more")

    # Fuel analysis
    print(f"\n[Fuel Analysis]")
    for f in insights.fuel_analysis:
        print(f"  {f.fuel_name}: {f.pass_rate:.1f}% ({format_number(f.total_tests)} tests)")

    # Best models
    print(f"\n[Best Model/Year Combinations]")
    for m in insights.best_models[:5]:
        print(f"  {m.model} {m.model_year} {m.fuel_name}: {m.pass_rate:.1f}%")

    # Worst models
    print(f"\n[Worst Model/Year Combinations]")
    for m in insights.worst_models[:5]:
        print(f"  {m.model} {m.model_year} {m.fuel_name}: {m.pass_rate:.1f}%")

    # Years to avoid
    avoid = insights.get_years_to_avoid(max_pass_rate=55.0)
    print(f"\n[Years to Avoid] (pass rate <= 55%): {len(avoid)} entries")
    for m in avoid[:5]:
        print(f"  {m.model} {m.model_year} {m.fuel_name}: {m.pass_rate:.1f}%")

    # Failure categories
    print(f"\n[Top Failure Categories]")
    for cat in insights.get_top_failure_categories(5):
        print(f"  {cat.name}: {format_number(cat.total_failures)} failures")

    # Hybrid comparison
    hybrid_comp = insights.get_hybrid_comparison()
    if hybrid_comp:
        print(f"\n[Hybrid vs Petrol vs Diesel]")
        for key in ['HY', 'PE', 'DI']:
            if key in hybrid_comp:
                f = hybrid_comp[key]
                print(f"  {f.fuel_name}: {f.pass_rate:.1f}%")

    print(f"\n{'='*60}")
    print("Parser test complete!")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(description="Generate HTML articles from insight JSON")
    parser.add_argument("json_file", nargs="?", help="Path to insights JSON file")
    parser.add_argument("--output", "-o", help="Output directory", default=str(OUTPUT_DIR))
    parser.add_argument("--all", action="store_true", help="Process all JSON files in data/")
    parser.add_argument("--test", "-t", action="store_true", help="Test parser and print insights (no HTML output)")

    args = parser.parse_args()

    # Collect JSON files to process
    if args.all:
        json_files = list(DATA_DIR.glob("*_insights.json"))
    elif args.json_file:
        json_files = [Path(args.json_file)]
    else:
        parser.print_help()
        return

    # Test mode - just parse and print insights
    if args.test:
        for json_path in json_files:
            test_parser(json_path)
        return

    # Normal mode - generate HTML
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in json_files:
        print(f"Processing: {json_path.name}")

        insights = parse_insights(json_path)
        html = generate_article(insights)

        output_file = output_dir / generate_filename(insights.make)
        output_file.write_text(html, encoding='utf-8')

        print(f"  Output: {output_file}")


if __name__ == "__main__":
    main()
