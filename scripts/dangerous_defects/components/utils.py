"""
Shared utilities for dangerous defects HTML generation.
"""

from html import escape

# Threshold classifications for dangerous defect rates (lower is better)
RATE_THRESHOLDS = {
    'excellent': 3.5,   # <= 3.5% - Very safe
    'good': 4.5,        # <= 4.5% - Safe
    'average': 5.5,     # <= 5.5% - Average
    # > 5.5% = Concerning
}

# Special make names that should not be title-cased
SPECIAL_MAKES = {
    'BMW': 'BMW',
    'MG': 'MG',
    'DS': 'DS',
    'LEVC': 'LEVC',
}


def get_rate_class(rate: float) -> str:
    """Return CSS class based on dangerous defect rate (lower is better)."""
    if rate <= RATE_THRESHOLDS['excellent']:
        return 'rate-excellent'
    elif rate <= RATE_THRESHOLDS['good']:
        return 'rate-good'
    elif rate <= RATE_THRESHOLDS['average']:
        return 'rate-average'
    return 'rate-poor'


def format_number(n: int | float) -> str:
    """Format number with thousands separator."""
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def safe_html(text: str) -> str:
    """Escape HTML special characters."""
    if text is None:
        return ""
    return escape(str(text))


def title_case(text: str) -> str:
    """Convert make/model to title case for display."""
    if text.upper() in SPECIAL_MAKES:
        return SPECIAL_MAKES[text.upper()]
    return text.title()
