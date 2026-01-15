# HTML Structure Reference: Current vs Target

Quick reference for remaining structural changes.

---

## Page Header

### Current (Hero Card)
```html
<div class="relative overflow-hidden rounded-2xl bg-white mb-6">
  <div class="relative z-10 px-6 py-8 text-center">
    <div class="inline-flex items-center px-3 py-1.5 text-xs...">MOT Report</div>
    <h1>BMW 3 SERIES</h1>
    <p>Comprehensive MOT reliability analysis...</p>
  </div>
</div>
```

### Target (Article Header)
```html
<header class="mb-8">
  <div class="flex flex-wrap items-center gap-3 mb-4">
    <span class="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-full border bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-600 border-blue-200/50">
      <i class="ph ph-chart-bar"></i>
      MOT Reliability Data
    </span>
    <span class="text-sm text-neutral-500">{variant_count} variants analysed</span>
    <span class="text-sm text-neutral-500">Updated {date}</span>
  </div>
  <h1 class="text-2xl sm:text-3xl font-semibold text-neutral-900 mb-3">
    {make} {model} MOT Reliability Report
  </h1>
  <p class="text-lg text-neutral-600 leading-relaxed">
    Complete MOT reliability analysis based on {total_tests} real test results.
  </p>
</header>
```

---

## Data Source Callout (NEW)

```html
<div class="flex items-center gap-4 p-4 bg-gradient-to-br from-emerald-50 to-emerald-100/50 border border-emerald-200/50 rounded-xl mb-8">
  <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
    <i class="ph ph-database text-emerald-600 text-xl"></i>
  </div>
  <div>
    <p class="text-base font-semibold text-emerald-700">{total_tests} MOT tests analysed</p>
    <p class="text-sm text-emerald-600">Real DVSA data covering {year_range}</p>
  </div>
</div>
```

---

## Two-Column Layout (NEW)

```html
<div class="article-layout">
  <aside class="article-sidebar">
    <nav class="article-toc" aria-label="Table of contents">
      <button class="article-toc-toggle" aria-expanded="false">
        <div class="article-toc-toggle-content">
          <i class="ph ph-list article-toc-toggle-icon"></i>
          <span class="article-toc-toggle-label">Contents</span>
          <span class="article-toc-count">{count}</span>
        </div>
        <i class="ph ph-caret-down article-toc-caret"></i>
      </button>
      <div class="article-toc-content">
        <div class="article-toc-header">
          <i class="ph ph-list article-toc-header-icon"></i>
          <span class="article-toc-header-text">Contents</span>
        </div>
        <ul class="article-toc-list">
          <li class="article-toc-item">
            <a href="#section-id" class="toc-link">
              <span class="toc-link-number">1.</span>
              <span class="toc-link-text">Section Title</span>
            </a>
          </li>
        </ul>
      </div>
    </nav>
  </aside>

  <div class="article-main">
    <!-- sections here -->
  </div>
</div>
```

---

## Section Card

### Current
```html
<div class="bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6">
  <div class="px-5 py-4 border-b border-neutral-100 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100/50">
        <i class="ph ph-chart-line text-xl text-blue-600"></i>
      </div>
      <h3 class="text-lg font-semibold text-neutral-900">Section Title</h3>
    </div>
  </div>
  <div class="p-5">
    <!-- content -->
  </div>
</div>
```

### Target
```html
<div class="scroll-reveal" data-reveal-index="1">
  <section id="section-id" class="article-section">
    <div class="article-section-header">
      <div class="article-section-icon">
        <i class="ph ph-chart-line"></i>
      </div>
      <h2 class="article-section-title">Section Title</h2>
    </div>
    <!-- content -->
  </section>
</div>
```

---

## Table

### Current
```html
<div class="mw-table-wrapper overflow-hidden">
  <table class="w-full text-sm">
    <thead>
      <tr>
        <th class="py-3 px-4 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wide bg-neutral-50 border-b border-neutral-200">Header</th>
      </tr>
    </thead>
    <tbody>
      <tr class="hover:bg-neutral-50 transition-colors duration-150">
        <td class="py-3 px-4 border-b border-neutral-100 text-neutral-600">Cell</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Target
```html
<div class="article-table-wrapper">
  <table class="article-table">
    <thead>
      <tr><th>Header</th></tr>
    </thead>
    <tbody>
      <tr><td>Cell</td></tr>
      <tr class="bg-emerald-50"><td><strong>Highlighted</strong></td></tr>
    </tbody>
  </table>
</div>
```

---

## Callout Box (NEW)

```html
<div class="callout tip">
  <i class="ph ph-check-circle callout-icon"></i>
  <div class="callout-content">
    <p class="callout-title">Title</p>
    <p class="callout-text">Description text</p>
  </div>
</div>
```

Types: `tip` (green), `warning` (amber), `info` (blue), `danger` (red)

---

## CSS Class Quick Reference

| Current | Target |
|---------|--------|
| `bg-white rounded-2xl shadow-xl...` | `.article-section` |
| `mw-table-wrapper` | `.article-table-wrapper` |
| `w-full text-sm` (table) | `.article-table` |
| `mw-cta-section` | `.article-cta` ✅ Done |
| Inline badge styles | `.data-badge .pass-rate-*` ✅ Done |
| N/A | `.article-prose` |
| N/A | `.callout .tip/.warning` |
| N/A | `.scroll-reveal` |
