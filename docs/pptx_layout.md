# Specifiche layout PPTX

## Template

Il template di riferimento è `assets/_CLEAN.pptx`. Contiene **6 slide identiche** già configurate con header, footer e grafica. Lo script non crea mai nuove slide — usa quelle pre-esistenti e le popola in ordine. Le slide vuote non vengono eliminate: le gestisce manualmente il responsabile.

## Implementazione — `output/pptx_generator.py`

### Logica di paginazione

```
Apri assets/_CLEAN.pptx → lista di 6 slide
slide_idx = 0, current_y = TOP_CONTENT_Y

Per ogni sezione (BANKING → INSURANCE → CROSS FINANCE → APPROFONDIMENTI):
  Se la sezione non ha notizie con "Includi in PPTX = SI" → salta
  Se current_y + altezza_intestazione > BOTTOM_CONTENT_Y → passa alla slide successiva
  Disegna intestazione sezione (icona + label in grassetto)
  Per ogni notizia della sezione:
    Calcola altezza_notizia in base al wrapping del testo
    Se current_y + altezza_notizia > BOTTOM_CONTENT_Y → passa alla slide successiva
    Disegna notizia (descrizione, data, link cliccabile)
```

Se le 6 slide si esauriscono prima della fine del contenuto, lo script lancia `RuntimeError` con istruzioni per aggiungere altre slide al template.

### Coordinate slide (EMU)

Formato slide: A4 portrait — 7,559,675 × 10,691,813 EMU

| Elemento | Valore EMU | Equivalente approssimativo |
|---|---|---|
| `TOP_CONTENT_Y` | 2,065,553 | Fondo header + 100k margine |
| `BOTTOM_CONTENT_Y` | 9,873,419 | Tetto footer |

### Colonne

| Colonna | Left (EMU) | Width (EMU) |
|---|---|---|
| Descrizione | 254,373 | 5,325,951 |
| Data | 5,580,324 | 866,037 |
| Link | 6,446,361 | 866,037 |

### Altezze e spaziature

| Elemento | Valore EMU |
|---|---|
| Intestazione sezione | 303,227 (~0.842 cm) |
| Spazio tra sezioni diverse | 180,000 (~0.500 cm) |
| Margine verticale tra notizie | 80,000 (~0.222 cm) |

### Wrapping testo

- `CHARS_PER_LINE = 79` — caratteri per riga per la stima del wrapping
- `LINE_HEIGHT_EMU = Pt(14)` → 177,800 EMU
- Altezza notizia = `max(1, righe_avvolte) × LINE_HEIGHT_EMU + 36,000 (padding)`

### Tipografia

| Elemento | Font | Dimensione | Stile |
|---|---|---|---|
| Intestazione sezione | Avenir Next LT Pro | 14pt | Bold, nero |
| Descrizione notizia | Avenir Next LT Pro | 10pt | Regular, nero |
| Data | Avenir Next LT Pro | 10pt | Regular, nero, centrato |
| Link | Avenir Next LT Pro | 10pt | Regular, blu navy (`#002060`), centrato, hyperlink |

### Icone sezione

Icone PNG in `assets/` per ogni sezione:

| Sezione | File |
|---|---|
| BANKING | `assets/icon_banking.png` |
| INSURANCE | `assets/icon_insurance.png` |
| CROSS FINANCE | `assets/icon_cross_finance.png` |
| APPROFONDIMENTI | `assets/icon_approfondimenti.png` |

Se il file icona non esiste, l'intestazione viene comunque disegnata (solo testo).

### Aggiornamento edizione

Il riquadro edizione (es. "N. 2 / Maggio 2026") viene individuato cercando la shape che contiene "N. " con un a-capo nel testo. I primi due run vengono aggiornati con numero e mese/anno.

## Nome file output

```
output/ALERT_PPT/{anno}/Alert_Normativo_n.{edizione}-{mese}.pptx
```

Esempio: `output/ALERT_PPT/2026/Alert_Normativo_n.2-06.pptx`

La directory `output/ALERT_PPT/{anno}/` viene creata automaticamente se non esiste.

## Flusso completo

1. Leggere `output/DB_EXCEL/alert_normativo_DB.xlsx` (revisionato dal responsabile)
2. Filtrare le righe con colonna H = "SI", colonna J = `--edizione`, colonna K = `--mese` (MM), colonna L = `--anno` (AAAA)
3. Raggruppare per categoria
4. Aprire `assets/_CLEAN.pptx`
5. Scorrere le 6 slide in ordine, disegnare il contenuto
6. Salvare il file in `output/ALERT_PPT/`
7. Il responsabile apre la PPTX, eventualmente elimina le slide vuote, converte in PDF e invia
