import os
from dotenv import load_dotenv

load_dotenv()

# Parametri edizione
EDIZIONE_NUMERO = os.getenv("EDIZIONE_NUMERO", "")  # Required for --publish; no default
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

FONTE_AMBITO = {
    # Banking
    "EBA":                  "BANKING",
    "BCE":                  "BANKING",
    "BCE Publications":     "BANKING",
    "AMLA":                 "BANKING",
    "Banca d'Italia":       "BANKING",
    "BdI Ricerche":         "BANKING",
    "BIS":                  "BANKING",
    "BCBS":                 "BANKING",
    "ABI":                  "BANKING",
    "Dirittobancario banca":"BANKING",
    # Insurance
    "EIOPA":                "INSURANCE",
    "IVASS":                "INSURANCE",
    "ANIA":                 "INSURANCE",
    "Insurance Europe":     "INSURANCE",
    "IAIS":                 "INSURANCE",
    # Cross Finance
    "CONSOB":               "CROSS FINANCE",
    "Gazzetta Ufficiale":   "CROSS FINANCE",
    "EUR-Lex":              "CROSS FINANCE",
    "ICMA":                 "CROSS FINANCE",
    "FSB":                  "CROSS FINANCE",
    "EDPB":                 "CROSS FINANCE",
    "IOSCO":                "CROSS FINANCE",
    "Commissione Europea":  "CROSS FINANCE",
    "ESMA":                 "CROSS FINANCE",
    "EFRAG":                "CROSS FINANCE",
    "Eurosif":              "CROSS FINANCE",
    "Dirittobancario finanza": "CROSS FINANCE",
}

SECTION_ICONS = {
    "BANKING":         f"{ASSETS_DIR}/icon_banking.png",
    "INSURANCE":       f"{ASSETS_DIR}/icon_insurance.png",
    "CROSS FINANCE":   f"{ASSETS_DIR}/icon_cross_finance.png",
    "APPROFONDIMENTI": f"{ASSETS_DIR}/icon_approfondimenti.png",
}

# RSS sources
RSS_SOURCES = [
    # Banking
    ("https://www.eba.europa.eu/rss.xml",                                          "EBA"),
    ("https://www.ecb.europa.eu/rss/press.html",                                   "BCE"),
    ("https://www.abi.it/feed",                                                    "ABI"),
    ("https://www.dirittobancario.it/cat/flash-news/feed/",                        "Dirittobancario banca"),
    ("https://www.dirittobancario.it/cat/approfondimenti/banche-e-intermediari/feed/", "Dirittobancario banca"),
    # Insurance
    ("https://www.eiopa.europa.eu/node/4816/rss_en",                               "EIOPA"),
    # Cross Finance
    ("https://www.fsb.org/feed",                                                   "FSB"),
    ("https://www.edpb.europa.eu/feed/news_it",                                    "EDPB"),
    ("https://www.esma.europa.eu/rss.xml",                                         "ESMA"),
    ("https://www.eurosif.org/feed/",                                              "Eurosif"),
    ("https://www.dirittobancario.it/sez/finanza-e-mercati/feed/",                 "Dirittobancario finanza"),
]

# HTML sources: (scraper_function_name, display_name)
# Functions are imported in main.py from scraper.html_scraper
HTML_SOURCES = [
    # Insurance — IVASS (6 section pages, same ivass-doc-list structure)
    ("scrape_ivass_regolamenti",       "IVASS Regolamenti"),
    ("scrape_ivass_provvedimenti",     "IVASS Provvedimenti"),
    ("scrape_ivass_comunicazioni",     "IVASS Comunicazioni"),
    ("scrape_ivass_lettere",           "IVASS Lettere"),
    ("scrape_ivass_consultazioni",     "IVASS Consultazioni"),
    ("scrape_ivass_esiti_cons",        "IVASS Esiti cons."),
    ("scrape_ivass_media",             "IVASS Media"),
    # Insurance — ANIA (Selenium, thumb-pubblicazioni structure)
    ("scrape_ania_comunicati",         "ANIA comunicati"),
    ("scrape_ania_pubblicazioni",      "ANIA pubblicazioni"),
    ("scrape_ania_cat_111377",         "ANIA"),
    ("scrape_ania_cat_53704",          "ANIA"),
    ("scrape_ania_cat_53705",          "ANIA"),
    ("scrape_ania_cat_53703",          "ANIA"),
    ("scrape_ania_cat_52472",          "ANIA"),
    # Insurance — Insurance Europe
    ("scrape_insurance_europe_news",         "Insurance Europe"),
    ("scrape_insurance_europe_publications", "Insurance Europe"),
    ("scrape_insurance_europe_events",       "Insurance Europe"),
    # Insurance — EIOPA HTML
    ("scrape_eiopa_events",            "EIOPA"),
    ("scrape_eiopa_doc_library",       "EIOPA"),
    ("scrape_eiopa_speeches",          "EIOPA"),
    ("scrape_eiopa_interviews",        "EIOPA"),
    # Banking — Banca d'Italia
    ("scrape_bdi_homepage",            "Banca d'Italia"),
    ("scrape_bdi_archivio_norme",      "Banca d'Italia"),
    ("scrape_bdi_consultazioni",       "Banca d'Italia"),
    ("scrape_bdi_approfondimenti",     "Banca d'Italia"),
    ("scrape_bdi_ricerche",            "BdI Ricerche"),
    ("scrape_bdi_comunicati_bce",      "Banca d'Italia"),
    # Banking — BIS/BCBS
    ("scrape_bis_bcbs",                "BIS"),
    # Banking — BCE Publications (tecnici, working papers)
    ("scrape_bce_publications",        "BCE Publications"),
    # Banking — AMLA
    ("scrape_amla_news",               "AMLA"),
    ("scrape_amla_publications",       "AMLA"),
    # Cross Finance
    ("scrape_consob",                  "CONSOB"),
    ("scrape_gazzetta_ufficiale",      "Gazzetta Ufficiale"),
    ("scrape_eurlex",                  "EUR-Lex"),
    ("scrape_icma",                    "ICMA"),
    ("scrape_iosco",                   "IOSCO"),
    ("scrape_commissione_europea",     "Commissione Europea"),
    ("scrape_efrag",                   "EFRAG"),
    ("scrape_commissione_ue_news",     "Commissione Europea"),
    ("scrape_iais_news",               "IAIS"),
    ("scrape_iais_consultations",      "IAIS"),
    ("scrape_iais_events",             "IAIS"),
]