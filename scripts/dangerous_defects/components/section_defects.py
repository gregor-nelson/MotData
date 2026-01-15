"""
Top defects section generator.
"""

from .utils import format_number, safe_html


def generate_top_defects_section(insights) -> str:
    """Generate the top defects section."""
    rows = []
    for d in insights.top_defects[:12]:
        rows.append(f'''              <tr>
                <td class="py-2">{safe_html(d.description.capitalize())}</td>
                <td class="py-2 text-neutral-600">{safe_html(d.category)}</td>
                <td class="py-2 text-right">{format_number(d.affected_models)}</td>
                <td class="py-2 text-right font-medium">{format_number(d.total_occurrences)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    return f'''      <!-- Section: Top Defects -->
      <section id="top-defects" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-red-100 text-red-700">
            <i class="ph ph-wrench"></i>
          </div>
          <h2 class="article-section-title">The Most Common Dangerous Defects</h2>
        </div>

        <div class="article-prose">
          <p>These are the specific defects that examiners flag as "dangerous" most often.
          Most are related to tyre wear and brake pad thickness. The "Models Affected" column shows how widespread each issue is across different vehicles.</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th class="text-left">Defect</th>
                <th class="text-left">Category</th>
                <th class="text-right">Models Affected</th>
                <th class="text-right">Occurrences</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="callout info mt-4">
          <i class="ph ph-info callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Prevention is Key</p>
            <p class="callout-text">Most dangerous defects are preventable with regular maintenance. Check your tyre tread depth monthly and have your brakes inspected at least annually.</p>
          </div>
        </div>
      </section>'''
