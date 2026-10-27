from io import BytesIO
from pathlib import Path

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


COLOR_NAMES = {"dark_gray": "Тёмно-серый", "light_gray": "Светло-серый", "black": "Чёрный", "beige": "Бежевый"}


def _font_name():
    candidates = (
        Path(__file__).resolve().parent / "fonts" / "DejaVuSans.ttf",
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )
    for path in candidates:
        if path.is_file():
            if "RampCyrillic" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("RampCyrillic", str(path)))
            return "RampCyrillic"
    raise RuntimeError("Не найден шрифт с поддержкой кириллицы для PDF.")


def _number(value, digits=1):
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def build_brief_pdf(brief):
    """Create a customer-readable specification from server-calculated values."""
    result = brief.result
    geometry = result["geometry"]
    font = _font_name()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595.28, 841.89), leftMargin=43, rightMargin=43, topMargin=43, bottomMargin=43)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RampTitle", fontName=font, fontSize=17, leading=23, textColor=colors.HexColor("#294b3b"), spaceAfter=10))
    styles.add(ParagraphStyle(name="RampHeading", fontName=font, fontSize=11, leading=16, textColor=colors.HexColor("#294b3b"), spaceBefore=17, spaceAfter=8))
    styles.add(ParagraphStyle(name="RampText", fontName=font, fontSize=9, leading=14))
    styles.add(ParagraphStyle(name="RampSmall", fontName=font, fontSize=8, leading=12, textColor=colors.HexColor("#666c67")))
    styles.add(ParagraphStyle(name="RampFooter", parent=styles["RampSmall"], alignment=TA_CENTER))
    p = lambda value, style="RampText": Paragraph(escape(str(value)).replace("\n", "<br/>"), styles[style])
    rows = [
        ("Высота подъёма", f"{_number(result['height_cm'])} см"),
        ("Длина наклонной поверхности", f"{_number(result['ramp_length_cm'])} см"),
        ("Ширина поверхности", f"{_number(result['width_cm'])} см"),
        ("Угол наклона", f"{_number(result['angle_deg'])}°"),
        ("Длина нижнего основания", f"{round(geometry['base_length_cm'])} см"),
        ("Опорная стойка", f"{_number(geometry['support_length_cm'])} × {_number(result['support_panel_width_cm'])} см"),
        ("Положение шарнира", f"{_number(geometry['support']['hinge_distance_cm'])} см от начала поверхности"),
        ("Цвет покрытия", COLOR_NAMES.get(result["color"], result["color"])),
        ("Поперечные рейки", f"{result['step_count']} шт.; 0,8 × 3 × {_number(result['width_cm'])} см" if result["has_slats"] else "Не предусмотрены"),
        ("Боковые бортики", "2 шт." if result["side_rails"] else "Не предусмотрены"),
        ("Ориентировочная стоимость", f"{int(result['price']['total_price_rub']):,} руб.".replace(",", " ")),
    ]
    document_label = f"№ {brief.pk} от {timezone.localtime(brief.created_at):%d.%m.%Y}" if brief.pk else f"Предварительный расчёт от {timezone.localtime():%d.%m.%Y}"
    story = [p("RAMP · Техническое задание", "RampTitle"), p(document_label, "RampSmall"),
             p("Заказчик", "RampHeading"), p(" · ".join(filter(None, (brief.customer.name, brief.customer.phone, brief.customer.email)))),
             p("Параметры изделия", "RampHeading")]
    table = Table([[p(k), p(v)] for k, v in rows], colWidths=[255, 254], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f3f6f3")]), ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#cbd5ce")), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(table)
    if result["has_slats"]:
        story.extend([p("Расположение реек", "RampHeading"), p(", ".join(_number(n) for n in result["step_positions_cm"]) + " см от нижнего края")])
    story.extend([p("Комментарий заказчика", "RampHeading"), p(brief.message or "Нет комментария"), Spacer(1, 14),
                  p("Размеры и стоимость рассчитаны по выбранным параметрам. Перед изготовлением детали заказа согласуются с мастером.", "RampSmall")])
    doc.build(story)
    return buffer.getvalue()
