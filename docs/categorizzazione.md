# Logica di categorizzazione

## 4 sezioni fisse

### BANKING
Vigilanza bancaria e normativa prudenziale per enti creditizi.

Includere notizie su: requisiti patrimoniali (CRR/CRD IV-VI), framework di Basilea (Basilea III/IV, FRTB), modelli interni di rischio (IRB, modelli di rischio di mercato/operativo/credito), antiriciclaggio e contrasto al finanziamento del terrorismo (AML/CFT), shadow banking e large exposures, segnalazioni di vigilanza (COREP, FINREP, AnaCredit), stress test bancari, SREP, risoluzione bancaria (BRRD, SRM), EMIR e derivati OTC, fintech e open banking, crowdfunding (lato bancario), Early Warning Systems, NPL e qualità degli attivi.

Autorità tipiche: EBA, Banca d'Italia, BCE, Comitato di Basilea, FSB, CONSOB (ambito bancario).

---

### INSURANCE
Vigilanza assicurativa e normativa prudenziale per imprese di assicurazione.

Includere notizie su: Solvency II (Pilastro I, II, III — SCR, MCR, ORSA, reporting QRT), revisione Solvency II e Omnibus II, IRRD (Insurance Recovery and Resolution Directive), IDD (Insurance Distribution Directive), sistemi di garanzia assicurativa (IGS), prodotti assicurativi d'investimento (IBIP, unit-linked, polizze vita), KID/PRIIPs in ambito assicurativo, riassicurazione e trasferimento del rischio, catastrofi naturali e NatCat SCR, piccole imprese assicurative (SNCU/SNCG), IVASS (circolari, regolamenti, statistiche), value for money dei prodotti assicurativi, AI Act applicato al settore assicurativo.

Autorità tipiche: EIOPA, IVASS, IAIS, Insurance Europe, ANIA.

---

### CROSS FINANCE
Normativa trasversale a più settori finanziari o di carattere generale.

Includere notizie su: mercati finanziari e infrastrutture (MiFID II/MiFIR, MAR, Consolidated Tape, internalizzatori sistematici), gestione collettiva del risparmio (AIFMD, UCITS, fondi monetari MMF, EuVECA), finanza sostenibile ed ESG (CSRD, ESRS, Tassonomia UE, SFDR, greenwashing, TCFD), Testo Unico della Finanza (TUF) e riforma societaria, cartolarizzazioni (STS), resilienza operativa digitale (DORA), protezione dei dati (GDPR, Digital Omnibus), intelligenza artificiale (AI Act — applicazione cross-settoriale), Listing Act e mercati dei capitali, rating del credito e ESG rating, crypto-assets (MiCA), rendicontazione societaria (ESEF, XBRL), crowdfunding (piattaforme), supervisione dei conglomerati finanziari.

Autorità tipiche: ESMA, Commissione Europea, CONSOB, Banca d'Italia (ambito mercati), ESAs (Joint Committee), FSB.

---

### APPROFONDIMENTI
Documenti di analisi, studi, statistiche e iniziative non urgenti.

Includere: rapporti periodici (Risk Dashboard EBA, Financial Stability Review BCE), discussion paper e consultation paper senza scadenza imminente, studi accademici e ricerche istituzionali, statistiche di mercato (ANIA TRENDS, bollettini IVASS), newsletter e rassegne periodiche (ESMA Spotlight on Markets), webinar e convegni con output normativo, white paper, memorandum of understanding (MoU), iniziative internazionali non ancora in fase di consultazione formale.

Autorità tipiche: tutte le precedenti quando pubblicano materiale di analisi anziché normativa.

---

## Regole di assegnazione

1. Se la notizia riguarda esclusivamente banche/vigilanza bancaria → **BANKING**
2. Se riguarda esclusivamente assicurazioni/vigilanza assicurativa → **INSURANCE**
3. Se è trasversale a più settori o riguarda normativa di carattere generale → **CROSS FINANCE**
4. Se è un documento di analisi/studio senza impatto normativo immediato → **APPROFONDIMENTI**
5. In caso di dubbio sulla categoria: BANKING > INSURANCE > CROSS FINANCE > APPROFONDIMENTI
6. L'AI Act va in INSURANCE se il contesto è esclusivamente assicurativo, in CROSS FINANCE negli altri casi

---

## Prompt di sistema per Claude API

```
Sei un esperto di regolamentazione finanziaria europea e italiana che lavora per SCS Consulting. Analizzi notizie normative grezze e produci sintesi per la newsletter "Alert Normativo".

Regole di sintesi:
- Lunghezza descrizione: 4-6 righe (circa 80-120 parole)
- Lingua: italiano professionale, tono neutro e informativo
- Evidenzia in grassetto i termini tecnici chiave e i nomi di regolamenti/direttive
- Non usare frasi generiche tipo "è importante sottolineare che" o "si segnala che"
- Non inventare informazioni non presenti nel testo originale
- Mantieni gli acronimi tecnici (EBA, EIOPA, RTS, ITS, CRR, DORA, AI Act ecc.) senza tradurli
```

## Prompt utente per batch di notizie

```
Analizza le notizie normative grezze qui sotto.

Per ogni notizia restituisci:
1. pertinente: true/false — se rilevante per la regolamentazione finanziaria europea/italiana
2. categoria: BANKING, INSURANCE, CROSS FINANCE, o APPROFONDIMENTI
3. fonte: nome breve dell'autorità (es. "EBA", "IVASS", "Banca d'Italia")
4. titolo: titolo sintetico della notizia in italiano (max 15 parole)
5. descrizione: sintesi in italiano di 4-6 righe con termini chiave in grassetto
6. data_originale: data della notizia in formato gg/mm/aaaa
7. url: link alla fonte originale
8. includi_in_pptx: SI se pertinente=true, NO se pertinente=false

Rispondi SOLO con JSON valido, nessun testo aggiuntivo:
{
  "notizie": [
    {
      "pertinente": true,
      "categoria": "BANKING",
      "fonte": "EBA",
      "titolo": "EBA pubblica linee guida sui requisiti patrimoniali",
      "descrizione": "...",
      "data_originale": "15/05/2026",
      "url": "https://...",
      "includi_in_pptx": "SI"
    }
  ]
}

NOTIZIE GREZZE:
{notizie_grezze}
```

Max 10 notizie per chiamata API. In caso di JSON non valido: ritentare max 2 volte, poi scartare il batch con log di errore.
