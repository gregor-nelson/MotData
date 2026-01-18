"""
HTML Layout Components
======================
HTML head, body structure, TOC, and JSON-LD generation.
"""

import re

from .data_classes import (
    ArticleInsights,
    ARTICLE_SECTIONS,
    format_number,
    safe_html,
    generate_faq_data,
)
from . import sections


def generate_faq_jsonld(insights: ArticleInsights) -> str:
    """Generate FAQ items for JSON-LD schema."""
    faqs = generate_faq_data(insights)

    items = []
    for faq in faqs:
        # Escape quotes in question and answer
        q = faq['question'].replace('"', '\\"')
        a = faq['answer'].replace('"', '\\"')
        items.append(f'''
      {{
        "@type": "Question",
        "name": "{q}",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "{a}"
        }}
      }}''')

    return ",".join(items)


def generate_html_head(insights: ArticleInsights, today: str) -> str:
    """Generate the HTML head section with SEO meta tags and JSON-LD."""
    make_slug = insights.make.lower().replace(' ', '-').replace('_', '-')

    # Get top models for description
    top_models = [m.name for m in insights.top_models[:5]]
    models_list = ", ".join(top_models[:-1]) + f" and {top_models[-1]}" if len(top_models) > 1 else top_models[0] if top_models else ""

    description = f"Which {insights.title_make} models are most reliable? We analysed {format_number(insights.total_tests)} real UK MOT tests to reveal pass rates for every {models_list} by year. Data-driven buying guide."

    # Generate FAQ JSON-LD
    faq_items = generate_faq_jsonld(insights)

    return f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Most Reliable {insights.title_make} Models: Real MOT Data Analysis (2000-2023) | Motorwise</title>
  <meta name="description" content="{description}">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/articles/content/reliability/{make_slug}-most-reliable-models.html">

  <!-- Open Graph -->
  <meta property="og:title" content="Most Reliable {insights.title_make} Models: Real MOT Data Analysis | Motorwise">
  <meta property="og:description" content="{format_number(insights.total_tests)} MOT tests analysed. See which {insights.title_make} models pass most often and which years to avoid.">
  <meta property="og:url" content="https://www.motorwise.io/articles/content/reliability/{make_slug}-most-reliable-models.html">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Motorwise">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Most Reliable {insights.title_make} Models: Real MOT Data Analysis | Motorwise">
  <meta name="twitter:description" content="{format_number(insights.total_tests)} MOT tests analysed. See which {insights.title_make} models pass most often and which years to avoid.">

  <!-- AI/LLM Discovery -->
  <meta name="ai-content-declaration" content="human-created, data-driven">
  <meta name="data-sources" content="DVSA MOT History API">
  <meta name="llms-txt" content="https://www.motorwise.io/llms-reliability.txt">

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

  <!-- JSON-LD Structured Data: Article -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Most Reliable {insights.title_make} Models: Real MOT Data Analysis (2000-2023)",
    "description": "{description}",
    "url": "https://www.motorwise.io/articles/content/reliability/{make_slug}-most-reliable-models.html",
    "datePublished": "{today}",
    "dateModified": "{today}",
    "author": {{
      "@type": "Organization",
      "name": "Motorwise"
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "Motorwise",
      "url": "https://www.motorwise.io"
    }},
    "keywords": ["{insights.title_make} reliability","{insights.title_make} MOT pass rate","most reliable {insights.title_make}","{insights.title_make} {top_models[0] if top_models else ''} reliability","{insights.title_make} MOT data","UK MOT data","DVSA data"]
  }}
  </script>

  <!-- JSON-LD Structured Data: BreadcrumbList -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://www.motorwise.io"
      }},
      {{
        "@type": "ListItem",
        "position": 2,
        "name": "Guides & Articles",
        "item": "https://www.motorwise.io/articles/"
      }},
      {{
        "@type": "ListItem",
        "position": 3,
        "name": "Most Reliable {insights.title_make} Models",
        "item": "https://www.motorwise.io/articles/content/reliability/{make_slug}-most-reliable-models.html"
      }}
    ]
  }}
  </script>

  <!-- JSON-LD Structured Data: FAQPage -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [{faq_items}
    ]
  }}
  </script>

  <!-- JSON-LD Structured Data: Dataset (AI Visibility) -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Motorwise {insights.title_make} MOT Reliability Data",
    "description": "MOT pass rate analysis for {insights.title_make} vehicles based on {format_number(insights.total_tests)} real UK MOT tests (2000-2023)",
    "url": "https://www.motorwise.io/articles/content/reliability/{make_slug}-most-reliable-models.html",
    "creator": {{
      "@type": "Organization",
      "name": "Motorwise"
    }},
    "datePublished": "{today}",
    "dateModified": "{today}",
    "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "isBasedOn": {{
      "@type": "GovernmentService",
      "name": "DVSA MOT History",
      "provider": {{
        "@type": "GovernmentOrganization",
        "name": "Driver and Vehicle Standards Agency"
      }}
    }},
    "measurementTechnique": "Aggregated MOT test pass/fail results",
    "variableMeasured": [
      "MOT Pass Rate",
      "Test Count by Model",
      "Fuel Type Comparison"
    ],
    "temporalCoverage": "2000/2023",
    "spatialCoverage": {{
      "@type": "Country",
      "name": "United Kingdom"
    }}
  }}
  </script>


  <!-- Reading Progress Bar Style & Mobile Gradient -->
  <style>
    /* Mobile gradient background - matches tools pages */
    @media (max-width: 767px) {{
      body {{
        background: linear-gradient(180deg, #EFF6FF 0%, #EFF6FF 60%, #FFFFFF 100%);
        min-height: 100vh;
      }}
    }}

    #reading-progress {{
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: linear-gradient(90deg, #2563eb, #3b82f6);
      z-index: 100;
      transition: width 0.1s ease;
    }}
    .pass-rate-excellent {{ color: #059669; background: #d1fae5; }}
    .pass-rate-good {{ color: #16a34a; background: #dcfce7; }}
    .pass-rate-average {{ color: #ca8a04; background: #fef9c3; }}
    .pass-rate-poor {{ color: #dc2626; background: #fee2e2; }}
    .data-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.125rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}
  </style>
</head>
'''


def generate_toc_html(insights: ArticleInsights) -> str:
    """
    Generate the Table of Contents sidebar HTML.

    Follows the Legal pages pattern with:
    - Mobile: Collapsible toggle button
    - Desktop: Sticky sidebar navigation
    - Active section tracking (via JavaScript)

    Only includes sections that have content (via get_available_sections).
    """
    # Get sections that have content for this make
    available_sections = insights.get_available_sections()

    # Build TOC links only for available sections
    toc_links = []
    toc_index = 0
    for section in ARTICLE_SECTIONS:
        # Skip sections without content
        if section.id not in available_sections:
            continue

        toc_index += 1

        # Use make-prefixed ID for competition section
        section_id = section.id
        if section_id == "competition":
            section_id = f"{insights.make.lower()}-vs-competition"

        # Format title with make name where appropriate
        title = section.title
        if "{make}" in title:
            title = title.replace("{make}", insights.title_make)
        elif title == "vs Competition":
            title = f"{insights.title_make} vs Competition"

        toc_links.append(f'''          <li class="article-toc-item">
            <a href="#{section_id}" class="toc-link">
              <span class="toc-link-number">{toc_index}.</span>
              <span class="toc-link-text">{safe_html(title)}</span>
            </a>
          </li>''')

    links_html = "\n".join(toc_links)
    section_count = len(toc_links)

    return f'''    <!-- Table of Contents Sidebar -->
    <aside class="article-sidebar">
      <nav class="article-toc" aria-label="Table of contents">
        <!-- Mobile Toggle -->
        <button class="article-toc-toggle" aria-expanded="false">
          <div class="article-toc-toggle-content">
            <i class="ph ph-list article-toc-toggle-icon"></i>
            <span class="article-toc-toggle-label">Contents</span>
            <span class="article-toc-count">{section_count}</span>
          </div>
          <i class="ph ph-caret-down article-toc-caret"></i>
        </button>

        <!-- TOC Content -->
        <div class="article-toc-content">
          <!-- Desktop Header -->
          <div class="article-toc-header">
            <i class="ph ph-list article-toc-header-icon"></i>
            <span class="article-toc-header-text">Contents</span>
          </div>

          <!-- Navigation Links -->
          <ul class="article-toc-list">
{links_html}
          </ul>
        </div>
      </nav>
    </aside>'''


def generate_html_body(insights: ArticleInsights, today_display: str) -> str:
    """
    Generate the HTML body section with two-column layout.

    Structure:
    - Full-width header section (above two-column layout)
    - Two-column layout:
      - Sidebar: Sticky TOC
      - Main: All content sections with scroll-reveal animations
    """

    # -------------------------------------------------------------------------
    # Header Content (full width, above two-column layout)
    # -------------------------------------------------------------------------
    # Use placeholder - will be replaced with actual word count at the end
    READ_TIME_PLACEHOLDER = "{{READ_TIME}}"
    header_content = []
    header_content.append(sections.generate_header_section(insights, today_display, READ_TIME_PLACEHOLDER))
    header_content.append(sections.generate_key_findings_section(insights))
    header_content.append(sections.generate_intro_section(insights))
    header_html = "\n".join(header_content)

    # -------------------------------------------------------------------------
    # Main Content Sections (inside two-column layout with scroll-reveal)
    # -------------------------------------------------------------------------
    main_sections = []
    reveal_index = 1

    # Helper to wrap section with scroll-reveal
    def wrap_scroll_reveal(html: str, index: int) -> str:
        return f'''      <div class="scroll-reveal" data-reveal-index="{index}">
{html}
      </div>'''

    # Competitor comparison
    main_sections.append(wrap_scroll_reveal(sections.generate_competitors_section(insights), reveal_index))
    reveal_index += 1

    # Best models by pass rate
    main_sections.append(wrap_scroll_reveal(sections.generate_best_models_section(insights), reveal_index))
    reveal_index += 1

    # Durability champions (proven, 11+ years)
    main_sections.append(wrap_scroll_reveal(sections.generate_durability_section(insights), reveal_index))
    reveal_index += 1

    # Early performers (3-6 years, with caveat)
    main_sections.append(wrap_scroll_reveal(sections.generate_early_performers_section(insights), reveal_index))
    reveal_index += 1

    # Model breakdowns (individual model sections - not in TOC)
    model_breakdowns = sections.generate_model_breakdowns_section(insights)
    if model_breakdowns.strip():
        main_sections.append(wrap_scroll_reveal(model_breakdowns, reveal_index))
        reveal_index += 1

    # Fuel type analysis
    main_sections.append(wrap_scroll_reveal(sections.generate_fuel_analysis_section(insights), reveal_index))
    reveal_index += 1

    # Models to avoid
    main_sections.append(wrap_scroll_reveal(sections.generate_avoid_section(insights), reveal_index))
    reveal_index += 1

    # Common failures
    main_sections.append(wrap_scroll_reveal(sections.generate_failures_section(insights), reveal_index))
    reveal_index += 1

    # FAQs
    main_sections.append(wrap_scroll_reveal(sections.generate_faqs_section(insights), reveal_index))
    reveal_index += 1

    # Buying recommendations
    main_sections.append(wrap_scroll_reveal(sections.generate_recommendations_section(insights), reveal_index))
    reveal_index += 1

    # Methodology
    main_sections.append(wrap_scroll_reveal(sections.generate_methodology_section(insights), reveal_index))
    reveal_index += 1

    # Bottom CTA (no scroll-reveal for CTA)
    main_sections.append(sections.generate_cta_section(insights))

    main_sections_html = "\n".join(main_sections)

    # -------------------------------------------------------------------------
    # Generate TOC Sidebar
    # -------------------------------------------------------------------------
    toc_html = generate_toc_html(insights)

    # Build HTML with placeholder
    html = f'''<body class="bg-white md:bg-neutral-50 min-h-screen">
  <!-- Reading Progress Bar -->
  <div id="reading-progress" style="width: 0%"></div>

  <!-- Shared Header (injected by articles-loader.js) -->
  <div id="mw-header"></div>

  <main id="main-content" class="max-w-6xl mx-auto px-4 py-6 sm:py-8 lg:py-12">
    <!-- Breadcrumb -->
    <nav aria-label="Breadcrumb" class="flex items-center gap-2 text-sm text-neutral-500 mb-6">
      <a href="/" class="hover:text-blue-600 transition-colors">Home</a>
      <i class="ph ph-caret-right text-xs"></i>
      <a href="/articles/content/index.html" class="hover:text-blue-600 transition-colors">Guides</a>
      <i class="ph ph-caret-right text-xs"></i>
      <span class="text-neutral-900">Most Reliable {insights.title_make} Models</span>
    </nav>

    <article>
      <!-- Header Section (Full Width) -->
{header_html}

      <!-- Two-Column Layout -->
      <div class="article-layout">
{toc_html}

        <!-- Main Content -->
        <div class="article-main">
{main_sections_html}
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
</html>'''

    # Calculate actual read time from word count
    text_only = re.sub(r'<[^>]+>', ' ', html)  # Strip HTML tags
    text_only = re.sub(r'\s+', ' ', text_only)  # Normalize whitespace
    word_count = len(text_only.split())
    read_time = max(1, round(word_count / 200))  # 200 wpm

    # Replace placeholder with actual read time
    return html.replace(READ_TIME_PLACEHOLDER, str(read_time))
