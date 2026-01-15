"""
Model and manufacturer rankings section generators.
"""

from .utils import format_number, safe_html, title_case, get_rate_class


def generate_worst_models_section(insights) -> str:
    """Generate the worst models section."""
    rows = []
    for m in insights.worst_models[:15]:
        rate_class = get_rate_class(m.dangerous_rate)
        year_display = f"{m.year_from}-{m.year_to}" if m.year_from and m.year_to else "All years"
        rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))} {safe_html(title_case(m.model))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
                <td class="py-2 text-neutral-500">{year_display}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    return f'''      <!-- Section: Worst Models -->
      <section id="worst-models" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-red-100 text-red-700">
            <i class="ph ph-warning-octagon"></i>
          </div>
          <h2 class="article-section-title">The 15 Most Dangerous Models</h2>
        </div>

        <div class="article-prose">
          <p>These models have the highest rates of dangerous defects. Many are MPVs and people carriers
          which tend to be heavier and put more stress on tyres and brakes.</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Rank</th>
                <th class="text-left">Model</th>
                <th class="text-left">Dangerous Rate</th>
                <th class="text-left">Tests</th>
                <th class="text-left">Years</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="callout warning mt-4">
          <i class="ph ph-warning callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Pattern Alert</p>
            <p class="callout-text">Notice how many Ford MPVs appear in this list: Focus C-MAX, S-MAX, Grand C-MAX, Galaxy, C-MAX, and Mondeo. If buying a used Ford people carrier, budget for brake and tyre maintenance.</p>
          </div>
        </div>
      </section>'''


def generate_safest_models_section(insights) -> str:
    """Generate the safest models section."""
    rows = []
    for m in insights.safest_models[:15]:
        rate_class = get_rate_class(m.dangerous_rate)
        year_display = f"{m.year_from}-{m.year_to}" if m.year_from and m.year_to else "All years"
        rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))} {safe_html(title_case(m.model))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
                <td class="py-2 text-neutral-500">{year_display}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Find Prius test count for the callout
    prius = next((m for m in insights.model_rankings if m.model.upper() == 'PRIUS'), None)
    prius_tests = format_number(prius.total_tests) if prius else "over 1.5 million"

    return f'''      <!-- Section: Safest Models -->
      <section id="safest-models" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-emerald-100 text-emerald-700">
            <i class="ph ph-shield-check"></i>
          </div>
          <h2 class="article-section-title">The 15 Safest Models</h2>
        </div>

        <div class="article-prose">
          <p>These models have the lowest rates of dangerous defects. Premium sports cars, hybrids,
          and pickups dominate - often because they're better maintained or built to higher standards.</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Rank</th>
                <th class="text-left">Model</th>
                <th class="text-left">Dangerous Rate</th>
                <th class="text-left">Tests</th>
                <th class="text-left">Years</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="callout tip mt-4">
          <i class="ph ph-check-circle callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Toyota Prius Stands Out</p>
            <p class="callout-text">The Toyota Prius has just a {prius.dangerous_rate:.2f}% dangerous defect rate despite being a high-volume family car with {prius_tests} tests analysed. Its regenerative braking reduces brake wear significantly.</p>
          </div>
        </div>
      </section>'''


def generate_manufacturer_rankings_section(insights) -> str:
    """Generate the manufacturer rankings section."""
    rows = []
    for m in insights.make_rankings[:20]:
        rate_class = get_rate_class(m.dangerous_rate)
        rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Get bottom 10 (safest)
    safest_rows = []
    for m in insights.make_rankings[-10:][::-1]:
        rate_class = get_rate_class(m.dangerous_rate)
        safest_rows.append(f'''              <tr>
                <td class="py-2">#{m.rank}</td>
                <td class="py-2"><strong>{safe_html(title_case(m.make))}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{m.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(m.total_tests)}</td>
              </tr>''')

    safest_rows_html = "\n".join(safest_rows)

    return f'''      <!-- Section: Manufacturer Rankings -->
      <section id="manufacturer-rankings" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-blue-100 text-blue-700">
            <i class="ph ph-ranking"></i>
          </div>
          <h2 class="article-section-title">Manufacturer Rankings</h2>
        </div>

        <div class="article-prose">
          <p>We ranked all major manufacturers by their dangerous defect rate. The difference
          between best and worst is stark - nearly 3x higher for the worst manufacturers.</p>
        </div>

        <h3 class="text-lg font-semibold text-neutral-900 mt-6 mb-3 flex items-center gap-2">
          <i class="ph ph-warning text-red-600"></i>
          Worst 20 Manufacturers
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
{rows_html}
            </tbody>
          </table>
        </div>

        <h3 class="text-lg font-semibold text-neutral-900 mt-8 mb-3 flex items-center gap-2">
          <i class="ph ph-shield-check text-emerald-600"></i>
          Safest 10 Manufacturers
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
{safest_rows_html}
            </tbody>
          </table>
        </div>
      </section>'''
