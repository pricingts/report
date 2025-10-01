import io
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter, PageObject

# Tipografías
pdfmetrics.registerFont(TTFont("MiFuente", "resources/fonts/OpenSauceSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Bold", "resources/fonts/OpenSauceSans-Bold.ttf"))

def _get_template_size_points(template_path: str):
    """Lee width/height (en points) de la plantilla PDF."""
    reader = PdfReader(template_path)
    page0 = reader.pages[0]
    w = float(page0.mediabox.width)
    h = float(page0.mediabox.height)
    return w, h


def build_overlay(df: pd.DataFrame, client_name: str, language: str, template_path: str, *,
                LEFT_MARGIN=100, RIGHT_MARGIN=65, BOTTOM_MARGIN=100, TOP_GAP=300) -> bytes:
    """Genera un overlay PDF con encabezado + tabla que fluye automáticamente en varias páginas."""

    page_width, page_height = _get_template_size_points(template_path)

    buf = io.BytesIO()

    doc = BaseDocTemplate(
        buf,
        pagesize=(page_width, page_height),
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_GAP,
        bottomMargin=BOTTOM_MARGIN,
    )

    frame = Frame(
        x1=LEFT_MARGIN,
        y1=BOTTOM_MARGIN,
        width=page_width - (LEFT_MARGIN + RIGHT_MARGIN),
        height=page_height - (TOP_GAP + BOTTOM_MARGIN),
        id="normal",
        showBoundary=0,
    )

    def draw_header(c, _doc):
        now = datetime.now().strftime("%Y-%m-%d")
        c.setFont("Bold", 30)
        c.drawString(680, 915, f"{client_name}")
        c.setFont("Bold", 12)
        c.drawRightString(1620, 925, now)

    template = PageTemplate(id="table_template", frames=[frame], onPage=draw_header)
    doc.addPageTemplates([template])

    # ===== Estilos =====
    styles = {
        "th": ParagraphStyle("th", fontName="MiFuente", fontSize=12, alignment=1, textColor=colors.HexColor("#333333")),
        "td": ParagraphStyle("td", fontName="MiFuente", fontSize=9, alignment=1, textColor=colors.black),
    }

    # Construcción de data para la tabla completa
    data = [[Paragraph(f"<b>{h}</b>", styles["th"]) for h in df.columns]]
    for _, row in df.iterrows():
        data.append([Paragraph(str(row[h]), styles["td"]) for h in df.columns])

    table_width = page_width - (LEFT_MARGIN + RIGHT_MARGIN)
    col_width = table_width / len(df.columns)
    col_widths = [col_width] * (len(df.columns) - 1)
    col_widths.append(table_width - sum(col_widths))

    # Crear tabla completa con encabezado repetido en cada página
    table = Table(data, colWidths=col_widths, repeatRows=1)

    ts = TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "MiFuente"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])

    for row_idx in range(1, len(data)):  
        ts.add("LINEBELOW", (0, row_idx), (-1, row_idx), 0.5, colors.HexColor("#F5F5F5"))


    table.setStyle(ts)

    elements = [table]
    doc.build(elements)

    pdf = buf.getvalue()
    buf.close()
    return pdf


def merge_with_template(template_path: str, overlay_bytes: bytes, output_buffer: io.BytesIO):
    """Superpone todas las páginas del overlay en la plantilla PDF, respetando tamaños."""
    template = PdfReader(template_path)
    overlay = PdfReader(io.BytesIO(overlay_bytes))
    writer = PdfWriter()

    for i, overlay_page in enumerate(overlay.pages):
        base_page = template.pages[i] if i < len(template.pages) else template.pages[0]

        merged = PageObject.create_blank_page(
            width=float(base_page.mediabox.width),
            height=float(base_page.mediabox.height)
        )
        merged.merge_page(base_page)
        merged.merge_page(overlay_page)

        writer.add_page(merged)

    writer.write(output_buffer)
