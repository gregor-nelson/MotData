"""
HTML Generator Components
=========================
Exports all components for article generation.
"""

from .data_classes import (
    # Data classes
    ArticleInsights,
    ModelYear,
    CoreModel,
    Competitor,
    FailureCategory,
    FuelAnalysis,
    BestWorstModel,
    DurabilityVehicle,
    EarlyPerformer,
    ReliabilitySummary,
    SectionConfig,
    # Constants
    FUEL_TYPE_NAMES,
    PASS_RATE_THRESHOLDS,
    MIN_TESTS_PROVEN_DURABILITY,
    MIN_TESTS_EARLY_PERFORMER,
    ARTICLE_SECTIONS,
    # Functions
    get_pass_rate_class,
    get_fuel_name,
    format_number,
    safe_html,
    slugify,
    get_section_config,
    parse_insights,
    load_insights,
    generate_faq_data,
)

from .layout import (
    generate_html_head,
    generate_html_body,
    generate_toc_html,
    generate_faq_jsonld,
)

from .sections import (
    generate_header_section,
    generate_key_findings_section,
    generate_intro_section,
    generate_competitors_section,
    generate_best_models_section,
    generate_durability_section,
    generate_early_performers_section,
    generate_model_breakdowns_section,
    generate_fuel_analysis_section,
    generate_avoid_section,
    generate_failures_section,
    generate_faqs_section,
    generate_recommendations_section,
    generate_methodology_section,
    generate_cta_section,
)
