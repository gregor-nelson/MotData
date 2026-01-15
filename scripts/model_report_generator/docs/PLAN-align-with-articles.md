# Model Report Generator: Articles Pattern Alignment

## Status: Complete

### All Items Completed
- [x] Stylesheet switched to `/articles/styles/articles.css`
- [x] Scripts switched to `articles-loader.js` + `article-common.js`
- [x] Footer changed to dynamic `<div id="mw-footer"></div>`
- [x] Reading progress bar added (element + CSS)
- [x] Body class updated to `bg-white md:bg-neutral-50 min-h-screen`
- [x] CTA section uses `.article-cta` pattern
- [x] Container width updated to `max-w-6xl`
- [x] Data badge CSS classes added (`.pass-rate-excellent`, etc.)
- [x] Add visible breadcrumb navigation after header
- [x] Replace hero section with article header pattern
- [x] Add data source callout (green box with test count)
- [x] Add key findings summary card (4-stat grid)
- [x] Implement two-column layout with TOC sidebar
- [x] Wrap sections in `.article-section` with scroll-reveal
- [x] Convert tables to `.article-table-wrapper` + `.article-table`
- [x] Add callout boxes where appropriate (warning callout for year variance)

---

## Reference Files

**Copy patterns from:**
```
C:\Users\gregor\Downloads\Dev\motorwise.io\frontend\public\articles\content\reliability\aston-martin-most-reliable-models.html
```

**CSS reference:**
```
C:\Users\gregor\Downloads\Dev\motorwise.io\frontend\public\articles\styles\articles.css
```

**Files to modify:**
```
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\html_templates.py
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\generate_model_report.py
C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator\tailwind_classes.py
```

---

## Key Structure Changes

### Current → Target

| Element | Current | Target |
|---------|---------|--------|
| Page header | Hero card with badge | `<header>` with category badge, h1, description |
| Layout | Single column | Two-column: TOC sidebar + main content |
| Sections | `tw.CARD` classes | `<section class="article-section">` |
| Tables | Inline Tailwind | `.article-table-wrapper` + `.article-table` |
| Animations | `.mw-fade-in` | `.scroll-reveal` with `data-reveal-index` |

### Target Document Structure

```html
<body>
  <div id="reading-progress"></div>
  <div id="mw-header"></div>

  <main class="max-w-6xl mx-auto px-4 py-6 sm:py-8 lg:py-12">
    <nav aria-label="Breadcrumb">...</nav>

    <article>
      <header><!-- Title, badge, description --></header>

      <!-- Data source callout (green) -->
      <!-- Key findings card (4-stat grid) -->

      <div class="article-layout">
        <aside class="article-sidebar">
          <nav class="article-toc">...</nav>
        </aside>

        <div class="article-main">
          <div class="scroll-reveal" data-reveal-index="1">
            <section id="section-id" class="article-section">
              <div class="article-section-header">...</div>
              <!-- content -->
            </section>
          </div>
          <!-- more sections -->

          <div class="article-cta">...</div>
        </div>
      </div>
    </article>
  </main>

  <div id="mw-footer"></div>
  <script src="/articles/js/articles-loader.js"></script>
  <script src="/articles/js/article-common.js"></script>
</body>
```

---

## Section Mapping for TOC

```python
REPORT_SECTIONS = [
    {'id': 'overview', 'title': 'Pass Rate Overview', 'icon': 'chart-pie'},
    {'id': 'rankings', 'title': 'Rankings', 'icon': 'trophy'},
    {'id': 'best-worst', 'title': 'Best & Worst Years', 'icon': 'thumbs-up'},
    {'id': 'age-impact', 'title': 'Age Impact', 'icon': 'clock'},
    {'id': 'fuel-mileage', 'title': 'Fuel & Mileage', 'icon': 'gas-pump'},
    {'id': 'seasonal', 'title': 'Seasonal Patterns', 'icon': 'calendar'},
    {'id': 'geographic', 'title': 'Geographic Variation', 'icon': 'map-pin'},
    {'id': 'failures', 'title': 'Common Failures', 'icon': 'wrench'},
    {'id': 'all-variants', 'title': 'All Variants', 'icon': 'list'},
    {'id': 'methodology', 'title': 'Methodology', 'icon': 'info'},
]
```

---

## Test Command

```bash
cd C:\Users\gregor\Downloads\Mot Data\scripts\model_report_generator
python generate_model_report.py BMW "3 SERIES"
```

Output: `C:\Users\gregor\Downloads\Mot Data\articles\model-reports\bmw-3-series-report.html`
