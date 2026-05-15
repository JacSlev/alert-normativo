# Schema Excel — DB Monitoraggio Alert Normativo

## File

`Template_settimanale.xlsx` — file template in `assets/` (già pulito con solo il foglio Monitoraggio finance). Lo script lavora su una copia in `output/` rinominata con numero edizione e data.

Nome file output: `monitoraggio_N{numero}_{mese}{anno}.xlsx`
Esempio: `monitoraggio_N2_Maggio2026.xlsx`

## Struttura — 1 foglio

### Foglio: Monitoraggio finance

Intestazione riga 1: **MONITORAGGIO FINANCE**
Intestazione riga 2: nomi colonne

| Colonna | Nome | Tipo | Note |
|---|---|---|---|
| A | ID | Numero | Progressivo automatico |
| B | Macro-Ambito | Testo | Es. "Banking", "Insurance", "Cross Finance" |
| C | Fonte | Testo | Es. "EBA", "IVASS" |
| D | Data | Data gg/mm/aaaa | Data pubblicazione notizia originale |
| E | Data Alert | Data gg/mm/aaaa | Data inserimento nell'alert |
| F | Titolo news | Testo | Titolo originale o generato da Claude API |
| G | Descrizione | Testo | Sintesi generata da Claude API (4-6 righe) |
| H | Includi in PPTX | Testo | SI / NO — precompilato da Claude API, modificabile dal responsabile |
| I | Link | Testo | URL fonte originale |

## Comportamento dello script

### Fase --scrape
- Copia `assets/Template_settimanale.xlsx` in `output/monitoraggio_N{n}_{mese}{anno}.xlsx`
- Popola il foglio "Monitoraggio finance" con le notizie elaborate da Claude API
- Colonna H (Includi in PPTX): precompilata con SI se pertinente=true, NO se pertinente=false
- Deduplicazione: non aggiungere una notizia se l'URL è già presente nel foglio

### Fase --publish
- Legge il foglio "Monitoraggio finance" dal file revisionato dal responsabile
- Filtra solo le righe con colonna H = "SI"
- Passa i dati al generatore PPTX

## Formattazione

- Intestazione riga 1: grassetto, sfondo grigio `#D9D9D9`
- Filtri attivi su tutte le colonne
- Larghezze colonne ottimizzate automaticamente
- Colonna G (Descrizione): larghezza fissa 60 caratteri, wrap text attivo
