from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
from scraper.rss_scraper import scrape_rss


def test_scrape_rss_returns_list_of_dicts():
    mock_entry = MagicMock()
    mock_entry.title = "EBA publishes guidelines on FRTB"
    mock_entry.link = "https://www.eba.europa.eu/news/1"
    mock_entry.summary = "The EBA published guidelines..."
    mock_entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=2)).timetuple()

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "EBA"
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"
    assert results[0]["link"] == "https://www.eba.europa.eu/news/1"


def test_scrape_rss_filters_by_date():
    mock_entry = MagicMock()
    mock_entry.title = "EBA publishes guidelines on FRTB"
    mock_entry.link = "https://www.eba.europa.eu/news/1"
    mock_entry.summary = "The EBA published guidelines..."
    mock_entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=2)).timetuple()

    old_entry = MagicMock()
    old_entry.title = "Old news"
    old_entry.link = "https://www.eba.europa.eu/news/old"
    old_entry.summary = "Old summary"
    old_entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=30)).timetuple()

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry, old_entry]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert len(results) == 1
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"


def test_scrape_rss_returns_empty_on_network_error():
    with patch("feedparser.parse", side_effect=Exception("Network error")):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert results == []


def test_scrape_rss_handles_missing_summary():
    entry = MagicMock(spec=["title", "link", "published_parsed"])  # no summary attribute
    entry.title = "Title only"
    entry.link = "https://example.com"
    entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=1)).timetuple()
    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    with patch("feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://example.com/rss", source_name="TEST", days=7)
    assert len(results) == 1
    assert results[0]["summary"] == ""
