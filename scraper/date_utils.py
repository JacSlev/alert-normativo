# scraper/date_utils.py
"""Shared date utilities for Alert Normativo scrapers."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def iso_week_cutoff(_now: Optional[datetime] = None) -> datetime:
    """Return Monday 00:00:00 UTC of the previous ISO week (Mon–Sun).

    The newsletter is sent on Monday and covers the previous complete week.
    Any news item published on or after this datetime (and before this Monday)
    is considered 'last week' and should be included in the scraping window.

    Args:
        _now: Override the current UTC time (for testing). If None,
              uses datetime.now(timezone.utc).
    """
    today = _now if _now is not None else datetime.now(timezone.utc)
    days_since_monday = today.weekday()          # 0=Mon … 6=Sun
    this_monday = today - timedelta(days=days_since_monday)
    prev_monday = this_monday - timedelta(days=7)
    return datetime(prev_monday.year, prev_monday.month, prev_monday.day, tzinfo=timezone.utc)


def previous_iso_week_window(
    _now: Optional[datetime] = None,
) -> Tuple[datetime, datetime]:
    """Return (prev_monday, this_monday) as UTC datetimes at 00:00:00.

    The previous ISO week window is the half-open interval [prev_monday, this_monday).
    A news item is in-window if: prev_monday <= pub < this_monday.

    Args:
        _now: Override the current UTC time (for testing). If None,
              uses datetime.now(timezone.utc).
    """
    today = _now if _now is not None else datetime.now(timezone.utc)
    days_since_monday = today.weekday()          # 0=Mon … 6=Sun
    this_monday = today - timedelta(days=days_since_monday)
    prev_monday = this_monday - timedelta(days=7)
    start = datetime(prev_monday.year, prev_monday.month, prev_monday.day, tzinfo=timezone.utc)
    end   = datetime(this_monday.year, this_monday.month, this_monday.day, tzinfo=timezone.utc)
    return start, end
