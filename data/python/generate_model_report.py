#!/usr/bin/env python3
"""
Model Report Static HTML Generator - MVP
=========================================
Generates static HTML pages for individual MODELS (all year/fuel variants).

Usage:
    python generate_model_report.py FORD FOCUS
    python generate_model_report.py "LAND ROVER" "RANGE ROVER"
    python generate_model_report.py --list FORD           # List models for a make
    python generate_model_report.py --top 100             # Generate top 100 most-tested models

Requires: API server running at http://localhost:8010
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import quote

# Configuration
API_BASE = "http://localhost:8010/api"
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "articles" / "model-reports"


def fetch_json(url: str) -> dict:
    """Fetch JSON from API endpoint."""
    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except URLError as e:
        print(f"Error fetching {url}: {e}")
        print("Make sure the API server is running: python -m api.backend.main")
        sys.exit(1)


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


def format_number(n) -> str:
    """Format number with commas."""
    if n is None:
        return "N/A"
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


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


def aggregate_model_data(make: str, model: str) -> dict:
    """Fetch and aggregate all variant data for a model."""
    # URL encode make and model for API calls
    make_enc = quote(make, safe='')
    model_enc = quote(model, safe='')

    # Get all variants for this model
    variants_url = f"{API_BASE}/makes/{make_enc}/models/{model_enc}/variants"
    variants = fetch_json(variants_url)

    if not variants:
        return None

    # Fetch full data for each variant
    variant_reports = []
    for v in variants:
        year = v["model_year"]
        fuel = v["fuel_type"]
        try:
            report_url = f"{API_BASE}/vehicle/{make_enc}/{model_enc}/{year}/{fuel}"
            report = fetch_json(report_url)
            variant_reports.append(report)
        except Exception as e:
            print(f"  Warning: Failed to fetch {year} {fuel}: {e}")

    if not variant_reports:
        return None

    # Aggregate the data
    total_tests = 0
    total_passes = 0
    total_fails = 0
    mileage_sum = 0
    mileage_count = 0
    age_sum = 0
    age_count = 0

    # Collect all variants with their stats
    all_variants = []
    for r in variant_reports:
        insights = r.get("insights", {}) or {}
        tests = insights.get("total_tests", 0) or 0
        passes = insights.get("total_passes", 0) or 0
        fails = insights.get("total_fails", 0) or 0

        total_tests += tests
        total_passes += passes
        total_fails += fails

        if insights.get("avg_mileage"):
            mileage_sum += insights["avg_mileage"] * tests
            mileage_count += tests

        if insights.get("avg_age_years"):
            age_sum += insights["avg_age_years"] * tests
            age_count += tests

        pass_rate = (passes / tests * 100) if tests > 0 else 0

        all_variants.append({
            "year": r["vehicle"]["model_year"],
            "fuel_type": r["vehicle"]["fuel_type"],
            "fuel_type_name": r["vehicle"]["fuel_type_name"],
            "total_tests": tests,
            "pass_rate": pass_rate,
            "avg_mileage": insights.get("avg_mileage"),
            "insights": insights,
            "mileage_bands": r.get("mileage_bands", []),
            "failure_categories": r.get("failure_categories", []),
            "top_failures": r.get("top_failures", []),
            "top_advisories": r.get("top_advisories", []),
            "dangerous_defects": r.get("dangerous_defects", []),
        })

    # Sort variants by pass rate (best first)
    all_variants.sort(key=lambda x: x["pass_rate"], reverse=True)

    # Calculate overall pass rate
    overall_pass_rate = (total_passes / total_tests * 100) if total_tests > 0 else 0

    # Find best and worst years
    best_variant = all_variants[0] if all_variants else None
    worst_variant = all_variants[-1] if all_variants else None

    # Aggregate by fuel type
    fuel_stats = {}
    for v in all_variants:
        fuel = v["fuel_type_name"]
        if fuel not in fuel_stats:
            fuel_stats[fuel] = {"tests": 0, "passes": 0, "variants": 0}
        fuel_stats[fuel]["tests"] += v["total_tests"]
        fuel_stats[fuel]["passes"] += int(v["total_tests"] * v["pass_rate"] / 100)
        fuel_stats[fuel]["variants"] += 1

    fuel_comparison = []
    for fuel, stats in fuel_stats.items():
        fuel_comparison.append({
            "fuel_type": fuel,
            "total_tests": stats["tests"],
            "pass_rate": (stats["passes"] / stats["tests"] * 100) if stats["tests"] > 0 else 0,
            "variants": stats["variants"],
        })
    fuel_comparison.sort(key=lambda x: x["pass_rate"], reverse=True)

    # Aggregate by year (across all fuel types)
    year_stats = {}
    for v in all_variants:
        year = v["year"]
        if year not in year_stats:
            year_stats[year] = {"tests": 0, "passes": 0}
        year_stats[year]["tests"] += v["total_tests"]
        year_stats[year]["passes"] += int(v["total_tests"] * v["pass_rate"] / 100)

    year_comparison = []
    for year, stats in year_stats.items():
        year_comparison.append({
            "year": year,
            "total_tests": stats["tests"],
            "pass_rate": (stats["passes"] / stats["tests"] * 100) if stats["tests"] > 0 else 0,
        })
    year_comparison.sort(key=lambda x: x["year"])

    # Aggregate failure categories
    category_totals = {}
    for v in all_variants:
        for cat in v.get("failure_categories", []):
            name = cat.get("category_name", "Unknown")
            count = cat.get("failure_count", 0)
            if name not in category_totals:
                category_totals[name] = 0
            category_totals[name] += count

    failure_categories = [
        {"category_name": name, "failure_count": count}
        for name, count in sorted(category_totals.items(), key=lambda x: -x[1])
    ][:10]

    # Aggregate top failures
    failure_totals = {}
    for v in all_variants:
        for f in v.get("top_failures", []):
            desc = f.get("defect_description", "Unknown")
            count = f.get("occurrence_count", 0)
            if desc not in failure_totals:
                failure_totals[desc] = 0
            failure_totals[desc] += count

    top_failures = [
        {"defect_description": desc, "occurrence_count": count}
        for desc, count in sorted(failure_totals.items(), key=lambda x: -x[1])
    ][:30]

    # Aggregate top advisories
    advisory_totals = {}
    for v in all_variants:
        for a in v.get("top_advisories", []):
            desc = a.get("defect_description", "Unknown")
            count = a.get("occurrence_count", 0)
            if desc not in advisory_totals:
                advisory_totals[desc] = 0
            advisory_totals[desc] += count

    top_advisories = [
        {"defect_description": desc, "occurrence_count": count}
        for desc, count in sorted(advisory_totals.items(), key=lambda x: -x[1])
    ][:30]

    # Aggregate dangerous defects
    dangerous_totals = {}
    for v in all_variants:
        for d in v.get("dangerous_defects", []):
            desc = d.get("defect_description", "Unknown")
            count = d.get("occurrence_count", 0)
            if desc not in dangerous_totals:
                dangerous_totals[desc] = 0
            dangerous_totals[desc] += count

    dangerous_defects = [
        {"defect_description": desc, "occurrence_count": count}
        for desc, count in sorted(dangerous_totals.items(), key=lambda x: -x[1])
    ][:20]

    # Aggregate mileage bands
    mileage_totals = {}
    for v in all_variants:
        for mb in v.get("mileage_bands", []):
            band = mb.get("mileage_band", "Unknown")
            order = mb.get("band_order", 0)
            tests = mb.get("total_tests", 0)
            passes = int(tests * (mb.get("pass_rate", 0) / 100))
            if band not in mileage_totals:
                mileage_totals[band] = {"order": order, "tests": 0, "passes": 0}
            mileage_totals[band]["tests"] += tests
            mileage_totals[band]["passes"] += passes

    mileage_bands = [
        {
            "mileage_band": band,
            "band_order": data["order"],
            "total_tests": data["tests"],
            "pass_rate": (data["passes"] / data["tests"] * 100) if data["tests"] > 0 else 0,
        }
        for band, data in sorted(mileage_totals.items(), key=lambda x: x[1]["order"])
    ]

    return {
        "make": make.upper(),
        "model": model.upper(),
        "summary": {
            "total_variants": len(all_variants),
            "total_tests": total_tests,
            "pass_rate": overall_pass_rate,
            "avg_mileage": (mileage_sum / mileage_count) if mileage_count > 0 else None,
            "avg_age_years": round(age_sum / age_count, 1) if age_count > 0 else None,
            "year_range": f"{min(v['year'] for v in all_variants)}-{max(v['year'] for v in all_variants)}" if all_variants else "N/A",
        },
        "best_variant": best_variant,
        "worst_variant": worst_variant,
        "fuel_comparison": fuel_comparison,
        "year_comparison": year_comparison,
        "all_variants": all_variants,
        "failure_categories": failure_categories,
        "top_failures": top_failures,
        "top_advisories": top_advisories,
        "dangerous_defects": dangerous_defects,
        "mileage_bands": mileage_bands,
    }


def generate_html(data: dict) -> str:
    """Generate complete HTML page from model report data."""
    make = data["make"]
    model = data["model"]
    summary = data["summary"]

    today = date.today().strftime("%d %b %Y")
    pass_rate = summary.get("pass_rate", 0) or 0
    pass_rate_color = get_pass_rate_color(pass_rate)

    # Best year to buy section
    best = data.get("best_variant")
    best_html = ""
    if best:
        best_html = f"""
        <div class="card highlight-good">
            <div class="card-header"><h3>Best Year to Buy</h3></div>
            <div class="card-body">
                <div class="highlight-stat">
                    <span class="highlight-value">{best['year']} {best['fuel_type_name']}</span>
                    <span class="badge good">{best['pass_rate']:.1f}% pass rate</span>
                </div>
                <p class="highlight-detail">Based on {format_number(best['total_tests'])} MOT tests</p>
            </div>
        </div>"""

    # Worst year to avoid section
    worst = data.get("worst_variant")
    worst_html = ""
    if worst and worst != best:
        worst_html = f"""
        <div class="card highlight-poor">
            <div class="card-header"><h3>Year to Avoid</h3></div>
            <div class="card-body">
                <div class="highlight-stat">
                    <span class="highlight-value">{worst['year']} {worst['fuel_type_name']}</span>
                    <span class="badge poor">{worst['pass_rate']:.1f}% pass rate</span>
                </div>
                <p class="highlight-detail">Based on {format_number(worst['total_tests'])} MOT tests</p>
            </div>
        </div>"""

    # Fuel type comparison
    fuel_rows = ""
    for f in data.get("fuel_comparison", []):
        rate = f.get("pass_rate", 0)
        fuel_rows += f"""
                <tr>
                    <td>{f.get('fuel_type', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(f.get('total_tests'))}</td>
                    <td>{f.get('variants', 0)}</td>
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
            <div class="year-bar-col">
                <div class="year-bar-wrapper">
                    <div class="year-bar" style="height: {height_pct}%; background: {get_pass_rate_color(rate)};" title="{rate:.1f}%"></div>
                </div>
                <div class="year-label">{y['year']}</div>
                <div class="year-rate">{rate:.0f}%</div>
            </div>"""

    # Mileage impact section
    mileage_rows = ""
    for mb in data.get("mileage_bands", []):
        rate = mb.get("pass_rate", 0)
        mileage_rows += f"""
                <tr>
                    <td>{mb.get('mileage_band', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(mb.get('total_tests'))}</td>
                </tr>"""

    # Build failure categories bars
    categories = data.get("failure_categories", [])[:10]
    max_failures = max((c.get("failure_count", 0) for c in categories), default=1)

    failure_bars = ""
    for cat in categories:
        count = cat.get("failure_count", 0)
        pct = (count / max_failures * 100) if max_failures > 0 else 0
        failure_bars += f"""
            <div class="bar-row">
                <div class="bar-label">{cat.get('category_name', 'Unknown')[:30]}</div>
                <div class="bar-container">
                    <div class="bar" style="width: {pct}%"></div>
                    <span class="bar-value">{format_number(count)}</span>
                </div>
            </div>"""

    # Top failures list
    failures_list = ""
    for d in data.get("top_failures", [])[:30]:
        failures_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Top advisories list
    advisories_list = ""
    for d in data.get("top_advisories", [])[:30]:
        advisories_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Dangerous defects
    dangerous_list = ""
    for d in data.get("dangerous_defects", [])[:20]:
        dangerous_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count dangerous">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    dangerous_section = ""
    if data.get("dangerous_defects"):
        dangerous_section = f"""
        <div class="card">
            <div class="card-header">
                <h3 class="dangerous-title">Dangerous Defects ({len(data['dangerous_defects'])})</h3>
            </div>
            <div class="card-body">
                <ul class="defect-list">{dangerous_list}
                </ul>
            </div>
        </div>
        """

    # All variants table
    all_variants_rows = ""
    for v in data.get("all_variants", []):
        rate = v.get("pass_rate", 0)
        all_variants_rows += f"""
                <tr>
                    <td>{v.get('year', 'N/A')}</td>
                    <td>{v.get('fuel_type_name', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(v.get('total_tests'))}</td>
                    <td>{format_number(v.get('avg_mileage'))}</td>
                </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{make} {model} MOT Reliability Report | MOT Insights</title>
    <meta name="description" content="Complete MOT reliability analysis for {make} {model} ({summary.get('year_range', 'all years')}) based on {format_number(summary.get('total_tests'))} real test results. Find the best year to buy.">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        :root {{
            --color-good: #10b981;
            --color-average: #f59e0b;
            --color-poor: #ef4444;
            --color-primary: #1e3a5f;
            --color-primary-light: #2d5a8a;
            --color-bg: #f8fafc;
            --color-card: #ffffff;
            --color-text: #1e293b;
            --color-text-muted: #64748b;
            --color-border: #e2e8f0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
        }}

        header {{
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
            color: white;
            padding: 32px;
        }}

        header h1 {{
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        header .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        header .meta {{
            margin-top: 16px;
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}

        .stat-card {{
            background: var(--color-card);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .stat-card .value {{
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .stat-card .label {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
        }}

        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        .card {{
            background: var(--color-card);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 24px;
        }}

        .card.highlight-good {{
            border-left: 4px solid var(--color-good);
        }}

        .card.highlight-poor {{
            border-left: 4px solid var(--color-poor);
        }}

        .card-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--color-border);
        }}

        .card-header h3 {{
            font-size: 1.1rem;
            font-weight: 600;
        }}

        .card-body {{
            padding: 20px;
        }}

        .highlight-stat {{
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }}

        .highlight-value {{
            font-size: 1.5rem;
            font-weight: 700;
        }}

        .highlight-detail {{
            margin-top: 8px;
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--color-border);
        }}

        th {{
            background: var(--color-bg);
            font-weight: 600;
            color: var(--color-text-muted);
            font-size: 0.8rem;
            text-transform: uppercase;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .badge.good {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge.average {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge.poor {{
            background: #fee2e2;
            color: #991b1b;
        }}

        /* Year trend chart */
        .year-chart {{
            display: flex;
            align-items: flex-end;
            gap: 8px;
            height: 200px;
            padding: 20px 0;
            overflow-x: auto;
        }}

        .year-bar-col {{
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 40px;
        }}

        .year-bar-wrapper {{
            height: 120px;
            width: 30px;
            display: flex;
            align-items: flex-end;
        }}

        .year-bar {{
            width: 100%;
            border-radius: 4px 4px 0 0;
            transition: height 0.3s;
        }}

        .year-label {{
            font-size: 0.75rem;
            margin-top: 8px;
            color: var(--color-text-muted);
        }}

        .year-rate {{
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--color-text);
        }}

        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}

        .bar-label {{
            width: 200px;
            font-size: 0.85rem;
            color: var(--color-text);
            flex-shrink: 0;
        }}

        .bar-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .bar {{
            height: 24px;
            background: var(--color-primary);
            border-radius: 4px;
            min-width: 4px;
        }}

        .bar-value {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
            min-width: 60px;
        }}

        .defect-list {{
            list-style: none;
            max-height: 400px;
            overflow-y: auto;
        }}

        .defect-list li {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--color-border);
            font-size: 0.9rem;
        }}

        .defect-list li:last-child {{
            border-bottom: none;
        }}

        .defect-name {{
            flex: 1;
            padding-right: 16px;
        }}

        .defect-count {{
            font-weight: 600;
            color: var(--color-text-muted);
        }}

        .defect-count.dangerous {{
            color: var(--color-poor);
        }}

        .dangerous-title {{
            color: var(--color-poor);
        }}

        .all-variants-table {{
            max-height: 400px;
            overflow-y: auto;
        }}

        footer {{
            text-align: center;
            padding: 32px;
            color: var(--color-text-muted);
            font-size: 0.85rem;
        }}

        @media (max-width: 600px) {{
            .grid-2 {{
                grid-template-columns: 1fr;
            }}
            .bar-label {{
                width: 120px;
                font-size: 0.75rem;
            }}
            .highlight-stat {{
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{make} {model} MOT Reliability Report</h1>
        <div class="subtitle">Comprehensive analysis based on {format_number(summary.get('total_tests'))} real MOT tests</div>
        <div class="meta">Years: {summary.get('year_range', 'N/A')} | {summary.get('total_variants', 0)} variants analysed</div>
        <div class="meta">Updated {today}</div>
    </header>

    <div class="container">
        <!-- Summary Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value" style="color: {pass_rate_color}">{pass_rate:.1f}%</div>
                <div class="label">Overall Pass Rate</div>
            </div>
            <div class="stat-card">
                <div class="value">{format_number(summary.get('total_tests'))}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('total_variants', 'N/A')}</div>
                <div class="label">Variants</div>
            </div>
            <div class="stat-card">
                <div class="value">{format_number(summary.get('avg_mileage'))}</div>
                <div class="label">Avg Mileage</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('avg_age_years', 'N/A')}</div>
                <div class="label">Avg Age (Years)</div>
            </div>
        </div>

        <!-- Best & Worst Year Highlights -->
        <div class="grid-2">
            {best_html}
            {worst_html}
        </div>

        <!-- Year Trend Chart -->
        <div class="card">
            <div class="card-header"><h3>Pass Rate by Year</h3></div>
            <div class="card-body">
                <div class="year-chart">{year_bars if year_bars else '<p>No year data available</p>'}
                </div>
            </div>
        </div>

        <!-- Fuel Type Comparison -->
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3>Fuel Type Comparison</h3></div>
                <div class="card-body">
                    <table>
                        <thead><tr><th>Fuel Type</th><th>Pass Rate</th><th>Tests</th><th>Variants</th></tr></thead>
                        <tbody>{fuel_rows if fuel_rows else '<tr><td colspan="4">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Mileage Impact -->
            <div class="card">
                <div class="card-header"><h3>Mileage Impact on Pass Rate</h3></div>
                <div class="card-body">
                    <table>
                        <thead><tr><th>Mileage Band</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{mileage_rows if mileage_rows else '<tr><td colspan="3">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Failure Categories -->
        <div class="card">
            <div class="card-header"><h3>Common Failure Categories</h3></div>
            <div class="card-body">{failure_bars if failure_bars else '<p>No data available</p>'}
            </div>
        </div>

        <!-- Top Failures & Advisories -->
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3>Top Failures ({len(data.get('top_failures', []))})</h3></div>
                <div class="card-body">
                    <ul class="defect-list">{failures_list if failures_list else '<li>No failures recorded</li>'}
                    </ul>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3>Top Advisories ({len(data.get('top_advisories', []))})</h3></div>
                <div class="card-body">
                    <ul class="defect-list">{advisories_list if advisories_list else '<li>No advisories recorded</li>'}
                    </ul>
                </div>
            </div>
        </div>

        <!-- Dangerous Defects -->
        {dangerous_section}

        <!-- All Variants Table -->
        <div class="card">
            <div class="card-header"><h3>All Variants ({len(data.get('all_variants', []))})</h3></div>
            <div class="card-body all-variants-table">
                <table>
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Fuel</th>
                            <th>Pass Rate</th>
                            <th>Tests</th>
                            <th>Avg Mileage</th>
                        </tr>
                    </thead>
                    <tbody>{all_variants_rows if all_variants_rows else '<tr><td colspan="5">No data available</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <footer>
        <p>Data source: UK DVSA MOT test records | Generated {today}</p>
        <p>MOT Insights - Real reliability data for UK vehicles</p>
    </footer>
</body>
</html>
"""
    return html


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
    # Create filename: ford-focus-report.html
    safe_make = make.lower().replace(' ', '-').replace('(', '').replace(')', '')
    safe_model = model.lower().replace(' ', '-').replace('(', '').replace(')', '')
    filename = f"{safe_make}-{safe_model}-report.html"
    output_path = output_dir / filename

    output_path.write_text(html, encoding='utf-8')
    print(f"Saved: {output_path}")

    return output_path


def list_models_for_make(make: str) -> list[str]:
    """Get list of models for a make."""
    make_enc = quote(make, safe='')
    models = fetch_json(f"{API_BASE}/makes/{make_enc}/models")
    return models


def get_top_models(limit: int = 100) -> list[dict]:
    """Get top N models by total test count across all makes."""
    # First get all makes
    makes = fetch_json(f"{API_BASE}/makes")

    print(f"Scanning {len(makes)} makes for top models...")
    all_models = []

    for make in makes:
        make_enc = quote(make, safe='')
        models = fetch_json(f"{API_BASE}/makes/{make_enc}/models")
        for model in models:
            model_enc = quote(model, safe='')
            variants = fetch_json(f"{API_BASE}/makes/{make_enc}/models/{model_enc}/variants")
            total_tests = sum(v.get("total_tests", 0) for v in variants)
            if total_tests > 0:
                all_models.append({
                    "make": make,
                    "model": model,
                    "total_tests": total_tests,
                    "variants": len(variants),
                })

    # Sort by test count
    all_models.sort(key=lambda x: x["total_tests"], reverse=True)
    return all_models[:limit]


def main():
    parser = argparse.ArgumentParser(description="Generate static HTML model reports")
    parser.add_argument("make", nargs="?", help="Vehicle make (e.g., FORD)")
    parser.add_argument("model", nargs="?", help="Vehicle model (e.g., FOCUS)")
    parser.add_argument("--output", "-o", help="Output directory", default=str(OUTPUT_DIR))
    parser.add_argument("--list", "-l", action="store_true", help="List models for the specified make")
    parser.add_argument("--top", type=int, help="Generate reports for top N most-tested models")

    args = parser.parse_args()
    output_dir = Path(args.output)

    # List models for a make
    if args.list:
        if not args.make:
            print("Error: --list requires a make name")
            print("Example: python generate_model_report.py --list FORD")
            sys.exit(1)

        models = list_models_for_make(args.make.upper())
        print(f"\nModels for {args.make.upper()} ({len(models)} total):")
        print("-" * 40)
        for m in models:
            print(f"  {m}")
        return

    # Generate top N models
    if args.top:
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

    # Single model mode
    if args.make and args.model:
        generate_model_report(args.make.upper(), args.model.upper(), output_dir)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python generate_model_report.py FORD FOCUS")
        print("  python generate_model_report.py --list FORD")
        print("  python generate_model_report.py --top 100")


if __name__ == "__main__":
    main()
