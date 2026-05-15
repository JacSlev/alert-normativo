import json
import logging

logger = logging.getLogger(__name__)

MAX_TOKENS = 4096

SYSTEM_PROMPT = """Sei un esperto di regolamentazione finanziaria europea e italiana, consulente per SCS Consulting.
Il tuo compito è analizzare notizie normative e produrre sintesi professionali per la newsletter Alert Normativo.
REGOLE:
- Lunghezza sintesi: 4-6 righe (~80-120 parole)
- Lingua: italiano professionale, tono neutro/informativo
- Metti in grassetto (**testo**) i termini tecnici e i nomi delle normative
- Non usare frasi generiche tipo "è importante notare", "si segnala che"
- Non inventare informazioni non presenti nell'originale
- Preserva gli acronimi (EBA, EIOPA, RTS, ITS, CRR, DORA, AI Act, ecc.)
"""

USER_PROMPT_TEMPLATE = """Analizza le seguenti notizie normative e per ciascuna restituisci un JSON con questi campi:
- pertinente: true/false (includi solo se rilevante per banche/assicurazioni/finanza europea)
- categoria: "BANKING" | "INSURANCE" | "CROSS FINANCE" | "APPROFONDIMENTI"
- fonte: nome breve dell'autorità (es. "EBA", "EIOPA", "BCE")
- titolo: titolo in italiano (max 15 parole)
- descrizione: sintesi 4-6 righe con termini tecnici in grassetto
- data_originale: data pubblicazione in formato dd/mm/yyyy
- url: link originale
- includi_in_pptx: "SI" se pertinente=true, "NO" altrimenti

Notizie:
{news_json}

Rispondi SOLO con un array JSON, senza testo aggiuntivo.
"""


def synthesize_batch(client, news_items: list[dict], max_retries: int = 2) -> list[dict]:
    """Send up to 10 news items to Claude API and return structured results."""
    if not news_items:
        return []

    if len(news_items) > 10:
        logger.warning("synthesize_batch received %d items; truncating to 10.", len(news_items))
        news_items = news_items[:10]

    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    user_prompt = USER_PROMPT_TEMPLATE.format(news_json=news_json)

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            response_text = response.content[0].text.strip()
            results = json.loads(response_text)
            if not isinstance(results, list):
                raise ValueError(f"Expected JSON array, got {type(results).__name__}")
            return results
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries:
                logger.warning("Parse error on attempt %d/%d: %s. Retrying...", attempt + 1, max_retries + 1, e)
            else:
                logger.error("Failed to parse response after %d attempts: %s", max_retries + 1, e)
                return []
        except Exception as e:
            logger.error("Unexpected error during synthesis: %s", e)
            return []

    return []


def synthesize_all(client, news_items: list[dict]) -> list[dict]:
    """Process all news items in batches of 10."""
    results = []
    batch_size = 10

    for i in range(0, len(news_items), batch_size):
        batch_num = (i // batch_size) + 1
        batch = news_items[i:i + batch_size]
        print(f"[AI] Elaborazione batch {batch_num} ({len(batch)} notizie)...")
        results.extend(synthesize_batch(client, batch))

    return results
