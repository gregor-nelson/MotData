"""
Data parser for dangerous defects insights JSON.
"""

from dataclasses import dataclass


@dataclass
class DefectCategory:
    """A category of dangerous defects (e.g., Tyres, Brakes)."""
    name: str
    total_occurrences: int
    percentage_of_all: float
    vehicle_variants: int
    unique_defects: int


@dataclass
class DangerousDefect:
    """A specific dangerous defect type."""
    description: str
    category: str
    total_occurrences: int
    affected_models: int


@dataclass
class MakeRanking:
    """A manufacturer's dangerous defect ranking."""
    make: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int
    rank: int
    variants_with_data: int


@dataclass
class ModelRanking:
    """A model's dangerous defect ranking."""
    make: str
    model: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int
    rank: int
    rank_total: int
    year_from: int
    year_to: int


@dataclass
class FuelComparison:
    """Fuel type comparison data."""
    fuel_type: str
    fuel_name: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int


@dataclass
class UsedCarEntry:
    """Entry in the used car buyer guide."""
    make: str
    model: str
    model_year: int
    fuel_type: str
    fuel_name: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int


@dataclass
class VehicleDeepDive:
    """Deep dive data for a specific vehicle."""
    make: str
    model: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int
    year_from: int
    year_to: int
    by_category: list
    top_defects: list
    by_model_year: list


@dataclass
class CategoryDeepDive:
    """Deep dive data for a defect category (e.g., brakes)."""
    name: str
    description: str
    rankings: list  # List of make rankings for this category


@dataclass
class AgeControlledMakeRanking:
    """Age-controlled ranking for a make (same model year comparison)."""
    make: str
    dangerous_rate: float
    total_dangerous: int
    total_tests: int
    rank: int


class DangerousDefectsInsights:
    """Parsed and structured insights for article generation."""

    def __init__(self, data: dict):
        self.raw = data
        self._parse(data)

    def _parse(self, data: dict):
        """Parse all sections from raw JSON."""
        # Meta
        meta = data.get('meta', {})
        self.title = meta.get('title', 'The Most Dangerous Cars on UK Roads')
        self.subtitle = meta.get('subtitle', 'Official DVSA MOT Data Analysis')
        self.generated_at = meta.get('generated_at', '')
        self.methodology = meta.get('methodology', {})

        # Key findings
        key = data.get('key_findings', {})
        self.total_dangerous = key.get('total_dangerous_occurrences', 0)
        self.total_tests = key.get('total_mot_tests_analysed', 0)
        self.overall_rate = key.get('overall_dangerous_rate', 0)

        rate_range = key.get('rate_range', {})
        self.safest_model = rate_range.get('lowest', {})
        self.most_dangerous_model = rate_range.get('highest', {})
        self.rate_difference_factor = rate_range.get('difference_factor', 0)

        headline = key.get('headline_stats', {})
        self.worst_make = headline.get('worst_make', {})
        self.safest_make = headline.get('safest_make', {})
        self.diesel_vs_petrol_gap = headline.get('diesel_vs_petrol_gap', '')

        # Overall statistics
        stats = data.get('overall_statistics', {})
        self.unique_makes = stats.get('unique_makes', 0)
        self.unique_models = stats.get('unique_models', 0)
        self.unique_variants = stats.get('unique_variants', 0)

        # Parse sections
        self._parse_categories(data.get('category_breakdown', []))
        self._parse_top_defects(data.get('top_dangerous_defects', []))
        self._parse_rankings(data.get('rankings', {}))
        self._parse_fuel_analysis(data.get('fuel_type_analysis', {}))
        self._parse_buyer_guide(data.get('used_car_buyer_guide', {}))
        self._parse_vehicle_deep_dives(data.get('vehicle_deep_dives', {}))
        self._parse_category_deep_dives(data.get('category_deep_dives', {}))
        self._parse_age_controlled(data.get('age_controlled_analysis', {}))

    def _parse_categories(self, categories: list):
        """Parse category breakdown."""
        self.categories = []
        for c in categories:
            self.categories.append(DefectCategory(
                name=c.get('category_name', ''),
                total_occurrences=c.get('total_occurrences', 0),
                percentage_of_all=c.get('percentage_of_all', 0),
                vehicle_variants=c.get('vehicle_variants', 0),
                unique_defects=c.get('unique_defects', 0)
            ))

    def _parse_top_defects(self, defects: list):
        """Parse top dangerous defects."""
        self.top_defects = []
        for d in defects:
            self.top_defects.append(DangerousDefect(
                description=d.get('defect_description', ''),
                category=d.get('category_name', ''),
                total_occurrences=d.get('total_occurrences', 0),
                affected_models=d.get('affected_models', 0)
            ))

    def _parse_rankings(self, rankings: dict):
        """Parse manufacturer and model rankings."""
        # Make rankings
        self.make_rankings = []
        for m in rankings.get('by_make', []):
            self.make_rankings.append(MakeRanking(
                make=m.get('make', ''),
                dangerous_rate=m.get('dangerous_rate', 0),
                total_dangerous=m.get('total_dangerous', 0),
                total_tests=m.get('total_tests', 0),
                rank=m.get('rank', 0),
                variants_with_data=m.get('variants_with_data', 0)
            ))

        # Build lookup from by_model for year_from/year_to (FIX for year bug)
        by_model_lookup = {}
        for m in rankings.get('by_model', []):
            key = (m.get('make', ''), m.get('model', ''))
            by_model_lookup[key] = m

        # Model rankings (with year info merged from by_model)
        self.model_rankings = []
        for m in rankings.get('popular_cars_full_ranking', []):
            key = (m.get('make', ''), m.get('model', ''))
            model_info = by_model_lookup.get(key, {})
            self.model_rankings.append(ModelRanking(
                make=m.get('make', ''),
                model=m.get('model', ''),
                dangerous_rate=m.get('rate', 0),
                total_dangerous=m.get('dangerous', 0),
                total_tests=m.get('tests', 0),
                rank=m.get('rank', 0),
                rank_total=m.get('rank_total', 330),
                year_from=model_info.get('year_from', 0),
                year_to=model_info.get('year_to', 0)
            ))

    def _parse_fuel_analysis(self, fuel_data: dict):
        """Parse fuel type analysis."""
        self.fuel_comparison = []
        for f in fuel_data.get('comparison', []):
            self.fuel_comparison.append(FuelComparison(
                fuel_type=f.get('fuel_type', ''),
                fuel_name=f.get('fuel_name', ''),
                dangerous_rate=f.get('dangerous_rate', 0),
                total_dangerous=f.get('total_dangerous', 0),
                total_tests=f.get('total_tests', 0)
            ))

        self.diesel_vs_petrol_examples = fuel_data.get('diesel_vs_petrol_same_model', [])[:10]
        self.fuel_insight = fuel_data.get('insight', '')

    def _parse_buyer_guide(self, guide: dict):
        """Parse used car buyer guide."""
        def parse_entries(entries: list) -> list[UsedCarEntry]:
            result = []
            for e in entries[:15]:  # Limit to 15 entries
                result.append(UsedCarEntry(
                    make=e.get('make', ''),
                    model=e.get('model', ''),
                    model_year=e.get('model_year', 0),
                    fuel_type=e.get('fuel_type', ''),
                    fuel_name=e.get('fuel_name', ''),
                    dangerous_rate=e.get('dangerous_rate', 0),
                    total_dangerous=e.get('total_dangerous', 0),
                    total_tests=e.get('total_tests', 0)
                ))
            return result

        worst = guide.get('worst_to_avoid', {})
        self.worst_2015_2017 = parse_entries(worst.get('2015_2017', []))
        self.worst_2018_2020 = parse_entries(worst.get('2018_2020', []))

        safest = guide.get('safest_choices', {})
        self.safest_2015_2017 = parse_entries(safest.get('2015_2017', []))
        self.safest_2018_2020 = parse_entries(safest.get('2018_2020', []))

    def _parse_vehicle_deep_dives(self, deep_dives: dict):
        """Parse vehicle deep dives."""
        self.vehicle_deep_dives = {}
        for key, data in deep_dives.items():
            overview = data.get('overview', {})
            self.vehicle_deep_dives[key] = VehicleDeepDive(
                make=overview.get('make', ''),
                model=overview.get('model', ''),
                dangerous_rate=overview.get('dangerous_rate', 0),
                total_dangerous=overview.get('total_dangerous', 0),
                total_tests=overview.get('total_tests', 0),
                year_from=overview.get('year_from', 0),
                year_to=overview.get('year_to', 0),
                by_category=data.get('by_category', []),
                top_defects=data.get('top_defects', [])[:10],
                by_model_year=data.get('by_model_year', [])
            )

    def _parse_category_deep_dives(self, category_dives: dict):
        """Parse category-specific deep dives (brakes, steering, etc.)."""
        self.category_deep_dives = {}
        for category_name, data in category_dives.items():
            self.category_deep_dives[category_name] = CategoryDeepDive(
                name=category_name.title(),
                description=data.get('description', ''),
                rankings=data.get('rankings', [])[:15]  # Top 15 worst makes
            )

    def _parse_age_controlled(self, age_data: dict):
        """Parse age-controlled analysis (2015 model year comparison)."""
        self.age_controlled_description = age_data.get('description', '')
        self.age_controlled_2015 = []
        for m in age_data.get('model_year_2015', []):
            self.age_controlled_2015.append(AgeControlledMakeRanking(
                make=m.get('make', ''),
                dangerous_rate=m.get('dangerous_rate', 0),
                total_dangerous=m.get('total_dangerous', 0),
                total_tests=m.get('total_tests', 0),
                rank=m.get('rank', 0)
            ))

    # Helper properties
    @property
    def worst_models(self) -> list[ModelRanking]:
        """Get worst 20 models by dangerous rate."""
        return self.model_rankings[:20]

    @property
    def safest_models(self) -> list[ModelRanking]:
        """Get safest 20 models by dangerous rate."""
        return self.model_rankings[-20:][::-1]  # Reverse to show safest first

    @property
    def all_vehicle_deep_dive_keys(self) -> list[str]:
        """Get all vehicle deep dive keys in display order."""
        # Order: worst performers first, then safest
        worst_order = ['NISSAN_QASHQAI', 'VAUXHALL_ZAFIRA', 'FORD_S-MAX', 'FORD_FOCUS']
        safe_order = ['TOYOTA_PRIUS', 'MAZDA_MX-5', 'PORSCHE_911', 'LAND ROVER_DEFENDER']
        all_keys = worst_order + safe_order
        return [k for k in all_keys if k in self.vehicle_deep_dives]
