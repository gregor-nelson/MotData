# Mobile Responsiveness Plan: Model Report Generator

## Objective
Fix mobile responsiveness issues in the model report generator using Tailwind utility classes only (no custom CSS).

## Files to Modify
1. `scripts/model_report_generator/tailwind_classes.py` - Update class constants
2. `scripts/model_report_generator/generate_model_report.py` - Update inline Tailwind classes

---

## Changes Summary

### HIGH PRIORITY

#### 1. Fix Chart Overflow (Missing overflow-x-auto)
**File:** `tailwind_classes.py`

| Constant | Current | New |
|----------|---------|-----|
| `MONTHLY_CHART` | `flex items-end gap-1 h-36 py-4` | `flex items-end gap-1 h-36 py-4 overflow-x-auto` |
| `AGE_CHART` | `flex items-end gap-2 h-44 py-4` | `flex items-end gap-2 h-44 py-4 overflow-x-auto` |

#### 2. Fix Horizontal Bar Layout (Failure Categories)
**File:** `tailwind_classes.py`

| Constant | Current | New |
|----------|---------|-----|
| `BAR_ROW` | `flex items-center mb-3` | `flex flex-col sm:flex-row sm:items-center mb-3 gap-1 sm:gap-0` |
| `BAR_LABEL` | `w-48 text-sm text-neutral-700 flex-shrink-0 truncate` | `text-sm text-neutral-700 sm:w-48 sm:flex-shrink-0 sm:truncate` |

**Result:** On mobile, label stacks above bar. On sm+, reverts to side-by-side layout.

---

### MEDIUM PRIORITY

#### 3. Fix Rankings Section Layout
**File:** `tailwind_classes.py`

| Constant | Current | New |
|----------|---------|-----|
| `RANKING_BADGES` | `flex gap-4 flex-wrap` | `grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4` |
| `RANKING_BADGE` | `flex-1 min-w-[120px] text-center p-4 bg-neutral-50 rounded-xl` | `text-center p-4 bg-neutral-50 rounded-xl` |

**File:** `generate_model_report.py` (line ~769)
- Update inline class in `generate_rankings_content()` to use the constants or update inline to match

#### 4. Fix Overview Stats Hero Section
**File:** `tailwind_classes.py`

| Constant | Current | New |
|----------|---------|-----|
| `HERO_DETAILS` | `flex-1 min-w-[250px]` | `flex-1 min-w-0 sm:min-w-[200px]` |

**File:** `generate_model_report.py` (line ~724)
- Update the inline `min-w-[250px]` to `min-w-0 sm:min-w-[200px]`

---

### LOW PRIORITY (Polish)

#### 5. Tighten Chart Bar Spacing on Mobile
**File:** `tailwind_classes.py`

| Constant | Current | New |
|----------|---------|-----|
| `YEAR_BAR_COL` | `flex flex-col items-center min-w-[40px]` | `flex flex-col items-center min-w-[28px] sm:min-w-[40px]` |
| `MONTHLY_BAR_COL` | `flex-1 flex flex-col items-center min-w-[30px]` | `flex-1 flex flex-col items-center min-w-[24px] sm:min-w-[30px]` |
| `AGE_BAR_COL` | `flex-1 flex flex-col items-center min-w-[50px]` | `flex-1 flex flex-col items-center min-w-[40px] sm:min-w-[50px]` |

#### 6. Stats Grid Mobile Gap
**File:** `generate_model_report.py` (line ~726)

| Current | New |
|---------|-----|
| `grid grid-cols-2 gap-4` | `grid grid-cols-2 gap-3 sm:gap-4` |

Reduce gap on mobile for tighter fit. Keep 2 cols as content is small enough.

---

## Implementation Order

1. **tailwind_classes.py** - Update all constants (single file, bulk changes)
2. **generate_model_report.py** - Update inline classes that reference changed patterns

---

## Exact Code Changes

### tailwind_classes.py

```python
# Line 142 - Add overflow-x-auto
MONTHLY_CHART = "flex items-end gap-1 h-36 py-4 overflow-x-auto"

# Line 149 - Add overflow-x-auto
AGE_CHART = "flex items-end gap-2 h-44 py-4 overflow-x-auto"

# Line 159 - Stack on mobile
BAR_ROW = "flex flex-col sm:flex-row sm:items-center mb-3 gap-1 sm:gap-0"

# Line 160 - Remove fixed width on mobile
BAR_LABEL = "text-sm text-neutral-700 sm:w-48 sm:flex-shrink-0 sm:truncate"

# Line 126 - Grid instead of flex
RANKING_BADGES = "grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4"

# Line 127 - Remove flex-1 and min-w
RANKING_BADGE = "text-center p-4 bg-neutral-50 rounded-xl"

# Line 116 - Remove min-w on mobile
HERO_DETAILS = "flex-1 min-w-0 sm:min-w-[200px]"

# Line 136 - Tighter on mobile
YEAR_BAR_COL = "flex flex-col items-center min-w-[28px] sm:min-w-[40px]"

# Line 143 - Tighter on mobile
MONTHLY_BAR_COL = "flex-1 flex flex-col items-center min-w-[24px] sm:min-w-[30px]"

# Line 150 - Tighter on mobile
AGE_BAR_COL = "flex-1 flex flex-col items-center min-w-[40px] sm:min-w-[50px]"
```

### generate_model_report.py

```python
# Line ~724 - Update inline min-w-[250px]
# Change: <div class="flex-1 min-w-[250px]">
# To:     <div class="flex-1 min-w-0 sm:min-w-[200px]">

# Line ~726 - Update stats grid gap
# Change: <div class="grid grid-cols-2 gap-4">
# To:     <div class="grid grid-cols-2 gap-3 sm:gap-4">

# Line ~769 - Update rankings wrapper (if not using constant)
# Change: <div class="flex gap-4 flex-wrap">
# To:     <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">

# Line ~769 - Update ranking badge (if not using constant)
# Change: <div class="flex-1 min-w-[120px] text-center p-4 bg-neutral-50 rounded-xl">
# To:     <div class="text-center p-4 bg-neutral-50 rounded-xl">
```

---

## Verification Steps

1. **Regenerate a report:**
   ```bash
   cd scripts/model_report_generator
   python generate_model_report.py FORD FOCUS
   ```

2. **Test in browser:**
   - Open `articles/model-reports/ford-focus-report.html`
   - Use browser DevTools to test at mobile widths (320px, 375px, 414px)
   - Check each section:
     - [ ] Pass Rate Overview - circle and stats should stack cleanly
     - [ ] Rankings - badges should stack vertically on mobile
     - [ ] Year trend chart - should scroll horizontally without page overflow
     - [ ] Age chart - should scroll horizontally
     - [ ] Seasonal chart - should scroll horizontally
     - [ ] Failure categories - labels should stack above bars on mobile
     - [ ] Tables - should scroll horizontally within their containers

3. **Verify no regressions on desktop:**
   - Test at 1024px+ to ensure layouts remain unchanged

---

## Background Context

The model report generator creates static HTML pages for vehicle MOT reliability reports. The current implementation has several mobile responsiveness issues:

1. **Horizontal bar charts** use fixed `w-48` labels that consume too much space on mobile
2. **Monthly and Age charts** are missing `overflow-x-auto`, causing page overflow
3. **Rankings badges** use `flex` with `min-w-[120px]` which doesn't stack cleanly
4. **Stats grid** has a `min-w-[250px]` that can cause layout issues on narrow screens

All fixes use Tailwind's responsive prefixes (`sm:`, `md:`) to maintain consistency with the rest of the app and avoid custom CSS.
