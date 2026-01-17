"""
HTML Generator Module
=====================
Generates styled HTML articles from MOT insights JSON data.
"""

from .generator import generate_article, generate_filename, test_parser, main
from .components import ArticleInsights, parse_insights, load_insights
