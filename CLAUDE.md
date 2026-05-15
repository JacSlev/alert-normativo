# Alert Normativo — Automazione Newsletter SCS Consulting

## Cos'è questo progetto

Script Python che automatizza la produzione della newsletter normativa settimanale "Alert Normativo" di SCS Consulting. Il flusso è diviso in due fasi lanciate manualmente dall'operatore:

**Fase 1 — `--scrape`:**
1. Scraping notizie dalle fonti → `assets/Link_Monitoraggio.xlsx`
2. Sintesi e categorizzazione via Claude API → `docs/categorizzazione.md`
3. Salvataggio Excel in `output/` → `docs/excel_schema.md`
4. Email di notifica al responsabile

**Fase 2 — `--publish`** (dopo review responsabile):
1. Lettura Excel revisionato da `output/`
2. Generazione PPTX dal template → `docs/pptx_layout.md`
3. Salvataggio PPTX in `output/`

Il responsabile converte la PPTX in PDF e invia la newsletter manualmente.

## Stack

- Python 3.11+
- `requests`, `beautifulsoup4`, `feedparser` per scraping
- `anthropic` SDK per Claude API — modello **`claude-haiku-4-5`**
- `openpyxl` per Excel
- `python-pptx` per generazione PPTX
- `smtplib` per email di notifica (Gmail)

## Struttura progetto

```
alert_normativo/
├── CLAUDE.md
├── .env                        # non committare mai
├── .env.example
├── requirements.txt
├── main.py                     # entry point: --scrape / --publish
├── config.py                   # fonti e parametri
├── docs/
│   ├── categorizzazione.md
│   ├── excel_schema.md
│   ├── pptx_layout.md
│   └── email_config.md
├── assets/
│   ├── Link_Monitoraggio.xlsx      # fonti da monitorare
│   ├── Template_settimanale.xlsx   # template DB Excel
│   ├── Template_settimanale.pptx   # template output PPTX
│   └── logo_scs.png
├── scraper/
│   ├── __init__.py
│   ├── rss_scraper.py
│   └── html_scraper.py
├── ai/
│   ├── __init__.py
│   └── synthesizer.py
└── output/
    ├── __init__.py
    ├── pptx_generator.py
    ├── excel_logger.py
    ├── email_sender.py
    └── uploader.py             # opzionale, per Google Drive / OneDrive futuro
```

## Regole di sviluppo

- Sviluppare e testare un modulo alla volta: scraper → synthesizer → excel → pptx → email
- Flag `--scrape` e `--publish` su main.py: due fasi separate
- Per i test iniziali usare solo EBA e EIOPA, poi aggiungere le altre fonti
- Non sovrascrivere mai dati esistenti nel file Excel
- Gestire sempre gli errori per singola fonte: se una è irraggiungibile, continuare con le altre

## Variabili d'ambiente richieste

```
# Claude API
ANTHROPIC_API_KEY=

# Email notifica (Gmail per test)
GMAIL_USER=tua@gmail.com
GMAIL_APP_PASSWORD=
EMAIL_NOTIFICA_DESTINATARIO=responsabile@email.it

# Parametri edizione
EDIZIONE_NUMERO=1
EDIZIONE_MESE=Maggio
EDIZIONE_ANNO=2026
FINESTRA_GIORNI=7

# Upload futuro (default: none)
UPLOAD_DESTINATION=none
# UPLOAD_DESTINATION=google_drive
# UPLOAD_DESTINATION=onedrive
```
