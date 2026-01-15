# Model Report Generator - Tailwind CSS Migration Guide

## Overview

This document provides a comprehensive implementation guide for migrating the `generate_model_report.py` script from inline CSS to Tailwind CSS, matching the styling patterns used in the reference application (`number-plate-decoder.html`).

---

## 1. Current State Analysis

### File Location
```
scripts/model_report_generator/generate_model_report.py
```

### Current Approach
- **~700 lines of inline CSS** embedded in the `<style>` block within `generate_html()`
- Custom CSS variables (`:root`) for colors
- System fonts
- No external dependencies
- No SEO metadata or structured data

### Problems with Current Approach
1. Large file size (~45KB per generated report)
2. Difficult to maintain consistency with other Motorwise pages
3. No icon system
4. Missing SEO elements (Open Graph, JSON-LD)
5. Different font family than main site

---

## 2. Target State

### Reference File
```
frontend/public/tools/html/number-plate-decoder.html
```

### Target Approach
- Tailwind CSS via CDN for all styling
- Jost font family (Google Fonts)
- Phosphor Icons for visual elements
- Shared external stylesheets (`tools.css`, `header.css`)
- Full SEO metadata
- Minimal custom CSS (~30 lines for SVG elements only)

---

## 3. New HTML Head Structure

Replace the entire `<head>` section generation with this template:

```html
<head>
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
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            'sans': ['Jost', 'system-ui', 'sans-serif'],
          },
          colors: {
            'good': '#10b981',
            'average': '#f59e0b',
            'poor': '#ef4444',
            'primary': '#1e3a5f',
            'primary-light': '#2d5a8a',
          }
        }
      }
    }
  </script>

  <!-- Phosphor Icons -->
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/style.css">
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css">

  <!-- Shared Styles -->
  <link rel="stylesheet" href="/tools/styles/tools.css">
  <link rel="stylesheet" href="/header/css/header.css">

  <!-- Minimal Custom Styles (only what Tailwind cannot handle) -->
  <style>
    .pass-rate-circle svg {
      transform: rotate(-90deg);
    }
    .pass-rate-circle .progress {
      stroke-linecap: round;
      transition: stroke-dashoffset 0.5s ease;
    }
  </style>

  <!-- JSON-LD: Vehicle Report -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{make} {model} MOT Reliability Report",
    "description": "Complete MOT reliability analysis for {make} {model}",
    "author": {
      "@type": "Organization",
      "name": "Motorwise",
      "url": "https://www.motorwise.io"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Motorwise"
    },
    "datePublished": "{today_iso}",
    "dateModified": "{today_iso}"
  }
  </script>

  <!-- JSON-LD: BreadcrumbList -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://www.motorwise.io"
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "Model Reports",
        "item": "https://www.motorwise.io/reports/model/"
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": "{make} {model}",
        "item": "https://www.motorwise.io/reports/model/{safe_make}-{safe_model}.html"
      }
    ]
  }
  </script>
</head>
```

---

## 4. Tailwind Class Mappings

### 4.1 Layout Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.container` | `max-w-7xl mx-auto px-6 py-6` |
| `.grid-2` | `grid grid-cols-1 md:grid-cols-2 gap-5 mb-6` |
| `.grid-3` | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6` |
| `.cards-grid` | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6` |

### 4.2 Card Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.card` | `bg-white rounded-xl shadow-sm overflow-hidden mb-6` |
| `.card.highlight-good` | `bg-white rounded-xl shadow-sm overflow-hidden mb-6 border-l-4 border-good` |
| `.card.highlight-poor` | `bg-white rounded-xl shadow-sm overflow-hidden mb-6 border-l-4 border-poor` |
| `.card-header` | `px-5 py-4 border-b border-slate-200` |
| `.card-header h3` | `text-base font-semibold text-slate-800` |
| `.card-body` | `p-5` |
| `.card-body.compact` | `p-4` |

### 4.3 Typography Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `header h1` | `text-2xl font-semibold mb-2` |
| `.subtitle` | `text-lg opacity-90` |
| `.meta` | `text-sm opacity-80 mt-4` |
| `.section-divider h2` | `text-xl font-semibold text-slate-800 mb-1` |
| `.section-divider p` | `text-sm text-slate-500` |

### 4.4 Badge Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.badge` (base) | `inline-block px-2.5 py-1 rounded-full text-sm font-semibold` |
| `.badge.good` | `inline-block px-2.5 py-1 rounded-full text-sm font-semibold bg-emerald-100 text-emerald-800` |
| `.badge.average` | `inline-block px-2.5 py-1 rounded-full text-sm font-semibold bg-amber-100 text-amber-800` |
| `.badge.poor` | `inline-block px-2.5 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800` |

### 4.5 Table Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `table` | `w-full text-sm` |
| `th` | `py-2.5 px-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide bg-slate-50 border-b border-slate-200` |
| `td` | `py-2.5 px-3 border-b border-slate-100` |

### 4.6 Stats & Data Display

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.stat-card` | `bg-white rounded-xl p-5 text-center shadow-sm` |
| `.stat-card .value` | `text-3xl font-bold text-primary` |
| `.stat-card .label` | `text-sm text-slate-500 mt-1` |
| `.stat-row` | `flex justify-between py-2 border-b border-slate-100 last:border-b-0` |
| `.stat-row .label` | `text-sm text-slate-500` |
| `.stat-row .value` | `font-semibold` |
| `.mini-stat` | `text-center p-4 bg-slate-50 rounded-lg` |
| `.mini-stat .value` | `text-2xl font-bold` |
| `.mini-stat .label` | `text-xs text-slate-500 mt-1` |

### 4.7 List Classes

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.defect-list` | `list-none max-h-96 overflow-y-auto` |
| `.defect-list li` | `flex justify-between py-2 border-b border-slate-100 last:border-b-0 text-sm` |
| `.defect-name` | `flex-1 pr-4` |
| `.defect-count` | `font-semibold text-slate-500` |
| `.defect-count.dangerous` | `font-semibold text-poor` |
| `.data-list` | `list-none` |
| `.data-list li` | `flex justify-between py-2 border-b border-slate-100 last:border-b-0 text-sm` |
| `.data-list .name` | `flex-1 pr-3 text-slate-700` |
| `.data-list .value` | `font-semibold whitespace-nowrap` |

### 4.8 Header & Footer

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `header` | `bg-gradient-to-br from-primary to-primary-light text-white p-8` |
| `footer` | `text-center py-8 text-slate-500 text-sm` |

### 4.9 Pass Rate Hero Section

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.pass-rate-hero` | `flex items-center gap-6 md:gap-8 bg-white p-6 rounded-xl shadow-md mb-6 flex-wrap` |
| `.pass-rate-circle` | `relative w-36 h-36 flex-shrink-0` |
| `.pass-rate-value` | `absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center` |
| `.pass-rate-value .number` | `text-3xl font-bold` |
| `.pass-rate-value .label` | `text-xs text-slate-500 uppercase tracking-wide` |
| `.pass-rate-details` | `flex-1 min-w-[250px]` |
| `.pass-rate-details h3` | `text-base font-semibold mb-3` |
| `.detail-grid` | `grid grid-cols-2 gap-3` |
| `.detail-item` | `flex flex-col` |
| `.detail-item .label` | `text-xs text-slate-500` |
| `.detail-item .value` | `text-lg font-semibold` |

### 4.10 Rankings Section

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.ranking-badges` | `flex gap-3 flex-wrap` |
| `.ranking-badge` | `flex-1 min-w-[100px] text-center p-4 bg-slate-50 rounded-lg` |
| `.ranking-badge .rank` | `text-2xl font-bold text-primary` |
| `.ranking-badge .context` | `text-xs text-slate-500 mt-1` |
| `.ranking-badge .percentile` | `inline-block mt-2 px-2 py-0.5 bg-primary text-white rounded-full text-xs font-semibold` |

### 4.11 Bar Charts (CSS-based)

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.bar-row` | `flex items-center mb-3` |
| `.bar-label` | `w-48 text-sm text-slate-700 flex-shrink-0` |
| `.bar-container` | `flex-1 flex items-center gap-3` |
| `.bar` | `h-6 bg-primary rounded min-w-1` |
| `.bar-value` | `text-sm text-slate-500 min-w-[60px]` |

### 4.12 Year/Age/Monthly Chart Columns

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.year-chart` | `flex items-end gap-2 h-48 py-5 overflow-x-auto` |
| `.year-bar-col` | `flex flex-col items-center min-w-[40px]` |
| `.year-bar-wrapper` | `h-28 w-7 flex items-end` |
| `.year-bar` | `w-full rounded-t` |
| `.year-label` | `text-xs mt-2 text-slate-500` |
| `.year-rate` | `text-xs font-semibold` |
| `.monthly-chart` | `flex items-end gap-1 h-36 py-4` |
| `.monthly-bar-col` | `flex-1 flex flex-col items-center min-w-[30px]` |
| `.age-chart` | `flex items-end gap-2 h-44 py-4` |
| `.age-bar-col` | `flex-1 flex flex-col items-center min-w-[50px]` |

### 4.13 Geographic Section

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.geo-split` | `grid grid-cols-1 md:grid-cols-2 gap-6` |
| `.geo-section h4` | `text-sm font-semibold mb-3 text-slate-500` |
| `.geo-section.best h4` | `text-sm font-semibold mb-3 text-good` |
| `.geo-section.worst h4` | `text-sm font-semibold mb-3 text-poor` |

### 4.14 Severity Bar

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.severity-bar` | `flex h-8 rounded-lg overflow-hidden mb-4` |
| `.severity-segment` | `flex items-center justify-center text-white text-xs font-semibold min-w-[40px]` |
| `.severity-legend` | `flex gap-4 flex-wrap justify-center` |
| `.severity-legend-item` | `flex items-center gap-1.5 text-sm` |
| `.severity-dot` | `w-3 h-3 rounded-full` |

### 4.15 Highlight Cards (Best/Worst Year)

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.highlight-stat` | `flex items-center gap-4 flex-wrap` |
| `.highlight-value` | `text-2xl font-bold` |
| `.highlight-detail` | `mt-2 text-slate-500 text-sm` |

### 4.16 Section Divider

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.section-divider` | `mt-8 mb-6 pb-2 border-b-2 border-slate-200` |

### 4.17 All Variants Table

| Old CSS Class | Tailwind Replacement |
|---------------|----------------------|
| `.all-variants-table` | `max-h-96 overflow-y-auto` |

---

## 5. Python Helper Functions to Create/Modify

### 5.1 Badge Generator

```python
def get_badge_html(rate: float, text: str = None) -> str:
    """Generate Tailwind-styled badge HTML."""
    display_text = text if text else f"{rate:.1f}%"
    base = "inline-block px-2.5 py-1 rounded-full text-sm font-semibold"

    if rate >= 80:
        return f'<span class="{base} bg-emerald-100 text-emerald-800">{display_text}</span>'
    elif rate >= 65:
        return f'<span class="{base} bg-amber-100 text-amber-800">{display_text}</span>'
    return f'<span class="{base} bg-red-100 text-red-800">{display_text}</span>'
```

### 5.2 Color Classes Helper

```python
def get_rate_color_class(rate: float) -> str:
    """Return Tailwind text color class based on pass rate."""
    if rate >= 80:
        return "text-good"
    elif rate >= 65:
        return "text-average"
    return "text-poor"

def get_rate_bg_color(rate: float) -> str:
    """Return hex color for inline styles (SVG, etc.)."""
    if rate >= 80:
        return "#10b981"
    elif rate >= 65:
        return "#f59e0b"
    return "#ef4444"
```

### 5.3 Card Generator

```python
def generate_card(title: str, body_content: str, icon: str = None, highlight: str = None) -> str:
    """Generate a card with optional icon and highlight border."""
    highlight_class = ""
    if highlight == "good":
        highlight_class = "border-l-4 border-good"
    elif highlight == "poor":
        highlight_class = "border-l-4 border-poor"

    icon_html = f'<i class="ph ph-{icon} text-lg text-slate-400"></i>' if icon else ""

    return f"""
    <div class="bg-white rounded-xl shadow-sm overflow-hidden mb-6 {highlight_class}">
        <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-800">{title}</h3>
            {icon_html}
        </div>
        <div class="p-5">
            {body_content}
        </div>
    </div>"""
```

### 5.4 Table Generator

```python
def generate_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate a Tailwind-styled table."""
    header_html = "".join(
        f'<th class="py-2.5 px-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide bg-slate-50 border-b border-slate-200">{h}</th>'
        for h in headers
    )

    rows_html = ""
    for row in rows:
        cells = "".join(f'<td class="py-2.5 px-3 border-b border-slate-100">{cell}</td>' for cell in row)
        rows_html += f"<tr class=\"hover:bg-slate-50\">{cells}</tr>"

    return f"""
    <table class="w-full text-sm">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>"""
```

---

## 6. Phosphor Icons to Use

Add icons to section headers for visual enhancement:

| Section | Icon | HTML |
|---------|------|------|
| Rankings | Trophy | `<i class="ph ph-trophy"></i>` |
| Pass Rate | Check Circle | `<i class="ph ph-check-circle"></i>` |
| Failures | Warning | `<i class="ph ph-warning"></i>` |
| Dangerous | Warning Octagon | `<i class="ph ph-warning-octagon"></i>` |
| Geographic | Map Pin | `<i class="ph ph-map-pin"></i>` |
| Seasonal | Calendar | `<i class="ph ph-calendar"></i>` |
| Mileage | Path | `<i class="ph ph-path"></i>` |
| Age Bands | Clock | `<i class="ph ph-clock"></i>` |
| Fuel Types | Gas Pump | `<i class="ph ph-gas-pump"></i>` |
| Best Year | Thumbs Up | `<i class="ph ph-thumbs-up"></i>` |
| Worst Year | Thumbs Down | `<i class="ph ph-thumbs-down"></i>` |
| Advisories | Info | `<i class="ph ph-info"></i>` |
| Retest | Arrow Clockwise | `<i class="ph ph-arrow-clockwise"></i>` |
| First MOT | Car | `<i class="ph ph-car"></i>` |
| Severity | Gauge | `<i class="ph ph-gauge"></i>` |

---

## 7. Responsive Breakpoints

Tailwind uses these breakpoints:
- `sm:` - 640px+
- `md:` - 768px+
- `lg:` - 1024px+
- `xl:` - 1280px+

### Key Responsive Patterns to Apply

```html
<!-- Two column grid that stacks on mobile -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-5">

<!-- Three column grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

<!-- Pass rate hero - stack on mobile -->
<div class="flex flex-col md:flex-row items-center gap-6">

<!-- Hide on mobile, show on desktop -->
<div class="hidden md:block">

<!-- Smaller text on mobile -->
<h1 class="text-xl md:text-2xl font-semibold">
```

---

## 8. Implementation Steps

### Step 1: Create Constants Module
Create `scripts/model_report_generator/tailwind_classes.py`:

```python
"""Tailwind CSS class constants for model report generation."""

# Layout
CONTAINER = "max-w-7xl mx-auto px-6 py-6"
GRID_2 = "grid grid-cols-1 md:grid-cols-2 gap-5 mb-6"
GRID_3 = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6"

# Cards
CARD = "bg-white rounded-xl shadow-sm overflow-hidden mb-6"
CARD_GOOD = f"{CARD} border-l-4 border-good"
CARD_POOR = f"{CARD} border-l-4 border-poor"
CARD_HEADER = "px-5 py-4 border-b border-slate-200 flex items-center justify-between"
CARD_TITLE = "text-base font-semibold text-slate-800"
CARD_BODY = "p-5"
CARD_BODY_COMPACT = "p-4"

# Badges
BADGE_BASE = "inline-block px-2.5 py-1 rounded-full text-sm font-semibold"
BADGE_GOOD = f"{BADGE_BASE} bg-emerald-100 text-emerald-800"
BADGE_AVG = f"{BADGE_BASE} bg-amber-100 text-amber-800"
BADGE_POOR = f"{BADGE_BASE} bg-red-100 text-red-800"

# Tables
TABLE = "w-full text-sm"
TH = "py-2.5 px-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide bg-slate-50 border-b border-slate-200"
TD = "py-2.5 px-3 border-b border-slate-100"
TR_HOVER = "hover:bg-slate-50"

# Typography
TITLE_LG = "text-xl font-semibold text-slate-800"
TITLE_MD = "text-base font-semibold text-slate-800"
TEXT_MUTED = "text-sm text-slate-500"
TEXT_XS_MUTED = "text-xs text-slate-500"

# Stats
STAT_VALUE_LG = "text-3xl font-bold"
STAT_VALUE_MD = "text-2xl font-bold"
STAT_LABEL = "text-sm text-slate-500 mt-1"

# Lists
LIST_ITEM = "flex justify-between py-2 border-b border-slate-100 last:border-b-0 text-sm"

# Header/Footer
HEADER = "bg-gradient-to-br from-primary to-primary-light text-white p-8"
FOOTER = "text-center py-8 text-slate-500 text-sm"

# Section divider
SECTION_DIVIDER = "mt-8 mb-6 pb-2 border-b-2 border-slate-200"

# Pass rate hero
HERO = "flex flex-col md:flex-row items-center gap-6 md:gap-8 bg-white p-6 rounded-xl shadow-md mb-6"
HERO_CIRCLE = "relative w-36 h-36 flex-shrink-0"
HERO_VALUE = "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
HERO_NUMBER = "text-3xl font-bold"
HERO_LABEL = "text-xs text-slate-500 uppercase tracking-wide"

# Rankings
RANKING_BADGES = "flex gap-3 flex-wrap"
RANKING_BADGE = "flex-1 min-w-[100px] text-center p-4 bg-slate-50 rounded-lg"
RANKING_RANK = "text-2xl font-bold text-primary"
RANKING_CONTEXT = "text-xs text-slate-500 mt-1"
RANKING_PERCENTILE = "inline-block mt-2 px-2 py-0.5 bg-primary text-white rounded-full text-xs font-semibold"

# Charts
YEAR_CHART = "flex items-end gap-2 h-48 py-5 overflow-x-auto"
YEAR_BAR_COL = "flex flex-col items-center min-w-[40px]"
YEAR_BAR_WRAPPER = "h-28 w-7 flex items-end"
MONTHLY_CHART = "flex items-end gap-1 h-36 py-4"
AGE_CHART = "flex items-end gap-2 h-44 py-4"

# Bar charts
BAR_ROW = "flex items-center mb-3"
BAR_LABEL = "w-48 text-sm text-slate-700 flex-shrink-0 truncate"
BAR_CONTAINER = "flex-1 flex items-center gap-3"
BAR = "h-6 bg-primary rounded"
BAR_VALUE = "text-sm text-slate-500 min-w-[60px]"

# Severity
SEVERITY_BAR = "flex h-8 rounded-lg overflow-hidden mb-4"
SEVERITY_SEGMENT = "flex items-center justify-center text-white text-xs font-semibold min-w-[40px]"
SEVERITY_LEGEND = "flex gap-4 flex-wrap justify-center"
SEVERITY_DOT = "w-3 h-3 rounded-full"

# Geographic
GEO_SPLIT = "grid grid-cols-1 md:grid-cols-2 gap-6"
```

### Step 2: Create Head Template Module
Create `scripts/model_report_generator/html_templates.py`:

```python
"""HTML template functions for model report generation."""

def generate_head(make: str, model: str, safe_make: str, safe_model: str,
                  total_tests: str, today_iso: str) -> str:
    """Generate the complete <head> section."""
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
```

### Step 3: Update Section Generators
Update each `generate_*_section()` function in `generate_model_report.py` to use Tailwind classes instead of CSS class names.

### Step 4: Update Main HTML Template
Modify `generate_html()` to:
1. Remove the entire `<style>` block (~700 lines)
2. Import and use the new head template
3. Replace all class references with Tailwind utilities

### Step 5: Test Generated Output
Generate a test report and verify:
1. Fonts load correctly (Jost)
2. Icons display (Phosphor)
3. Colors match (custom Tailwind config)
4. Responsive behavior works
5. File size is reduced

---

## 9. Expected Outcomes

| Metric | Before | After |
|--------|--------|-------|
| CSS lines in file | ~700 | ~5 |
| Generated HTML size | ~45KB | ~25KB |
| External dependencies | 0 | 4 CDN |
| Maintainability | Low | High |
| Consistency with site | Low | High |
| SEO metadata | Minimal | Complete |

---

## 10. Files to Create/Modify

### New Files
1. `scripts/model_report_generator/tailwind_classes.py` - Class constants
2. `scripts/model_report_generator/html_templates.py` - Head and template functions

### Modified Files
1. `scripts/model_report_generator/generate_model_report.py` - Main generator

---

## 11. Testing Checklist

- [ ] Generated HTML passes W3C validation
- [ ] Jost font loads and displays correctly
- [ ] Phosphor icons render in section headers
- [ ] Custom colors (good/average/poor/primary) work
- [ ] Responsive layout works at all breakpoints
- [ ] SVG circular progress renders correctly
- [ ] Tables are styled consistently
- [ ] Badges show correct colors for pass rates
- [ ] Charts (year/monthly/age) display properly
- [ ] Geographic split view works
- [ ] JSON-LD structured data is valid
- [ ] Open Graph tags render in social previews
- [ ] File size is reduced compared to before
- [ ] No console errors from CDN resources

---

## 12. Reference Links

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind CDN Play](https://tailwindcss.com/docs/installation/play-cdn)
- [Phosphor Icons](https://phosphoricons.com/)
- [Google Fonts - Jost](https://fonts.google.com/specimen/Jost)
- [Schema.org Article](https://schema.org/Article)
- [Open Graph Protocol](https://ogp.me/)
