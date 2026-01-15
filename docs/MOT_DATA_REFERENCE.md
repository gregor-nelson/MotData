# MOT Testing Data Reference Documentation

> **Purpose**: Comprehensive reference for the DVSA MOT bulk dataset to power motorwise.io failure pattern analysis.
> **Data Period**: 2023 (01/01/2023 - 31/12/2023)
> **Source**: Department for Transport / DVSA bulk data extracts

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Dataset Overview](#dataset-overview)
3. [Core Tables](#core-tables)
   - [test_result.csv](#test_resultcsv)
   - [test_item.csv](#test_itemcsv)
4. [Lookup Tables](#lookup-tables)
   - [item_detail.csv](#item_detailcsv)
   - [item_group.csv](#item_groupcsv)
   - [mdr_test_outcome.csv](#mdr_test_outcomecsv)
   - [mdr_test_type.csv](#mdr_test_typecsv)
   - [mdr_fuel_types.csv](#mdr_fuel_typescsv)
   - [mdr_rfr_location.csv](#mdr_rfr_locationcsv)
5. [Entity Relationships](#entity-relationships)
6. [Data Quality & Caveats](#data-quality--caveats)
7. [Business Logic & Calculations](#business-logic--calculations)
8. [Example Queries](#example-queries)
9. [Implementation Notes](#implementation-notes)

---

## Executive Summary

### Dataset Scale
| Metric | Value |
|--------|-------|
| Total MOT Tests | ~42 million records |
| Total Defect Records | ~89 million records |
| Avg Defects per Test | ~2.1 |
| File Format | Pipe-delimited CSV (`\|`) |
| Encoding | UTF-8 |

### Business Goal
Transform raw MOT data into actionable insights:
- "Ford Focus 2017 - Top 5 failure points with percentages"
- "62% of similar vehicles developed brake issues by 80k miles"
- Advisory-to-failure progression patterns
- Pass rates vs national average by make/model/year

---

## Dataset Overview

### File Inventory

| File | Size | Records | Purpose |
|------|------|---------|---------|
| `test_result.csv` | 3.4 GB | ~42M | MOT test outcomes with vehicle details |
| `test_item.csv` | 1.9 GB | ~89M | Individual defects/advisories per test |
| `item_detail.csv` | 3.5 MB | ~3,700 | Defect code descriptions (RfR lookup) |
| `item_group.csv` | 143 KB | ~2,500 | Hierarchical component groupings |
| `mdr_test_outcome.csv` | 132 B | 7 | Test result code lookup |
| `mdr_test_type.csv` | 146 B | 6 | Test type code lookup |
| `mdr_fuel_types.csv` | 261 B | 14 | Fuel type code lookup |
| `mdr_rfr_location.csv` | 2.7 KB | 128 | Defect location lookup |

### Data Format
- **Delimiter**: Pipe character `|`
- **Line Terminator**: `\n` (newline)
- **Header Row**: Yes (first row contains column names)
- **Date Format**: `YYYY-MM-DD` (e.g., `2023-01-15`)
- **Null Handling**: Empty string between delimiters

---

## Core Tables

### test_result.csv

The primary table containing every MOT test conducted, with vehicle information captured at time of test.

#### Schema

| Column | Type | Length | Description | Example |
|--------|------|--------|-------------|---------|
| `test_id` | INTEGER | 10 | **Primary Key** - Unique test identifier | `1994821045` |
| `vehicle_id` | INTEGER | 10 | Unique vehicle identifier (tracks same vehicle across tests) | `838565361` |
| `test_date` | DATE | 10 | Date of test (YYYY-MM-DD) | `2023-01-02` |
| `test_class_id` | CHAR | 2 | Vehicle class tested | `4` |
| `test_type` | CHAR | 2 | Type of MOT test | `NT` |
| `test_result` | CHAR | 5 | Test outcome code | `P`, `F`, `PRS` |
| `test_mileage` | INTEGER | 7 | Odometer reading at test (miles) | `179357` |
| `postcode_area` | CHAR | 2 | Geographic region (anonymised) | `NW`, `B`, `XX` |
| `make` | CHAR | 50 | Vehicle manufacturer | `TOYOTA` |
| `model` | CHAR | 50 | Vehicle model | `PRIUS +` |
| `colour` | CHAR | 16 | Vehicle colour | `WHITE` |
| `fuel_type` | CHAR | 2 | Fuel type code | `HY`, `PE`, `DI` |
| `cylinder_capacity` | INTEGER | 10 | Engine size in cc | `1798` |
| `first_use_date` | DATE | 10 | Vehicle first registration date | `2016-06-17` |

#### Sample Records
```
test_id|vehicle_id|test_date|test_class_id|test_type|test_result|test_mileage|postcode_area|make|model|colour|fuel_type|cylinder_capacity|first_use_date
1994821045|838565361|2023-01-02|4|NT|P|179357|NW|TOYOTA|PRIUS +|WHITE|HY|1798|2016-06-17
358005195|484499974|2023-01-01|4|NT|P|300072|B|TOYOTA|PRIUS|RED|HY|1500|2008-09-13
133665147|606755010|2023-01-02|4|NT|F|65810|SE|TOYOTA|PRIUS|SILVER|HY|1497|2007-03-28
```

#### Key Notes
- **`vehicle_id`**: Critical for tracking same vehicle across multiple tests (enables progression analysis)
- **`test_mileage`**: Zero or blank means reading not obtained (e.g., aborted test)
- **`postcode_area`**: Regions with <5 active VTS sites merged to `XX` for anonymity
- **`make`/`model`**: Sourced from DVSA vehicle dataset; `UNCLASSIFIED` if no valid record

---

### test_item.csv

Contains individual defects, advisories, and failure items recorded during each test. One test may have multiple items (or none if clean pass).

#### Schema

| Column | Type | Length | Description | Example |
|--------|------|--------|-------------|---------|
| `test_id` | INTEGER | 10 | **Foreign Key** → test_result.test_id | `703671925` |
| `rfr_id` | INTEGER | 4 | Reason for Rejection ID → item_detail.rfr_id | `30305` |
| `rfr_type_code` | CHAR | 1 | Defect severity type | `F`, `P`, `A`, `M` |
| `location_id` | INTEGER | 4 | Location on vehicle → mdr_rfr_location.id | `7` |
| `dangerous_mark` | CHAR | 1 | Pre-May 2018 dangerous marker | `Y`, `` |

#### RfR Type Codes

| Code | Name | Description | Causes Failure? |
|------|------|-------------|-----------------|
| `F` | **Fail** | Major or dangerous defect | ✅ Yes |
| `P` | **PRS** | Item was failing, repaired within 1 hour before result recorded | ✅ Initially (then pass) |
| `A` | **Advisory** | Warning item, not currently failing | ❌ No |
| `M` | **Minor** | Minor defect (post-May 2018) | ❌ No |

#### Sample Records
```
test_id|rfr_id|rfr_type_code|location_id|dangerous_mark
703671925|30305|A|7|
703671925|30823|M|243|
618374953|31194|A|27|
405132523|31043|F|9|
191890093|30616|F|37|
```

#### Key Notes
- A single `test_id` may appear multiple times (one row per defect)
- Tests with no defects will have NO rows in this table
- `dangerous_mark` only populated pre-May 2018; post-2018 use `rfr_deficiency_category` in item_detail

---

## Lookup Tables

### item_detail.csv

Master list of all possible defect codes (Reasons for Rejection) with descriptions.

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `rfr_id` | INTEGER | **Primary Key (with test_class_id)** - Defect code |
| `test_class_id` | CHAR(2) | Vehicle class this applies to |
| `test_item_id` | INTEGER | Parent test item → item_group.test_item_id |
| `minor_item` | CHAR(1) | `Y`/`N` - Qualifies for free partial retest |
| `rfr_deficiency_category` | CHAR(2) | EU category (see below) |
| `rfr_desc` | CHAR(250) | Short description (printed on VT30 fail doc) |
| `rfr_loc_marker` | CHAR(1) | `Y`/`N` - Requires location details |
| `rfr_insp_manual_desc` | CHAR(500) | Full inspection manual description |
| `rfr_advisory_text` | CHAR(250) | Advisory text (printed on VT20 pass cert) |
| `test_item_set_section_id` | INTEGER | **Top-level category** → item_group |

#### Deficiency Categories (rfr_deficiency_category)

| Code | Meaning | Notes |
|------|---------|-------|
| `PE` | Pre-EU Directive | Tests before 20th May 2018 |
| `MI` | Minor | Does not cause failure |
| `MA` | Major | Causes failure |
| `D` | Dangerous | Causes failure, vehicle unsafe |

#### Sample Records
```
rfr_id|test_class_id|test_item_id|minor_item|rfr_deficiency_category|rfr_desc|rfr_loc_marker|rfr_insp_manual_desc|rfr_advisory_text|test_item_set_section_id
4|1|3|Y|Pre-EU Directive|missing|N|an obligatory lamp missing||1
5|1|3|Y|Pre-EU Directive|damaged and function impaired|N|so damaged or deteriorated that its function is impaired|damaged but function not impaired|1
```

---

### item_group.csv

Hierarchical grouping of test items. Enables rolling up defects to categories like "Brakes", "Suspension", "Lights".

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `test_item_id` | INTEGER | **Primary Key (with test_class_id)** |
| `test_class_id` | CHAR(2) | Vehicle class |
| `parent_id` | INTEGER | Parent in hierarchy (0 = top level "Vehicle") |
| `test_item_set_section_id` | INTEGER | Top-level section ID |
| `item_name` | CHAR(100) | Human-readable name |

#### Hierarchy Structure
```
Vehicle (test_item_id=0)
├── Brakes (test_item_set_section_id=X)
│   ├── Service brake
│   │   ├── Front axle
│   │   │   └── [specific RfRs]
│   │   └── Rear axle
│   └── Parking brake
├── Suspension
│   ├── Front suspension
│   └── Rear suspension
├── Lighting and signalling
│   ├── Position lamps
│   ├── Headlamps
│   └── Stop lamps
└── [etc.]
```

#### Sample Records
```
test_item_id|test_class_id|parent_id|test_item_set_section_id|item_name
0|4|0|0|Vehicle
1|4|0|1|Brakes
2|4|1|1|Service brake
3|4|2|1|Front axle
```

---

### mdr_test_outcome.csv

Complete lookup for test result codes.

| result_code | result | Description |
|-------------|--------|-------------|
| `P` | Passed | Test passed |
| `F` | Failed | Test failed |
| `PRS` | Pass with Rectification at Station | Failed initially, fixed within 1 hour |
| `ABA` | Abandoned | Unsafe to continue or items can't be inspected |
| `ABR` | Aborted | Equipment problem, no fee charged |
| `ABRVE` | Aborted by VE | Aborted by Vehicle Examiner |
| `R` | Refused | Test refused |

---

### mdr_test_type.csv

Complete lookup for test type codes.

| type_code | test_type | Description | Use in Analysis |
|-----------|-----------|-------------|-----------------|
| `NT` | Normal Test | Full initial MOT test | ✅ Primary |
| `RT` | Re-Test | Full retest of vehicle | Secondary |
| `PL` | Partial Retest Left VTS | Half-fee retest, vehicle left and returned | Secondary |
| `PV` | Partial Retest Repaired at VTS | Free retest, vehicle stayed for repair | Secondary |
| `ES` | Statutory Appeal | Appeal test | Exclude |
| `EI` | Inverted Appeal | Appeal test | Exclude |

---

### mdr_fuel_types.csv

Complete lookup for fuel type codes.

| type_code | fuel_type | Common Makes |
|-----------|-----------|--------------|
| `PE` | Petrol | Most common |
| `DI` | Diesel | Vans, SUVs, older vehicles |
| `HY` | Hybrid Electric (Clean) | Toyota Prius, Lexus |
| `EL` | Electric | Tesla, Nissan Leaf |
| `ED` | Electric Diesel | Plug-in hybrid diesel |
| `CN` | Compressed Natural Gas (CNG) | Rare |
| `LN` | Liquefied Natural Gas (LNG) | Commercial |
| `LP` | Liquefied Petroleum Gas (LPG) | Converted vehicles |
| `GA` | Gas | Generic gas |
| `GB` | Gas Bi-Fuel | Dual fuel |
| `GD` | Gas Diesel | Dual fuel diesel |
| `FC` | Fuel Cells | Hydrogen (rare) |
| `ST` | Steam | Historic vehicles |
| `OT` | Other | Unclassified |

---

### mdr_rfr_location.csv

Location identifiers for where on vehicle a defect was found.

#### Schema
| Column | Description |
|--------|-------------|
| `id` | Location ID (referenced by test_item.location_id) |
| `lateral` | Left/right position: Nearside, Offside, Centre, Inner, Outer |
| `longitudinal` | Front/rear position: Front, Rear |
| `vertical` | Up/down position: Upper, Lower |

#### Common Locations

| id | lateral | longitudinal | vertical | Meaning |
|----|---------|--------------|----------|---------|
| 1 | | | | Unspecified |
| 3 | Nearside | | | Left side (UK passenger side) |
| 5 | Offside | | | Right side (UK driver side) |
| 7 | | Front | | Front of vehicle |
| 9 | | Rear | | Rear of vehicle |
| 13 | Nearside | Rear | | Left rear |
| 17 | Offside | Rear | | Right rear |
| 25 | Nearside | Front | | Left front |
| 27 | Offside | Front | | Right front |

#### UK Vehicle Orientation
```
         FRONT
    ┌─────────────┐
    │  25     27  │   25 = Nearside Front (passenger)
    │  NF     OF  │   27 = Offside Front (driver)
    │             │
    │  13     17  │   13 = Nearside Rear (passenger)
    │  NR     OR  │   17 = Offside Rear (driver)
    └─────────────┘
         REAR
```

---

## Entity Relationships

### ER Diagram (Text)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  test_result    │       │   test_item     │       │  item_detail    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ test_id (PK)    │──1:N──│ test_id (FK)    │       │ rfr_id (PK)     │
│ vehicle_id      │       │ rfr_id (FK)     │──N:1──│ test_class_id   │
│ test_date       │       │ rfr_type_code   │       │ test_item_id    │──┐
│ test_class_id   │       │ location_id(FK) │       │ rfr_desc        │  │
│ test_type       │       │ dangerous_mark  │       │ test_item_set_  │  │
│ test_result     │       └────────┬────────┘       │   section_id    │  │
│ test_mileage    │                │                └─────────────────┘  │
│ postcode_area   │                │                                     │
│ make            │                │N:1             ┌─────────────────┐  │
│ model           │                │                │  item_group     │  │
│ colour          │                ▼                ├─────────────────┤  │
│ fuel_type       │       ┌─────────────────┐       │ test_item_id(PK)│◄─┘
│ cylinder_cap    │       │ mdr_rfr_location│       │ test_class_id   │
│ first_use_date  │       ├─────────────────┤       │ parent_id       │──┐
└─────────────────┘       │ id (PK)         │       │ item_name       │  │
                          │ lateral         │       └────────┬────────┘  │
                          │ longitudinal    │                │           │
                          │ vertical        │                └───────────┘
                          └─────────────────┘                (self-ref hierarchy)
```

### Join Paths

#### Get defect details for a test
```sql
test_result
  → test_item ON test_result.test_id = test_item.test_id
  → item_detail ON test_item.rfr_id = item_detail.rfr_id
                AND test_result.test_class_id = item_detail.test_class_id
```

#### Get top-level category for a defect
```sql
item_detail
  → item_group ON item_detail.test_item_set_section_id = item_group.test_item_id
              AND item_detail.test_class_id = item_group.test_class_id
```

#### Get defect location description
```sql
test_item
  → mdr_rfr_location ON test_item.location_id = mdr_rfr_location.id
```

---

## Data Quality & Caveats

### Critical Issues

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **1971 Date Anomaly** | Vehicles with unknown manufacture date assigned `01/01/1971` | Filter or flag `first_use_date = '1971-01-01'` |
| **Hybrid Fuel Misrecording** | Pre-2022 hybrids often recorded as petrol/diesel (especially Toyota Prius) | 2022+ data corrected; consider make/model override |
| **Mileage in Kilometres** | Pre-2022 data may contain km instead of miles | 2022+ converted (×0.6213711922); older data uncorrected |
| **Location ID Errors** | Pre-2022 location IDs incorrect | Only 2022+ location data reliable |
| **Incomplete Pre-2006** | MOT computerisation completed 01/04/2006 | 2005-2006 data incomplete |

### Recommended Filters for Analysis

```sql
-- Standard filter for failure rate analysis
WHERE test_type = 'NT'                    -- Normal tests only
  AND test_result IN ('P', 'F', 'PRS')    -- Completed tests only
  AND test_class_id = '4'                 -- Class 4 (cars) - adjust as needed
  AND first_use_date != '1971-01-01'      -- Exclude unknown dates
  AND test_mileage > 0                    -- Valid mileage reading
```

### Vehicle Classes

| Class | Description | First Test Age |
|-------|-------------|----------------|
| 1 | Motorcycles up to 200cc | 3 years |
| 2 | All motorcycles | 3 years |
| 3 | 3-wheelers ≤450kg | 3 years |
| **4** | **Cars, light vehicles ≤8 passengers** | **3 years** |
| 5 | Passenger vehicles 9-12 seats | 1 year |
| 7 | Goods vehicles 3,000-3,500kg | 3 years |
| 0 | Pre-computerisation records | N/A |

**Class 4 is the primary focus for consumer vehicle analysis.**

---

## Business Logic & Calculations

### Official DVSA Failure Rate Formulas

#### Initial Failure Rate
"What percentage of vehicles had at least one failure item when first presented?"

```sql
Initial Failure Rate = (COUNT(F) + COUNT(PRS)) / COUNT(NT tests with P/F/PRS result)
```

#### Final Failure Rate
"What percentage of vehicles ultimately failed their MOT?"

```sql
Final Failure Rate = COUNT(F) / COUNT(NT tests with P/F/PRS result)
```

### Counting Failures by Category

Count distinct tests with failure items, not total failure items:

```sql
-- Correct: Count tests with brake failures
SELECT COUNT(DISTINCT test_id)
FROM test_item
WHERE rfr_type_code IN ('F', 'P')
  AND rfr_id IN (SELECT rfr_id FROM item_detail WHERE test_item_set_section_id = [BRAKES_ID])

-- Incorrect: This counts total brake failure items (inflated)
SELECT COUNT(*) FROM test_item WHERE ...
```

### Vehicle Age Calculation

```sql
-- Age at test in years
DATEDIFF(year, first_use_date, test_date) AS vehicle_age_years

-- Or derive model year from first_use_date
YEAR(first_use_date) AS model_year
```

### Mileage Bands

Suggested bands for analysis:

| Band | Range | Typical Age |
|------|-------|-------------|
| Low | 0 - 30,000 | 1-3 years |
| Medium-Low | 30,001 - 60,000 | 3-5 years |
| Medium | 60,001 - 90,000 | 5-7 years |
| Medium-High | 90,001 - 120,000 | 7-10 years |
| High | 120,001 - 150,000 | 10-12 years |
| Very High | 150,001+ | 12+ years |

---

## Example Queries

### 1. Top 10 Failure Categories for Ford Focus 2017

```sql
SELECT
    g.item_name AS failure_category,
    COUNT(DISTINCT t.test_id) AS tests_with_failure,
    ROUND(100.0 * COUNT(DISTINCT t.test_id) /
        (SELECT COUNT(*) FROM test_result
         WHERE make = 'FORD' AND model LIKE 'FOCUS%'
         AND YEAR(first_use_date) = 2017
         AND test_type = 'NT' AND test_result IN ('P','F','PRS')), 2) AS failure_pct
FROM test_result r
JOIN test_item t ON r.test_id = t.test_id
JOIN item_detail d ON t.rfr_id = d.rfr_id AND r.test_class_id = d.test_class_id
JOIN item_group g ON d.test_item_set_section_id = g.test_item_id AND d.test_class_id = g.test_class_id
WHERE r.make = 'FORD'
  AND r.model LIKE 'FOCUS%'
  AND YEAR(r.first_use_date) = 2017
  AND r.test_type = 'NT'
  AND r.test_result IN ('F', 'PRS')
  AND t.rfr_type_code IN ('F', 'P')
GROUP BY g.item_name
ORDER BY tests_with_failure DESC
LIMIT 10;
```

### 2. Pass Rate by Make/Model vs National Average

```sql
WITH national AS (
    SELECT
        ROUND(100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*), 2) AS national_pass_rate
    FROM test_result
    WHERE test_type = 'NT' AND test_result IN ('P','F','PRS') AND test_class_id = '4'
),
by_vehicle AS (
    SELECT
        make,
        model,
        YEAR(first_use_date) AS model_year,
        COUNT(*) AS total_tests,
        ROUND(100.0 * SUM(CASE WHEN test_result = 'P' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pass_rate
    FROM test_result
    WHERE test_type = 'NT' AND test_result IN ('P','F','PRS') AND test_class_id = '4'
    GROUP BY make, model, YEAR(first_use_date)
    HAVING COUNT(*) >= 1000  -- Minimum sample size
)
SELECT
    v.*,
    n.national_pass_rate,
    v.pass_rate - n.national_pass_rate AS vs_national
FROM by_vehicle v, national n
ORDER BY total_tests DESC;
```

### 3. Failure Rate by Mileage Band

```sql
SELECT
    CASE
        WHEN test_mileage <= 30000 THEN '0-30k'
        WHEN test_mileage <= 60000 THEN '30-60k'
        WHEN test_mileage <= 90000 THEN '60-90k'
        WHEN test_mileage <= 120000 THEN '90-120k'
        WHEN test_mileage <= 150000 THEN '120-150k'
        ELSE '150k+'
    END AS mileage_band,
    COUNT(*) AS total_tests,
    SUM(CASE WHEN test_result = 'F' THEN 1 ELSE 0 END) AS failures,
    ROUND(100.0 * SUM(CASE WHEN test_result = 'F' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate
FROM test_result
WHERE test_type = 'NT'
  AND test_result IN ('P','F','PRS')
  AND test_class_id = '4'
  AND test_mileage > 0
  AND make = 'FORD' AND model LIKE 'FOCUS%'
GROUP BY mileage_band
ORDER BY MIN(test_mileage);
```

### 4. Advisory-to-Failure Progression (Same Vehicle Over Time)

```sql
-- Find vehicles that had an advisory, then later failed on same component
WITH advisory_tests AS (
    SELECT DISTINCT
        r.vehicle_id,
        r.test_date AS advisory_date,
        d.test_item_set_section_id AS component,
        r.test_mileage AS advisory_mileage
    FROM test_result r
    JOIN test_item t ON r.test_id = t.test_id
    JOIN item_detail d ON t.rfr_id = d.rfr_id AND r.test_class_id = d.test_class_id
    WHERE t.rfr_type_code = 'A'
      AND r.test_type = 'NT'
),
failure_tests AS (
    SELECT DISTINCT
        r.vehicle_id,
        r.test_date AS failure_date,
        d.test_item_set_section_id AS component,
        r.test_mileage AS failure_mileage
    FROM test_result r
    JOIN test_item t ON r.test_id = t.test_id
    JOIN item_detail d ON t.rfr_id = d.rfr_id AND r.test_class_id = d.test_class_id
    WHERE t.rfr_type_code IN ('F', 'P')
      AND r.test_type = 'NT'
)
SELECT
    g.item_name AS component,
    COUNT(*) AS progression_count,
    AVG(DATEDIFF(day, a.advisory_date, f.failure_date)) AS avg_days_to_failure,
    AVG(f.failure_mileage - a.advisory_mileage) AS avg_miles_to_failure
FROM advisory_tests a
JOIN failure_tests f ON a.vehicle_id = f.vehicle_id
                     AND a.component = f.component
                     AND f.failure_date > a.advisory_date
JOIN item_group g ON a.component = g.test_item_id AND g.test_class_id = '4'
GROUP BY g.item_name
HAVING COUNT(*) >= 100
ORDER BY progression_count DESC;
```

### 5. Top-Level Category IDs for Class 4 Vehicles

```sql
-- Get the test_item_set_section_id values for major categories
SELECT DISTINCT
    g.test_item_id,
    g.item_name
FROM item_group g
WHERE g.test_class_id = '4'
  AND g.parent_id = 0
  AND g.test_item_id != 0
ORDER BY g.test_item_id;
```

---

## Implementation Notes

### Recommended Database

Given the dataset size (~5.5GB, 130M+ total rows), use:
- **PostgreSQL** (recommended) - Free, handles large datasets well
- **MySQL** - Good alternative
- **SQLite** - Possible for single-user analysis, may be slow
- **DuckDB** - Excellent for analytical queries on CSV directly

**NOT recommended**: MS Access, Excel (will crash or truncate)

### Suggested Indexes

```sql
-- test_result
CREATE INDEX idx_tr_make_model ON test_result(make, model);
CREATE INDEX idx_tr_test_type_result ON test_result(test_type, test_result);
CREATE INDEX idx_tr_vehicle_id ON test_result(vehicle_id);
CREATE INDEX idx_tr_first_use_date ON test_result(first_use_date);

-- test_item
CREATE INDEX idx_ti_test_id ON test_item(test_id);
CREATE INDEX idx_ti_rfr_id ON test_item(rfr_id);
CREATE INDEX idx_ti_rfr_type ON test_item(rfr_type_code);

-- item_detail
CREATE INDEX idx_id_section ON item_detail(test_item_set_section_id, test_class_id);
```

### Import Commands (MySQL)

```sql
LOAD DATA LOCAL INFILE 'test_result.csv'
INTO TABLE test_result
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'test_item.csv'
INTO TABLE test_item
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
```

### Import Commands (PostgreSQL)

```sql
COPY test_result FROM 'test_result.csv' DELIMITER '|' CSV HEADER;
COPY test_item FROM 'test_item.csv' DELIMITER '|' CSV HEADER;
```

### Memory Considerations

- Full dataset requires ~8GB RAM for comfortable querying
- Consider partitioning by year or make for large-scale analysis
- Pre-aggregate common queries into summary tables

---

## Appendix: Quick Reference Card

### Filter for Standard Analysis
```sql
WHERE test_type = 'NT' AND test_result IN ('P','F','PRS') AND test_class_id = '4'
```

### Failure Items Only
```sql
WHERE rfr_type_code IN ('F', 'P')  -- F=Fail, P=PRS (was failing)
```

### Advisory Items Only
```sql
WHERE rfr_type_code = 'A'
```

### Join Path: Test → Defect Description
```sql
FROM test_result r
JOIN test_item t ON r.test_id = t.test_id
JOIN item_detail d ON t.rfr_id = d.rfr_id AND r.test_class_id = d.test_class_id
```

### Join Path: Defect → Top-Level Category
```sql
JOIN item_group g ON d.test_item_set_section_id = g.test_item_id
                 AND d.test_class_id = g.test_class_id
```

---

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2023-12-31 | Claude/Gregor | Initial comprehensive documentation |

---

*This document serves as the authoritative reference for MOT data analysis. For questions about the source data, refer to the official DVSA user guide: `mot-testing-data-user-guide-v5.1.odt`*
