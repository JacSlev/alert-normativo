# scraper/date_utils.py
"""Shared date utilities for Alert Normativo scrapers."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

# Module-level window override.
# When set (by main.py before scraping begins), all scrapers use this window
# instead of computing the previous ISO week automatically.
# Format: (start_inclusive, end_exclusive) as UTC datetimes at 00:00:00.
_window_override: Optional[Tuple[datetime, datetime]] = None


def set_window(start: datetime, end: datetime) -> None:
    """Set a global scraping window override.

    Call this once in main.py before launching any scraper.
    Both datetimes must be timezone-aware UTC.
    """
    global _window_override
    _window_override = (start, end)


def get_window(_now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """Return the active scraping window as (start_inclusive, end_exclusive).

    If set_window() has been called, returns that override.
    Otherwise falls back to the previous ISO week (Mon–Sun).
    """
    if _window_override is not None:
        return _window_override
    return previous_iso_week_window(_now=_now)


def parse_window(dal: str, al: str) -> Tuple[datetime, datetime]:
    """Parse --dal / --al CLI strings (DD/MM/YYYY) into a UTC window tuple.

    The window is half-open: [start, end) where end = al + 1 day,
    so --al 15/05/2026 includes all publications on 15 May 2026.

    Raises SystemExit with a clear message on bad format.
    """
    import sys
    fmt = "%d/%m/%Y"
    try:
        start = datetime.strptime(dal, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"[ERRORE] Formato --dal non valido: '{dal}'. Usa DD/MM/YYYY (es. 01/05/2026).")
        sys.exit(1)
    try:
        al_dt = datetime.strptime(al, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"[ERRORE] Formato --al non valido: '{al}'. Usa DD/MM/YYYY (es. 15/05/2026).")
        sys.exit(1)
    if al_dt < start:
        print(f"[ERRORE] --al ({al}) è precedente a --dal ({dal}).")
        sys.exit(1)
    end = al_dt + timedelta(days=1)  # half-open: end is exclusive
    return start, end


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
