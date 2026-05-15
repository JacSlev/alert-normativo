import feedparser
from datetime import datetime, timedelta, timezone


def scrape_rss(url: str, source_name: str, days: int) -> list[dict]:
    """Parse RSS feed and return news items from the last `days` days."""
    try:
        feed = feedparser.parse(url)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results = []
        for entry in feed.entries:
            try:
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
            })
        return results
    except Exception as e:
        print(f"[ERRORE] RSS {source_name} ({url}): {e}")
        return []
