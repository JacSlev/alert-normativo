# tests/test_rss_scraper.py
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
from scraper.rss_scraper import scrape_rss

# Fixed window: Mon 2026-05-11 00:00 UTC → Mon 2026-05-18 00:00 UTC (exclusive)
MOCK_MONDAY = datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)
MOCK_WINDOW = (MOCK_MONDAY, MOCK_MONDAY + timedelta(days=7))


def _make_entry(pub_dt: datetime) -> MagicMock:
    entry = MagicMock()
    entry.title = "EBA publishes guidelines on FRTB"
    entry.link = "https://www.eba.europa.eu/news/1"
    entry.summary = "The EBA published guidelines..."
    entry.published_parsed = pub_dt.timetuple()
    return entry


def _mock_feed(entries):
    feed = MagicMock()
    feed.bozo = False
    feed.entries = entries
    return feed


@pytest.fixture
def recent_entry():
    return _make_entry(MOCK_MONDAY + timedelta(days=2))   # Wednesday inside window


@pytest.fixture
def old_entry():
    return _make_entry(MOCK_MONDAY - timedelta(days=1))   # Sunday before window


def test_scrape_rss_returns_list_of_dicts(recent_entry):
    with patch("scraper.rss_scraper.get_window", return_value=MOCK_WINDOW), \
         patch("scraper.rss_scraper.feedparser.parse", return_value=_mock_feed([recent_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "EBA"
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"
    assert results[0]["link"] == "https://www.eba.europa.eu/news/1"


def test_scrape_rss_filters_by_iso_week(recent_entry, old_entry):
    with patch("scraper.rss_scraper.get_window", return_value=MOCK_WINDOW), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([recent_entry, old_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA")
    assert len(results) == 1
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"


def test_scrape_rss_includes_monday_itself():
    monday_entry = _make_entry(MOCK_MONDAY)       # exactly at start boundary
    with patch("scraper.rss_scraper.get_window", return_value=MOCK_WINDOW), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([monday_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA")
    assert len(results) == 1


def test_scrape_rss_returns_empty_on_network_error():
    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Connection refused")
    mock_feed.entries = []
    with patch("scraper.rss_scraper.get_window", return_value=MOCK_WINDOW), \
         patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA")
    assert results == []


def test_scrape_rss_handles_missing_summary():
    entry = MagicMock(spec=["title", "link", "published_parsed"])
    entry.title = "Title only"
    entry.link = "https://example.com"
    entry.published_parsed = (MOCK_MONDAY + timedelta(days=1)).timetuple()
    with patch("scraper.rss_scraper.get_window", return_value=MOCK_WINDOW), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([entry])):
        results = scrape_rss("https://example.com/rss", source_name="TEST")
    assert len(results) == 1
    assert results[0]["summary"] == ""
