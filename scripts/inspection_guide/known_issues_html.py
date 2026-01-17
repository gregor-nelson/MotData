"""
HTML Generator for Known Issues Reports

Generates buyer-friendly HTML pages highlighting model-specific
known issues rather than raw defect data dumps.
"""

from datetime import date
from .known_issues import KnownIssuesReport, KnownIssue, GroupedKnownIssue, SystemSummary


def format_mileage_band(band: str | None) -> str:
    """Convert mileage band to readable format."""
    if not band:
        return ""
    # "60-90k" -> "60,000 - 90,000 miles"
    mapping = {
        "0-30k": "0 - 30,000 miles",
        "30-60k": "30,000 - 60,000 miles",
        "60-90k": "60,000 - 90,000 miles",
        "90-120k": "90,000 - 120,000 miles",
        "120-150k": "120,000 - 150,000 miles",
        "150k+": "150,000+ miles",
    }
    return mapping.get(band, band)


def format_rate_as_one_in(rate_percentage: float) -> str:
    """
    Convert a percentage rate to '1 in X' format for clarity.

    e.g., 2.42% -> "1 in 41"
    """
    if rate_percentage <= 0:
        return ""
    one_in = round(100 / rate_percentage)
    if one_in < 1:
        one_in = 1
    return f"1 in {one_in:,}"


def format_years(years: list[int] | None) -> str:
    """Format affected years as range."""
    if not years or len(years) == 0:
        return ""
    if len(years) == 1:
        return str(years[0])
    return f"{min(years)} - {max(years)}"


def generate_issue_card(issue: KnownIssue, severity_class: str, icon: str, make: str = "", model: str = "") -> str:
    """Generate HTML card for a single (ungrouped) known issue with clear insights."""

    # Format "1 in X" rate
    one_in_rate = format_rate_as_one_in(issue.model_rate)

    # Mileage context
    mileage_html = ""
    if issue.typical_mileage:
        mileage_display = format_mileage_band(issue.typical_mileage)
        premature_note = ""
        if issue.is_premature:
            premature_note = ' <span class="text-amber-600 font-medium">(earlier than typical)</span>'
        mileage_html = f"""
        <div class="flex items-start gap-2 text-sm text-neutral-600">
          <i class="ph ph-gauge text-neutral-400 mt-0.5"></i>
          <span>Usually occurs around {mileage_display}{premature_note}</span>
        </div>"""

    # Affected years context
    years_html = ""
    if issue.affected_years:
        years_display = format_years(issue.affected_years)
        years_html = f"""
        <div class="flex items-start gap-2 text-sm text-neutral-600">
          <i class="ph ph-calendar text-neutral-400 mt-0.5"></i>
          <span>Most affected years: {years_display}</span>
        </div>"""

    model_name = f"{make} {model}".strip() if make or model else "this model"

    return f"""
    <div class="bg-white border {severity_class} rounded-lg p-5 shadow-sm">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">{icon}</div>
          <div>
            <p class="text-sm text-neutral-500 mb-1">{issue.category_name}</p>
            <h3 class="font-medium text-neutral-900 leading-snug">{issue.defect_description}</h3>
          </div>
        </div>
        <div class="flex-shrink-0 text-right">
          <span class="text-3xl font-bold text-neutral-900">{issue.ratio}×</span>
        </div>
      </div>

      <div class="bg-neutral-50 rounded-lg p-3 mb-4">
        <p class="text-sm text-neutral-700 leading-relaxed">
          <strong>{one_in_rate}</strong> {model_name} MOT tests fail on this.
          This is <strong>{issue.ratio}× the rate</strong> seen on comparable vehicles.
        </p>
        <p class="text-xs text-neutral-500 mt-2">
          {issue.occurrence_count:,} recorded failures in total
        </p>
      </div>

      <div class="space-y-2">
        {mileage_html}
        {years_html}
      </div>
    </div>"""


def generate_grouped_issue_card(issue: GroupedKnownIssue, severity_class: str, icon: str, make: str = "", model: str = "") -> str:
    """Generate HTML card for a grouped component issue with clear, actionable insights."""

    # Format "1 in X" rate
    one_in_rate = format_rate_as_one_in(issue.model_rate)

    # Mileage context
    mileage_html = ""
    if issue.typical_mileage:
        mileage_display = format_mileage_band(issue.typical_mileage)
        premature_note = ""
        if issue.is_premature:
            premature_note = ' <span class="text-amber-600 font-medium">(earlier than typical for vehicle age)</span>'
        mileage_html = f"""
        <div class="flex items-start gap-2 text-sm text-neutral-600">
          <i class="ph ph-gauge text-neutral-400 mt-0.5"></i>
          <span>Usually occurs around {mileage_display}{premature_note}</span>
        </div>"""

    # Affected years context
    years_html = ""
    if issue.affected_years:
        years_display = format_years(issue.affected_years)
        years_html = f"""
        <div class="flex items-start gap-2 text-sm text-neutral-600">
          <i class="ph ph-calendar text-neutral-400 mt-0.5"></i>
          <span>Most affected years: {years_display}</span>
        </div>"""

    # MOT failure descriptions - show prominently as these ARE the insight
    variants_html = ""
    if issue.variant_descriptions:
        # Show first 3 variants directly (not collapsed)
        visible_variants = issue.variant_descriptions[:3]
        hidden_variants = issue.variant_descriptions[3:]

        variant_items = ""
        for v in visible_variants:
            variant_items += f'<li class="text-sm text-neutral-600 leading-relaxed">{v}</li>'

        hidden_html = ""
        if hidden_variants:
            hidden_items = ""
            for v in hidden_variants:
                hidden_items += f'<li class="text-sm text-neutral-600 leading-relaxed">{v}</li>'
            hidden_html = f"""
            <details class="mt-2">
              <summary class="text-xs text-neutral-500 cursor-pointer hover:text-neutral-700">
                + {len(hidden_variants)} more MOT failure descriptions
              </summary>
              <ul class="mt-2 space-y-2 list-disc list-inside">
                {hidden_items}
              </ul>
            </details>"""

        variants_html = f"""
        <div class="mt-3 pt-3 border-t border-neutral-100">
          <p class="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">
            Recorded MOT failures ({issue.variant_count} related types)
          </p>
          <ul class="space-y-2 list-disc list-inside text-neutral-600">
            {variant_items}
          </ul>
          {hidden_html}
        </div>"""

    # Build the card
    model_name = f"{make} {model}".strip() if make or model else "this model"

    return f"""
    <div class="bg-white border {severity_class} rounded-lg p-5 shadow-sm">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">{icon}</div>
          <div>
            <h3 class="font-semibold text-neutral-900 text-lg leading-snug">{issue.group_name}</h3>
            <p class="text-sm text-neutral-500 mt-1">{issue.category_name}</p>
          </div>
        </div>
        <div class="flex-shrink-0 text-right">
          <span class="text-3xl font-bold text-neutral-900">{issue.ratio}×</span>
        </div>
      </div>

      <div class="bg-neutral-50 rounded-lg p-3 mb-4">
        <p class="text-sm text-neutral-700 leading-relaxed">
          <strong>{one_in_rate}</strong> {model_name} MOT tests fail on this issue.
          This is <strong>{issue.ratio}× the rate</strong> seen on comparable vehicles.
        </p>
        <p class="text-xs text-neutral-500 mt-2">
          {issue.total_occurrences:,} recorded failures in total
        </p>
      </div>

      <div class="space-y-2">
        {mileage_html}
        {years_html}
      </div>
      {variants_html}
    </div>"""


def generate_grouped_major_section(issues: list[GroupedKnownIssue], make: str = "", model: str = "") -> str:
    """Generate the Major Component Issues section."""
    if not issues:
        return ""

    cards_html = ""
    for issue in issues:
        cards_html += generate_grouped_issue_card(
            issue,
            severity_class="border-red-200 bg-red-50/30",
            icon='<span class="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center"><i class="ph ph-warning-circle text-red-600 text-lg"></i></span>',
            make=make,
            model=model
        )

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-red-50 to-red-100/50 flex items-center justify-center">
          <i class="ph ph-warning text-red-600 text-xl"></i>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-neutral-900">Major Known Issues</h2>
          <p class="text-sm text-neutral-500">3× or higher than comparable vehicles - significant concern</p>
        </div>
      </div>
      <div class="space-y-4">
        {cards_html}
      </div>
    </section>"""


def generate_grouped_known_section(issues: list[GroupedKnownIssue], make: str = "", model: str = "") -> str:
    """Generate the Known Component Issues section."""
    if not issues:
        return ""

    cards_html = ""
    for issue in issues:
        cards_html += generate_grouped_issue_card(
            issue,
            severity_class="border-amber-200 bg-amber-50/30",
            icon='<span class="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center"><i class="ph ph-info text-amber-600 text-lg"></i></span>',
            make=make,
            model=model
        )

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-50 to-amber-100/50 flex items-center justify-center">
          <i class="ph ph-lightbulb text-amber-600 text-xl"></i>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-neutral-900">Known Issues</h2>
          <p class="text-sm text-neutral-500">2-3× higher than comparable vehicles - worth checking</p>
        </div>
      </div>
      <div class="space-y-4">
        {cards_html}
      </div>
    </section>"""


def generate_grouped_elevated_section(issues: list[GroupedKnownIssue]) -> str:
    """Generate the Elevated Components section (collapsible)."""
    if not issues:
        return ""

    items_html = ""
    for issue in issues:
        mileage = f" • {format_mileage_band(issue.typical_mileage)}" if issue.typical_mileage else ""
        items_html += f"""
        <div class="flex items-center justify-between py-2 border-b border-neutral-100 last:border-0">
          <div class="flex-1 pr-4">
            <p class="text-sm text-neutral-700">{issue.group_name}</p>
            <p class="text-xs text-neutral-500">{issue.category_name}{mileage}</p>
          </div>
          <span class="text-sm font-medium text-neutral-600">{issue.ratio}×</span>
        </div>"""

    return f"""
    <section class="mb-8">
      <details class="bg-neutral-50 rounded-lg">
        <summary class="px-4 py-3 cursor-pointer text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg flex items-center gap-2">
          <i class="ph ph-caret-right transition-transform details-open:rotate-90"></i>
          Worth Noting ({len(issues)} components slightly above average)
        </summary>
        <div class="px-4 pb-4">
          {items_html}
        </div>
      </details>
    </section>"""


def generate_major_issues_section(issues: list[KnownIssue], make: str = "", model: str = "") -> str:
    """Generate the Other Major Issues section (for ungrouped defects)."""
    if not issues:
        return ""

    cards_html = ""
    for issue in issues:
        cards_html += generate_issue_card(
            issue,
            severity_class="border-red-200 bg-red-50/30",
            icon='<span class="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center"><i class="ph ph-warning-circle text-red-600 text-lg"></i></span>',
            make=make,
            model=model
        )

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-red-50 to-red-100/50 flex items-center justify-center">
          <i class="ph ph-warning text-red-600 text-xl"></i>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-neutral-900">Other Major Issues</h2>
          <p class="text-sm text-neutral-500">Individual defects 3× or higher than comparable vehicles</p>
        </div>
      </div>
      <div class="space-y-4">
        {cards_html}
      </div>
    </section>"""


def generate_known_issues_section(issues: list[KnownIssue], make: str = "", model: str = "") -> str:
    """Generate the Other Known Issues section (for ungrouped defects)."""
    if not issues:
        return ""

    cards_html = ""
    for issue in issues:
        cards_html += generate_issue_card(
            issue,
            severity_class="border-amber-200 bg-amber-50/30",
            icon='<span class="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center"><i class="ph ph-info text-amber-600 text-lg"></i></span>',
            make=make,
            model=model
        )

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-50 to-amber-100/50 flex items-center justify-center">
          <i class="ph ph-lightbulb text-amber-600 text-xl"></i>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-neutral-900">Other Known Issues</h2>
          <p class="text-sm text-neutral-500">Individual defects 2-3× higher than comparable vehicles</p>
        </div>
      </div>
      <div class="space-y-4">
        {cards_html}
      </div>
    </section>"""


def generate_elevated_items_section(issues: list[KnownIssue]) -> str:
    """Generate the Elevated Items section (collapsible)."""
    if not issues:
        return ""

    items_html = ""
    for issue in issues:
        mileage = f" • {format_mileage_band(issue.typical_mileage)}" if issue.typical_mileage else ""
        items_html += f"""
        <div class="flex items-center justify-between py-2 border-b border-neutral-100 last:border-0">
          <div class="flex-1 pr-4">
            <p class="text-sm text-neutral-700">{issue.defect_description}</p>
            <p class="text-xs text-neutral-500">{issue.category_name}{mileage}</p>
          </div>
          <span class="text-sm font-medium text-neutral-600">{issue.ratio}×</span>
        </div>"""

    return f"""
    <section class="mb-8">
      <details class="bg-neutral-50 rounded-lg">
        <summary class="px-4 py-3 cursor-pointer text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg flex items-center gap-2">
          <i class="ph ph-caret-right transition-transform details-open:rotate-90"></i>
          Worth Noting ({len(issues)} items slightly above average)
        </summary>
        <div class="px-4 pb-4">
          {items_html}
        </div>
      </details>
    </section>"""


def generate_system_summary_section(systems: list[SystemSummary]) -> str:
    """Generate the System Summary section with bar chart."""
    if not systems:
        return ""

    bars_html = ""
    for sys in systems:
        # Calculate bar widths (cap at 100%)
        model_width = min(sys.model_percentage * 2, 100)  # Scale for visual
        national_width = min(sys.national_percentage * 2, 100)

        elevated_class = "text-amber-600" if sys.is_elevated else "text-neutral-600"
        elevated_icon = '<i class="ph ph-arrow-up text-amber-500 text-xs ml-1"></i>' if sys.is_elevated else ""

        bars_html += f"""
        <div class="mb-4 last:mb-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-medium {elevated_class}">{sys.category_name}{elevated_icon}</span>
            <span class="text-xs text-neutral-500">{sys.model_percentage}% (avg: {sys.national_percentage}%)</span>
          </div>
          <div class="relative h-2 bg-neutral-100 rounded-full overflow-hidden">
            <div class="absolute h-full bg-neutral-300 rounded-full" style="width: {national_width}%"></div>
            <div class="absolute h-full bg-blue-500 rounded-full" style="width: {model_width}%"></div>
          </div>
        </div>"""

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center">
          <i class="ph ph-chart-bar text-blue-600"></i>
        </div>
        <div>
          <h2 class="text-lg font-semibold text-neutral-900">System Summary</h2>
          <p class="text-sm text-neutral-500">Failure distribution by component category</p>
        </div>
      </div>
      <div class="bg-white border border-neutral-200 rounded-lg p-4">
        <div class="flex items-center gap-4 mb-4 text-xs text-neutral-500">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 bg-blue-500 rounded"></span> This model</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 bg-neutral-300 rounded"></span> National average</span>
        </div>
        {bars_html}
      </div>
    </section>"""


def generate_years_section(best_years: list[dict], worst_years: list[dict]) -> str:
    """Generate the Best/Worst Years section."""
    if not best_years:
        return ""

    best_html = ""
    for i, y in enumerate(best_years):
        stars = "★" * (5 - i) + "☆" * i
        best_html += f"""
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-3">
            <span class="text-lg font-semibold text-neutral-900">{y['model_year']}</span>
            <span class="text-amber-500 text-sm">{stars}</span>
          </div>
          <div class="text-right">
            <span class="font-medium text-green-600">{y['pass_rate']}%</span>
            <span class="text-xs text-neutral-500 ml-1">({y['total_tests']:,} tests)</span>
          </div>
        </div>"""

    worst_html = ""
    if worst_years:
        for y in worst_years:
            worst_html += f"""
            <div class="flex items-center justify-between py-2">
              <span class="text-sm text-neutral-700">{y['model_year']}</span>
              <div class="text-right">
                <span class="font-medium text-red-600">{y['pass_rate']}%</span>
                <span class="text-xs text-neutral-500 ml-1">({y['total_tests']:,} tests)</span>
              </div>
            </div>"""

    return f"""
    <section class="mb-8">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-green-50 to-green-100/50 flex items-center justify-center">
          <i class="ph ph-calendar-check text-green-600"></i>
        </div>
        <div>
          <h2 class="text-lg font-semibold text-neutral-900">Years to Consider</h2>
          <p class="text-sm text-neutral-500">MOT pass rates by model year</p>
        </div>
      </div>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-white border border-green-200 rounded-lg p-4">
          <h3 class="text-sm font-medium text-green-700 mb-3 flex items-center gap-2">
            <i class="ph ph-thumbs-up"></i> Best Years
          </h3>
          <div class="divide-y divide-neutral-100">
            {best_html}
          </div>
        </div>
        <div class="bg-white border border-neutral-200 rounded-lg p-4">
          <h3 class="text-sm font-medium text-neutral-600 mb-3 flex items-center gap-2">
            <i class="ph ph-thumbs-down"></i> Years to Avoid
          </h3>
          <div class="divide-y divide-neutral-100">
            {worst_html}
          </div>
        </div>
      </div>
    </section>"""


def generate_no_issues_section() -> str:
    """Generate section when no significant issues are found."""
    return """
    <section class="mb-8">
      <div class="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
          <i class="ph ph-check-circle text-green-600 text-2xl"></i>
        </div>
        <h2 class="text-lg font-semibold text-green-800 mb-2">No Major Known Issues</h2>
        <p class="text-sm text-green-700">
          This model doesn't show any defects significantly above average compared to similar vehicles.
          Standard pre-purchase inspection is still recommended.
        </p>
      </div>
    </section>"""


def generate_methodology_footer(total_tests: int) -> str:
    """Generate the methodology disclosure footer."""
    return f"""
    <section class="mt-8">
      <details class="bg-neutral-50 border border-neutral-200 rounded-lg">
        <summary class="px-4 py-3 cursor-pointer text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg flex items-center gap-2">
          <i class="ph ph-info"></i>
          How we identify known issues
        </summary>
        <div class="px-4 pb-4 text-sm text-neutral-600 space-y-4">
          <p>
            This analysis is based on <strong>{total_tests:,} MOT tests</strong> from DVSA records.
          </p>

          <div>
            <p class="font-medium text-neutral-700 mb-1">Comparable vehicles</p>
            <p>
              When we say a defect is "2.4× more common than comparable vehicles," we compare
              against a weighted baseline: all vehicles nationally (50%), vehicles of the
              same age (30%), and same manufacturer (20%). This accounts for normal age-related
              wear while highlighting model-specific issues.
            </p>
          </div>

          <div>
            <p class="font-medium text-neutral-700 mb-1">Known issue thresholds</p>
            <ul class="list-disc list-inside space-y-1 text-neutral-600">
              <li><strong>1.5× – 2×</strong> baseline = Slightly elevated (noted)</li>
              <li><strong>2× – 3×</strong> baseline = Known issue</li>
              <li><strong>3×+</strong> baseline = Major known issue</li>
            </ul>
          </div>

          <div>
            <p class="font-medium text-neutral-700 mb-1">Mileage estimates</p>
            <p>
              "Typical onset" mileages are derived from failure rate spikes across mileage
              bands. The band where failures increase most sharply indicates when the
              component typically reaches end of life.
            </p>
          </div>

          <p class="text-xs text-neutral-500 pt-2 border-t border-neutral-200">
            MOT data captures test failures, not all repairs made between tests.
            Always conduct a thorough inspection before purchasing any used vehicle.
          </p>
        </div>
      </details>
    </section>"""


def generate_known_issues_page(report: KnownIssuesReport) -> str:
    """
    Generate the complete HTML page for a Known Issues report.

    Args:
        report: KnownIssuesReport from generate_known_issues_report()

    Returns:
        Complete HTML string
    """
    make = report.make.title()
    model = report.model.title()
    safe_make = report.make.lower().replace(" ", "-")
    safe_model = report.model.lower().replace(" ", "-")
    total_tests_fmt = f"{report.total_tests:,}"
    today_iso = date.today().isoformat()

    # Determine if we have any significant issues (check grouped first, then individual)
    has_grouped_issues = bool(report.grouped_major_issues or report.grouped_known_issues)
    has_individual_issues = bool(report.major_issues or report.known_issues)
    has_issues = has_grouped_issues or has_individual_issues

    # Build content sections - grouped issues first (primary), then ungrouped individual
    if has_issues:
        issues_content = (
            # Grouped component issues (primary)
            generate_grouped_major_section(report.grouped_major_issues, make, model) +
            generate_grouped_known_section(report.grouped_known_issues, make, model) +
            generate_grouped_elevated_section(report.grouped_elevated_items) +
            # Individual ungrouped issues (if any)
            generate_major_issues_section(report.major_issues, make, model) +
            generate_known_issues_section(report.known_issues, make, model) +
            generate_elevated_items_section(report.elevated_items)
        )
    else:
        issues_content = (
            generate_no_issues_section() +
            generate_grouped_elevated_section(report.grouped_elevated_items) +
            generate_elevated_items_section(report.elevated_items)
        )

    system_content = generate_system_summary_section(report.system_summary)
    years_content = generate_years_section(report.best_years, report.worst_years)
    methodology_content = generate_methodology_footer(report.total_tests)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{make} {model} Known Issues | Motorwise</title>
  <meta name="description" content="Known issues and common problems with the {make} {model}, based on {total_tests_fmt} MOT test results. What to check before buying.">

  <link rel="canonical" href="https://www.motorwise.io/articles/content/known-issues/{safe_make}-{safe_model}-known-issues.html">

  <meta property="og:title" content="{make} {model} Known Issues | Motorwise">
  <meta property="og:description" content="Known issues with the {make} {model} based on {total_tests_fmt} MOT tests.">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Motorwise">

  <link rel="icon" type="image/svg+xml" href="/favicon.svg">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">

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

  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">

  <link rel="stylesheet" href="/articles/styles/articles.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <style>
    details[open] summary .ph-caret-right {{
      transform: rotate(90deg);
    }}
    @media (max-width: 767px) {{
      body {{
        background: linear-gradient(180deg, #EFF6FF 0%, #EFF6FF 60%, #FFFFFF 100%);
        min-height: 100vh;
      }}
    }}
  </style>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} Known Issues",
    "description": "Known issues and common problems with the {make} {model}",
    "author": {{ "@type": "Organization", "name": "Motorwise" }},
    "publisher": {{ "@type": "Organization", "name": "Motorwise" }},
    "datePublished": "{today_iso}",
    "dateModified": "{today_iso}"
  }}
  </script>
</head>
<body class="bg-white font-sans text-neutral-900 antialiased">
  <div id="mw-header"></div>

  <main class="max-w-3xl mx-auto px-4 py-8">
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
          Known Issues
        </span>
      </div>

      <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
        {make} {model} - Known Issues
      </h1>
      <p class="text-lg text-neutral-600 leading-relaxed">
        Model-specific issues based on {total_tests_fmt} MOT tests
      </p>
    </header>

    {issues_content}
    {system_content}
    {years_content}
    {methodology_content}
  </main>

  <footer class="max-w-3xl mx-auto px-4 py-6 text-center text-sm text-neutral-500">
    <p>&copy; {date.today().year} Motorwise. Data sourced from DVSA MOT records.</p>
  </footer>

  <script src="/header/js/header.js"></script>
</body>
</html>"""


# Test
if __name__ == "__main__":
    from .known_issues import generate_known_issues_report
    from pathlib import Path

    # Generate a sample report
    report = generate_known_issues_report("AUDI", "A4")

    if report:
        html = generate_known_issues_page(report)

        # Save to file for preview
        output_path = Path(__file__).parent.parent.parent / "articles" / "known-issues" / "audi-a4-known-issues.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        print(f"Generated: {output_path}")
    else:
        print("No report generated")
