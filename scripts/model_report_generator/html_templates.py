"""HTML template functions for model report generation.

This module provides template generation functions for the HTML head section,
cards, tables, badges, and other reusable components using Tailwind CSS.

Aligned with Motorwise production articles styling (articles.css patterns).
"""

from datetime import date

try:
    from . import tailwind_classes as tw
except ImportError:
    import tailwind_classes as tw


def generate_head(make: str, model: str, safe_make: str, safe_model: str,
                  total_tests: str, today_iso: str) -> str:
    """Generate the complete <head> section with SEO metadata matching production tools."""
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{make} {model} MOT Reliability Report | Motorwise</title>
  <meta name="description" content="Complete MOT reliability analysis for {make} {model} based on {total_tests} real test results. Pass rates, common failures, best years to buy.">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/articles/content/model-reports/{safe_make}-{safe_model}-report.html">

  <!-- Open Graph -->
  <meta property="og:title" content="{make} {model} MOT Reliability Report | Motorwise">
  <meta property="og:description" content="Complete MOT reliability analysis for {make} {model} based on {total_tests} real test results.">
  <meta property="og:url" content="https://www.motorwise.io/articles/content/model-reports/{safe_make}-{safe_model}-report.html">
  <meta property="og:type" content="website">
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
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/style.css">
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css">

  <!-- Shared Styles -->
  <link rel="stylesheet" href="/articles/styles/articles.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <!-- Page-specific Styles -->
  <style>
    /* Mobile gradient background - matches articles pattern */
    @media (max-width: 767px) {{
      body {{
        background: linear-gradient(180deg, #EFF6FF 0%, #EFF6FF 60%, #FFFFFF 100%);
        min-height: 100vh;
      }}
    }}

    /* Reading progress bar - uses blue-600 to blue-500 gradient */
    #reading-progress {{
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: linear-gradient(90deg, #2563eb, #3b82f6);  /* blue-600 to blue-500 */
      z-index: 100;
      transition: width 0.1s ease;
    }}

    /* Pass rate badges - aligned with articles.css color tokens */
    /* Uses -600 for text, gradient from -50 to -100/50 per ComparisonDashboard pattern */
    .pass-rate-excellent {{ color: #059669; background: linear-gradient(to bottom right, #ecfdf5, rgba(209, 250, 229, 0.5)); }}
    .pass-rate-good {{ color: #059669; background: linear-gradient(to bottom right, #ecfdf5, rgba(209, 250, 229, 0.5)); }}
    .pass-rate-average {{ color: #d97706; background: linear-gradient(to bottom right, #fffbeb, rgba(254, 243, 199, 0.5)); }}
    .pass-rate-poor {{ color: #dc2626; background: linear-gradient(to bottom right, #fef2f2, rgba(254, 226, 226, 0.5)); }}

    .data-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.125rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}

    /* Pass rate circle animation */
    .pass-rate-circle svg {{ transform: rotate(-90deg); }}
    .pass-rate-circle .progress {{ stroke-linecap: round; transition: stroke-dashoffset 0.5s ease; }}

    /* Featured card shadow effect - matches production depth card pattern */
    .featured-card {{
      position: relative;
    }}
    .featured-card::before {{
      content: '';
      position: absolute;
      left: 8px;
      top: 8px;
      width: calc(100% - 16px);
      height: 100%;
      background: linear-gradient(to bottom right, #eff6ff, rgba(219, 234, 254, 0.5));  /* blue-50 to blue-100/50 */
      border-radius: 1rem;
      transform: rotate(0.5deg);
      z-index: -1;
    }}

    /* Smooth animations */
    .mw-fade-in {{
      animation: fadeIn 0.3s ease-out forwards;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Card hover lift effect */
    .mw-card-lift {{
      transition: all 0.3s ease-out;
    }}
    .mw-card-lift:hover {{
      transform: translateY(-2px);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }}

    /* Custom scrollbar - thin minimal style for all overflow elements */
    .article-table-wrapper::-webkit-scrollbar,
    .overflow-y-auto::-webkit-scrollbar,
    .overflow-x-auto::-webkit-scrollbar,
    .overflow-auto::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .article-table-wrapper::-webkit-scrollbar-track,
    .overflow-y-auto::-webkit-scrollbar-track,
    .overflow-x-auto::-webkit-scrollbar-track,
    .overflow-auto::-webkit-scrollbar-track {{
      background: transparent;
      border-radius: 3px;
    }}
    .article-table-wrapper::-webkit-scrollbar-thumb,
    .overflow-y-auto::-webkit-scrollbar-thumb,
    .overflow-x-auto::-webkit-scrollbar-thumb,
    .overflow-auto::-webkit-scrollbar-thumb {{
      background: rgba(0, 0, 0, 0.15);
      border-radius: 3px;
      transition: background 0.2s ease;
    }}
    .article-table-wrapper::-webkit-scrollbar-thumb:hover,
    .overflow-y-auto::-webkit-scrollbar-thumb:hover,
    .overflow-x-auto::-webkit-scrollbar-thumb:hover,
    .overflow-auto::-webkit-scrollbar-thumb:hover {{
      background: rgba(0, 0, 0, 0.25);
    }}
    .article-table-wrapper::-webkit-scrollbar-button,
    .overflow-y-auto::-webkit-scrollbar-button,
    .overflow-x-auto::-webkit-scrollbar-button,
    .overflow-auto::-webkit-scrollbar-button {{
      display: none;
    }}
    /* Firefox scrollbar */
    .article-table-wrapper,
    .overflow-y-auto,
    .overflow-x-auto,
    .overflow-auto {{
      scrollbar-width: thin;
      scrollbar-color: rgba(0, 0, 0, 0.15) transparent;
    }}
  </style>

  <!-- JSON-LD: Article -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} MOT Reliability Report",
    "description": "Complete MOT reliability analysis for {make} {model} based on {total_tests} real test results",
    "author": {{ "@type": "Organization", "name": "Motorwise", "url": "https://www.motorwise.io" }},
    "publisher": {{ "@type": "Organization", "name": "Motorwise" }},
    "datePublished": "{today_iso}",
    "dateModified": "{today_iso}"
  }}
  </script>

  <!-- JSON-LD: BreadcrumbList -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.motorwise.io" }},
      {{ "@type": "ListItem", "position": 2, "name": "Guides", "item": "https://www.motorwise.io/articles/" }},
      {{ "@type": "ListItem", "position": 3, "name": "Model Reports", "item": "https://www.motorwise.io/articles/content/model-reports/" }},
      {{ "@type": "ListItem", "position": 4, "name": "{make} {model}", "item": "https://www.motorwise.io/articles/content/model-reports/{safe_make}-{safe_model}-report.html" }}
    ]
  }}
  </script>
</head>"""


def get_badge_html(rate: float, text: str = None) -> str:
    """Generate Tailwind-styled badge HTML based on pass rate."""
    display_text = text if text else f"{rate:.1f}%"

    if rate >= 80:
        return f'<span class="{tw.BADGE_GOOD}">{display_text}</span>'
    elif rate >= 65:
        return f'<span class="{tw.BADGE_AVG}">{display_text}</span>'
    return f'<span class="{tw.BADGE_POOR}">{display_text}</span>'


def get_rate_color_class(rate: float) -> str:
    """Return Tailwind text color class based on pass rate."""
    if rate >= 80:
        return "text-good"
    elif rate >= 65:
        return "text-average"
    return "text-poor"


def get_rate_bg_color(rate: float) -> str:
    """Return hex color for text/inline styles.

    Aligned with articles.css color tokens:
    - emerald-600 (#059669) for good (>=80%)
    - amber-600 (#d97706) for average (>=65%)
    - red-600 (#dc2626) for poor (<65%)
    """
    if rate >= 80:
        return "#059669"  # emerald-600
    elif rate >= 65:
        return "#d97706"  # amber-600
    return "#dc2626"      # red-600


def get_rate_bar_color(rate: float) -> str:
    """Return hex color for chart bar fills.

    Uses -400 variants for softer appearance matching production
    ComparisonDashboard pattern:
    - emerald-400 (#34d399) for good (>=80%)
    - amber-400 (#fbbf24) for average (>=65%)
    - red-400 (#f87171) for poor (<65%)
    """
    if rate >= 80:
        return "#34d399"  # emerald-400
    elif rate >= 65:
        return "#fbbf24"  # amber-400
    return "#f87171"      # red-400


def get_severity_color(severity: str) -> str:
    """Return hex color based on severity level.

    Aligned with articles.css color tokens:
    - emerald-600 (#059669) for minor defects
    - amber-600 (#d97706) for major defects
    - red-600 (#dc2626) for dangerous defects
    - neutral-600 (#525252) for unknown
    """
    colors = {
        "minor": "#059669",     # emerald-600
        "major": "#d97706",     # amber-600
        "dangerous": "#dc2626"  # red-600
    }
    return colors.get(severity.lower(), "#525252")  # neutral-600


def generate_card(title: str, body_content: str, icon: str = None, highlight: str = None) -> str:
    """Generate a card component with optional icon and highlight border.

    Args:
        title: Card header title
        body_content: HTML content for the card body
        icon: Phosphor icon class (e.g., 'trophy', 'warning')
        highlight: 'good' or 'poor' for colored left border
    """
    if highlight == "good":
        card_class = tw.CARD_GOOD
    elif highlight == "poor":
        card_class = tw.CARD_POOR
    else:
        card_class = tw.CARD

    icon_html = f'<i class="ph ph-{icon} {tw.ICON_HEADER}"></i>' if icon else ""

    return f"""
    <div class="{card_class}">
        <div class="{tw.CARD_HEADER}">
            <h3 class="{tw.CARD_TITLE}">{title}</h3>
            {icon_html}
        </div>
        <div class="{tw.CARD_BODY}">
            {body_content}
        </div>
    </div>"""


def generate_card_compact(title: str, body_content: str, icon: str = None) -> str:
    """Generate a card with compact body padding."""
    icon_html = f'<i class="ph ph-{icon} {tw.ICON_HEADER}"></i>' if icon else ""

    return f"""
    <div class="{tw.CARD}">
        <div class="{tw.CARD_HEADER}">
            <h3 class="{tw.CARD_TITLE}">{title}</h3>
            {icon_html}
        </div>
        <div class="{tw.CARD_BODY_COMPACT}">
            {body_content}
        </div>
    </div>"""


def generate_table(headers: list[str], rows: list[list[str]], scrollable: bool = False) -> str:
    """Generate a Tailwind-styled table.

    Args:
        headers: List of column header strings
        rows: List of row data (each row is a list of cell values)
        scrollable: If True, wraps table in scrollable container
    """
    header_html = "".join(
        f'<th class="{tw.TH}">{h}</th>'
        for h in headers
    )

    rows_html = ""
    for row in rows:
        cells = "".join(f'<td class="{tw.TD}">{cell}</td>' for cell in row)
        rows_html += f'<tr class="{tw.TR_HOVER}">{cells}</tr>'

    table_html = f"""
    <table class="{tw.TABLE}">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>"""

    if scrollable:
        return f'<div class="{tw.ALL_VARIANTS_TABLE}">{table_html}</div>'
    return table_html


def generate_section_divider(title: str, subtitle: str = None) -> str:
    """Generate a section divider with title and optional subtitle."""
    subtitle_html = f'<p class="{tw.SECTION_DIVIDER_P}">{subtitle}</p>' if subtitle else ""
    return f"""
        <div class="{tw.SECTION_DIVIDER}">
            <h2 class="{tw.SECTION_DIVIDER_H2}">{title}</h2>
            {subtitle_html}
        </div>"""


def generate_stat_row(label: str, value: str) -> str:
    """Generate a single stat row (label-value pair)."""
    return f"""
            <div class="{tw.STAT_ROW}">
                <span class="{tw.STAT_ROW_LABEL}">{label}</span>
                <span class="{tw.STAT_ROW_VALUE}">{value}</span>
            </div>"""


def generate_mini_stat(value: str, label: str, color: str = None) -> str:
    """Generate a mini stat block with value and label."""
    style = f' style="color: {color}"' if color else ""
    return f"""
            <div class="{tw.MINI_STAT}">
                <div class="{tw.MINI_STAT_VALUE}"{style}>{value}</div>
                <div class="{tw.MINI_STAT_LABEL}">{label}</div>
            </div>"""


def generate_defect_list_item(name: str, count: str, dangerous: bool = False) -> str:
    """Generate a defect list item."""
    count_class = tw.DEFECT_COUNT_DANGEROUS if dangerous else tw.DEFECT_COUNT
    return f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DEFECT_NAME}">{name}</span>
                <span class="{count_class}">{count}</span>
            </li>"""


def generate_data_list_item(name: str, value: str, value_color: str = None) -> str:
    """Generate a data list item (name-value pair for lists)."""
    style = f' style="color: {value_color}"' if value_color else ""
    return f"""
            <li class="{tw.LIST_ITEM}">
                <span class="{tw.DATA_LIST_NAME}">{name}</span>
                <span class="{tw.DATA_LIST_VALUE}"{style}>{value}</span>
            </li>"""


# =============================================================================
# ARTICLES PATTERN TEMPLATES
# =============================================================================

def generate_breadcrumb(make: str, model: str) -> str:
    """Generate breadcrumb navigation matching articles pattern."""
    return f"""
    <nav aria-label="Breadcrumb" class="flex items-center gap-2 text-sm text-neutral-500 mb-6">
      <a href="/" class="hover:text-blue-600 transition-colors">Home</a>
      <i class="ph ph-caret-right text-xs"></i>
      <a href="/articles/content/index.html" class="hover:text-blue-600 transition-colors">Guides</a>
      <i class="ph ph-caret-right text-xs"></i>
      <span class="text-neutral-900">{make} {model}</span>
    </nav>"""


def generate_article_header(make: str, model: str, variant_count: int,
                            total_tests: str, today: str) -> str:
    """Generate article header matching articles pattern."""
    return f"""
      <header class="mb-8">
        <div class="flex flex-wrap items-center gap-3 mb-4">
          <span class="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-full border bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-600 border-blue-200/50">
            <i class="ph ph-chart-bar"></i>
            MOT Reliability Data
          </span>
          <span class="text-sm text-neutral-500">{variant_count} variants analysed</span>
          <span class="text-sm text-neutral-500">Updated {today}</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
          {make} {model} MOT Reliability Report
        </h1>
        <p class="text-lg text-neutral-600 leading-relaxed">
          Complete MOT reliability analysis based on {total_tests} real test results.
        </p>
      </header>"""


def generate_data_source_callout(total_tests: str, year_range: str) -> str:
    """Generate data source callout (green box with test count)."""
    return f"""
      <div class="flex items-center gap-4 p-4 bg-gradient-to-br from-emerald-50 to-emerald-100/50 border border-emerald-200/50 rounded-xl mb-8 transition-all hover:-translate-y-0.5 hover:shadow-md">
        <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 shadow-sm">
          <i class="ph ph-database text-emerald-600 text-xl"></i>
        </div>
        <div>
          <p class="text-base font-semibold text-emerald-700">{total_tests} MOT tests analysed</p>
          <p class="text-sm text-emerald-600">Real DVSA data covering {year_range}</p>
        </div>
      </div>"""


def generate_key_findings_card(best_variant: dict, worst_variant: dict,
                                pass_rate: float, national_avg: float = 71.5) -> str:
    """Generate key findings summary card (4-stat grid)."""
    diff = pass_rate - national_avg
    diff_sign = "+" if diff >= 0 else ""
    diff_color = "emerald" if diff >= 0 else "red"

    best_html = ""
    if best_variant:
        best_html = f"""
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Best Year to Buy</p>
            <p class="text-lg font-semibold text-neutral-900">{best_variant.get('year', 'N/A')} {best_variant.get('fuel_type_name', '')}</p>
            <p class="text-sm text-emerald-600 font-medium">{best_variant.get('pass_rate', 0):.1f}% pass rate</p>
          </div>"""

    worst_html = ""
    if worst_variant and worst_variant != best_variant:
        worst_html = f"""
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Year to Avoid</p>
            <p class="text-lg font-semibold text-neutral-900">{worst_variant.get('year', 'N/A')} {worst_variant.get('fuel_type_name', '')}</p>
            <p class="text-sm text-red-600 font-medium">{worst_variant.get('pass_rate', 0):.1f}% pass rate</p>
          </div>"""
    else:
        worst_html = f"""
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Overall Reliability</p>
            <p class="text-lg font-semibold text-neutral-900">Consistently Good</p>
            <p class="text-sm text-emerald-600 font-medium">Low variance across years</p>
          </div>"""

    return f"""
      <div class="relative bg-white rounded-2xl shadow-xl border border-neutral-100/80 p-6 mb-10">
        <h2 class="text-lg font-semibold text-neutral-900 mb-5 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center shadow-sm">
            <i class="ph ph-lightning text-blue-600 text-xl"></i>
          </div>
          Key Findings
        </h2>
        <div class="grid sm:grid-cols-2 gap-4">
          {best_html}
          {worst_html}
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Overall Pass Rate</p>
            <p class="text-lg font-semibold text-neutral-900">{pass_rate:.1f}%</p>
            <p class="text-sm text-{diff_color}-600 font-medium">{diff_sign}{diff:.1f}% vs national average</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">National Average</p>
            <p class="text-lg font-semibold text-neutral-900">{national_avg:.1f}%</p>
            <p class="text-sm text-neutral-500 font-medium">All UK vehicles</p>
          </div>
        </div>
      </div>"""


def generate_toc_sidebar(sections: list) -> str:
    """Generate table of contents sidebar matching articles pattern."""
    toc_items = ""
    for i, section in enumerate(sections, 1):
        toc_items += f"""
          <li class="article-toc-item">
            <a href="#{section['id']}" class="toc-link">
              <span class="toc-link-number">{i}.</span>
              <span class="toc-link-text">{section['title']}</span>
            </a>
          </li>"""

    return f"""
    <aside class="article-sidebar">
      <nav class="article-toc" aria-label="Table of contents">
        <button class="article-toc-toggle" aria-expanded="false">
          <div class="article-toc-toggle-content">
            <i class="ph ph-list article-toc-toggle-icon"></i>
            <span class="article-toc-toggle-label">Contents</span>
            <span class="article-toc-count">{len(sections)}</span>
          </div>
          <i class="ph ph-caret-down article-toc-caret"></i>
        </button>
        <div class="article-toc-content">
          <div class="article-toc-header">
            <i class="ph ph-list article-toc-header-icon"></i>
            <span class="article-toc-header-text">Contents</span>
          </div>
          <ul class="article-toc-list">{toc_items}
          </ul>
        </div>
      </nav>
    </aside>"""


def generate_article_section(section_id: str, title: str, icon: str,
                              content: str, reveal_index: int) -> str:
    """Generate article section with scroll-reveal."""
    return f"""
      <div class="scroll-reveal" data-reveal-index="{reveal_index}">
        <section id="{section_id}" class="article-section">
          <div class="article-section-header">
            <div class="article-section-icon">
              <i class="ph ph-{icon}"></i>
            </div>
            <h2 class="article-section-title">{title}</h2>
          </div>
          {content}
        </section>
      </div>"""


def generate_callout(callout_type: str, title: str, text: str, icon: str = None) -> str:
    """Generate callout box matching articles pattern.

    Types: 'tip' (green), 'warning' (amber), 'info' (blue), 'danger' (red)
    """
    icon_map = {
        'tip': 'check-circle',
        'warning': 'warning',
        'info': 'info',
        'danger': 'warning-octagon'
    }
    icon_class = icon if icon else icon_map.get(callout_type, 'info')

    return f"""
        <div class="callout {callout_type}">
          <i class="ph ph-{icon_class} callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">{title}</p>
            <p class="callout-text">{text}</p>
          </div>
        </div>"""
