import json
import pytest
from unittest.mock import MagicMock
from ai.synthesizer import synthesize_batch, synthesize_all, _strip_markdown_bold

SAMPLE_NEWS = [
    {"title": "EBA publishes FRTB guidelines", "link": "https://eba.eu/1",
     "summary": "The EBA published...", "date": "14/05/2026", "source": "EBA"},
    {"title": "EIOPA updates Solvency II framework", "link": "https://eiopa.eu/1",
     "summary": "EIOPA updated...", "date": "13/05/2026", "source": "EIOPA"},
]

VALID_RESPONSE = json.dumps([
    {"categoria": "BANKING", "fonte": "EBA",
     "titolo": "EBA pubblica linee guida FRTB", "descrizione": "L'**EBA** ha pubblicato...",
     "data_originale": "14/05/2026", "url": "https://eba.eu/1", "includi_in_pptx": "SI"},
    {"categoria": "INSURANCE", "fonte": "EIOPA",
     "titolo": "EIOPA aggiorna Solvency II", "descrizione": "**EIOPA** ha aggiornato...",
     "data_originale": "13/05/2026", "url": "https://eiopa.eu/1", "includi_in_pptx": "SI"},
])


def make_mock_client(response_text, stop_reason="end_turn"):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    mock_msg.stop_reason = stop_reason
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_strip_markdown_bold():
    assert _strip_markdown_bold("L'**EBA** ha pubblicato il **CRR**.") == "L'EBA ha pubblicato il CRR."
    assert _strip_markdown_bold("nessun grassetto") == "nessun grassetto"
    assert _strip_markdown_bold("") == ""


def test_synthesize_batch_returns_parsed_list():
    client = make_mock_client(VALID_RESPONSE)
    results = synthesize_batch(client, SAMPLE_NEWS)
    assert len(results) == 2
    assert results[0]["categoria"] == "BANKING"
    assert results[1]["categoria"] == "INSURANCE"


def test_synthesize_batch_strips_bold_from_titolo_and_descrizione():
    client = make_mock_client(VALID_RESPONSE)
    results = synthesize_batch(client, SAMPLE_NEWS)
    # VALID_RESPONSE contains ** in descrizione — must be stripped
    assert "**" not in results[0]["descrizione"]
    assert "**" not in results[1]["descrizione"]
    # titoli in VALID_RESPONSE have no **, but verify field is present and clean
    assert "**" not in results[0]["titolo"]
    assert "**" not in results[1]["titolo"]


def test_synthesize_batch_retries_on_invalid_json():
    client = make_mock_client("not valid json")
    results = synthesize_batch(client, SAMPLE_NEWS, max_retries=2)
    assert results == []
    assert client.messages.create.call_count == 3  # 1 original + 2 retries


def test_synthesize_all_chunks_into_batches_of_10():
    news_21 = [{"title": f"News {i}", "link": f"https://ex.com/{i}",
                "summary": "s", "date": "14/05/2026", "source": "EBA"} for i in range(21)]
    client = make_mock_client("[]")
    synthesize_all(client, news_21)
    assert client.messages.create.call_count == 3  # ceil(21/10) = 3 batches


def test_synthesize_batch_uses_correct_model():
    client = make_mock_client(VALID_RESPONSE)
    synthesize_batch(client, SAMPLE_NEWS)
    call_kwargs = client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-haiku-4-5"


def test_synthesize_batch_returns_empty_on_non_list_json():
    """API returns valid JSON but not an array — should retry and return []."""
    client = make_mock_client('{"items": []}')
    results = synthesize_batch(client, SAMPLE_NEWS, max_retries=2)
    assert results == []
    assert client.messages.create.call_count == 3


def test_synthesize_batch_empty_input_returns_empty():
    """Empty input returns empty list without making API call."""
    client = make_mock_client("[]")
    results = synthesize_batch(client, [])
    assert results == []
    assert client.messages.create.call_count == 0


def test_synthesize_all_empty_input():
    """synthesize_all with empty input returns empty list, no API calls."""
    client = make_mock_client("[]")
    results = synthesize_all(client, [])
    assert results == []
    assert client.messages.create.call_count == 0


def test_synthesize_batch_uses_max_tokens():
    client = make_mock_client(VALID_RESPONSE)
    synthesize_batch(client, SAMPLE_NEWS)
    call_kwargs = client.messages.create.call_args[1]
    assert call_kwargs["max_tokens"] == 8192


def test_synthesize_batch_retries_on_max_tokens_truncation():
    """stop_reason=max_tokens → risposta troncata, va trattata come errore e ritentata."""
    client = make_mock_client(VALID_RESPONSE, stop_reason="max_tokens")
    results = synthesize_batch(client, SAMPLE_NEWS, max_retries=2)
    assert results == []
    assert client.messages.create.call_count == 3  # 1 original + 2 retries


def test_synthesize_batch_accepts_partial_results_with_warning(caplog):
    """Risposta con meno sintesi delle notizie inviate → warning, parziali accettati, nessun retry."""
    partial_response = json.dumps([json.loads(VALID_RESPONSE)[0]])  # 1 sintesi per 2 notizie
    client = make_mock_client(partial_response)
    with caplog.at_level("WARNING", logger="ai.synthesizer"):
        results = synthesize_batch(client, SAMPLE_NEWS)
    assert len(results) == 1
    assert client.messages.create.call_count == 1  # no retry
    assert any("attese 2 sintesi, ricevute 1" in r.message for r in caplog.records)


def test_synthesize_all_warns_on_lost_news(capsys):
    """Se alla fine mancano sintesi rispetto alle notizie in input, stampa un warning riepilogativo."""
    client = make_mock_client("[]")
    results = synthesize_all(client, SAMPLE_NEWS)
    assert results == []
    out = capsys.readouterr().out
    assert "[WARNING] 2 notizie su 2" in out
