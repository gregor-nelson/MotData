# Known Issues: Confidence Scoring & Defect Grouping Analysis

**Date:** 17 January 2026
**Status:** Analysis Complete - Awaiting Decision
**Purpose:** Document findings on data quality issues affecting Known Issues accuracy

---

## Executive Summary

Investigation into the Known Issues algorithm revealed two interconnected data quality concerns:

1. **Defect Fragmentation:** Similar issues are recorded with slightly different MOT wording, fragmenting what should be a single signal into multiple entries with artificially inflated ratios.

2. **Sample Size Variation:** Issues range from 50 to 85,000+ occurrences. Low-count issues may be noise OR may be genuine model-specific problems (e.g., Ford speedometer issues).

**Key Finding:** These issues require careful balancing. Over-filtering risks losing genuine insights; under-filtering risks showing misleading data. This is a premium product where accuracy is paramount.

---

## Database Overview

| Metric | Value |
|--------|-------|
| Total MOT tests | 32,801,943 |
| Unique defect descriptions | 521 |
| Unique make/model combinations | 40,716 |

---

## Issue 1: Defect Fragmentation

### The Problem

The same underlying mechanical issue can be recorded with multiple MOT defect description variants. The algorithm treats each as a separate defect, leading to:

- **Fragmented baselines** (each variant has its own national rate)
- **Inflated ratios** for rare wording variants
- **Redundant entries** in the output

### Case Study: Vauxhall Corsa Brake Imbalance

**CURRENT OUTPUT (7 separate entries):**

| Ratio | Occurrences | Defect Description |
|-------|-------------|-------------------|
| 13.1× | 8,781 | Brakes imbalance...less than 50% of the maximum effort...steered axle |
| 11.8× | 4,231 | Braking effort not recording at a wheel |
| 2.4× | 56 | Brakes imbalance...vehicle deviates excessively |
| 2.3× | 846 | Braking effort inadequate at a wheel |
| 2.0× | 324 | Brakes imbalance...less than 70%...same axle (variant) |
| 1.5× | 6,552 | Brakes imbalance...less than 70%...same axle |
| 1.1× | 383 | Braking effort inadequate at any wheel |
| 1.0× | 173 | Braking effort not recording at any wheel |

**PROPOSED OUTPUT (1 grouped entry):**

| Ratio | Occurrences | Defect Description |
|-------|-------------|-------------------|
| 3.3× | 21,346 | Brake imbalance/effort issues (combined) |

**Impact:** The 13.1× and 11.8× ratios are misleading. They result from comparing against rare national wording variants, not because Corsa has 13× more brake issues. The true elevation is ~3.3×.

### Brake Imbalance National Fragmentation

All variants of brake imbalance/effort defects nationally:

| National Total | Makes Affected | Description |
|----------------|----------------|-------------|
| 166,073 | 291 | Brakes imbalance...less than 70%...same axle |
| 24,844 | 128 | Brakes imbalance...less than 50%...steered axle |
| 13,696 | 117 | Braking effort inadequate at a wheel |
| 13,287 | 125 | Braking effort not recording at a wheel |
| 12,505 | 93 | Braking effort inadequate at any wheel |
| 6,367 | 75 | Braking effort not recording at any wheel |
| 6,084 | 86 | Brakes imbalance...third variant |
| 856 | 46 | Brakes imbalance...vehicle deviates excessively |
| **243,712** | **TOTAL** | If grouped as "Brake Imbalance/Effort" |

### Shock Absorber Fragmentation

| National Total | Description |
|----------------|-------------|
| 274,436 | A shock absorber damaged...does not function or showing signs of severe leakage |
| 44,368 | A shock absorber bush excessively worn |
| 31,496 | A shock absorber which has negligible damping effect |
| 5,679 | A shock absorber insecurely attached to chassis or axle |
| 4,321 | A shock absorber missing or likely to become detached |
| **360,300** | **TOTAL if grouped** |

### Wheel Bearing Fragmentation

| National Total | Description |
|----------------|-------------|
| 95,144 | A wheel bearing excessively rough |
| 52,091 | A wheel bearing with excessive play |
| 8,620 | A wheel bearing play so excessive it is likely to break up |
| 6,454 | A wheel bearing so rough it is likely to overheat or break up |
| **162,309** | **TOTAL if grouped** |

### Brake Hose Fragmentation

| National Total | Description |
|----------------|-------------|
| 26,975 | A brake hose ferrule excessively corroded |
| 23,649 | A flexible brake hose excessively damaged, deteriorated, chafed... |
| 20,841 | Flexible brake hose excessively damaged, chafed, twisted... |
| 7,618 | Brake hoses or connections leaking on hydraulic systems |
| 3,369 | Brake pipe likely to become detached or damaged |
| 1,464 | Brake hose bulging under pressure |
| 131 | Brake hose damaged and likely to fail |
| **84,047** | **TOTAL if grouped** |

---

## Issue 2: Sample Size Variation

### Current Distribution (487 issues across 20 vehicles)

| Occurrence Range | Count | Percentage | Visual |
|------------------|-------|------------|--------|
| 50 - 100 | 84 | 17.2% | ######## |
| 100 - 250 | 96 | 19.7% | ######### |
| 250 - 500 | 72 | 14.8% | ####### |
| 500 - 1,000 | 57 | 11.7% | ##### |
| 1,000 - 2,500 | 68 | 14.0% | ###### |
| 2,500 - 5,000 | 50 | 10.3% | ##### |
| 5,000 - 10,000 | 30 | 6.2% | ### |
| 10,000+ | 28 | 5.7% | ## |

**37% of flagged issues have fewer than 250 occurrences.**

### By Severity Tier

| Tier | Count | Avg Occurrences | Min | Max |
|------|-------|-----------------|-----|-----|
| Major (3×+) | 144 | 1,593 | 50 | 24,481 |
| Known (2-3×) | 181 | 2,752 | 50 | 85,060 |
| Elevated (1.5-2×) | 162 | 3,395 | 50 | 48,359 |

### Low-Occurrence Issues Currently Flagged as Major

| Ratio | Occurrences | Vehicle | Defect |
|-------|-------------|---------|--------|
| 9.3× | 128 | Ford Focus | Function of the switch impaired |
| 6.6× | 93 | Toyota Yaris | Fuel pipe or hose damaged |
| 6.1× | 140 | Ford Fiesta | Movement between stub axle and axle beam |
| 5.8× | 86 | Vauxhall Corsa | Actuator excessively corroded |
| 5.5× | 50 | Ford Fiesta | Stub axle movement (variant) |
| 4.7× | 271 | BMW 3 Series | Shock absorber missing or likely detached |
| 4.3× | 317 | BMW 3 Series | Shock absorber insecurely attached |
| 4.1× | 142 | BMW 3 Series | Transmission shaft bolts loose/missing |

**Question:** Are these noise or genuine model-specific issues?

---

## Case Study: Ford Focus Speedometer (Genuine Low-Occurrence Issue)

The user correctly identified that Ford Focus mid-2000s models have known speedometer/instrument cluster issues. This is a real-world known problem.

### Data

| Defect | Focus Rate | National Rate | Ratio | Focus Occurrences |
|--------|------------|---------------|-------|-------------------|
| Speedometer not working | 0.0073% | 0.0030% | 2.4× | 71 |

### Year Breakdown

| Model Year | Occurrences |
|------------|-------------|
| 2003 | 26 |
| 2002 | 15 |
| 2004 | 6 |
| 2008 | 6 |
| 2001 | 4 |
| 2006 | 4 |

**Insight:** Only 71 occurrences, but clearly concentrated in 2002-2003 model years. This IS a genuine model-specific issue despite low numbers.

**Risk:** Aggressive sample size filtering would eliminate this valid insight.

---

## All Category Defect Data (For Reference)

### Brakes (Top 20)

| Occurrences | Defect Description |
|-------------|-------------------|
| 619,873 | a brake lining or pad worn below 1.5mm |
| 380,386 | Parking brake efficiency below minimum requirement |
| 290,591 | Significant brake effort recorded with no brake applied indicating binding |
| 232,725 | Brake pipe damaged or excessively corroded |
| 196,255 | Brake disc or drum significantly and obviously worn |
| 169,657 | Parking brake inoperative on one side |
| 166,073 | Brakes imbalance...less than 70%...same axle |
| 136,129 | Warning device shows system malfunction |
| 102,494 | Excessive fluctuation in brake effort through each wheel revolution |
| 99,439 | Parking brake efficiency less than 50% of required value |
| 83,889 | Brake disc or drum excessively weakened, insecure or fractured |
| 64,482 | Parking brake lever excessive movement indicating incorrect adjustment |
| 63,377 | Service brake efficiency below minimum requirement |
| 59,085 | ESC MIL indicates a system malfunction |
| 55,338 | Brake lining or pad worn down to wear indicator |
| 51,119 | Brake performance unable to be tested |
| 40,071 | A service brake control has insufficient reserve travel |
| 32,482 | Abnormal lag in brake operation on a wheel |
| 31,220 | Leaking brake pipe or connection on hydraulic system |
| 26,975 | A brake hose ferrule excessively corroded |

### Suspension (Top 20)

| Occurrences | Defect Description |
|-------------|-------------------|
| 1,244,006 | A suspension pin, bush or joint excessively worn |
| 861,878 | A spring or spring component fractured or seriously weakened |
| 473,936 | A suspension joint dust cover missing or no longer prevents ingress |
| 274,436 | A shock absorber damaged...does not function or severe leakage |
| 215,564 | Load bearing structure within 30cm of mounting significantly reduced |
| 95,144 | A wheel bearing excessively rough |
| 89,543 | A suspension component excessively damaged or corroded |
| 67,946 | A suspension pin, bush or joint likely to become detached |
| 52,091 | A wheel bearing with excessive play |
| 44,368 | A shock absorber bush excessively worn |
| 33,741 | A suspension component fractured or likely to fail |
| 31,496 | A shock absorber which has negligible damping effect |
| 29,747 | A stub axle swivel pin and/or bush excessively worn |
| 27,046 | A suspension pin, bush, joint or bearing excessively worn |
| 26,265 | A suspension component missing, likely detached or directional stability impaired |
| 20,948 | A suspension component insecurely attached to chassis or axle |
| 10,822 | Load bearing structure so weakened control likely adversely affected |
| 8,620 | A wheel bearing play so excessive likely to break up |
| 6,454 | A wheel bearing so rough likely to overheat or break up |
| 5,679 | A shock absorber insecurely attached to chassis or axle |

### Lamps, Reflectors & Electrical (Top 20)

| Occurrences | Defect Description |
|-------------|-------------------|
| 1,168,307 | The aim of a headlamp is not within limits |
| 883,906 | A lamp missing, inoperative or multiple light source with more than 1/3 not working |
| 660,312 | Stop lamp missing, inoperative or multiple with more than 1/3 not working |
| 558,222 | A headlamp or light source missing, inoperative or more than 50% not working |
| 369,866 | A rear registration plate lamp missing or inoperative |
| 226,200 | A direction indicator lamp missing or inoperative |
| 180,188 | Lamp emitted colour, position or intensity not in accordance |
| 163,141 | Obligatory rear fog lamp missing, or front/rear fog lamp inoperative |
| 100,659 | Audible warning inoperative |
| 82,583 | Headlamp aim unable to be tested |
| 57,161 | Rear registration plate lamp does not illuminate simultaneously |
| 55,493 | Product on lens or light source which reduces light output |
| 53,787 | Lamp not securely attached |
| 51,890 | Headlamp reflector or lens seriously defective or missing |
| 41,703 | Headlamp emitted colour, position or intensity not in accordance |
| 40,484 | Headlamp levelling device inoperative |
| 37,376 | Stop lamps all missing or inoperative |
| 36,292 | A reversing lamp inoperative |
| 29,712 | A battery insecure and likely to fall or cause short circuit |
| 25,283 | A position lamp adversely affected by operation of another lamp |

### Steering (Top 15)

| Occurrences | Defect Description |
|-------------|-------------------|
| 353,330 | A steering ball joint with excessive wear or free play |
| 177,924 | Steering rack gaiter or ball joint dust cover missing |
| 23,261 | Power steering fluid leaking or system malfunctioning |
| 22,697 | A steering ball joint worn to extent there is serious risk |
| 11,754 | Free play in steering measured at rim exceeds limits |
| 5,033 | EPS MIL indicating a system malfunction |
| 4,788 | Steering linkage retaining or locking device missing |
| 2,673 | A steering linkage component with excessive movement |
| 2,528 | Power steering inoperative and steering adversely affected |
| 2,069 | Power steering inoperative |
| 2,023 | Power steering fluid reservoir empty |
| 1,953 | Excessive wear in universal joint or flexible coupling |
| 1,823 | Excessive roughness in operation of steering |
| 1,814 | Free play in steering...variant |
| 1,684 | A steering linkage component with relative movement |

### Tyres (All)

| Occurrences | Defect Description |
|-------------|-------------------|
| 850,063 | Tyre tread depth not in accordance with requirements |
| 742,767 | A tyre seriously damaged |
| 457,460 | A tyre cords visible or damaged |
| 111,934 | A tyre pressure monitoring system malfunctioning |
| 58,737 | A tyre has a lump, bulge or tear caused by separation |
| 41,405 | Tyres on same axle or twin wheels are different sizes |
| 21,587 | A tyre not fitted in compliance with manufacturers sidewall |
| 9,732 | A tyre valve seriously damaged likely to cause sudden deflation |
| 7,402 | A tyre fouling a part of the vehicle |
| 1,102 | A recut tyre fitted to vehicle not permitted |
| 1,036 | Tyres on same axle of different structure |
| 955 | A tyre incorrectly seated on wheel rim |
| 309 | A tyre over ten years old on front steered axle |
| 63 | A date code illegible on tyre fitted to front steered axle |

### Noise, Emissions & Leaks (Top 15)

| Occurrences | Defect Description |
|-------------|-------------------|
| 476,554 | Engine MIL illuminated indicating a malfunction |
| 173,147 | Lambda coefficient outside default limits |
| 130,020 | Emissions test unable to be completed |
| 129,120 | Emissions levels exceed default limits |
| 88,943 | Smoke opacity levels exceed manufacturers specified limit |
| 88,427 | Emissions levels exceed manufacturers specified limits |
| 58,232 | An induction or exhaust leak that could affect emissions |
| 51,886 | Fluid leaking excessively and likely to harm environment |
| 29,549 | Smoke opacity levels exceed default limit |
| 14,279 | Emissions test not completed because smoke levels significant |
| 9,769 | Emission control equipment missing, modified or defective |
| 7,895 | Exhaust on DPF-fitted vehicle emitting visible smoke |
| 7,028 | Emits excessive dense blue or visible black smoke during acceleration |
| 5,796 | Exhaust emits excessive smoke or vapour |
| 4,783 | Fluid leaking continuously posing serious risk |

### Body, Chassis, Structure (Top 15)

| Occurrences | Defect Description |
|-------------|-------------------|
| 453,104 | A transmission shaft CV joint boot missing or no longer effective |
| 350,525 | Exhaust system leaking or insecure |
| 79,430 | Vehicle structure corroded to extent rigidity affected |
| 63,627 | A door will not open using control or close properly |
| 45,859 | Fuel system leaking, or missing/ineffective filler cap |
| 44,937 | Body, cab or chassis excessively corroded at mounting point |
| 35,174 | A body panel damaged or corroded and likely to cause injury |
| 30,876 | Bumper insecure or with damage likely to cause injury |
| 19,433 | Fuel system leaking excessively or fire risk |
| 11,611 | Any part of noise suppression system insecure |
| 10,583 | Fire risk due to fuel tank/exhaust shield missing |
| 9,993 | An engine mounting severely damaged resulting in misalignment |
| 9,595 | A body panel likely to become detached |
| 7,912 | A drivers seat fore/aft adjustment not functioning |
| 7,732 | A transmission joint, belt or chain excessively worn |

---

## Proposed Grouping Strategy

### Component Keywords by Category

```python
DEFECT_GROUPS = {
    'Brakes': {
        'Brake imbalance/effort': ['imbalance', 'braking effort'],
        'Brake hose': ['brake hose', 'flexible brake hose'],
        'Brake pipe': ['brake pipe'],
        'Brake disc/drum': ['brake disc', 'brake drum'],
        'Brake lining/pad': ['brake lining', 'brake pad'],
        'Parking brake': ['parking brake'],
        'Service brake': ['service brake'],
        'Brake actuator': ['actuator'],
    },
    'Suspension': {
        'Shock absorber': ['shock absorber'],
        'Wheel bearing': ['wheel bearing'],
        'Suspension bush/joint': ['suspension pin', 'suspension bush', 'suspension joint'],
        'Spring': ['spring'],
        'Stub axle': ['stub axle'],
    },
    'Lamps': {
        'Headlamp': ['headlamp'],
        'Stop lamp': ['stop lamp'],
        'Fog lamp': ['fog lamp'],
        'Direction indicator': ['direction indicator'],
        'Registration plate lamp': ['registration plate lamp'],
    },
    'Steering': {
        'Steering ball joint': ['steering ball joint'],
        'Power steering': ['power steering'],
        'Steering rack': ['steering rack'],
    },
    # etc.
}
```

### Grouping Logic

1. Match defect description to group by keyword within category
2. Sum all variant occurrences for both model and national baseline
3. Calculate ratio on combined totals
4. Display as single grouped entry

---

## Options to Consider

### Option A: Group First, Then Consider Confidence

**Approach:**
1. Implement defect grouping (solves fragmentation)
2. Recalculate all ratios with grouped data
3. Review new distribution before deciding on sample size thresholds

**Pros:**
- Addresses the most obvious accuracy issue first
- May naturally reduce the low-occurrence problem (variants combine to higher counts)
- More conservative approach

**Cons:**
- Defers confidence scoring decision

### Option B: Confidence Tiers (Display-Level)

**Approach:**
- Keep all issues but add visual confidence indicators
- "High confidence" (1000+ occurrences)
- "Moderate confidence" (250-1000)
- "Limited data" (< 250)

**Pros:**
- Transparent to users
- Doesn't lose potentially genuine insights
- Premium feel (shows the depth of analysis)

**Cons:**
- More UI complexity
- Doesn't solve fragmentation

### Option C: Sliding Scale (Ratio × Sample)

**Approach:**
- Require higher ratios for smaller sample sizes
- e.g., 50 occurrences needs 5×+ to be "Major", 1000 occurrences needs 3×+

**Pros:**
- Statistically sound
- Accounts for uncertainty

**Cons:**
- Complex to explain
- May miss genuine issues like Ford speedometer

### Option D: Hybrid (Recommended Direction)

1. **Implement grouping** (required for accuracy)
2. **Add confidence display** (transparency for premium)
3. **Review thresholds** after grouping is in place

---

## Questions for Next Session

1. **Grouping granularity:** Should "brake hose" and "brake pipe" be separate groups or combined as "brake lines"?

2. **Universal issue handling:** After grouping, should we still flag a 3× "brake imbalance" issue, or is this too common to be meaningful?

3. **Year-specific patterns:** The Ford speedometer issue is concentrated in 2002-2003. Should the algorithm highlight year-specific patterns more strongly?

4. **Confidence display:** Should low-confidence issues be:
   - Shown with a caveat label?
   - Moved to "Worth Noting" regardless of ratio?
   - Hidden entirely with a minimum threshold?

5. **Premium value:** What makes a premium user pay for this vs free data? Is it:
   - More accurate/grouped insights?
   - Confidence scoring transparency?
   - Year-specific recommendations?
   - Something else?

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/inspection_guide/known_issues.py` | Core algorithm |
| `scripts/inspection_guide/known_issues_html.py` | HTML generation |
| `scripts/inspection_guide/specs/KNOWN_ISSUES_HANDOVER.md` | Original handover doc |
| `scripts/inspection_guide/reports/CONFIDENCE_SCORING_ANALYSIS.md` | This document |

---

## Quick Test Commands

```bash
# Run current algorithm
cd "c:\Users\gregor\Downloads\Mot Data"
python -m scripts.inspection_guide.known_issues

# Generate HTML for a vehicle
python -c "
from scripts.known_issues.known_issues import generate_known_issues_report
from scripts.known_issues.known_issues_html import generate_known_issues_page

report = generate_known_issues_report('FORD', 'FOCUS')
html = generate_known_issues_page(report)
print(html[:500])
"
```

---

*Analysis conducted 17 January 2026*
