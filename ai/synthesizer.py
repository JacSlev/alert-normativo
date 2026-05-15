import json
import logging

logger = logging.getLogger(__name__)

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


def synthesize_batch(client, news_items, max_retries=2) -> list[dict]:
    """
    Synthesize a batch of up to 10 news items using Claude API.

    Args:
        client: anthropic.Anthropic client instance
        news_items: list of dicts with keys: title, link, summary, date, source
        max_retries: number of retries on JSON parse failure

    Returns:
        list of synthesized news dicts, or [] on fatal failure
    """
    if not news_items:
        return []

    # Prepare news in JSON format for the prompt
    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    user_prompt = USER_PROMPT_TEMPLATE.format(news_json=news_json)

    # Retry loop
    attempts = 0
    while attempts <= max_retries:
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse as bare JSON array
            results = json.loads(response_text)

            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")

            return results

        except json.JSONDecodeError as e:
            attempts += 1
            if attempts <= max_retries:
                logger.warning(f"JSON decode error on attempt {attempts}: {e}. Retrying...")
            else:
                logger.error(f"Failed to parse JSON after {max_retries + 1} attempts. Returning empty list.")
                return []
        except Exception as e:
            logger.error(f"Unexpected error during synthesis: {e}")
            return []

    return []


def synthesize_all(client, news_items) -> list[dict]:
    """
    Synthesize all news items by chunking into batches of 10.

    Args:
        client: anthropic.Anthropic client instance
        news_items: list of news dicts

    Returns:
        concatenated list of all synthesized results
    """
    results = []
    batch_size = 10

    for i in range(0, len(news_items), batch_size):
        batch_num = (i // batch_size) + 1
        batch = news_items[i:i + batch_size]
        print(f"[AI] Elaborazione batch {batch_num} ({len(batch)} notizie)...")

        batch_results = synthesize_batch(client, batch)
        results.extend(batch_results)

    return results
