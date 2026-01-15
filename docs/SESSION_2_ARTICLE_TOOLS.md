# MOT Insights - Article Generation Tools

> **Session Date:** 2026-01-01
> **Purpose:** Build tooling to generate SEO article data from MOT insights database
> **Status:** Core tooling complete, ready for article generation

---

## 1. Session Overview

### Business Goal
Create static HTML articles for motorwise.io using real MOT test data to drive organic traffic. Articles like "Most Reliable Honda Models" provide unique, data-driven content that competitors cannot replicate.

### What Was Built
A suite of Python tools to:
1. Extract comprehensive insights for any vehicle manufacturer
2. Export data as clean JSON for article generation
3. Explore the database to identify high-value article opportunities
4. GUI wrapper for easy operation without command line

### Key Decision
**Separated data extraction from article generation.** Rather than generating HTML directly, tools output JSON that can be processed in a separate session to create articles. This allows:
- Quick iteration on data queries
- Consistent JSON structure for templating
- Reuse of data across multiple article formats

---

## 2. Files Created

```
mot_data_2023/
├── mot_insights_gui.py                    # GUI wrapper for all tools
├── scripts/
│   ├── generate_make_insights.py          # Core insight generator
│   ├── generate_all_priority_makes.py     # Batch generator for 20 priority makes
│   └── explore_article_opportunities.py   # Data exploration for article ideas
├── data/
│   └── honda_insights.json                # Example output (generated)
├── articles/
│   └── honda-most-reliable-models.html    # Example article (prototype)
└── docs/
    └── SESSION_2_ARTICLE_TOOLS.md         # This document
```

---

## 3. Tool Reference

### 3.1 generate_make_insights.py

**Purpose:** Generate comprehensive JSON insights for a single vehicle manufacturer.

**Location:** `scripts/generate_make_insights.py`

**Usage:**
```bash
# Generate insights for a specific make
python scripts/generate_make_insights.py HONDA

# With custom output path
python scripts/generate_make_insights.py TOYOTA --output data/toyota.json

# Pretty print for readability
python scripts/generate_make_insights.py BMW --pretty

# List all available makes
python scripts/generate_make_insights.py --list

# Show top 20 makes by test volume
python scripts/generate_make_insights.py --list --top 20
```

**Output:** JSON file containing all insights for the specified make.

**Console Output Example:**
```
============================================================
  HONDA MOT INSIGHTS SUMMARY
============================================================
  Total Tests:     927,815
  Models/Variants: 1469
  Pass Rate:       72.2%
  vs National:     +0.7%
  Rank:            #41 of 75
============================================================
  Best:  CR-V 2021 (96.5%)
  Worst: STREAM 2001 (41.5%)
============================================================

  Output: C:\...\data\honda_insights.json
  Size:   135,228 bytes
```

---

### 3.2 explore_article_opportunities.py

**Purpose:** Explore the database to find article-worthy data patterns.

**Location:** `scripts/explore_article_opportunities.py`

**Usage:**
```bash
# Run all explorations
python scripts/explore_article_opportunities.py

# Focus on specific area
python scripts/explore_article_opportunities.py --focus reliability
python scripts/explore_article_opportunities.py --focus problems
python scripts/explore_article_opportunities.py --focus trends
python scripts/explore_article_opportunities.py --focus evs
```

**Available Analyses:**
| Analysis | Description |
|----------|-------------|
| `best_manufacturers` | Top 15 most reliable brands (min 50k tests) |
| `worst_manufacturers` | Bottom 15 brands (min 10k tests) |
| `best_vehicles` | Top 25 specific model/year/fuel combinations |
| `worst_vehicles` | Bottom 25 (the "avoid" list) |
| `hybrid_advantage` | Hybrid vs petrol vs diesel by brand |
| `worst_diesels` | Diesel models with highest failure rates |
| `best_first_cars` | Small cars suitable for new drivers |
| `ev_reliability` | Electric vehicle pass rates |
| `year_trends` | Pass rates by model year |

---

### 3.3 generate_all_priority_makes.py

**Purpose:** Batch generate insights for 20 high-priority manufacturers.

**Location:** `scripts/generate_all_priority_makes.py`

**Usage:**
```bash
python scripts/generate_all_priority_makes.py
```

**Priority Makes (in order):**
1. TOYOTA, HONDA, BMW, FORD, VOLKSWAGEN, AUDI, MERCEDES-BENZ
2. MAZDA, KIA, HYUNDAI, NISSAN, VAUXHALL
3. MINI, VOLVO, SUZUKI, SKODA, LAND ROVER, JAGUAR, LEXUS, PORSCHE

**Output:** Creates JSON files in `data/make_insights/` directory.

---

### 3.4 mot_insights_gui.py

**Purpose:** GUI wrapper for all tools - no command line needed.

**Location:** `mot_insights_gui.py` (project root)

**Usage:**
```bash
python mot_insights_gui.py
```

**Features:**
- **Generate Insights Tab:** Select make from dropdown, generate JSON
- **Explore Data Tab:** Run any exploration analysis, view results
- **Batch Generate Tab:** Select multiple makes, generate all at once
- **View JSON Tab:** Browse and preview generated JSON files
- **Log Panel:** All operations logged with timestamps

**GUI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  [Generate Insights] [Explore Data] [Batch Generate] [View] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tab content area                                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Log Output                                    [Clear][Save]│
│  [12:34:56] Generated honda_insights.json                   │
│  [12:34:57] Tests: 927,815 | Pass Rate: 72.2%              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. JSON Output Structure

The `generate_make_insights.py` script outputs JSON with this structure:

```json
{
  "meta": {
    "make": "HONDA",
    "generated_at": "2026-01-01T12:00:00",
    "database": "mot_insights.db",
    "national_pass_rate": 71.51
  },

  "summary": {
    "total_tests": 927815,
    "total_models": 1469,
    "avg_pass_rate": 72.2,
    "rank": 41,
    "rank_total": 75,
    "vs_national": 0.69,
    "best_model": "CR-V 2021",
    "best_model_pass_rate": 96.5,
    "worst_model": "STREAM 2001",
    "worst_model_pass_rate": 41.5
  },

  "competitors": [
    {"make": "TOYOTA", "avg_pass_rate": 74.0, "total_tests": 1606300, "rank": 31},
    {"make": "HONDA", "avg_pass_rate": 72.2, "total_tests": 927815, "rank": 41},
    ...
  ],

  "core_models": [
    {
      "core_model": "HR-V",
      "total_tests": 32512,
      "pass_rate": 87.75,
      "year_from": 2000,
      "year_to": 2020,
      "variant_count": 18,
      "variants": "HR-V,HR-V EX,HR-V SE,..."
    },
    ...
  ],

  "model_year_breakdowns": {
    "JAZZ": [
      {"model_year": 2020, "fuel_type": "PE", "pass_rate": 94.29, "total_tests": 4943},
      {"model_year": 2019, "fuel_type": "PE", "pass_rate": 92.88, "total_tests": 16755},
      ...
    ],
    "CR-V": [...],
    "CIVIC": [...]
  },

  "fuel_analysis": [
    {"fuel_type": "HY", "fuel_name": "Hybrid Electric", "pass_rate": 82.5, "total_tests": 25050},
    {"fuel_type": "PE", "fuel_name": "Petrol", "pass_rate": 71.4, "total_tests": 694437},
    {"fuel_type": "DI", "fuel_name": "Diesel", "pass_rate": 69.5, "total_tests": 191873}
  ],

  "best_models": [
    {"model": "CR-V", "model_year": 2021, "fuel_type": "HY", "pass_rate": 98.0, "total_tests": 152},
    ...
  ],

  "worst_models": [
    {"model": "CR-V", "model_year": 2003, "fuel_type": "PE", "pass_rate": 49.8, "total_tests": 5636},
    ...
  ],

  "failures": {
    "categories": [
      {"category_name": "Lamps, reflectors and electrical equipment", "total_failures": 120795},
      {"category_name": "Suspension", "total_failures": 77791},
      ...
    ],
    "top_failures": [
      {"defect_description": "Tyre tread depth below requirements", "category_name": "Tyres", "total_occurrences": 45000},
      ...
    ],
    "top_advisories": [...],
    "dangerous": [...]
  },

  "mileage_impact": [
    {"mileage_band": "0-30k", "band_order": 0, "total_tests": 150000, "avg_pass_rate": 89.5},
    {"mileage_band": "30k-60k", "band_order": 1, "total_tests": 200000, "avg_pass_rate": 82.1},
    ...
  ],

  "all_models": [
    // Every individual variant with full stats (250 entries for Honda)
  ]
}
```

---

## 5. Key Data Insights Discovered

### High-Value Article Opportunities

| Article Idea | Data Story | Priority |
|-------------|-----------|----------|
| Nissan Qashqai Reliability Disaster | 2007-2010 diesel has 41-45% pass rate | HIGH - viral potential |
| Most Reliable Toyota Models | Toyota #31, strong hybrid performance | HIGH - search volume |
| Worst Diesels to Buy | Renault/Vauxhall vans dominate bottom | HIGH - buying intent |
| Best First Cars by MOT Data | Jazz vs Yaris vs Polo comparison | MEDIUM - young drivers |
| The Hybrid Advantage | Hybrids pass 10-15% more often | MEDIUM - decision content |
| Electric Car Reliability | Tesla, Leaf, Zoe data | MEDIUM - growing segment |

### Problem Vehicles Identified (Avoid List)
```
Nissan Qashqai 2008 DI:    41.9% pass rate (4,960 tests)
Nissan Qashqai 2009 DI:    42.3% pass rate (11,182 tests)
Renault Megane 2006 DI:    42.8% pass rate (1,532 tests)
Renault Clio 2009 DI:      43.4% pass rate (3,294 tests)
Vauxhall Vivaro 2011 DI:   45.4% pass rate (11,218 tests)
```

### Manufacturer Rankings (Top/Bottom)
```
Best:                      Worst:
#1  Rolls Royce  94.7%    #75 Daewoo      49.4%
#2  Lamborghini  94.7%    #74 Chevrolet   54.4%
#3  Ferrari      94.5%    #73 LDV         54.5%
#4  McLaren      94.3%    #72 Proton      54.7%
#5  Bentley      91.6%    #71 Rover       58.9%
```

---

## 6. Example Article Created

An example HTML article was generated as a prototype:

**File:** `articles/honda-most-reliable-models.html`

**Features:**
- Full SEO metadata (title, description, OG tags)
- JSON-LD structured data (Article, BreadcrumbList, FAQPage)
- Responsive design using Tailwind CSS
- Data tables with pass rates
- Year-by-year breakdowns
- Best/worst recommendations
- FAQ section for rich snippets
- CTA to motorwise.io

**Note:** This was created before the decision to separate data extraction from article generation. Future articles should be generated from JSON output.

---

## 7. Workflow for Creating New Articles

### Step 1: Identify Article Opportunity
```bash
python scripts/explore_article_opportunities.py --focus problems
```
Review output to find compelling data stories.

### Step 2: Generate JSON Data
```bash
python scripts/generate_make_insights.py NISSAN --output data/nissan.json --pretty
```

### Step 3: Create Article (Separate Session)
Load the JSON file and use it to populate an HTML template based on the article type and target keywords.

### Step 4: Deploy
Copy the generated HTML to `public/articles/` in the motorwise.io project.

---

## 8. Technical Notes

### Database Connection
- Read-only mode: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
- Row factory returns dicts for easy JSON serialization
- All queries use parameterized inputs (SQL injection safe)

### Data Thresholds
- Minimum 100 tests per vehicle variant for inclusion in database
- Minimum 500 tests for aggregated model statistics
- Minimum 1000 tests for "best/worst" lists

### Core Model Aggregation
The script identifies "core models" by finding the shortest model name in each family:
- CIVIC, CIVIC SR VTEC, CIVIC EX → aggregated under "CIVIC"
- JAZZ, JAZZ CROSSTAR EX → aggregated under "JAZZ"

### Competitor Groups
Predefined competitor groups for comparison:
- Japanese: HONDA, TOYOTA, MAZDA, NISSAN, HYUNDAI, KIA, SUZUKI
- German Premium: BMW, MERCEDES-BENZ, AUDI, LEXUS, JAGUAR, VOLVO
- Mainstream: FORD, VAUXHALL, VOLKSWAGEN, PEUGEOT, RENAULT, CITROEN

---

## 9. Dependencies

**Python:** 3.8+ (uses built-in libraries only)

**Required Packages:** None (uses only standard library)
- `sqlite3` - database access
- `json` - JSON serialization
- `argparse` - CLI argument parsing
- `tkinter` - GUI (built into Python)
- `pathlib` - path handling
- `threading` - background operations in GUI

**Database:** `mot_insights.db` (122.7 MB, read-only)

---

## 10. Next Steps

### Immediate
1. Run batch generator for all priority makes
2. Review JSON output structure for any missing data
3. Create article generation templates

### Article Pipeline
1. Create HTML template that consumes JSON
2. Build article generator script
3. Set up review/approval workflow
4. Deploy to motorwise.io public folder

### Potential Enhancements
- Add search/filter to JSON viewer in GUI
- Export comparison tables as images
- Generate meta descriptions automatically
- Create sitemap entries for new articles

---

*Document created: 2026-01-01*
*Ready for continuation in new session*
