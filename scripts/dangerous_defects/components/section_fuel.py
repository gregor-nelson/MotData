"""
Fuel type analysis section generator.
"""

from .utils import format_number, safe_html, title_case, get_rate_class


def generate_fuel_analysis_section(insights) -> str:
    """Generate the fuel type analysis section."""
    # Extract hybrid and diesel rates for dynamic comparison
    hybrid = next((f for f in insights.fuel_comparison if f.fuel_type == 'HY'), None)
    diesel = next((f for f in insights.fuel_comparison if f.fuel_type == 'DI'), None)
    hybrid_rate = hybrid.dangerous_rate if hybrid else 0
    diesel_rate = diesel.dangerous_rate if diesel else 0
    hybrid_vs_diesel_pct = round((diesel_rate - hybrid_rate) / diesel_rate * 100) if diesel_rate else 0

    rows = []
    for f in sorted(insights.fuel_comparison, key=lambda x: x.dangerous_rate, reverse=True):
        rate_class = get_rate_class(f.dangerous_rate)
        rows.append(f'''              <tr>
                <td class="py-2"><strong>{safe_html(f.fuel_name)}</strong></td>
                <td class="py-2"><span class="data-badge {rate_class}">{f.dangerous_rate:.2f}%</span></td>
                <td class="py-2 text-neutral-500">{format_number(f.total_tests)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Diesel vs petrol examples
    example_rows = []
    for e in insights.diesel_vs_petrol_examples[:8]:
        example_rows.append(f'''              <tr>
                <td class="py-2">{safe_html(title_case(e.get('make', '')))} {safe_html(title_case(e.get('model', '')))} {e.get('model_year', '')}</td>
                <td class="py-2 text-emerald-600">{e.get('petrol_rate', 0):.1f}%</td>
                <td class="py-2 text-red-600">{e.get('diesel_rate', 0):.1f}%</td>
                <td class="py-2 font-semibold text-red-700">+{e.get('diesel_difference', 0):.1f}%</td>
              </tr>''')

    examples_html = "\n".join(example_rows)

    return f'''      <!-- Section: Fuel Type Analysis -->
      <section id="fuel-analysis" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-purple-100 text-purple-700">
            <i class="ph ph-gas-pump"></i>
          </div>
          <h2 class="article-section-title">Diesel vs Petrol: Which is Safer?</h2>
        </div>

        <div class="article-prose">
          <p>Diesel vehicles consistently show higher dangerous defect rates than petrol equivalents.
          The heavier diesel engines put more stress on brakes and tyres.</p>
        </div>

        <div class="article-table-wrapper mb-6">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Fuel Type</th>
                <th class="text-left">Dangerous Rate</th>
                <th class="text-left">Tests Analysed</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="p-4 bg-purple-50 border border-purple-200 rounded-lg mb-6">
          <p class="font-semibold text-purple-900 mb-1">Hybrids are the safest choice</p>
          <p class="text-sm text-purple-800">Hybrid vehicles have a {hybrid_rate:.2f}% dangerous defect rate - {hybrid_vs_diesel_pct}% lower than diesels. Regenerative braking significantly reduces brake wear.</p>
        </div>

        <h3 class="text-lg font-semibold text-neutral-900 mb-3">Same Model, Different Fuel: Direct Comparisons</h3>

        <div class="article-prose mb-4">
          <p>When we compare the exact same model and year in petrol vs diesel, the difference is dramatic:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Model</th>
                <th class="text-left">Petrol Rate</th>
                <th class="text-left">Diesel Rate</th>
                <th class="text-left">Difference</th>
              </tr>
            </thead>
            <tbody>
{examples_html}
            </tbody>
          </table>
        </div>
      </section>'''
