# ETL Verification: Full RFR Descriptions Update

**Date:** 2026-01-17
**Change Summary:** Updated ETL to use `rfr_insp_manual_desc` (full descriptions) instead of `rfr_desc` (truncated codes)
**Critical Level:** HIGH - This database is the foundation for all insight reports

---

## Context

The ETL script `main/generate_insights_optimized.py` was modified to populate `defect_description` columns in `top_defects` and `dangerous_defects` tables using the full human-readable descriptions from `rfr_insp_manual_desc` instead of the short codes from `rfr_desc`.

### Problem Being Solved
- **Before:** Descriptions like "across an axle", "not working", "fractured or broken"
- **After:** Full descriptions like "Brakes imbalance across an axle such that the braking effort from any wheel is less than 70% of the maximum effort recorded from the other wheel on the same axle."

---

## Files Modified

| File | Lines Changed |
|------|---------------|
| `main/generate_insights_optimized.py` | 749, 757, 823, 831, 1278, 1287 |

---

## Verification Tasks

### 1. Source Data Verification

Confirm `item_detail.csv` contains the expected columns:

```bash
# Check CSV header for required columns
head -1 data/source/item_detail.csv
```

**Expected columns must include:**
- `rfr_id`
- `rfr_desc`
- `rfr_insp_manual_desc`
- `rfr_advisory_text`

**Verify sample data exists:**
```sql
-- Run against DuckDB or load CSV directly
SELECT rfr_id, rfr_desc, rfr_insp_manual_desc
FROM read_csv_auto('data/source/item_detail.csv', delim='|')
WHERE rfr_id = 30002;
```

**Expected result for rfr_id=30002:**
- `rfr_desc`: "across an axle" (short)
- `rfr_insp_manual_desc`: "Brakes imbalance across an axle such that the braking effort from any wheel is less than 70% of the maximum effort recorded from the other wheel on the same axle." (full)

---

### 2. Code Change Verification

Verify the exact code changes in `main/generate_insights_optimized.py`:

#### Location A: Failure Defects (around line 749)

**Must contain:**
```python
COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_desc, 'Unknown') as defect_desc,
```

**Must NOT contain:**
```python
COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
```

**GROUP BY clause (around line 757) must use alias:**
```python
GROUP BY ftd.make, ftd.model, ftd.model_year, ftd.fuel_type,
         ftd.rfr_id, defect_desc, ig.item_name
```

#### Location B: Advisory Defects (around line 823)

**Must contain:**
```python
COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_advisory_text, id.rfr_desc, 'Unknown') as defect_desc,
```

**Must NOT contain:**
```python
COALESCE(id.rfr_advisory_text, id.rfr_desc, 'Unknown') as defect_desc,
```

**GROUP BY clause (around line 831) must use alias:**
```python
GROUP BY atd.make, atd.model, atd.model_year, atd.fuel_type,
         atd.rfr_id, defect_desc, ig.item_name
```

#### Location C: Dangerous Defects (around line 1278)

**Must contain:**
```python
COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_desc, 'Unknown') as defect_desc,
```

**Must NOT contain:**
```python
COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
```

**GROUP BY clause (around line 1287) must use alias:**
```python
GROUP BY dtd.make, dtd.model, dtd.model_year, dtd.fuel_type,
         dtd.rfr_id, defect_desc, ig.item_name
```

---

### 3. Database Output Verification

After running the ETL (`python main/generate_insights_optimized.py`), verify the database output:

#### Test Query 1: Specific RFR ID Check
```sql
-- Connect to: data/database/mot_insights.db
SELECT DISTINCT defect_description
FROM top_defects
WHERE rfr_id = 30002
LIMIT 1;
```

**Expected:** Full description containing "Brakes imbalance across an axle such that the braking effort..."
**Fail if:** Returns "across an axle" (short description)

#### Test Query 2: Dangerous Defects Check
```sql
SELECT DISTINCT defect_description
FROM dangerous_defects
WHERE rfr_id = 30002
LIMIT 1;
```

**Expected:** Same full description as above
**Fail if:** Returns short description

#### Test Query 3: Description Length Distribution
```sql
-- Descriptions should generally be longer now
SELECT
    CASE
        WHEN LENGTH(defect_description) < 30 THEN 'short (<30)'
        WHEN LENGTH(defect_description) < 100 THEN 'medium (30-99)'
        ELSE 'long (100+)'
    END as length_category,
    COUNT(*) as count
FROM top_defects
GROUP BY length_category
ORDER BY count DESC;
```

**Expected:** Majority should be in 'long (100+)' or 'medium (30-99)' categories
**Fail if:** Majority are in 'short (<30)' category

#### Test Query 4: Sample Random Descriptions
```sql
-- Spot check: descriptions should be human-readable sentences
SELECT DISTINCT rfr_id, defect_description
FROM top_defects
WHERE defect_type = 'failure'
ORDER BY RANDOM()
LIMIT 10;
```

**Manual check:** Descriptions should be complete sentences, not fragments like "missing", "worn", "damaged"

#### Test Query 5: Advisory Text Fallback
```sql
-- For advisories, should prefer rfr_insp_manual_desc, then rfr_advisory_text, then rfr_desc
SELECT DISTINCT rfr_id, defect_description
FROM top_defects
WHERE defect_type = 'advisory'
ORDER BY RANDOM()
LIMIT 10;
```

**Manual check:** Descriptions should be full sentences

---

### 4. Fallback Logic Verification

The COALESCE/NULLIF pattern must handle these cases:

| rfr_insp_manual_desc | rfr_desc | Expected Result |
|---------------------|----------|-----------------|
| "Full description" | "short" | "Full description" |
| "" (empty string) | "short" | "short" |
| NULL | "short" | "short" |
| NULL | NULL | "Unknown" |

**Test empty string handling:**
```sql
-- Check if any rfr_insp_manual_desc values are empty strings
SELECT COUNT(*)
FROM read_csv_auto('data/source/item_detail.csv', delim='|')
WHERE rfr_insp_manual_desc = '';
```

If count > 0, verify those RFR IDs fall back to rfr_desc in the database.

---

### 5. Regression Checks

Ensure no data was lost or corrupted:

```sql
-- Record counts should be similar to before (may vary slightly due to description grouping)
SELECT 'top_defects' as table_name, COUNT(*) as row_count FROM top_defects
UNION ALL
SELECT 'dangerous_defects', COUNT(*) FROM dangerous_defects;

-- No NULL descriptions (should all have at least 'Unknown')
SELECT COUNT(*) FROM top_defects WHERE defect_description IS NULL;
SELECT COUNT(*) FROM dangerous_defects WHERE defect_description IS NULL;

-- Expected: Both return 0

-- Check for 'Unknown' descriptions (should be minimal)
SELECT COUNT(*) as unknown_count,
       COUNT(*) * 100.0 / (SELECT COUNT(*) FROM top_defects) as unknown_pct
FROM top_defects
WHERE defect_description = 'Unknown';

-- Expected: Less than 1% unknown
```

---

### 6. Downstream Consumer Verification

These scripts read from the affected tables and should now receive full descriptions:

| Script | Purpose | Verify |
|--------|---------|--------|
| `scripts/inspection_guide/db_queries.py` | Buyer guides | Generate a sample report, check descriptions |
| `scripts/model_report_generator/db_queries.py` | Model reports | Generate a sample report |
| `scripts/article_generation/json_parser/parser.py` | Articles | Generate a sample article |
| `api/backend/queries.py` | REST API | Call API endpoint, check response |

---

### 7. Post-Verification Cleanup

Once verified, the following can be cleaned up:

1. **Drop lookup table** (if it exists):
```sql
DROP TABLE IF EXISTS rfr_descriptions;
```

2. **Simplify queries in `scripts/inspection_guide/db_queries.py`:**
   - Remove LEFT JOIN to rfr_descriptions
   - Remove COALESCE wrapper for defect_description
   - Use defect_description directly from top_defects/dangerous_defects

---

## Verification Checklist

- [ ] Source CSV contains `rfr_insp_manual_desc` column with data
- [ ] Code change A (failures): Uses `COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_desc, 'Unknown')`
- [ ] Code change B (advisories): Uses `COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_advisory_text, id.rfr_desc, 'Unknown')`
- [ ] Code change C (dangerous): Uses `COALESCE(NULLIF(id.rfr_insp_manual_desc, ''), id.rfr_desc, 'Unknown')`
- [ ] All GROUP BY clauses use `defect_desc` alias (not `id.rfr_desc`)
- [ ] ETL runs without errors
- [ ] rfr_id=30002 returns full brake imbalance description
- [ ] Majority of descriptions are 30+ characters
- [ ] No NULL defect_description values
- [ ] Less than 1% 'Unknown' descriptions
- [ ] Sample descriptions are human-readable sentences
- [ ] Downstream consumers receive full descriptions

---

## Rollback Instructions

If issues are found, revert the three COALESCE lines to:

**Failures (line 749):**
```python
COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
```

**Advisories (line 823):**
```python
COALESCE(id.rfr_advisory_text, id.rfr_desc, 'Unknown') as defect_desc,
```

**Dangerous (line 1278):**
```python
COALESCE(id.rfr_desc, 'Unknown') as defect_desc,
```

And restore GROUP BY clauses to use `id.rfr_desc` instead of `defect_desc`.

---

## Contact

Session that made changes: 2026-01-17
Original requirement: Use full `rfr_insp_manual_desc` instead of truncated `rfr_desc`
