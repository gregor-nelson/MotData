"""
Deep dive section generators for vehicles, categories, and age-controlled analysis.
"""

from .utils import format_number, safe_html, title_case, get_rate_class


def generate_vehicle_deep_dive_section(insights) -> str:
    """Generate vehicle deep dive sections for all notable cars (8 vehicles)."""
    deep_dives = []

    # Show all 8 vehicles (was only 2)
    for key in insights.all_vehicle_deep_dive_keys:
        if key not in insights.vehicle_deep_dives:
            continue
        v = insights.vehicle_deep_dives[key]

        # Build category breakdown
        cat_items = []
        for c in v.by_category[:4]:
            cat_items.append(f'''            <div class="flex justify-between items-center py-1">
              <span class="text-neutral-700">{safe_html(c.get('category_name', ''))}</span>
              <span class="font-medium">{format_number(c.get('occurrences', 0))}</span>
            </div>''')

        # Build top defects
        defect_items = []
        for d in v.top_defects[:5]:
            defect_items.append(f'''            <li class="text-sm text-neutral-700">{safe_html(d.get('defect_description', ''))} <span class="text-neutral-500">({safe_html(d.get('category_name', ''))})</span></li>''')

        # Build by_model_year bar chart (6 most recent years)
        year_items = []
        years_data = sorted(v.by_model_year, key=lambda x: x.get('model_year', 0), reverse=True)[:6]
        if years_data:
            max_rate = max(y.get('rate', 0) for y in years_data) or 1
            for y in years_data:
                year = y.get('model_year', 0)
                rate = y.get('rate', 0)
                bar_width = int(rate / max_rate * 100)
                year_items.append(f'''              <div class="flex items-center gap-2 text-sm">
                <span class="w-12 text-neutral-600">{year}</span>
                <div class="flex-1 bg-neutral-200 rounded-full h-3">
                  <div class="bg-red-500 h-3 rounded-full" style="width: {bar_width}%"></div>
                </div>
                <span class="w-14 text-right font-medium">{rate:.1f}%</span>
              </div>''')

        rate_class = get_rate_class(v.dangerous_rate)

        # Determine if this is a "worst" or "safe" vehicle for styling
        is_safe = v.dangerous_rate < 4.0
        border_color = "border-emerald-200" if is_safe else "border-red-200"
        header_note = "Low risk" if is_safe else "High risk"
        header_color = "text-emerald-600" if is_safe else "text-red-600"

        deep_dives.append(f'''        <!-- {v.make} {v.model} Deep Dive -->
        <div class="bg-neutral-50 rounded-xl p-6 mb-6 border {border_color}">
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-xl font-semibold text-neutral-900">{safe_html(title_case(v.make))} {safe_html(title_case(v.model))}</h3>
              <p class="text-neutral-600">{v.year_from}-{v.year_to} models <span class="{header_color} text-sm">({header_note})</span></p>
            </div>
            <span class="data-badge {rate_class} text-base">{v.dangerous_rate:.2f}%</span>
          </div>

          <div class="grid sm:grid-cols-3 gap-4 mb-4">
            <div class="bg-white rounded-lg p-3 border border-neutral-200">
              <p class="text-2xl font-bold text-neutral-900">{format_number(v.total_tests)}</p>
              <p class="text-sm text-neutral-500">MOT tests analysed</p>
            </div>
            <div class="bg-white rounded-lg p-3 border border-neutral-200">
              <p class="text-2xl font-bold text-red-600">{format_number(v.total_dangerous)}</p>
              <p class="text-sm text-neutral-500">Dangerous defects</p>
            </div>
            <div class="bg-white rounded-lg p-3 border border-neutral-200">
              <p class="text-2xl font-bold text-neutral-900">{safe_html(v.by_category[0].get('category_name', 'Tyres')) if v.by_category else 'N/A'}</p>
              <p class="text-sm text-neutral-500">Top defect category</p>
            </div>
          </div>

          <div class="grid sm:grid-cols-2 gap-6">
            <div>
              <h4 class="font-semibold text-neutral-900 mb-2">Defects by Category</h4>
{"".join(cat_items)}
            </div>
            <div>
              <h4 class="font-semibold text-neutral-900 mb-2">Most Common Defects</h4>
              <ul class="space-y-1">
{"".join(defect_items)}
              </ul>
            </div>
          </div>
{f"""
          <div class="mt-4">
            <h4 class="font-semibold text-neutral-900 mb-2">Dangerous Defect Rate by Model Year</h4>
            <div class="space-y-1.5">
{"".join(year_items)}
            </div>
          </div>""" if year_items else ""}
        </div>''')

    deep_dives_html = "\n".join(deep_dives)

    return f'''      <!-- Section: Vehicle Deep Dives -->
      <section id="vehicle-deep-dives" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-indigo-100 text-indigo-700">
            <i class="ph ph-magnifying-glass-plus"></i>
          </div>
          <h2 class="article-section-title">Vehicle Deep Dives</h2>
        </div>

        <div class="article-prose mb-6">
          <p>A closer look at some popular models - what's actually going wrong? We've analysed
          both the worst and safest performers to show you exactly where the issues lie.</p>
        </div>

        <h3 class="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
          <i class="ph ph-warning text-red-600"></i>
          High-Risk Vehicles
        </h3>

{deep_dives_html}
      </section>'''


def generate_category_deep_dives_section(insights) -> str:
    """Generate category-specific deep dives (brakes, steering, suspension, tyres)."""
    if not insights.category_deep_dives:
        return ""

    category_sections = []

    # Define icons and colors for each category
    category_styles = {
        'brakes': {'icon': 'ph-disc', 'bg': 'bg-red-100', 'text': 'text-red-700'},
        'steering': {'icon': 'ph-steering-wheel', 'bg': 'bg-blue-100', 'text': 'text-blue-700'},
        'suspension': {'icon': 'ph-arrows-out-line-vertical', 'bg': 'bg-amber-100', 'text': 'text-amber-700'},
        'tyres': {'icon': 'ph-tire', 'bg': 'bg-orange-100', 'text': 'text-orange-700'},
    }

    for cat_key, cat_data in insights.category_deep_dives.items():
        style = category_styles.get(cat_key, {'icon': 'ph-warning', 'bg': 'bg-neutral-100', 'text': 'text-neutral-700'})

        rows = []
        for i, m in enumerate(cat_data.rankings[:10], 1):
            rate_class = get_rate_class(m.get('category_rate', 0) * 10)  # Scale up for coloring
            rows.append(f'''              <tr>
                <td class="py-2">#{i}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.get('make', '')))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.get('category_rate', 0):.3f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.get('total_tests', 0))}</td>
              </tr>''')

        rows_html = "\n".join(rows)

        category_sections.append(f'''        <div class="mb-8">
          <h3 class="text-lg font-semibold text-neutral-900 mb-3 flex items-center gap-2">
            <div class="w-8 h-8 rounded-full {style['bg']} {style['text']} flex items-center justify-center">
              <i class="ph {style['icon']}"></i>
            </div>
            {cat_data.name} Defects by Manufacturer
          </h3>
          <p class="text-sm text-neutral-600 mb-4">{safe_html(cat_data.description)}</p>

          <div class="article-table-wrapper">
            <table class="article-table">
              <thead>
                <tr>
                  <th class="text-left">Rank</th>
                  <th class="text-left">Manufacturer</th>
                  <th class="text-left">{cat_data.name} Rate</th>
                  <th class="text-left">Tests</th>
                </tr>
              </thead>
              <tbody>
{rows_html}
              </tbody>
            </table>
          </div>
        </div>''')

    sections_html = "\n".join(category_sections)

    return f'''      <!-- Section: Category Deep Dives -->
      <section id="category-deep-dives" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-teal-100 text-teal-700">
            <i class="ph ph-chart-bar"></i>
          </div>
          <h2 class="article-section-title">Defect Categories: Which Makes Are Worst?</h2>
        </div>

        <div class="article-prose mb-6">
          <p>Not all manufacturers have the same weaknesses. Some have particularly high rates of
          brake issues, while others struggle more with tyres or suspension. Here's the breakdown
          by defect category.</p>
        </div>

{sections_html}
      </section>'''


def generate_age_controlled_section(insights) -> str:
    """Generate age-controlled analysis section (2015 model year comparison)."""
    if not insights.age_controlled_2015:
        return ""

    # Build worst 10 rows
    worst_rows = []
    for m in insights.age_controlled_2015[:10]:
        rate_class = get_rate_class(m.dangerous_rate)
        worst_rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
              </tr>''')

    # Build best 10 rows (from end)
    best_rows = []
    for m in insights.age_controlled_2015[-10:][::-1]:
        rate_class = get_rate_class(m.dangerous_rate)
        best_rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
              </tr>''')

    worst_rows_html = "\n".join(worst_rows)
    best_rows_html = "\n".join(best_rows)

    return f'''      <!-- Section: Age-Controlled Analysis -->
      <section id="age-controlled" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-cyan-100 text-cyan-700">
            <i class="ph ph-calendar-check"></i>
          </div>
          <h2 class="article-section-title">Fair Comparison: 2015 Model Year Only</h2>
        </div>

        <div class="article-prose mb-6">
          <p>Older cars naturally have more issues. To make a fair comparison, we looked at vehicles
          from the same model year (2015) - now approximately 10 years old. This removes age as a
          confounding factor and shows which manufacturers truly build more durable vehicles.</p>
        </div>

        <div class="p-4 bg-cyan-50 border border-cyan-200 rounded-lg mb-6">
          <p class="text-sm text-cyan-800">
            <i class="ph ph-info text-cyan-600 mr-1"></i>
            <strong>Why 2015?</strong> These cars are old enough to show wear patterns but new enough
            to have substantial MOT test data. All vehicles are the same age, making this a true
            apples-to-apples comparison.
          </p>
        </div>

        <h3 class="text-lg font-semibold text-red-900 mb-3 flex items-center gap-2">
          <i class="ph ph-warning text-red-600"></i>
          Worst Ageing Makes (2015 Models)
        </h3>

        <div class="article-table-wrapper mb-6">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Rank</th>
                <th class="text-left">Manufacturer</th>
                <th class="text-left">Dangerous Rate</th>
                <th class="text-left">Tests</th>
              </tr>
            </thead>
            <tbody>
{worst_rows_html}
            </tbody>
          </table>
        </div>

        <h3 class="text-lg font-semibold text-emerald-900 mt-8 mb-3 flex items-center gap-2">
          <i class="ph ph-shield-check text-emerald-600"></i>
          Best Ageing Makes (2015 Models)
        </h3>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Rank</th>
                <th class="text-left">Manufacturer</th>
                <th class="text-left">Dangerous Rate</th>
                <th class="text-left">Tests</th>
              </tr>
            </thead>
            <tbody>
{best_rows_html}
            </tbody>
          </table>
        </div>

        <div class="callout tip mt-4">
          <i class="ph ph-lightbulb callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Key Insight</p>
            <p class="callout-text">Japanese manufacturers (Toyota, Honda, Mazda) consistently appear in the "best ageing" list, while some European brands show higher wear rates at the same age.</p>
          </div>
        </div>
      </section>'''
