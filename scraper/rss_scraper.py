# scraper/rss_scraper.py
import feedparser
from datetime import datetime, timezone
import config
from scraper.date_utils import iso_week_cutoff


def scrape_rss(url: str, source_name: str, days: int = 7) -> list[dict]:
    """Parse RSS feed and return news items from the current ISO week (Mon–Sun).

    The `days` parameter is accepted for backward compatibility but is not used;
    the cutoff is always Monday 00:00:00 UTC of the current ISO week.

    Note: feedparser documents published_parsed as UTC 9-tuple.
    Date key stores dd/mm/yyyy only (time-of-day discarded).
    """
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[ERRORE] RSS {source_name} ({url}): {e}")
        return []

    if feed.bozo and not feed.entries:
        print(f"[ERRORE] RSS {source_name} ({url}): {feed.bozo_exception}")
        return []

    cutoff = iso_week_cutoff()
    results = []
    for entry in feed.entries:
        try:
            # feedparser documents published_parsed as UTC 9-tuple
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (AttributeError, TypeError):
            continue
        if pub < cutoff:
            continue
        results.append({
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "summary": getattr(entry, "summary", ""),
            "date": pub.strftime("%d/%m/%Y"),
            "source": source_name,
            "ambito_fonte": config.FONTE_AMBITO.get(source_name, "CROSS FINANCE"),
        })
    return results
