"""
Known Issues Detection Module

Identifies model-specific defects that occur at statistically elevated rates
compared to a composite baseline of comparable vehicles.

Methodology:
- Composite baseline = National avg (50%) + Same year avg (30%) + Same make avg (20%)
- Defects are grouped by component for baseline calculation to prevent fragmentation
- Known issue threshold: 2x+ baseline
- Major known issue threshold: 3x+ baseline
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from collections import defaultdict

from baseline_groups import get_baseline_group, get_all_groups, get_group_display_name

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "source" / "data" / "mot_insights.db"


@dataclass
class GroupedKnownIssue:
    """Represents a component group with elevated defect rates."""
    group_id: str                    # e.g., "brake_imbalance_effort"
    group_name: str                  # e.g., "Brake Imbalance/Effort"
    category_name: str               # e.g., "Brakes"
    model_rate: float                # Combined rate for all variants
    composite_baseline: float        # Grouped baseline rate
    ratio: float                     # model_rate / composite_baseline
    total_occurrences: int           # Sum of all variant occurrences
    variant_count: int               # Number of MOT wording variants
    variant_descriptions: list[str]  # Individual MOT wordings (for transparency)
    typical_mileage: Optional[str] = None
    is_premature: bool = False
    affected_years: Optional[list[int]] = None

    @property
    def severity(self) -> str:
        """Classify severity based on ratio."""
        if self.ratio >= 3.0:
            return "major"
        elif self.ratio >= 2.0:
            return "known"
        elif self.ratio >= 1.5:
            return "elevated"
        return "normal"


@dataclass
class KnownIssue:
    """Represents a single known issue for a vehicle."""
    defect_description: str
    category_name: str
    model_rate: float          # Occurrence % on this model
    composite_baseline: float  # Weighted average of comparisons
    ratio: float               # model_rate / composite_baseline
    occurrence_count: int
    baseline_group: Optional[str] = None  # Component group used for baseline (for transparency)
    typical_mileage: Optional[str] = None
    is_premature: bool = False
    affected_years: Optional[list[int]] = None

    @property
    def severity(self) -> str:
        """Classify severity based on ratio."""
        if self.ratio >= 3.0:
            return "major"
        elif self.ratio >= 2.0:
            return "known"
        elif self.ratio >= 1.5:
            return "elevated"
        return "normal"


@dataclass
class SystemSummary:
    """Category-level failure summary."""
    category_name: str
    model_percentage: float
    national_percentage: float
    ratio: float

    @property
    def is_elevated(self) -> bool:
        return self.ratio > 1.25


@dataclass
class KnownIssuesReport:
    """Complete known issues report for a vehicle."""
    make: str
    model: str
    total_tests: int

    # Grouped component issues (primary - aggregated by component group)
    grouped_major_issues: list[GroupedKnownIssue]    # 3x+ baseline
    grouped_known_issues: list[GroupedKnownIssue]    # 2x-3x baseline
    grouped_elevated_items: list[GroupedKnownIssue]  # 1.5x-2x baseline

    # Individual issues (for ungrouped defects only)
    major_issues: list[KnownIssue]      # 3x+ baseline
    known_issues: list[KnownIssue]      # 2x-3x baseline
    elevated_items: list[KnownIssue]    # 1.5x-2x baseline

    # System-level summary
    system_summary: list[SystemSummary]

    # Year recommendations
    best_years: list[dict]
    worst_years: list[dict]


def get_db_connection():
    """Create read-only database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def compute_national_baselines(conn, total_national_tests: int) -> dict:
    """
    Compute national occurrence rate per defect as percentage of all tests.
    Returns dict: {defect_description: rate_percentage}
    """
    cursor = conn.execute("""
        SELECT
            defect_description,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE defect_type = 'failure'
        GROUP BY defect_description
        HAVING total_occurrences >= 100
    """)

    return {
        row["defect_description"]: (row["total_occurrences"] / total_national_tests * 100)
        for row in cursor.fetchall()
    }


def compute_year_baselines(conn, model_year: int) -> dict:
    """
    Compute occurrence rate per defect for a specific model year.
    Returns dict: {defect_description: rate_percentage}
    """
    # Get total tests for this model year
    cursor = conn.execute("""
        SELECT SUM(total_tests) as total FROM vehicle_insights WHERE model_year = ?
    """, (model_year,))
    year_total_tests = cursor.fetchone()["total"] or 1

    cursor = conn.execute("""
        SELECT
            defect_description,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE defect_type = 'failure'
            AND model_year = ?
        GROUP BY defect_description
    """, (model_year,))

    return {
        row["defect_description"]: (row["total_occurrences"] / year_total_tests * 100)
        for row in cursor.fetchall()
    }


def compute_make_baselines(conn, make: str) -> dict:
    """
    Compute occurrence rate per defect for a manufacturer.
    Returns dict: {defect_description: rate_percentage}
    """
    # Get total tests for this manufacturer
    cursor = conn.execute("""
        SELECT SUM(total_tests) as total FROM vehicle_insights WHERE make = ?
    """, (make,))
    make_total_tests = cursor.fetchone()["total"] or 1

    cursor = conn.execute("""
        SELECT
            defect_description,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE defect_type = 'failure'
            AND make = ?
        GROUP BY defect_description
    """, (make,))

    return {
        row["defect_description"]: (row["total_occurrences"] / make_total_tests * 100)
        for row in cursor.fetchall()
    }


def compute_national_category_baselines(conn) -> dict:
    """
    Compute national average failure percentage per category.
    Returns dict: {category_name: avg_percentage}
    """
    cursor = conn.execute("""
        SELECT
            category_name,
            AVG(failure_percentage) as avg_pct
        FROM failure_categories
        GROUP BY category_name
    """)

    return {row["category_name"]: row["avg_pct"] for row in cursor.fetchall()}


def compute_grouped_baselines(individual_baselines: dict) -> dict:
    """
    Aggregate individual defect baselines into component group baselines.

    For each defect in a group, sums the rates to get the group's total rate.
    This ensures we compare against all variants of a component defect,
    not just the specific wording variant.

    Args:
        individual_baselines: dict of {defect_description: rate_percentage}

    Returns:
        dict of {group_name: combined_rate_percentage}
    """
    group_totals = defaultdict(float)

    for defect, rate in individual_baselines.items():
        group = get_baseline_group(defect)
        if group:
            group_totals[group] += rate

    return dict(group_totals)


def aggregate_model_defects_by_group(
    model_defects: list[dict],
    model_total_tests: int
) -> dict[str, dict]:
    """
    Aggregate individual defects into component groups.

    Args:
        model_defects: List of defect dicts with defect_description, category_name, total_occurrences
        model_total_tests: Total number of MOT tests for this model

    Returns:
        dict: {group_id: {occurrences, rate_pct, variants, category}}
    """
    groups = defaultdict(lambda: {"occurrences": 0, "variants": [], "category": None})

    for defect in model_defects:
        group = get_baseline_group(defect["defect_description"])
        if group:
            groups[group]["occurrences"] += defect["total_occurrences"]
            groups[group]["variants"].append(defect["defect_description"])
            # Use first category found (all variants should be same category)
            if groups[group]["category"] is None:
                groups[group]["category"] = defect["category_name"]

    # Calculate rates
    for group_id, data in groups.items():
        data["rate_pct"] = (data["occurrences"] / model_total_tests * 100) if model_total_tests > 0 else 0

    return dict(groups)


def get_model_defects(conn, make: str, model: str, model_total_tests: int) -> list[dict]:
    """
    Get aggregated defect data for a make/model across all years.
    Calculates rate as percentage of total tests.
    """
    cursor = conn.execute("""
        SELECT
            defect_description,
            category_name,
            SUM(occurrence_count) as total_occurrences
        FROM top_defects
        WHERE make = ? AND model = ?
            AND defect_type = 'failure'
        GROUP BY defect_description, category_name
        ORDER BY total_occurrences DESC
    """, (make, model))

    results = []
    for row in cursor.fetchall():
        rate = (row["total_occurrences"] / model_total_tests * 100) if model_total_tests > 0 else 0
        results.append({
            "defect_description": row["defect_description"],
            "category_name": row["category_name"],
            "total_occurrences": row["total_occurrences"],
            "rate_pct": rate
        })
    return results


def get_model_categories(conn, make: str, model: str) -> list[dict]:
    """
    Get category-level failure breakdown for a make/model.
    """
    cursor = conn.execute("""
        SELECT
            category_name,
            SUM(failure_count) as total_failures,
            AVG(failure_percentage) as avg_pct
        FROM failure_categories
        WHERE make = ? AND model = ?
        GROUP BY category_name
        ORDER BY total_failures DESC
    """, (make, model))

    return [dict(row) for row in cursor.fetchall()]


def get_mileage_context(conn, make: str, model: str) -> dict:
    """
    Get mileage spike data per category.
    Returns dict: {category_name: {spike_band, spike_pct, is_premature}}
    """
    cursor = conn.execute("""
        SELECT
            category_name,
            spike_mileage_band,
            spike_increase_pct
        FROM component_mileage_thresholds
        WHERE make = ? AND model = ?
            AND spike_mileage_band IS NOT NULL
            AND spike_increase_pct > 20
        ORDER BY spike_increase_pct DESC
    """, (make, model))

    result = {}
    for row in cursor.fetchall():
        cat = row["category_name"]
        band = row["spike_mileage_band"]
        # Consider premature if spike is in early bands
        is_premature = band in ("0-30k", "30-60k")

        if cat not in result:
            result[cat] = {
                "spike_band": band,
                "spike_pct": row["spike_increase_pct"],
                "is_premature": is_premature
            }

    return result


def get_defect_by_year(conn, make: str, model: str, defect_description: str) -> list[dict]:
    """
    Get occurrence rate of a specific defect across model years.
    Used to identify affected year ranges.
    """
    cursor = conn.execute("""
        SELECT
            model_year,
            AVG(occurrence_percentage) as pct,
            SUM(occurrence_count) as occurrences
        FROM top_defects
        WHERE make = ? AND model = ?
            AND defect_description = ?
            AND defect_type = 'failure'
        GROUP BY model_year
        HAVING occurrences >= 10
        ORDER BY model_year
    """, (make, model, defect_description))

    return [dict(row) for row in cursor.fetchall()]


def get_year_pass_rates(conn, make: str, model: str) -> list[dict]:
    """
    Get pass rates by model year, sorted by pass rate descending.
    """
    cursor = conn.execute("""
        SELECT
            model_year,
            SUM(total_tests) as total_tests,
            ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
        FROM vehicle_insights
        WHERE make = ? AND model = ?
        GROUP BY model_year
        HAVING total_tests >= 100
        ORDER BY pass_rate DESC
    """, (make, model))

    return [dict(row) for row in cursor.fetchall()]


def identify_affected_years(year_data: list[dict], overall_avg: float) -> list[int]:
    """
    Identify which years have elevated rates (above overall average).
    """
    affected = []
    for item in year_data:
        if item["pct"] > overall_avg * 1.2:  # 20% above average
            affected.append(item["model_year"])
    return sorted(affected)


def compute_composite_baseline(
    defect: str,
    national_baselines: dict,
    year_baselines: dict,
    make_baselines: dict,
    grouped_national: dict = None,
    grouped_year: dict = None,
    grouped_make: dict = None
) -> tuple[float, Optional[str]]:
    """
    Compute weighted composite baseline for a defect.

    If the defect belongs to a component group, uses the grouped baseline
    (sum of all variants) to prevent baseline fragmentation.

    Weights:
    - National: 50%
    - Same year: 30%
    - Same manufacturer: 20%

    Falls back to national if year/make data unavailable.

    Returns:
        tuple of (baseline_rate, group_name or None)
    """
    # Check if this defect belongs to a component group
    group = get_baseline_group(defect)

    if group and grouped_national:
        # Use grouped baselines for accurate comparison
        national = grouped_national.get(group, 0)
        year = grouped_year.get(group, national) if grouped_year else national
        make = grouped_make.get(group, national) if grouped_make else national
    else:
        # Use individual baselines (ungrouped defect or no grouped data)
        national = national_baselines.get(defect, 0)
        year = year_baselines.get(defect, national)
        make = make_baselines.get(defect, national)

    if national == 0:
        return 0, group

    composite = (national * 0.5) + (year * 0.3) + (make * 0.2)
    return composite, group


def generate_known_issues_report(make: str, model: str) -> Optional[KnownIssuesReport]:
    """
    Generate a complete known issues report for a vehicle.

    Args:
        make: Vehicle make (e.g., "FORD")
        model: Vehicle model (e.g., "FOCUS")

    Returns:
        KnownIssuesReport or None if insufficient data
    """
    make = make.upper()
    model = model.upper()

    with get_db_connection() as conn:
        # Get total tests for this model
        cursor = conn.execute("""
            SELECT SUM(total_tests) as total_tests
            FROM vehicle_insights
            WHERE make = ? AND model = ?
        """, (make, model))
        row = cursor.fetchone()

        if not row or not row["total_tests"]:
            return None

        total_tests = row["total_tests"]

        # Get national total tests
        cursor = conn.execute("SELECT SUM(total_tests) as total FROM vehicle_insights")
        national_total_tests = cursor.fetchone()["total"]

        # Get representative model year for year baseline
        # (use the year with the most tests)
        cursor = conn.execute("""
            SELECT model_year, SUM(total_tests) as tests
            FROM vehicle_insights
            WHERE make = ? AND model = ?
            GROUP BY model_year
            ORDER BY tests DESC
            LIMIT 1
        """, (make, model))
        primary_year = cursor.fetchone()["model_year"]

        # Compute individual baselines (now using occurrence/tests rate)
        national_baselines = compute_national_baselines(conn, national_total_tests)
        year_baselines = compute_year_baselines(conn, primary_year)
        make_baselines = compute_make_baselines(conn, make)
        national_category_baselines = compute_national_category_baselines(conn)

        # Compute grouped baselines to prevent fragmentation
        grouped_national = compute_grouped_baselines(national_baselines)
        grouped_year = compute_grouped_baselines(year_baselines)
        grouped_make = compute_grouped_baselines(make_baselines)

        # Get model data
        model_defects = get_model_defects(conn, make, model, total_tests)
        model_categories = get_model_categories(conn, make, model)
        mileage_context = get_mileage_context(conn, make, model)
        year_pass_rates = get_year_pass_rates(conn, make, model)

        # =================================================================
        # GROUPED DEFECTS: Aggregate by component group, then compare
        # =================================================================
        grouped_model_data = aggregate_model_defects_by_group(model_defects, total_tests)

        grouped_major_issues = []
        grouped_known_issues = []
        grouped_elevated_items = []

        for group_id, group_data in grouped_model_data.items():
            model_rate = group_data["rate_pct"]
            total_occurrences = group_data["occurrences"]
            variants = group_data["variants"]
            category = group_data["category"]

            # Skip if insufficient data (sum of all variants)
            if total_occurrences < 50:
                continue

            # Get grouped baseline (composite of national, year, make)
            national_rate = grouped_national.get(group_id, 0)
            year_rate = grouped_year.get(group_id, national_rate)
            make_rate = grouped_make.get(group_id, national_rate)

            if national_rate == 0:
                continue

            # Composite baseline: 50% national, 30% year, 20% make
            baseline = (national_rate * 0.5) + (year_rate * 0.3) + (make_rate * 0.2)
            ratio = model_rate / baseline

            # Skip if not elevated
            if ratio < 1.5:
                continue

            # Get mileage context for this category
            mileage = mileage_context.get(category, {})
            typical_mileage = mileage.get("spike_band")
            is_premature = mileage.get("is_premature", False)

            # Get affected years (use first variant as representative)
            affected_years = None
            if variants:
                year_data = get_defect_by_year(conn, make, model, variants[0])
                affected_years = identify_affected_years(year_data, model_rate)

            grouped_issue = GroupedKnownIssue(
                group_id=group_id,
                group_name=get_group_display_name(group_id),
                category_name=category or "Other",
                model_rate=round(model_rate, 4),
                composite_baseline=round(baseline, 4),
                ratio=round(ratio, 1),
                total_occurrences=total_occurrences,
                variant_count=len(variants),
                variant_descriptions=variants,
                typical_mileage=typical_mileage,
                is_premature=is_premature,
                affected_years=affected_years if affected_years else None
            )

            # Categorize by severity
            if ratio >= 3.0:
                grouped_major_issues.append(grouped_issue)
            elif ratio >= 2.0:
                grouped_known_issues.append(grouped_issue)
            else:
                grouped_elevated_items.append(grouped_issue)

        # Sort grouped issues by ratio (most severe first)
        grouped_major_issues.sort(key=lambda x: x.ratio, reverse=True)
        grouped_known_issues.sort(key=lambda x: x.ratio, reverse=True)
        grouped_elevated_items.sort(key=lambda x: x.ratio, reverse=True)

        # =================================================================
        # UNGROUPED DEFECTS: Individual comparison (no baseline group)
        # =================================================================
        major_issues = []
        known_issues = []
        elevated_items = []

        for defect in model_defects:
            desc = defect["defect_description"]
            category = defect["category_name"]
            model_rate = defect["rate_pct"]
            occurrence_count = defect["total_occurrences"]

            # Skip if this defect belongs to a group (already processed above)
            if get_baseline_group(desc) is not None:
                continue

            # Skip if insufficient data
            if occurrence_count < 50:
                continue

            # Use individual baseline (ungrouped)
            national_rate = national_baselines.get(desc, 0)
            year_rate = year_baselines.get(desc, national_rate)
            make_rate = make_baselines.get(desc, national_rate)

            if national_rate == 0:
                continue

            # Composite baseline: 50% national, 30% year, 20% make
            baseline = (national_rate * 0.5) + (year_rate * 0.3) + (make_rate * 0.2)
            ratio = model_rate / baseline

            # Skip if not elevated
            if ratio < 1.5:
                continue

            # Get mileage context for this category
            mileage = mileage_context.get(category, {})
            typical_mileage = mileage.get("spike_band")
            is_premature = mileage.get("is_premature", False)

            # Get affected years
            year_data = get_defect_by_year(conn, make, model, desc)
            affected_years = identify_affected_years(year_data, model_rate)

            issue = KnownIssue(
                defect_description=desc,
                category_name=category,
                model_rate=round(model_rate, 4),
                composite_baseline=round(baseline, 4),
                ratio=round(ratio, 1),
                occurrence_count=occurrence_count,
                baseline_group=None,  # Ungrouped
                typical_mileage=typical_mileage,
                is_premature=is_premature,
                affected_years=affected_years if affected_years else None
            )

            # Categorize by severity
            if ratio >= 3.0:
                major_issues.append(issue)
            elif ratio >= 2.0:
                known_issues.append(issue)
            else:
                elevated_items.append(issue)

        # Sort individual issues by ratio (most severe first)
        major_issues.sort(key=lambda x: x.ratio, reverse=True)
        known_issues.sort(key=lambda x: x.ratio, reverse=True)
        elevated_items.sort(key=lambda x: x.ratio, reverse=True)

        # Process category summaries
        system_summary = []
        for cat in model_categories:
            cat_name = cat["category_name"]
            model_pct = cat["avg_pct"]
            national_pct = national_category_baselines.get(cat_name, model_pct)

            if national_pct > 0:
                ratio = model_pct / national_pct
                system_summary.append(SystemSummary(
                    category_name=cat_name,
                    model_percentage=round(model_pct, 1),
                    national_percentage=round(national_pct, 1),
                    ratio=round(ratio, 2)
                ))

        # Sort by ratio
        system_summary.sort(key=lambda x: x.ratio, reverse=True)

        # Year recommendations
        best_years = year_pass_rates[:3] if len(year_pass_rates) >= 3 else year_pass_rates
        worst_years = year_pass_rates[-3:] if len(year_pass_rates) >= 3 else []
        worst_years.reverse()

        return KnownIssuesReport(
            make=make,
            model=model,
            total_tests=total_tests,
            # Grouped component issues (primary)
            grouped_major_issues=grouped_major_issues[:10],
            grouped_known_issues=grouped_known_issues[:10],
            grouped_elevated_items=grouped_elevated_items[:10],
            # Individual ungrouped issues
            major_issues=major_issues[:10],
            known_issues=known_issues[:10],
            elevated_items=elevated_items[:10],
            system_summary=system_summary[:6],
            best_years=best_years,
            worst_years=worst_years
        )


# Quick test
if __name__ == "__main__":
    report = generate_known_issues_report("FORD", "FOCUS")

    if report:
        print(f"\n{'='*60}")
        print(f"KNOWN ISSUES REPORT: {report.make} {report.model}")
        print(f"Based on {report.total_tests:,} MOT tests")
        print(f"{'='*60}")

        # GROUPED ISSUES (Primary)
        if report.grouped_major_issues:
            print(f"\n[!] MAJOR COMPONENT ISSUES ({len(report.grouped_major_issues)})")
            print("-" * 50)
            for issue in report.grouped_major_issues[:5]:
                print(f"  {issue.ratio}x | {issue.total_occurrences:,} | {issue.group_name} ({issue.variant_count} variants)")
                if issue.typical_mileage:
                    print(f"       Typical onset: {issue.typical_mileage}")

        if report.grouped_known_issues:
            print(f"\n[*] KNOWN COMPONENT ISSUES ({len(report.grouped_known_issues)})")
            print("-" * 50)
            for issue in report.grouped_known_issues[:5]:
                print(f"  {issue.ratio}x | {issue.total_occurrences:,} | {issue.group_name} ({issue.variant_count} variants)")

        if report.grouped_elevated_items:
            print(f"\n[~] ELEVATED COMPONENTS ({len(report.grouped_elevated_items)})")
            print("-" * 50)
            for issue in report.grouped_elevated_items[:5]:
                print(f"  {issue.ratio}x | {issue.total_occurrences:,} | {issue.group_name} ({issue.variant_count} variants)")

        # UNGROUPED ISSUES (Individual defects not in any group)
        if report.major_issues:
            print(f"\n[!] MAJOR INDIVIDUAL ISSUES ({len(report.major_issues)})")
            print("-" * 50)
            for issue in report.major_issues[:5]:
                print(f"  {issue.ratio}x | {issue.defect_description[:55]}...")

        if report.known_issues:
            print(f"\n[*] KNOWN INDIVIDUAL ISSUES ({len(report.known_issues)})")
            print("-" * 50)
            for issue in report.known_issues[:5]:
                print(f"  {issue.ratio}x | {issue.defect_description[:55]}...")

        if report.system_summary:
            print(f"\n[=] SYSTEM SUMMARY")
            print("-" * 50)
            for sys in report.system_summary[:5]:
                flag = "(!)" if sys.is_elevated else "   "
                print(f"  {flag} {sys.category_name}: {sys.model_percentage}% (national avg: {sys.national_percentage}%)")

        print(f"\n[+] BEST YEARS TO BUY")
        for y in report.best_years:
            print(f"  {y['model_year']}: {y['pass_rate']}% pass rate ({y['total_tests']:,} tests)")

        print(f"\n[-] WORST YEARS")
        for y in report.worst_years:
            print(f"  {y['model_year']}: {y['pass_rate']}% pass rate ({y['total_tests']:,} tests)")
    else:
        print("No data found")
