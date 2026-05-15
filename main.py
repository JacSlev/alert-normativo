import argparse
import sys
from collections import Counter

import anthropic

import config
from scraper.rss_scraper import scrape_rss
from ai.synthesizer import synthesize_all
from output.excel_logger import create_excel, append_news, get_output_path as excel_path
from output.pptx_generator import generate_pptx, get_output_path as pptx_path
from output.email_sender import send_notification


def scrape():
    print("Fase 1 — Scraping in corso...")

    all_news = []
    for url, name in config.RSS_SOURCES:
        items = scrape_rss(url, source_name=name, days=config.FINESTRA_GIORNI)
        print(f"  [{name}] {len(items)} notizie trovate")
        all_news.extend(items)
    print(f"Totale notizie scraped: {len(all_news)}")

    if not all_news:
        print("Nessuna notizia trovata. Uscita.")
        sys.exit(0)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    synthesized = synthesize_all(client, all_news)
    print(f"Totale notizie elaborate: {len(synthesized)}")

    out_excel = excel_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)
    create_excel(config.TEMPLATE_XLSX, out_excel)
    added = append_news(out_excel, synthesized)
    print(f"[OK] Excel salvato: {out_excel} ({added} notizie aggiunte)")

    counts = dict(Counter(item.get("categoria", "ALTRO") for item in synthesized))

    if config.GMAIL_USER and config.GMAIL_APP_PASSWORD and config.EMAIL_NOTIFICA_DESTINATARIO:
        send_notification(
            gmail_user=config.GMAIL_USER,
            gmail_password=config.GMAIL_APP_PASSWORD,
            recipient=config.EMAIL_NOTIFICA_DESTINATARIO,
            numero=config.EDIZIONE_NUMERO,
            mese=config.EDIZIONE_MESE,
            anno=config.EDIZIONE_ANNO,
            excel_path=out_excel,
            counts=counts,
        )
    else:
        print("[WARN] Credenziali email non configurate — notifica saltata")


def publish():
    print("Fase 2 — Generazione PPTX in corso...")
    out_excel = excel_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)
    out_pptx = pptx_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)
    generate_pptx(
        template_path=config.TEMPLATE_PPTX,
        excel_path=out_excel,
        output_path=out_pptx,
        numero=config.EDIZIONE_NUMERO,
        mese=config.EDIZIONE_MESE,
        anno=config.EDIZIONE_ANNO,
    )


def main():
    parser = argparse.ArgumentParser(description="Alert Normativo — SCS Consulting")
    parser.add_argument("--scrape", action="store_true", help="Fase 1: scraping e generazione Excel")
    parser.add_argument("--publish", action="store_true", help="Fase 2: generazione PPTX")
    args = parser.parse_args()

    if args.scrape:
        scrape()
    elif args.publish:
        publish()
    else:
        print("Specifica --scrape o --publish")
        sys.exit(1)


if __name__ == "__main__":
    main()