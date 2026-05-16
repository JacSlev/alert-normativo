# Logica di categorizzazione

## 4 sezioni fisse

### BANKING
Vigilanza bancaria e normativa prudenziale per enti creditizi.

Includere notizie su: requisiti patrimoniali (CRR/CRD IV-VI), framework di Basilea (Basilea III/IV, FRTB), modelli interni di rischio (IRB, modelli di rischio di mercato/operativo/credito), antiriciclaggio e contrasto al finanziamento del terrorismo (AML/CFT), shadow banking e large exposures, segnalazioni di vigilanza (COREP, FINREP, AnaCredit), stress test bancari, SREP, risoluzione bancaria (BRRD, SRM), EMIR e derivati OTC, fintech e open banking, crowdfunding (lato bancario), Early Warning Systems, NPL e qualità degli attivi.

Autorità tipiche: EBA, Banca d'Italia, BCE, Comitato di Basilea, BIS/BCBS, ABI.

---

### INSURANCE
Vigilanza assicurativa e normativa prudenziale per imprese di assicurazione.

Includere notizie su: Solvency II (Pilastro I, II, III — SCR, MCR, ORSA, reporting QRT), revisione Solvency II e Omnibus II, IRRD (Insurance Recovery and Resolution Directive), IDD (Insurance Distribution Directive), sistemi di garanzia assicurativa (IGS), prodotti assicurativi d'investimento (IBIP, unit-linked, polizze vita), KID/PRIIPs in ambito assicurativo, riassicurazione e trasferimento del rischio, catastrofi naturali e NatCat SCR, piccole imprese assicurative (SNCU/SNCG), IVASS (circolari, regolamenti, statistiche), value for money dei prodotti assicurativi, AI Act applicato al settore assicurativo.

Autorità tipiche: EIOPA, IVASS, IAIS, Insurance Europe, ANIA.

---

### CROSS FINANCE
Normativa trasversale a più settori finanziari o di carattere generale.

Includere notizie su: mercati finanziari e infrastrutture (MiFID II/MiFIR, MAR, Consolidated Tape, internalizzatori sistematici), gestione collettiva del risparmio (AIFMD, UCITS, fondi monetari MMF, EuVECA), finanza sostenibile ed ESG (CSRD, ESRS, Tassonomia UE, SFDR, greenwashing, TCFD), Testo Unico della Finanza (TUF) e riforma societaria, cartolarizzazioni (STS), resilienza operativa digitale (DORA), protezione dei dati (GDPR, Digital Omnibus), intelligenza artificiale (AI Act — applicazione cross-settoriale), Listing Act e mercati dei capitali, rating del credito e ESG rating, crypto-assets (MiCA), rendicontazione societaria (ESEF, XBRL), crowdfunding (piattaforme), supervisione dei conglomerati finanziari.

Autorità tipiche: ESMA, Commissione Europea, CONSOB, Banca d'Italia (ambito mercati), ESAs (Joint Committee), FSB, EDPB, EFRAG, ICMA, IOSCO, Eurosif.

---

### APPROFONDIMENTI
Documenti di analisi, studi, statistiche e iniziative non urgenti.

Includere: rapporti periodici (Risk Dashboard EBA, Financial Stability Review BCE), discussion paper e consultation paper senza scadenza imminente, studi accademici e ricerche istituzionali, statistiche di mercato (ANIA TRENDS, bollettini IVASS), newsletter e rassegne periodiche (ESMA Spotlight on Markets), webinar e convegni con output normativo, white paper, memorandum of understanding (MoU), iniziative internazionali non ancora in fase di consultazione formale.

Autorità tipiche: tutte le precedenti quando pubblicano materiale di analisi anziché normativa.

---

## Regole di assegnazione

1. Il campo `ambito_fonte` trasmesso con ogni notizia indica l'ambito regolatorio della fonte — è il riferimento prioritario per la categoria
2. Se la notizia riguarda esclusivamente banche/vigilanza bancaria → **BANKING**
3. Se riguarda esclusivamente assicurazioni/vigilanza assicurativa → **INSURANCE**
4. Se è trasversale a più settori o riguarda normativa di carattere generale → **CROSS FINANCE**
5. Se è un documento di analisi/studio senza impatto normativo immediato → **APPROFONDIMENTI** (indipendentemente dall'ambito_fonte)
6. In caso di dubbio residuo: BANKING > INSURANCE > CROSS FINANCE > APPROFONDIMENTI
7. L'AI Act va in INSURANCE se il contesto è esclusivamente assicurativo, in CROSS FINANCE negli altri casi

---

## Implementazione — `ai/synthesizer.py`

### Prompt di sistema (SYSTEM_PROMPT)

```
Sei un esperto di regolamentazione finanziaria europea e italiana, consulente per SCS Consulting.
Il tuo compito è analizzare notizie normative e produrre sintesi professionali per la newsletter Alert Normativo.
REGOLE:
- Lunghezza sintesi: 4-6 righe (~80-120 parole)
- Lingua: italiano professionale, tono neutro/informativo
- Metti in grassetto (**testo**) i termini tecnici e i nomi delle normative
- Non usare frasi generiche tipo "è importante notare", "si segnala che"
- Non inventare informazioni non presenti nell'originale
- Preserva gli acronimi (EBA, EIOPA, RTS, ITS, CRR, DORA, AI Act, ecc.)

Categorie disponibili:
- BANKING: vigilanza bancaria, requisiti patrimoniali, Basilea, AML/CFT, COREP/FINREP, stress test, BRRD, NPL. Autorità: EBA, Banca d'Italia, BCE, BCBS.
- INSURANCE: Solvency II, IRRD, IDD, IBIP, IVASS, EIOPA, IAIS, prodotti vita/danni.
- CROSS FINANCE: normativa trasversale, MiFID II, ESG/SFDR/CSRD, DORA, MiCA, AI Act (cross-settoriale), Listing Act. Autorità: ESMA, Commissione Europea, FSB.
- APPROFONDIMENTI: analisi, studi, statistiche, discussion paper senza scadenza, newsletter periodiche, webinar.
Regola di categorizzazione: il campo `ambito_fonte` indica l'ambito regolatorio della fonte di provenienza —
usalo come riferimento prioritario per la categorizzazione. Puoi comunque assegnare APPROFONDIMENTI se la
notizia è chiaramente un documento di analisi senza impatto normativo diretto. In caso di dubbio residuo:
BANKING > INSURANCE > CROSS FINANCE > APPROFONDIMENTI. Ogni notizia deve sempre avere una categoria.
```

### Prompt utente (USER_PROMPT_TEMPLATE)

```
Analizza le seguenti notizie normative e per ciascuna restituisci un oggetto JSON con questi campi:
- categoria: "BANKING" | "INSURANCE" | "CROSS FINANCE" | "APPROFONDIMENTI" (obbligatorio)
- fonte: nome breve dell'autorità (es. "EBA", "EIOPA", "BCE")
- titolo: titolo in italiano (max 15 parole)
- descrizione: sintesi 4-6 righe con termini tecnici in grassetto (obbligatorio)
- data_originale: data pubblicazione in formato dd/mm/yyyy
- url: link originale
- includi_in_pptx: "SI" per BANKING, INSURANCE e CROSS FINANCE; "NO" per APPROFONDIMENTI

Il campo `ambito_fonte` di ogni notizia indica l'ambito della fonte (BANKING/INSURANCE/CROSS FINANCE)
— usalo come guida primaria per la categorizzazione.

Notizie:
{news_json}

Rispondi SOLO con un array JSON, senza testo aggiuntivo.
```

### Note implementative

- Modello: `claude-haiku-4-5`
- Max token risposta: 4096
- Batch size: 10 notizie per chiamata API
- Retry: max 2 tentativi in caso di JSON non valido
- Post-processing: i marker `**...**` (grassetto markdown) vengono rimossi dal titolo e dalla descrizione prima della scrittura su Excel — la formattazione grassetto nella PPTX è gestita dalla logica di rendering del generatore
- Risposta attesa: array JSON (non oggetto — il vecchio formato `{"notizie": [...]}` non è più usato)
