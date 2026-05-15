import os
from openpyxl import load_workbook
from pptx import Presentation
from pptx.oxml.ns import qn

CATEGORY_ORDER = ["BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI"]
DATA_START_ROW = 3  # rows 1=title, 2=header in template


def read_approved_news(excel_path: str) -> dict[str, list[dict]]:
    """Read reviewed Excel and return news grouped by category where Includi=SI."""
    wb = load_workbook(excel_path)
    ws = wb["Monitoraggio finance"]
    grouped: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_ORDER}
    for row in ws.iter_rows(min_row=DATA_START_ROW, values_only=True):
        if row[0] is None:
            continue
        includi = str(row[7]).strip().upper() if row[7] else "NO"
        if includi != "SI":
            continue
        categoria = str(row[1]).strip() if row[1] else ""
        if categoria not in grouped:
            grouped[categoria] = []
        grouped[categoria].append({
            "descrizione": row[6] or "",
            "data": row[3] or "",
            "url": row[8] or "",
        })
    return grouped


def _section_map(slide) -> dict[str, tuple]:
    """Return {category_label: (group_shape, table_shape)} sorted by vertical position."""
    items = []
    for shape in slide.shapes:
        if shape.shape_type == 6:   # GROUP
            label = ""
            for s in shape.shapes:
                if s.has_text_frame:
                    label = s.text_frame.text.strip()
            items.append((shape.top, "group", shape, label))
        elif shape.shape_type == 19:  # TABLE
            items.append((shape.top, "table", shape, ""))

    items.sort(key=lambda x: x[0])

    result = {}
    i = 0
    while i < len(items):
        _, kind, shape, label = items[i]
        if kind == "group" and label in CATEGORY_ORDER:
            group = shape
            table = None
            if i + 1 < len(items) and items[i + 1][1] == "table":
                table = items[i + 1][2]
                i += 2
            else:
                i += 1
            result[label] = (group, table)
        else:
            i += 1
    return result


def _set_cell_text(cell, text: str) -> None:
    """Replace all text in a table cell while preserving paragraph formatting."""
    tf = cell.text_frame
    for para in tf.paragraphs:
        for run in para.runs:
            run.text = ""
    if tf.paragraphs and tf.paragraphs[0].runs:
        tf.paragraphs[0].runs[0].text = text
    elif tf.paragraphs:
        run = tf.paragraphs[0].add_run()
        run.text = text


def _clear_cell(cell) -> None:
    """Clear all text from a table cell."""
    tf = cell.text_frame
    for para in tf.paragraphs:
        for run in para.runs:
            run.text = ""


def _hide_shape(shape) -> None:
    """Hide a shape by setting hidden=1 on its cNvPr element."""
    elem = shape.element
    for tag in ("p:nvSpPr", "p:nvGrpSpPr", "p:nvGraphicFramePr"):
        nv = elem.find(qn(tag))
        if nv is not None:
            cnv = nv.find(qn("p:cNvPr"))
            if cnv is not None:
                cnv.set("hidden", "1")
                return


def _set_cell_link(cell, url: str) -> None:
    """Set cell text to 'Link' with a clickable hyperlink to url."""
    tf = cell.text_frame
    for para in tf.paragraphs:
        for run in para.runs:
            run.text = ""
    if tf.paragraphs and tf.paragraphs[0].runs:
        run = tf.paragraphs[0].runs[0]
    elif tf.paragraphs:
        run = tf.paragraphs[0].add_run()
    else:
        return
    run.text = "Link"
    run.hyperlink.address = url


def _fill_section(table_shape, news_items: list[dict]) -> None:
    """Fill table rows with news items; clear unused rows."""
    tbl = table_shape.table
    for row_idx, row in enumerate(tbl.rows):
        if row_idx < len(news_items):
            item = news_items[row_idx]
            _set_cell_text(row.cells[0], item["descrizione"])
            _set_cell_text(row.cells[1], item["data"])
            _set_cell_link(row.cells[2], item["url"])
        else:
            _clear_cell(row.cells[0])
            _clear_cell(row.cells[1])
            _clear_cell(row.cells[2])


def _update_edition(slide, numero: str, mese: str, anno: str) -> None:
    """Update the edition number and month/year text box."""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text
        if "N. " in text and "\n" in text:
            runs = [run for para in shape.text_frame.paragraphs for run in para.runs]
            if len(runs) >= 2:
                runs[0].text = f"N. {numero}"
                runs[1].text = f"{mese} {anno}"
            break


def get_output_path(numero: str, mese: str, anno: str) -> str:
    return f"output/alert_normativo_N{numero}_{mese}{anno}.pptx"


def generate_pptx(
    template_path: str,
    excel_path: str,
    output_path: str,
    numero: str,
    mese: str,
    anno: str,
) -> None:
    """Generate PPTX from reviewed Excel data."""
    grouped = read_approved_news(excel_path)
    prs = Presentation(template_path)
    slide = prs.slides[0]

    sections = _section_map(slide)
    _update_edition(slide, numero, mese, anno)

    for category in CATEGORY_ORDER:
        news_items = grouped.get(category, [])
        group, table = sections.get(category, (None, None))

        if not news_items:
            if group:
                _hide_shape(group)
            if table:
                _hide_shape(table)
        else:
            if table:
                _fill_section(table, news_items)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    prs.save(output_path)
    print(f"[OK] PPTX salvata: {output_path}")
