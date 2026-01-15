#!/usr/bin/env python3
"""
Dangerous Defects Article HTML Generator
=========================================
Generates a styled HTML article from dangerous_defects_insights.json.

Usage:
    python generate_dangerous_defects_html.py
    python generate_dangerous_defects_html.py --output articles/generated/
    python generate_dangerous_defects_html.py --input custom_insights.json

Output:
    most-dangerous-cars-uk.html
"""

import argparse
import json
from datetime import date
from pathlib import Path

from components import (
    DangerousDefectsInsights,
    format_number,
    generate_html_head,
    generate_header_section,
    generate_key_findings_section,
    generate_intro_section,
    generate_category_breakdown_section,
    generate_worst_models_section,
    generate_safest_models_section,
    generate_manufacturer_rankings_section,
    generate_fuel_analysis_section,
    generate_buyer_guide_section,
    generate_vehicle_deep_dive_section,
    generate_category_deep_dives_section,
    generate_age_controlled_section,
    generate_top_defects_section,
    generate_faq_section,
    generate_methodology_section,
)

# =============================================================================
# Constants
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
DEFAULT_INPUT = SCRIPT_DIR / "dangerous_defects_insights.json"
DEFAULT_OUTPUT = PROJECT_DIR / "articles" / "generated"


# =============================================================================
# Article Generation
# =============================================================================

def generate_html_body(insights: DangerousDefectsInsights, today_display: str) -> str:
    """Generate the HTML body section with all article content."""
    sections = [
        generate_header_section(insights, today_display),
        generate_key_findings_section(insights),
        generate_intro_section(insights),
        generate_category_breakdown_section(insights),
        generate_worst_models_section(insights),
        generate_safest_models_section(insights),
        generate_manufacturer_rankings_section(insights),
        generate_fuel_analysis_section(insights),
        generate_buyer_guide_section(insights),
        generate_vehicle_deep_dive_section(insights),
        generate_category_deep_dives_section(insights),  # NEW: Category-specific rankings
        generate_age_controlled_section(insights),       # NEW: 2015 model year comparison
        generate_top_defects_section(insights),
        generate_faq_section(insights),
        generate_methodology_section(insights),
    ]

    all_sections = "\n".join(s for s in sections if s)  # Filter empty sections

    return f'''<body class="bg-white min-h-screen">
  <!-- Reading Progress Bar -->
  <div id="reading-progress" style="width: 0%"></div>

  <!-- Shared Header (injected by articles-loader.js) -->
  <div id="mw-header"></div>

  <main id="main-content" class="max-w-3xl mx-auto px-4 py-8 sm:py-12">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="flex items-center gap-2 text-sm text-neutral-500 mb-6">
      <a href="/" class="hover:text-blue-600 transition-colors">Home</a>
      <i class="ph ph-caret-right text-xs"></i>
      <a href="/articles/" class="hover:text-blue-600 transition-colors">Guides</a>
      <i class="ph ph-caret-right text-xs"></i>
      <span class="text-neutral-900">Most Dangerous Cars UK</span>
    </nav>

    <article>
{all_sections}
    </article>
  </main>

  <!-- Shared Footer (injected by articles-loader.js) -->
  <div id="mw-footer"></div>

  <!-- Articles Loader (shared components) -->
  <script src="/articles/js/articles-loader.js"></script>

  <!-- Common Article JS -->
  <script src="/articles/js/article-common.js"></script>
</body>
</html>'''


def generate_article(insights: DangerousDefectsInsights) -> str:
    """Generate the complete HTML article."""
    today = date.today().strftime("%Y-%m-%d")
    day = str(date.today().day)
    month_year = date.today().strftime("%b %Y")
    today_display = f"{day} {month_year}"

    html = generate_html_head(insights, today)
    html += generate_html_body(insights, today_display)

    return html


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML article from dangerous defects insights JSON"
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input JSON file (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})"
    )

    args = parser.parse_args()

    # Load JSON
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    print(f"Loading insights from: {args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse insights
    insights = DangerousDefectsInsights(data)
    print(f"Parsed {format_number(insights.total_tests)} tests, {len(insights.model_rankings)} models")

    # Generate HTML
    html = generate_article(insights)

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    # Write output
    output_file = args.output / "most-dangerous-cars-uk.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated: {output_file}")
    print(f"File size: {len(html):,} bytes")

    return 0


if __name__ == '__main__':
    exit(main())
