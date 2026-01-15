#!/usr/bin/env python3
"""
Model Report Static HTML Generator
===================================
Generates static HTML pages for individual MODELS (all year/fuel variants).
Matches the feature set of the API frontend's renderVehicleReport().

Usage:
    python generate_model_report.py FORD FOCUS
    python generate_model_report.py "LAND ROVER" "RANGE ROVER"
    python generate_model_report.py --list FORD           # List models for a make
    python generate_model_report.py --top 100             # Generate top 100 most-tested models

Requires: API server running at http://localhost:8010
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote

# Import database queries module
from db_queries import get_complete_model_data, get_models_for_make, get_top_models

# Import Tailwind classes and HTML templates
try:
    from . import tailwind_classes as tw
    from . import html_templates as templates
except ImportError:
    import tailwind_classes as tw
    import html_templates as templates

# Configuration
API_BASE = "http://localhost:8010/api"
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = Path(r"C:\Users\gregor\Downloads\Dev\motorwise.io\frontend\public\articles\content\model-reports")


def fetch_json(url: str, silent: bool = False) -> dict | list | None:
    """Fetch JSON from API endpoint. Returns None on error if silent=True."""
    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        if not silent:
            print(f"HTTP Error {e.code} fetching {url}")
        return None
    except URLError as e:
        if not silent:
            print(f"Error fetching {url}: {e}")
            print("Make sure the API server is running: python -m api.backend.main")
            sys.exit(1)
        return None


def get_pass_rate_class(rate: float) -> str:
    """Return CSS class based on pass rate."""
    if rate >= 80:
        return "good"
    elif rate >= 65:
        return "average"
    return "poor"


def get_pass_rate_color(rate: float) -> str:
    """Return color based on pass rate."""
    if rate >= 80:
        return "#10b981"  # green
    elif rate >= 65:
        return "#f59e0b"  # amber
    return "#ef4444"  # red


def get_severity_color(severity: str) -> str:
    """Return color based on severity level."""
    colors = {
        "minor": "#10b981",
        "major": "#f59e0b",
        "dangerous": "#ef4444"
    }
    return colors.get(severity.lower(), "#64748b")


def format_number(n) -> str:
    """Format number with commas."""
    if n is None:
        return "N/A"
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


def format_ranking_type(rank_type: str) -> str:
    """Format ranking type for display."""
    labels = {
        "overall": "overall",
        "within_make": "in brand",
        "within_year": "in year"
    }
    return labels.get(rank_type, rank_type)


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    return text[:max_len] + "..." if len(text) > max_len else text


def get_fuel_name(code: str) -> str:
    """Convert fuel code to human-readable name."""
    fuel_names = {
        "PE": "Petrol",
        "DI": "Diesel",
        "HY": "Hybrid Electric",
        "EL": "Electric",
        "ED": "Plug-in Hybrid",
        "GB": "Gas Bi-fuel",
        "GD": "Gas Diesel",
        "OT": "Other",
    }
    return fuel_names.get(code, code)


def get_month_name(month: int) -> str:
    """Convert month number to abbreviation."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return months[month - 1] if 1 <= month <= 12 else str(month)


# =============================================================================
# DATA AGGREGATION FUNCTIONS
# =============================================================================

def aggregate_rankings(all_rankings: list[dict]) -> dict:
    """Aggregate rankings across variants - show best ranking achieved."""
    if not all_rankings:
        return {}

    result = {}
    for rankings in all_rankings:
        if not rankings:
            continue
        for rank_type, rank_data in rankings.items():
            if not rank_data:
                continue
            if rank_type not in result or rank_data.get("rank", 999999) < result[rank_type].get("rank", 999999):
                result[rank_type] = rank_data
    return result


def aggregate_severity(all_severity: list[list]) -> list[dict]:
    """Aggregate failure severity data across variants."""
    severity_totals = {}

    for severity_list in all_severity:
        if not severity_list:
            continue
        for s in severity_list:
            sev = s.get("severity", "unknown")
            if sev not in severity_totals:
                severity_totals[sev] = {"count": 0, "total_failures": 0}
            severity_totals[sev]["count"] += s.get("failure_count", 0)
            severity_totals[sev]["total_failures"] += s.get("total_failures", 0)

    total_count = sum(d["count"] for d in severity_totals.values())
    result = []
    for sev, data in severity_totals.items():
        result.append({
            "severity": sev,
            "failure_count": data["count"],
            "failure_percentage": (data["count"] / total_count * 100) if total_count > 0 else 0
        })

    return sorted(result, key=lambda x: x["failure_count"], reverse=True)


def aggregate_first_mot(all_first_mot: list) -> list[dict]:
    """Aggregate first MOT vs subsequent data."""
    totals = {"first": {"tests": 0, "passes": 0}, "subsequent": {"tests": 0, "passes": 0}}

    for fm in all_first_mot:
        if not fm:
            continue
        # Handle both list and dict formats
        items = fm if isinstance(fm, list) else [fm]
        for item in items:
            mot_type = item.get("mot_type", "").lower()
            if mot_type in totals:
                tests = item.get("total_tests", 0) or 0
                rate = item.get("pass_rate", 0) or 0
                totals[mot_type]["tests"] += tests
                totals[mot_type]["passes"] += int(tests * rate / 100)

    result = []
    for mot_type, data in totals.items():
        if data["tests"] > 0:
            result.append({
                "mot_type": mot_type,
                "total_tests": data["tests"],
                "pass_rate": (data["passes"] / data["tests"] * 100)
            })
    return result


def aggregate_retest(all_retest: list) -> dict:
    """Aggregate retest statistics."""
    total_failed = 0
    weighted_retest_rate = 0
    weighted_success_rate = 0
    weight_sum = 0

    for rt in all_retest:
        if not rt:
            continue
        failed = rt.get("failed_tests", 0) or 0
        total_failed += failed
        if failed > 0:
            weighted_retest_rate += (rt.get("retest_rate", 0) or 0) * failed
            weighted_success_rate += (rt.get("retest_success_rate", 0) or 0) * failed
            weight_sum += failed

    if weight_sum == 0:
        return None

    return {
        "failed_tests": total_failed,
        "retest_rate": weighted_retest_rate / weight_sum,
        "retest_success_rate": weighted_success_rate / weight_sum
    }


def aggregate_age_bands(all_age: list[list]) -> list[dict]:
    """Aggregate age band data across variants."""
    age_totals = {}

    for age_list in all_age:
        if not age_list:
            continue
        for a in age_list:
            band = a.get("age_band", "Unknown")
            order = a.get("band_order", 0)
            tests = a.get("total_tests", 0) or 0
            rate = a.get("pass_rate", 0) or 0
            passes = int(tests * rate / 100)

            if band not in age_totals:
                age_totals[band] = {"order": order, "tests": 0, "passes": 0}
            age_totals[band]["tests"] += tests
            age_totals[band]["passes"] += passes

    result = []
    for band, data in age_totals.items():
        if data["tests"] > 0:
            result.append({
                "age_band": band,
                "band_order": data["order"],
                "total_tests": data["tests"],
                "pass_rate": (data["passes"] / data["tests"] * 100)
            })

    return sorted(result, key=lambda x: x["band_order"])


def aggregate_geographic(all_geo: list[list]) -> list[dict]:
    """Aggregate geographic data across variants."""
    geo_totals = {}

    for geo_list in all_geo:
        if not geo_list:
            continue
        for g in geo_list:
            area = g.get("postcode_area", "Unknown")
            tests = g.get("total_tests", 0) or 0
            rate = g.get("pass_rate", 0) or 0
            passes = int(tests * rate / 100)

            if area not in geo_totals:
                geo_totals[area] = {"tests": 0, "passes": 0}
            geo_totals[area]["tests"] += tests
            geo_totals[area]["passes"] += passes

    result = []
    for area, data in geo_totals.items():
        if data["tests"] > 0:
            result.append({
                "postcode_area": area,
                "total_tests": data["tests"],
                "pass_rate": (data["passes"] / data["tests"] * 100)
            })

    return sorted(result, key=lambda x: x["pass_rate"], reverse=True)


def aggregate_seasonal(all_seasonal: list[list]) -> list[dict]:
    """Aggregate seasonal/monthly data across variants."""
    month_totals = {}

    for seasonal_list in all_seasonal:
        if not seasonal_list:
            continue
        for s in seasonal_list:
            month = s.get("month", 0)
            tests = s.get("total_tests", 0) or 0
            rate = s.get("pass_rate", 0) or 0
            passes = int(tests * rate / 100)

            if month not in month_totals:
                month_totals[month] = {"tests": 0, "passes": 0}
            month_totals[month]["tests"] += tests
            month_totals[month]["passes"] += passes

    result = []
    for month, data in month_totals.items():
        if data["tests"] > 0:
            result.append({
                "month": month,
                "total_tests": data["tests"],
                "pass_rate": (data["passes"] / data["tests"] * 100)
            })

    return sorted(result, key=lambda x: x["month"])


def aggregate_advisory_progression(all_progression: list[list]) -> list[dict]:
    """Aggregate advisory to failure progression data."""
    progression_totals = {}

    for prog_list in all_progression:
        if not prog_list:
            continue
        for p in prog_list:
            desc = p.get("advisory_text") or p.get("defect_description", "Unknown")
            rate = p.get("progression_rate", 0) or 0
            count = p.get("advisory_count", 1) or 1

            if desc not in progression_totals:
                progression_totals[desc] = {"weighted_rate": 0, "count": 0}
            progression_totals[desc]["weighted_rate"] += rate * count
            progression_totals[desc]["count"] += count

    result = []
    for desc, data in progression_totals.items():
        if data["count"] > 0:
            result.append({
                "advisory_text": desc,
                "progression_rate": data["weighted_rate"] / data["count"],
                "advisory_count": data["count"]
            })

    return sorted(result, key=lambda x: x["progression_rate"], reverse=True)[:10]


def aggregate_component_thresholds(all_thresholds: list[list]) -> list[dict]:
    """Aggregate component mileage threshold data."""
    component_totals = {}

    for thresh_list in all_thresholds:
        if not thresh_list:
            continue
        for t in thresh_list:
            component = t.get("component") or t.get("category_name", "Unknown")
            mileage = t.get("avg_failure_mileage") or t.get("threshold_mileage", 0)
            count = t.get("failure_count", 1) or 1

            if mileage and mileage > 0:
                if component not in component_totals:
                    component_totals[component] = {"weighted_mileage": 0, "count": 0}
                component_totals[component]["weighted_mileage"] += mileage * count
                component_totals[component]["count"] += count

    result = []
    for component, data in component_totals.items():
        if data["count"] > 0:
            result.append({
                "component": component,
                "avg_failure_mileage": data["weighted_mileage"] / data["count"],
                "failure_count": data["count"]
            })

    return sorted(result, key=lambda x: x["avg_failure_mileage"])[:10]


# =============================================================================
# MAIN DATA FETCHING
# =============================================================================

def aggregate_model_data(make: str, model: str) -> dict:
    """Fetch and aggregate all variant data for a model using direct DB queries."""
    data = get_complete_model_data(make, model)
    if data is None:
        return None
    return data


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(data: dict) -> str:
    """Generate complete HTML page from model report data using articles pattern."""
    make = data["make"]
    model = data["model"]
    summary = data["summary"]

    today = date.today().strftime("%d %b %Y")
    today_iso = date.today().isoformat()
    pass_rate = summary.get("pass_rate", 0) or 0

    # Create safe URL slugs
    safe_make = make.lower().replace(' ', '-').replace('(', '').replace(')', '')
    safe_model = model.lower().replace(' ', '-').replace('(', '').replace(')', '')

    # Generate the HTML head section
    head_html = templates.generate_head(
        make=make,
        model=model,
        safe_make=safe_make,
        safe_model=safe_model,
        total_tests=format_number(summary.get('total_tests')),
        today_iso=today_iso
    )

    # Generate article header components
    breadcrumb_html = templates.generate_breadcrumb(make, model)
    article_header_html = templates.generate_article_header(
        make=make,
        model=model,
        variant_count=summary.get('total_variants', 0),
        total_tests=format_number(summary.get('total_tests')),
        today=today
    )
    data_source_html = templates.generate_data_source_callout(
        total_tests=format_number(summary.get('total_tests')),
        year_range=summary.get('year_range', 'N/A')
    )
    key_findings_html = templates.generate_key_findings_card(
        best_variant=data.get("best_variant"),
        worst_variant=data.get("worst_variant"),
        pass_rate=pass_rate
    )

    # Define sections for TOC
    sections = build_toc_sections(data)

    # Generate TOC sidebar
    toc_html = templates.generate_toc_sidebar(sections)

    # Generate all main content sections
    main_content = generate_main_sections(data)

    html = f"""<!DOCTYPE html>
<html lang="en-GB">
{head_html}
<body class="bg-white md:bg-neutral-50 min-h-screen">
    <!-- Reading Progress Bar -->
    <div id="reading-progress" style="width: 0%"></div>

    <!-- Shared Header -->
    <div id="mw-header"></div>

    <!-- Main Content -->
    <main id="main-content" class="{tw.CONTAINER}">
        {breadcrumb_html}

        <article>
            {article_header_html}
            {data_source_html}
            {key_findings_html}

            <!-- Two-Column Layout -->
            <div class="article-layout">
                {toc_html}

                <!-- Main Content -->
                <div class="article-main">
                    {main_content}

                    <!-- CTA Section -->
                    <div class="article-cta">
                        <div class="article-cta-icon">
                            <i class="ph ph-magnifying-glass"></i>
                        </div>
                        <h3 class="article-cta-title">Check Any Vehicle's MOT History</h3>
                        <p class="article-cta-text">
                            Get the full MOT history, mileage records, and reliability insights for any UK vehicle. Make an informed decision before you buy.
                        </p>
                        <a href="/" class="article-cta-btn group">
                            Run a Free Check
                            <i class="ph ph-arrow-right transition-transform group-hover:translate-x-1"></i>
                        </a>
                    </div>
                </div>
            </div>
        </article>
    </main>

    <!-- Shared Footer (injected by articles-loader.js) -->
    <div id="mw-footer"></div>

    <!-- Articles Loader (shared components) -->
    <script src="/articles/js/articles-loader.js"></script>

    <!-- Common Article JS -->
    <script src="/articles/js/article-common.js"></script>
</body>
</html>
"""
    return html


def build_toc_sections(data: dict) -> list:
    """Build list of sections for table of contents based on available data."""
    sections = []

    # Always include overview
    sections.append({'id': 'overview', 'title': 'Pass Rate Overview', 'icon': 'chart-pie'})

    if data.get("rankings"):
        sections.append({'id': 'rankings', 'title': 'Rankings', 'icon': 'trophy'})

    if data.get("best_variant") or data.get("worst_variant"):
        sections.append({'id': 'best-worst', 'title': 'Best & Worst Years', 'icon': 'thumbs-up'})

    if data.get("age_bands"):
        sections.append({'id': 'age-impact', 'title': 'Age Impact', 'icon': 'clock'})

    if data.get("fuel_comparison") or data.get("mileage_bands"):
        sections.append({'id': 'fuel-mileage', 'title': 'Fuel & Mileage', 'icon': 'gas-pump'})

    if data.get("seasonal"):
        sections.append({'id': 'seasonal', 'title': 'Seasonal Patterns', 'icon': 'calendar'})

    if data.get("geographic"):
        sections.append({'id': 'geographic', 'title': 'Geographic Variation', 'icon': 'map-pin'})

    if data.get("failure_categories") or data.get("top_failures"):
        sections.append({'id': 'failures', 'title': 'Common Failures', 'icon': 'wrench'})

    if data.get("all_variants"):
        sections.append({'id': 'all-variants', 'title': 'All Variants', 'icon': 'list'})

    # Always include methodology
    sections.append({'id': 'methodology', 'title': 'About This Data', 'icon': 'info'})

    return sections


def generate_main_sections(data: dict) -> str:
    """Generate all main content sections with article-section pattern."""
    sections_html = []
    reveal_index = 1

    # Section 1: Pass Rate Overview
    overview_content = generate_overview_section_content(data)
    sections_html.append(templates.generate_article_section(
        section_id='overview',
        title='Pass Rate Overview',
        icon='chart-pie',
        content=overview_content,
        reveal_index=reveal_index
    ))
    reveal_index += 1

    # Section 2: Rankings (if available)
    if data.get("rankings"):
        rankings_content = generate_rankings_content(data.get("rankings", {}))
        sections_html.append(templates.generate_article_section(
            section_id='rankings',
            title='Rankings',
            icon='trophy',
            content=rankings_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 3: Best & Worst Years (if available)
    if data.get("best_variant") or data.get("worst_variant"):
        best_worst_content = generate_best_worst_content(data)
        sections_html.append(templates.generate_article_section(
            section_id='best-worst',
            title='Best & Worst Years',
            icon='thumbs-up',
            content=best_worst_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 4: Age Impact (if available)
    if data.get("age_bands"):
        age_content = generate_age_section_content(data.get("age_bands", []))
        sections_html.append(templates.generate_article_section(
            section_id='age-impact',
            title='Age Impact on Reliability',
            icon='clock',
            content=age_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 5: Fuel & Mileage (if available)
    if data.get("fuel_comparison") or data.get("mileage_bands"):
        fuel_mileage_content = generate_fuel_mileage_content(data)
        sections_html.append(templates.generate_article_section(
            section_id='fuel-mileage',
            title='Fuel Type & Mileage Analysis',
            icon='gas-pump',
            content=fuel_mileage_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 6: Seasonal Patterns (if available)
    if data.get("seasonal"):
        seasonal_content = generate_seasonal_content(data.get("seasonal", []))
        sections_html.append(templates.generate_article_section(
            section_id='seasonal',
            title='Seasonal Patterns',
            icon='calendar',
            content=seasonal_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 7: Geographic (if available)
    if data.get("geographic"):
        geo_content = generate_geographic_content(data.get("geographic", []))
        sections_html.append(templates.generate_article_section(
            section_id='geographic',
            title='Geographic Variation',
            icon='map-pin',
            content=geo_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 8: Common Failures (if available)
    if data.get("failure_categories") or data.get("top_failures"):
        failures_content = generate_failures_content(data)
        sections_html.append(templates.generate_article_section(
            section_id='failures',
            title='Common MOT Failures',
            icon='wrench',
            content=failures_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 9: All Variants (if available)
    if data.get("all_variants"):
        variants_content = generate_variants_content(data.get("all_variants", []))
        sections_html.append(templates.generate_article_section(
            section_id='all-variants',
            title='All Variants',
            icon='list',
            content=variants_content,
            reveal_index=reveal_index
        ))
        reveal_index += 1

    # Section 10: Methodology (always include)
    methodology_content = generate_methodology_content(data)
    sections_html.append(templates.generate_article_section(
        section_id='methodology',
        title='About This Data',
        icon='info',
        content=methodology_content,
        reveal_index=reveal_index
    ))

    return "\n".join(sections_html)


def generate_overview_section_content(data: dict) -> str:
    """Generate pass rate overview section content."""
    summary = data["summary"]
    pass_rate = summary.get("pass_rate", 0) or 0
    pass_rate_color = get_pass_rate_color(pass_rate)
    circumference = 2 * 3.14159 * 54
    progress = circumference - (pass_rate / 100) * circumference

    total_passes = summary.get("total_passes", 0) or 0
    total_fails = summary.get("total_fails", 0) or 0

    # Year trend chart
    year_data = data.get("year_comparison", [])
    max_tests = max((y.get("total_tests", 0) for y in year_data), default=1)

    year_bars = ""
    for y in year_data:
        tests = y.get("total_tests", 0)
        rate = y.get("pass_rate", 0)
        height_pct = (tests / max_tests * 100) if max_tests > 0 else 0
        year_bars += f"""
            <div class="{tw.YEAR_BAR_COL}">
                <div class="{tw.YEAR_BAR_WRAPPER}">
                    <div class="{tw.YEAR_BAR}" style="height: {height_pct}%; background: {get_pass_rate_color(rate)};" title="{rate:.1f}%"></div>
                </div>
                <div class="{tw.YEAR_LABEL}">{y['year']}</div>
                <div class="{tw.YEAR_RATE}" style="color: {get_pass_rate_color(rate)}">{rate:.0f}%</div>
            </div>"""

    return f"""
        <div class="flex flex-col md:flex-row items-center gap-6 md:gap-8 mb-6">
            <div class="relative w-36 h-36 flex-shrink-0 pass-rate-circle">
                <svg width="144" height="144">
                    <circle class="bg" cx="72" cy="72" r="54" fill="none" stroke="#f1f5f9" stroke-width="12"/>
                    <circle class="progress" cx="72" cy="72" r="54"
                        fill="none"
                        stroke="{pass_rate_color}"
                        stroke-width="12"
                        stroke-dasharray="{circumference}"
                        stroke-dashoffset="{progress}"/>
                </svg>
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                    <div class="text-3xl font-bold" style="color: {pass_rate_color}">{pass_rate:.1f}%</div>
                    <div class="text-xs text-neutral-500 uppercase tracking-wide">Pass Rate</div>
                </div>
            </div>
            <div class="flex-1 min-w-0 sm:min-w-[200px]">
                <h3 class="text-base font-semibold text-neutral-900 mb-3">Test Statistics</h3>
                <div class="grid grid-cols-2 gap-3 sm:gap-4">
                    <div class="flex flex-col p-3 bg-neutral-50 rounded-xl">
                        <span class="text-xs text-neutral-500">Total Tests</span>
                        <span class="text-lg font-semibold text-neutral-900">{format_number(summary.get('total_tests'))}</span>
                    </div>
                    <div class="flex flex-col p-3 bg-neutral-50 rounded-xl">
                        <span class="text-xs text-neutral-500">Average Mileage</span>
                        <span class="text-lg font-semibold text-neutral-900">{format_number(summary.get('avg_mileage'))} mi</span>
                    </div>
                    <div class="flex flex-col p-3 bg-neutral-50 rounded-xl">
                        <span class="text-xs text-neutral-500">Total Passes</span>
                        <span class="text-lg font-semibold text-neutral-900">{format_number(total_passes)}</span>
                    </div>
                    <div class="flex flex-col p-3 bg-neutral-50 rounded-xl">
                        <span class="text-xs text-neutral-500">Total Failures</span>
                        <span class="text-lg font-semibold text-neutral-900">{format_number(total_fails)}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="article-prose mb-4">
            <p>Pass rate trend by model year:</p>
        </div>

        <div class="{tw.YEAR_CHART}">{year_bars if year_bars else '<p class="text-neutral-500">No year data available</p>'}
        </div>"""


def generate_rankings_content(rankings: dict) -> str:
    """Generate rankings section content."""
    if not rankings:
        return '<p class="text-neutral-500">No ranking data available</p>'

    badges = ""
    for rank_type, rank_data in rankings.items():
        if not rank_data:
            continue
        rank = rank_data.get("rank", "N/A")
        total = rank_data.get("total_in_category", 0)
        percentile = rank_data.get("percentile", 0)

        badges += f"""
            <div class="text-center p-4 bg-neutral-50 rounded-xl">
                <div class="text-2xl font-bold text-blue-600">#{rank}</div>
                <div class="text-xs text-neutral-500 mt-1">of {total} {format_ranking_type(rank_type)}</div>
                <div class="inline-block mt-2 px-2.5 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold">Top {percentile}%</div>
            </div>"""

    return f"""
        <div class="article-prose mb-4">
            <p>How this vehicle ranks compared to others:</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">{badges}</div>"""


def generate_best_worst_content(data: dict) -> str:
    """Generate best and worst years section content."""
    best = data.get("best_variant")
    worst = data.get("worst_variant")

    content = '<div class="grid md:grid-cols-2 gap-4">'

    if best:
        content += f"""
            <div class="bg-gradient-to-br from-emerald-50 to-emerald-100/30 rounded-xl p-5 border border-emerald-100/80">
                <h4 class="font-semibold text-emerald-900 mb-1">Best Year to Buy</h4>
                <p class="text-2xl font-bold text-neutral-900">{best['year']} {best.get('fuel_type_name', '')}</p>
                <p class="text-sm text-emerald-600 font-medium mt-1">{best['pass_rate']:.1f}% pass rate</p>
                <p class="text-xs text-neutral-500 mt-2">Based on {format_number(best.get('total_tests'))} tests</p>
            </div>"""

    if worst and worst != best:
        content += f"""
            <div class="bg-gradient-to-br from-red-50 to-red-100/30 rounded-xl p-5 border border-red-100/80">
                <h4 class="font-semibold text-red-900 mb-1">Year to Avoid</h4>
                <p class="text-2xl font-bold text-neutral-900">{worst['year']} {worst.get('fuel_type_name', '')}</p>
                <p class="text-sm text-red-600 font-medium mt-1">{worst['pass_rate']:.1f}% pass rate</p>
                <p class="text-xs text-neutral-500 mt-2">Based on {format_number(worst.get('total_tests'))} tests</p>
            </div>"""

    content += '</div>'

    # Add callout if there's significant variance
    if best and worst and best != worst:
        variance = best['pass_rate'] - worst['pass_rate']
        if variance > 10:
            content += templates.generate_callout(
                'warning',
                'Significant year variation',
                f"There's a {variance:.1f}% difference between the best and worst years. Choose your model year carefully."
            )

    return content


def generate_age_section_content(age_bands: list) -> str:
    """Generate age bands section content."""
    if not age_bands:
        return '<p class="text-neutral-500">No age data available</p>'

    max_rate = max((a.get("pass_rate", 0) for a in age_bands), default=100)
    min_rate = min((a.get("pass_rate", 0) for a in age_bands), default=0)
    range_val = max(max_rate - min_rate, 10)

    bars = ""
    for a in age_bands:
        rate = a.get("pass_rate", 0)
        band = a.get("age_band", "")
        height_pct = ((rate - min_rate + 5) / (range_val + 10)) * 100

        bars += f"""
            <div class="{tw.AGE_BAR_COL}">
                <div class="{tw.AGE_BAR_WRAPPER}">
                    <div class="{tw.AGE_BAR}" style="height: {height_pct}%; background: {get_pass_rate_color(rate)};"></div>
                </div>
                <div class="{tw.AGE_LABEL}">{band}</div>
                <div class="{tw.AGE_RATE}" style="color: {get_pass_rate_color(rate)}">{rate:.0f}%</div>
            </div>"""

    return f"""
        <div class="article-prose mb-4">
            <p>How pass rate changes as the vehicle ages:</p>
        </div>
        <div class="{tw.AGE_CHART}">{bars}</div>"""


def generate_fuel_mileage_content(data: dict) -> str:
    """Generate fuel type and mileage section content."""
    content = '<div class="grid md:grid-cols-2 gap-6">'

    # Fuel type comparison
    fuel_rows = ""
    for f in data.get("fuel_comparison", []):
        rate = f.get("pass_rate", 0)
        badge_class = "pass-rate-excellent" if rate >= 80 else ("pass-rate-good" if rate >= 65 else "pass-rate-average")
        fuel_rows += f"""
            <tr>
                <td>{f.get('fuel_type', 'N/A')}</td>
                <td><span class="data-badge {badge_class}">{rate:.1f}%</span></td>
                <td>{format_number(f.get('total_tests'))}</td>
            </tr>"""

    if fuel_rows:
        content += f"""
            <div>
                <h4 class="text-sm font-semibold text-neutral-900 mb-3">Fuel Type Comparison</h4>
                <div class="article-table-wrapper">
                    <table class="article-table">
                        <thead><tr><th>Fuel Type</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{fuel_rows}</tbody>
                    </table>
                </div>
            </div>"""

    # Mileage impact
    mileage_rows = ""
    for mb in data.get("mileage_bands", []):
        rate = mb.get("pass_rate", 0)
        badge_class = "pass-rate-excellent" if rate >= 80 else ("pass-rate-good" if rate >= 65 else "pass-rate-average")
        mileage_rows += f"""
            <tr>
                <td>{mb.get('mileage_band', 'N/A')}</td>
                <td><span class="data-badge {badge_class}">{rate:.1f}%</span></td>
                <td>{format_number(mb.get('total_tests'))}</td>
            </tr>"""

    if mileage_rows:
        content += f"""
            <div>
                <h4 class="text-sm font-semibold text-neutral-900 mb-3">Mileage Impact</h4>
                <div class="article-table-wrapper">
                    <table class="article-table">
                        <thead><tr><th>Mileage Band</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{mileage_rows}</tbody>
                    </table>
                </div>
            </div>"""

    content += '</div>'
    return content


def generate_seasonal_content(seasonal: list) -> str:
    """Generate seasonal patterns section content."""
    if not seasonal:
        return '<p class="text-neutral-500">No seasonal data available</p>'

    max_rate = max((s.get("pass_rate", 0) for s in seasonal), default=100)
    min_rate = min((s.get("pass_rate", 0) for s in seasonal), default=0)
    range_val = max(max_rate - min_rate, 5)

    bars = ""
    for s in seasonal:
        month = s.get("month", 0)
        rate = s.get("pass_rate", 0)
        height_pct = ((rate - min_rate + 2) / (range_val + 4)) * 100

        bars += f"""
            <div class="{tw.MONTHLY_BAR_COL}">
                <div class="{tw.MONTHLY_BAR_WRAPPER}">
                    <div class="{tw.MONTHLY_BAR}" style="height: {height_pct}%; background: {get_pass_rate_color(rate)};"></div>
                </div>
                <div class="{tw.MONTHLY_LABEL}">{get_month_name(month)}</div>
                <div class="{tw.MONTHLY_RATE}" style="color: {get_pass_rate_color(rate)}">{rate:.0f}%</div>
            </div>"""

    return f"""
        <div class="article-prose mb-4">
            <p>Monthly pass rate variation for this vehicle:</p>
        </div>
        <div class="{tw.MONTHLY_CHART}">{bars}</div>"""


def generate_geographic_content(geographic: list) -> str:
    """Generate geographic section content."""
    if not geographic or len(geographic) < 2:
        return '<p class="text-neutral-500">Insufficient geographic data</p>'

    best = geographic[:5]
    worst = geographic[-5:][::-1]

    best_rows = ""
    for g in best:
        rate = g.get("pass_rate", 0)
        badge_class = "pass-rate-excellent" if rate >= 80 else ("pass-rate-good" if rate >= 65 else "pass-rate-average")
        best_rows += f"""
            <tr>
                <td><strong>{g.get('postcode_area', 'N/A')}</strong></td>
                <td><span class="data-badge {badge_class}">{rate:.1f}%</span></td>
                <td>{format_number(g.get('total_tests'))}</td>
            </tr>"""

    worst_rows = ""
    for g in worst:
        rate = g.get("pass_rate", 0)
        badge_class = "pass-rate-excellent" if rate >= 80 else ("pass-rate-good" if rate >= 65 else "pass-rate-average")
        worst_rows += f"""
            <tr>
                <td><strong>{g.get('postcode_area', 'N/A')}</strong></td>
                <td><span class="data-badge {badge_class}">{rate:.1f}%</span></td>
                <td>{format_number(g.get('total_tests'))}</td>
            </tr>"""

    return f"""
        <div class="article-prose mb-4">
            <p>Pass rates by UK postcode area:</p>
        </div>
        <div class="grid md:grid-cols-2 gap-6">
            <div>
                <h4 class="text-sm font-semibold text-emerald-600 mb-3">Best Areas</h4>
                <div class="article-table-wrapper">
                    <table class="article-table">
                        <thead><tr><th>Postcode</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{best_rows}</tbody>
                    </table>
                </div>
            </div>
            <div>
                <h4 class="text-sm font-semibold text-red-600 mb-3">Worst Areas</h4>
                <div class="article-table-wrapper">
                    <table class="article-table">
                        <thead><tr><th>Postcode</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{worst_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>"""


def generate_failures_content(data: dict) -> str:
    """Generate failures section content."""
    content = ""

    # Failure categories bars
    categories = data.get("failure_categories", [])[:10]
    if categories:
        max_failures = max((c.get("failure_count", 0) for c in categories), default=1)

        failure_bars = ""
        for cat in categories:
            count = cat.get("failure_count", 0)
            pct = (count / max_failures * 100) if max_failures > 0 else 0
            failure_bars += f"""
                <div class="{tw.BAR_ROW}">
                    <div class="{tw.BAR_LABEL}">{truncate(cat.get('category_name', 'Unknown'), 30)}</div>
                    <div class="{tw.BAR_CONTAINER}">
                        <div class="{tw.BAR}" style="width: {pct}%"></div>
                        <span class="{tw.BAR_VALUE}">{format_number(count)}</span>
                    </div>
                </div>"""

        content += f"""
            <div class="article-prose mb-4">
                <p>Most common failure categories:</p>
            </div>
            <div class="mb-6">{failure_bars}</div>"""

    # Top specific failures
    top_failures = data.get("top_failures", [])[:10]
    if top_failures:
        failures_rows = ""
        for d in top_failures:
            failures_rows += f"""
                <tr>
                    <td>{truncate(d.get('defect_description', 'Unknown'), 50)}</td>
                    <td>{format_number(d.get('occurrence_count'))}</td>
                </tr>"""

        content += f"""
            <div class="mt-6">
                <h4 class="text-sm font-semibold text-neutral-900 mb-3">Top Specific Failures</h4>
                <div class="article-table-wrapper">
                    <table class="article-table">
                        <thead><tr><th>Defect</th><th>Count</th></tr></thead>
                        <tbody>{failures_rows}</tbody>
                    </table>
                </div>
            </div>"""

    # Dangerous defects warning
    dangerous = data.get("dangerous_defects", [])
    if dangerous:
        dangerous_list = ", ".join([d.get('defect_description', 'Unknown')[:30] for d in dangerous[:3]])
        content += templates.generate_callout(
            'danger',
            f'{len(dangerous)} dangerous defects recorded',
            f'Including: {dangerous_list}...'
        )

    return content if content else '<p class="text-neutral-500">No failure data available</p>'


def generate_variants_content(all_variants: list) -> str:
    """Generate all variants table content."""
    if not all_variants:
        return '<p class="text-neutral-500">No variant data available</p>'

    rows = ""
    for v in all_variants:
        rate = v.get("pass_rate", 0)
        badge_class = "pass-rate-excellent" if rate >= 80 else ("pass-rate-good" if rate >= 65 else "pass-rate-average")
        rows += f"""
            <tr>
                <td>{v.get('year', 'N/A')}</td>
                <td>{v.get('fuel_type_name', 'N/A')}</td>
                <td><span class="data-badge {badge_class}">{rate:.1f}%</span></td>
                <td>{format_number(v.get('total_tests'))}</td>
                <td>{format_number(v.get('avg_mileage'))} mi</td>
            </tr>"""

    return f"""
        <div class="article-prose mb-4">
            <p>Complete breakdown of all {len(all_variants)} variants:</p>
        </div>
        <div class="article-table-wrapper max-h-96 overflow-y-auto">
            <table class="article-table">
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Fuel</th>
                        <th>Pass Rate</th>
                        <th>Tests</th>
                        <th>Avg Mileage</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>"""


def generate_methodology_content(data: dict) -> str:
    """Generate methodology section content."""
    summary = data["summary"]
    total_tests = format_number(summary.get('total_tests'))
    year_range = summary.get('year_range', 'N/A')

    return f"""
        <div class="text-sm text-neutral-600 space-y-3 leading-relaxed">
            <p>This analysis uses real MOT test results from the DVSA database, covering <strong>{total_tests}</strong> tests on this vehicle between <strong>{year_range}</strong>.</p>
            <p><strong class="text-neutral-800">Data source:</strong> All data comes from the UK Driver and Vehicle Standards Agency (DVSA) MOT database, which records every MOT test conducted in the UK.</p>
            <p><strong class="text-neutral-800">Pass rate calculation:</strong> Pass rates are calculated as first-time passes, excluding retests. A vehicle passes if it has no dangerous or major defects.</p>
            <p><strong class="text-neutral-800">Limitations:</strong> MOT tests only cover vehicles 3+ years old. Very new vehicles aren't represented. Regional variations may reflect differences in testing standards or vehicle condition.</p>
        </div>"""


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def generate_model_report(make: str, model: str, output_dir: Path) -> Path:
    """Generate HTML report for a single model."""
    print(f"Fetching data for {make} {model}...")
    data = aggregate_model_data(make, model)

    if not data:
        print(f"No data found for {make} {model}")
        return None

    print(f"  Found {data['summary']['total_variants']} variants, {format_number(data['summary']['total_tests'])} tests")
    print(f"Generating HTML...")
    html = generate_html(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_make = make.lower().replace(' ', '-').replace('(', '').replace(')', '')
    safe_model = model.lower().replace(' ', '-').replace('(', '').replace(')', '')
    filename = f"{safe_make}-{safe_model}-report.html"
    output_path = output_dir / filename

    output_path.write_text(html, encoding='utf-8')
    print(f"Saved: {output_path}")

    return output_path


def clear_output_directory(output_dir: Path):
    """Clear all HTML files from the output directory."""
    if output_dir.exists():
        html_files = list(output_dir.glob("*.html"))
        if html_files:
            print(f"Clearing {len(html_files)} existing HTML files from {output_dir}")
            for f in html_files:
                f.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Generate static HTML model reports")
    parser.add_argument("make", nargs="?", help="Vehicle make (e.g., FORD)")
    parser.add_argument("model", nargs="?", help="Vehicle model (e.g., FOCUS)")
    parser.add_argument("--output", "-o", help="Output directory", default=str(OUTPUT_DIR))
    parser.add_argument("--list", "-l", action="store_true", help="List models for the specified make")
    parser.add_argument("--top", type=int, help="Generate reports for top N most-tested models")

    args = parser.parse_args()
    output_dir = Path(args.output)

    if args.list:
        if not args.make:
            print("Error: --list requires a make name")
            print("Example: python generate_model_report.py --list FORD")
            sys.exit(1)

        models = get_models_for_make(args.make.upper())
        print(f"\nModels for {args.make.upper()} ({len(models)} total):")
        print("-" * 40)
        for m in models:
            print(f"  {m}")
        return

    if args.top:
        clear_output_directory(output_dir)
        print(f"\nFinding top {args.top} most-tested models...")
        top_models = get_top_models(args.top)

        print(f"\n{'#':<4} {'Make':<15} {'Model':<25} {'Tests':>12} {'Variants':>8}")
        print("-" * 68)
        for i, m in enumerate(top_models, 1):
            print(f"{i:<4} {m['make']:<15} {m['model']:<25} {m['total_tests']:>12,} {m['variants']:>8}")

        print(f"\nGenerating reports for {len(top_models)} models...\n")

        success = 0
        for i, m in enumerate(top_models, 1):
            try:
                print(f"[{i}/{len(top_models)}] ", end="")
                result = generate_model_report(m["make"], m["model"], output_dir)
                if result:
                    success += 1
            except Exception as e:
                print(f"Error generating {m['make']} {m['model']}: {e}")

        print(f"\nDone! Generated {success}/{len(top_models)} reports")
        print(f"Output: {output_dir}")
        return

    if args.make and args.model:
        clear_output_directory(output_dir)
        generate_model_report(args.make.upper(), args.model.upper(), output_dir)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python generate_model_report.py FORD FOCUS")
        print("  python generate_model_report.py --list FORD")
        print("  python generate_model_report.py --top 100")


if __name__ == "__main__":
    main()
