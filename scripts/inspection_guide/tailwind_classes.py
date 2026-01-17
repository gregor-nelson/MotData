"""Tailwind CSS class constants for inspection guide generation."""

# Layout
CONTAINER = "max-w-4xl mx-auto px-4 py-6 sm:py-8 lg:py-12"

# Cards
CARD = "bg-white rounded-2xl shadow-xl border border-neutral-100/80 overflow-hidden mb-6"
CARD_HEADER = "px-5 py-4 border-b border-neutral-100 flex items-center justify-between"
CARD_TITLE = "text-lg font-semibold text-neutral-900"
CARD_BODY = "p-5"

# Tables
TABLE = "w-full text-sm"
TH = "py-3 px-4 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wide bg-neutral-50 border-b border-neutral-200"
TD = "py-3 px-4 border-b border-neutral-100 text-neutral-600"
TR_HOVER = "hover:bg-neutral-50 transition-colors duration-150"

# Typography
TEXT_MUTED = "text-sm text-neutral-500"

# Lists
LIST_ITEM = "flex justify-between py-2.5 border-b border-neutral-100 last:border-b-0 text-sm"
DEFECT_NAME = "flex-1 pr-4 text-neutral-700"
DEFECT_PERCENT = "font-semibold text-neutral-600"
DEFECT_CATEGORY = "text-xs text-neutral-400 mt-0.5"

# Numbered list for top failures
NUMBERED_ITEM = "flex gap-4 py-3 border-b border-neutral-100 last:border-b-0"
NUMBERED_BADGE = "flex-shrink-0 w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold"

# Callout (warning box for dangerous defects)
CALLOUT_WARNING = "rounded-xl p-4 bg-amber-50 border border-amber-200/50 mb-4"
CALLOUT_ICON = "text-amber-600 text-lg"
CALLOUT_TITLE = "font-semibold text-amber-800"
CALLOUT_TEXT = "text-sm text-amber-700 mt-1"

# Footer
FOOTER = "text-center py-6 text-neutral-400 text-xs border-t border-neutral-100 mt-8"

# Section divider
SECTION_HEADER = "flex items-center gap-3 mb-4"
SECTION_ICON_BOX = "w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 flex items-center justify-center"
SECTION_ICON = "text-blue-600 text-lg"
SECTION_TITLE = "text-lg font-semibold text-neutral-900"
