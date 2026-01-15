# Handover: New Article Opportunities Investigation

> **Task**: Investigate and prototype new high-value article types beyond the existing per-make reliability articles.
>
> **Goal**: Identify the most clickable, sticky, and shareable article concepts that leverage the unique MOT dataset.

---

## Context

### What Exists

The current pipeline generates **per-manufacturer reliability articles** (e.g., "Most Reliable Honda Models"):
- `generate_make_insights.py` → JSON with make-specific data
- `generate_article_html.py` → Styled HTML article
- Works well for 75 manufacturers

### The Opportunity

The database contains **unique insights no competitor has**:
- 32 million MOT tests
- Dangerous defect tracking
- Advisory-to-failure progression
- Component failure by mileage thresholds
- Geographic pass rates by postcode
- Seasonal patterns
- Left/right side defect distribution

These enable article types that **differentiate from generic "best cars" content**.

---

## Database Reference

**Location**: `data/database/mot_insights.db` (122 MB, read-only)

### Key Tables for New Articles

| Table | Rows | Unique Value |
|-------|------|--------------|
| `dangerous_defects` | 105,879 | Safety-critical failures by vehicle |
| `advisory_progression` | 5,869 | When advisories become failures |
| `component_mileage_thresholds` | 77,475 | What breaks at what mileage |
| `geographic_insights` | 325,640 | Pass rates by UK postcode area |
| `seasonal_patterns` | 122,368 | Monthly pass rate variations |
| `defect_locations` | 194,115 | Nearside/offside/front/rear distribution |
| `mileage_bands` | 50,039 | Pass rates by mileage bracket |
| `first_mot_insights` | 12,037 | First MOT vs subsequent comparison |
| `retest_success` | 10,920 | Retest pass rates |
| `failure_severity` | 22,707 | Major vs dangerous breakdown |

### Full Schema Reference

See: `docs/MOT_INSIGHTS_REFERENCE.md`

---

## Priority Article Concepts to Investigate

### Priority 1: Safety/Dangerous Defects Articles

**Concept**: "The Most Dangerous Cars on UK Roads"

**Why High Value**:
- Fear-based content = high CTR
- Safety angle = shareable with families
- Unique data no one else has

**Investigation Queries**:

```sql
-- Which vehicles have the highest dangerous defect rates?
SELECT
    make, model, model_year, fuel_type,
    SUM(occurrence_count) as total_dangerous,
    vi.total_tests,
    ROUND(SUM(occurrence_count) * 100.0 / vi.total_tests, 2) as dangerous_rate
FROM dangerous_defects dd
JOIN vehicle_insights vi USING (make, model, model_year, fuel_type)
WHERE vi.total_tests >= 1000
GROUP BY make, model, model_year, fuel_type, vi.total_tests
ORDER BY dangerous_rate DESC
LIMIT 25;

-- What are the most common dangerous defects overall?
SELECT
    defect_description,
    category_name,
    SUM(occurrence_count) as total_occurrences
FROM dangerous_defects
GROUP BY defect_description, category_name
ORDER BY total_occurrences DESC
LIMIT 20;

-- Which makes have the highest dangerous defect rates?
SELECT
    make,
    SUM(occurrence_count) as total_dangerous,
    SUM(vi.total_tests) as total_tests,
    ROUND(SUM(occurrence_count) * 100.0 / SUM(vi.total_tests), 3) as dangerous_rate
FROM dangerous_defects dd
JOIN vehicle_insights vi USING (make, model, model_year, fuel_type)
GROUP BY make
HAVING SUM(vi.total_tests) >= 50000
ORDER BY dangerous_rate DESC;
```

**Article Variants**:
- "Cars With the Most Brake Failures (Dangerous Category)"
- "Which SUVs Have the Most Safety Defects?"
- "Family Cars to Avoid: Dangerous Defect Rankings"

---

### Priority 2: Advisory Progression Articles

**Concept**: "When Your Advisory Becomes a Failure: What the Data Shows"

**Why High Value**:
- Actionable for car owners right now
- Unique data (tracks same vehicle over time)
- Creates urgency to fix advisories

**Investigation Queries**:

```sql
-- Which categories progress from advisory to failure most often?
SELECT
    category_name,
    SUM(advisory_count) as total_advisories,
    SUM(progressed_to_failure) as total_progressed,
    ROUND(AVG(progression_rate), 1) as avg_progression_rate,
    ROUND(AVG(avg_miles_to_failure), 0) as avg_miles_to_fail
FROM advisory_progression
GROUP BY category_name
ORDER BY avg_progression_rate DESC;

-- Which vehicles have highest advisory progression rates?
SELECT
    make, model, model_year,
    SUM(advisory_count) as advisories,
    SUM(progressed_to_failure) as progressed,
    ROUND(SUM(progressed_to_failure) * 100.0 / SUM(advisory_count), 1) as progression_pct
FROM advisory_progression
GROUP BY make, model, model_year
HAVING SUM(advisory_count) >= 100
ORDER BY progression_pct DESC
LIMIT 20;

-- How quickly do brake advisories become failures?
SELECT
    make,
    AVG(avg_days_to_failure) as avg_days,
    AVG(avg_miles_to_failure) as avg_miles
FROM advisory_progression
WHERE category_name = 'Brakes'
GROUP BY make
HAVING COUNT(*) >= 10
ORDER BY avg_days ASC;
```

**Article Variants**:
- "Brake Advisories: How Long Before They Fail?"
- "The Advisories You Can't Ignore"
- "Tyre Warnings: When 'Close to Limit' Becomes Illegal"

---

### Priority 3: Mileage Threshold Articles

**Concept**: "The 60,000 Mile Danger Zone: What Breaks First"

**Why High Value**:
- Specific and memorable
- Helps used car buyers
- Visual potential (charts showing failure curves)

**Investigation Queries**:

```sql
-- When do brakes start failing significantly?
SELECT
    make,
    AVG(failure_rate_0_30k) as rate_0_30k,
    AVG(failure_rate_30_60k) as rate_30_60k,
    AVG(failure_rate_60_90k) as rate_60_90k,
    AVG(failure_rate_90_120k) as rate_90_120k,
    COUNT(*) as models
FROM component_mileage_thresholds
WHERE category_name = 'Brakes'
GROUP BY make
HAVING COUNT(*) >= 20
ORDER BY rate_90_120k DESC;

-- Which components spike at which mileage?
SELECT
    category_name,
    spike_mileage_band,
    COUNT(*) as vehicle_count,
    ROUND(AVG(spike_increase_pct), 1) as avg_spike_pct
FROM component_mileage_thresholds
WHERE spike_mileage_band IS NOT NULL
GROUP BY category_name, spike_mileage_band
ORDER BY category_name, spike_mileage_band;

-- Cars that hold up best at high mileage
SELECT
    make, model, model_year, fuel_type,
    pass_rate, total_tests
FROM mileage_bands
WHERE mileage_band = '150k+' AND total_tests >= 100
ORDER BY pass_rate DESC
LIMIT 25;
```

**Article Variants**:
- "Cars That Survive 150,000 Miles"
- "When Suspension Fails: The Mileage Truth"
- "High-Mileage Heroes: Best Cars for 100k+ Buyers"

---

### Priority 4: Geographic/Regional Articles

**Concept**: "Where Do Cars Fail MOTs Most? UK Postcode Map"

**Why High Value**:
- Local SEO potential
- Shareable (regional pride/rivalry)
- Visual map potential

**Investigation Queries**:

```sql
-- Overall pass rate by postcode area
SELECT
    postcode_area,
    SUM(total_tests) as tests,
    ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as avg_pass_rate
FROM geographic_insights
GROUP BY postcode_area
ORDER BY avg_pass_rate DESC;

-- Best and worst areas
SELECT
    postcode_area,
    SUM(total_tests) as tests,
    ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as avg_pass_rate
FROM geographic_insights
GROUP BY postcode_area
HAVING SUM(total_tests) >= 10000
ORDER BY avg_pass_rate ASC
LIMIT 10;

-- Do certain cars fail more in certain regions?
SELECT
    make,
    postcode_area,
    SUM(total_tests) as tests,
    ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate
FROM geographic_insights
WHERE make IN ('FORD', 'VAUXHALL', 'BMW')
GROUP BY make, postcode_area
HAVING SUM(total_tests) >= 500
ORDER BY make, pass_rate DESC;
```

**Article Variants**:
- "Scotland vs England: Who Maintains Cars Better?"
- "The Worst Postcodes for MOT Failures"
- "Does London Really Fail More Cars?"

---

### Priority 5: Fuel Type Comparison Articles

**Concept**: "Hybrid vs Petrol: 5 Years of Real MOT Data"

**Why High Value**:
- Ongoing debate with strong opinions
- Hot topic as EV transition continues
- Clear data advantage over opinion pieces

**Investigation Queries**:

```sql
-- Hybrid advantage by make
SELECT
    make,
    SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END) as hybrid_tests,
    ROUND(SUM(CASE WHEN fuel_type = 'HY' THEN total_passes ELSE 0 END) * 100.0 /
          NULLIF(SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END), 0), 1) as hybrid_rate,
    ROUND(SUM(CASE WHEN fuel_type = 'PE' THEN total_passes ELSE 0 END) * 100.0 /
          NULLIF(SUM(CASE WHEN fuel_type = 'PE' THEN total_tests ELSE 0 END), 0), 1) as petrol_rate,
    ROUND(SUM(CASE WHEN fuel_type = 'DI' THEN total_passes ELSE 0 END) * 100.0 /
          NULLIF(SUM(CASE WHEN fuel_type = 'DI' THEN total_tests ELSE 0 END), 0), 1) as diesel_rate
FROM vehicle_insights
GROUP BY make
HAVING SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END) >= 1000
ORDER BY hybrid_rate DESC;

-- Electric vehicle reliability ranking
SELECT
    make, model, model_year,
    pass_rate, total_tests
FROM vehicle_insights
WHERE fuel_type = 'EL' AND total_tests >= 100
ORDER BY pass_rate DESC;

-- Diesel vs petrol failure categories
SELECT
    fuel_type,
    category_name,
    SUM(failure_count) as total_failures
FROM failure_categories fc
JOIN vehicle_insights vi USING (make, model, model_year, fuel_type)
WHERE fuel_type IN ('PE', 'DI')
GROUP BY fuel_type, category_name
ORDER BY fuel_type, total_failures DESC;
```

**Article Variants**:
- "Electric Cars: More Reliable Than You Think?"
- "Diesels to Avoid: The MOT Failure Data"
- "Plug-in Hybrids: The Hidden Reliability Problem?"

---

### Priority 6: Seasonal/Timing Articles

**Concept**: "Best Month to Book Your MOT (The Data Says...)"

**Why High Value**:
- Practical, actionable
- Timely/seasonal content
- Surprising insights

**Investigation Queries**:

```sql
-- National pass rates by month
SELECT
    month,
    total_tests,
    pass_rate
FROM national_seasonal
ORDER BY month;

-- Which month is best for specific makes?
SELECT
    make,
    month,
    SUM(total_tests) as tests,
    ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as avg_pass_rate
FROM seasonal_patterns sp
GROUP BY make, month
ORDER BY make, month;

-- Biggest seasonal variation by make
SELECT
    make,
    MAX(pass_rate) - MIN(pass_rate) as seasonal_variation,
    AVG(pass_rate) as avg_rate
FROM (
    SELECT make, month,
           ROUND(SUM(total_tests * pass_rate) / SUM(total_tests), 2) as pass_rate
    FROM seasonal_patterns
    GROUP BY make, month
)
GROUP BY make
HAVING COUNT(*) = 12
ORDER BY seasonal_variation DESC
LIMIT 20;
```

**Article Variants**:
- "Winter MOT Failures: What to Check Before January"
- "The Best and Worst Months for MOT Tests"
- "Summer vs Winter: When Do Cars Fail Most?"

---

### Priority 7: Quirky/Shareable Articles

**Concept**: "Left vs Right: Which Side of Your Car Fails More?"

**Why High Value**:
- Quirky, memorable
- Shareable on social media
- Uses unique `defect_locations` data

**Investigation Queries**:

```sql
-- Nearside vs offside failures
SELECT
    lateral,
    SUM(failure_count) as total_failures,
    ROUND(SUM(failure_count) * 100.0 / (SELECT SUM(failure_count) FROM defect_locations WHERE lateral IS NOT NULL), 1) as pct
FROM defect_locations
WHERE lateral IS NOT NULL
GROUP BY lateral;

-- Front vs rear failures
SELECT
    longitudinal,
    SUM(failure_count) as total_failures
FROM defect_locations
WHERE longitudinal IS NOT NULL
GROUP BY longitudinal;

-- Location distribution by category
SELECT
    category_name,
    lateral,
    longitudinal,
    SUM(failure_count) as failures
FROM defect_locations dl
JOIN failure_categories fc ON dl.make = fc.make
    AND dl.model = fc.model
    AND dl.model_year = fc.model_year
GROUP BY category_name, lateral, longitudinal
HAVING SUM(failure_count) >= 1000
ORDER BY category_name, failures DESC;
```

**Note**: The `defect_locations` table may need joining to get category context.

---

## Recommended Investigation Process

### Step 1: Validate Data Availability

For each priority concept, run the investigation queries to confirm:
- Sufficient sample sizes (aim for 1000+ tests per grouping)
- Meaningful variation in the data
- No obvious data quality issues

### Step 2: Identify Story Angles

Look for:
- **Surprises**: Data that contradicts common assumptions
- **Extremes**: Best/worst performers that stand out
- **Patterns**: Consistent trends across makes/years
- **Actionable insights**: Things readers can do with the info

### Step 3: Prototype One Article

Pick the strongest concept and create:
1. A new JSON generator function (similar to `generate_make_insights.py`)
2. A new HTML template function
3. Sample output for 2-3 test cases

### Step 4: Evaluate and Iterate

Consider:
- Is the data compelling enough?
- Is the article differentiated from competitors?
- Does it drive traffic to the main product (vehicle reports)?

---

## Technical Implementation Notes

### Database Connection Pattern

```python
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "mot_insights.db"

def get_connection():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
```

### Existing Code to Reference

- `scripts/article_generation/generate_make_insights.py` - JSON generation patterns
- `scripts/article_generation/generate_article_html.py` - HTML templating patterns
- `scripts/article_generation/explore_article_opportunities.py` - Query patterns

### Output Locations

- JSON: `data/generated/`
- HTML: `articles/generated/`

---

## Quick Start Commands

```bash
cd "C:\Users\gregor\Downloads\mot_data_2023"

# Explore existing article ideas
python scripts/article_generation/explore_article_opportunities.py --focus all

# Test database queries interactively
python -c "
import sqlite3
conn = sqlite3.connect('data/database/mot_insights.db')
conn.row_factory = sqlite3.Row

# Example: Top dangerous defect rates
cur = conn.execute('''
    SELECT make, model, model_year,
           SUM(occurrence_count) as dangerous_count
    FROM dangerous_defects
    GROUP BY make, model, model_year
    ORDER BY dangerous_count DESC
    LIMIT 10
''')
for row in cur:
    print(dict(row))
"

# Generate existing make article for reference
python scripts/article_generation/generate_make_insights.py HONDA --output test.json --pretty
python scripts/article_generation/generate_article_html.py test.json --output ./test_output/
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `data/database/mot_insights.db` | SQLite database (read-only) |
| `docs/MOT_INSIGHTS_REFERENCE.md` | Complete schema documentation |
| `docs/PROJECT_REFERENCE.md` | Project overview |
| `scripts/article_generation/REFERENCE.md` | Current pipeline documentation |
| `scripts/article_generation/explore_article_opportunities.py` | Exploration queries |

---

## Success Criteria

A good new article type should:

1. **Use unique data** - Something competitors can't easily replicate
2. **Have strong headlines** - Clickable, shareable titles
3. **Be actionable** - Help readers make decisions
4. **Drive traffic** - Include CTAs to vehicle reports
5. **Be scalable** - Can generate multiple articles from one template

---

## Recommended First Investigation

Start with **Priority 1: Dangerous Defects** because:
- Most unique data (no competitor has this)
- Highest emotional engagement (safety)
- Clear article structure (rankings + details)
- Multiple spin-off articles possible

Run the dangerous defects queries, identify the top 20 vehicles, and draft a headline structure.

---

*End of Handover*
