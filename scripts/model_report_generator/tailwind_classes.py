"""Tailwind CSS class constants for model report generation.

This module centralizes all Tailwind CSS class definitions used in the
model report HTML generator, ensuring consistency and easy maintenance.
"""

# =============================================================================
# LAYOUT
# =============================================================================
CONTAINER = "max-w-7xl mx-auto px-6 py-6"
GRID_2 = "grid grid-cols-1 md:grid-cols-2 gap-5 mb-6"
GRID_3 = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6"

# =============================================================================
# CARDS
# =============================================================================
CARD = "bg-white rounded-xl shadow-sm overflow-hidden mb-6"
CARD_GOOD = f"{CARD} border-l-4 border-good"
CARD_POOR = f"{CARD} border-l-4 border-poor"
CARD_HEADER = "px-5 py-4 border-b border-slate-200 flex items-center justify-between"
CARD_TITLE = "text-base font-semibold text-slate-800"
CARD_BODY = "p-5"
CARD_BODY_COMPACT = "p-4"

# =============================================================================
# BADGES
# =============================================================================
BADGE_BASE = "inline-block px-2.5 py-1 rounded-full text-sm font-semibold"
BADGE_GOOD = f"{BADGE_BASE} bg-emerald-100 text-emerald-800"
BADGE_AVG = f"{BADGE_BASE} bg-amber-100 text-amber-800"
BADGE_POOR = f"{BADGE_BASE} bg-red-100 text-red-800"

# =============================================================================
# TABLES
# =============================================================================
TABLE = "w-full text-sm"
TH = "py-2.5 px-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide bg-slate-50 border-b border-slate-200"
TD = "py-2.5 px-3 border-b border-slate-100"
TR_HOVER = "hover:bg-slate-50"

# =============================================================================
# TYPOGRAPHY
# =============================================================================
TITLE_LG = "text-xl font-semibold text-slate-800"
TITLE_MD = "text-base font-semibold text-slate-800"
TEXT_MUTED = "text-sm text-slate-500"
TEXT_XS_MUTED = "text-xs text-slate-500"

# =============================================================================
# STATS
# =============================================================================
STAT_VALUE_LG = "text-3xl font-bold"
STAT_VALUE_MD = "text-2xl font-bold"
STAT_LABEL = "text-sm text-slate-500 mt-1"
MINI_STAT = "text-center p-4 bg-slate-50 rounded-lg"
MINI_STAT_VALUE = "text-2xl font-bold"
MINI_STAT_LABEL = "text-xs text-slate-500 mt-1"

# =============================================================================
# STAT ROWS
# =============================================================================
STAT_ROW = "flex justify-between py-2 border-b border-slate-100 last:border-b-0"
STAT_ROW_LABEL = "text-sm text-slate-500"
STAT_ROW_VALUE = "font-semibold"

# =============================================================================
# LISTS
# =============================================================================
LIST_ITEM = "flex justify-between py-2 border-b border-slate-100 last:border-b-0 text-sm"
DEFECT_LIST = "list-none max-h-96 overflow-y-auto"
DEFECT_NAME = "flex-1 pr-4"
DEFECT_COUNT = "font-semibold text-slate-500"
DEFECT_COUNT_DANGEROUS = "font-semibold text-poor"
DATA_LIST = "list-none"
DATA_LIST_NAME = "flex-1 pr-3 text-slate-700"
DATA_LIST_VALUE = "font-semibold whitespace-nowrap"

# =============================================================================
# HEADER & FOOTER
# =============================================================================
HEADER = "bg-gradient-to-br from-primary to-primary-light text-white p-8"
HEADER_H1 = "text-2xl font-semibold mb-2"
HEADER_SUBTITLE = "text-lg opacity-90"
HEADER_META = "text-sm opacity-80 mt-4"
FOOTER = "text-center py-8 text-slate-500 text-sm"

# =============================================================================
# SECTION DIVIDER
# =============================================================================
SECTION_DIVIDER = "mt-8 mb-6 pb-2 border-b-2 border-slate-200"
SECTION_DIVIDER_H2 = "text-xl font-semibold text-slate-800 mb-1"
SECTION_DIVIDER_P = "text-sm text-slate-500"

# =============================================================================
# PASS RATE HERO
# =============================================================================
HERO = "flex flex-col md:flex-row items-center gap-6 md:gap-8 bg-white p-6 rounded-xl shadow-md mb-6"
HERO_CIRCLE = "relative w-36 h-36 flex-shrink-0"
HERO_VALUE = "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
HERO_NUMBER = "text-3xl font-bold"
HERO_LABEL = "text-xs text-slate-500 uppercase tracking-wide"
HERO_DETAILS = "flex-1 min-w-[250px]"
HERO_DETAILS_H3 = "text-base font-semibold mb-3"
DETAIL_GRID = "grid grid-cols-2 gap-3"
DETAIL_ITEM = "flex flex-col"
DETAIL_ITEM_LABEL = "text-xs text-slate-500"
DETAIL_ITEM_VALUE = "text-lg font-semibold"

# =============================================================================
# RANKINGS
# =============================================================================
RANKING_BADGES = "flex gap-3 flex-wrap"
RANKING_BADGE = "flex-1 min-w-[100px] text-center p-4 bg-slate-50 rounded-lg"
RANKING_RANK = "text-2xl font-bold text-primary"
RANKING_CONTEXT = "text-xs text-slate-500 mt-1"
RANKING_PERCENTILE = "inline-block mt-2 px-2 py-0.5 bg-primary text-white rounded-full text-xs font-semibold"

# =============================================================================
# CHARTS - YEAR/AGE/MONTHLY
# =============================================================================
YEAR_CHART = "flex items-end gap-2 h-48 py-5 overflow-x-auto"
YEAR_BAR_COL = "flex flex-col items-center min-w-[40px]"
YEAR_BAR_WRAPPER = "h-28 w-7 flex items-end"
YEAR_BAR = "w-full rounded-t"
YEAR_LABEL = "text-xs mt-2 text-slate-500"
YEAR_RATE = "text-xs font-semibold"

MONTHLY_CHART = "flex items-end gap-1 h-36 py-4"
MONTHLY_BAR_COL = "flex-1 flex flex-col items-center min-w-[30px]"
MONTHLY_BAR_WRAPPER = "h-24 w-full flex items-end"
MONTHLY_BAR = "w-full rounded-t min-h-1"
MONTHLY_LABEL = "text-xs mt-1.5 text-slate-500"
MONTHLY_RATE = "text-xs font-semibold"

AGE_CHART = "flex items-end gap-2 h-44 py-4"
AGE_BAR_COL = "flex-1 flex flex-col items-center min-w-[50px]"
AGE_BAR_WRAPPER = "h-28 w-full flex items-end"
AGE_BAR = "w-full rounded-t min-h-1"
AGE_LABEL = "text-xs mt-1.5 text-slate-500 text-center"
AGE_RATE = "text-xs font-semibold"

# =============================================================================
# BAR CHARTS (HORIZONTAL)
# =============================================================================
BAR_ROW = "flex items-center mb-3"
BAR_LABEL = "w-48 text-sm text-slate-700 flex-shrink-0 truncate"
BAR_CONTAINER = "flex-1 flex items-center gap-3"
BAR = "h-6 bg-primary rounded min-w-1"
BAR_VALUE = "text-sm text-slate-500 min-w-[60px]"

# =============================================================================
# SEVERITY
# =============================================================================
SEVERITY_BAR = "flex h-8 rounded-lg overflow-hidden mb-4"
SEVERITY_SEGMENT = "flex items-center justify-center text-white text-xs font-semibold min-w-[40px]"
SEVERITY_LEGEND = "flex gap-4 flex-wrap justify-center"
SEVERITY_LEGEND_ITEM = "flex items-center gap-1.5 text-sm"
SEVERITY_DOT = "w-3 h-3 rounded-full"

# =============================================================================
# GEOGRAPHIC
# =============================================================================
GEO_SPLIT = "grid grid-cols-1 md:grid-cols-2 gap-6"
GEO_SECTION_TITLE = "text-sm font-semibold mb-3 text-slate-500"
GEO_SECTION_TITLE_BEST = "text-sm font-semibold mb-3 text-good"
GEO_SECTION_TITLE_WORST = "text-sm font-semibold mb-3 text-poor"

# =============================================================================
# HIGHLIGHT CARDS (BEST/WORST)
# =============================================================================
HIGHLIGHT_STAT = "flex items-center gap-4 flex-wrap"
HIGHLIGHT_VALUE = "text-2xl font-bold"
HIGHLIGHT_DETAIL = "mt-2 text-slate-500 text-sm"

# =============================================================================
# ALL VARIANTS TABLE
# =============================================================================
ALL_VARIANTS_TABLE = "max-h-96 overflow-y-auto"

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

# Icon wrapper class for card headers
ICON_HEADER = "text-lg text-slate-400"
