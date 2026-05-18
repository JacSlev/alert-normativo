"""
html_scraper.py — HTML scrapers for all non-RSS sources.

Patterns used:
  - IVASS:             div.ivass-doc-list > ul > li > a  (date in title text, Italian)
  - Insurance Europe:  div.el-object{news|publication|event}  (date: div.date D-M-YYYY or text)
  - EIOPA ECL:         div.ecl-content-item  (date in first text node, English abbreviated)
  - CONSOB:            div.news-entry > a  (date in title attr: "... (DD mese YYYY)")
  - EFRAG:             div.node--article--teaser  (date: div.field--name-field-news-date DD.MM.YYYY)
  - Commissione EU:    div.ecl-content-item--stack  (date in text, Italian)
  - ANIA/BdI/BIS/ICMA/IAIS/IOSCO: Selenium headless Chrome
  - EUR-Lex / GU:      REST API fallback
"""

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
import config
from scraper.date_utils import iso_week_cutoff

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
TIMEOUT = 12

# ── Month name tables ─────────────────────────────────────────────────────────
MESI_IT = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

MESI_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}


# ── Date parsers ──────────────────────────────────────────────────────────────

def _cutoff(days: int = 7) -> datetime:
    """Return Monday 00:00:00 UTC of the current ISO week.

    The `days` parameter is accepted for backward compatibility but is ignored.
    """
    return iso_week_cutoff()


def _get(url: str) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error("Fetch error %s: %s", url, e)
        return None


def _parse_italian_date(text: str) -> Optional[datetime]:
    """Parse 'DD mese YYYY' Italian date embedded anywhere in text."""
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text, re.IGNORECASE)
    if not m:
        return None
    day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    month = MESI_IT.get(month_str)
    if not month:
        return None
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_numeric_date(text: str) -> Optional[datetime]:
    """Parse 'D-M-YYYY' date (Insurance Europe format)."""
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", text.strip())
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_english_date(text: str) -> Optional[datetime]:
    """Parse 'DD Mon YYYY' or 'DD Month YYYY' English date embedded in text."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    month = MESI_EN.get(month_str) or MESI_EN.get(month_str[:3])
    if not month:
        return None
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_dot_date(text: str) -> Optional[datetime]:
    """Parse 'DD.MM.YYYY' date (EFRAG format)."""
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text.strip())
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_slash_date(text: str) -> Optional[datetime]:
    """Parse 'DD/MM/YYYY' date (GU / EUR-Lex metadata format)."""
    m = re.search(r"(\d{1,2})/(\d{2})/(\d{4})", text)
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), tzinfo=timezone.utc)
    except ValueError:
        return None


# ── Selenium helper ───────────────────────────────────────────────────────────

def _get_selenium(url: str, wait_css: str = "body", wait_sec: int = 20) -> Optional[BeautifulSoup]:
    """Fetch a JS-rendered page using headless Chrome. Returns BeautifulSoup or None."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        driver.get(url)
        try:
            WebDriverWait(driver, wait_sec).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_css))
            )
        except Exception:
            pass
        html = driver.page_source
        driver.quit()
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.error("Selenium error fetching %s: %s", url, e)
        return None


# ── Generic scrapers ──────────────────────────────────────────────────────────

_IVASS_BASE = "https://www.ivass.it"

def _scrape_ivass_page(url: str, source_label: str, days: int) -> list:
    """Generic IVASS section scraper. All IVASS pages use div.ivass-doc-list."""
    cutoff = _cutoff(days)
    results = []
    page = 1
    while True:
        page_url = url if page == 1 else f"{url}?page={page}"
        soup = _get(page_url)
        if not soup:
            break
        items = soup.select("div.ivass-doc-list li")
        if not items:
            break
        found_recent = False
        for li in items:
            a = li.find("a")
            if not a:
                continue
            # Title is in span.link-title inside the anchor
            title_span = a.find("span", class_="link-title")
            title = title_span.get_text(strip=True) if title_span else a.get_text(strip=True)
            href = a.get("href", "")
            link = href if href.startswith("http") else _IVASS_BASE + href
            # Date is in span.link-date OUTSIDE the anchor, inside the li
            date_span = li.find("span", class_="link-date")
            date_text = date_span.get_text(strip=True) if date_span else li.get_text(strip=True)
            pub = _parse_italian_date(date_text)
            if pub is None:
                # fallback: try the title text (older pages had date in title)
                pub = _parse_italian_date(title)
            if pub is None:
                continue
            if pub < cutoff:
                continue
            found_recent = True
            results.append({
                "title": title,
                "link": link,
                "summary": "",
                "date": pub.strftime("%d/%m/%Y"),
                "source": "IVASS",
                "ambito_fonte": config.FONTE_AMBITO.get("IVASS", "INSURANCE"),
            })
        if not found_recent:
            break
        page += 1
    logger.info("%s: %d notizie in %d giorni", source_label, len(results), days)
    return results


_IE_BASE = "https://www.insuranceeurope.eu"

def _scrape_ie_page(url: str, card_class: str, days: int) -> list:
    """Generic Insurance Europe page scraper.
    card_class: 'el-objectnews' | 'el-objectpublication' | 'el-objectevent'
    """
    cutoff = _cutoff(days)
    results = []
    soup = _get(url)
    if not soup:
        return []
    for card in soup.select(f"div.{card_class}"):
        # Title + link
        a = card.select_one("h3 a") or card.select_one("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else _IE_BASE + href

        # Date — try div.date (D-M-YYYY), then embedded English/Italian text
        date_el = card.select_one("div.date")
        pub: Optional[datetime] = None
        if date_el:
            pub = _parse_numeric_date(date_el.get_text(strip=True))
        if pub is None:
            # Events often have "28 May 2026" as first text
            pub = _parse_english_date(card.get_text(" ", strip=True))
        if pub is None or pub < cutoff:
            continue

        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "Insurance Europe",
            "ambito_fonte": config.FONTE_AMBITO.get("Insurance Europe", "INSURANCE"),
        })
    logger.info("IE %s: %d notizie in %d giorni", card_class, len(results), days)
    return results


def _scrape_ecl_page(url: str, source_name: str, days: int,
                     selector: str = "div.ecl-content-item") -> list:
    """Generic ECL scraper for EIOPA / Commissione Europea pages.
    Date is embedded in item text as 'DD Mon YYYY' (EN) or 'DD mese YYYY' (IT).
    """
    cutoff = _cutoff(days)
    results = []
    soup = _get(url)
    if not soup:
        return []
    for item in soup.select(selector):
        a = item.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else url.rstrip("/") + href

        text = item.get_text(" ", strip=True)
        pub = _parse_english_date(text) or _parse_italian_date(text)
        if pub is None or pub < cutoff:
            continue

        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": source_name,
            "ambito_fonte": config.FONTE_AMBITO.get(source_name, "CROSS FINANCE"),
        })
    logger.info("%s ECL: %d notizie in %d giorni", source_name, len(results), days)
    return results


_ANIA_BASE = "https://www.ania.it"

def _scrape_ania_page(url: str, days: int) -> list:
    """Generic ANIA Selenium scraper. All ANIA pages use div.thumb-pubblicazioni."""
    cutoff = _cutoff(days)
    results = []
    soup = _get_selenium(url, wait_css="div.thumb-pubblicazioni")
    if not soup:
        return []
    for card in soup.select("div.thumb-pubblicazioni"):
        date_el = card.select_one("div.thumb-pubblicazioni-date")
        title_el = card.select_one("div.thumb-pubblicazioni-title a")
        if not date_el or not title_el:
            continue
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        link = href if href.startswith("http") else _ANIA_BASE + href
        pub = _parse_italian_date(date_el.get_text(strip=True))
        if pub is None or pub < cutoff:
            continue
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "ANIA",
            "ambito_fonte": config.FONTE_AMBITO.get("ANIA", "INSURANCE"),
        })
    logger.info("ANIA %s: %d notizie in %d giorni", url, len(results), days)
    return results


# ── IVASS — 7 section pages ───────────────────────────────────────────────────

def scrape_ivass_regolamenti(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/regolamenti/index.html",
        "IVASS Regolamenti", days)

def scrape_ivass_provvedimenti(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/normativi-provv/index.html",
        "IVASS Provvedimenti", days)

def scrape_ivass_comunicazioni(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/comunicazioni/index.html",
        "IVASS Comunicazioni", days)

def scrape_ivass_lettere(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/lettere/index.html",
        "IVASS Lettere", days)

def scrape_ivass_consultazioni(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/pubbliche-consultazioni/index.html",
        "IVASS Consultazioni", days)

def scrape_ivass_esiti_cons(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/esiti-pubb-cons/index.html",
        "IVASS Esiti cons.", days)

def scrape_ivass_media(days: int) -> list:
    return _scrape_ivass_page(
        _IVASS_BASE + "/media/comunicati/index.html",
        "IVASS Media", days)


# ── Insurance Europe ──────────────────────────────────────────────────────────

def scrape_insurance_europe_news(days: int) -> list:
    return _scrape_ie_page(_IE_BASE + "/news", "el-objectnews", days)

def scrape_insurance_europe_publications(days: int) -> list:
    return _scrape_ie_page(_IE_BASE + "/publications", "el-objectpublication", days)

def scrape_insurance_europe_events(days: int) -> list:
    return _scrape_ie_page(_IE_BASE + "/events", "el-objectevent", days)


# ── ANIA — comunicati + pubblicazioni + categorie ─────────────────────────────

def scrape_ania_comunicati(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/comunicati", days)

def scrape_ania_pubblicazioni(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni", days)

def scrape_ania_cat_111377(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni/-/categories/111377", days)

def scrape_ania_cat_53704(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni/-/categories/53704", days)

def scrape_ania_cat_53705(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni/-/categories/53705", days)

def scrape_ania_cat_53703(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni/-/categories/53703", days)

def scrape_ania_cat_52472(days: int) -> list:
    return _scrape_ania_page(_ANIA_BASE + "/pubblicazioni/-/categories/52472", days)


# ── EIOPA — HTML section pages (ECL structure) ────────────────────────────────

def _scrape_eiopa_page(url: str, label: str, days: int) -> list:
    """EIOPA pages use article.ecl-content-item with <time> for date — static requests."""
    cutoff = _cutoff(days)
    results = []
    soup = _get(url)
    if not soup:
        return []
    seen = set()
    for item in soup.select("article.ecl-content-item"):
        a = item.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://www.eiopa.europa.eu" + href
        if link in seen or not title:
            continue
        # Date in <time> element: text like "01 June 2026" or "5 May 2026"
        time_el = item.find("time")
        date_text = time_el.get_text(" ", strip=True) if time_el else item.get_text(" ", strip=True)
        pub = _parse_english_date(date_text) or _parse_italian_date(date_text)
        if pub is None or pub < cutoff:
            continue
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "EIOPA",
            "ambito_fonte": config.FONTE_AMBITO.get("EIOPA", "INSURANCE"),
        })
    logger.info("EIOPA %s: %d notizie in %d giorni", label, len(results), days)
    return results

def scrape_eiopa_events(days: int) -> list:
    return _scrape_eiopa_page("https://www.eiopa.europa.eu/media/events_en", "events", days)

def scrape_eiopa_doc_library(days: int) -> list:
    return _scrape_eiopa_page("https://www.eiopa.europa.eu/document-library_en", "doc_library", days)

def scrape_eiopa_speeches(days: int) -> list:
    return _scrape_eiopa_page("https://www.eiopa.europa.eu/media/speeches-presentations_en", "speeches", days)

def scrape_eiopa_interviews(days: int) -> list:
    return _scrape_eiopa_page("https://www.eiopa.europa.eu/media/interviews-contributions_en", "interviews", days)


# ── CONSOB ────────────────────────────────────────────────────────────────────
# Structure: div.news-entry > a[title="... (DD mese YYYY)"]

_CONSOB_BASE = "https://www.consob.it"

def scrape_consob(days: int) -> list:
    cutoff = _cutoff(days)
    results = []
    soup = _get(_CONSOB_BASE + "/web/area-pubblica/home")
    if not soup:
        return []
    for ne in soup.select("div.news-entry"):
        a = ne.find("a", href=True)
        if not a:
            continue
        title_attr = a.get("title", "") or a.get_text(strip=True)
        title_text = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else _CONSOB_BASE + href

        # Date is "(DD mese YYYY)" in title attribute
        pub = _parse_italian_date(title_attr) or _parse_italian_date(title_text)
        if pub is None or pub < cutoff:
            continue

        results.append({
            "title": title_attr or title_text,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "CONSOB",
            "ambito_fonte": config.FONTE_AMBITO.get("CONSOB", "CROSS FINANCE"),
        })
    logger.info("CONSOB: %d notizie in %d giorni", len(results), days)
    return results


# ── EFRAG ─────────────────────────────────────────────────────────────────────
# Structure: div.node--article--teaser  date: div.field--name-field-news-date (DD.MM.YYYY)

def scrape_efrag(days: int) -> list:
    cutoff = _cutoff(days)
    results = []
    soup = _get("https://www.efrag.org/en/news-and-calendar/news")
    if not soup:
        return []
    for article in soup.select("div.node--article--teaser, article.node--article"):
        a = article.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://www.efrag.org" + href

        date_el = article.select_one("div.field--name-field-news-date, time")
        date_text = date_el.get_text(strip=True) if date_el else ""
        pub = _parse_dot_date(date_text) or _parse_english_date(date_text)
        if pub is None:
            # Try from article text
            pub = _parse_dot_date(article.get_text(" ", strip=True)[:20])
        if pub is None or pub < cutoff:
            continue

        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "EFRAG",
            "ambito_fonte": config.FONTE_AMBITO.get("EFRAG", "CROSS FINANCE"),
        })
    logger.info("EFRAG: %d notizie in %d giorni", len(results), days)
    return results


# ── Commissione Europea ───────────────────────────────────────────────────────
# Structure: div.ecl-content-item--stack  date in Italian text "DD mese YYYY"

def _scrape_commission_page(url: str, days: int) -> list:
    """Commissione Europea ECL pages — article.ecl-content-item with <time>."""
    cutoff = _cutoff(days)
    results = []
    soup = _get(url)
    if not soup:
        return []
    seen = set()
    for item in soup.select("article.ecl-content-item"):
        a = item.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://commission.europa.eu" + href
        if link in seen or not title:
            continue
        time_el = item.find("time")
        date_text = time_el.get_text(" ", strip=True) if time_el else item.get_text(" ", strip=True)
        pub = _parse_italian_date(date_text) or _parse_english_date(date_text)
        if pub is None or pub < cutoff:
            continue
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "Commissione Europea",
            "ambito_fonte": config.FONTE_AMBITO.get("Commissione Europea", "CROSS FINANCE"),
        })
    logger.info("Commissione EU %s: %d notizie in %d giorni", url, len(results), days)
    return results

def scrape_commissione_europea(days: int) -> list:
    return _scrape_commission_page("https://commission.europa.eu/index_it", days)

def scrape_commissione_ue_news(days: int) -> list:
    return _scrape_commission_page("https://commission.europa.eu/news-and-media/news_en", days)


# ── Banca d'Italia ────────────────────────────────────────────────────────────
# BdI uses JavaScript-rendered content; Selenium required.
# Waits for div.bdi-comunicati or ul.bdi-list, then parses links + Italian dates.

_BDI_BASE = "https://www.bancaditalia.it"

def _scrape_bdi_page(url: str, label: str, days: int) -> list:
    """BdI page scraper via Selenium. Finds anchors with Italian dates in title or text."""
    cutoff = _cutoff(days)
    results = []
    soup = _get_selenium(url, wait_css="main", wait_sec=20)
    if not soup:
        return []
    main = soup.find("main") or soup
    seen = set()
    for a in main.find_all("a", href=True):
        href = a.get("href", "")
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        title = (a.get("title") or a.get_text(" ", strip=True))[:200]
        if not title or len(title) < 10:
            continue
        link = href if href.startswith("http") else _BDI_BASE + href
        if link in seen:
            continue
        # Look for date in title, nearby text, or parent element
        parent_text = ""
        parent = a.parent
        if parent:
            parent_text = parent.get_text(" ", strip=True)
        pub = (_parse_italian_date(title) or
               _parse_italian_date(parent_text) or
               _parse_english_date(title))
        if pub is None or pub < cutoff:
            continue
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "Banca d'Italia",
            "ambito_fonte": config.FONTE_AMBITO.get("Banca d'Italia", "BANKING"),
        })
    logger.info("BdI %s: %d notizie in %d giorni", label, len(results), days)
    return results

def scrape_bdi_homepage(days: int) -> list:
    return _scrape_bdi_page(_BDI_BASE + "/", "homepage", days)

def scrape_bdi_archivio_norme(days: int) -> list:
    return _scrape_bdi_page(
        _BDI_BASE + "/compiti/vigilanza/normativa/archivio-norme/", "archivio norme", days)

def scrape_bdi_consultazioni(days: int) -> list:
    return _scrape_bdi_page(
        _BDI_BASE + "/compiti/vigilanza/normativa/consultazioni/", "consultazioni", days)

def scrape_bdi_approfondimenti(days: int) -> list:
    return _scrape_bdi_page(
        _BDI_BASE + "/media/approfondimenti/", "approfondimenti", days)

def scrape_bdi_comunicati_bce(days: int) -> list:
    return _scrape_bdi_page(
        _BDI_BASE + "/media/bce-comunicati/", "comunicati BCE", days)


# ── BIS / BCBS ────────────────────────────────────────────────────────────────
# BIS renders publications table via JS. Selenium + wait for table rows.

def scrape_bis_bcbs(days: int) -> list:
    cutoff = _cutoff(days)
    results = []
    url = "https://www.bis.org/bcbs/publications.htm?m=3%7C14%7C566"
    soup = _get_selenium(url, wait_css="table.tbl, tr.bcbs_row, div.item", wait_sec=20)
    if not soup:
        return []
    seen = set()
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        a = row.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://www.bis.org" + href
        if link in seen:
            continue
        # Date: try each cell text
        text_all = row.get_text(" ", strip=True)
        pub = _parse_english_date(text_all)
        if pub is None or pub < cutoff:
            continue
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "BIS",
            "ambito_fonte": config.FONTE_AMBITO.get("BIS", "BANKING"),
        })
    logger.info("BIS/BCBS: %d notizie in %d giorni", len(results), days)
    return results


# ── ICMA ─────────────────────────────────────────────────────────────────────
# ICMA homepage has .news div with "News In Brief" items "DD Month YYYY title..."

def scrape_icma(days: int) -> list:
    """ICMA: news items live in div.newsissues on the homepage.
    Each link text starts with 'DD Month YYYY' followed by the title.
    """
    cutoff = _cutoff(days)
    results = []
    soup = _get("https://www.icmagroup.org/")
    if not soup:
        return []
    seen = set()
    # News items are in div.newsissues > ... > a  with text "DD Month YYYYTitle"
    for container in soup.select("div.newsissues, div.col.news"):
        for a in container.find_all("a", href=True):
            href = a.get("href", "")
            raw = a.get_text(strip=True)
            if not raw or len(raw) < 15:
                continue
            link = href if href.startswith("http") else "https://www.icmagroup.org" + href
            if link in seen:
                continue
            # Date is at the start of the anchor text: "7 May 2026ICMA Board..."
            pub = _parse_english_date(raw)
            if pub is None:
                # Try parent element text
                pub = _parse_english_date((a.parent or a).get_text(" ", strip=True))
            if pub is None or pub < cutoff:
                continue
            # Strip the date part from the title
            title = re.sub(r"^\d{1,2}\s+\w+\s+\d{4}\s*", "", raw).strip() or raw
            seen.add(link)
            results.append({
                "title": title,
                "link": link,
                "summary": "",
                "date": pub.strftime("%d/%m/%Y"),
                "source": "ICMA",
                "ambito_fonte": config.FONTE_AMBITO.get("ICMA", "CROSS FINANCE"),
            })
    logger.info("ICMA: %d notizie in %d giorni", len(results), days)
    return results


# ── IOSCO ─────────────────────────────────────────────────────────────────────
# IOSCO news page is JS-rendered; use Selenium on /news/?subsection=news_releases

def scrape_iosco(days: int) -> list:
    """IOSCO: scrape news releases from iosco.org.
    The /news/?subsection=news_releases path returns 403; try the library search page.
    Falls back gracefully to empty list on access denial.
    """
    cutoff = _cutoff(days)
    results = []
    # Attempt static requests on the library/annual-reports page — news_releases blocks
    for url in [
        "https://www.iosco.org/library/pubdocs/",
        "https://www.iosco.org/library/",
    ]:
        soup = _get(url)
        if not soup:
            continue
        seen: set = set()
        for row in soup.select("tr, li, div.document"):
            a = row.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not href or not title or len(title) < 10:
                continue
            link = href if href.startswith("http") else "https://www.iosco.org" + href
            if link in seen:
                continue
            text = row.get_text(" ", strip=True)
            pub = _parse_english_date(text)
            if pub is None or pub < cutoff:
                continue
            seen.add(link)
            results.append({
                "title": title,
                "link": link,
                "summary": "",
                "date": pub.strftime("%d/%m/%Y"),
                "source": "IOSCO",
                "ambito_fonte": config.FONTE_AMBITO.get("IOSCO", "CROSS FINANCE"),
            })
        if results:
            break
    logger.info("IOSCO: %d notizie in %d giorni", len(results), days)
    return results


# ── IAIS ─────────────────────────────────────────────────────────────────────
# IAIS is JS-rendered. Selenium on /activities/news/

def _scrape_iais_page(url: str, label: str, days: int) -> list:
    """IAIS scraper (iais.org — static HTML, article elements).
    Date is at the start of each article text: 'DD Mon YYYY Title...'
    """
    cutoff = _cutoff(days)
    results = []
    soup = _get(url)
    if not soup:
        return []
    seen = set()
    for item in soup.select("article"):
        a = item.find("a", href=True)
        if not a:
            continue
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://www.iais.org" + href
        if link in seen:
            continue
        text = item.get_text(" ", strip=True)
        # Date is at start of article text: "30 Apr 2026 Title text..."
        pub = _parse_english_date(text)
        if pub is None or pub < cutoff:
            continue
        # Title: strip the leading date ("30 Apr 2026 ")
        title = re.sub(r"^\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}\s*", "", text).strip()
        title = title[:200]  # guard against very long text
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "IAIS",
            "ambito_fonte": config.FONTE_AMBITO.get("IAIS", "INSURANCE"),
        })
    logger.info("IAIS %s: %d notizie in %d giorni", label, len(results), days)
    return results

def scrape_iais_news(days: int) -> list:
    return _scrape_iais_page("https://www.iais.org/news-and-events/latest-news/", "news", days)

def scrape_iais_consultations(days: int) -> list:
    return _scrape_iais_page("https://www.iais.org/consultations/", "consultations", days)

def scrape_iais_events(days: int) -> list:
    return _scrape_iais_page("https://www.iais.org/news-and-events/stakeholder-events/", "events", days)


# ── EUR-Lex ───────────────────────────────────────────────────────────────────
# EUR-Lex: search for recent L/C-series financial regulation docs via search API.
# Filter by document type (Regulation, Directive) and date within window.

def scrape_eurlex(days: int) -> list:
    """EUR-Lex: search for recently published regulations/directives via Selenium.
    The results page is JS-rendered (div.SearchResult injected by JS).
    Date filter uses DTA/DTB params (dd%2Fmm%2Fyyyy).
    """
    from datetime import date as date_cls
    cutoff = _cutoff(days)
    today = date_cls.today()
    start = (today - timedelta(days=days))
    dta = start.strftime("%d%%2F%m%%2F%Y")
    dtb = today.strftime("%d%%2F%m%%2F%Y")
    url = (
        f"https://eur-lex.europa.eu/search.html"
        f"?scope=EURLEX&type=quick&lang=it&OBSOLETE=false"
        f"&DTA={dta}&DTB={dtb}"
        f"&sortOne=DD&sortOneOrder=desc&qid=1"
        f"&DTS_SUBDOM=ALL_ALL"
    )
    soup = _get_selenium(url, wait_css="div.SearchResult, div.search-results, div.EurlexContent",
                         wait_sec=25)
    if not soup:
        return []
    results = []
    seen = set()
    for item in soup.select("div.SearchResult"):
        a = item.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else "https://eur-lex.europa.eu" + href
        if link in seen or not title:
            continue
        text = item.get_text(" ", strip=True)
        pub = _parse_slash_date(text) or _parse_english_date(text)
        if pub is None or pub < cutoff:
            continue
        seen.add(link)
        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "EUR-Lex",
            "ambito_fonte": config.FONTE_AMBITO.get("EUR-Lex", "CROSS FINANCE"),
        })
    logger.info("EUR-Lex: %d notizie in %d giorni", len(results), days)
    return results


# ── Gazzetta Ufficiale ────────────────────────────────────────────────────────
# GU: use the sparql/REST endpoint for recent publications.
# Fallback: scrape https://www.gazzettaufficiale.it/home with Selenium.

def scrape_gazzetta_ufficiale(days: int) -> list:
    """Gazzetta Ufficiale: scrape recent laws and acts from the homepage.
    Homepage shows acts with parent text format: "DD/MM/YYYY TITLE (law ref)"
    Links with 'eli/id/' are direct act documents.
    """
    cutoff = _cutoff(days)
    results = []
    soup = _get_selenium("https://www.gazzettaufficiale.it/home",
                         wait_css="body", wait_sec=20)
    if not soup:
        return []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        # Only GU document links (eli/id/ pattern)
        if "eli/id/" not in href and "eli/gu/" not in href:
            continue
        link = href if href.startswith("http") else "https://www.gazzettaufficiale.it" + href
        if link in seen:
            continue
        # Date and title are in the parent element text
        parent = a.parent
        parent_text = parent.get_text(" ", strip=True) if parent else ""
        # DD/MM/YYYY date appears before the title in parent text
        pub = _parse_slash_date(parent_text)
        if pub is None:
            pub = _parse_italian_date(parent_text)
        if pub is None or pub < cutoff:
            continue
        # Title: sibling text around the link (grandparent usually has full text)
        gp = parent.parent if parent else None
        full_text = gp.get_text(" ", strip=True) if gp else parent_text
        # Strip the law reference "(L. DD mese YYYY, n. XX)" from end
        title = re.sub(r"\s*\(.*?\)\s*$", "", full_text).strip()
        # Remove leading DD/MM/YYYY
        title = re.sub(r"^\d{1,2}/\d{2}/\d{4}\s*", "", title).strip()
        if not title or len(title) < 8:
            title = a.get_text(strip=True) or full_text[:120]
        seen.add(link)
        results.append({
            "title": title[:200],
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "Gazzetta Ufficiale",
            "ambito_fonte": config.FONTE_AMBITO.get("Gazzetta Ufficiale", "CROSS FINANCE"),
        })
    logger.info("GU: %d notizie in %d giorni", len(results), days)
    return results


# ── BCE Publications ──────────────────────────────────────────────────────────
# Page https://www.ecb.europa.eu/pub/pubbydate/html/index.en.html is fully
# JS-rendered. Selenium required. DOM: <dl> with <dt> date headings ("12 May 2026")
# and <dd> publication items. Publications are in reverse-chronological order.

def scrape_bce_publications(days: int) -> list:
    """BCE publications by date — Selenium-rendered <dl>/<dt>/<dd> structure."""
    cutoff = _cutoff(days)
    results = []
    url = "https://www.ecb.europa.eu/pub/pubbydate/html/index.en.html"
    soup = _get_selenium(url, wait_css="dl, main, .content", wait_sec=25)
    if not soup:
        logger.warning("[WARNING] BCE Publications: Selenium returned no content")
        return []
    try:
        seen: set = set()
        current_date = None
        for el in soup.select("dt, dd"):
            if el.name == "dt":
                current_date = _parse_english_date(el.get_text(" ", strip=True))
            elif el.name == "dd" and current_date is not None:
                if current_date < cutoff:
                    break  # list is reverse-chronological; nothing newer follows
                a = el.find("a", href=True)
                if not a:
                    continue
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not href or not title:
                    continue
                link = href if href.startswith("http") else "https://www.ecb.europa.eu" + href
                if link in seen:
                    continue
                seen.add(link)
                results.append({
                    "title": title,
                    "link": link,
                    "summary": "",
                    "date": current_date.strftime("%d/%m/%Y"),
                    "source": "BCE Publications",
                    "ambito_fonte": config.FONTE_AMBITO.get("BCE Publications", "BANKING"),
                })
    except Exception as e:
        logger.warning("[WARNING] BCE Publications parsing error: %s", e)
    logger.info("BCE Publications: %d notizie in %d giorni", len(results), days)
    return results


# ── AMLA ─────────────────────────────────────────────────────────────────────
# AMLA (Anti-Money Laundering Authority) provides official RSS feeds.
# News:          https://www.amla.europa.eu/node/19/rss_en
# Document lib:  https://www.amla.europa.eu/node/105/rss_en
# RSS date format: RFC 2822 — "Wed, 13 May 2026 19:17:46 +0200"
# News links are relative (/slug_en) → prepend _AMLA_BASE.
# Publication links are absolute PDF download URLs.
# Best-effort: returns [] on any error (403, network, parse failure).

_AMLA_BASE = "https://www.amla.europa.eu"


def _scrape_amla_rss(rss_url: str, label: str, days: int) -> list:
    """Fetch AMLA RSS feed and return news items within the ISO week window."""
    import feedparser as _feedparser
    cutoff = _cutoff(days)
    results = []
    try:
        feed = _feedparser.parse(rss_url)
        for entry in feed.entries:
            try:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except (AttributeError, TypeError):
                continue
            if pub < cutoff:
                continue
            link = getattr(entry, "link", "") or ""
            if link and not link.startswith("http"):
                link = _AMLA_BASE + link
            results.append({
                "title": getattr(entry, "title", ""),
                "link": link,
                "summary": getattr(entry, "summary", "") or "",
                "date": pub.strftime("%d/%m/%Y"),
                "source": "AMLA",
                "ambito_fonte": config.FONTE_AMBITO.get("AMLA", "BANKING"),
            })
    except Exception as e:
        logger.warning("[WARNING] AMLA %s: %s", label, e)
    logger.info("AMLA %s: %d notizie in %d giorni", label, len(results), days)
    return results


def scrape_amla_news(days: int) -> list:
    return _scrape_amla_rss(
        "https://www.amla.europa.eu/node/19/rss_en", "news", days
    )


def scrape_amla_publications(days: int) -> list:
    return _scrape_amla_rss(
        "https://www.amla.europa.eu/node/105/rss_en", "publications", days
    )
