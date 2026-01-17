"""HTML generation functions for inspection guides."""

from datetime import date
from . import tailwind_classes as tw

# Categories considered universal wear items (affect all vehicles equally)
UNIVERSAL_CATEGORIES = {
    "Tyres",
    "Visibility",  # Wipers, washer fluid
}

# Specific defect patterns that are universal wear items
# (even if category is not fully universal)
UNIVERSAL_DEFECT_PATTERNS = [
    "tread depth",
    "ply or cords exposed",
    "bulge, caused by separation",
    "tear, caused by separation",
    "cut in excess",
    "less than 1.5 mm thick",  # Brake pad wear
    "efficiency below requirements",  # Brake efficiency (wear-related)
    "not working",  # Bulbs
    "not working on dipped beam",
    "washer liquid",
    "windscreen effectively",
]


def is_universal_defect(defect_description: str, category_name: str) -> bool:
    """
    Determine if a defect is a universal wear item.

    Universal defects are things that happen to all vehicles regardless of
    make/model (tyres wearing, brake pads wearing, bulbs burning out).

    Model-specific defects are things that indicate design or quality issues
    particular to that vehicle (suspension fractures, CV joint failures).
    """
    # Check if entire category is universal
    if category_name in UNIVERSAL_CATEGORIES:
        return True

    # Check for specific universal patterns
    desc_lower = defect_description.lower()
    for pattern in UNIVERSAL_DEFECT_PATTERNS:
        if pattern.lower() in desc_lower:
            return True

    return False


def generate_head(make: str, model: str, safe_make: str, safe_model: str,
                  total_tests: str, today_iso: str) -> str:
    """Generate the complete <head> section with SEO metadata."""
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{make} {model} Buyer's Inspection Guide | Motorwise</title>
  <meta name="description" content="What to check before buying a used {make} {model}. Top MOT failure points and safety issues based on {total_tests} real test results.">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/articles/content/inspection-guides/{safe_make}-{safe_model}-inspection-guide.html">

  <!-- Open Graph -->
  <meta property="og:title" content="{make} {model} Buyer's Inspection Guide | Motorwise">
  <meta property="og:description" content="What to check before buying a used {make} {model}. Based on {total_tests} real MOT test results.">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Motorwise">

  <!-- Favicon -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- Tailwind CDN -->
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

  <!-- Phosphor Icons -->
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">

  <!-- Shared Styles -->
  <link rel="stylesheet" href="/articles/styles/articles.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <!-- Page Styles -->
  <style>
    @media (max-width: 767px) {{
      body {{
        background: linear-gradient(180deg, #EFF6FF 0%, #EFF6FF 60%, #FFFFFF 100%);
        min-height: 100vh;
      }}
    }}
  </style>

  <!-- JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} Buyer's Inspection Guide",
    "description": "What to check before buying a used {make} {model}",
    "author": {{ "@type": "Organization", "name": "Motorwise" }},
    "publisher": {{ "@type": "Organization", "name": "Motorwise" }},
    "datePublished": "{today_iso}",
    "dateModified": "{today_iso}"
  }}
  </script>
</head>"""


def generate_header(make: str, model: str, total_tests: str) -> str:
    """Generate page header with title and data source."""
    return f"""
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
          Buyer's Guide
        </span>
      </div>

      <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
        {make} {model} - Buyer's Inspection Guide
      </h1>
      <p class="text-lg text-neutral-600 leading-relaxed">
        Based on {total_tests} MOT tests
      </p>
    </header>"""


def generate_top_failures_section(failures: list[dict]) -> str:
    """Generate the Top 5 Failure Points section with universal/specific filtering.

    Returns empty string if no failures data.
    """
    if not failures:
        return ""

    # Count how many are universal vs model-specific
    universal_count = sum(
        1 for f in failures
        if is_universal_defect(f['defect_description'], f['category_name'])
    )
    has_universal = universal_count > 0
    has_specific = universal_count < len(failures)

    items_html = ""
    for i, f in enumerate(failures, 1):
        is_universal = is_universal_defect(f['defect_description'], f['category_name'])
        data_attr = 'data-universal="true"' if is_universal else 'data-universal="false"'
        items_html += f"""
        <div class="{tw.NUMBERED_ITEM} defect-item" {data_attr}>
          <span class="{tw.NUMBERED_BADGE} defect-number">{i}</span>
          <div class="flex-1">
            <div class="flex justify-between items-start">
              <span class="{tw.DEFECT_NAME}">{f['defect_description']}</span>
              <span class="{tw.DEFECT_PERCENT}">{f['percentage']}%</span>
            </div>
            <span class="{tw.DEFECT_CATEGORY}">Category: {f['category_name']}</span>
          </div>
        </div>"""

    # Only show toggle if we have both types
    toggle_html = ""
    if has_universal and has_specific:
        toggle_html = f"""
        <div class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-100">
          <p class="{tw.TEXT_MUTED}">The most common reasons this model fails its MOT</p>
          <label class="inline-flex items-center gap-2 cursor-pointer text-sm">
            <span class="text-neutral-500">Hide wear items</span>
            <div class="relative">
              <input type="checkbox" id="toggle-failures" class="sr-only peer" checked>
              <div class="w-9 h-5 bg-neutral-200 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
            </div>
          </label>
        </div>
        <p id="filter-hint" class="{tw.TEXT_MUTED} mb-3 text-xs italic">Showing model-specific issues only. Toggle to see all failures including tyres, bulbs, and brake pads.</p>"""
    else:
        toggle_html = f"""<p class="{tw.TEXT_MUTED} mb-4">The most common reasons this model fails its MOT</p>"""

    return f"""
    <section class="{tw.CARD}" id="failures-section">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-wrench {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Top Failure Points</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        {toggle_html}
        <div id="failures-list">{items_html}
        </div>
        <p id="no-specific-msg" class="hidden text-center py-4 text-neutral-400 text-sm">No model-specific failures in top results. Toggle to see all failures.</p>
      </div>
    </section>"""


def generate_advisories_section(advisories: list[dict]) -> str:
    """Generate the Advisories section with universal/specific filtering.

    Returns empty string if no advisories data.
    """
    if not advisories:
        return ""

    # Count how many are universal vs model-specific
    universal_count = sum(
        1 for a in advisories
        if is_universal_defect(a['defect_description'], a['category_name'])
    )
    has_universal = universal_count > 0
    has_specific = universal_count < len(advisories)

    items_html = ""
    for i, a in enumerate(advisories, 1):
        is_universal = is_universal_defect(a['defect_description'], a['category_name'])
        data_attr = 'data-universal="true"' if is_universal else 'data-universal="false"'
        items_html += f"""
        <div class="{tw.NUMBERED_ITEM} advisory-item" {data_attr}>
          <span class="{tw.NUMBERED_BADGE} advisory-number">{i}</span>
          <div class="flex-1">
            <div class="flex justify-between items-start">
              <span class="{tw.DEFECT_NAME}">{a['defect_description']}</span>
              <span class="{tw.DEFECT_PERCENT}">{a['percentage']}%</span>
            </div>
            <span class="{tw.DEFECT_CATEGORY}">Category: {a['category_name']}</span>
          </div>
        </div>"""

    # Only show toggle if we have both types
    toggle_html = ""
    if has_universal and has_specific:
        toggle_html = f"""
        <div class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-100">
          <p class="{tw.TEXT_MUTED}">Items noted but not causing immediate failure</p>
          <label class="inline-flex items-center gap-2 cursor-pointer text-sm">
            <span class="text-neutral-500">Hide wear items</span>
            <div class="relative">
              <input type="checkbox" id="toggle-advisories" class="sr-only peer" checked>
              <div class="w-9 h-5 bg-neutral-200 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
            </div>
          </label>
        </div>
        <p id="filter-hint-advisories" class="{tw.TEXT_MUTED} mb-3 text-xs italic">Showing model-specific advisories only. Toggle to see all including tyres, bulbs, and brake pads.</p>"""
    else:
        toggle_html = f"""<p class="{tw.TEXT_MUTED} mb-4">Items noted but not causing immediate failure</p>"""

    return f"""
    <section class="{tw.CARD}" id="advisories-section">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-info {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Advisories</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        {toggle_html}
        <div id="advisories-list">{items_html}
        </div>
        <p id="no-advisories-msg" class="hidden text-center py-4 text-neutral-400 text-sm">No model-specific advisories in top results. Toggle to see all.</p>
      </div>
    </section>"""


def generate_minor_defects_section(defects: list[dict]) -> str:
    """Generate the Minor Defects section with universal/specific filtering.

    Returns empty string if no minor defects data.
    """
    if not defects:
        return ""

    # Count how many are universal vs model-specific
    universal_count = sum(
        1 for d in defects
        if is_universal_defect(d['defect_description'], d['category_name'])
    )
    has_universal = universal_count > 0
    has_specific = universal_count < len(defects)

    items_html = ""
    for i, d in enumerate(defects, 1):
        is_universal = is_universal_defect(d['defect_description'], d['category_name'])
        data_attr = 'data-universal="true"' if is_universal else 'data-universal="false"'
        items_html += f"""
        <div class="{tw.NUMBERED_ITEM} minor-item" {data_attr}>
          <span class="{tw.NUMBERED_BADGE} minor-number" style="background-color: rgb(254 243 199); color: rgb(180 83 9);">{i}</span>
          <div class="flex-1">
            <div class="flex justify-between items-start">
              <span class="{tw.DEFECT_NAME}">{d['defect_description']}</span>
              <span class="{tw.DEFECT_PERCENT}">{d['percentage']}%</span>
            </div>
            <span class="{tw.DEFECT_CATEGORY}">Category: {d['category_name']}</span>
          </div>
        </div>"""

    # Only show toggle if we have both types
    toggle_html = ""
    if has_universal and has_specific:
        toggle_html = f"""
        <div class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-100">
          <p class="{tw.TEXT_MUTED}">Minor issues that don't cause failure but worth noting</p>
          <label class="inline-flex items-center gap-2 cursor-pointer text-sm">
            <span class="text-neutral-500">Hide wear items</span>
            <div class="relative">
              <input type="checkbox" id="toggle-minor" class="sr-only peer" checked>
              <div class="w-9 h-5 bg-neutral-200 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
            </div>
          </label>
        </div>
        <p id="filter-hint-minor" class="{tw.TEXT_MUTED} mb-3 text-xs italic">Showing model-specific minor defects only. Toggle to see all including tyres, bulbs, and brake pads.</p>"""
    else:
        toggle_html = f"""<p class="{tw.TEXT_MUTED} mb-4">Minor issues that don't cause failure but worth noting</p>"""

    return f"""
    <section class="{tw.CARD}" id="minor-section">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}" style="background: linear-gradient(to bottom right, rgb(254 243 199), rgb(253 230 138 / 0.5));">
            <i class="ph ph-note-pencil" style="color: rgb(180 83 9);"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Minor Defects</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        {toggle_html}
        <div id="minor-list">{items_html}
        </div>
        <p id="no-minor-msg" class="hidden text-center py-4 text-neutral-400 text-sm">No model-specific minor defects in top results. Toggle to see all.</p>
      </div>
    </section>"""


def generate_dangerous_defects_section(defects: list[dict]) -> str:
    """Generate the MOT History Check section for dangerous defects with filtering.

    Returns empty string if no dangerous defects data.
    """
    if not defects:
        return ""

    # Count universal vs model-specific
    universal_count = sum(
        1 for d in defects
        if is_universal_defect(d['defect_description'], d['category_name'])
    )
    has_universal = universal_count > 0
    has_specific = universal_count < len(defects)

    items_html = ""
    for d in defects:
        is_universal = is_universal_defect(d['defect_description'], d['category_name'])
        data_attr = 'data-universal="true"' if is_universal else 'data-universal="false"'
        items_html += f"""
        <li class="{tw.LIST_ITEM} dangerous-item" {data_attr}>
          <span class="{tw.DEFECT_NAME}">{d['defect_description']}</span>
          <span class="text-xs text-neutral-400">{d['category_name']}</span>
        </li>"""

    # Toggle for dangerous defects section
    toggle_html = ""
    if has_universal and has_specific:
        toggle_html = f"""
        <div class="flex items-center justify-end mb-3">
          <label class="inline-flex items-center gap-2 cursor-pointer text-sm">
            <span class="text-neutral-500">Hide wear items</span>
            <div class="relative">
              <input type="checkbox" id="toggle-dangerous" class="sr-only peer" checked>
              <div class="w-9 h-5 bg-neutral-200 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
            </div>
          </label>
        </div>"""

    return f"""
    <section class="{tw.CARD}" id="dangerous-section">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-warning {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">MOT History Check</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        <div class="{tw.CALLOUT_WARNING}">
          <div class="flex gap-3">
            <i class="ph ph-warning-circle {tw.CALLOUT_ICON}"></i>
            <div>
              <p class="{tw.CALLOUT_TITLE}">Check the vehicle's MOT history</p>
              <p class="{tw.CALLOUT_TEXT}">These are 'dangerous' defects that cause immediate MOT failure. If present in recent tests, investigate further before purchasing.</p>
            </div>
          </div>
        </div>
        {toggle_html}
        <ul class="list-none" id="dangerous-list">{items_html}
        </ul>
        <p id="no-dangerous-msg" class="hidden text-center py-4 text-neutral-400 text-sm">No model-specific dangerous defects. Toggle to see all.</p>
      </div>
    </section>"""


def generate_year_pass_rates_section(year_data: list[dict]) -> str:
    """Generate the Pass Rates by Year section.

    Returns empty string if no year data.
    """
    if not year_data:
        return ""

    rows_html = ""
    for y in year_data:
        tests_formatted = f"{y['total_tests']:,}"
        rows_html += f"""
        <tr class="{tw.TR_HOVER}">
          <td class="{tw.TD} font-medium text-neutral-900">{y['model_year']}</td>
          <td class="{tw.TD} font-semibold">{y['pass_rate']}%</td>
          <td class="{tw.TD}">{tests_formatted}</td>
        </tr>"""

    return f"""
    <section class="{tw.CARD}">
      <div class="{tw.CARD_HEADER}">
        <div class="{tw.SECTION_HEADER}">
          <div class="{tw.SECTION_ICON_BOX}">
            <i class="ph ph-calendar {tw.SECTION_ICON}"></i>
          </div>
          <h2 class="{tw.SECTION_TITLE}">Pass Rates by Year</h2>
        </div>
      </div>
      <div class="{tw.CARD_BODY}">
        <p class="{tw.TEXT_MUTED} mb-4">MOT pass rates for each model year (sorted by best performance)</p>
        <div class="overflow-x-auto">
          <table class="{tw.TABLE}">
            <thead>
              <tr>
                <th class="{tw.TH}">Year</th>
                <th class="{tw.TH}">Pass Rate</th>
                <th class="{tw.TH}">Tests</th>
              </tr>
            </thead>
            <tbody>{rows_html}
            </tbody>
          </table>
        </div>
      </div>
    </section>"""


def generate_about_section(total_tests: str) -> str:
    """Generate the About This Data footer section."""
    return f"""
    <section class="bg-neutral-50 rounded-xl p-5 mt-8">
      <h2 class="text-sm font-semibold text-neutral-700 mb-2">About This Data</h2>
      <p class="text-sm text-neutral-500">
        Analysis based on {total_tests} MOT tests from DVSA records.
        Pass rates reflect MOT test outcomes only and may not represent overall vehicle reliability.
        Always conduct a thorough inspection and obtain a professional assessment before purchasing any used vehicle.
      </p>
    </section>"""


def generate_footer() -> str:
    """Generate page footer."""
    year = date.today().year
    return f"""
    <footer class="{tw.FOOTER}">
      <p>&copy; {year} Motorwise. Data sourced from DVSA MOT records.</p>
    </footer>"""


def generate_filter_script() -> str:
    """Generate JavaScript for filtering universal wear items."""
    return """
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      // Filter function for a section
      function setupFilter(toggleId, listId, noMsgId, itemClass) {
        const toggle = document.getElementById(toggleId);
        const list = document.getElementById(listId);
        const noMsg = document.getElementById(noMsgId);

        if (!toggle || !list) return;

        function applyFilter() {
          const hideUniversal = toggle.checked;
          const items = list.querySelectorAll('.' + itemClass);
          let visibleCount = 0;
          let numberIndex = 1;

          items.forEach(item => {
            const isUniversal = item.dataset.universal === 'true';
            if (hideUniversal && isUniversal) {
              item.classList.add('hidden');
            } else {
              item.classList.remove('hidden');
              visibleCount++;
              // Renumber if this is a numbered list (failures, advisories, or minor sections)
              const numberBadge = item.querySelector('.defect-number, .advisory-number, .minor-number');
              if (numberBadge) {
                numberBadge.textContent = numberIndex++;
              }
            }
          });

          // Show "no items" message if all filtered out
          if (noMsg) {
            noMsg.classList.toggle('hidden', visibleCount > 0);
          }

          // Update hint text for failures section
          const hint = document.getElementById('filter-hint');
          if (hint) {
            hint.classList.toggle('hidden', !hideUniversal);
          }
        }

        toggle.addEventListener('change', applyFilter);
        // Apply on load (default is checked = filtered)
        applyFilter();
      }

      // Setup filters for all sections
      setupFilter('toggle-failures', 'failures-list', 'no-specific-msg', 'defect-item');
      setupFilter('toggle-advisories', 'advisories-list', 'no-advisories-msg', 'advisory-item');
      setupFilter('toggle-minor', 'minor-list', 'no-minor-msg', 'minor-item');
      setupFilter('toggle-dangerous', 'dangerous-list', 'no-dangerous-msg', 'dangerous-item');
    });
  </script>"""


def generate_full_page(data: dict) -> str:
    """
    Generate the complete HTML page.

    Args:
        data: Dict from get_inspection_guide_data()

    Returns:
        Complete HTML string
    """
    make = data["make"].title()
    model = data["model"].title()
    safe_make = data["make"].lower().replace(" ", "-")
    safe_model = data["model"].lower().replace(" ", "-")
    total_tests = f"{data['total_tests']:,}"
    today_iso = date.today().isoformat()

    # Generate sections (empty string if no data)
    top_failures_html = generate_top_failures_section(data["top_failures"])
    advisories_html = generate_advisories_section(data.get("advisories", []))
    minor_html = generate_minor_defects_section(data.get("minor_defects", []))
    dangerous_html = generate_dangerous_defects_section(data["dangerous_defects"])
    year_rates_html = generate_year_pass_rates_section(data["year_pass_rates"])

    # Check if we have ANY content
    has_content = any([top_failures_html, advisories_html, minor_html, dangerous_html, year_rates_html])
    if not has_content:
        return ""  # Signal to skip this model

    return f"""<!DOCTYPE html>
<html lang="en">
{generate_head(make, model, safe_make, safe_model, total_tests, today_iso)}
<body class="bg-white font-sans text-neutral-900 antialiased">
  <div id="mw-header"></div>

  <main class="{tw.CONTAINER}">
    {generate_header(make, model, total_tests)}

    {top_failures_html}
    {advisories_html}
    {minor_html}
    {dangerous_html}
    {year_rates_html}

    {generate_about_section(total_tests)}
  </main>

  {generate_footer()}

  <script src="/header/js/header.js"></script>
  {generate_filter_script()}
</body>
</html>"""
