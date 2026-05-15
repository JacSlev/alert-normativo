from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
from scraper.rss_scraper import scrape_rss

MOCK_ENTRY = MagicMock()
MOCK_ENTRY.title = "EBA publishes guidelines on FRTB"
MOCK_ENTRY.link = "https://www.eba.europa.eu/news/1"
MOCK_ENTRY.summary = "The EBA published guidelines..."
MOCK_ENTRY.published_parsed = (datetime.now(timezone.utc) - timedelta(days=2)).timetuple()

OLD_ENTRY = MagicMock()
OLD_ENTRY.title = "Old news"
OLD_ENTRY.link = "https://www.eba.europa.eu/news/old"
OLD_ENTRY.summary = "Old summary"
OLD_ENTRY.published_parsed = (datetime.now(timezone.utc) - timedelta(days=30)).timetuple()


def test_scrape_rss_returns_list_of_dicts():
    mock_feed = MagicMock()
    mock_feed.entries = [MOCK_ENTRY]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "EBA"
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"
    assert results[0]["link"] == "https://www.eba.europa.eu/news/1"


def test_scrape_rss_filters_by_date():
    mock_feed = MagicMock()
    mock_feed.entries = [MOCK_ENTRY, OLD_ENTRY]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert len(results) == 1
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"


def test_scrape_rss_returns_empty_on_network_error():
    with patch("feedparser.parse", side_effect=Exception("Network error")):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert results == []


def test_scrape_rss_handles_missing_summary():
    entry = MagicMock()
    entry.title = "Title only"
    entry.link = "https://example.com"
    entry.summary = ""
    entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=1)).timetuple()
    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://example.com/rss", source_name="TEST", days=7)
    assert results[0]["summary"] == ""
