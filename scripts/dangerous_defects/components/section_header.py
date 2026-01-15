"""
Header and key findings section generators.
"""

from .utils import format_number, safe_html, title_case


def generate_header_section(insights, today_display: str) -> str:
    """Generate the article header."""
    return f'''      <!-- Header -->
      <header class="mb-8">
        <div class="flex flex-wrap items-center gap-3 mb-4">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
            <i class="ph ph-warning"></i>
            Safety Data
          </span>
          <span class="text-sm text-neutral-500">15 min read</span>
          <span class="text-sm text-neutral-500">Updated {today_display}</span>
        </div>

        <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
          {safe_html(insights.title)}
        </h1>

        <p class="text-lg text-neutral-600">
          We analysed {format_number(insights.total_tests)} real UK MOT tests to reveal which cars
          are most likely to have dangerous defects that make them unsafe to drive.
        </p>
      </header>

      <!-- Data Source Callout -->
      <div class="danger-callout">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-600 text-white flex items-center justify-center">
            <i class="ph ph-warning-circle text-xl"></i>
          </div>
          <div>
            <p class="font-semibold text-red-900">{format_number(insights.total_dangerous)} dangerous defects recorded</p>
            <p class="text-red-800 text-sm">Real DVSA data from {format_number(insights.total_tests)} MOT tests. Dangerous defects mean a vehicle should not be driven until fixed.</p>
          </div>
        </div>
      </div>'''


def generate_key_findings_section(insights) -> str:
    """Generate the key findings summary boxes."""
    most_dangerous = insights.most_dangerous_model
    safest = insights.safest_model
    worst_make = insights.worst_make
    safest_make = insights.safest_make

    return f'''      <!-- Key Findings Summary -->
      <div class="bg-neutral-50 rounded-xl p-6 mb-10">
        <h2 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <i class="ph ph-lightning text-red-600"></i>
          Key Findings
        </h2>
        <div class="grid sm:grid-cols-2 gap-4">
          <div class="bg-white rounded-lg p-4 border border-red-200 border-l-4 border-l-red-500">
            <p class="text-sm text-neutral-500 mb-1">Most Dangerous Model</p>
            <p class="text-lg font-semibold text-neutral-900">{safe_html(title_case(most_dangerous.get('make', '')))} {safe_html(title_case(most_dangerous.get('model', '')))}</p>
            <p class="text-sm text-red-600">{most_dangerous.get('rate', 0):.2f}% dangerous defect rate</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-emerald-200 border-l-4 border-l-emerald-500">
            <p class="text-sm text-neutral-500 mb-1">Safest Model</p>
            <p class="text-lg font-semibold text-neutral-900">{safe_html(title_case(safest.get('make', '')))} {safe_html(title_case(safest.get('model', '')))}</p>
            <p class="text-sm text-emerald-600">{safest.get('rate', 0):.2f}% dangerous defect rate</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-neutral-200">
            <p class="text-sm text-neutral-500 mb-1">Worst Manufacturer</p>
            <p class="text-lg font-semibold text-neutral-900">{safe_html(title_case(worst_make.get('make', '')))}</p>
            <p class="text-sm text-red-600">{worst_make.get('dangerous_rate', 0):.2f}% dangerous defect rate</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-neutral-200">
            <p class="text-sm text-neutral-500 mb-1">Safest Manufacturer</p>
            <p class="text-lg font-semibold text-neutral-900">{safe_html(title_case(safest_make.get('make', '')))}</p>
            <p class="text-sm text-emerald-600">{safest_make.get('dangerous_rate', 0):.2f}% dangerous defect rate</p>
          </div>
        </div>

        <div class="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p class="text-sm text-amber-800 flex items-center gap-2">
            <i class="ph ph-info text-amber-600"></i>
            <span>There's a <strong>{insights.rate_difference_factor}x difference</strong> between the safest and most dangerous models - choose wisely.</span>
          </p>
        </div>
      </div>'''


def generate_intro_section(insights) -> str:
    """Generate the introduction prose."""
    return f'''      <!-- Introduction -->
      <div class="article-prose text-lg mb-10">
        <p>
          Every year, millions of UK vehicles undergo MOT tests. When an examiner finds a fault so severe
          that the vehicle should not be driven until it's fixed, it's recorded as a <strong>"dangerous defect"</strong>.
          These aren't minor issues - they're faults that could cause serious accidents.
        </p>
        <p>
          We analysed <strong>{format_number(insights.total_tests)} MOT tests</strong> from the official DVSA
          database to find out which cars are most likely to have these dangerous defects. The results reveal
          significant differences between manufacturers and models that every car buyer should know about.
        </p>
        <p>
          The overall dangerous defect rate across all vehicles is <strong>{insights.overall_rate:.2f}%</strong>.
          But some models have rates more than {insights.rate_difference_factor}x higher than the safest cars on the road.
        </p>
      </div>'''
