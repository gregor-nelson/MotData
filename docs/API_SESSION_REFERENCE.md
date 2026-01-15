# MOT Insights API Development - Session Reference

> **Project**: motorwise.io MOT Insights Feature
> **Phase**: API Development & Frontend Explorer
> **Date**: 2026-01-01

---

## 1. Project Overview

### What Was Built
A Python FastAPI backend + HTML/JS frontend to explore and serve pre-aggregated UK MOT test data for potential integration into a vehicle report application.

### Business Context
- **Target App:** motorwise.io (UK vehicle report application)
- **Data Source:** `mot_insights.db` - SQLite database (122.7 MB)
- **Data Scope:** 32.3 million MOT tests, 11,406 vehicle combinations, 86 manufacturers
- **Year Range:** 2000-2023

---

## 2. Database Summary

### Key Statistics
| Metric | Value |
|--------|-------|
| Total records | 1,327,482 |
| Tables | 19 |
| Unique vehicles | 11,406 (make/model/year/fuel combos) |
| Manufacturers | 86 |
| Models | 2,182 |
| UK postcode areas | 118 |
| National pass rate | 71.51% |

### Fuel Types
| Code | Name | Vehicles | Avg Pass Rate |
|------|------|----------|---------------|
| PE | Petrol | 5,388 | 74.4% |
| DI | Diesel | 5,064 | 69.3% |
| HY | Hybrid Electric | 644 | 86.5% |
| EL | Electric | 218 | 84.3% |
| ED | Plug-in Hybrid | 71 | ~85% |
| GB | Gas Bi-fuel | 2 | - |
| OT | Other | 19 | - |

### All 19 Tables

#### High-Value (Core Vehicle Data)
| Table | Rows | Purpose |
|-------|------|---------|
| `vehicle_insights` | 11,406 | Core stats: pass rate, test counts, mileage, vs national |
| `available_vehicles` | 11,406 | Index for dropdowns (make/model/year/fuel combos) |
| `failure_categories` | 103,507 | Top 10 failure categories per vehicle |
| `top_defects` | 225,881 | Specific failure + advisory defects |
| `dangerous_defects` | 105,879 | Safety-critical defects only |
| `mileage_bands` | 50,039 | Pass rate by mileage (0-30k, 30-60k, etc.) |
| `vehicle_rankings` | 34,218 | Rankings: overall, within make, within year |
| `manufacturer_rankings` | 75 | Brand-level reliability rankings |

#### Supporting Data
| Table | Rows | Purpose |
|-------|------|---------|
| `national_averages` | 36 | Benchmark metrics (71.51% pass rate, etc.) |
| `national_seasonal` | 12 | Monthly national pass rates |
| `age_bands` | 13,892 | Pass rate by vehicle age |
| `geographic_insights` | 325,640 | Pass rate by UK postcode area (118 areas) |

#### Lower Priority (Niche Use Cases)
| Table | Rows | Purpose |
|-------|------|---------|
| `seasonal_patterns` | 122,368 | Monthly patterns per vehicle |
| `first_mot_insights` | 12,037 | First MOT vs subsequent |
| `retest_success` | 10,920 | 99.3% retest pass rate |
| `advisory_progression` | 5,869 | Advisories rarely become failures (0.2%) |
| `component_mileage_thresholds` | 77,475 | When specific parts start failing |
| `defect_locations` | 194,115 | Physical location on vehicle |
| `failure_severity` | 22,707 | Major vs dangerous breakdown |

---

## 3. Key Data Insights

### Pass Rate Patterns
- **By Age:** 86.4% (3-4 yrs) → 59.9% (13+ yrs) = 26.5 point drop
- **By Mileage:** 86.3% (0-30k) → 57.5% (150k+) = 29 point drop
- **By Fuel:** Hybrid 86.5% > Electric 84.3% > Petrol 74.4% > Diesel 69.3%

### Top Failure Categories (by frequency)
1. Lamps/Electrical Equipment (10.8%)
2. Suspension (9.1%)
3. Brakes (7.2%)
4. Tyres (6.0%)
5. Visibility (4.6%)

### Best Manufacturers
1. Rolls Royce: 94.7%
2. Lamborghini: 94.7%
3. Ferrari: 94.5%
4. McLaren: 94.3%
5. Bentley: 91.6%

### Worst Manufacturers
1. Daewoo: 49.4%
2. Chevrolet: 54.4%
3. LDV: 54.5%
4. Proton: 54.7%
5. Rover: 58.9%

### Known Problem Vehicles
- Nissan Qashqai 2007-2009 diesel: 41-44% pass rate
- Renault Megane 2006 diesel: 42.8%
- Chevrolet Kalos 2005: 42.5%

### Best Performers (min 500 tests)
- Toyota Corolla Icon HEV 2023: 99.6%
- Honda Jazz Crosstar 2020: 96.1%
- Porsche Cayman 2019: 96.0%
- Lexus RX 2020: 96.0%

### Geographic Variation
- **Best:** BR (79.1%), EN (78.6%), TW (78.3%)
- **Worst:** KY (61.7%), DD (62.6%), TR (64.2%)

---

## 4. Project Structure

```
mot_data_2023/
├── mot_insights.db              # SQLite database (read-only)
├── requirements.txt             # fastapi, uvicorn
│
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app (26 endpoints)
│   ├── database.py              # SQLite connection helper
│   └── queries.py               # All SQL query functions
│
├── frontend/
│   └── index.html               # Dev explorer UI
│
└── docs/
    ├── API_IMPLEMENTATION_GUIDE.md   # Database schema + endpoint planning
    ├── API_SESSION_REFERENCE.md      # This document
    ├── MOT_DATA_REFERENCE.md         # Raw data documentation
    ├── MOT_INSIGHTS_REFERENCE.md     # Insights methodology
    └── PROJECT_REFERENCE.md          # Overall project reference
```

---

## 5. API Endpoints (26 total)

### Running the API
```bash
cd C:\Users\gregor\Downloads\mot_data_2023
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8010
```

### Utility
| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Connection check |
| `GET /api/stats` | Row counts per table |

### Vehicle Lookup (Cascading Dropdowns)
| Endpoint | Purpose |
|----------|---------|
| `GET /api/makes` | All 86 makes |
| `GET /api/makes/{make}/models` | Models for a make |
| `GET /api/makes/{make}/models/{model}/variants` | Year/fuel options |

### Combined Vehicle Report
| Endpoint | Purpose |
|----------|---------|
| `GET /api/vehicle/{make}/{model}/{year}/{fuel}` | Full report (insights, rankings, failures, defects, mileage) |

### Individual Table Endpoints
| Endpoint | Table |
|----------|-------|
| `GET /api/insights/{make}/{model}/{year}/{fuel}` | vehicle_insights |
| `GET /api/failures/{make}/{model}/{year}/{fuel}` | failure_categories |
| `GET /api/defects/{make}/{model}/{year}/{fuel}` | top_defects |
| `GET /api/dangerous/{make}/{model}/{year}/{fuel}` | dangerous_defects |
| `GET /api/mileage/{make}/{model}/{year}/{fuel}` | mileage_bands |
| `GET /api/rankings/{make}/{model}/{year}/{fuel}` | vehicle_rankings |
| `GET /api/geographic/{make}/{model}/{year}/{fuel}` | geographic_insights |
| `GET /api/seasonal/{make}/{model}/{year}/{fuel}` | seasonal_patterns |
| `GET /api/age/{make}/{model}/{year}/{fuel}` | age_bands |
| `GET /api/severity/{make}/{model}/{year}/{fuel}` | failure_severity |
| `GET /api/first-mot/{make}/{model}/{year}/{fuel}` | first_mot_insights |
| `GET /api/retest/{make}/{model}/{year}/{fuel}` | retest_success |
| `GET /api/advisory-progression/{make}/{model}/{year}/{fuel}` | advisory_progression |
| `GET /api/component-thresholds/{make}/{model}/{year}/{fuel}` | component_mileage_thresholds |
| `GET /api/defect-locations/{make}/{model}/{year}/{fuel}` | defect_locations |

### National/Aggregate
| Endpoint | Purpose |
|----------|---------|
| `GET /api/national/averages` | National benchmarks |
| `GET /api/national/seasonal` | Monthly national data |
| `GET /api/manufacturers` | All 75 manufacturer rankings |
| `GET /api/manufacturers/{make}` | Single manufacturer |

---

## 6. Sample API Responses

### Vehicle Report (`/api/vehicle/FORD/FOCUS/2018/PE`)
```json
{
  "vehicle": {
    "make": "FORD",
    "model": "FOCUS",
    "model_year": 2018,
    "fuel_type": "PE",
    "fuel_type_name": "Petrol"
  },
  "insights": {
    "total_tests": 37330,
    "total_passes": 32102,
    "total_fails": 4078,
    "pass_rate": 86.0,
    "avg_mileage": 34915,
    "pass_rate_vs_national": 14.48
  },
  "rankings": {
    "overall": {"rank": 2815, "total_in_category": 11406, "percentile": 75},
    "within_make": {"rank": 134, "total_in_category": 677, "percentile": 80},
    "within_year": {"rank": 281, "total_in_category": 641, "percentile": 56}
  },
  "failure_categories": [...],
  "top_failures": [...],
  "top_advisories": [...],
  "dangerous_defects": [...],
  "mileage_bands": [...]
}
```

---

## 7. Frontend Features

**Location:** `frontend/index.html` (open directly in browser)

**Tabs:**
1. **Vehicle Lookup** - Cascading dropdowns + quick vehicle buttons + full report display
2. **Table Explorer** - Raw JSON view of any table for selected vehicle
3. **National Data** - Averages and seasonal benchmarks
4. **Manufacturers** - All 75 ranked brands with cards

**Quick Test Vehicles:**
- Ford Focus 2018 PE
- Vauxhall Corsa 2015 PE
- VW Golf 2017 DI
- BMW 3 Series 2018 DI
- Tesla Model 3 2020 EL

---

## 8. Technical Notes

### Database Connection
- Read-only mode: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
- Row factory returns dicts, not tuples
- All queries use parameterized inputs (SQL injection safe)

### Case Handling
- All make/model/fuel inputs normalized to UPPERCASE
- Database stores everything in uppercase

### URL Encoding
- Model names with spaces work: `GOLF%20GTI`, `3%20SERIES`
- Frontend uses `encodeURIComponent()`

### CORS
- Configured to allow all origins (`*`) for dev
- Supports file:// protocol and localhost

### Port Configuration
- Currently set to port 8010
- Frontend hardcoded to `http://localhost:8010/api`

---

## 9. Integration Ideas for motorwise.io

### Option A: Simple Vehicle Lookup
- User enters/selects vehicle → show pass rate, top failures, ranking
- Single API call returns everything needed
- Colour-code: green (>80%), amber (65-80%), red (<65%)

### Option B: Pre-Purchase Report Enhancement
- Add "MOT Reliability" section to existing vehicle reports
- Show: pass rate vs national, common failures, mileage impact
- Flag known problem vehicles (Nissan Qashqai 2007-2009, etc.)

### Option C: Regional Context
- "MOT pass rates in your area" using postcode data
- Compare vehicle performance in user's region vs national

### Option D: Predictive Maintenance
- Use mileage bands to show: "At your current mileage, expect X% pass rate"
- Highlight which components fail at which mileages

### Option E: Comparison Tool
- Compare selected vehicle to alternatives
- "Ford Focus 2018 vs VW Golf 2018 vs Vauxhall Astra 2018"

---

## 10. Next Steps for Continuation

### Immediate
1. Explore the frontend to understand data structure
2. Identify which insights are most valuable for vehicle reports
3. Design how MOT data fits into existing report layout

### Integration Planning
1. Determine lookup method (user selects vs auto-match from reg)
2. Decide which tables/endpoints are needed for production
3. Plan how to handle missing vehicles (< 100 tests excluded)

### Production Considerations
1. Move from SQLite to PostgreSQL if scaling needed
2. Add caching headers for static data
3. Integrate behind nginx with existing app
4. Consider search endpoint for type-ahead

---

## 11. Useful Test Queries

```bash
# Health check
curl http://localhost:8010/api/health

# Get all makes
curl http://localhost:8010/api/makes

# Get Ford models
curl http://localhost:8010/api/makes/FORD/models

# Get Focus variants
curl "http://localhost:8010/api/makes/FORD/models/FOCUS/variants"

# Full vehicle report
curl "http://localhost:8010/api/vehicle/FORD/FOCUS/2018/PE"

# Manufacturer rankings
curl http://localhost:8010/api/manufacturers
```

---

## 12. Related Documentation

| File | Purpose |
|------|---------|
| `docs/API_IMPLEMENTATION_GUIDE.md` | Database schema + endpoint planning |
| `docs/API_SESSION_REFERENCE.md` | This document |
| `docs/MOT_DATA_REFERENCE.md` | Raw data documentation |
| `docs/MOT_INSIGHTS_REFERENCE.md` | Insights methodology |
| `docs/PROJECT_REFERENCE.md` | Overall project reference |
| `api/main.py` | All 26 API endpoints |
| `api/queries.py` | All SQL queries |
| `frontend/index.html` | Dev exploration UI |

---

*Document created: 2026-01-01*
*Ready for continuation in new session*
