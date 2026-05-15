import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_notification(
    gmail_user: str,
    gmail_password: str,
    recipient: str,
    numero: str,
    mese: str,
    anno: str,
    excel_path: str,
    counts: dict[str, int],
) -> None:
    """Send scrape-complete notification via Gmail SMTP. Logs error on failure, never raises."""
    subject = f"Alert Normativo N.{numero} — Excel pronto per review"
    lines = [
        f"Il file Excel per l'edizione N.{numero} {mese} {anno} è pronto per la review.",
        "",
        "Notizie trovate:",
    ]
    for cat, count in counts.items():
        lines.append(f"- {cat}: {count}")
    lines += [
        "",
        f"File salvato in: {excel_path}",
        "",
        "Dopo la review, conferma all'operatore per procedere con la generazione della PPTX.",
    ]
    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        print(f"[OK] Email inviata a {recipient}")
    except Exception as e:
        print(f"[ERRORE] Email non inviata: {e}")
