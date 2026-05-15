import email as email_lib
import email.header
from unittest.mock import patch, MagicMock
from output.email_sender import send_notification


def _decode_mime(raw_msg: str) -> tuple[str, str]:
    """Parse raw MIME message string, return (subject, body)."""
    msg = email_lib.message_from_string(raw_msg)
    subject_parts = email.header.decode_header(msg["Subject"])
    subject = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in subject_parts
    )
    if msg.is_multipart():
        body = msg.get_payload(0).get_payload(decode=True).decode("utf-8")
    else:
        body = msg.get_payload(decode=True).decode("utf-8")
    return subject, body

COUNTS = {"BANKING": 5, "INSURANCE": 3, "CROSS FINANCE": 4, "APPROFONDIMENTI": 2}


def test_send_notification_uses_starttls_and_login():
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        send_notification(
            gmail_user="from@gmail.com",
            gmail_password="pass",
            recipient="to@example.com",
            numero="2",
            mese="Maggio",
            anno="2026",
            excel_path="output/monitoraggio_N2_Maggio2026.xlsx",
            counts=COUNTS,
        )
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("from@gmail.com", "pass")
        mock_smtp.sendmail.assert_called_once()


def test_send_notification_subject_contains_edition():
    sent = []
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_smtp.sendmail.side_effect = lambda f, t, msg: sent.append(msg)
        send_notification(
            gmail_user="from@gmail.com",
            gmail_password="pass",
            recipient="to@example.com",
            numero="2",
            mese="Maggio",
            anno="2026",
            excel_path="output/test.xlsx",
            counts=COUNTS,
        )
    assert len(sent) == 1
    subject, body = _decode_mime(sent[0])
    assert "N.2" in subject
    assert "Maggio" in subject or "Maggio" in body


def test_send_notification_body_contains_counts():
    sent = []
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_smtp.sendmail.side_effect = lambda f, t, msg: sent.append(msg)
        send_notification(
            gmail_user="from@gmail.com",
            gmail_password="pass",
            recipient="to@example.com",
            numero="2",
            mese="Maggio",
            anno="2026",
            excel_path="output/test.xlsx",
            counts=COUNTS,
        )
    _, body = _decode_mime(sent[0])
    assert "BANKING" in body
    assert "5" in body
    assert "INSURANCE" in body
    assert "3" in body


def test_send_notification_handles_smtp_error_silently():
    """SMTP failure must not raise — just log and return."""
    with patch("smtplib.SMTP", side_effect=Exception("Connection refused")):
        send_notification(
            gmail_user="from@gmail.com",
            gmail_password="pass",
            recipient="to@example.com",
            numero="2",
            mese="Maggio",
            anno="2026",
            excel_path="output/test.xlsx",
            counts=COUNTS,
        )
