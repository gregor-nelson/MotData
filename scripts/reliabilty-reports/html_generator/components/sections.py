"""
Article Section Generators
==========================
All HTML section generators for the MOT reliability articles.
"""

from .data_classes import (
    ArticleInsights,
    DurabilityVehicle,
    EarlyPerformer,
    format_number,
    safe_html,
    slugify,
    get_pass_rate_class,
    MIN_TESTS_PROVEN_DURABILITY,
    MIN_TESTS_EARLY_PERFORMER,
    AVOID_PASS_RATE_THRESHOLD,
    AVOID_VS_NATIONAL_THRESHOLD,
    PASS_RATE_EXCELLENT,
    generate_faq_data,
    # Derived constants
    DATA_YEAR_START,
    DATA_YEAR_END,
    PASS_RATE_EXCEPTIONAL,
    VS_NATIONAL_EXCEPTIONAL,
    VS_NATIONAL_GOOD,
    VS_NATIONAL_AROUND_AVERAGE,
    # Editorial constants
    SAMPLE_SIZE_LOW,
    SAMPLE_SIZE_MODERATE,
    MIN_TESTS_MODEL_BREAKDOWN,
    MIN_TESTS_FAQ_POPULAR,
    RANK_TOP_PERFORMER,
    # Methodology display values
    METHODOLOGY_TOTAL_TESTS,
    METHODOLOGY_YEAR_RANGE_EXAMPLE,
)


def generate_header_section(insights: ArticleInsights, today_display: str, read_time: str) -> str:
    """Generate the article header."""
    # Calculate actual year range from core_models data
    # Filter for reasonable years (1970+ to exclude data anomalies like "1012")
    if insights.core_models:
        valid_years_from = [m.year_from for m in insights.core_models if 1970 <= m.year_from <= 2030]
        valid_years_to = [m.year_to for m in insights.core_models if 1970 <= m.year_to <= 2030]
        if valid_years_from and valid_years_to:
            min_year = min(valid_years_from)
            max_year = max(valid_years_to)
            year_range = f"{min_year}-{max_year}"
        else:
            year_range = f"{DATA_YEAR_START}-{DATA_YEAR_END}"  # Fallback for no valid years
    else:
        year_range = f"{DATA_YEAR_START}-{DATA_YEAR_END}"  # Fallback

    return f'''      <!-- Header -->
      <header class="mb-8">
        <div class="flex flex-wrap items-center gap-3 mb-4">
          <span class="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-full border bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-600 border-blue-200/50">
            <i class="ph ph-chart-bar"></i>
            Reliability Data
          </span>
          <span class="text-sm text-neutral-500">{read_time} min read</span>
          <span class="text-sm text-neutral-500">Updated {today_display}</span>
        </div>

        <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
          Most Reliable {insights.title_make} Models: Real MOT Data Analysis
        </h1>

        <p class="text-lg text-neutral-600 leading-relaxed">
          We analysed {format_number(insights.total_tests)} real UK MOT tests to reveal which {insights.title_make} models pass most often, which years to buy, and which to avoid entirely.
        </p>
      </header>

      <!-- Data Source Callout - Enhanced with gradient icon -->
      <div class="flex items-center gap-4 p-4 bg-gradient-to-br from-emerald-50 to-emerald-100/50 border border-emerald-200/50 rounded-xl mb-8 transition-all hover:-translate-y-0.5 hover:shadow-md">
        <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 shadow-sm">
          <i class="ph ph-database text-emerald-600 text-xl"></i>
        </div>
        <div>
          <p class="text-base font-semibold text-emerald-700">{format_number(insights.total_tests)} MOT tests analysed</p>
          <p class="text-sm text-emerald-600">Real DVSA data covering every {insights.title_make} model from {year_range}</p>
        </div>
      </div>'''


def generate_key_findings_section(insights: ArticleInsights) -> str:
    """Generate the key findings summary boxes."""
    # Find best model and best single year
    top_model = insights.top_models[0] if insights.top_models else None
    best_year = insights.best_models[0] if insights.best_models else None
    durability_champ = insights.get_top_durable_model()

    vs_national_text = f"+{insights.vs_national:.1f}%" if insights.vs_national >= 0 else f"{insights.vs_national:.1f}%"
    vs_national_class = "text-blue-600" if insights.vs_national >= 0 else "text-red-600"
    vs_national_label = "above average" if insights.vs_national >= 0 else "below average"

    # Durability champion info - now uses evidence-tiered data
    if durability_champ:
        # v3.0: model_year may be 0 when aggregated by core model
        if durability_champ.model_year and durability_champ.model_year > 0:
            durability_name = f"{durability_champ.model} {durability_champ.model_year}"
        else:
            durability_name = durability_champ.model
        durability_score = durability_champ.vs_national_formatted
        # New format includes age band tested at
        durability_context = f" at {durability_champ.age_band}"
        durability_label = "Proven Durability Champion"
    else:
        # Fall back to early performer if no proven champion
        early_performer = insights.get_top_early_performer()
        if early_performer:
            # v3.0: model_year may be 0 when aggregated by core model
            if early_performer.model_year and early_performer.model_year > 0:
                durability_name = f"{early_performer.model} {early_performer.model_year}"
            else:
                durability_name = early_performer.model
            durability_score = early_performer.vs_national_formatted
            durability_context = " (early results)"
            durability_label = "Best Early Performer"
        else:
            durability_name = "N/A"
            durability_score = "N/A"
            durability_context = ""
            durability_label = "Durability Champion"

    # Build display values with None checks
    top_model_name = f"{insights.title_make} {top_model.name}" if top_model else "Insufficient data"
    top_model_rate = f"{top_model.pass_rate:.1f}% pass rate" if top_model else "N/A"

    best_year_name = f"{best_year.model} {best_year.model_year} {best_year.fuel_name}" if best_year else "Insufficient data"
    best_year_rate = f"{best_year.pass_rate:.1f}% pass rate" if best_year else "N/A"

    return f'''      <!-- Key Findings Summary - Featured Card Pattern -->
      <div class="relative bg-white rounded-2xl shadow-xl border border-neutral-100/80 p-6 mb-10">
        <h2 class="text-lg font-semibold text-neutral-900 mb-5 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center shadow-sm">
            <i class="ph ph-lightning text-blue-600 text-xl"></i>
          </div>
          Key Findings
        </h2>
        <div class="grid sm:grid-cols-2 gap-4">
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Most Reliable Model</p>
            <p class="text-lg font-semibold text-neutral-900">{top_model_name}</p>
            <p class="text-sm text-emerald-600 font-medium">{top_model_rate}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">Best Single Year</p>
            <p class="text-lg font-semibold text-neutral-900">{best_year_name}</p>
            <p class="text-sm text-emerald-600 font-medium">{best_year_rate}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-1">{insights.title_make} vs National Average</p>
            <p class="text-lg font-semibold text-neutral-900">{insights.avg_pass_rate:.1f}% vs {insights.national_pass_rate:.1f}%</p>
            <p class="text-sm {vs_national_class} font-medium">{vs_national_text} {vs_national_label}</p>
          </div>
          <div class="bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-xl p-4 border border-amber-200/50 transition-all hover:-translate-y-0.5 hover:shadow-md">
            <p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">{durability_label}</p>
            <p class="text-lg font-semibold text-neutral-900">{durability_name}</p>
            <p class="text-sm text-amber-600 font-medium">{durability_score}{durability_context}</p>
          </div>
        </div>
      </div>'''


def _get_dynamic_intro(insights: ArticleInsights) -> str:
    """
    Generate intro paragraph based on actual data metrics.

    Avoids generic claims like "built its reputation on reliability" which
    don't apply to all manufacturers (e.g., exotic brands, low-volume makes).
    """
    tests_formatted = format_number(insights.total_tests)

    # Low sample size - acknowledge data limitations first
    if insights.total_tests < SAMPLE_SIZE_LOW:
        return f'''<p>
          With <strong>{tests_formatted} MOT tests</strong> in the DVSA database, {insights.title_make} has limited test data compared to mainstream manufacturers. Here's what that data reveals about which models perform best.
        </p>'''

    # Moderate sample size - still note the context
    if insights.total_tests < SAMPLE_SIZE_MODERATE:
        position_text = f"#{insights.rank} out of {insights.rank_total}" if insights.rank else "in the rankings"
        return f'''<p>
          {insights.title_make} ranks <strong>{position_text} manufacturers</strong> with {tests_formatted} MOT tests in our database. We analysed this data to identify which {insights.title_make} models deliver the best reliability.
        </p>'''

    # High volume brands - position based on actual performance
    is_top_performer = insights.rank <= RANK_TOP_PERFORMER and insights.vs_national >= VS_NATIONAL_GOOD
    is_above_average = insights.vs_national >= VS_NATIONAL_AROUND_AVERAGE
    is_around_average = -VS_NATIONAL_AROUND_AVERAGE < insights.vs_national < VS_NATIONAL_AROUND_AVERAGE

    if is_top_performer:
        return f'''<p>
          {insights.title_make} ranks <strong>#{insights.rank} out of {insights.rank_total} manufacturers</strong> for MOT pass rates. We analysed <strong>{tests_formatted} real MOT tests</strong> from the DVSA database to find exactly which {insights.title_make} models deliver the best reliability and which ones fall short.
        </p>'''

    elif is_above_average:
        return f'''<p>
          How reliable are {insights.title_make}s really? We analysed <strong>{tests_formatted} real MOT tests</strong> from the DVSA database to find out which {insights.title_make} models pass most often and which years are worth buying.
        </p>'''

    elif is_around_average:
        return f'''<p>
          {insights.title_make} sits near the middle of UK manufacturer rankings. We analysed <strong>{tests_formatted} real MOT tests</strong> from the DVSA database to identify which {insights.title_make} models outperform the brand average and which to avoid.
        </p>'''

    else:  # below average
        return f'''<p>
          {insights.title_make} ranks #{insights.rank} out of {insights.rank_total} manufacturers, below the national average. We analysed <strong>{tests_formatted} real MOT tests</strong> from the DVSA database to find the most reliable {insights.title_make} models and which years to avoid.
        </p>'''


def generate_intro_section(insights: ArticleInsights) -> str:
    """Generate a data-driven introduction based on actual performance metrics."""
    intro_text = _get_dynamic_intro(insights)

    return f'''      <!-- Introduction -->
      <div class="article-prose text-lg mb-10">
        {intro_text}
        <p>
          This isn't survey data or owner opinions. These are actual pass/fail results from UK garages, covering {insights.title_make} models sold in the UK from {DATA_YEAR_START} to {DATA_YEAR_END}.
        </p>
      </div>'''


def generate_competitors_section(insights: ArticleInsights) -> str:
    """Generate the competitors comparison section."""
    rows = []
    for c in insights.competitors:
        highlight = ' class="bg-blue-50"' if c.is_current else ''
        make_bold = f"<strong>{safe_html(c.make.title())}</strong>"
        rows.append(f'''              <tr{highlight}>
                <td>{make_bold}</td>
                <td><span class="data-badge {get_pass_rate_class(c.pass_rate)}">{c.pass_rate:.1f}%</span></td>
                <td>#{c.rank}</td>
                <td>{format_number(c.total_tests)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Generate verdict
    competitors_above = [c for c in insights.competitors if c.pass_rate > insights.avg_pass_rate and not c.is_current]
    if competitors_above:
        leader = competitors_above[0].make.title()
        verdict = f"{leader} maintains a lead among competitors, while {insights.title_make} sits at #{insights.rank}."
    else:
        verdict = f"{insights.title_make} leads its competitors with a {insights.avg_pass_rate:.1f}% pass rate."

    return f'''      <!-- Section: {insights.title_make} vs Competition -->
      <section id="{insights.make.lower()}-vs-competition" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-trophy"></i>
          </div>
          <h2 class="article-section-title">How {insights.title_make} Compares to Rivals</h2>
        </div>

        <div class="article-prose">
          <p>{insights.title_make} ranks <strong>#{insights.rank} out of {insights.rank_total} manufacturers</strong> with a {insights.avg_pass_rate:.1f}% average MOT pass rate. That's {"above" if insights.vs_national >= 0 else "below"} the national average of {insights.national_pass_rate:.1f}%:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Manufacturer</th>
                <th>Pass Rate</th>
                <th>Rank</th>
                <th>Tests Analysed</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p><strong>The verdict:</strong> {verdict}</p>
        </div>
      </section>'''


def generate_best_models_section(insights: ArticleInsights) -> str:
    """Generate the best models by pass rate section.

    Note: This section shows aggregate pass rates across all years for each model family.
    The 'vs National' column compares against the overall national average ({national_pass_rate}%),
    not year-adjusted averages. For year-adjusted comparisons, see the model breakdown sections.
    """
    rows = []
    for m in insights.top_models[:10]:
        vs = f"+{m.vs_national:.1f}%" if m.vs_national >= 0 else f"{m.vs_national:.1f}%"
        highlight = ' class="bg-emerald-50"' if m.pass_rate >= PASS_RATE_EXCELLENT else ''
        rows.append(f'''              <tr{highlight}>
                <td><strong>{safe_html(m.name)}</strong></td>
                <td><span class="data-badge {m.pass_rate_class}">{m.pass_rate:.1f}%</span></td>
                <td>{vs}</td>
                <td>{format_number(m.total_tests)}</td>
                <td>{m.year_from}-{m.year_to}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Find the surprise/notable insight - only show if genuinely exceptional
    top = insights.top_models[0] if insights.top_models else None
    note = ""
    if top and top.pass_rate >= PASS_RATE_EXCEPTIONAL:
        # Only claim "among most reliable" if truly exceptional (90%+)
        note = f'''
        <div class="callout tip">
          <i class="ph ph-check-circle callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Top performer</p>
            <p class="callout-text">The {top.name} achieves a {top.pass_rate:.1f}% pass rate, {top.pass_rate - insights.national_pass_rate:.0f} percentage points above the national average.</p>
          </div>
        </div>'''
    elif top and top.pass_rate >= PASS_RATE_EXCELLENT and top.vs_national >= VS_NATIONAL_EXCEPTIONAL:
        # Good but not exceptional - more measured claim
        note = f'''
        <div class="callout tip">
          <i class="ph ph-check-circle callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Top performer</p>
            <p class="callout-text">The {top.name} leads {insights.title_make}'s lineup with an {top.pass_rate:.1f}% pass rate.</p>
          </div>
        </div>'''

    return f'''      <!-- Section: Best {insights.title_make} Models -->
      <section id="best-models" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-star"></i>
          </div>
          <h2 class="article-section-title">Best {insights.title_make} Models by MOT Pass Rate</h2>
        </div>

        <div class="article-prose">
          <p>Looking at overall reliability across all years, here's how {insights.title_make}'s core models rank against the {insights.national_pass_rate:.1f}% national average:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Pass Rate</th>
                <th>vs National ({insights.national_pass_rate:.1f}%)</th>
                <th>Tests</th>
                <th>Years</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
          <p class="text-xs text-neutral-500 mt-2">* Compared to overall {insights.national_pass_rate:.1f}% national average across all years. For year-adjusted comparisons that account for newer cars passing more often, see individual model breakdowns below.</p>
        </div>{note}
      </section>'''


def _get_durability_intro_text(insights: ArticleInsights) -> str:
    """
    Generate appropriate intro text for durability section based on actual rating.

    Avoids blanket "proven their durability" claims for brands with mixed/poor results.
    Uses the durability_rating from reliability_summary to determine tone.
    """
    rating = None
    avg_vs_national = None

    if insights.reliability_summary:
        rating = insights.reliability_summary.durability_rating
        avg_vs_national = insights.reliability_summary.proven_avg_vs_national

    # Tier the intro based on actual durability performance
    if rating == "Excellent" or (avg_vs_national and avg_vs_national >= VS_NATIONAL_EXCEPTIONAL):
        return f'''These {insights.title_make} models have <strong>proven exceptional durability</strong> with 11+ years of real-world MOT data. They consistently outperform the national average for cars of the same age:'''

    elif rating == "Good" or (avg_vs_national and avg_vs_national >= VS_NATIONAL_GOOD):
        return f'''These {insights.title_make} models show <strong>solid long-term reliability</strong> based on 11+ years of MOT data. Here's how they compare to the national average for cars of the same age:'''

    elif rating == "Average" or (avg_vs_national and avg_vs_national >= 0):
        return f'''Here's how {insights.title_make} models have performed over 11+ years of real-world MOT testing, compared against the national average for cars of the same age:'''

    elif rating == "Below Average" or (avg_vs_national and avg_vs_national < 0):
        return f'''Long-term MOT data shows mixed results for {insights.title_make} durability. Here's how specific models compare to the national average for cars of the same age:'''

    else:
        # Fallback for unknown/missing rating - neutral factual statement
        return f'''Here's how {insights.title_make} models with 11+ years of MOT history compare to the national average for cars of the same age:'''


def generate_durability_section(insights: ArticleInsights) -> str:
    """
    Generate the durability champions section using evidence-tiered scoring.

    This section highlights models with PROVEN durability (11+ years of data)
    that still perform above average for their age.

    v2.2: Dynamic intro text based on actual durability_rating.
    """
    # Check if we have proven durability data
    if not insights.has_proven_durability_data():
        return ""

    rows = []
    for m in insights.proven_durability_champions[:10]:
        vs_class = "text-emerald-600" if m.vs_national_at_age >= 0 else "text-red-600"
        highlight = ' class="bg-emerald-50"' if m.vs_national_at_age >= VS_NATIONAL_EXCEPTIONAL else ''
        # v2.1: Show context with age-specific national average
        vs_display = f'<span class="{vs_class} font-semibold" title="{m.comparison_context}">{m.vs_national_formatted}</span>'
        # v3.0: Show "-" if model_year is 0 (aggregated data)
        year_display = str(m.model_year) if m.model_year and m.model_year > 0 else "-"

        rows.append(f'''              <tr{highlight}>
                <td><strong>{safe_html(m.model)}</strong></td>
                <td>{year_display}</td>
                <td>{safe_html(m.fuel_name)}</td>
                <td>{vs_display}</td>
                <td class="text-neutral-500 text-sm">{safe_html(m.age_band)}</td>
                <td><span class="data-badge {m.pass_rate_class}">{m.pass_rate:.1f}%</span></td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Find the standout model
    top = insights.get_top_durable_model()
    standout_note = ""
    if top and top.vs_national_at_age >= VS_NATIONAL_EXCEPTIONAL + VS_NATIONAL_GOOD:
        # v3.0: model_year may be 0 when aggregated by core model
        top_name = f"{top.model} {top.model_year}" if top.model_year and top.model_year > 0 else top.model
        standout_note = f'''
        <div class="callout tip">
          <i class="ph ph-trophy callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Proven durability champion</p>
            <p class="callout-text">The {top_name} outperforms the average {top.age_band}-old car by {top.vs_national_at_age:.0f} percentage points, with {format_number(top.total_tests)} MOT tests proving its reliability.</p>
          </div>
        </div>'''

    # Reliability rating badge
    rating_badge = ""
    if insights.reliability_summary:
        rating = insights.reliability_summary.durability_rating
        rating_class = {
            "Excellent": "bg-emerald-100 text-emerald-800",
            "Good": "bg-green-100 text-green-800",
            "Average": "bg-amber-100 text-amber-800",
            "Below Average": "bg-red-100 text-red-800"
        }.get(rating, "bg-neutral-100 text-neutral-800")
        rating_badge = f'''
        <div class="flex items-center gap-2 mb-4">
          <span class="text-sm text-neutral-600">Overall {insights.title_make} Durability Rating:</span>
          <span class="px-3 py-1 rounded-full text-sm font-semibold {rating_class}">{rating}</span>
        </div>'''

    return f'''      <!-- Section: Durability Champions (Proven) -->
      <section id="durability" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-shield-check"></i>
          </div>
          <h2 class="article-section-title">Proven Durability Champions: Which {insights.title_make} Models Age Best?</h2>
        </div>

        <div class="article-prose">
          <p>{_get_durability_intro_text(insights)}</p>
        </div>
{rating_badge}
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <p class="text-sm text-blue-800 flex items-center gap-2">
            <i class="ph ph-seal-check text-blue-600"></i>
            <span><strong>High-confidence data:</strong> Only vehicles with 11+ years of MOT history and {format_number(MIN_TESTS_PROVEN_DURABILITY)}+ tests are included in this ranking.</span>
          </p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Year</th>
                <th>Fuel</th>
                <th>vs Same-Age Average</th>
                <th>Tested At</th>
                <th>Pass Rate</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p><strong>How to read this:</strong> A score of "+15%" means the model passes MOTs 15 percentage points more often than the average car of the same age. These are proven results from vehicles that have genuinely aged well.</p>
        </div>{standout_note}
      </section>'''


def generate_early_performers_section(insights: ArticleInsights) -> str:
    """
    Generate the early performers section (3-6 years, unproven durability).

    IMPORTANT: This section includes a prominent caveat that these vehicles
    have NOT yet proven long-term durability.

    v2.1: Now shows comparison context with weighted age-band averages from database.
    """
    if not insights.early_performers:
        return ""

    rows = []
    for m in insights.early_performers[:8]:
        vs_class = "text-emerald-600" if m.vs_national_at_age >= 0 else "text-red-600"
        # v2.1: Show context with age-specific national average
        vs_display = f'<span class="{vs_class} font-semibold" title="{m.comparison_context}">{m.vs_national_formatted}</span>'
        # v3.0: Show "-" if model_year is 0 (aggregated data)
        year_display = str(m.model_year) if m.model_year and m.model_year > 0 else "-"

        rows.append(f'''              <tr>
                <td><strong>{safe_html(m.model)}</strong></td>
                <td>{year_display}</td>
                <td>{safe_html(m.fuel_name)}</td>
                <td>{vs_display}</td>
                <td class="text-neutral-500 text-sm">{safe_html(m.age_band)}</td>
                <td><span class="data-badge {m.pass_rate_class}">{m.pass_rate:.1f}%</span></td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Get the section caveat
    caveat_text = insights.early_performers_section.get('caveat', 'Durability NOT yet proven')

    return f'''      <!-- Section: Early Performers (Unproven) -->
      <section id="early-performers" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-shooting-star"></i>
          </div>
          <h2 class="article-section-title">Early Performers: Strong Start, Unproven Durability</h2>
        </div>

        <div class="article-prose">
          <p>These newer {insights.title_make} models (3-6 years old) show strong early results, but haven't yet proven long-term durability:</p>
        </div>

        <div class="bg-amber-50 border border-amber-300 rounded-lg p-3 mb-4">
          <p class="text-sm text-amber-800 flex items-center gap-2">
            <i class="ph ph-warning text-amber-600"></i>
            <span><strong>Important caveat:</strong> {caveat_text}. Older versions of the same model may tell a different story at 11+ years.</span>
          </p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Year</th>
                <th>Fuel</th>
                <th>vs Same-Age Average</th>
                <th>Tested At</th>
                <th>Pass Rate</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p><strong>What this means:</strong> These models are performing well in their early years, but we recommend checking the Durability Champions section above to see how older versions of the same model family have fared over time.</p>
        </div>
      </section>'''


def generate_model_breakdowns_section(insights: ArticleInsights) -> str:
    """Generate year-by-year breakdown sections for major models.

    v2.1: Now shows year-adjusted comparisons with context (e.g., 'vs 87.7% avg for 2020').
    """
    sections = []

    # Get top models with enough data
    breakdown_models = insights.get_models_for_breakdown(min_tests=MIN_TESTS_MODEL_BREAKDOWN, limit=5)

    for model in breakdown_models:
        if not model.year_breakdowns:
            continue

        # Sort breakdowns by year descending, then by pass rate
        sorted_breakdowns = sorted(model.year_breakdowns, key=lambda x: (-x.model_year, -x.pass_rate))

        # Build best years (top 10) and worst years (bottom 3)
        best_rows = []
        worst_rows = []

        for i, y in enumerate(sorted_breakdowns[:12]):
            vs = y.vs_national_formatted
            # v2.1: Show context with year-specific national average
            vs_context = f'<span title="{y.comparison_context}">{vs}</span>' if y.national_avg_for_year else vs
            highlight = ' class="bg-emerald-50"' if y.pass_rate >= PASS_RATE_EXCEPTIONAL else ''
            best_rows.append(f'''              <tr{highlight}>
                <td><strong>{y.model_year}</strong></td>
                <td>{y.fuel_name}</td>
                <td><span class="data-badge {y.pass_rate_class}">{y.pass_rate:.1f}%</span></td>
                <td>{vs_context}</td>
                <td>{format_number(y.total_tests)}</td>
              </tr>''')

        # Find worst years for this model
        worst_years = [y for y in sorted_breakdowns if y.pass_rate < AVOID_PASS_RATE_THRESHOLD]
        for y in worst_years[:3]:
            vs = y.vs_national_formatted
            vs_context = f'<span title="{y.comparison_context}">{vs}</span>' if y.national_avg_for_year else vs
            worst_rows.append(f'''              <tr class="bg-red-50">
                <td><strong>{y.model_year}</strong></td>
                <td>{y.fuel_name}</td>
                <td><span class="data-badge {y.pass_rate_class}">{y.pass_rate:.1f}%</span></td>
                <td>{vs_context}</td>
                <td>{format_number(y.total_tests)}</td>
              </tr>''')

        rows_html = "\n".join(best_rows)
        if worst_rows:
            rows_html += f'''
              <tr>
                <td colspan="5" class="text-center text-neutral-500 py-2">...</td>
              </tr>
'''
            rows_html += "\n".join(worst_rows)

        # Generate verdict
        best_year = sorted_breakdowns[0] if sorted_breakdowns else None
        worst_year = worst_years[0] if worst_years else None

        verdict = f"<strong>{safe_html(model.name)} verdict:</strong> "
        if best_year and best_year.pass_rate >= PASS_RATE_EXCEPTIONAL:
            points_above = best_year.pass_rate - insights.national_pass_rate
            verdict += f"The {best_year.model_year} {best_year.fuel_name.lower()} model achieves a {best_year.pass_rate:.1f}% pass rate ({points_above:.0f} points above average). "
        if worst_year:
            verdict += f"Avoid the {worst_year.model_year} {worst_year.fuel_name.lower()} ({worst_year.pass_rate:.1f}%)."

        # Add warning callout if there are bad years
        warning = ""
        if worst_years:
            worst_example = worst_years[0]

            # Generate specific title based on how many bad years exist
            bad_year_list = [y.model_year for y in worst_years]
            if len(worst_years) == 1:
                # Single bad year - be specific
                warning_title = f"Avoid the {worst_example.model_year} {model.name}"
            elif len(worst_years) == 2:
                # Two bad years - list them
                warning_title = f"Avoid {bad_year_list[0]} and {bad_year_list[1]} {model.name}s"
            else:
                # Check if years are consecutive (pattern)
                sorted_years = sorted(bad_year_list)
                is_consecutive = all(sorted_years[i+1] - sorted_years[i] <= 2 for i in range(len(sorted_years)-1))
                if is_consecutive:
                    warning_title = f"Avoid {sorted_years[0]}-{sorted_years[-1]} {model.name}s"
                else:
                    warning_title = f"Avoid early {model.name} models"

            # Generate accurate callout text based on actual pass rate
            if worst_example.pass_rate < 50:
                callout_desc = f"has a {worst_example.pass_rate:.1f}% pass rate, failing MOTs more often than passing"
            else:
                callout_desc = f"has a {worst_example.pass_rate:.1f}% pass rate, well below the national average"

            warning = f'''

        <div class="callout warning">
          <i class="ph ph-warning callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">{warning_title}</p>
            <p class="callout-text">The {worst_example.model_year} {worst_example.fuel_name.lower()} {model.name} {callout_desc}.</p>
          </div>
        </div>'''

        icon = "ph-car"
        if "SUV" in model.name.upper() or "CR-V" in model.name.upper() or "HR-V" in model.name.upper():
            icon = "ph-jeep"

        sections.append(f'''      <!-- Section: {insights.title_make} {model.name} -->
      <section id="{slugify(model.name)}" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph {icon}"></i>
          </div>
          <h2 class="article-section-title">{insights.title_make} {model.name}: Year-by-Year Breakdown</h2>
        </div>

        <div class="article-prose">
          <p>The {model.name} has <strong>{format_number(model.total_tests)} tests</strong> in our database with an overall {model.pass_rate:.1f}% pass rate:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Year</th>
                <th>Fuel</th>
                <th>Pass Rate</th>
                <th>vs Same-Year Avg</th>
                <th>Tests</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p>{verdict}</p>
        </div>{warning}
      </section>''')

    return "\n\n".join(sections)


def _get_fuel_intro_text(insights: ArticleInsights) -> str:
    """Generate appropriate intro text for fuel analysis based on available data."""
    fuel_count = len(insights.fuel_analysis)

    if fuel_count <= 1:
        fuel_name = insights.fuel_analysis[0].fuel_name if insights.fuel_analysis else "vehicles"
        return f"Here's how {insights.title_make} {fuel_name.lower()} models perform:"

    # Check if there are meaningful differences
    if fuel_count >= 2:
        rates = [f.pass_rate for f in insights.fuel_analysis]
        max_diff = max(rates) - min(rates)
        if max_diff >= 5:
            return f"Reliability varies by fuel type for {insights.title_make}. Here's how each performs:"
        else:
            return f"Here's how {insights.title_make}'s fuel types compare:"

    return f"Here's the breakdown by fuel type for {insights.title_make}:"


def generate_fuel_analysis_section(insights: ArticleInsights) -> str:
    """Generate the fuel type analysis section."""
    if not insights.fuel_analysis:
        return ""

    rows = []
    for f in insights.fuel_analysis:
        vs = f.pass_rate - insights.national_pass_rate
        vs_str = f"+{vs:.1f}%" if vs >= 0 else f"{vs:.1f}%"
        highlight = ' class="bg-emerald-50"' if f.pass_rate >= PASS_RATE_EXCELLENT else ''
        rows.append(f'''              <tr{highlight}>
                <td><strong>{f.fuel_name}</strong></td>
                <td><span class="data-badge {f.pass_rate_class}">{f.pass_rate:.1f}%</span></td>
                <td>{vs_str}</td>
                <td>{format_number(f.total_tests)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Calculate hybrid advantage if available
    hybrid_comp = insights.get_hybrid_comparison()
    verdict = ""
    if 'HY' in hybrid_comp and 'PE' in hybrid_comp:
        hy = hybrid_comp['HY']
        pe = hybrid_comp['PE']
        di = hybrid_comp.get('DI')
        diff_pe = hy.pass_rate - pe.pass_rate
        verdict = f"<strong>The hybrid advantage:</strong> {insights.title_make} hybrids pass MOTs {diff_pe:.0f}% more often than petrols"
        if di:
            diff_di = hy.pass_rate - di.pass_rate
            verdict += f" and {diff_di:.0f}% more often than diesels"
        verdict += "."

    return f'''      <!-- Section: Hybrids vs Petrol vs Diesel -->
      <section id="fuel-types" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-leaf"></i>
          </div>
          <h2 class="article-section-title">{insights.title_make} Hybrids vs Petrol vs Diesel</h2>
        </div>

        <div class="article-prose">
          <p>{_get_fuel_intro_text(insights)}</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Fuel Type</th>
                <th>Average Pass Rate</th>
                <th>vs National</th>
                <th>Tests</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p>{verdict}</p>
        </div>
      </section>'''


def _get_avoid_severity_text(insights: ArticleInsights) -> str:
    """Generate severity text based on actual worst model pass rates."""
    if not insights.worst_models:
        return ""

    worst = insights.worst_models[0]
    if worst.pass_rate < 50:
        return " These vehicles fail MOTs more often than they pass."
    elif worst.pass_rate < 60:
        return " These models have significantly higher failure rates than average."
    else:
        return " These are the weakest performers in the lineup."


def generate_avoid_section(insights: ArticleInsights) -> str:
    """Generate the models to avoid section.

    Fixes Issue 6: Only shows genuinely poor performers, not just
    models that are slightly below average.
    """
    if not insights.worst_models:
        return ""

    # Filter to only genuinely poor performers
    # Pass rate < 60% OR vs_national < -10%
    filtered_worst = [
        m for m in insights.worst_models
        if m.pass_rate < AVOID_PASS_RATE_THRESHOLD or m.vs_national < AVOID_VS_NATIONAL_THRESHOLD
    ]

    # If no models meet the threshold, don't show the section
    if not filtered_worst:
        return ""

    rows = []
    for m in filtered_worst[:10]:
        rows.append(f'''              <tr class="bg-red-50">
                <td><strong>{safe_html(m.model)}</strong></td>
                <td>{m.model_year}</td>
                <td>{safe_html(m.fuel_name)}</td>
                <td><span class="data-badge {m.pass_rate_class}">{m.pass_rate:.1f}%</span></td>
                <td>{format_number(m.total_tests)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Identify patterns in worst models
    patterns = {}
    for m in filtered_worst[:10]:
        key = m.model
        if key not in patterns:
            patterns[key] = []
        patterns[key].append(m)

    pattern_notes = []
    for model, entries in patterns.items():
        if len(entries) >= 2:
            years = sorted([e.model_year for e in entries])
            fuels = set([e.fuel_name.lower() for e in entries])
            fuel_text = "/".join(fuels) if len(fuels) <= 2 else ""
            pattern_notes.append(f"{years[0]}-{years[-1]} {fuel_text} {model}s")

    pattern_text = ""
    if pattern_notes:
        pattern_text = f"Early {', '.join(pattern_notes[:3])} are the models that drag down {insights.title_make}'s average."

    # Add proven durability context if worst ager is significantly below average
    worst_ager = insights.get_worst_ager()
    age_context = ""
    if worst_ager and worst_ager.vs_national_at_age <= -8:
        # v3.0: model_year may be 0 when aggregated by core model
        worst_ager_name = f"{worst_ager.model} {worst_ager.model_year}" if worst_ager.model_year and worst_ager.model_year > 0 else worst_ager.model
        age_context = f" The {worst_ager_name} performs {abs(worst_ager.vs_national_at_age):.0f}% worse than the average car of the same age at {worst_ager.age_band} - this is proven poor durability."

    return f'''      <!-- Section: Models to Avoid -->
      <section id="avoid" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-warning-octagon"></i>
          </div>
          <h2 class="article-section-title">{insights.title_make} Models to Avoid</h2>
        </div>

        <div class="article-prose">
          <p>Not all {insights.title_make}s are reliable. These specific model/year combinations have failure rates well above average:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Year</th>
                <th>Fuel</th>
                <th>Pass Rate</th>
                <th>Tests</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="callout warning">
          <i class="ph ph-warning callout-icon"></i>
          <div class="callout-content">
            <p class="callout-title">Pattern to avoid</p>
            <p class="callout-text">{pattern_text}{age_context}{_get_avoid_severity_text(insights)}</p>
          </div>
        </div>
      </section>'''


def generate_failures_section(insights: ArticleInsights) -> str:
    """Generate the common failures section."""
    if not insights.failure_categories:
        return ""

    rows = []
    for i, cat in enumerate(insights.failure_categories[:7], 1):
        rows.append(f'''              <tr>
                <td><strong>{i}. {safe_html(cat.name)}</strong></td>
                <td>{format_number(cat.total_failures)}</td>
              </tr>''')

    rows_html = "\n".join(rows)

    # Generate pre-MOT checklist based on top failures
    checklist_items = []
    for cat in insights.failure_categories[:5]:
        name = cat.name.lower()
        if 'lamp' in name or 'light' in name or 'electrical' in name:
            checklist_items.append("Check all bulbs (number plate lights are commonly missed)")
        elif 'suspension' in name:
            checklist_items.append("Inspect suspension bushes and anti-roll bar links")
        elif 'brake' in name:
            checklist_items.append("Check brake pad thickness and disc condition")
        elif 'tyre' in name:
            checklist_items.append("Ensure tyres meet 1.6mm tread requirement")
        elif 'visibility' in name or 'wiper' in name:
            checklist_items.append("Clean windscreen and check wiper blade condition")
        elif 'emission' in name or 'exhaust' in name:
            checklist_items.append("Check exhaust system for leaks and emissions")

    checklist_html = "\n".join([f"            <li>{item}</li>" for item in checklist_items[:5]])

    return f'''      <!-- Section: Common Failures -->
      <section id="failures" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon">
            <i class="ph ph-wrench"></i>
          </div>
          <h2 class="article-section-title">What Goes Wrong on {insights.title_make}s?</h2>
        </div>

        <div class="article-prose">
          <p>When {insights.title_make}s fail MOTs, these are the most common causes:</p>
        </div>

        <div class="article-table-wrapper">
          <table class="article-table">
            <thead>
              <tr>
                <th>Failure Category</th>
                <th>Total Failures</th>
              </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>

        <div class="article-prose mt-4">
          <p><strong>Pre-MOT checklist for {insights.title_make} owners:</strong></p>
          <ul>
{checklist_html}
          </ul>
        </div>
      </section>'''


def generate_faqs_section(insights: ArticleInsights) -> str:
    """Generate the FAQs section."""
    faqs = generate_faq_data(insights)

    # Add extra FAQs about specific popular models
    popular_models = insights.get_models_for_breakdown(min_tests=MIN_TESTS_FAQ_POPULAR, limit=3)
    for model in popular_models:
        best_years = [y for y in model.year_breakdowns if y.pass_rate >= PASS_RATE_EXCEPTIONAL]

        # Check overall model performance against national average
        model_above_average = model.pass_rate >= insights.national_pass_rate

        if best_years and model_above_average:
            # Model is genuinely reliable - can say "Yes"
            best = sorted(best_years, key=lambda x: -x.pass_rate)[0]
            answer = f"Yes. The {model.name} averages {model.pass_rate:.1f}% overall, above the {insights.national_pass_rate:.1f}% national average. The {best.model_year} model achieves {best.pass_rate:.1f}% pass rates."
            if model.pass_rate >= 75:
                answer += f" {model.name} models from {model.year_from}-{model.year_to} have consistently strong results."
            faqs.append({
                "question": f"Is the {insights.title_make} {model.name} reliable?",
                "answer": answer
            })
        elif best_years:
            # Has good years but overall average is below national - be balanced
            best = sorted(best_years, key=lambda x: -x.pass_rate)[0]
            answer = f"It depends on the year. While the {best.model_year} {model.name} achieves {best.pass_rate:.1f}% pass rates, the model overall averages {model.pass_rate:.1f}% (vs {insights.national_pass_rate:.1f}% national average). Choose newer model years for better reliability."
            faqs.append({
                "question": f"Is the {insights.title_make} {model.name} reliable?",
                "answer": answer
            })
        elif model_above_average:
            # No standout years but overall above average
            answer = f"The {model.name} averages {model.pass_rate:.1f}% pass rate, {'slightly ' if model.pass_rate - insights.national_pass_rate < 3 else ''}above the {insights.national_pass_rate:.1f}% national average."
            faqs.append({
                "question": f"Is the {insights.title_make} {model.name} reliable?",
                "answer": answer
            })

    faq_items = []
    for faq in faqs[:6]:  # Limit to 6 FAQs
        faq_items.append(f'''          <div class="faq-item">
            <button class="faq-question">
              {faq['question']}
              <i class="ph ph-caret-down"></i>
            </button>
            <div class="faq-answer">
              {faq['answer']}
            </div>
          </div>''')

    faq_html = "\n\n".join(faq_items)

    return f'''      <!-- FAQs Section - Enhanced header -->
      <section id="faqs" class="mt-10">
        <h3 class="text-lg font-semibold text-neutral-900 mb-5 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center shadow-sm">
            <i class="ph ph-question text-blue-600 text-xl"></i>
          </div>
          Frequently Asked Questions
        </h3>

        <div class="space-y-3">
{faq_html}
        </div>
      </section>'''


def generate_recommendations_section(insights: ArticleInsights) -> str:
    """Generate the buying recommendations section with evidence-tiered advice."""

    # === Best Nearly New (2019-2023) - using raw pass rates ===
    # Note: These are early performers, caveat included in text
    # Threshold aligned with PASS_RATE_EXCELLENT (85%)
    nearly_new_items = []
    seen_models = set()
    for m in insights.get_best_nearly_new(max_age=5, limit=10):
        if m.model not in seen_models and m.pass_rate >= PASS_RATE_EXCELLENT:
            seen_models.add(m.model)
            nearly_new_items.append(f'''            <li class="flex items-start gap-2">
              <i class="ph ph-check-circle text-emerald-600 mt-1"></i>
              <span><strong>{safe_html(m.model)} {m.model_year} {safe_html(m.fuel_name)}:</strong> {m.pass_rate:.0f}% pass rate</span>
            </li>''')

    # === Best Used (PROVEN Durability) - using new evidence-tiered data ===
    used_items = []
    seen_models = set()
    # Use proven durability champions (11+ years data)
    for m in insights.proven_durability_champions[:10]:
        if m.model not in seen_models and m.vs_national_at_age > VS_NATIONAL_GOOD:
            seen_models.add(m.model)
            # Find year range for this model in durability list
            similar = [x for x in insights.proven_durability_champions if x.model == m.model]
            if similar:
                years = sorted([x.model_year for x in similar if x.model_year and x.model_year > 0])
                if years:
                    year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
                else:
                    year_range = f"({similar[0].age_band})"
                avg_score = sum(x.vs_national_at_age for x in similar) / len(similar)
                used_items.append(f'''            <li class="flex items-start gap-2">
              <i class="ph ph-shield-check text-amber-600 mt-1"></i>
              <span><strong>{safe_html(m.model)} {year_range}:</strong> {avg_score:+.0f}% vs same-age (proven at 11+ years)</span>
            </li>''')

    # === Models to Avoid - using PROVEN poor durability data ===
    worst_items = []
    seen_models = set()
    for m in insights.proven_models_to_avoid[:8]:
        if m.model not in seen_models and m.vs_national_at_age < -VS_NATIONAL_GOOD:
            seen_models.add(m.model)
            # Find year range for this model
            similar = [x for x in insights.proven_models_to_avoid if x.model == m.model]
            if similar:
                years = sorted([x.model_year for x in similar if x.model_year and x.model_year > 0])
                if years:
                    year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
                else:
                    year_range = f"({similar[0].age_band})"
                avg_score = sum(x.vs_national_at_age for x in similar) / len(similar)
                # Include concern text if available
                concern_text = ""
                if m.concern:
                    concern_text = f' <span class="text-red-500 text-xs">({safe_html(m.concern)})</span>'
                worst_items.append(f'''            <li class="flex items-start gap-2">
              <i class="ph ph-x-circle text-red-600 mt-1"></i>
              <span><strong>{safe_html(m.model)} {year_range}:</strong> {avg_score:.0f}% vs same-age (proven poor at 11+ years){concern_text}</span>
            </li>''')

    nearly_new_html = "\n".join(nearly_new_items[:4]) if nearly_new_items else '''            <li class="text-neutral-500">Limited data for recent models</li>'''
    used_html = "\n".join(used_items[:4]) if used_items else '''            <li class="text-neutral-500">Limited proven durability data available</li>'''
    worst_html = "\n".join(worst_items[:4]) if worst_items else '''            <li class="text-neutral-500">No major proven reliability concerns</li>'''

    return f'''      <!-- Buying Recommendations - Enhanced with mw-info-card pattern -->
      <section id="recommendations" class="mt-10">
        <h3 class="text-lg font-semibold text-neutral-900 mb-5 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center shadow-sm">
            <i class="ph ph-thumbs-up text-blue-600 text-xl"></i>
          </div>
          Our Buying Recommendations
        </h3>

        <div class="grid md:grid-cols-2 gap-4 mb-4">
          <div class="bg-gradient-to-br from-emerald-50 to-emerald-100/30 rounded-xl p-5 border border-emerald-100/80 transition-all hover:-translate-y-0.5 hover:shadow-lg">
            <h4 class="font-semibold text-emerald-900 mb-1">Best If Buying Nearly New</h4>
            <p class="text-sm text-emerald-700 mb-3">{DATA_YEAR_END - 4}-{DATA_YEAR_END} models with highest early pass rates</p>
            <ul class="space-y-2 text-emerald-800">
{nearly_new_html}
            </ul>
            <p class="text-xs text-emerald-600 mt-3 italic">Note: Long-term durability not yet proven for these newer models</p>
          </div>

          <div class="bg-gradient-to-br from-amber-50 to-amber-100/30 rounded-xl p-5 border border-amber-100/80 transition-all hover:-translate-y-0.5 hover:shadow-lg">
            <h4 class="font-semibold text-amber-900 mb-1">Best If Buying Used (Proven)</h4>
            <p class="text-sm text-amber-700 mb-3">11+ years of proven durability data</p>
            <ul class="space-y-2 text-amber-800">
{used_html}
            </ul>
          </div>
        </div>

        <div class="bg-gradient-to-br from-red-50 to-red-100/30 rounded-xl p-5 border border-red-100/80 transition-all hover:-translate-y-0.5 hover:shadow-lg">
          <h4 class="font-semibold text-red-900 mb-3">{insights.title_make} Models to Avoid (Proven Poor)</h4>
          <p class="text-sm text-red-700 mb-3">Proven below average at 11+ years - not just old, genuinely problematic</p>
          <ul class="space-y-2 text-red-800">
{worst_html}
          </ul>
        </div>
      </section>'''


def generate_methodology_section(insights: ArticleInsights) -> str:
    """Generate the methodology section (v2.1: year-adjusted scoring)."""
    return f'''      <!-- Methodology - Enhanced styling -->
      <section id="methodology" class="mt-10 bg-white rounded-2xl shadow-lg border border-neutral-100/80 p-6">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200/50 flex items-center justify-center shadow-sm">
            <i class="ph ph-info text-slate-600 text-xl"></i>
          </div>
          About This Data
        </h3>
        <div class="text-sm text-neutral-600 space-y-3 leading-relaxed">
          <p>This analysis uses real MOT test results from the DVSA database, covering {format_number(insights.total_tests)} tests on {insights.title_make} vehicles between {DATA_YEAR_START} and {DATA_YEAR_END}.</p>
          <p><strong class="text-neutral-800">Year-Adjusted Scoring (v2.1):</strong> In year-by-year breakdowns, each vehicle is compared against the national average for vehicles of the <em>same model year</em>. This removes the natural bias where newer cars pass more often, allowing fair comparisons across eras.</p>
          <p><strong class="text-neutral-800">Evidence-Tiered Durability:</strong> We separate "proven durability" (vehicles tested at 11+ years old) from "early performers" (3-6 years old). Only vehicles with proven long-term data are used for durability claims. Age-band comparisons use weighted national averages.</p>
          <p>Minimum thresholds: {format_number(MIN_TESTS_PROVEN_DURABILITY)} tests for proven durability rankings, {format_number(MIN_TESTS_EARLY_PERFORMER)} tests for early performer rankings. Pass rates are calculated as first-time passes, excluding retests.</p>
          <p>The overall national average MOT pass rate is {insights.national_pass_rate:.2f}% based on {format_number(METHODOLOGY_TOTAL_TESTS)} tests across all manufacturers. Year-specific averages range {METHODOLOGY_YEAR_RANGE_EXAMPLE}.</p>
        </div>
      </section>'''


def generate_cta_section(insights: ArticleInsights) -> str:
    """Generate the bottom CTA section."""
    return f'''      <!-- Bottom CTA - Enhanced styling -->
      <div class="article-cta">
        <div class="article-cta-icon">
          <i class="ph ph-magnifying-glass"></i>
        </div>
        <h3 class="article-cta-title">Check Any Vehicle's MOT History</h3>
        <p class="article-cta-text">
          Get the full MOT history, mileage records, and reliability insights for any UK vehicle. Make an informed decision before you buy.
        </p>
        <a href="/" class="article-cta-btn group">
          Run a Free Check
          <i class="ph ph-arrow-right transition-transform group-hover:translate-x-1"></i>
        </a>
      </div>'''
