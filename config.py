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

# Email
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
EMAIL_NOTIFICA_DESTINATARIO = os.getenv("EMAIL_NOTIFICA_DESTINATARIO")

# Upload
UPLOAD_DESTINATION = os.getenv("UPLOAD_DESTINATION", "none")

# Paths
ASSETS_DIR = "assets"
OUTPUT_DIR = "output"
TEMPLATE_XLSX = f"{ASSETS_DIR}/Template_settimanale.xlsx"
TEMPLATE_PPTX = f"{ASSETS_DIR}/Template_settimanale.pptx"
LINK_MONITORAGGIO = f"{ASSETS_DIR}/Link_Monitoraggio.xlsx"

# RSS sources (MVP: EBA e EIOPA — aggiungere altre da docs/fonti.md)
RSS_SOURCES = [
    ("https://www.eba.europa.eu/rss.xml", "EBA"),
    ("https://www.eiopa.europa.eu/node/4816/rss_en", "EIOPA"),
]