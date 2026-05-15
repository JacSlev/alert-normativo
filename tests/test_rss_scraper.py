from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
from scraper.rss_scraper import scrape_rss


@pytest.fixture
def recent_entry():
    entry = MagicMock()
    entry.title = "EBA publishes guidelines on FRTB"
    entry.link = "https://www.eba.europa.eu/news/1"
    entry.summary = "The EBA published guidelines..."
    entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=2)).timetuple()
    return entry


@pytest.fixture
def old_entry():
    entry = MagicMock()
    entry.title = "Old news"
    entry.link = "https://www.eba.europa.eu/news/old"
    entry.summary = "Old summary"
    entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=30)).timetuple()
    return entry


def test_scrape_rss_returns_list_of_dicts(recent_entry):
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [recent_entry]
    with patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "EBA"
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"
    assert results[0]["link"] == "https://www.eba.europa.eu/news/1"


def test_scrape_rss_filters_by_date(recent_entry, old_entry):
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [recent_entry, old_entry]
    with patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert len(results) == 1
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"


def test_scrape_rss_returns_empty_on_network_error():
    """feedparser returns bozo=True with empty entries on network/parse failure."""
    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Connection refused")
    mock_feed.entries = []
    with patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert results == []


def test_scrape_rss_handles_missing_summary():
    entry = MagicMock(spec=["title", "link", "published_parsed"])  # no summary attribute
    entry.title = "Title only"
    entry.link = "https://example.com"
    entry.published_parsed = (datetime.now(timezone.utc) - timedelta(days=1)).timetuple()
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [entry]
    with patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://example.com/rss", source_name="TEST", days=7)
    assert len(results) == 1
    assert results[0]["summary"] == ""
