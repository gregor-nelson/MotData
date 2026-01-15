"""
Dangerous Defects HTML Components

A modular component library for generating the dangerous defects article HTML.
"""

# Utilities
from .utils import (
    RATE_THRESHOLDS,
    get_rate_class,
    format_number,
    safe_html,
    title_case,
)

# Data parser
from .data_parser import (
    DefectCategory,
    DangerousDefect,
    MakeRanking,
    ModelRanking,
    FuelComparison,
    UsedCarEntry,
    VehicleDeepDive,
    CategoryDeepDive,
    AgeControlledMakeRanking,
    DangerousDefectsInsights,
)

# HTML Head
from .html_head import generate_html_head

# Section generators
from .section_header import (
    generate_header_section,
    generate_key_findings_section,
    generate_intro_section,
)
from .section_categories import generate_category_breakdown_section
from .section_rankings import (
    generate_worst_models_section,
    generate_safest_models_section,
    generate_manufacturer_rankings_section,
)
from .section_fuel import generate_fuel_analysis_section
from .section_buyer_guide import generate_buyer_guide_section
from .section_deep_dives import (
    generate_vehicle_deep_dive_section,
    generate_category_deep_dives_section,
    generate_age_controlled_section,
)
from .section_defects import generate_top_defects_section
from .section_faq import generate_faq_section
from .section_methodology import generate_methodology_section

__all__ = [
    # Utilities
    'RATE_THRESHOLDS',
    'get_rate_class',
    'format_number',
    'safe_html',
    'title_case',
    # Data classes
    'DefectCategory',
    'DangerousDefect',
    'MakeRanking',
    'ModelRanking',
    'FuelComparison',
    'UsedCarEntry',
    'VehicleDeepDive',
    'CategoryDeepDive',
    'AgeControlledMakeRanking',
    'DangerousDefectsInsights',
    # HTML generators
    'generate_html_head',
    'generate_header_section',
    'generate_key_findings_section',
    'generate_intro_section',
    'generate_category_breakdown_section',
    'generate_worst_models_section',
    'generate_safest_models_section',
    'generate_manufacturer_rankings_section',
    'generate_fuel_analysis_section',
    'generate_buyer_guide_section',
    'generate_vehicle_deep_dive_section',
    'generate_category_deep_dives_section',
    'generate_age_controlled_section',
    'generate_top_defects_section',
    'generate_faq_section',
    'generate_methodology_section',
]
