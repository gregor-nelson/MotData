"""Tailwind CSS class constants for model report generation.

This module centralizes all Tailwind CSS class definitions used in the
model report HTML generator, ensuring consistency and easy maintenance.

Aligned with Motorwise production articles styling (articles.css patterns).
"""

# =============================================================================
# LAYOUT - Matches production articles pages
# =============================================================================
CONTAINER = "max-w-6xl mx-auto px-4 py-6 sm:py-8 lg:py-12"
GRID_2 = "grid grid-cols-1 md:grid-cols-2 gap-4 mb-6"
GRID_3 = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6"

# =============================================================================
# CARDS - Production uses rounded-2xl, shadow-xl, border-neutral-100/80
# =============================================================================
CARD = "bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6 transition-all duration-200 hover:border-neutral-200/60"
CARD_GOOD = "bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6 border-l-4 border-l-emerald-500"
CARD_POOR = "bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6 border-l-4 border-l-red-500"
CARD_HEADER = "px-5 py-4 border-b border-neutral-100 flex items-center justify-between"
CARD_TITLE = "text-lg font-semibold text-neutral-900"
CARD_BODY = "p-5"
CARD_BODY_COMPACT = "p-4"

# Featured card (with pseudo-element shadow effect in CSS)
CARD_FEATURED = "featured-card bg-white rounded-2xl shadow-xl border border-neutral-100/80 p-6 mb-6 transition-all duration-200 hover:border-neutral-200/60"

# =============================================================================
# BADGES - Production uses rounded-full with borders
# =============================================================================
BADGE_BASE = "inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full border"
BADGE_GOOD = f"{BADGE_BASE} bg-emerald-50 text-emerald-600 border-emerald-200/50"
BADGE_AVG = f"{BADGE_BASE} bg-amber-50 text-amber-600 border-amber-200/50"
BADGE_POOR = f"{BADGE_BASE} bg-red-50 text-red-600 border-red-200/50"

# =============================================================================
# TABLES - Production styling with neutral colors
# =============================================================================
TABLE = "w-full text-sm"
TH = "py-3 px-4 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wide bg-neutral-50 border-b border-neutral-200"
TD = "py-3 px-4 border-b border-neutral-100 text-neutral-600"
TR_HOVER = "hover:bg-neutral-50 transition-colors duration-150"

# Table wrapper for production-like styling
TABLE_WRAPPER = "mw-table-wrapper overflow-hidden"

# =============================================================================
# TYPOGRAPHY - Production uses neutral instead of slate
# =============================================================================
TITLE_LG = "text-xl font-semibold text-neutral-900"
TITLE_MD = "text-base font-semibold text-neutral-900"
TEXT_MUTED = "text-sm text-neutral-500"
TEXT_XS_MUTED = "text-xs text-neutral-500"

# =============================================================================
# STATS - Production styling
# =============================================================================
STAT_VALUE_LG = "text-3xl font-bold text-neutral-900"
STAT_VALUE_MD = "text-2xl font-bold text-neutral-900"
STAT_LABEL = "text-sm text-neutral-500 mt-1"
MINI_STAT = "text-center p-4 bg-neutral-50 rounded-xl"
MINI_STAT_VALUE = "text-2xl font-bold"
MINI_STAT_LABEL = "text-xs text-neutral-500 mt-1"

# =============================================================================
# STAT ROWS
# =============================================================================
STAT_ROW = "flex justify-between py-2.5 border-b border-neutral-100 last:border-b-0"
STAT_ROW_LABEL = "text-sm text-neutral-500"
STAT_ROW_VALUE = "font-semibold text-neutral-900"

# =============================================================================
# LISTS
# =============================================================================
LIST_ITEM = "flex justify-between py-2.5 border-b border-neutral-100 last:border-b-0 text-sm"
DEFECT_LIST = "list-none max-h-96 overflow-y-auto"
DEFECT_NAME = "flex-1 pr-4 text-neutral-700"
DEFECT_COUNT = "font-semibold text-neutral-500"
DEFECT_COUNT_DANGEROUS = "font-semibold text-red-600"
DATA_LIST = "list-none"
DATA_LIST_NAME = "flex-1 pr-3 text-neutral-700"
DATA_LIST_VALUE = "font-semibold whitespace-nowrap text-neutral-900"

# =============================================================================
# HEADER & FOOTER - Production uses dynamic header
# =============================================================================
# Note: Production tools use <div id="mw-header"></div> loaded dynamically
# For static pages, we use a hero-style header inside main content
HEADER_HERO = "relative overflow-hidden rounded-2xl bg-white mb-6"
HEADER_HERO_INNER = "relative z-10 px-6 py-8 text-center"
HEADER_BADGE = "inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full border bg-blue-50 text-blue-600 border-blue-200/50 mb-4"
HEADER_H1 = "text-2xl sm:text-3xl font-medium text-neutral-900 mb-3 leading-tight"
HEADER_SUBTITLE = "text-sm text-neutral-600 max-w-md mx-auto leading-relaxed"
HEADER_META = "text-xs text-neutral-400 mt-4"

FOOTER = "text-center py-8 text-neutral-500 text-sm border-t border-neutral-100 mt-8"

# =============================================================================
# SECTION DIVIDER - Production gradient style
# =============================================================================
SECTION_DIVIDER = "mt-10 mb-6"
SECTION_DIVIDER_H2 = "text-xl font-semibold text-neutral-900 mb-2"
SECTION_DIVIDER_P = "text-sm text-neutral-500"
SECTION_DIVIDER_LINE = "h-px bg-gradient-to-r from-transparent via-neutral-200 to-transparent mt-4"

# =============================================================================
# PASS RATE HERO - Production card styling
# =============================================================================
HERO = "flex flex-col md:flex-row items-center gap-6 md:gap-8 bg-white p-6 rounded-2xl shadow-xl border border-neutral-100/80 mb-6"
HERO_CIRCLE = "relative w-36 h-36 flex-shrink-0"
HERO_VALUE = "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
HERO_NUMBER = "text-3xl font-bold"
HERO_LABEL = "text-xs text-neutral-500 uppercase tracking-wide"
HERO_DETAILS = "flex-1 min-w-0 sm:min-w-[200px]"
HERO_DETAILS_H3 = "text-base font-semibold text-neutral-900 mb-3"
DETAIL_GRID = "grid grid-cols-2 gap-4"
DETAIL_ITEM = "flex flex-col p-3 bg-neutral-50 rounded-xl"
DETAIL_ITEM_LABEL = "text-xs text-neutral-500"
DETAIL_ITEM_VALUE = "text-lg font-semibold text-neutral-900"

# =============================================================================
# RANKINGS - Production styling
# =============================================================================
RANKING_BADGES = "grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4"
RANKING_BADGE = "text-center p-4 bg-neutral-50 rounded-xl"
RANKING_RANK = "text-2xl font-bold text-blue-600"
RANKING_CONTEXT = "text-xs text-neutral-500 mt-1"
RANKING_PERCENTILE = "inline-block mt-2 px-2.5 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold"

# =============================================================================
# CHARTS - YEAR/AGE/MONTHLY
# =============================================================================
YEAR_CHART = "flex items-end gap-2 h-48 py-5 overflow-x-auto"
YEAR_BAR_COL = "flex flex-col items-center min-w-[28px] sm:min-w-[40px]"
YEAR_BAR_WRAPPER = "h-28 w-7 flex items-end"
YEAR_BAR = "w-full rounded-t transition-all duration-200"
YEAR_LABEL = "text-xs mt-2 text-neutral-500"
YEAR_RATE = "text-xs font-semibold"

MONTHLY_CHART = "flex items-end gap-1 h-36 py-4 overflow-x-auto"
MONTHLY_BAR_COL = "flex-1 flex flex-col items-center min-w-[24px] sm:min-w-[30px]"
MONTHLY_BAR_WRAPPER = "h-24 w-full flex items-end"
MONTHLY_BAR = "w-full rounded-t min-h-1 transition-all duration-200"
MONTHLY_LABEL = "text-xs mt-1.5 text-neutral-500"
MONTHLY_RATE = "text-xs font-semibold"

AGE_CHART = "flex items-end gap-2 h-44 py-4 overflow-x-auto"
AGE_BAR_COL = "flex-1 flex flex-col items-center min-w-[40px] sm:min-w-[50px]"
AGE_BAR_WRAPPER = "h-28 w-full flex items-end"
AGE_BAR = "w-full rounded-t min-h-1 transition-all duration-200"
AGE_LABEL = "text-xs mt-1.5 text-neutral-500 text-center"
AGE_RATE = "text-xs font-semibold"

# =============================================================================
# BAR CHARTS (HORIZONTAL)
# =============================================================================
BAR_ROW = "flex flex-col sm:flex-row sm:items-center mb-3 gap-1 sm:gap-0"
BAR_LABEL = "text-sm text-neutral-700 sm:w-48 sm:flex-shrink-0 sm:truncate"
BAR_CONTAINER = "flex-1 flex items-center gap-3"
BAR = "h-6 bg-blue-600 rounded min-w-1 transition-all duration-200"
BAR_VALUE = "text-sm text-neutral-500 min-w-[60px]"

# =============================================================================
# SEVERITY
# =============================================================================
SEVERITY_BAR = "flex h-8 rounded-xl overflow-hidden mb-4"
SEVERITY_SEGMENT = "flex items-center justify-center text-white text-xs font-semibold min-w-[40px]"
SEVERITY_LEGEND = "flex gap-4 flex-wrap justify-center"
SEVERITY_LEGEND_ITEM = "flex items-center gap-1.5 text-sm text-neutral-600"
SEVERITY_DOT = "w-3 h-3 rounded-full"

# =============================================================================
# GEOGRAPHIC
# =============================================================================
GEO_SPLIT = "grid grid-cols-1 md:grid-cols-2 gap-6"
GEO_SECTION_TITLE = "text-sm font-semibold mb-3 text-neutral-500"
GEO_SECTION_TITLE_BEST = "text-sm font-semibold mb-3 text-emerald-600"
GEO_SECTION_TITLE_WORST = "text-sm font-semibold mb-3 text-red-600"

# =============================================================================
# HIGHLIGHT CARDS (BEST/WORST)
# =============================================================================
HIGHLIGHT_STAT = "flex items-center gap-4 flex-wrap"
HIGHLIGHT_VALUE = "text-2xl font-bold text-neutral-900"
HIGHLIGHT_DETAIL = "mt-2 text-neutral-500 text-sm"

# =============================================================================
# ALL VARIANTS TABLE
# =============================================================================
ALL_VARIANTS_TABLE = "max-h-96 overflow-y-auto"

# =============================================================================
# ICON BOXES - Production gradient style (w-12 h-12 matches production)
# =============================================================================
ICON_BOX = "w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
ICON_BOX_BLUE = f"{ICON_BOX} bg-gradient-to-br from-blue-50 to-blue-100/50"
ICON_BOX_EMERALD = f"{ICON_BOX} bg-gradient-to-br from-emerald-50 to-emerald-100/50"
ICON_BOX_AMBER = f"{ICON_BOX} bg-gradient-to-br from-amber-50 to-amber-100/50"
ICON_BOX_RED = f"{ICON_BOX} bg-gradient-to-br from-red-50 to-red-100/50"
ICON_BOX_NEUTRAL = f"{ICON_BOX} bg-gradient-to-br from-neutral-50 to-neutral-100/50"

# Icon sizes for inside boxes (text-xl matches production)
ICON_LG = "text-xl"

# =============================================================================
# ICONS (Phosphor icon classes)
# =============================================================================
ICON_TROPHY = "ph ph-trophy"
ICON_CHECK_CIRCLE = "ph ph-check-circle"
ICON_WARNING = "ph ph-warning"
ICON_WARNING_OCTAGON = "ph ph-warning-octagon"
ICON_MAP_PIN = "ph ph-map-pin"
ICON_CALENDAR = "ph ph-calendar"
ICON_PATH = "ph ph-path"
ICON_CLOCK = "ph ph-clock"
ICON_GAS_PUMP = "ph ph-gas-pump"
ICON_THUMBS_UP = "ph ph-thumbs-up"
ICON_THUMBS_DOWN = "ph ph-thumbs-down"
ICON_INFO = "ph ph-info"
ICON_ARROW_CLOCKWISE = "ph ph-arrow-clockwise"
ICON_CAR = "ph ph-car"
ICON_GAUGE = "ph ph-gauge"
ICON_CHART_LINE = "ph ph-chart-line"
ICON_WRENCH = "ph ph-wrench"
ICON_LIST = "ph ph-list"
ICON_CERTIFICATE = "ph ph-certificate"

# Icon wrapper class for card headers - production uses blue-600 for active icons
ICON_HEADER = "text-lg text-neutral-400"

# =============================================================================
# INFO CARDS - Production mw-info-card pattern
# =============================================================================
INFO_CARD = "rounded-xl p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl"
INFO_CARD_BLUE = f"{INFO_CARD} bg-blue-50 border border-blue-100/80"
INFO_CARD_EMERALD = f"{INFO_CARD} bg-emerald-50 border border-emerald-100/80"
INFO_CARD_AMBER = f"{INFO_CARD} bg-amber-50 border border-amber-100/80"
INFO_CARD_RED = f"{INFO_CARD} bg-red-50 border border-red-100/80"
INFO_CARD_NEUTRAL = f"{INFO_CARD} bg-white border border-neutral-200/80"

# =============================================================================
# BUTTONS - Production mw-btn patterns
# =============================================================================
BTN_PRIMARY = "inline-flex items-center gap-2.5 bg-blue-600 text-white px-6 py-3.5 rounded-xl font-semibold transition-all duration-200 hover:bg-blue-700 hover:-translate-y-0.5 shadow-lg shadow-blue-600/20 hover:shadow-xl hover:shadow-blue-600/30"
BTN_SECONDARY = "inline-flex items-center gap-2 bg-white text-neutral-600 px-4 py-3 rounded-xl font-medium border border-neutral-200/80 transition-all duration-200 hover:bg-neutral-50 hover:text-neutral-900 hover:border-neutral-300"

# =============================================================================
# ANIMATIONS
# =============================================================================
FADE_IN = "mw-fade-in"
CARD_LIFT = "mw-card-lift"
