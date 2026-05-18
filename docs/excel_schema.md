# Schema Excel — DB Monitoraggio Alert Normativo

## File

`assets/Template_settimanale.xlsx` — file template con il foglio "Monitoraggio finance" già strutturato. Lo script crea una copia per ogni edizione.

Nome file output: `output/DB_EXCEL/monitoraggio_N{numero}_{mese}{anno}.xlsx`
Esempio: `output/DB_EXCEL/monitoraggio_N2_Maggio2026.xlsx`

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

## Comportamento dello script

### Fase --scrape (`output/excel_logger.py`)

- Copia `assets/Template_settimanale.xlsx` in `output/DB_EXCEL/monitoraggio_N{n}_{mese}{anno}.xlsx`
- Crea la directory `output/DB_EXCEL/` se non esiste
- Popola il foglio "Monitoraggio finance" con le notizie elaborate da Claude API (a partire dalla riga 3)
- Colonna H (Includi in PPTX): "SI" per BANKING/INSURANCE/CROSS FINANCE, "NO" per APPROFONDIMENTI
- Deduplicazione: non aggiungere una notizia se l'URL è già presente nel foglio (confronto colonna I)
- Chiamate ripetute sullo stesso file aggiungono righe senza sovrascrivere quelle esistenti

### Fase --publish (`output/pptx_generator.py`)

- Legge il foglio "Monitoraggio finance" dal file revisionato dal responsabile
- Filtra solo le righe che soddisfano **entrambe** le condizioni:
  - Colonna H = "SI" (case-insensitive) — approvata dal responsabile
  - Colonna J = valore di `EDIZIONE_NUMERO` nel `.env` — appartiene all'edizione corrente
- Se `EDIZIONE_NUMERO` non è valorizzato nel `.env`, lo script termina con errore esplicito
- Raggruppa le notizie per categoria (ordine fisso: BANKING → INSURANCE → CROSS FINANCE → APPROFONDIMENTI)
- Passa i dati al generatore PPTX

## Formattazione automatica

- Riga 2 (intestazione colonne): grassetto, sfondo grigio `#D9D9D9`
- Filtri automatici attivi su tutte le colonne
- Larghezze colonne ottimizzate automaticamente (max 50 caratteri)
- Colonna G (Descrizione): larghezza fissa 60 caratteri, wrap text attivo
