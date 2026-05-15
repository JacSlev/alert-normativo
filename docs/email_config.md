# Configurazione email — Notifica operativa

## Scopo

Lo script invia una sola email automatica: la **notifica al responsabile** al termine della fase `--scrape`, per segnalare che il file Excel è pronto per la review.

L'invio della newsletter è fuori scope — viene fatto manualmente dal responsabile dopo aver generato la PPTX.

---

## Provider — Gmail (MVP)

**Libreria:** `smtplib` (standard Python, nessuna dipendenza aggiuntiva)

**Setup:**
1. Attivare autenticazione a 2 fattori sull'account Google
2. Generare una App Password: Account Google → Sicurezza → App Password
3. Usare quella password nel `.env` (non la password normale dell'account)

**Variabili:**
```
GMAIL_USER=tua@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_NOTIFICA_DESTINATARIO=responsabile@email.it
```

**Configurazione SMTP:**
- Host: `smtp.gmail.com`
- Porta: `587`
- TLS: STARTTLS

---

## Struttura email di notifica

- **Mittente:** valore di `GMAIL_USER`
- **Destinatario:** valore di `EMAIL_NOTIFICA_DESTINATARIO`
- **Oggetto:** `Alert Normativo N.{numero} — Excel pronto per review`
- **Corpo:** testo semplice con numero di notizie trovate per ambito e percorso del file

Esempio corpo:
```
Il file Excel per l'edizione N.2 Maggio 2026 è pronto per la review.

Notizie trovate:
- Banking: 8
- Insurance: 5
- Cross Finance: 4
- Cross Finance - Sostenibilità: 2

File salvato in: output/monitoraggio_N2_Maggio2026.xlsx

Dopo la review, conferma all'operatore per procedere con la generazione della PPTX.
```

---

## Evoluzione futura

Quando l'infrastruttura aziendale lo consentirà, sostituire Gmail con **Microsoft 365** tramite libreria `O365` e OAuth2. Il cambio richiede solo l'aggiornamento delle variabili d'ambiente e del provider in `email_sender.py` — il resto del codice non cambia.

```
# Futuro
EMAIL_PROVIDER=microsoft365
MS365_CLIENT_ID=
MS365_CLIENT_SECRET=
MS365_TENANT_ID=
```

---

## Gestione errori

Se l'invio della notifica fallisce: loggare l'errore a console e continuare. L'Excel è già stato generato correttamente — l'operatore può notificare il responsabile manualmente.
