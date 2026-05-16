# Alert Normativo — Automazione Newsletter SCS Consulting

## Cos'è questo progetto

Script Python che automatizza la produzione della newsletter normativa settimanale "Alert Normativo" di SCS Consulting. Il flusso è diviso in due fasi lanciate manualmente dall'operatore:

**Fase 1 — `--scrape`:**
1. Scraping notizie da ~50 fonti RSS e HTML (→ `docs/fonti.md`)
2. Sintesi e categorizzazione via Claude API (→ `docs/categorizzazione.md`)
3. Salvataggio Excel in `output/DB_EXCEL/` (→ `docs/excel_schema.md`)
4. Notifica manuale al responsabile (email non ancora implementata → `docs/email_config.md`)

**Fase 2 — `--publish`** (dopo review responsabile):
1. Lettura Excel revisionato da `output/DB_EXCEL/`
2. Generazione PPTX dal template `assets/_CLEAN.pptx` (→ `docs/pptx_layout.md`)
3. Salvataggio PPTX in `output/ALERT_PPT/`

Il responsabile apre la PPTX, rimuove eventuali slide vuote, converte in PDF e invia la newsletter.

## Stack

- Python 3.11
- `requests`, `beautifulsoup4`, `feedparser` — scraping RSS e HTML statico
- `selenium` + `webdriver-manager` — scraping pagine JS-rendered (ANIA, BdI, BIS, GU, EUR-Lex)
- `anthropic` SDK — Claude API, modello **`claude-haiku-4-5`**
- `openpyxl` — lettura/scrittura Excel
- `python-pptx` — generazione PPTX

## Struttura progetto

```
alert_normativo/
├── CLAUDE.md
├── .env                              # non committare mai
├── .env.example
├── requirements.txt
├── main.py                           # entry point: --scrape / --publish
├── config.py                         # fonti, FONTE_AMBITO, parametri edizione
├── docs/
│   ├── categorizzazione.md           # logica Claude API + prompt aggiornati
│   ├── excel_schema.md               # schema foglio "Monitoraggio finance"
│   ├── pptx_layout.md                # specifiche layout e paginazione PPTX
│   ├── fonti.md                      # elenco completo fonti con URL e metodo accesso
│   └── email_config.md               # configurazione email (non ancora implementata)
├── assets/
│   ├── Template_settimanale.xlsx     # template DB Excel
│   ├── _CLEAN.pptx                   # template PPTX — 6 slide identiche pronte
│   ├── icon_banking.png              # icone sezione per PPTX
│   ├── icon_insurance.png
│   ├── icon_cross_finance.png
│   └── icon_approfondimenti.png
├── scraper/
│   ├── __init__.py
│   ├── rss_scraper.py                # RSS via feedparser
│   └── html_scraper.py               # HTML statico + Selenium (~37 funzioni scraper)
├── ai/
│   ├── __init__.py
│   └── synthesizer.py                # batch Claude API, retry, strip markdown
├── output/
│   ├── __init__.py
│   ├── excel_logger.py               # copia template, append righe, deduplicazione URL
│   ├── pptx_generator.py             # genera PPTX da 6 slide pre-esistenti
│   └── uploader.py                   # stub futuro Google Drive / OneDrive
└── tests/
    ├── __init__.py
    └── test_rss_scraper.py
```

## Architettura chiave

### `config.py`
- `RSS_SOURCES` — lista di tuple `(url, nome_fonte)` per feedparser
- `HTML_SOURCES` — lista di tuple `(nome_funzione, nome_fonte)` per html_scraper
- `FONTE_AMBITO` — dict che mappa `nome_fonte → "BANKING"|"INSURANCE"|"CROSS FINANCE"`
- `CATEGORY_ORDER = ["BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI"]`

### `scraper/rss_scraper.py`
- `scrape_rss(url, source_name, days)` → `list[dict]`
- Ogni notizia include il campo `ambito_fonte` (da `config.FONTE_AMBITO`) usato da Claude API per la categorizzazione

### `scraper/html_scraper.py`
- ~37 funzioni scraper, una per ogni sezione di ogni fonte
- Helper interni: `_get()` (statico), `_get_selenium()` (JS), `_parse_*_date()` per vari formati data
- Fonti Selenium: ANIA, Banca d'Italia, BIS/BCBS, Gazzetta Ufficiale, EUR-Lex (best-effort)
- Fonti best-effort (possono restituire 0): EUR-Lex (202/throttled), IOSCO (403)

### `ai/synthesizer.py`
- `synthesize_all(client, news_items)` → `list[dict]`
- Batch di 10 notizie per chiamata, max 2 retry su JSON non valido
- Output per notizia: `{categoria, fonte, titolo, descrizione, data_originale, url, includi_in_pptx}`
- I marker grassetto `**...**` vengono rimossi prima della scrittura su Excel

### `output/excel_logger.py`
- `create_excel(template_path, output_path)` — copia template
- `append_news(output_path, news_items)` — aggiunge righe, deduplicazione per URL
- Output: `output/DB_EXCEL/monitoraggio_N{n}_{mese}{anno}.xlsx`

### `output/pptx_generator.py`
- Template `assets/_CLEAN.pptx` con 6 slide identiche pre-esistenti
- Paginazione: scorre le slide in ordine, quando `current_y > BOTTOM_CONTENT_Y` passa alla successiva
- Non crea mai nuove slide — se le 6 si esauriscono lancia `RuntimeError`
- Disegna: icona + intestazione sezione (bold), descrizione (10pt regular), data (centrato), link cliccabile (blu navy)
- Output: `output/ALERT_PPT/alert_normativo_N{n}_{mese}{anno}_{YYYYMMDD}.pptx`

## Regole di sviluppo

- Non sovrascrivere mai dati esistenti nel file Excel
- Gestire sempre gli errori per singola fonte: se una è irraggiungibile, continuare con le altre
- I font delle descrizioni PPTX devono essere `run.font.bold = False` esplicitamente (altrimenti ereditano dal master)
- `FONTE_AMBITO` in `config.py` è la fonte di verità per la categorizzazione per ambito

## Variabili d'ambiente

```
# Claude API
ANTHROPIC_API_KEY=

# Parametri edizione
EDIZIONE_NUMERO=1
EDIZIONE_MESE=Maggio
EDIZIONE_ANNO=2026
FINESTRA_GIORNI=7

# Upload futuro (default: none)
UPLOAD_DESTINATION=none

# Email (non ancora implementata)
GMAIL_USER=
GMAIL_APP_PASSWORD=
EMAIL_NOTIFICA_DESTINATARIO=
```

## Version Control

- Repository GitHub privato: `https://github.com/JacSlev/alert-normativo`
- Sviluppo su PC personale (Mac, Python 3.11), test su PC aziendale (Windows, Python 3.11)
- Flusso: `git push` da Mac → `git pull` su PC aziendale
- Il file `.env` con le credenziali resta solo in locale, non va mai su GitHub
