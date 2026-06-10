# Schema Excel — DB Monitoraggio Alert Normativo

## File

`assets/Template_settimanale.xlsx` — file template con il foglio "Monitoraggio finance" già strutturato (include le colonne K e L). Lo script crea il file una volta sola e vi accumula tutte le edizioni successive.

Nome file output: `output/DB_EXCEL/alert_normativo_DB.xlsx` (fisso, unico per tutto il progetto)

## Struttura — 1 foglio

### Foglio: Monitoraggio finance

| Riga | Contenuto |
|---|---|
| 1 | Intestazione generale: "MONITORAGGIO FINANCE" (merge celle, grassetto) |
| 2 | Nomi colonne (riga usata per i filtri automatici) |
| 3+ | Dati — una riga per notizia |

### Colonne

| Colonna | Nome | Tipo | Note |
|---|---|---|---|
| A | ID | Numero | Progressivo automatico |
| B | Macro-Ambito | Testo | Es. "BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI" |
| C | Fonte | Testo | Es. "EBA", "IVASS", "Banca d'Italia" |
| D | Data | Data gg/mm/aaaa | Data pubblicazione notizia originale |
| E | Data Alert | Data gg/mm/aaaa | Data inserimento nell'alert (data odierna) |
| F | Titolo news | Testo | Titolo generato da Claude API (max 15 parole, senza markdown) |
| G | Descrizione | Testo | Sintesi generata da Claude API (4-6 righe, senza marker `**`) |
| H | Includi in PPTX | Testo | SI / NO — precompilato da Claude API, modificabile dal responsabile |
| I | Link | Testo | URL fonte originale |
| J | Numero Edizione | Testo | Numero progressivo dell'edizione — valorizzato **manualmente** dal responsabile dopo la review; lo scraper non scrive mai su questa colonna |
| K | Mese | Testo | Mese di **inserimento** in formato `MM` (es. `"06"`) — popolato automaticamente da `append_news` con la data odierna di esecuzione dello scraping; **non** usata come filtro in fase `--publish` (solo tracciamento) |
| L | Anno | Testo | Anno di **inserimento** in formato `AAAA` (es. `"2026"`) — popolato automaticamente da `append_news` con la data odierna di esecuzione dello scraping; usata come filtro in fase `--publish` |

## Comportamento dello script

### Fase --scrape (`output/excel_logger.py`)

- Se `output/DB_EXCEL/alert_normativo_DB.xlsx` non esiste, lo crea copiando `assets/Template_settimanale.xlsx`; altrimenti lo apre e aggiunge righe in coda
- Crea la directory `output/DB_EXCEL/` se non esiste
- Popola il foglio "Monitoraggio finance" con le notizie elaborate da Claude API (a partire dalla riga 3)
- Colonna H (Includi in PPTX): "SI" per BANKING/INSURANCE/CROSS FINANCE, "NO" per APPROFONDIMENTI
- Colonne K e L: popolate automaticamente con mese (`MM`) e anno (`AAAA`) della data di esecuzione
- Deduplicazione: non aggiungere una notizia se l'URL è già presente nel foglio (confronto colonna I)
- Prima di ogni salvataggio crea/sovrascrive il backup `output/DB_EXCEL/alert_normativo_DB.backup.xlsx` con lo stato precedente del file (se la copia fallisce, logga un warning e procede)
- Chiamate ripetute sullo stesso file aggiungono righe senza sovrascrivere quelle esistenti

### Fase --publish (`output/pptx_generator.py`)

- Legge il foglio "Monitoraggio finance" da `output/DB_EXCEL/alert_normativo_DB.xlsx`
- Filtra solo le righe che soddisfano **tutte** le condizioni:
  - Colonna H = "SI" (case-insensitive) — approvata dal responsabile
  - Colonna J = valore di `--edizione` — appartiene a questa edizione (i numeri edizione ripartono da 1 ogni anno)
  - Colonna L = valore di `--anno` (AAAA) — anno di inserimento della riga (disambigua le edizioni tra anni)
- La colonna K **non** è usata come filtro: resta una colonna informativa di tracciamento. Il flag `--mese` serve solo per il nome file e per il riquadro edizione sulla slide
- Se manca uno dei flag `--edizione`, `--mese`, `--anno`, lo script termina con errore esplicito
- Se il filtro non trova **nessuna** notizia, lo script termina con errore bloccante (nessuna PPTX generata) stampando una diagnostica a stadi — righe totali → approvate (H) → edizione (J) → anno (L) — con un suggerimento sul filtro che ha azzerato il risultato
- **Nota su K/L:** le colonne K e L contengono il mese/anno in cui la riga è stata **scritta** da `--scrape` (data di esecuzione), non un campo "edizione". Solo L partecipa al filtro di `--publish`; il caso raro di scraping a cavallo d'anno rispetto alla pubblicazione viene segnalato dalla diagnostica
- Raggruppa le notizie per categoria (ordine fisso: BANKING → INSURANCE → CROSS FINANCE → APPROFONDIMENTI)
- Passa i dati al generatore PPTX

## Formattazione automatica

- Riga 2 (intestazione colonne): grassetto, sfondo grigio `#D9D9D9`
- Filtri automatici attivi su tutte le colonne
- Larghezze colonne ottimizzate automaticamente (max 50 caratteri)
- Colonna G (Descrizione): larghezza fissa 60 caratteri, wrap text attivo
