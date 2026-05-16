"""
pptx_generator.py — Dynamic layout PPTX generator for Alert Normativo

Layout constants derived from template inspection:
  Template vecchio (assets/Template_settimanale.pptx) → coordinate colonne
  Template clean   (assets/_CLEAN.pptx)                → area contenuto

Slide A4 portrait: 7,559,675 × 10,691,813 EMU (20.999 × 29.699 cm)

Content area:
  TOP_CONTENT_Y    = 1,762,545 EMU (4.895 cm)  — header bottom + margine
  BOTTOM_CONTENT_Y = 9,873,419 EMU (27.426 cm) — footer top

Colonne (costanti su tutte le tabelle del vecchio template):
  Descrizione: left=254,373  width=5,325,951
  Data:        left=5,580,324 width=866,037
  Link:        left=6,446,361 width=866,037

Section header:
  Altezza = 303,227 (0.842 cm)
  Icona: left=34,935 size=252,000 (0.70 cm)
  Label: left=336,935 font=14pt bold nero
"""

import copy
import math
import os
import textwrap
from datetime import date
from openpyxl import load_workbook
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Struttura slide ───────────────────────────────────────────────────────────
SLIDE_W = 7559675
SLIDE_H = 10691813

TOP_CONTENT_Y    = 2065553    # fondo "Principali aggiornamenti normativi" (1,965,553) + 100k margine
BOTTOM_CONTENT_Y = 9873419    # tetto footer

# ── Colonne ───────────────────────────────────────────────────────────────────
DESC_LEFT  = 254373;  DESC_WIDTH  = 5325951
DATE_LEFT  = 5580324; DATE_WIDTH  = 866037
LINK_LEFT  = 6446361; LINK_WIDTH  = 866037

# ── Altezze ───────────────────────────────────────────────────────────────────
SECTION_HEADER_H = 303227    # 0.842 cm — intestazione sezione
SECTION_GAP      = 180000    # 0.500 cm — spazio tra sezioni diverse
ITEM_V_MARGIN    = 80000     # 0.222 cm — margine tra notizie consecutive (~2.25mm)

# ── Calcolo altezza dinamica ──────────────────────────────────────────────────
# Avenir Next LT Pro 10pt in DESC_WIDTH (419pt):
#   avg char width ≈ 5.3pt → ~79 chars per line
#   line height = 14pt (1.4× spacing) = 177,800 EMU
FONT_NAME        = "Avenir Next LT Pro"
CHARS_PER_LINE   = 79
LINE_HEIGHT_EMU  = int(Pt(14))    # 177,800 — interlinea generosa
TEXT_V_PAD       = 36000          # padding interno verticale del textbox


def _item_height(text: str) -> int:
    """Stima altezza EMU per il textbox descrizione basandosi sul wrapping del testo."""
    if not text:
        return LINE_HEIGHT_EMU + TEXT_V_PAD
    lines = textwrap.wrap(str(text), width=CHARS_PER_LINE)
    n_lines = max(1, len(lines))
    return n_lines * LINE_HEIGHT_EMU + TEXT_V_PAD


# ── Icona sezione ─────────────────────────────────────────────────────────────
ICON_LEFT = 34935
ICON_PAD  = 25614                               # (SECTION_HEADER_H - 252000) / 2
ICON_SIZE = SECTION_HEADER_H - 2 * ICON_PAD    # ≈ 252,000 EMU (0.70cm)

LABEL_LEFT  = ICON_LEFT + ICON_SIZE + 60000     # ≈ 346,935 EMU
LABEL_WIDTH = SLIDE_W - LABEL_LEFT - ICON_LEFT

CATEGORY_ORDER = ["BANKING", "INSURANCE", "CROSS FINANCE", "APPROFONDIMENTI"]
DATA_START_ROW  = 3


# ── Lettura Excel ─────────────────────────────────────────────────────────────

def read_approved_news(excel_path: str) -> dict:
    """Leggi l'Excel revisionato e raggruppa le notizie con includi_in_pptx=SI."""
    wb = load_workbook(excel_path)
    ws = wb["Monitoraggio finance"]
    grouped: dict = {cat: [] for cat in CATEGORY_ORDER}
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


# ── Gestione slide ────────────────────────────────────────────────────────────

def _update_edition(slide, numero: str, mese: str, anno: str) -> None:
    """Aggiorna il riquadro edizione (N. X / Mese Anno) nella slide."""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if "N. " in shape.text_frame.text and "\n" in shape.text_frame.text:
            runs = [r for p in shape.text_frame.paragraphs for r in p.runs]
            if len(runs) >= 2:
                runs[0].text = f"N. {numero}"
                runs[1].text = f"{mese} {anno}"
            break


def _save_template_state(slide):
    """Salva copia del template (pre-contenuto) per la paginazione."""
    children = [copy.deepcopy(el) for el in list(slide.shapes._spTree)[2:]]
    rels = dict(slide.part.rels.items())
    return children, rels


def _add_content_slide(prs, template_children: list, template_rels: dict):
    """Aggiunge una nuova slide come copia del template base."""
    blank_layout = prs.slide_layouts[6]
    new_slide = prs.slides.add_slide(blank_layout)

    sp_tree = new_slide.shapes._spTree
    for el in list(sp_tree)[2:]:
        sp_tree.remove(el)
    for el in template_children:
        sp_tree.append(copy.deepcopy(el))
    for rId, rel in template_rels.items():
        new_slide.part.rels._rels[rId] = rel

    return new_slide


# ── Disegno elementi ──────────────────────────────────────────────────────────

def _draw_section_header(slide, section: str, icon_path: str, y: int) -> None:
    """Disegna intestazione sezione: icona PNG + nome sezione nero 14pt bold.
    Nessuna banda colorata di sfondo."""

    # Icona PNG (se il file esiste)
    if os.path.exists(icon_path):
        slide.shapes.add_picture(
            icon_path,
            ICON_LEFT + ICON_PAD,
            y + ICON_PAD,
            ICON_SIZE,
            ICON_SIZE,
        )

    # Label sezione — nero, 14pt, bold, Avenir Next LT Pro
    tb = slide.shapes.add_textbox(LABEL_LEFT, y, LABEL_WIDTH, SECTION_HEADER_H)
    tf = tb.text_frame
    tf.word_wrap = False
    tf._txBody.bodyPr.set("anchor", "ctr")
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.LEFT
    run = para.add_run()
    run.text = section
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)


def _draw_news_item(slide, item: dict, y: int, item_h: int) -> None:
    """Disegna descrizione, data e link per una singola notizia.
    item_h è l'altezza precalcolata per questo item."""

    BLACK = RGBColor(0x00, 0x00, 0x00)
    NAVY  = RGBColor(0x00, 0x20, 0x60)

    # — Descrizione —
    tb_desc = slide.shapes.add_textbox(DESC_LEFT, y, DESC_WIDTH, item_h)
    tf = tb_desc.text_frame
    tf.word_wrap = True
    tf._txBody.bodyPr.set("anchor", "t")
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.LEFT
    run = para.add_run()
    run.text = str(item.get("descrizione", ""))
    run.font.name = FONT_NAME
    run.font.size = Pt(10)
    run.font.bold = False
    run.font.color.rgb = BLACK

    # — Data —
    tb_date = slide.shapes.add_textbox(DATE_LEFT, y, DATE_WIDTH, item_h)
    tf = tb_date.text_frame
    tf.word_wrap = False
    tf._txBody.bodyPr.set("anchor", "t")
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.CENTER
    run = para.add_run()
    run.text = str(item.get("data", ""))
    run.font.name = FONT_NAME
    run.font.size = Pt(10)
    run.font.bold = False
    run.font.color.rgb = BLACK

    # — Link cliccabile —
    tb_link = slide.shapes.add_textbox(LINK_LEFT, y, LINK_WIDTH, item_h)
    tf = tb_link.text_frame
    tf.word_wrap = False
    tf._txBody.bodyPr.set("anchor", "t")
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.CENTER
    run = para.add_run()
    run.text = "Link"
    run.font.name = FONT_NAME
    run.font.size = Pt(10)
    run.font.bold = False
    run.font.color.rgb = NAVY
    url = item.get("url", "")
    if url:
        run.hyperlink.address = url


# ── Entry point ───────────────────────────────────────────────────────────────

def generate_pptx(
    template_path: str,
    excel_path: str,
    output_path: str,
    numero: str,
    mese: str,
    anno: str,
) -> None:
    """Genera la PPTX con layout dinamico dal template clean e dall'Excel revisionato."""
    grouped = read_approved_news(excel_path)

    prs = Presentation(template_path)
    slide = prs.slides[0]

    _update_edition(slide, numero, mese, anno)
    template_children, template_rels = _save_template_state(slide)

    current_y     = TOP_CONTENT_Y
    first_section = True

    for section in CATEGORY_ORDER:
        items = grouped.get(section, [])
        if not items:
            continue

        icon_path = os.path.join(
            "assets",
            f"icon_{section.lower().replace(' ', '_')}.png",
        )

        # Spazio tra sezioni (non prima della prima)
        if not first_section:
            current_y += SECTION_GAP
        first_section = False

        # Pagina nuova se l'intestazione non entra
        if current_y + SECTION_HEADER_H > BOTTOM_CONTENT_Y:
            slide = _add_content_slide(prs, template_children, template_rels)
            _update_edition(slide, numero, mese, anno)
            current_y = TOP_CONTENT_Y

        _draw_section_header(slide, section, icon_path, current_y)
        current_y += SECTION_HEADER_H

        for item in items:
            item_h = _item_height(item.get("descrizione", ""))

            # Pagina nuova se la notizia non entra
            if current_y + item_h > BOTTOM_CONTENT_Y:
                slide = _add_content_slide(prs, template_children, template_rels)
                _update_edition(slide, numero, mese, anno)
                current_y = TOP_CONTENT_Y

            _draw_news_item(slide, item, current_y, item_h)
            current_y += item_h + ITEM_V_MARGIN

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    prs.save(output_path)
    print(f"[OK] PPTX salvata: {output_path} ({len(prs.slides)} slide)")


def get_output_path(numero: str, mese: str, anno: str) -> str:
    today = date.today().strftime("%Y%m%d")
    return f"output/ALERT_PPT/alert_normativo_N{numero}_{mese}{anno}_{today}.pptx"
