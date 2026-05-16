import os
from dotenv import load_dotenv

load_dotenv()

# Parametri edizione
EDIZIONE_NUMERO = os.getenv("EDIZIONE_NUMERO", "1")
EDIZIONE_MESE = os.getenv("EDIZIONE_MESE", "Maggio")
EDIZIONE_ANNO = os.getenv("EDIZIONE_ANNO", "2026")
FINESTRA_GIORNI = int(os.getenv("FINESTRA_GIORNI", "7"))

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Upload
UPLOAD_DESTINATION = os.getenv("UPLOAD_DESTINATION", "none")

# Paths
ASSETS_DIR = "assets"
OUTPUT_DIR = "output"
TEMPLATE_XLSX      = f"{ASSETS_DIR}/Template_settimanale.xlsx"
TEMPLATE_PPTX_OLD  = f"{ASSETS_DIR}/Template_settimanale.pptx"   # vecchio template con slot TBD
TEMPLATE_PPTX      = f"{ASSETS_DIR}/_CLEAN.pptx"                  # template clean — usato dal generatore
LINK_MONITORAGGIO  = f"{ASSETS_DIR}/Link_Monitoraggio.xlsx"

SECTION_ICONS = {
    "BANKING":         f"{ASSETS_DIR}/icon_banking.png",
    "INSURANCE":       f"{ASSETS_DIR}/icon_insurance.png",
    "CROSS FINANCE":   f"{ASSETS_DIR}/icon_cross_finance.png",
    "APPROFONDIMENTI": f"{ASSETS_DIR}/icon_approfondimenti.png",
}

# RSS sources
RSS_SOURCES = [
    ("https://www.eba.europa.eu/rss.xml", "EBA"),
    ("https://www.eiopa.europa.eu/node/4816/rss_en", "EIOPA"),
    ("https://www.ecb.europa.eu/rss/press.html", "BCE"),
]

# HTML sources: (scraper_function_name, display_name)
# Functions are imported in main.py from scraper.html_scraper
HTML_SOURCES = [
    ("scrape_ivass_regolamenti", "IVASS"),
    ("scrape_insurance_europe_news", "Insurance Europe"),
    ("scrape_ania_comunicati", "ANIA"),
]