import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from scraper.html_scraper import (
    scrape_ivass_regolamenti,
    scrape_insurance_europe_news,
    scrape_ania_comunicati,
    _parse_italian_date,
    _parse_numeric_date,
    scrape_bce_publications,
    scrape_amla_news,
    scrape_amla_publications,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_response(html: str, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.text = html
    mock.raise_for_status = MagicMock()
    if status >= 400:
        mock.raise_for_status.side_effect = Exception(f"HTTP {status}")
    return mock


# ---------------------------------------------------------------------------
# Date parsers
# ---------------------------------------------------------------------------

def test_parse_italian_date_valid():
    dt = _parse_italian_date("Regolamento IVASS n. 58 del 10 febbraio 2026")
    assert dt == datetime(2026, 2, 10, tzinfo=timezone.utc)


def test_parse_italian_date_invalid():
    assert _parse_italian_date("nessuna data qui") is None


def test_parse_numeric_date_valid():
    dt = _parse_numeric_date("11-5-2026")
    assert dt == datetime(2026, 5, 11, tzinfo=timezone.utc)


def test_parse_numeric_date_invalid():
    assert _parse_numeric_date("not-a-date") is None


# ---------------------------------------------------------------------------
# IVASS Regolamenti
# ---------------------------------------------------------------------------

IVASS_HTML_P1 = """
<html><body>
<div class="ivass-doc-list">
  <ul>
    <li><a href="/normativa/2026/n58/index.html">Regolamento IVASS n. 58 del 12 maggio 2026</a></li>
    <li><a href="/normativa/2026/n57/index.html">Regolamento IVASS n. 57 del 9 febbraio 2026</a></li>
  </ul>
</div>
</body></html>
"""

# Page with no items stops pagination
IVASS_HTML_EMPTY = "<html><body><div class='ivass-doc-list'><ul></ul></div></body></html>"


def test_scrape_ivass_returns_recent_items():
    # page 1 returns items; page 2 returns empty → pagination stops
    with patch("scraper.html_scraper.requests.get",
               side_effect=[_mock_response(IVASS_HTML_P1), _mock_response(IVASS_HTML_EMPTY)]):
        results = scrape_ivass_regolamenti(days=7)
    # May 12 (Tue) is within the current ISO week (Mon 2026-05-11)
    assert len(results) == 1
    assert results[0]["source"] == "IVASS"
    assert results[0]["date"] == "12/05/2026"
    assert results[0]["link"] == "https://www.ivass.it/normativa/2026/n58/index.html"


def test_scrape_ivass_excludes_pre_week_items():
    """Items dated before the current ISO week start (Mon 2026-05-11) are excluded."""
    html_pre_week = """
    <div class="ivass-doc-list"><ul>
    <li><a href="/normativa/2026/n55/index.html">Regolamento IVASS n. 55 del 9 maggio 2026</a></li>
    </ul></div>"""
    # May 9 is Saturday of the PREVIOUS ISO week → excluded
    with patch("scraper.html_scraper.requests.get",
               side_effect=[_mock_response(html_pre_week), _mock_response(IVASS_HTML_EMPTY)]):
        results = scrape_ivass_regolamenti(days=7)
    assert len(results) == 0


def test_scrape_ivass_returns_empty_on_http_error():
    err_resp = _mock_response("", status=500)
    with patch("scraper.html_scraper.requests.get", return_value=err_resp):
        results = scrape_ivass_regolamenti(days=7)
    assert results == []


def test_scrape_ivass_returns_empty_on_network_error():
    with patch("scraper.html_scraper.requests.get", side_effect=Exception("timeout")):
        results = scrape_ivass_regolamenti(days=7)
    assert results == []


def test_scrape_ivass_absolute_link_preserved():
    html = """
    <div class="ivass-doc-list"><ul>
    <li><a href="https://external.example.com/doc">Regolamento IVASS n. 99 del 12 maggio 2026</a></li>
    </ul></div>"""
    with patch("scraper.html_scraper.requests.get",
               side_effect=[_mock_response(html), _mock_response(IVASS_HTML_EMPTY)]):
        results = scrape_ivass_regolamenti(days=7)
    assert results[0]["link"] == "https://external.example.com/doc"


# ---------------------------------------------------------------------------
# Insurance Europe
# ---------------------------------------------------------------------------

IE_HTML = """
<html><body>
  <div class="el-objectnews">
    <h3 class="title"><a href="/news/3558/updated-guide">Updated guide on indirect taxation</a></h3>
    <div class="date">11-5-2026</div>
  </div>
  <div class="el-objectnews">
    <h3 class="title"><a href="/news/3556/digital-omnibus">Digital Omnibus report</a></h3>
    <div class="date">2-1-2026</div>
  </div>
</body></html>
"""


def test_scrape_insurance_europe_returns_recent():
    with patch("scraper.html_scraper.requests.get", return_value=_mock_response(IE_HTML)):
        results = scrape_insurance_europe_news(days=7)
    assert len(results) == 1
    assert results[0]["title"] == "Updated guide on indirect taxation"
    assert results[0]["date"] == "11/05/2026"
    assert results[0]["link"] == "https://www.insuranceeurope.eu/news/3558/updated-guide"
    assert results[0]["source"] == "Insurance Europe"


def test_scrape_insurance_europe_days_param_ignored():
    """The `days` param is deprecated — ISO week boundary is always used.
    May 11 is the Monday of the current ISO week, so it is included
    regardless of the `days` argument passed."""
    with patch("scraper.html_scraper.requests.get", return_value=_mock_response(IE_HTML)):
        results = scrape_insurance_europe_news(days=3)
    # May 11 is the ISO week start → still included even with days=3
    assert len(results) == 1


def test_scrape_insurance_europe_empty_on_error():
    with patch("scraper.html_scraper.requests.get", side_effect=Exception("SSL error")):
        results = scrape_insurance_europe_news(days=7)
    assert results == []


def test_scrape_insurance_europe_no_date_skipped():
    html = """
    <div class="el-objectnews">
      <h3 class="title"><a href="/news/1/no-date">No date article</a></h3>
    </div>"""
    with patch("scraper.html_scraper.requests.get", return_value=_mock_response(html)):
        results = scrape_insurance_europe_news(days=7)
    assert results == []


# ---------------------------------------------------------------------------
# ANIA comunicati (Selenium mock)
# ---------------------------------------------------------------------------

# May 12 is Tuesday of the current ISO week (Mon 2026-05-11)
ANIA_HTML = """
<html><body>
  <div class="thumb-pubblicazioni">
    <div class="thumb-pubblicazioni-date">12 Maggio 2026</div>
    <div class="thumb-pubblicazioni-title">
      <a href="/comunicati/comunicato-recente">Comunicato stampa ANIA — maggio 2026</a>
    </div>
  </div>
  <div class="thumb-pubblicazioni">
    <div class="thumb-pubblicazioni-date">01 Dicembre 2025</div>
    <div class="thumb-pubblicazioni-title">
      <a href="/comunicati/comunicato-vecchio">Comunicato vecchio</a>
    </div>
  </div>
</body></html>
"""


def test_scrape_ania_returns_recent():
    with patch("scraper.html_scraper._get_selenium") as mock_sel:
        from bs4 import BeautifulSoup
        mock_sel.return_value = BeautifulSoup(ANIA_HTML, "html.parser")
        results = scrape_ania_comunicati(days=7)
    assert len(results) == 1
    assert results[0]["source"] == "ANIA"
    assert results[0]["date"] == "12/05/2026"
    assert results[0]["link"] == "https://www.ania.it/comunicati/comunicato-recente"


def test_scrape_ania_excludes_pre_week_items():
    """Items dated before the current ISO week start are excluded."""
    ania_pre_week = """
    <html><body>
      <div class="thumb-pubblicazioni">
        <div class="thumb-pubblicazioni-date">09 Maggio 2026</div>
        <div class="thumb-pubblicazioni-title">
          <a href="/comunicati/comunicato-old">Comunicato del sabato scorso</a>
        </div>
      </div>
    </body></html>"""
    # May 9 is Saturday of the PREVIOUS ISO week → excluded
    with patch("scraper.html_scraper._get_selenium") as mock_sel:
        from bs4 import BeautifulSoup
        mock_sel.return_value = BeautifulSoup(ania_pre_week, "html.parser")
        results = scrape_ania_comunicati(days=7)
    assert len(results) == 0


def test_scrape_ania_returns_empty_on_selenium_failure():
    with patch("scraper.html_scraper._get_selenium", return_value=None):
        results = scrape_ania_comunicati(days=7)
    assert results == []


# ---------------------------------------------------------------------------
# BCE Publications
# ---------------------------------------------------------------------------

BCE_HTML_IN_WINDOW = """
<html><body>
<dl>
  <dt>12 May 2026</dt>
  <dd><a href="/pub/research/working-papers/2026/html/ecb.wp2601.en.html">Working Paper on FRTB capital requirements</a></dd>
  <dt>4 May 2026</dt>
  <dd><a href="/pub/economic-bulletin/2026/html/ecb.eb202605.en.html">Economic Bulletin Issue 4/2026</a></dd>
</dl>
</body></html>
"""

# Today is 2026-05-18 (Monday). iso_week_cutoff() returns 2026-05-11 (previous Monday).
# Previous ISO week: Mon 2026-05-11 to Sun 2026-05-17.
# May 12 (Tue) → within window → included
# May 4 (Sun) → before cutoff (< May 11) → excluded


def test_scrape_bce_publications_includes_in_window():
    with patch("scraper.html_scraper._get_selenium",
               return_value=BeautifulSoup(BCE_HTML_IN_WINDOW, "html.parser")):
        results = scrape_bce_publications(days=7)
    assert len(results) == 1
    assert results[0]["source"] == "BCE Publications"
    assert results[0]["date"] == "12/05/2026"
    assert "ecb.wp2601" in results[0]["link"]


def test_scrape_bce_publications_excludes_pre_week():
    html_old = """
    <dl>
      <dt>4 May 2026</dt>
      <dd><a href="/pub/economic-bulletin/2026/html/ecb.eb.en.html">Old bulletin</a></dd>
    </dl>"""
    with patch("scraper.html_scraper._get_selenium",
               return_value=BeautifulSoup(html_old, "html.parser")):
        results = scrape_bce_publications(days=7)
    assert results == []


def test_scrape_bce_publications_returns_empty_on_selenium_failure():
    with patch("scraper.html_scraper._get_selenium", return_value=None):
        results = scrape_bce_publications(days=7)
    assert results == []


def test_scrape_bce_publications_deduplicates():
    html_dup = """
    <dl>
      <dt>12 May 2026</dt>
      <dd><a href="/pub/wp1.en.html">Paper A</a></dd>
      <dd><a href="/pub/wp1.en.html">Paper A duplicate</a></dd>
    </dl>"""
    with patch("scraper.html_scraper._get_selenium",
               return_value=BeautifulSoup(html_dup, "html.parser")):
        results = scrape_bce_publications(days=7)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# AMLA
# ---------------------------------------------------------------------------

def _amla_feed(entries: list) -> MagicMock:
    mock_feed = MagicMock()
    mock_feed.entries = entries
    return mock_feed


def _amla_entry(title: str, link: str, days_ago: int) -> MagicMock:
    from datetime import timedelta
    pub = datetime.now(timezone.utc) - timedelta(days=days_ago)
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = ""
    entry.published_parsed = pub.timetuple()
    return entry


# Today = 2026-05-18. iso_week_cutoff() = 2026-05-11 (previous Monday).
# 5 days ago = 2026-05-13 (Wed) → within window → included
# 15 days ago = 2026-05-03 → before cutoff → excluded


def test_scrape_amla_news_includes_recent():
    entry_in = _amla_entry("AMLA publishes template", "/amla-template_en", days_ago=5)
    with patch("feedparser.parse", return_value=_amla_feed([entry_in])):
        results = scrape_amla_news(days=7)
    assert len(results) == 1
    assert results[0]["source"] == "AMLA"
    assert results[0]["link"] == "https://www.amla.europa.eu/amla-template_en"


def test_scrape_amla_news_excludes_old():
    entry_old = _amla_entry("Old news", "/old-news_en", days_ago=15)
    with patch("feedparser.parse", return_value=_amla_feed([entry_old])):
        results = scrape_amla_news(days=7)
    assert results == []


def test_scrape_amla_news_absolute_link_unchanged():
    entry = _amla_entry("Doc", "https://www.amla.europa.eu/doc_en", days_ago=5)
    with patch("feedparser.parse", return_value=_amla_feed([entry])):
        results = scrape_amla_news(days=7)
    assert results[0]["link"] == "https://www.amla.europa.eu/doc_en"


def test_scrape_amla_news_returns_empty_on_error():
    with patch("feedparser.parse", side_effect=Exception("network error")):
        results = scrape_amla_news(days=7)
    assert results == []


def test_scrape_amla_publications_includes_recent():
    entry_in = _amla_entry(
        "RTS draft under Art. 31",
        "https://www.amla.europa.eu/document/download/abc123_en",
        days_ago=6,
    )
    with patch("feedparser.parse", return_value=_amla_feed([entry_in])):
        results = scrape_amla_publications(days=7)
    assert len(results) == 1
    assert results[0]["source"] == "AMLA"
    assert "abc123" in results[0]["link"]


# ---------------------------------------------------------------------------
# Upper-bound exclusion — deterministic window test
# ---------------------------------------------------------------------------
# Patch previous_iso_week_window to fix the window at [2026-05-11, 2026-05-18).
# An item published on 2026-05-18 (= end, this_monday) must be excluded.
# An item published on 2026-05-17 (Sunday, last day of the window) must be included.

FIXED_START = datetime(2026, 5, 11, 0, 0, 0, tzinfo=timezone.utc)
FIXED_END   = datetime(2026, 5, 18, 0, 0, 0, tzinfo=timezone.utc)

IE_BOUNDARY_HTML = """
<html><body>
  <div class="el-objectnews">
    <h3 class="title"><a href="/news/9001/this-monday">Published on this Monday</a></h3>
    <div class="date">18-5-2026</div>
  </div>
  <div class="el-objectnews">
    <h3 class="title"><a href="/news/9000/last-sunday">Published on last Sunday</a></h3>
    <div class="date">17-5-2026</div>
  </div>
</body></html>
"""


def test_upper_bound_excluded_deterministic():
    """A publication dated == this_monday (end) must be excluded; dated == this_monday-1 must be included."""
    with patch("scraper.html_scraper.previous_iso_week_window",
               return_value=(FIXED_START, FIXED_END)), \
         patch("scraper.html_scraper.requests.get",
               return_value=_mock_response(IE_BOUNDARY_HTML)):
        results = scrape_insurance_europe_news(days=7)
    urls = [r["link"] for r in results]
    assert "https://www.insuranceeurope.eu/news/9001/this-monday" not in urls   # >= end → excluded
    assert "https://www.insuranceeurope.eu/news/9000/last-sunday" in urls       # < end → included
