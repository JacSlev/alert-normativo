import pytest
import os
import shutil
from openpyxl import load_workbook
from output.excel_logger import create_excel, append_news, get_output_path

SAMPLE_NEWS = [
    {"pertinente": True, "categoria": "BANKING", "fonte": "EBA",
     "titolo": "EBA pubblica linee guida FRTB", "descrizione": "L'**EBA** ha pubblicato linee guida.",
     "data_originale": "14/05/2026", "url": "https://eba.eu/1", "includi_in_pptx": "SI"},
    {"pertinente": False, "categoria": "APPROFONDIMENTI", "fonte": "EIOPA",
     "titolo": "Studio EIOPA", "descrizione": "Studio pubblicato.",
     "data_originale": "13/05/2026", "url": "https://eiopa.eu/1", "includi_in_pptx": "NO"},
]

TEMPLATE_PATH = "assets/Template_settimanale.xlsx"


@pytest.fixture
def output_path(tmp_path):
    if not os.path.exists(TEMPLATE_PATH):
        pytest.skip("Template XLSX non trovato in assets/")
    dest = str(tmp_path / "test_output.xlsx")
    shutil.copy(TEMPLATE_PATH, dest)
    return dest


def test_get_output_path_format():
    path = get_output_path(numero="2", mese="Maggio", anno="2026")
    assert path == "output/monitoraggio_N2_Maggio2026.xlsx"


def test_create_excel_copies_template(tmp_path):
    if not os.path.exists(TEMPLATE_PATH):
        pytest.skip("Template XLSX non trovato")
    dest = str(tmp_path / "out.xlsx")
    create_excel(TEMPLATE_PATH, dest)
    assert os.path.exists(dest)


def test_append_news_writes_rows(output_path):
    added = append_news(output_path, SAMPLE_NEWS)
    assert added == 2
    wb = load_workbook(output_path)
    ws = wb["Monitoraggio finance"]
    urls = [ws.cell(row=r, column=9).value for r in range(3, ws.max_row + 1)
            if ws.cell(row=r, column=1).value is not None]
    assert "https://eba.eu/1" in urls
    assert "https://eiopa.eu/1" in urls


def test_append_news_deduplicates_by_url(output_path):
    append_news(output_path, SAMPLE_NEWS)
    added_second = append_news(output_path, SAMPLE_NEWS)
    assert added_second == 0
    wb = load_workbook(output_path)
    ws = wb["Monitoraggio finance"]
    urls = [ws.cell(row=r, column=9).value for r in range(3, ws.max_row + 1)
            if ws.cell(row=r, column=1).value is not None]
    assert urls.count("https://eba.eu/1") == 1


def test_append_news_returns_count(output_path):
    added = append_news(output_path, SAMPLE_NEWS)
    assert added == 2
