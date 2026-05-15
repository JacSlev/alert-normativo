# Specifiche layout PPTX

## Riferimento visivo

Il template di riferimento è `assets/Template_settimanale.pptx`. È la fonte di verità per layout, colori, font e spaziature. Questa specifica descrive la struttura, ma il file reale prevale in caso di discrepanza.

## Implementazione

Usare **python-pptx** per compilare il template esistente. Non ricreare il layout da zero — aprire `assets/Template_settimanale.pptx`, trovare i placeholder e sostituire il testo "TBD" con i dati reali.

## Struttura slide

Il template ha una singola slide con:

**Header:**
- Titolo "Alert Normativo"
- Numero edizione (es. "N. 2") e mese/anno (es. "Maggio 2026")
- Label "SOMMARIO — Principali aggiornamenti normativi"

**4 sezioni in ordine:**
1. BANKING
2. INSURANCE
3. CROSS FINANCE
4. APPROFONDIMENTI

**Ogni notizia nella slide ha 3 elementi:**
- Testo descrizione (placeholder "TBD")
- Data (placeholder "/05/2026")
- Link cliccabile (placeholder "Link")

**Footer:**
- "Per informazioni e approfondimenti rivolgersi al Presidio Normativo Finance di SCS al seguente indirizzo e-mail: alert@scsconsulting.it"
- Disclaimer in corsivo: "Il presente documento comprende le news identificate come coerenti con il focus aziendale dell'Area Finance ed in linea con gli eventuali interessi correlati"

## Logica di compilazione

- Se una sezione non ha notizie con "Includi in PPTX = SI", nascondere l'intera sezione
- Sostituire ogni "TBD" con la descrizione della notizia (colonna G del foglio Excel)
- Sostituire ogni placeholder data con la data pubblicazione (colonna D)
- Sostituire ogni "Link" con l'URL cliccabile (colonna I)
- Aggiornare numero edizione e mese/anno nell'header

## Nome file output

`alert_normativo_N{numero}_{mese}{anno}.pptx`

Esempio: `alert_normativo_N2_Maggio2026.pptx`

Salvato in: `output/`
