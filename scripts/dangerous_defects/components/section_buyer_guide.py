"""
Used car buyer guide section generator.
"""

from .utils import safe_html, title_case


def generate_buyer_guide_section(insights) -> str:
    """Generate the used car buyer guide section."""
    # Worst to avoid 2015-2017
    worst_2015_rows = []
    for e in insights.worst_2015_2017[:10]:
        worst_2015_rows.append(f'''              <tr class="bg-red-50">
                <td class="py-2">{safe_html(title_case(e.make))} {safe_html(title_case(e.model))}</td>
                <td class="py-2">{e.model_year}</td>
                <td class="py-2">{e.fuel_name}</td>
                <td class="py-2"><span class="data-badge rate-poor">{e.dangerous_rate:.1f}%</span></td>
              </tr>''')

    # Worst to avoid 2018-2020 (NEW - was missing)
    worst_2018_rows = []
    for e in insights.worst_2018_2020[:10]:
        worst_2018_rows.append(f'''              <tr class="bg-red-50">
                <td class="py-2">{safe_html(title_case(e.make))} {safe_html(title_case(e.model))}</td>
                <td class="py-2">{e.model_year}</td>
                <td class="py-2">{e.fuel_name}</td>
                <td class="py-2"><span class="data-badge rate-poor">{e.dangerous_rate:.1f}%</span></td>
              </tr>''')

    # Safest 2015-2017
    safest_2015_rows = []
    for e in insights.safest_2015_2017[:10]:
        safest_2015_rows.append(f'''              <tr class="bg-emerald-50">
                <td class="py-2">{safe_html(title_case(e.make))} {safe_html(title_case(e.model))}</td>
                <td class="py-2">{e.model_year}</td>
                <td class="py-2">{e.fuel_name}</td>
                <td class="py-2"><span class="data-badge rate-excellent">{e.dangerous_rate:.1f}%</span></td>
              </tr>''')

    # Safest 2018-2020
    safest_2018_rows = []
    for e in insights.safest_2018_2020[:10]:
        safest_2018_rows.append(f'''              <tr class="bg-emerald-50">
                <td class="py-2">{safe_html(title_case(e.make))} {safe_html(title_case(e.model))}</td>
                <td class="py-2">{e.model_year}</td>
                <td class="py-2">{e.fuel_name}</td>
                <td class="py-2"><span class="data-badge rate-excellent">{e.dangerous_rate:.1f}%</span></td>
              </tr>''')

    return f'''      <!-- Section: Used Car Buyer Guide -->
      <section id="buyer-guide" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-orange-100 text-orange-700">
            <i class="ph ph-shopping-cart"></i>
          </div>
          <h2 class="article-section-title">Used Car Buyer's Safety Guide</h2>
        </div>

        <div class="article-prose">
          <p>If you're buying a used car, this section shows which specific year/model/fuel combinations
          to avoid - and which are the safest choices.</p>
        </div>

        <h3 class="text-lg font-semibold text-red-900 mt-6 mb-3 flex items-center gap-2">
          <i class="ph ph-x-circle text-red-600"></i>
          Avoid: Cars from 2015-2017
        </h3>

        <div class="article-table-wrapper mb-6">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Model</th>
                <th class="text-left">Year</th>
                <th class="text-left">Fuel</th>
                <th class="text-left">Dangerous Rate</th>
              </tr>
            </thead>
            <tbody>
{"".join(worst_2015_rows)}
            </tbody>
          </table>
        </div>

        <h3 class="text-lg font-semibold text-red-900 mt-8 mb-3 flex items-center gap-2">
          <i class="ph ph-x-circle text-red-600"></i>
          Avoid: Cars from 2018-2020
        </h3>

        <div class="article-table-wrapper mb-6">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Model</th>
                <th class="text-left">Year</th>
                <th class="text-left">Fuel</th>
                <th class="text-left">Dangerous Rate</th>
              </tr>
            </thead>
            <tbody>
{"".join(worst_2018_rows)}
            </tbody>
          </table>
        </div>

        <h3 class="text-lg font-semibold text-emerald-900 mt-8 mb-3 flex items-center gap-2">
          <i class="ph ph-check-circle text-emerald-600"></i>
          Safe Choices: Cars from 2015-2017
        </h3>

        <div class="article-table-wrapper mb-6">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Model</th>
                <th class="text-left">Year</th>
                <th class="text-left">Fuel</th>
                <th class="text-left">Dangerous Rate</th>
              </tr>
            </thead>
            <tbody>
{"".join(safest_2015_rows)}
            </tbody>
          </table>
        </div>

        <h3 class="text-lg font-semibold text-emerald-900 mt-8 mb-3 flex items-center gap-2">
          <i class="ph ph-check-circle text-emerald-600"></i>
          Safe Choices: Newer Cars (2018-2020)
        </h3>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Model</th>
                <th class="text-left">Year</th>
                <th class="text-left">Fuel</th>
                <th class="text-left">Dangerous Rate</th>
              </tr>
            </thead>
            <tbody>
{"".join(safest_2018_rows)}
            </tbody>
          </table>
        </div>
      </section>'''
