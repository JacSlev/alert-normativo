import argparse
import sys
from config import *

def scrape():
    print("Fase 1 — Scraping in corso...")
    # TODO: scraper
    # TODO: synthesizer
    # TODO: excel_logger
    # TODO: email_sender

def publish():
    print("Fase 2 — Generazione PPTX in corso...")
    # TODO: leggi Excel revisionato
    # TODO: pptx_generator

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