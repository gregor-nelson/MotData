"""HTML template functions for model report generation.

This module provides template generation functions for the HTML head section,
cards, tables, badges, and other reusable components using Tailwind CSS.
"""

from datetime import date

try:
    from . import tailwind_classes as tw
except ImportError:
    import tailwind_classes as tw


def generate_head(make: str, model: str, safe_make: str, safe_model: str,
                  total_tests: str, today_iso: str) -> str:
    """Generate the complete <head> section with SEO metadata."""
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{make} {model} MOT Reliability Report | Motorwise</title>
  <meta name="description" content="Complete MOT reliability analysis for {make} {model} based on {total_tests} real test results. Pass rates, common failures, best years to buy.">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/reports/model/{safe_make}-{safe_model}.html">

  <!-- Open Graph -->
  <meta property="og:title" content="{make} {model} MOT Reliability Report | Motorwise">
  <meta property="og:description" content="Complete MOT reliability analysis for {make} {model} based on {total_tests} real test results.">
  <meta property="og:url" content="https://www.motorwise.io/reports/model/{safe_make}-{safe_model}.html">
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
          }},
          colors: {{
            'good': '#10b981',
            'average': '#f59e0b',
            'poor': '#ef4444',
            'primary': '#1e3a5f',
            'primary-light': '#2d5a8a',
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
  <link rel="stylesheet" href="/tools/styles/tools.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <!-- Minimal Custom Styles -->
  <style>
    .pass-rate-circle svg {{ transform: rotate(-90deg); }}
    .pass-rate-circle .progress {{ stroke-linecap: round; transition: stroke-dashoffset 0.5s ease; }}
  </style>

  <!-- JSON-LD: Article -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} MOT Reliability Report",
    "description": "Complete MOT reliability analysis for {make} {model}",
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
      {{ "@type": "ListItem", "position": 2, "name": "Model Reports", "item": "https://www.motorwise.io/reports/model/" }},
      {{ "@type": "ListItem", "position": 3, "name": "{make} {model}", "item": "https://www.motorwise.io/reports/model/{safe_make}-{safe_model}.html" }}
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
    """Return hex color for inline styles (SVG, charts, etc.)."""
    if rate >= 80:
        return "#10b981"
    elif rate >= 65:
        return "#f59e0b"
    return "#ef4444"


def get_severity_color(severity: str) -> str:
    """Return hex color based on severity level."""
    colors = {
        "minor": "#10b981",
        "major": "#f59e0b",
        "dangerous": "#ef4444"
    }
    return colors.get(severity.lower(), "#64748b")


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
