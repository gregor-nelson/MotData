# MOT Insights API - Overview

> Quick reference for LLMs and developers. For full details, see [API_REFERENCE.md](./API_REFERENCE.md).

---

## What This Is

A FastAPI application serving UK MOT vehicle test analytics from a pre-computed SQLite database. Provides pass rates, failure analysis, and reliability insights for 11,406 vehicle variants.

**[Full details → Project Overview](./API_REFERENCE.md#1-project-overview)**

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI (Python) |
| Database | SQLite (read-only) |
| Server | Uvicorn on port 8010 |
| Frontend | Single HTML file |

---

## File Structure

```
api/
├── app.py              # Entry point - run this to start server
├── backend/
│   ├── main.py         # All FastAPI endpoint definitions
│   ├── database.py     # SQLite connection (get_db context manager)
│   └── queries.py      # All SQL query functions
├── frontend/
│   └── index.html      # Dev explorer UI
└── docs/
    ├── OVERVIEW.md     # This file
    └── API_REFERENCE.md
data/database/
└── mot_insights.db     # SQLite database
```

**[Full details → Architecture](./API_REFERENCE.md#2-architecture)**

---

## Database Tables (19 total)

| Table | Purpose |
|-------|---------|
| `available_vehicles` | Master index of 11,406 vehicle variants |
| `vehicle_insights` | Core stats (pass_rate, total_tests, avg_mileage) |
| `failure_categories` | Top 10 failure categories per vehicle |
| `top_defects` | Top failures & advisories per vehicle |
| `dangerous_defects` | Safety-critical defects |
| `mileage_bands` | Pass rates by mileage (0-30k, 30k-60k, etc.) |
| `vehicle_rankings` | Rankings (overall, within_make, within_year) |
| `manufacturer_rankings` | Brand-level rankings |
| `national_averages` | Benchmark metrics (71.5% national pass rate) |

Other tables: `geographic_insights`, `seasonal_patterns`, `age_bands`, `failure_severity`, `first_mot_insights`, `retest_success`, `advisory_progression`, `component_mileage_thresholds`, `defect_locations`, `national_seasonal`

**[Full details → Database Schema](./API_REFERENCE.md#3-database-schema)**

---

## Key API Endpoints

### Vehicle Lookup (cascading dropdowns)
| Endpoint | Returns |
|----------|---------|
| `GET /api/makes` | List of all makes |
| `GET /api/makes/{make}/models` | Models for a make |
| `GET /api/makes/{make}/models/{model}/variants` | Year/fuel combinations |

### Vehicle Data
| Endpoint | Returns |
|----------|---------|
| `GET /api/vehicle/{make}/{model}/{year}/{fuel}` | **Full report** (all data combined) |
| `GET /api/insights/{make}/{model}/{year}/{fuel}` | Core stats only |
| `GET /api/failures/{make}/{model}/{year}/{fuel}` | Failure categories |
| `GET /api/defects/{make}/{model}/{year}/{fuel}` | Top defects |
| `GET /api/mileage/{make}/{model}/{year}/{fuel}` | Mileage band breakdown |
| `GET /api/rankings/{make}/{model}/{year}/{fuel}` | Comparative rankings |

### National/Aggregate
| Endpoint | Returns |
|----------|---------|
| `GET /api/manufacturers` | All manufacturer rankings |
| `GET /api/manufacturers/{make}` | Single manufacturer |
| `GET /api/national/averages` | Benchmark metrics |

### Utility
| Endpoint | Returns |
|----------|---------|
| `GET /api/health` | API/database status |
| `GET /api/stats` | Row counts for all tables |

**[Full details → API Endpoints Reference](./API_REFERENCE.md#4-api-endpoints-reference)**

---

## Query Functions (queries.py)

Key functions:
- `get_all_makes(conn)` → list of makes
- `get_models_for_make(conn, make)` → list of models
- `get_variants_for_model(conn, make, model)` → year/fuel combos
- `get_vehicle_insights(conn, make, model, year, fuel)` → core stats dict
- `get_failure_categories(conn, ...)` → top 10 categories
- `get_top_defects(conn, ...)` → `{"failures": [...], "advisories": [...]}`
- `get_vehicle_rankings(conn, ...)` → `{"overall": {...}, "within_make": {...}, ...}`
- `check_vehicle_exists(conn, ...)` → boolean

All lookups normalize inputs to uppercase.

**[Full details → Query Functions](./API_REFERENCE.md#5-query-functions)**

---

## Running the Server

```bash
cd C:\Users\gregor\Downloads\Mot Data\api
python app.py
```

Access:
- Frontend: http://localhost:8010
- API: http://localhost:8010/api
- Swagger docs: http://localhost:8010/api/docs

**[Full details → Setup & Running](./API_REFERENCE.md#7-setup--running)**

---

## Key Data Codes

### Fuel Types
| Code | Meaning |
|------|---------|
| `PE` | Petrol |
| `DI` | Diesel |
| `HY` | Hybrid |
| `EL` | Electric |
| `ED` | Plug-in Hybrid |

### Mileage Bands
`0-30k`, `30k-60k`, `60k-90k`, `90k-120k`, `120k-150k`, `150k+`

### Pass Rate Thresholds
- **Good**: 80%+ (above average)
- **Average**: 65-80%
- **Poor**: <65% (below average)
- **National average**: 71.5%

**[Full details → Data Dictionary](./API_REFERENCE.md#8-data-dictionary)**

---

## Quick Example

```bash
# Get Ford Focus 2018 Petrol report
curl http://localhost:8010/api/vehicle/FORD/FOCUS/2018/PE
```

Response includes: `vehicle`, `insights`, `rankings`, `failure_categories`, `top_failures`, `top_advisories`, `dangerous_defects`, `mileage_bands`

---

## When to Read Full Reference

Jump to [API_REFERENCE.md](./API_REFERENCE.md) for:
- Complete table schemas with column definitions
- Full endpoint parameter/response documentation
- All query function signatures and SQL logic
- Frontend UI feature details
- cURL/JavaScript/Python examples
