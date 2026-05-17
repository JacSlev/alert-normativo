# scraper/date_utils.py
"""Shared date utilities for Alert Normativo scrapers."""
from datetime import datetime, timedelta, timezone


def iso_week_cutoff() -> datetime:
    """Return Monday 00:00:00 UTC of the current ISO week.

    Any news item published on or after this datetime is considered
    'this week' and should be included in the scraping window.
    """
    today = datetime.now(timezone.utc)
    days_since_monday = today.weekday()          # 0=Mon … 6=Sun
    monday = today - timedelta(days=days_since_monday)
    return datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)
