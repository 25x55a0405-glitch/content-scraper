"""Importers for real platform exports. One entry point: `import_file`."""

from __future__ import annotations

from typing import Optional

from .common import ImportError_, ImportResult, looks_binary
from .ga4 import parse_ga4, parse_ga4_for_period
from .generic import parse_generic
from .google_ads import parse_google_ads
from .meta_ads import parse_meta_ads
from .search_console import parse_search_console

SOURCES = {
    "ga4": "Google Analytics 4 (Traffic acquisition CSV)",
    "google_ads": "Google Ads (Campaigns report CSV)",
    "search_console": "Search Console (Performance export zip)",
    "meta_ads": "Meta Ads Manager (exported table CSV)",
    "generic": "Other source (generic CSV)",
}

# Which source wins when two supply the same figure. Analytics is the single
# attribution model across channels, so it owns sessions, conversions and
# revenue; the ad platforms own what only they can measure.
PRECEDENCE = {
    "sessions":    ["manual", "ga4", "generic"],
    "users":       ["manual", "ga4", "generic"],
    "conversions": ["manual", "ga4", "generic", "google_ads", "meta_ads"],
    "revenue":     ["manual", "ga4", "generic", "google_ads", "meta_ads"],
    "spend":       ["manual", "google_ads", "meta_ads", "generic", "ga4"],
    "clicks":      ["manual", "google_ads", "meta_ads", "search_console", "generic"],
    "impressions": ["manual", "google_ads", "meta_ads", "search_console", "generic"],
    "avg_position": ["manual", "search_console", "generic"],
}


def import_file(source_type: str, data: bytes, period_hint: Optional[str] = None) -> ImportResult:
    if source_type not in SOURCES:
        raise ImportError_(f"Unknown source type: {source_type}")
    if not data:
        raise ImportError_("The file is empty.")
    if source_type != "search_console" and looks_binary(data):
        raise ImportError_("This looks like an Excel or zip file. Export as CSV and upload that instead.")
    if source_type == "ga4":
        return parse_ga4_for_period(data, period_hint) if period_hint else parse_ga4(data)
    if source_type == "google_ads":
        return parse_google_ads(data, period_hint)
    if source_type == "search_console":
        return parse_search_console(data, period_hint)
    if source_type == "meta_ads":
        return parse_meta_ads(data, period_hint)
    return parse_generic(data, period_hint)


__all__ = ["import_file", "ImportError_", "ImportResult", "SOURCES", "PRECEDENCE"]
