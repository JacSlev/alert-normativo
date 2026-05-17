# tests/test_rss_scraper.py
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
from scraper.rss_scraper import scrape_rss

# Fixed ISO week: Mon 2026-05-11 00:00 UTC → Sun 2026-05-17 23:59 UTC
MOCK_MONDAY = datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)


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
    return _make_entry(MOCK_MONDAY + timedelta(days=2))   # Wednesday this ISO week


@pytest.fixture
def old_entry():
    return _make_entry(MOCK_MONDAY - timedelta(days=1))   # Sunday last ISO week


def test_scrape_rss_returns_list_of_dicts(recent_entry):
    with patch("scraper.rss_scraper.iso_week_cutoff", return_value=MOCK_MONDAY), \
         patch("scraper.rss_scraper.feedparser.parse", return_value=_mock_feed([recent_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "EBA"
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"
    assert results[0]["link"] == "https://www.eba.europa.eu/news/1"


def test_scrape_rss_filters_by_iso_week(recent_entry, old_entry):
    with patch("scraper.rss_scraper.iso_week_cutoff", return_value=MOCK_MONDAY), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([recent_entry, old_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert len(results) == 1
    assert results[0]["title"] == "EBA publishes guidelines on FRTB"


def test_scrape_rss_includes_monday_itself():
    monday_entry = _make_entry(MOCK_MONDAY)       # exactly at cutoff boundary
    with patch("scraper.rss_scraper.iso_week_cutoff", return_value=MOCK_MONDAY), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([monday_entry])):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert len(results) == 1


def test_scrape_rss_returns_empty_on_network_error():
    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Connection refused")
    mock_feed.entries = []
    with patch("scraper.rss_scraper.iso_week_cutoff", return_value=MOCK_MONDAY), \
         patch("scraper.rss_scraper.feedparser.parse", return_value=mock_feed):
        results = scrape_rss("https://www.eba.europa.eu/rss", source_name="EBA", days=7)
    assert results == []


def test_scrape_rss_handles_missing_summary():
    entry = MagicMock(spec=["title", "link", "published_parsed"])
    entry.title = "Title only"
    entry.link = "https://example.com"
    entry.published_parsed = (MOCK_MONDAY + timedelta(days=1)).timetuple()
    with patch("scraper.rss_scraper.iso_week_cutoff", return_value=MOCK_MONDAY), \
         patch("scraper.rss_scraper.feedparser.parse",
               return_value=_mock_feed([entry])):
        results = scrape_rss("https://example.com/rss", source_name="TEST", days=7)
    assert len(results) == 1
    assert results[0]["summary"] == ""
