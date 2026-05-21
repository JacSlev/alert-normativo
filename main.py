import argparse
import sys
from collections import Counter

import anthropic

import config
from scraper.rss_scraper import scrape_rss
from scraper.html_scraper import (
    # IVASS (7 section pages)
    scrape_ivass_regolamenti, scrape_ivass_provvedimenti, scrape_ivass_comunicazioni,
    scrape_ivass_lettere, scrape_ivass_consultazioni, scrape_ivass_esiti_cons,
    scrape_ivass_media,
    # Insurance Europe
    scrape_insurance_europe_news, scrape_insurance_europe_publications,
    scrape_insurance_europe_events,
    # ANIA (comunicati + pubblicazioni + 5 categorie)
    scrape_ania_comunicati, scrape_ania_pubblicazioni,
    scrape_ania_cat_111377, scrape_ania_cat_53704, scrape_ania_cat_53705,
    scrape_ania_cat_53703, scrape_ania_cat_52472,
    # EIOPA HTML
    scrape_eiopa_events, scrape_eiopa_doc_library,
    scrape_eiopa_speeches, scrape_eiopa_interviews,
    # Banca d'Italia
    scrape_bdi_homepage, scrape_bdi_archivio_norme, scrape_bdi_consultazioni,
    scrape_bdi_approfondimenti, scrape_bdi_ricerche, scrape_bdi_comunicati_bce,
    # BIS/BCBS
    scrape_bis_bcbs,
    # Cross Finance
    scrape_consob, scrape_gazzetta_ufficiale, scrape_eurlex,
    scrape_icma, scrape_iosco,
    scrape_commissione_europea, scrape_commissione_ue_news, scrape_efrag,
    # IAIS
    scrape_iais_news, scrape_iais_consultations, scrape_iais_events,
    # BCE Publications + AMLA
    scrape_bce_publications,
    scrape_amla_news, scrape_amla_publications,
)
from ai.synthesizer import synthesize_all
from output.excel_logger import ensure_excel_exists, count_existing_rows, append_news, get_output_path as excel_path
from output.pptx_generator import generate_pptx, get_output_path as pptx_path

_HTML_SCRAPERS = {
    "scrape_ivass_regolamenti":             scrape_ivass_regolamenti,
    "scrape_ivass_provvedimenti":           scrape_ivass_provvedimenti,
    "scrape_ivass_comunicazioni":           scrape_ivass_comunicazioni,
    "scrape_ivass_lettere":                 scrape_ivass_lettere,
    "scrape_ivass_consultazioni":           scrape_ivass_consultazioni,
    "scrape_ivass_esiti_cons":              scrape_ivass_esiti_cons,
    "scrape_ivass_media":                   scrape_ivass_media,
    "scrape_insurance_europe_news":         scrape_insurance_europe_news,
    "scrape_insurance_europe_publications": scrape_insurance_europe_publications,
    "scrape_insurance_europe_events":       scrape_insurance_europe_events,
    "scrape_ania_comunicati":               scrape_ania_comunicati,
    "scrape_ania_pubblicazioni":            scrape_ania_pubblicazioni,
    "scrape_ania_cat_111377":               scrape_ania_cat_111377,
    "scrape_ania_cat_53704":                scrape_ania_cat_53704,
    "scrape_ania_cat_53705":                scrape_ania_cat_53705,
    "scrape_ania_cat_53703":                scrape_ania_cat_53703,
    "scrape_ania_cat_52472":                scrape_ania_cat_52472,
    "scrape_eiopa_events":                  scrape_eiopa_events,
    "scrape_eiopa_doc_library":             scrape_eiopa_doc_library,
    "scrape_eiopa_speeches":                scrape_eiopa_speeches,
    "scrape_eiopa_interviews":              scrape_eiopa_interviews,
    "scrape_bdi_homepage":                  scrape_bdi_homepage,
    "scrape_bdi_archivio_norme":            scrape_bdi_archivio_norme,
    "scrape_bdi_consultazioni":             scrape_bdi_consultazioni,
    "scrape_bdi_approfondimenti":           scrape_bdi_approfondimenti,
    "scrape_bdi_ricerche":                  scrape_bdi_ricerche,
    "scrape_bdi_comunicati_bce":            scrape_bdi_comunicati_bce,
    "scrape_bis_bcbs":                      scrape_bis_bcbs,
    "scrape_consob":                        scrape_consob,
    "scrape_gazzetta_ufficiale":            scrape_gazzetta_ufficiale,
    "scrape_eurlex":                        scrape_eurlex,
    "scrape_icma":                          scrape_icma,
    "scrape_iosco":                         scrape_iosco,
    "scrape_commissione_europea":           scrape_commissione_europea,
    "scrape_commissione_ue_news":           scrape_commissione_ue_news,
    "scrape_efrag":                         scrape_efrag,
    "scrape_iais_news":                     scrape_iais_news,
    "scrape_iais_consultations":            scrape_iais_consultations,
    "scrape_iais_events":                   scrape_iais_events,
    "scrape_bce_publications":              scrape_bce_publications,
    "scrape_amla_news":                     scrape_amla_news,
    "scrape_amla_publications":             scrape_amla_publications,
}


def scrape():
    print("Fase 1 — Scraping in corso...")

    all_news = []
    for url, name in config.RSS_SOURCES:
        items = scrape_rss(url, source_name=name, days=config.FINESTRA_GIORNI)
        print(f"  [RSS] [{name}] {len(items)} notizie trovate")
        all_news.extend(items)

    for fn_name, name in config.HTML_SOURCES:
        fn = _HTML_SCRAPERS[fn_name]
        items = fn(days=config.FINESTRA_GIORNI)
        print(f"  [HTML] [{name}] {len(items)} notizie trovate")
        all_news.extend(items)

    print(f"Totale notizie scraped: {len(all_news)}")

    if not all_news:
        print("Nessuna notizia trovata. Uscita.")
        sys.exit(0)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    synthesized = synthesize_all(client, all_news)
    print(f"Totale notizie elaborate: {len(synthesized)}")

    out_excel = excel_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)

    created = ensure_excel_exists(config.TEMPLATE_XLSX, out_excel)
    if created:
        print("[INFO] Creato nuovo Excel da template")
    else:
        existing = count_existing_rows(out_excel)
        print(f"[INFO] Uso Excel esistente — {existing} notizie già presenti")

    added = append_news(out_excel, synthesized)
    print(f"[OK] Excel salvato: {out_excel} ({added} nuove notizie aggiunte)")

    counts = dict(Counter(item.get("categoria", "ALTRO") for item in synthesized))
    print("\nRiepilogo per categoria:")
    for cat in ["BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI"]:
        print(f"  {cat}: {counts.get(cat, 0)}")
    if "ALTRO" in counts:
        print(f"  ALTRO: {counts['ALTRO']}")


def publish():
    print("Fase 2 — Generazione PPTX in corso...")
    if not config.EDIZIONE_NUMERO:
        print(
            "[ERRORE] EDIZIONE_NUMERO non è valorizzato nel file .env.\n"
            "         Aggiungere la riga:  EDIZIONE_NUMERO=<numero>  nel .env e riprovare."
        )
        sys.exit(1)
    out_excel = excel_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)
    out_pptx = pptx_path(config.EDIZIONE_NUMERO, config.EDIZIONE_MESE, config.EDIZIONE_ANNO)
    generate_pptx(
        template_path=config.TEMPLATE_PPTX,
        excel_path=out_excel,
        output_path=out_pptx,
        numero=config.EDIZIONE_NUMERO,
        mese=config.EDIZIONE_MESE,
        anno=config.EDIZIONE_ANNO,
        edizione_numero=config.EDIZIONE_NUMERO,
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