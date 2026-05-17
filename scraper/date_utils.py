# scraper/date_utils.py
"""Shared date utilities for Alert Normativo scrapers."""
from datetime import datetime, timedelta, timezone
from typing import Optional


def iso_week_cutoff(_now: Optional[datetime] = None) -> datetime:
    """Return Monday 00:00:00 UTC of the current ISO week.

    Any news item published on or after this datetime is considered
    'this week' and should be included in the scraping window.

    Args:
        _now: Override the current UTC time (for testing). If None,
              uses datetime.now(timezone.utc).
    """
    today = _now if _now is not None else datetime.now(timezone.utc)
    days_since_monday = today.weekday()          # 0=Mon … 6=Sun
    monday = today - timedelta(days=days_since_monday)
    return datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)
