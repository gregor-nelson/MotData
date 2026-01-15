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
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "articles" / "model-reports"


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
    """Generate complete HTML page from model report data using Tailwind CSS."""
    make = data["make"]
    model = data["model"]
    summary = data["summary"]

    today = date.today().strftime("%d %b %Y")
    today_iso = date.today().isoformat()
    pass_rate = summary.get("pass_rate", 0) or 0
    pass_rate_color = get_pass_rate_color(pass_rate)

    # Create safe URL slugs
    safe_make = make.lower().replace(' ', '-').replace('(', '').replace(')', '')
    safe_model = model.lower().replace(' ', '-').replace('(', '').replace(')', '')

    # Build all the HTML sections
    rankings_html = generate_rankings_section(data.get("rankings", {}))
    severity_html = generate_severity_section(data.get("severity", []))
    first_mot_html = generate_first_mot_section(data.get("first_mot", []))
    retest_html = generate_retest_section(data.get("retest"))
    age_bands_html = generate_age_bands_section(data.get("age_bands", []))
    geographic_html = generate_geographic_section(data.get("geographic", []))
    seasonal_html = generate_seasonal_section(data.get("seasonal", []))
    advisory_prog_html = generate_advisory_progression_section(data.get("advisory_progression", []))
    component_thresh_html = generate_component_thresholds_section(data.get("component_thresholds", []))

    # Best year to buy section
    best = data.get("best_variant")
    best_html = ""
    if best:
        best_html = f"""
        <div class="{tw.CARD_GOOD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Best Year to Buy</h3>
                <i class="{tw.ICON_THUMBS_UP} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.HIGHLIGHT_STAT}">
                    <span class="{tw.HIGHLIGHT_VALUE}">{best['year']} {best['fuel_type_name']}</span>
                    {templates.get_badge_html(best['pass_rate'], f"{best['pass_rate']:.1f}% pass rate")}
                </div>
                <p class="{tw.HIGHLIGHT_DETAIL}">Based on {format_number(best['total_tests'])} MOT tests</p>
            </div>
        </div>"""

    # Worst year to avoid section
    worst = data.get("worst_variant")
    worst_html = ""
    if worst and worst != best:
        worst_html = f"""
        <div class="{tw.CARD_POOR}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Year to Avoid</h3>
                <i class="{tw.ICON_THUMBS_DOWN} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.HIGHLIGHT_STAT}">
                    <span class="{tw.HIGHLIGHT_VALUE}">{worst['year']} {worst['fuel_type_name']}</span>
                    {templates.get_badge_html(worst['pass_rate'], f"{worst['pass_rate']:.1f}% pass rate")}
                </div>
                <p class="{tw.HIGHLIGHT_DETAIL}">Based on {format_number(worst['total_tests'])} MOT tests</p>
            </div>
        </div>"""

    # Fuel type comparison
    fuel_rows = ""
    for f in data.get("fuel_comparison", []):
        rate = f.get("pass_rate", 0)
        fuel_rows += f"""
                <tr class="{tw.TR_HOVER}">
                    <td class="{tw.TD}">{f.get('fuel_type', 'N/A')}</td>
                    <td class="{tw.TD}">{templates.get_badge_html(rate)}</td>
                    <td class="{tw.TD}">{format_number(f.get('total_tests'))}</td>
                    <td class="{tw.TD}">{f.get('variants', 0)}</td>
                </tr>"""

    # Year trend chart (CSS bars)
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

    # Mileage impact section
    mileage_rows = ""
    for mb in data.get("mileage_bands", []):
        rate = mb.get("pass_rate", 0)
        mileage_rows += f"""
                <tr class="{tw.TR_HOVER}">
                    <td class="{tw.TD}">{mb.get('mileage_band', 'N/A')}</td>
                    <td class="{tw.TD}">{templates.get_badge_html(rate)}</td>
                    <td class="{tw.TD}">{format_number(mb.get('total_tests'))}</td>
                </tr>"""

    # Build failure categories bars
    categories = data.get("failure_categories", [])[:10]
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

    # Top failures list
    failures_list = ""
    for d in data.get("top_failures", [])[:15]:
        failures_list += f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DEFECT_NAME}">{d.get('defect_description', 'Unknown')}</span>
                <span class="{tw.DEFECT_COUNT}">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Top advisories list
    advisories_list = ""
    for d in data.get("top_advisories", [])[:15]:
        advisories_list += f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DEFECT_NAME}">{d.get('defect_description', 'Unknown')}</span>
                <span class="{tw.DEFECT_COUNT}">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Dangerous defects
    dangerous_list = ""
    for d in data.get("dangerous_defects", [])[:10]:
        dangerous_list += f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DEFECT_NAME}">{d.get('defect_description', 'Unknown')}</span>
                <span class="{tw.DEFECT_COUNT_DANGEROUS}">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    dangerous_section = ""
    if data.get("dangerous_defects"):
        dangerous_section = f"""
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE} text-poor">Dangerous Defects ({len(data['dangerous_defects'])})</h3>
                <i class="{tw.ICON_WARNING_OCTAGON} {tw.ICON_HEADER} text-poor"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <ul class="{tw.DEFECT_LIST}">{dangerous_list}
                </ul>
            </div>
        </div>
        """

    # All variants table
    all_variants_rows = ""
    for v in data.get("all_variants", []):
        rate = v.get("pass_rate", 0)
        all_variants_rows += f"""
                <tr class="{tw.TR_HOVER}">
                    <td class="{tw.TD}">{v.get('year', 'N/A')}</td>
                    <td class="{tw.TD}">{v.get('fuel_type_name', 'N/A')}</td>
                    <td class="{tw.TD}">{templates.get_badge_html(rate)}</td>
                    <td class="{tw.TD}">{format_number(v.get('total_tests'))}</td>
                    <td class="{tw.TD}">{format_number(v.get('avg_mileage'))}</td>
                </tr>"""

    # Generate the HTML head section
    head_html = templates.generate_head(
        make=make,
        model=model,
        safe_make=safe_make,
        safe_model=safe_model,
        total_tests=format_number(summary.get('total_tests')),
        today_iso=today_iso
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
{head_html}
<body class="bg-slate-50 text-slate-800 font-sans leading-relaxed">
    <header class="{tw.HEADER}">
        <h1 class="{tw.HEADER_H1}">{make} {model} MOT Reliability Report</h1>
        <div class="{tw.HEADER_SUBTITLE}">Comprehensive analysis based on {format_number(summary.get('total_tests'))} real MOT tests</div>
        <div class="{tw.HEADER_META}">Years: {summary.get('year_range', 'N/A')} | {summary.get('total_variants', 0)} variants analysed</div>
        <div class="{tw.HEADER_META}">Updated {today}</div>
    </header>

    <div class="{tw.CONTAINER}">
        <!-- Pass Rate Hero Section -->
        {generate_pass_rate_hero(summary, pass_rate, pass_rate_color)}

        <!-- Rankings Section -->
        {rankings_html}

        <!-- Best & Worst Year Highlights -->
        <div class="{tw.GRID_2}">
            {best_html}
            {worst_html}
        </div>

        <!-- Key Insights Grid -->
        <div class="{tw.GRID_3}">
            {severity_html}
            {first_mot_html}
            {retest_html}
        </div>

        <!-- Year Trend Chart -->
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Pass Rate by Year</h3>
                <i class="{tw.ICON_CHART_LINE} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.YEAR_CHART}">{year_bars if year_bars else '<p class="text-slate-500">No year data available</p>'}
                </div>
            </div>
        </div>

        <!-- Age Bands Section -->
        {age_bands_html}

        <!-- Fuel Type & Mileage Comparison -->
        <div class="{tw.GRID_2}">
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Fuel Type Comparison</h3>
                    <i class="{tw.ICON_GAS_PUMP} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <table class="{tw.TABLE}">
                        <thead><tr>
                            <th class="{tw.TH}">Fuel Type</th>
                            <th class="{tw.TH}">Pass Rate</th>
                            <th class="{tw.TH}">Tests</th>
                            <th class="{tw.TH}">Variants</th>
                        </tr></thead>
                        <tbody>{fuel_rows if fuel_rows else f'<tr><td class="{tw.TD}" colspan="4">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Mileage Impact on Pass Rate</h3>
                    <i class="{tw.ICON_PATH} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <table class="{tw.TABLE}">
                        <thead><tr>
                            <th class="{tw.TH}">Mileage Band</th>
                            <th class="{tw.TH}">Pass Rate</th>
                            <th class="{tw.TH}">Tests</th>
                        </tr></thead>
                        <tbody>{mileage_rows if mileage_rows else f'<tr><td class="{tw.TD}" colspan="3">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Seasonal Patterns -->
        {seasonal_html}

        <!-- Geographic Insights -->
        {geographic_html}

        <!-- Failure Categories -->
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Common Failure Categories</h3>
                <i class="{tw.ICON_WRENCH} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">{failure_bars if failure_bars else '<p class="text-slate-500">No data available</p>'}
            </div>
        </div>

        <!-- Advisory Progression & Component Thresholds -->
        <div class="{tw.GRID_2}">
            {advisory_prog_html}
            {component_thresh_html}
        </div>

        <!-- Top Failures & Advisories -->
        <div class="{tw.GRID_2}">
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Top Failures ({len(data.get('top_failures', []))})</h3>
                    <i class="{tw.ICON_WARNING} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <ul class="{tw.DEFECT_LIST}">{failures_list if failures_list else '<li class="text-slate-500">No failures recorded</li>'}
                    </ul>
                </div>
            </div>
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Top Advisories ({len(data.get('top_advisories', []))})</h3>
                    <i class="{tw.ICON_INFO} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <ul class="{tw.DEFECT_LIST}">{advisories_list if advisories_list else '<li class="text-slate-500">No advisories recorded</li>'}
                    </ul>
                </div>
            </div>
        </div>

        <!-- Dangerous Defects -->
        {dangerous_section}

        <!-- All Variants Table -->
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">All Variants ({len(data.get('all_variants', []))})</h3>
                <i class="{tw.ICON_LIST} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.ALL_VARIANTS_TABLE}">
                    <table class="{tw.TABLE}">
                        <thead>
                            <tr>
                                <th class="{tw.TH}">Year</th>
                                <th class="{tw.TH}">Fuel</th>
                                <th class="{tw.TH}">Pass Rate</th>
                                <th class="{tw.TH}">Tests</th>
                                <th class="{tw.TH}">Avg Mileage</th>
                            </tr>
                        </thead>
                        <tbody>{all_variants_rows if all_variants_rows else f'<tr><td class="{tw.TD}" colspan="5">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <footer class="{tw.FOOTER}">
        <p>Data source: UK DVSA MOT test records | Generated {today}</p>
        <p>Motorwise - Real reliability data for UK vehicles</p>
    </footer>
</body>
</html>
"""
    return html


def generate_pass_rate_hero(summary: dict, pass_rate: float, pass_rate_color: str) -> str:
    """Generate the pass rate hero section with circular gauge."""
    circumference = 2 * 3.14159 * 54
    progress = circumference - (pass_rate / 100) * circumference

    total_passes = summary.get("total_passes", 0) or 0
    total_fails = summary.get("total_fails", 0) or 0

    return f"""
        <div class="{tw.HERO}">
            <div class="{tw.HERO_CIRCLE} pass-rate-circle">
                <svg width="144" height="144">
                    <circle class="bg" cx="72" cy="72" r="54" fill="none" stroke="#f1f5f9" stroke-width="12"/>
                    <circle class="progress" cx="72" cy="72" r="54"
                        fill="none"
                        stroke="{pass_rate_color}"
                        stroke-width="12"
                        stroke-dasharray="{circumference}"
                        stroke-dashoffset="{progress}"/>
                </svg>
                <div class="{tw.HERO_VALUE}">
                    <div class="{tw.HERO_NUMBER}" style="color: {pass_rate_color}">{pass_rate:.1f}%</div>
                    <div class="{tw.HERO_LABEL}">Pass Rate</div>
                </div>
            </div>
            <div class="{tw.HERO_DETAILS}">
                <h3 class="{tw.HERO_DETAILS_H3}">Test Statistics</h3>
                <div class="{tw.DETAIL_GRID}">
                    <div class="{tw.DETAIL_ITEM}">
                        <span class="{tw.DETAIL_ITEM_LABEL}">Total Tests</span>
                        <span class="{tw.DETAIL_ITEM_VALUE}">{format_number(summary.get('total_tests'))}</span>
                    </div>
                    <div class="{tw.DETAIL_ITEM}">
                        <span class="{tw.DETAIL_ITEM_LABEL}">Average Mileage</span>
                        <span class="{tw.DETAIL_ITEM_VALUE}">{format_number(summary.get('avg_mileage'))} mi</span>
                    </div>
                    <div class="{tw.DETAIL_ITEM}">
                        <span class="{tw.DETAIL_ITEM_LABEL}">Total Passes</span>
                        <span class="{tw.DETAIL_ITEM_VALUE}">{format_number(total_passes)}</span>
                    </div>
                    <div class="{tw.DETAIL_ITEM}">
                        <span class="{tw.DETAIL_ITEM_LABEL}">Total Failures</span>
                        <span class="{tw.DETAIL_ITEM_VALUE}">{format_number(total_fails)}</span>
                    </div>
                </div>
            </div>
        </div>"""


def generate_rankings_section(rankings: dict) -> str:
    """Generate rankings badges section."""
    if not rankings:
        return ""

    badges = ""
    for rank_type, rank_data in rankings.items():
        if not rank_data:
            continue
        rank = rank_data.get("rank", "N/A")
        total = rank_data.get("total_in_category", 0)
        percentile = rank_data.get("percentile", 0)

        badges += f"""
            <div class="{tw.RANKING_BADGE}">
                <div class="{tw.RANKING_RANK}">#{rank}</div>
                <div class="{tw.RANKING_CONTEXT}">of {total} {format_ranking_type(rank_type)}</div>
                <div class="{tw.RANKING_PERCENTILE}">Top {percentile}%</div>
            </div>"""

    if not badges:
        return ""

    return f"""
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Rankings</h3>
                <i class="{tw.ICON_TROPHY} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.RANKING_BADGES}">{badges}
                </div>
            </div>
        </div>"""


def generate_severity_section(severity: list) -> str:
    """Generate failure severity breakdown section."""
    if not severity:
        return ""

    total = sum(s.get("failure_count", 0) for s in severity)
    if total == 0:
        return ""

    # Build severity bar
    bar_segments = ""
    legend_items = ""
    for s in severity:
        sev = s.get("severity", "unknown")
        count = s.get("failure_count", 0)
        pct = s.get("failure_percentage", 0)
        color = get_severity_color(sev)

        if pct > 0:
            bar_segments += f"""<div class="{tw.SEVERITY_SEGMENT}" style="width: {pct}%; background: {color};">{pct:.0f}%</div>"""
            legend_items += f"""
                <div class="{tw.SEVERITY_LEGEND_ITEM}">
                    <div class="{tw.SEVERITY_DOT}" style="background: {color};"></div>
                    <span>{sev.title()} ({format_number(count)})</span>
                </div>"""

    return f"""
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Failure Severity</h3>
                    <i class="{tw.ICON_GAUGE} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <div class="{tw.SEVERITY_BAR}">{bar_segments}</div>
                    <div class="{tw.SEVERITY_LEGEND}">{legend_items}</div>
                </div>
            </div>"""


def generate_first_mot_section(first_mot: list) -> str:
    """Generate first MOT vs subsequent section."""
    if not first_mot:
        return ""

    stats = ""
    for fm in first_mot:
        mot_type = fm.get("mot_type", "")
        rate = fm.get("pass_rate", 0)
        label = "First MOT" if mot_type == "first" else "Subsequent"

        stats += f"""
            <div class="{tw.MINI_STAT}">
                <div class="{tw.MINI_STAT_VALUE}" style="color: {get_pass_rate_color(rate)}">{rate:.1f}%</div>
                <div class="{tw.MINI_STAT_LABEL}">{label}</div>
            </div>"""

    if not stats:
        return ""

    return f"""
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">First MOT vs Subsequent</h3>
                    <i class="{tw.ICON_CAR} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY}">
                    <div class="flex gap-6 justify-center flex-wrap">{stats}</div>
                </div>
            </div>"""


def generate_retest_section(retest: dict) -> str:
    """Generate retest statistics section."""
    if not retest:
        return ""

    return f"""
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Retest Statistics</h3>
                    <i class="{tw.ICON_ARROW_CLOCKWISE} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY_COMPACT}">
                    <div class="{tw.STAT_ROW}">
                        <span class="{tw.STAT_ROW_LABEL}">Failed Tests</span>
                        <span class="{tw.STAT_ROW_VALUE}">{format_number(retest.get('failed_tests'))}</span>
                    </div>
                    <div class="{tw.STAT_ROW}">
                        <span class="{tw.STAT_ROW_LABEL}">Retested Within 30 Days</span>
                        <span class="{tw.STAT_ROW_VALUE}">{retest.get('retest_rate', 0):.1f}%</span>
                    </div>
                    <div class="{tw.STAT_ROW}">
                        <span class="{tw.STAT_ROW_LABEL}">Passed on Retest</span>
                        <span class="{tw.STAT_ROW_VALUE}">{retest.get('retest_success_rate', 0):.1f}%</span>
                    </div>
                </div>
            </div>"""


def generate_age_bands_section(age_bands: list) -> str:
    """Generate age bands chart section."""
    if not age_bands:
        return ""

    max_rate = max((a.get("pass_rate", 0) for a in age_bands), default=100)
    min_rate = min((a.get("pass_rate", 0) for a in age_bands), default=0)
    range_val = max(max_rate - min_rate, 10)

    bars = ""
    for a in age_bands:
        rate = a.get("pass_rate", 0)
        band = a.get("age_band", "")
        # Scale height relative to the range
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
        <div class="{tw.SECTION_DIVIDER}">
            <h2 class="{tw.SECTION_DIVIDER_H2}">Age Impact</h2>
            <p class="{tw.SECTION_DIVIDER_P}">How pass rate changes as the vehicle ages</p>
        </div>
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Pass Rate by Age</h3>
                <i class="{tw.ICON_CLOCK} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.AGE_CHART}">{bars}</div>
            </div>
        </div>"""


def generate_geographic_section(geographic: list) -> str:
    """Generate geographic insights section."""
    if not geographic or len(geographic) < 2:
        return ""

    # Get top 5 and bottom 5
    best = geographic[:5]
    worst = geographic[-5:][::-1]  # Reverse to show worst first

    best_rows = ""
    for g in best:
        rate = g.get("pass_rate", 0)
        best_rows += f"""
            <tr class="{tw.TR_HOVER}">
                <td class="{tw.TD} font-semibold">{g.get('postcode_area', 'N/A')}</td>
                <td class="{tw.TD}" style="color: {get_pass_rate_color(rate)}">{rate:.1f}%</td>
                <td class="{tw.TD}">{format_number(g.get('total_tests'))}</td>
            </tr>"""

    worst_rows = ""
    for g in worst:
        rate = g.get("pass_rate", 0)
        worst_rows += f"""
            <tr class="{tw.TR_HOVER}">
                <td class="{tw.TD} font-semibold">{g.get('postcode_area', 'N/A')}</td>
                <td class="{tw.TD}" style="color: {get_pass_rate_color(rate)}">{rate:.1f}%</td>
                <td class="{tw.TD}">{format_number(g.get('total_tests'))}</td>
            </tr>"""

    return f"""
        <div class="{tw.SECTION_DIVIDER}">
            <h2 class="{tw.SECTION_DIVIDER_H2}">Geographic Variation</h2>
            <p class="{tw.SECTION_DIVIDER_P}">Pass rates by UK postcode area</p>
        </div>
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Regional Pass Rates</h3>
                <i class="{tw.ICON_MAP_PIN} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.GEO_SPLIT}">
                    <div>
                        <h4 class="{tw.GEO_SECTION_TITLE_BEST}">Best Areas</h4>
                        <table class="{tw.TABLE}">
                            <thead><tr>
                                <th class="{tw.TH}">Postcode</th>
                                <th class="{tw.TH}">Pass Rate</th>
                                <th class="{tw.TH}">Tests</th>
                            </tr></thead>
                            <tbody>{best_rows}</tbody>
                        </table>
                    </div>
                    <div>
                        <h4 class="{tw.GEO_SECTION_TITLE_WORST}">Worst Areas</h4>
                        <table class="{tw.TABLE}">
                            <thead><tr>
                                <th class="{tw.TH}">Postcode</th>
                                <th class="{tw.TH}">Pass Rate</th>
                                <th class="{tw.TH}">Tests</th>
                            </tr></thead>
                            <tbody>{worst_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>"""


def generate_seasonal_section(seasonal: list) -> str:
    """Generate seasonal patterns chart."""
    if not seasonal:
        return ""

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
        <div class="{tw.SECTION_DIVIDER}">
            <h2 class="{tw.SECTION_DIVIDER_H2}">Seasonal Patterns</h2>
            <p class="{tw.SECTION_DIVIDER_P}">Monthly pass rate variation for this vehicle</p>
        </div>
        <div class="{tw.CARD}">
            <div class="{tw.CARD_HEADER}">
                <h3 class="{tw.CARD_TITLE}">Pass Rate by Month</h3>
                <i class="{tw.ICON_CALENDAR} {tw.ICON_HEADER}"></i>
            </div>
            <div class="{tw.CARD_BODY}">
                <div class="{tw.MONTHLY_CHART}">{bars}</div>
            </div>
        </div>"""


def generate_advisory_progression_section(progression: list) -> str:
    """Generate advisory to failure progression section."""
    if not progression:
        return ""

    items = ""
    for p in progression[:5]:
        desc = truncate(p.get("advisory_text", "Unknown"), 35)
        rate = p.get("progression_rate", 0)
        color = get_pass_rate_color(100 - rate)  # Invert: high progression = bad

        items += f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DATA_LIST_NAME}">{desc}</span>
                <span class="{tw.DATA_LIST_VALUE}" style="color: {color}">{rate:.1f}%</span>
            </li>"""

    return f"""
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Advisory to Failure Risk</h3>
                    <i class="{tw.ICON_INFO} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY_COMPACT}">
                    <ul class="{tw.DATA_LIST}">{items}</ul>
                    <p class="text-xs text-slate-500 mt-3">
                        Shows how often advisories become failures on subsequent tests
                    </p>
                </div>
            </div>"""


def generate_component_thresholds_section(thresholds: list) -> str:
    """Generate component mileage thresholds section."""
    if not thresholds:
        return ""

    items = ""
    for t in thresholds[:5]:
        component = truncate(t.get("component", "Unknown"), 25)
        mileage = t.get("avg_failure_mileage", 0)

        items += f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DATA_LIST_NAME}">{component}</span>
                <span class="{tw.DATA_LIST_VALUE}">{format_number(mileage)} mi</span>
            </li>"""

    return f"""
            <div class="{tw.CARD}">
                <div class="{tw.CARD_HEADER}">
                    <h3 class="{tw.CARD_TITLE}">Component Failure Mileage</h3>
                    <i class="{tw.ICON_PATH} {tw.ICON_HEADER}"></i>
                </div>
                <div class="{tw.CARD_BODY_COMPACT}">
                    <ul class="{tw.DATA_LIST}">{items}</ul>
                    <p class="text-xs text-slate-500 mt-3">
                        Average mileage when components typically fail
                    </p>
                </div>
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
