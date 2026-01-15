"""
HTML head section generator with SEO meta tags and JSON-LD structured data.
"""

from .utils import format_number


def generate_faq_jsonld(insights) -> str:
    """Generate FAQ items for JSON-LD schema."""
    # Extract category percentages dynamically
    tyres_cat = next((c for c in insights.categories if 'tyre' in c.name.lower()), None)
    brakes_cat = next((c for c in insights.categories if 'brake' in c.name.lower()), None)
    tyres_pct = tyres_cat.percentage_of_all if tyres_cat else 0
    brakes_pct = brakes_cat.percentage_of_all if brakes_cat else 0

    faqs = [
        {
            "question": "What is the most dangerous car on UK roads?",
            "answer": f"According to official DVSA MOT data, the {insights.most_dangerous_model.get('make', '')} {insights.most_dangerous_model.get('model', '')} has the highest rate of dangerous defects at {insights.most_dangerous_model.get('rate', 0):.2f}%, based on {format_number(insights.most_dangerous_model.get('tests', 0))} MOT tests."
        },
        {
            "question": "What is the safest car based on MOT dangerous defect data?",
            "answer": f"The {insights.safest_model.get('make', '')} {insights.safest_model.get('model', '')} has the lowest dangerous defect rate at just {insights.safest_model.get('rate', 0):.2f}%, making it the safest car in our analysis of {format_number(insights.total_tests)} MOT tests."
        },
        {
            "question": "Are diesel cars more dangerous than petrol cars?",
            "answer": f"Yes, our analysis shows diesel vehicles have a {insights.diesel_vs_petrol_gap} higher dangerous defect rate than petrol equivalents. This is primarily due to heavier weight causing more brake and tyre wear."
        },
        {
            "question": "What are the most common dangerous defects?",
            "answer": f"Tyres account for {tyres_pct:.1f}% of all dangerous defects, primarily tread depth below 1.6mm and structural damage. Brakes account for {brakes_pct:.1f}%, mainly worn brake pads under 1.5mm thick."
        }
    ]

    items = []
    for faq in faqs:
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


def generate_html_head(insights, today: str) -> str:
    """Generate the HTML head section with SEO meta tags and JSON-LD."""
    description = (
        f"We analysed {format_number(insights.total_tests)} MOT tests to reveal which cars have "
        f"the most dangerous defects on UK roads. Data shows a {insights.rate_difference_factor}x "
        f"difference between the safest and most dangerous models."
    )

    return f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Most Dangerous Cars on UK Roads: Official MOT Data Analysis | Motorwise</title>
  <meta name="description" content="{description}">

  <!-- Canonical -->
  <link rel="canonical" href="https://www.motorwise.io/articles/most-dangerous-cars-uk.html">

  <!-- Open Graph -->
  <meta property="og:title" content="The Most Dangerous Cars on UK Roads | Motorwise">
  <meta property="og:description" content="{format_number(insights.total_tests)} MOT tests analysed. See which cars have the most dangerous defects.">
  <meta property="og:url" content="https://www.motorwise.io/articles/most-dangerous-cars-uk.html">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Motorwise">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="The Most Dangerous Cars on UK Roads | Motorwise">
  <meta name="twitter:description" content="{format_number(insights.total_tests)} MOT tests analysed. See which cars have the most dangerous defects.">

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
  <link rel="stylesheet" href="/styles/articles.css">

  <!-- JSON-LD Structured Data: Article -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "The Most Dangerous Cars on UK Roads: Official MOT Data Analysis",
    "description": "{description}",
    "url": "https://www.motorwise.io/articles/most-dangerous-cars-uk.html",
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
    }}
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
        "name": "Most Dangerous Cars UK",
        "item": "https://www.motorwise.io/articles/most-dangerous-cars-uk.html"
      }}
    ]
  }}
  </script>

  <!-- JSON-LD Structured Data: FAQPage -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [{generate_faq_jsonld(insights)}
    ]
  }}
  </script>

  <!-- Custom Styles -->
  <style>
    #reading-progress {{
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: linear-gradient(90deg, #dc2626, #ef4444);
      z-index: 100;
      transition: width 0.1s ease;
    }}
    .rate-excellent {{ color: #059669; background: #d1fae5; }}
    .rate-good {{ color: #16a34a; background: #dcfce7; }}
    .rate-average {{ color: #ca8a04; background: #fef9c3; }}
    .rate-poor {{ color: #dc2626; background: #fee2e2; }}
    .data-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.125rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}
    .danger-callout {{
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
      border: 1px solid #fecaca;
      border-left: 4px solid #dc2626;
      border-radius: 0.5rem;
      padding: 1rem 1.25rem;
      margin: 1.5rem 0;
    }}
  </style>
</head>
'''
