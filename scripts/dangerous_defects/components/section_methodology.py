"""
Methodology section generator.
"""

from .utils import format_number, safe_html


def generate_methodology_section(insights) -> str:
    """Generate the methodology section."""
    methodology = insights.methodology

    return f'''      <!-- Section: Methodology -->
      <section id="methodology" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-neutral-200 text-neutral-700">
            <i class="ph ph-flask"></i>
          </div>
          <h2 class="article-section-title">Methodology</h2>
        </div>

        <div class="bg-neutral-50 rounded-lg p-6">
          <h3 class="font-semibold text-neutral-900 mb-3">How we calculated these rankings</h3>

          <ul class="space-y-2 text-neutral-700">
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Data source:</strong> Official DVSA MOT test data</span>
            </li>
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Tests analysed:</strong> {format_number(insights.total_tests)} MOT tests</span>
            </li>
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Definition:</strong> {safe_html(methodology.get('dangerous_defects_definition', 'Defects classified as Dangerous by DVSA'))}</span>
            </li>
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Rate calculation:</strong> {safe_html(methodology.get('rate_calculation', 'Dangerous defect occurrences / Total MOT tests * 100'))}</span>
            </li>
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Model rankings:</strong> Only models with 100,000+ tests included for statistical significance</span>
            </li>
            <li class="flex gap-2">
              <i class="ph ph-check text-emerald-600 mt-1"></i>
              <span><strong>Manufacturer rankings:</strong> Only manufacturers with 50,000+ tests included</span>
            </li>
          </ul>

          <p class="mt-4 text-sm text-neutral-600">
            <strong>Note:</strong> {safe_html(methodology.get('note', 'A single test can have multiple dangerous defects'))}
          </p>
        </div>
      </section>'''
