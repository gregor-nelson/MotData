"""
Data Classes and ArticleInsights Parser
=======================================
Contains all data structures and the main parser for article generation.
"""

import json
import re
from html import escape
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Constants & Mappings
# =============================================================================

FUEL_TYPE_NAMES = {
    'PE': 'Petrol',
    'DI': 'Diesel',
    'HY': 'Hybrid Electric',
    'EL': 'Electric',
    'ED': 'Plug-in Hybrid',
    'GB': 'Gas Bi-fuel',
    'OT': 'Other',
}

PASS_RATE_THRESHOLDS = {
    'excellent': 85.0,  # >= 85%
    'good': 70.0,       # >= 70%
    'average': 60.0,    # >= 60%
    # below 60% = poor
}

# Minimum test thresholds for statistical significance
MIN_TESTS_PROVEN_DURABILITY = 100    # Minimum tests for proven durability rankings
MIN_TESTS_EARLY_PERFORMER = 100      # Minimum tests for early performer rankings


# =============================================================================
# Utility Functions
# =============================================================================

def get_pass_rate_class(rate: float) -> str:
    """Return CSS class based on pass rate."""
    if rate >= PASS_RATE_THRESHOLDS['excellent']:
        return 'pass-rate-excellent'
    elif rate >= PASS_RATE_THRESHOLDS['good']:
        return 'pass-rate-good'
    elif rate >= PASS_RATE_THRESHOLDS['average']:
        return 'pass-rate-average'
    return 'pass-rate-poor'


def get_fuel_name(code: str) -> str:
    """Convert fuel type code to readable name."""
    return FUEL_TYPE_NAMES.get(code, code)


def format_number(n: int | float) -> str:
    """Format number with thousands separator."""
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def safe_html(text: str) -> str:
    """Escape HTML special characters in text."""
    if text is None:
        return ""
    return escape(str(text))


def slugify(text: str) -> str:
    """Convert text to valid HTML ID slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().replace(' ', '-')
    # Remove any character that isn't alphanumeric, hyphen, or underscore
    slug = re.sub(r'[^a-z0-9\-_]', '', slug)
    # Ensure it starts with a letter
    if slug and not slug[0].isalpha():
        slug = 'model-' + slug
    return slug or 'model'


# =============================================================================
# Data Classes for Parsed Insights
# =============================================================================

@dataclass
class ModelYear:
    """Single model-year-fuel combination (v2.1: year-adjusted comparisons)."""
    model_year: int
    fuel_type: str
    fuel_name: str
    total_tests: int
    pass_rate: float
    avg_mileage: float
    vs_national: float  # Now: vs same-year national average
    pass_rate_class: str
    national_avg_for_year: Optional[float] = None  # v2.1: baseline for comparison

    @property
    def vs_national_formatted(self) -> str:
        """Formatted vs national string with +/- prefix."""
        if self.vs_national >= 0:
            return f"+{self.vs_national:.1f}%"
        return f"{self.vs_national:.1f}%"

    @property
    def comparison_context(self) -> str:
        """Human-readable context showing the baseline average for this year."""
        if self.national_avg_for_year:
            return f"(avg for {self.model_year}: {self.national_avg_for_year:.1f}%)"
        return ""


@dataclass
class CoreModel:
    """Aggregated stats for a core model (e.g., Jazz, Civic)."""
    name: str
    total_tests: int
    pass_rate: float
    avg_mileage: float
    year_from: int
    year_to: int
    vs_national: float
    pass_rate_class: str
    year_breakdowns: list[ModelYear] = field(default_factory=list)


@dataclass
class Competitor:
    """Competitor manufacturer stats."""
    make: str
    pass_rate: float
    total_tests: int
    rank: int
    is_current: bool = False


@dataclass
class FailureCategory:
    """MOT failure category."""
    name: str
    total_failures: int
    vehicle_count: int


@dataclass
class FuelAnalysis:
    """Pass rate by fuel type."""
    fuel_type: str
    fuel_name: str
    total_tests: int
    pass_rate: float
    pass_rate_class: str


@dataclass
class BestWorstModel:
    """Entry in best/worst models list (v2.1: year-adjusted scoring)."""
    model: str
    model_year: int
    fuel_type: str
    fuel_name: str
    total_tests: int
    pass_rate: float
    vs_national: float  # Now: vs same-year national average
    pass_rate_class: str
    national_avg_for_year: Optional[float] = None  # v2.1: baseline for comparison

    @property
    def vs_national_formatted(self) -> str:
        """Formatted vs national string with +/- prefix."""
        if self.vs_national >= 0:
            return f"+{self.vs_national:.1f}%"
        return f"{self.vs_national:.1f}%"

    @property
    def comparison_context(self) -> str:
        """Human-readable context for the comparison, e.g., 'vs 87.7% avg for 2020 vehicles'."""
        if self.national_avg_for_year:
            return f"vs {self.national_avg_for_year:.1f}% avg for {self.model_year} vehicles"
        return "vs same-year avg"


# =============================================================================
# Evidence-Tiered Durability Data Classes
# =============================================================================

@dataclass
class DurabilityVehicle:
    """
    Vehicle with proven durability data (11+ years tested).

    These are vehicles that have genuinely demonstrated long-term reliability
    through extensive real-world MOT testing at mature ages.

    v2.1: Now includes national_avg_for_age showing the weighted national average
    for vehicles of the same age band, providing context for the comparison.
    """
    model: str
    model_year: int
    fuel_type: str
    fuel_name: str
    age_band: str
    age_band_order: int
    total_tests: int
    pass_rate: float
    vs_national_at_age: float
    avg_mileage: float
    maturity_tier: str  # "proven", "maturing", "early"
    evidence_quality: str  # "high", "medium", "limited"
    concern: Optional[str] = None  # For models to avoid
    national_avg_for_age: Optional[float] = None  # v2.1: weighted avg for this age band

    @property
    def vs_national_formatted(self) -> str:
        """Formatted vs national string."""
        if self.vs_national_at_age >= 0:
            return f"+{self.vs_national_at_age:.1f}%"
        return f"{self.vs_national_at_age:.1f}%"

    @property
    def pass_rate_class(self) -> str:
        """CSS class based on pass rate."""
        return get_pass_rate_class(self.pass_rate)

    @property
    def comparison_context(self) -> str:
        """Human-readable context, e.g., 'vs 63.2% avg at 11-12 years'."""
        if self.national_avg_for_age:
            return f"vs {self.national_avg_for_age:.1f}% avg at {self.age_band}"
        return f"vs avg at {self.age_band}"


@dataclass
class EarlyPerformer:
    """
    Newer vehicle (3-6 years) showing strong early results.

    IMPORTANT: These have NOT proven durability. The caveat must be clear
    that these are early results only.

    v2.1: Now includes national_avg_for_age showing the weighted national average
    for vehicles of the same age band.
    """
    model: str
    model_year: int
    fuel_type: str
    fuel_name: str
    age_band: str
    age_band_order: int
    total_tests: int
    pass_rate: float
    vs_national_at_age: float
    avg_mileage: float
    maturity_tier: str
    evidence_quality: str
    caveat: str
    national_avg_for_age: Optional[float] = None  # v2.1: weighted avg for this age band

    @property
    def vs_national_formatted(self) -> str:
        """Formatted vs national string."""
        if self.vs_national_at_age >= 0:
            return f"+{self.vs_national_at_age:.1f}%"
        return f"{self.vs_national_at_age:.1f}%"

    @property
    def pass_rate_class(self) -> str:
        """CSS class based on pass rate."""
        return get_pass_rate_class(self.pass_rate)

    @property
    def comparison_context(self) -> str:
        """Human-readable context, e.g., 'vs 86.4% avg at 3-4 years'."""
        if self.national_avg_for_age:
            return f"vs {self.national_avg_for_age:.1f}% avg at {self.age_band}"
        return f"vs avg at {self.age_band}"


@dataclass
class ReliabilitySummary:
    """High-level reliability summary based on proven data."""
    tier_distribution: dict  # {"proven": {vehicles, tests}, "maturing": {...}, "early": {...}}
    proven_vehicles_tested: int
    proven_above_average_pct: Optional[float]
    proven_avg_vs_national: Optional[float]
    durability_rating: str  # "Excellent", "Good", "Average", "Below Average", "Insufficient Data"
    methodology_note: str


# =============================================================================
# Section Configuration
# =============================================================================

@dataclass
class SectionConfig:
    """Configuration for an article section."""
    id: str
    title: str
    icon: str
    theme: str  # blue, emerald, amber, red, neutral


# Sections that appear in the TOC (in order)
# Note: id values should match section IDs in generate_*_section functions
ARTICLE_SECTIONS = [
    SectionConfig("competition", "vs Competition", "ph-trophy", "blue"),
    SectionConfig("best-models", "Best Models by Pass Rate", "ph-star", "emerald"),
    SectionConfig("durability", "Proven Durability Champions", "ph-shield-check", "emerald"),
    SectionConfig("early-performers", "Promising Early Performers", "ph-trend-up", "blue"),
    SectionConfig("fuel-types", "Fuel Type Analysis", "ph-gas-pump", "amber"),
    SectionConfig("avoid", "Models to Avoid", "ph-warning-circle", "red"),
    SectionConfig("failures", "Common MOT Failures", "ph-wrench", "amber"),
    SectionConfig("faqs", "FAQs", "ph-question", "blue"),
    SectionConfig("recommendations", "Buying Recommendations", "ph-shopping-cart", "emerald"),
    SectionConfig("methodology", "Methodology", "ph-info", "neutral"),
]


def get_section_config(section_id: str) -> Optional[SectionConfig]:
    """Get section config by ID."""
    for section in ARTICLE_SECTIONS:
        if section.id == section_id:
            return section
    return None


# =============================================================================
# Main Parser Class
# =============================================================================

class ArticleInsights:
    """
    Parsed and structured insights ready for article generation.

    Usage:
        data = load_insights(json_path)
        insights = ArticleInsights(data)

        print(insights.make)              # "HONDA"
        print(insights.title_make)        # "Honda"
        print(insights.total_tests)       # 927815
        print(insights.top_models[:5])    # Top 5 core models
        print(insights.get_model_years('JAZZ'))  # Year breakdown for Jazz
    """

    def __init__(self, data: dict):
        self.raw = data
        self._parse(data)

    def _parse(self, data: dict):
        """Parse all sections from raw JSON."""
        # Meta
        meta = data.get('meta', {})
        self.make = meta.get('make', 'Unknown')
        self.national_pass_rate = meta.get('national_pass_rate', 71.51)
        self.generated_at = meta.get('generated_at', '')

        # Summary/Overview (use 'summary' if available, fall back to 'overview')
        summary = data.get('summary', data.get('overview', {}))
        self.total_tests = summary.get('total_tests', 0)
        self.total_models = summary.get('total_models', 0)
        self.avg_pass_rate = summary.get('avg_pass_rate', 0.0)
        self.rank = summary.get('rank', 0)
        self.rank_total = summary.get('rank_total', 75)
        self.best_model = summary.get('best_model', '')
        self.best_model_pass_rate = summary.get('best_model_pass_rate', 0.0)
        self.worst_model = summary.get('worst_model', '')
        self.worst_model_pass_rate = summary.get('worst_model_pass_rate', 0.0)
        self.vs_national = summary.get('vs_national', self.avg_pass_rate - self.national_pass_rate)

        # Parse sections
        self._parse_competitors(data.get('competitors', []))
        self._parse_core_models(data.get('core_models', []), data.get('model_year_breakdowns', {}))
        self._parse_fuel_analysis(data.get('fuel_analysis', []))
        self._parse_best_worst(data.get('best_models', []), data.get('worst_models', []))
        self._parse_failures(data.get('failures', {}))
        self._parse_mileage(data.get('mileage_impact', []))
        self._parse_durability(data.get('durability', {}))

    def _parse_competitors(self, competitors: list):
        """Parse competitor comparison data."""
        self.competitors = []
        for c in competitors:
            self.competitors.append(Competitor(
                make=c.get('make', ''),
                pass_rate=c.get('avg_pass_rate', 0.0),
                total_tests=c.get('total_tests', 0),
                rank=c.get('rank', 0),
                is_current=(c.get('make', '') == self.make)
            ))

    def _parse_core_models(self, core_models: list, breakdowns: dict):
        """Parse core models with their year breakdowns (v2.1: year-adjusted comparisons)."""
        self.core_models = []

        for m in core_models:
            name = m.get('core_model', '')
            vs_nat = m.get('pass_rate', 0) - self.national_pass_rate

            model = CoreModel(
                name=name,
                total_tests=m.get('total_tests', 0),
                pass_rate=m.get('pass_rate', 0.0),
                avg_mileage=m.get('avg_mileage', 0.0),
                year_from=m.get('year_from', 0),
                year_to=m.get('year_to', 0),
                vs_national=vs_nat,
                pass_rate_class=get_pass_rate_class(m.get('pass_rate', 0)),
                year_breakdowns=[]
            )

            # Add year breakdowns if available (v2.1: now includes year-specific averages)
            if name in breakdowns:
                for y in breakdowns[name]:
                    fuel_code = y.get('fuel_type', 'PE')
                    model.year_breakdowns.append(ModelYear(
                        model_year=y.get('model_year', 0),
                        fuel_type=fuel_code,
                        fuel_name=get_fuel_name(fuel_code),
                        total_tests=y.get('total_tests', 0),
                        pass_rate=y.get('pass_rate', 0.0),
                        avg_mileage=y.get('avg_mileage', 0.0),
                        vs_national=y.get('pass_rate_vs_national', 0.0),
                        pass_rate_class=get_pass_rate_class(y.get('pass_rate', 0)),
                        national_avg_for_year=y.get('national_avg_for_year')  # v2.1
                    ))

            self.core_models.append(model)

    def _parse_fuel_analysis(self, fuel_data: list):
        """Parse fuel type analysis."""
        self.fuel_analysis = []
        for f in fuel_data:
            code = f.get('fuel_type', '')
            self.fuel_analysis.append(FuelAnalysis(
                fuel_type=code,
                fuel_name=f.get('fuel_name', get_fuel_name(code)),
                total_tests=f.get('total_tests', 0),
                pass_rate=f.get('pass_rate', 0.0),
                pass_rate_class=get_pass_rate_class(f.get('pass_rate', 0))
            ))

    def _parse_best_worst(self, best: list, worst: list):
        """Parse best and worst model lists (v2.1: year-adjusted scoring)."""
        def parse_list(items: list) -> list[BestWorstModel]:
            result = []
            for item in items:
                code = item.get('fuel_type', 'PE')
                result.append(BestWorstModel(
                    model=item.get('model', ''),
                    model_year=item.get('model_year', 0),
                    fuel_type=code,
                    fuel_name=get_fuel_name(code),
                    total_tests=item.get('total_tests', 0),
                    pass_rate=item.get('pass_rate', 0.0),
                    vs_national=item.get('pass_rate_vs_national', 0.0),
                    pass_rate_class=get_pass_rate_class(item.get('pass_rate', 0)),
                    national_avg_for_year=item.get('national_avg_for_year')  # v2.1
                ))
            return result

        self.best_models = parse_list(best)
        self.worst_models = parse_list(worst)

    def _parse_failures(self, failures: dict):
        """Parse failure categories."""
        self.failure_categories = []
        for cat in failures.get('categories', []):
            self.failure_categories.append(FailureCategory(
                name=cat.get('category_name', ''),
                total_failures=cat.get('total_failures', 0),
                vehicle_count=cat.get('vehicle_count', 0)
            ))

        # Also store top specific failures and dangerous defects if available
        self.top_failures = failures.get('top_failures', [])
        self.dangerous_defects = failures.get('dangerous', [])

    def _parse_mileage(self, mileage_data: list):
        """Parse mileage impact data."""
        self.mileage_impact = mileage_data

    def _parse_durability(self, durability_data: dict):
        """
        Parse evidence-tiered durability data.

        v3.0: Now parses from 'age_band_analysis' structure with model_breakdown.
        Creates DurabilityVehicle and EarlyPerformer objects from age band data.

        Evidence tiering:
        - Proven (band_order >= 2): 11+ years - solid durability data
        - Early (band_order <= 1): 3-10 years - unproven durability
        """
        # Initialize empty containers
        self.durability_methodology = {}
        self.durability_champions_section = {}
        self.models_to_avoid_section = {}
        self.early_performers_section = {'caveat': 'Durability NOT yet proven - too early to assess long-term reliability'}
        self.proven_durability_champions = []
        self.proven_models_to_avoid = []
        self.early_performers = []
        self.model_trajectories = {}
        self.reliability_summary = None

        # Check if this is old format (durability) or new format (parsed via age_band_analysis)
        if durability_data.get('durability_champions') or durability_data.get('reliability_summary'):
            # Old format - use legacy parsing
            self._parse_durability_legacy(durability_data)
            return

        # New v3.0 format - durability_data is empty, we parse from age_band_analysis
        self._parse_age_band_analysis()

    def _parse_durability_legacy(self, durability_data: dict):
        """
        Parse legacy durability format (v2.x).
        Kept for backwards compatibility.
        """
        # Parse methodology info
        methodology = durability_data.get('methodology', {})
        self.durability_methodology = methodology

        # Parse reliability summary
        summary_data = durability_data.get('reliability_summary', {})
        if summary_data:
            self.reliability_summary = ReliabilitySummary(
                tier_distribution=summary_data.get('tier_distribution', {}),
                proven_vehicles_tested=summary_data.get('proven_vehicles_tested', 0),
                proven_above_average_pct=summary_data.get('proven_above_average_pct'),
                proven_avg_vs_national=summary_data.get('proven_avg_vs_national'),
                durability_rating=summary_data.get('durability_rating', 'Unknown'),
                methodology_note=summary_data.get('methodology_note', '')
            )

        # Parse durability champions (proven high performers, 11+ years)
        champions_data = durability_data.get('durability_champions', {})
        self.durability_champions_section = champions_data
        for v in champions_data.get('vehicles', []):
            code = v.get('fuel_type', 'PE')
            self.proven_durability_champions.append(DurabilityVehicle(
                model=v.get('model', ''),
                model_year=v.get('model_year', 0),
                fuel_type=code,
                fuel_name=get_fuel_name(code),
                age_band=v.get('age_band', ''),
                age_band_order=v.get('age_band_order', 0),
                total_tests=v.get('total_tests', 0),
                pass_rate=v.get('pass_rate', 0.0),
                vs_national_at_age=v.get('vs_national_at_age', 0.0),
                avg_mileage=v.get('avg_mileage', 0.0),
                maturity_tier=v.get('maturity_tier', 'proven'),
                evidence_quality=v.get('evidence_quality', 'high'),
                national_avg_for_age=v.get('national_avg_for_age')
            ))

        # Parse models to avoid (proven poor performers, 11+ years)
        avoid_data = durability_data.get('models_to_avoid', {})
        self.models_to_avoid_section = avoid_data
        for v in avoid_data.get('vehicles', []):
            code = v.get('fuel_type', 'PE')
            self.proven_models_to_avoid.append(DurabilityVehicle(
                model=v.get('model', ''),
                model_year=v.get('model_year', 0),
                fuel_type=code,
                fuel_name=get_fuel_name(code),
                age_band=v.get('age_band', ''),
                age_band_order=v.get('age_band_order', 0),
                total_tests=v.get('total_tests', 0),
                pass_rate=v.get('pass_rate', 0.0),
                vs_national_at_age=v.get('vs_national_at_age', 0.0),
                avg_mileage=v.get('avg_mileage', 0.0),
                maturity_tier=v.get('maturity_tier', 'proven'),
                evidence_quality=v.get('evidence_quality', 'high'),
                concern=v.get('concern'),
                national_avg_for_age=v.get('national_avg_for_age')
            ))

        # Parse early performers (3-6 years, unproven durability)
        early_data = durability_data.get('early_performers', {})
        self.early_performers_section = early_data
        early_caveat = early_data.get('caveat', 'Durability NOT yet proven')
        for v in early_data.get('vehicles', []):
            code = v.get('fuel_type', 'PE')
            self.early_performers.append(EarlyPerformer(
                model=v.get('model', ''),
                model_year=v.get('model_year', 0),
                fuel_type=code,
                fuel_name=get_fuel_name(code),
                age_band=v.get('age_band', ''),
                age_band_order=v.get('age_band_order', 0),
                total_tests=v.get('total_tests', 0),
                pass_rate=v.get('pass_rate', 0.0),
                vs_national_at_age=v.get('vs_national_at_age', 0.0),
                avg_mileage=v.get('avg_mileage', 0.0),
                maturity_tier=v.get('maturity_tier', 'early'),
                evidence_quality=v.get('evidence_quality', 'limited'),
                caveat=v.get('caveat', early_caveat),
                national_avg_for_age=v.get('national_avg_for_age')
            ))

        # Parse model trajectories (aging curves)
        self.model_trajectories = durability_data.get('model_trajectories', {})

    def _parse_age_band_analysis(self):
        """
        Parse v3.0 age_band_analysis structure into durability data.

        Converts model_breakdown with age_bands into:
        - proven_durability_champions (band_order >= 2, vs_national > 0)
        - proven_models_to_avoid (band_order >= 2, vs_national < -3)
        - early_performers (band_order <= 1, vs_national > 0)
        """
        age_band_data = self.raw.get('age_band_analysis', {})
        if not age_band_data:
            return

        # Store methodology info
        self.durability_methodology = {
            'description': age_band_data.get('description', ''),
            'confidence_levels': age_band_data.get('confidence_levels', {}),
            'age_bands': age_band_data.get('age_bands', {})
        }

        # Get model breakdown
        model_breakdown = age_band_data.get('model_breakdown', [])

        # Collect entries for proven durability (band_order >= 2 = 11+ years)
        proven_champions = []
        proven_avoid = []
        early_performers_list = []

        for model_data in model_breakdown:
            core_model = model_data.get('core_model', '')
            model_total_tests = model_data.get('total_tests', 0)

            # Skip models with insufficient overall data
            if model_total_tests < MIN_TESTS_PROVEN_DURABILITY:
                continue

            age_bands = model_data.get('age_bands', [])

            for band in age_bands:
                band_order = band.get('band_order', 0)
                vs_national = band.get('vs_national', 0.0)
                total_tests = band.get('total_tests', 0)
                confidence = band.get('confidence', 'low')

                # Skip insufficient sample sizes
                if total_tests < MIN_TESTS_PROVEN_DURABILITY:
                    continue

                # Determine maturity tier and evidence quality
                if band_order >= 2:  # 11+ years = proven
                    maturity_tier = 'proven'
                    evidence_quality = 'high' if confidence == 'high' else 'medium'

                    entry = DurabilityVehicle(
                        model=core_model,
                        model_year=0,  # v3.0 aggregates by core model, not year
                        fuel_type='',  # v3.0 aggregates all fuel types
                        fuel_name='All',
                        age_band=band.get('age_band', ''),
                        age_band_order=band_order,
                        total_tests=total_tests,
                        pass_rate=band.get('pass_rate', 0.0),
                        vs_national_at_age=vs_national,
                        avg_mileage=0.0,
                        maturity_tier=maturity_tier,
                        evidence_quality=evidence_quality,
                        concern=f"Below average at {band.get('age_band', '')}" if vs_national < 0 else None,
                        national_avg_for_age=band.get('national_pass_rate')
                    )

                    if vs_national > 0:
                        proven_champions.append(entry)
                    elif vs_national < -3:  # Only flag as "avoid" if significantly below average
                        proven_avoid.append(entry)

                elif band_order <= 1:  # 3-10 years = early
                    if vs_national > 0:  # Only show early performers with positive scores
                        entry = EarlyPerformer(
                            model=core_model,
                            model_year=0,
                            fuel_type='',
                            fuel_name='All',
                            age_band=band.get('age_band', ''),
                            age_band_order=band_order,
                            total_tests=total_tests,
                            pass_rate=band.get('pass_rate', 0.0),
                            vs_national_at_age=vs_national,
                            avg_mileage=0.0,
                            maturity_tier='early',
                            evidence_quality='limited',
                            caveat='Durability NOT yet proven - too early to assess long-term reliability',
                            national_avg_for_age=band.get('national_pass_rate')
                        )
                        early_performers_list.append(entry)

        # Sort by vs_national score (best first for champions, worst first for avoid)
        self.proven_durability_champions = sorted(
            proven_champions,
            key=lambda x: x.vs_national_at_age,
            reverse=True
        )
        self.proven_models_to_avoid = sorted(
            proven_avoid,
            key=lambda x: x.vs_national_at_age
        )
        self.early_performers = sorted(
            early_performers_list,
            key=lambda x: x.vs_national_at_age,
            reverse=True
        )

        # Calculate reliability summary from the data
        self._calculate_reliability_summary()

    def _calculate_reliability_summary(self):
        """
        Calculate reliability summary from parsed age band data.
        """
        total_proven = len(self.proven_durability_champions) + len(self.proven_models_to_avoid)
        if total_proven == 0:
            self.reliability_summary = None
            return

        above_avg_count = len(self.proven_durability_champions)
        pct_above = (above_avg_count / total_proven * 100) if total_proven > 0 else 0

        # Calculate average vs_national for champions
        if self.proven_durability_champions:
            avg_vs_national = sum(m.vs_national_at_age for m in self.proven_durability_champions) / len(self.proven_durability_champions)
        else:
            avg_vs_national = 0

        # Determine rating
        if pct_above >= 80 and avg_vs_national >= 5:
            rating = "Excellent"
        elif pct_above >= 60 and avg_vs_national >= 2:
            rating = "Good"
        elif pct_above >= 40:
            rating = "Average"
        elif total_proven > 0:
            rating = "Below Average"
        else:
            rating = "Insufficient Data"

        self.reliability_summary = ReliabilitySummary(
            tier_distribution={
                'proven': {'vehicles': total_proven, 'tests': sum(m.total_tests for m in self.proven_durability_champions + self.proven_models_to_avoid)},
                'early': {'vehicles': len(self.early_performers), 'tests': sum(m.total_tests for m in self.early_performers)}
            },
            proven_vehicles_tested=total_proven,
            proven_above_average_pct=round(pct_above, 1) if total_proven > 0 else None,
            proven_avg_vs_national=round(avg_vs_national, 2) if self.proven_durability_champions else None,
            durability_rating=rating,
            methodology_note="Rating based on models with 11+ years of MOT data compared to national averages for vehicles of the same age."
        )

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def title_make(self) -> str:
        """Title-cased make name for display."""
        return self.make.title()

    @property
    def pass_rate_class(self) -> str:
        """CSS class for overall pass rate."""
        return get_pass_rate_class(self.avg_pass_rate)

    @property
    def vs_national_formatted(self) -> str:
        """Formatted vs national string with +/- prefix."""
        if self.vs_national >= 0:
            return f"+{self.vs_national:.1f}%"
        return f"{self.vs_national:.1f}%"

    @property
    def top_models(self) -> list[CoreModel]:
        """Core models sorted by pass rate (highest first)."""
        return sorted(self.core_models, key=lambda m: m.pass_rate, reverse=True)

    @property
    def bottom_models(self) -> list[CoreModel]:
        """Core models sorted by pass rate (lowest first)."""
        return sorted(self.core_models, key=lambda m: m.pass_rate)

    @property
    def durability_champions(self) -> list[DurabilityVehicle]:
        """
        Vehicles with PROVEN durability - 11+ years old, still above average.

        This is the new evidence-tiered methodology. Use this for durability claims.
        """
        return self.proven_durability_champions

    @property
    def worst_agers(self) -> list[DurabilityVehicle]:
        """
        Vehicles with PROVEN poor durability - 11+ years old, below average.

        These are genuinely problematic vehicles, not just old cars.
        """
        return self.proven_models_to_avoid

    def get_top_durable_model(self) -> Optional[DurabilityVehicle]:
        """Get the single best proven durability champion."""
        return self.proven_durability_champions[0] if self.proven_durability_champions else None

    def get_worst_ager(self) -> Optional[DurabilityVehicle]:
        """Get the worst proven model to avoid."""
        return self.proven_models_to_avoid[0] if self.proven_models_to_avoid else None

    def get_top_early_performer(self) -> Optional[EarlyPerformer]:
        """Get the top early performer (with caveat about unproven durability)."""
        return self.early_performers[0] if self.early_performers else None

    def has_proven_durability_data(self) -> bool:
        """Check if we have any proven durability data (11+ years)."""
        return len(self.proven_durability_champions) > 0 or len(self.proven_models_to_avoid) > 0

    def get_available_sections(self) -> set:
        """Return section IDs that have content to display.

        Used by TOC generation to hide links to empty sections.
        """
        # Sections that always have content
        available = {"competition", "best-models", "fuel-types", "failures", "faqs", "methodology"}

        # Durability section requires proven data (11+ years)
        if self.has_proven_durability_data():
            available.add("durability")

        # Early performers section
        if self.early_performers:
            available.add("early-performers")

        # Avoid section needs either proven bad durability or worst models
        if self.proven_models_to_avoid or self.worst_models:
            available.add("avoid")

        # Recommendations section - always show but content varies
        available.add("recommendations")

        return available

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_models_for_breakdown(self, min_tests: int = 10000, limit: int = 5) -> list[CoreModel]:
        """
        Get models with sufficient data for detailed year-by-year breakdown.
        Returns top models by test count that meet the minimum threshold.
        """
        eligible = [m for m in self.core_models if m.total_tests >= min_tests]
        # Sort by total tests to get most popular models
        by_tests = sorted(eligible, key=lambda m: m.total_tests, reverse=True)
        return by_tests[:limit]

    def get_model_by_name(self, name: str) -> Optional[CoreModel]:
        """Get a specific core model by name."""
        for m in self.core_models:
            if m.name.upper() == name.upper():
                return m
        return None

    def get_hybrid_comparison(self) -> dict:
        """Get hybrid vs petrol vs diesel comparison if data exists."""
        result = {}
        for f in self.fuel_analysis:
            if f.fuel_type in ('HY', 'PE', 'DI'):
                result[f.fuel_type] = f
        return result

    def get_years_to_avoid(self, max_pass_rate: float = 55.0) -> list[BestWorstModel]:
        """Get model/years with very poor pass rates to warn about."""
        return [m for m in self.worst_models if m.pass_rate <= max_pass_rate]

    def get_top_failure_categories(self, limit: int = 7) -> list[FailureCategory]:
        """Get top N failure categories by count."""
        return self.failure_categories[:limit]

    def get_best_nearly_new(self, max_age: int = 5, limit: int = 10) -> list[BestWorstModel]:
        """
        Get best models from recent years using raw pass rates.

        For cars 1-5 years old, raw pass rate is meaningful because
        we're comparing vehicles at similar ages.

        Args:
            max_age: Maximum age in years (default 5 = 2019+ for 2023 data)
            limit: Maximum number of results
        """
        # Data ends at 2023, so 5 years = 2019+
        min_year = 2023 - max_age + 1
        recent = [m for m in self.best_models if m.model_year >= min_year]
        return recent[:limit]

    def summary_stats(self) -> dict:
        """Get key summary statistics for quick reference."""
        return {
            'make': self.make,
            'title_make': self.title_make,
            'total_tests': self.total_tests,
            'total_tests_formatted': format_number(self.total_tests),
            'avg_pass_rate': self.avg_pass_rate,
            'rank': self.rank,
            'rank_total': self.rank_total,
            'vs_national': self.vs_national,
            'vs_national_formatted': self.vs_national_formatted,
            'best_model': self.best_model,
            'best_model_pass_rate': self.best_model_pass_rate,
            'worst_model': self.worst_model,
            'worst_model_pass_rate': self.worst_model_pass_rate,
            'national_pass_rate': self.national_pass_rate,
        }


# =============================================================================
# Loading Functions
# =============================================================================

def parse_insights(json_path: Path) -> ArticleInsights:
    """Load JSON and parse into ArticleInsights object."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return ArticleInsights(data)


def load_insights(json_path: Path) -> dict:
    """Load a make insights JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_faq_data(insights: ArticleInsights) -> list[dict]:
    """Generate FAQ content from insights data."""
    faqs = []

    # FAQ 1: Most reliable model
    top_model = insights.top_models[0] if insights.top_models else None
    if top_model:
        # Find best recent model/year
        best_recent = insights.best_models[0] if insights.best_models else None
        answer = f"Based on {format_number(insights.total_tests)} MOT tests, the {insights.title_make} {top_model.name} is the most reliable {insights.title_make} with an {top_model.pass_rate:.1f}% pass rate."
        if best_recent and best_recent.pass_rate > top_model.pass_rate:
            answer += f" The {best_recent.model} {best_recent.model_year} achieves an even higher {best_recent.pass_rate:.1f}% pass rate."
        faqs.append({
            "question": f"What is the most reliable {insights.title_make} model?",
            "answer": answer
        })

    # FAQ 2: Comparison to other brands
    competitors_above = [c for c in insights.competitors if c.pass_rate > insights.avg_pass_rate and not c.is_current]
    competitors_below = [c for c in insights.competitors if c.pass_rate < insights.avg_pass_rate and not c.is_current]

    answer = f"{insights.title_make} ranks #{insights.rank} out of {insights.rank_total} manufacturers with a {insights.avg_pass_rate:.1f}% average MOT pass rate."
    if competitors_above:
        above_names = ", ".join([c.make.title() for c in competitors_above[:3]])
        answer += f" This places them behind {above_names}"
    if competitors_below:
        below_names = ", ".join([c.make.title() for c in competitors_below[:3]])
        answer += f", but ahead of {below_names}."

    faqs.append({
        "question": f"Are {insights.title_make} cars reliable compared to other brands?",
        "answer": answer
    })

    # FAQ 3: Years to avoid
    years_to_avoid = insights.get_years_to_avoid(max_pass_rate=55.0)
    if years_to_avoid:
        avoid_examples = [f"{m.model} {m.model_year} {m.fuel_name.lower()} ({m.pass_rate:.0f}% pass rate)" for m in years_to_avoid[:3]]
        answer = f"Avoid the {', '.join(avoid_examples)}. These models fail MOTs at nearly double the national average rate."
        faqs.append({
            "question": f"Which {insights.title_make} years should I avoid?",
            "answer": answer
        })

    # FAQ 4: Hybrid comparison
    hybrid_comp = insights.get_hybrid_comparison()
    if 'HY' in hybrid_comp and 'PE' in hybrid_comp:
        hy = hybrid_comp['HY']
        pe = hybrid_comp['PE']
        di = hybrid_comp.get('DI')
        answer = f"Yes. {insights.title_make} hybrids average {hy.pass_rate:.1f}% MOT pass rate compared to {pe.pass_rate:.1f}% for petrol"
        if di:
            answer += f" and {di.pass_rate:.1f}% for diesel"
        answer += "."
        faqs.append({
            "question": f"Are {insights.title_make} hybrids more reliable than petrol?",
            "answer": answer
        })

    return faqs
