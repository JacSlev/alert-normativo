import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from scraper.html_scraper import (
    scrape_ivass_regolamenti,
    scrape_insurance_europe_news,
    scrape_ania_comunicati,
    _parse_italian_date,
    _parse_numeric_date,
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
    <li><a href="/normativa/2026/n58/index.html">Regolamento IVASS n. 58 del 10 maggio 2026</a></li>
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
    # Only the May 10 item is within 7 days of today (2026-05-15)
    assert len(results) == 1
    assert results[0]["source"] == "IVASS"
    assert results[0]["date"] == "10/05/2026"
    assert results[0]["link"] == "https://www.ivass.it/normativa/2026/n58/index.html"


def test_scrape_ivass_filters_old_items():
    with patch("scraper.html_scraper.requests.get",
               return_value=_mock_response(IVASS_HTML_P1)):
        results = scrape_ivass_regolamenti(days=3)
    # Both items older than 3 days → 0 results, no second page fetch
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


def test_scrape_insurance_europe_filters_old():
    with patch("scraper.html_scraper.requests.get", return_value=_mock_response(IE_HTML)):
        results = scrape_insurance_europe_news(days=3)
    assert len(results) == 0


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

# 2026-05-09 is 6 days ago (within 7d window, outside 3d window)
ANIA_HTML = """
<html><body>
  <div class="thumb-pubblicazioni">
    <div class="thumb-pubblicazioni-date">09 Maggio 2026</div>
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
    assert results[0]["date"] == "09/05/2026"
    assert results[0]["link"] == "https://www.ania.it/comunicati/comunicato-recente"


def test_scrape_ania_filters_old():
    with patch("scraper.html_scraper._get_selenium") as mock_sel:
        from bs4 import BeautifulSoup
        mock_sel.return_value = BeautifulSoup(ANIA_HTML, "html.parser")
        results = scrape_ania_comunicati(days=3)
    assert len(results) == 0


def test_scrape_ania_returns_empty_on_selenium_failure():
    with patch("scraper.html_scraper._get_selenium", return_value=None):
        results = scrape_ania_comunicati(days=7)
    assert results == []
