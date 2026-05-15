import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AlertNormativo/1.0)"}
TIMEOUT = 10

MESI_IT = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


def _cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _get(url: str) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error("Fetch error %s: %s", url, e)
        return None


def _parse_italian_date(text: str) -> Optional[datetime]:
    """Parse 'DD mese YYYY' Italian date string to UTC datetime."""
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text, re.IGNORECASE)
    if not m:
        return None
    day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    month = MESI_IT.get(month_str)
    if not month:
        return None
    return datetime(year, month, day, tzinfo=timezone.utc)


def _parse_numeric_date(text: str) -> Optional[datetime]:
    """Parse 'D-M-YYYY' date string (Insurance Europe format) to UTC datetime."""
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", text.strip())
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# IVASS — Regolamenti
# URL: https://www.ivass.it/normativa/nazionale/secondaria-ivass/regolamenti/index.html
# Structure: div.ivass-doc-list > ul > li > a  (date embedded in title text)
# ---------------------------------------------------------------------------

_IVASS_BASE = "https://www.ivass.it"
_IVASS_URL = _IVASS_BASE + "/normativa/nazionale/secondaria-ivass/regolamenti/index.html"


def scrape_ivass_regolamenti(days: int) -> list:
    cutoff = _cutoff(days)
    results = []
    page = 1

    while True:
        url = _IVASS_URL if page == 1 else f"{_IVASS_URL}?page={page}"
        soup = _get(url)
        if not soup:
            break

        items = soup.select("div.ivass-doc-list li")
        if not items:
            break

        found_any_recent = False
        for li in items:
            a = li.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            link = href if href.startswith("http") else _IVASS_BASE + href

            pub = _parse_italian_date(title)
            if pub is None:
                continue
            if pub < cutoff:
                continue

            found_any_recent = True
            results.append({
                "title": title,
                "link": link,
                "summary": "",
                "date": pub.strftime("%d/%m/%Y"),
                "source": "IVASS",
            })

        if not found_any_recent:
            break
        page += 1

    logger.info("IVASS Regolamenti: %d notizie negli ultimi %d giorni", len(results), days)
    return results


# ---------------------------------------------------------------------------
# Insurance Europe — News
# URL: https://www.insuranceeurope.eu/news
# Structure: div.el-objectnews  title: h3.title a  date: div.date  (D-M-YYYY)
# ---------------------------------------------------------------------------

_IE_BASE = "https://www.insuranceeurope.eu"
_IE_URL = _IE_BASE + "/news"


def scrape_insurance_europe_news(days: int) -> list:
    cutoff = _cutoff(days)
    results = []

    soup = _get(_IE_URL)
    if not soup:
        return []

    for card in soup.select("div.el-objectnews"):
        a = card.select_one("h3.title a") or card.select_one("h3 a")
        date_el = card.select_one("div.date")
        if not a or not date_el:
            continue

        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = href if href.startswith("http") else _IE_BASE + href
        date_text = date_el.get_text(strip=True)

        pub = _parse_numeric_date(date_text)
        if pub is None:
            continue
        if pub < cutoff:
            continue

        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "Insurance Europe",
        })

    logger.info("Insurance Europe: %d notizie negli ultimi %d giorni", len(results), days)
    return results


# ---------------------------------------------------------------------------
# ANIA — Comunicati (Cloudflare-protected, requires headless Chrome)
# URL: https://www.ania.it/comunicati
# Structure: article.press-release-teaser  title: h3 a  date: time[datetime]
# ---------------------------------------------------------------------------

_ANIA_URL = "https://www.ania.it/comunicati"
_ANIA_BASE = "https://www.ania.it"


def _get_selenium(url: str) -> Optional[BeautifulSoup]:
    """Fetch a Cloudflare-protected page using headless Chrome."""
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
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.thumb-pubblicazioni"))
            )
        except Exception:
            pass  # parse whatever loaded

        html = driver.page_source
        driver.quit()
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.error("Selenium error fetching %s: %s", url, e)
        return None


def scrape_ania_comunicati(days: int) -> list:
    cutoff = _cutoff(days)
    results = []

    soup = _get_selenium(_ANIA_URL)
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
        date_text = date_el.get_text(strip=True)

        pub = _parse_italian_date(date_text)
        if pub is None:
            continue
        if pub < cutoff:
            continue

        results.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": pub.strftime("%d/%m/%Y"),
            "source": "ANIA",
        })

    logger.info("ANIA comunicati: %d notizie negli ultimi %d giorni", len(results), days)
    return results
