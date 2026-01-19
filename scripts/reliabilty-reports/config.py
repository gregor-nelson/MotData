"""
Central Configuration - MOT Reliability Reports
================================================
Single source of truth for all configurable values.
"""

# =============================================================================
# DATA SOURCE
# =============================================================================
REFERENCE_YEAR = 2024

# =============================================================================
# MINIMUM TEST THRESHOLDS
# =============================================================================
MIN_TESTS_DEFAULT = 500
MIN_TESTS_BEST_MODELS = 1000
MIN_TESTS_WORST_MODELS = 100
MIN_TESTS_PROVEN_DURABILITY = 100
MIN_TESTS_EARLY_PERFORMER = 100
MIN_TESTS_FUEL_TYPE = 20
MIN_TESTS_META_DESCRIPTION = 5000

# =============================================================================
# PASS RATE THRESHOLDS (for CSS classes)
# =============================================================================
PASS_RATE_EXCELLENT = 85.0
PASS_RATE_GOOD = 70.0
PASS_RATE_AVERAGE = 60.0

# =============================================================================
# AVOID THRESHOLDS
# =============================================================================
AVOID_PASS_RATE = 60.0
AVOID_VS_NATIONAL = -10.0

# =============================================================================
# RATING CALCULATION
# =============================================================================
RATING_EXCELLENT_PCT = 80
RATING_EXCELLENT_VS_NAT = 5
RATING_GOOD_PCT = 60
RATING_GOOD_VS_NAT = 2
RATING_AVERAGE_PCT = 40
FALLBACK_NATIONAL_AVG = 71.45  # Per DATABASE_SPEC.md: overall national pass rate

# =============================================================================
# EXCLUSIONS
# =============================================================================
EXCLUSION_YEAR_CUTOFF = 1986

MOTORHOME_BRANDS = frozenset({
    'AUTO-TRAIL', 'AUTOTRAIL', 'BENIMAR', 'CHAUSSON', 'ROLLER TEAM',
    'ROLLERTEAM', 'HOBBY', 'SWIFT', 'BESSACARR', 'CI', 'TRIGANO',
    'RIMOR', 'LAIKA', 'ADRIA', 'HYMER', 'BURSTNER', 'DETHLEFFS',
    'BAILEY', 'ELDDIS', 'RAPIDO', 'PILOTE', 'EURAMOBIL', 'SUNLIGHT',
    'KNAUS', 'WEINSBERG', 'AUTOSTAR', 'LUNAR', 'CARADO', 'MORELO',
    'CARTHAGO', 'FRANKIA', 'CONCORDE', 'NIESMANN', 'FENDT', 'TABBERT', 'ACE'
})

VALID_FUEL_TYPES = frozenset({'PE', 'DI', 'HY', 'EL', 'ED', 'GB', 'OT'})

# =============================================================================
# AGE BANDS
# =============================================================================
AGE_BAND_ORDER = {
    "3-7 years": 0,
    "8-10 years": 1,
    "11-14 years": 2,
    "15-17 years": 3,
    "18-20 years": 4,
    "21+ years": 5
}

NATIONAL_AVG_BY_BAND = {
    0: 88.0,
    1: 75.0,
    2: 68.0,
    3: 62.0,
    4: 58.0,
    5: 55.0
}

# =============================================================================
# SAMPLE CONFIDENCE
# =============================================================================
SAMPLE_CONFIDENCE = {
    "high": {"min_tests": 1000, "note": None},
    "medium": {"min_tests": 200, "note": None},
    "low": {"min_tests": 50, "note": "Limited sample size - interpret with caution"},
    "insufficient": {"min_tests": 0, "note": "Insufficient data for reliable comparison"}
}

# =============================================================================
# DISPLAY MAPPINGS
# =============================================================================
FUEL_TYPE_NAMES = {
    'PE': 'Petrol',
    'DI': 'Diesel',
    'HY': 'Hybrid Electric',
    'EL': 'Electric',
    'ED': 'Plug-in Hybrid',
    'GB': 'Gas Bi-fuel',
    'OT': 'Other'
}

# =============================================================================
# DERIVED THRESHOLDS (calculated from base values)
# =============================================================================
DATA_YEAR_START = 2000  # Fixed historical start
DATA_YEAR_END = REFERENCE_YEAR - 1  # 2023 if REFERENCE_YEAR=2024

# Pass rate tiers for prose (derived from PASS_RATE_EXCELLENT)
PASS_RATE_EXCEPTIONAL = PASS_RATE_EXCELLENT + 5  # 90.0

# vs_national thresholds for prose (derived from RATING constants)
VS_NATIONAL_EXCEPTIONAL = RATING_EXCELLENT_VS_NAT * 2  # 10.0
VS_NATIONAL_GOOD = RATING_EXCELLENT_VS_NAT  # 5.0
VS_NATIONAL_AROUND_AVERAGE = RATING_GOOD_VS_NAT  # 2.0

# =============================================================================
# SAMPLE SIZE TIERS (for prose generation)
# =============================================================================
SAMPLE_SIZE_LOW = 5000       # "limited test data" intro
SAMPLE_SIZE_MODERATE = 20000 # "moderate sample" intro

# =============================================================================
# MODEL DISPLAY THRESHOLDS
# =============================================================================
MIN_TESTS_MODEL_BREAKDOWN = 10000  # min tests for year-by-year breakdown
MIN_TESTS_FAQ_POPULAR = 50000      # min tests for FAQ inclusion
RANK_TOP_PERFORMER = 15            # rank threshold for "top performer" label

# =============================================================================
# METHODOLOGY DISPLAY VALUES (update when database is refreshed)
# =============================================================================
METHODOLOGY_TOTAL_TESTS = 32_300_000
METHODOLOGY_YEAR_RANGE_EXAMPLE = "from ~59% (2009 vehicles) to ~88% (2020 vehicles)"
