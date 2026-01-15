#!/usr/bin/env python3
"""
Make Report Static HTML Generator - MVP
========================================
Generates static HTML pages from the /api/make-report/{make} endpoint.

Usage:
    python generate_make_report.py FORD
    python generate_make_report.py FORD --output ./output/
    python generate_make_report.py --list          # Show top makes by test count
    python generate_make_report.py --top 10        # Generate top 10 makes

Requires: API server running at http://localhost:8010
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Configuration
API_BASE = "http://localhost:8010/api"
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "articles" / "make-reports"


def fetch_json(url: str) -> dict:
    """Fetch JSON from API endpoint."""
    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except URLError as e:
        print(f"Error fetching {url}: {e}")
        print("Make sure the API server is running: python api/app.py")
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


def generate_html(data: dict) -> str:
    """Generate complete HTML page from make report data."""
    make = data["make"]
    summary = data["summary"]
    ranking = data.get("ranking", {})

    today = date.today().strftime("%d %b %Y")
    pass_rate = summary.get("pass_rate", 0) or 0
    pass_rate_color = get_pass_rate_color(pass_rate)

    # Build best models table rows
    best_rows = ""
    for m in data.get("best_models", []):
        rate = m.get("pass_rate", 0) or 0
        best_rows += f"""
                <tr>
                    <td>{m.get('model', 'N/A')}</td>
                    <td>{m.get('model_year', 'N/A')}</td>
                    <td>{m.get('fuel_type', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(m.get('total_tests'))}</td>
                </tr>"""

    # Build worst models table rows
    worst_rows = ""
    for m in data.get("worst_models", []):
        rate = m.get("pass_rate", 0) or 0
        worst_rows += f"""
                <tr>
                    <td>{m.get('model', 'N/A')}</td>
                    <td>{m.get('model_year', 'N/A')}</td>
                    <td>{m.get('fuel_type', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(m.get('total_tests'))}</td>
                </tr>"""

    # Build failure categories bars (pure CSS, no Chart.js needed)
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

    # Build top failures list
    failures_list = ""
    for d in data.get("top_failures", [])[:30]:
        failures_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Build top advisories list
    advisories_list = ""
    for d in data.get("top_advisories", [])[:30]:
        advisories_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Build dangerous defects list
    dangerous_list = ""
    for d in data.get("dangerous_defects", [])[:20]:
        dangerous_list += f"""
            <li>
                <span class="defect-name">{d.get('defect_description', 'Unknown')}</span>
                <span class="defect-count dangerous">{format_number(d.get('occurrence_count'))}</span>
            </li>"""

    # Build all models table
    all_models_rows = ""
    for m in data.get("models", []):
        rate = m.get("pass_rate", 0) or 0
        all_models_rows += f"""
                <tr>
                    <td>{m.get('model', 'N/A')}</td>
                    <td>{m.get('model_year', 'N/A')}</td>
                    <td>{m.get('fuel_type', 'N/A')}</td>
                    <td><span class="badge {get_pass_rate_class(rate)}">{rate:.1f}%</span></td>
                    <td>{format_number(m.get('total_tests'))}</td>
                    <td>{format_number(m.get('avg_mileage'))}</td>
                </tr>"""

    # Dangerous defects section (only if there are any)
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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{make} MOT Reliability Report | MOT Insights</title>
    <meta name="description" content="Comprehensive MOT reliability analysis for {make} vehicles based on {format_number(summary.get('total_tests'))} real test results.">
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
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        .card {{
            background: var(--color-card);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 24px;
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

        .all-models-table {{
            max-height: 500px;
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
        }}
    </style>
</head>
<body>
    <header>
        <h1>{make} MOT Reliability Report</h1>
        <div class="subtitle">Comprehensive analysis based on {format_number(summary.get('total_tests'))} real MOT tests</div>
        {f'<div class="meta">Ranked #{ranking.get("rank")} nationally</div>' if ranking and ranking.get("rank") else ''}
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
                <div class="value">{summary.get('total_models', 'N/A')}</div>
                <div class="label">Models</div>
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

        <!-- Best & Worst Models -->
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3>Best Performing Models</h3></div>
                <div class="card-body">
                    <table>
                        <thead><tr><th>Model</th><th>Year</th><th>Fuel</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{best_rows if best_rows else '<tr><td colspan="5">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3>Worst Performing Models</h3></div>
                <div class="card-body">
                    <table>
                        <thead><tr><th>Model</th><th>Year</th><th>Fuel</th><th>Pass Rate</th><th>Tests</th></tr></thead>
                        <tbody>{worst_rows if worst_rows else '<tr><td colspan="5">No data available</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Failure Categories -->
        <div class="card">
            <div class="card-header"><h3>Top Failure Categories</h3></div>
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

        <!-- All Models Table -->
        <div class="card">
            <div class="card-header"><h3>All Models ({len(data.get('models', []))})</h3></div>
            <div class="card-body all-models-table">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Year</th>
                            <th>Fuel</th>
                            <th>Pass Rate</th>
                            <th>Tests</th>
                            <th>Avg Mileage</th>
                        </tr>
                    </thead>
                    <tbody>{all_models_rows if all_models_rows else '<tr><td colspan="6">No data available</td></tr>'}
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


def generate_make_report(make: str, output_dir: Path) -> Path:
    """Generate HTML report for a single make."""
    print(f"Fetching data for {make}...")
    data = fetch_json(f"{API_BASE}/make-report/{make}")

    print(f"Generating HTML...")
    html = generate_html(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{make.lower().replace(' ', '-')}-report.html"
    output_path = output_dir / filename

    output_path.write_text(html, encoding='utf-8')
    print(f"Saved: {output_path}")

    return output_path


def list_makes(limit: int = 20) -> list[dict]:
    """Get list of makes sorted by test count."""
    manufacturers = fetch_json(f"{API_BASE}/manufacturers")
    # Sort by total_tests descending
    sorted_makes = sorted(manufacturers, key=lambda x: x.get("total_tests", 0), reverse=True)
    return sorted_makes[:limit]


def main():
    parser = argparse.ArgumentParser(description="Generate static HTML make reports")
    parser.add_argument("make", nargs="?", help="Vehicle make (e.g., FORD, TOYOTA)")
    parser.add_argument("--output", "-o", help="Output directory", default=str(OUTPUT_DIR))
    parser.add_argument("--list", "-l", action="store_true", help="List top makes by test count")
    parser.add_argument("--top", type=int, help="Generate reports for top N makes")

    args = parser.parse_args()

    output_dir = Path(args.output)

    # List mode
    if args.list:
        makes = list_makes(50)
        print(f"\n{'#':<4} {'Make':<20} {'Tests':>12} {'Pass Rate':>10} {'Rank':>6}")
        print("-" * 56)
        for i, m in enumerate(makes, 1):
            print(f"{i:<4} {m['make']:<20} {m['total_tests']:>12,} {m['avg_pass_rate']:>9.1f}% #{m['rank']:>4}")
        return

    # Batch mode - generate top N
    if args.top:
        makes = list_makes(args.top)
        print(f"\nGenerating reports for top {args.top} makes...\n")

        success = 0
        for i, m in enumerate(makes, 1):
            try:
                print(f"[{i}/{len(makes)}] ", end="")
                generate_make_report(m["make"], output_dir)
                success += 1
            except Exception as e:
                print(f"Error generating {m['make']}: {e}")

        print(f"\nDone! Generated {success}/{len(makes)} reports")
        print(f"Output: {output_dir}")
        return

    # Single make mode
    if args.make:
        generate_make_report(args.make.upper(), output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
