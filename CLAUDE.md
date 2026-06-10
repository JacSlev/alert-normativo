# Alert Normativo — Automazione Newsletter SCS Consulting

## Cos'è questo progetto

Script Python che automatizza la produzione della newsletter normativa settimanale "Alert Normativo" di SCS Consulting. Il flusso è diviso in due fasi lanciate manualmente dall'operatore:

**Fase 1 — `--scrape`:**
1. Scraping notizie da 53 fonti RSS e HTML (11 RSS + 42 HTML → `docs/fonti.md`)
2. Sintesi e categorizzazione via Claude API (→ `docs/categorizzazione.md`)
3. Salvataggio Excel in `output/DB_EXCEL/` (→ `docs/excel_schema.md`)
4. Notifica manuale al responsabile (email non ancora implementata → `docs/email_config.md`)

**Fase 2 — `--publish`** (dopo review responsabile):
1. Lettura Excel revisionato da `output/DB_EXCEL/`
2. Generazione PPTX dal template `assets/_CLEAN.pptx` (→ `docs/pptx_layout.md`)
3. Salvataggio PPTX in `output/ALERT_PPT/`

Il responsabile apre la PPTX, rimuove eventuali slide vuote, converte in PDF e invia la newsletter.

## Stack

- Python 3.14 (versione del venv di progetto su Windows; `requirements.txt` non vincola una versione minima)
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
├── config.py                         # fonti, FONTE_AMBITO, parametri API
├── docs/
│   ├── categorizzazione.md           # logica Claude API + prompt aggiornati
│   ├── excel_schema.md               # schema foglio "Monitoraggio finance"
│   ├── pptx_layout.md                # specifiche layout e paginazione PPTX
│   ├── fonti.md                      # elenco completo fonti con URL e metodo accesso
│   └── email_config.md               # configurazione email (non ancora implementata)
├── assets/
│   ├── Template_settimanale.xlsx     # template DB Excel
│   ├── Template_settimanale.pptx     # vecchio template PPTX con slot TBD (TEMPLATE_PPTX_OLD, non più usato)
│   ├── _CLEAN.pptx                   # template PPTX — 6 slide identiche pronte
│   ├── Link_Monitoraggio.xlsx        # elenco link monitoraggio (LINK_MONITORAGGIO in config.py)
│   ├── icon_banking.png              # icone sezione per PPTX
│   ├── icon_insurance.png
│   ├── icon_cross_finance.png
│   └── icon_approfondimenti.png
├── scraper/
│   ├── __init__.py
│   ├── rss_scraper.py                # RSS via feedparser
│   ├── html_scraper.py               # HTML statico + Selenium (42 funzioni scraper)
│   └── date_utils.py                 # iso_week_cutoff(), previous_iso_week_window() — finestra settimana ISO precedente
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
    ├── test_rss_scraper.py
    ├── test_html_scraper.py
    ├── test_date_utils.py
    ├── test_excel_logger.py
    └── test_synthesizer.py
```

## Architettura chiave

### `config.py`
- `RSS_SOURCES` — lista di tuple `(url, nome_fonte)` per feedparser
- `HTML_SOURCES` — lista di tuple `(nome_funzione, nome_fonte)` per html_scraper
- `FONTE_AMBITO` — dict che mappa `nome_fonte → "BANKING"|"INSURANCE"|"CROSS FINANCE"`

### `scraper/date_utils.py`
- `iso_week_cutoff(_now=None)` → `datetime` — restituisce lunedì 00:00:00 UTC della settimana ISO precedente
- `previous_iso_week_window(_now=None)` → `tuple[datetime, datetime]` — restituisce `(prev_monday, this_monday)` come finestra half-open `[start, end)` UTC
- `_window_override` — variabile di modulo (`None` di default); se impostata, `get_window()` restituisce questa invece della settimana ISO
- `set_window(start, end)` — imposta `_window_override`; chiamato da `main.py --scrape` dopo `parse_window()`
- `get_window(_now=None)` → `tuple[datetime, datetime]` — restituisce l'override se impostato, altrimenti `previous_iso_week_window()`
- `parse_window(dal, al)` → `tuple[datetime, datetime]` — converte le stringhe `DD/MM/YYYY` in UTC; `end = al + 1 giorno` (half-open); termina con `sys.exit(1)` su formato errato o range invertito

### `scraper/rss_scraper.py`
- `scrape_rss(url, source_name, days)` → `list[dict]`
- La finestra di scraping viene da `get_window()` (usa l'override se impostato da `--scrape`, altrimenti settimana ISO precedente); il parametro `days` è ignorato
- Ogni notizia include il campo `ambito_fonte` (da `config.FONTE_AMBITO`) usato da Claude API per la categorizzazione

### `scraper/html_scraper.py`
- 42 funzioni scraper pubbliche `scrape_*`, una per ogni sezione di ogni fonte
- Helper interni: `_get()` (statico), `_get_selenium()` (JS), `_parse_*_date()` per vari formati data
- `_cutoff(days) → tuple[datetime, datetime]` — delega a `get_window()` e restituisce `(start, end)`; il parametro `days` è ignorato
- `scrape_eurlex`: i parametri URL `DTA`/`DTB` usano `start.date()` e `(end - 1 day).date()` dalla finestra ISO — coerenti col filtro sui risultati parsati
- `_scrape_bdi_form_results_page(url, label, source_name, days)` — helper Selenium condiviso da `scrape_bdi_approfondimenti` e `scrape_bdi_ricerche`; attende `#bdi_form_results li` e legge `a.bdi-result-title` + `div.bdi-result-date`
- Fonti Selenium: ANIA, Banca d'Italia, BIS/BCBS, Gazzetta Ufficiale, EUR-Lex (best-effort)
- Fonti best-effort (possono restituire 0): EUR-Lex (202/throttled), IOSCO (403)

### `ai/synthesizer.py`
- `synthesize_all(client, news_items)` → `list[dict]`
- Batch di 10 notizie per chiamata, max 2 retry su JSON non valido
- Output per notizia: `{categoria, fonte, titolo, descrizione, data_originale, url, includi_in_pptx}`
- I marker grassetto `**...**` vengono rimossi prima della scrittura su Excel

### `output/excel_logger.py`
- `CATEGORY_ORDER = ["BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI"]` — definita qui e duplicata in `pptx_generator.py` (non esiste in `config.py`)
- `get_output_path()` → `str` — restituisce sempre `output/DB_EXCEL/alert_normativo_DB.xlsx` (file unico permanente, nessun parametro)
- `ensure_excel_exists(template_path, output_path)` → `bool` — crea il file da template se non esiste, restituisce `True` se creato, `False` se già esistente
- `count_existing_rows(output_path)` → `int` — conta le righe dati con ID valorizzato a partire da `DATA_START_ROW`
- `append_news(output_path, news_items)` — aggiunge righe, deduplicazione per URL; popola automaticamente **colonna K** (mese odierno `MM`) e **colonna L** (anno odierno `AAAA`)
- `_create_backup(output_path)` — backup rolling `alert_normativo_DB.backup.xlsx` (stessa cartella) creato da `append_news` subito prima di ogni `wb.save`, con lo stato pre-modifica del file; se la copia fallisce logga `[WARNING]` e procede
- `read_approved_news(excel_path, edizione_numero, mese="", anno="")` — legge il foglio revisionato e restituisce un dict `{categoria: [notizie]}` filtrando: colonna H = "SI", colonna J = `edizione_numero`, colonna K = `mese` (se non vuoto — il flusso `--publish` non lo passa più), colonna L = `anno` (se non vuoto)
- `count_filter_stages(excel_path, edizione_numero, anno)` → `dict` — conteggi diagnostici a stadi (righe → approvate H → edizione J → anno L); usato da `generate_pptx` per spiegare un filtro a risultato vuoto

### `output/pptx_generator.py`
- Template `assets/_CLEAN.pptx` con 6 slide identiche pre-esistenti
- Legge i dati approvati tramite `excel_logger.read_approved_news()` (filtro: colonna H = "SI", colonna J = `--edizione`, colonna L = `--anno`; la colonna K **non** filtra — `--mese` serve solo per nome file e riquadro edizione)
- Se il filtro restituisce 0 notizie: stampa una diagnostica a stadi (`count_filter_stages`) con suggerimento mirato e termina con `sys.exit(1)` senza generare la PPTX
- `get_output_path(edizione, mese, anno)` → `output/ALERT_PPT/{anno}/Alert_Normativo_n.{edizione}-{mese}.pptx`
- Paginazione: scorre le slide in ordine, quando `current_y > BOTTOM_CONTENT_Y` passa alla successiva
- Non crea mai nuove slide — se le 6 si esauriscono lancia `RuntimeError`
- Disegna: icona + intestazione sezione (bold), descrizione (10pt regular), data (centrato), link cliccabile (blu navy)

## Regole di sviluppo

- Non sovrascrivere mai dati esistenti nel file Excel
- Gestire sempre gli errori per singola fonte: se una è irraggiungibile, continuare con le altre
- I font delle descrizioni PPTX devono essere `run.font.bold = False` esplicitamente (altrimenti ereditano dal master)
- `FONTE_AMBITO` in `config.py` è la fonte di verità per la categorizzazione per ambito

### Convenzioni test

- Nei test non usare mai `datetime.now() - timedelta(days=N)` per costruire date di pubblicazione — i test diventano dipendenti dalla data corrente e falliscono a settimane diverse
- Usare sempre datetime espliciti (es. `datetime(2026, 5, 13, tzinfo=timezone.utc)`) e mockare `scraper.html_scraper.get_window` (o `scraper.rss_scraper.get_window`) con `return_value=(FIXED_START, FIXED_END)`
- Le costanti `FIXED_START` / `FIXED_END` nel file di test definiscono la finestra pinned; le date "in-window" e "out-of-window" vanno scelte rispetto a quella finestra

## Variabili d'ambiente

```
# Claude API
ANTHROPIC_API_KEY=

# Upload futuro (default: none)
UPLOAD_DESTINATION=none

# Email (non ancora implementata)
GMAIL_USER=
GMAIL_APP_PASSWORD=
EMAIL_NOTIFICA_DESTINATARIO=
```

I parametri di edizione (numero, mese, anno) **non** si configurano nel `.env` — vengono passati come flag CLI:
- `--scrape` richiede `--dal DD/MM/YYYY` e `--al DD/MM/YYYY`
- `--publish` richiede `--edizione N`, `--mese MM`, `--anno AAAA`

## Version Control

- Repository GitHub privato: `https://github.com/JacSlev/alert-normativo`
- Sviluppo su PC personale (Mac), test su PC aziendale (Windows, Python 3.14 — venv di progetto)
- Flusso: `git push` da Mac → `git pull` su PC aziendale
- Il file `.env` con le credenziali resta solo in locale, non va mai su GitHub
