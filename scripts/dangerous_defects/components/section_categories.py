"""
Category breakdown section generator.
"""

from .utils import format_number, safe_html


def generate_category_breakdown_section(insights) -> str:
    """Generate the defect category breakdown section."""
    rows = []
    for c in insights.categories[:8]:
        if c.percentage_of_all < 0.05:
            continue
        rows.append(f'''              <tr>
                <td class="py-2"><strong>{safe_html(c.name)}</strong></td>
                <td class="py-2 text-right">{format_number(c.total_occurrences)}</td>
                <td class="py-2 text-right"><span class="font-semibold">{c.percentage_of_all:.1f}%</span></td>
              </tr>''')

    rows_html = "\n".join(rows)

    tyres_cat = next((c for c in insights.categories if 'tyre' in c.name.lower()), None)
    brakes_cat = next((c for c in insights.categories if 'brake' in c.name.lower()), None)

    tyres_pct = tyres_cat.percentage_of_all if tyres_cat else 0
    brakes_pct = brakes_cat.percentage_of_all if brakes_cat else 0

    return f'''      <!-- Section: Category Breakdown -->
      <section id="category-breakdown" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-amber-100 text-amber-700">
            <i class="ph ph-chart-pie"></i>
          </div>
          <h2 class="article-section-title">What Makes a Car "Dangerous"?</h2>
        </div>

        <div class="article-prose">
          <p>Two categories dominate dangerous defects: <strong>tyres</strong> and <strong>brakes</strong>.
          Together they account for nearly 99% of all dangerous defects recorded.</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Category</th>
                <th class="text-right">Occurrences</th>
                <th class="text-right">% of All</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="grid sm:grid-cols-2 gap-4 mt-6">
          <div class="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <i class="ph ph-tire text-orange-600 text-xl"></i>
              <span class="font-semibold text-orange-900">Tyres: {tyres_pct:.1f}%</span>
            </div>
            <p class="text-sm text-orange-800">Worn tread, structural damage, bulges and tears</p>
          </div>
          <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <i class="ph ph-disc text-red-600 text-xl"></i>
              <span class="font-semibold text-red-900">Brakes: {brakes_pct:.1f}%</span>
            </div>
            <p class="text-sm text-red-800">Worn pads, weakened discs, efficiency failures</p>
          </div>
        </div>
      </section>'''
