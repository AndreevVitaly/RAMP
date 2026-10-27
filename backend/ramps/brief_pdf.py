from io import BytesIO
import base64
from pathlib import Path

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


COLOR_NAMES = {"dark_gray": "Тёмно-серый", "light_gray": "Светло-серый", "black": "Чёрный", "beige": "Бежевый"}
SURFACE_COLORS = {"dark_gray": "#555957", "light_gray": "#b7b9b6", "black": "#292b2a", "beige": "#c7af8d"}


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


def _polygon(points, **kwargs):
    return Polygon([coordinate for point in points for coordinate in point], **kwargs)


def _projection_drawing(result, view, font):
    """Render compact customer-facing projections from the calculated geometry."""
    drawing = Drawing(162, 112)
    g = result["geometry_3d"]
    dimensions = g["dimensions"]
    run, width, height = dimensions["horizontal_run_cm"], dimensions["width_cm"], dimensions["height_cm"]
    surface = colors.HexColor(SURFACE_COLORS.get(result["color"], SURFACE_COLORS["dark_gray"]))
    edge = colors.HexColor("#294b3b")
    slat = colors.HexColor("#77736b")
    drawing.add(Rect(0, 0, 162, 112, fillColor=colors.HexColor("#f6f8f6"), strokeColor=colors.HexColor("#d8dfda"), rx=5, ry=5))

    if view == "side":
        scale = min(140 / max(run, 1), 72 / max(height + 7, 1))
        ox, oy = 10, 22
        point = lambda x, z: (ox + x * scale, oy + z * scale)
        base_end = g["base"]["length_cm"]
        drawing.add(Line(*point(0, 0), *point(base_end, 0), strokeColor=edge, strokeWidth=2.2))
        support = g["support"]["axis"]
        drawing.add(Line(*point(support["foot"]["x"], support["foot"]["z"]), *point(support["hinge"]["x"], support["hinge"]["z"]), strokeColor=surface, strokeWidth=7))
        drawing.add(Line(*point(0, 0), *point(run, height), strokeColor=surface, strokeWidth=8))
        drawing.add(Line(*point(0, 0), *point(run, height), strokeColor=edge, strokeWidth=1))
        if result["side_rails"]:
            panel = g["side_panels"]["left"]
            drawing.add(_polygon([point(panel[key]["x"], panel[key]["z"]) for key in ("bottom_start", "bottom_end", "top_end", "top_start")], fillColor=surface, strokeColor=edge, strokeWidth=.8))
        if result["has_slats"] and not result["side_rails"]:
            for step in g["steps"]:
                drawing.add(Line(*point(step["start_left"]["x"], step["start_left"]["z"]), *point(step["top_start_left"]["x"], step["top_start_left"]["z"]), strokeColor=slat, strokeWidth=2))
        label = "Сбоку"
    elif view == "top":
        scale = min(140 / max(result["ramp_length_cm"], 1), 66 / max(width, 1))
        ox, oy = 10, 24 + (66 - width * scale) / 2
        drawing.add(Rect(ox, oy, result["ramp_length_cm"] * scale, width * scale, fillColor=surface, strokeColor=edge, strokeWidth=1))
        if result["has_slats"]:
            for position in result["step_positions_cm"]:
                drawing.add(Rect(ox + position * scale, oy, result["step_width_cm"] * scale, width * scale, fillColor=slat, strokeColor=None))
        label = "Сверху"
    else:
        project = lambda x, y, z: (12 + (x + y * .42) * .92, 23 + (z + y * .26) * .92)
        corners = g["ramp_surface"]["corners"]
        a_l, a_r, b_l, b_r = (corners[key] for key in ("a_left", "a_right", "b_left", "b_right"))
        drawing.add(_polygon([project(p["x"], p["y"], p["z"]) for p in (a_l, b_l, b_r, a_r)], fillColor=surface, strokeColor=edge, strokeWidth=1))
        for step in g["steps"] if result["has_slats"] else []:
            drawing.add(Line(*project(step["start_left"]["x"], 0, step["start_left"]["z"]), *project(step["start_right"]["x"], width, step["start_right"]["z"]), strokeColor=slat, strokeWidth=2.4))
        support = g["support"]["axis"]
        drawing.add(Line(*project(support["foot"]["x"], width / 2, support["foot"]["z"]), *project(support["hinge"]["x"], width / 2, support["hinge"]["z"]), strokeColor=surface, strokeWidth=8))
        drawing.add(Line(*project(0, 0, 0), *project(g["base"]["length_cm"], 0, 0), strokeColor=edge, strokeWidth=2))
        label = "Аксонометрия"

    drawing.add(String(81, 7, label, textAnchor="middle", fontName=font, fontSize=8, fillColor=edge))
    return drawing


def _geometry_sheet(result, font):
    """Mirror the successful dimensioned XZ profile used by the configurator."""
    drawing = Drawing(509, 210)
    edge = colors.HexColor("#294b3b")
    muted = colors.HexColor("#6a716c")
    accent = colors.HexColor("#a46f35")
    surface = colors.HexColor(SURFACE_COLORS.get(result["color"], SURFACE_COLORS["dark_gray"]))
    geometry, g3 = result["geometry"], result["geometry_3d"]
    points = geometry["points"]
    run, height, width = result["horizontal_run_cm"], result["height_cm"], result["width_cm"]
    drawing.add(Rect(0, 0, 509, 210, fillColor=colors.HexColor("#f6f8f6"), strokeColor=colors.HexColor("#d8dfda"), rx=5, ry=5))

    # Main manufacturing profile (XZ).
    scale = min(405 / max(run, 1), 118 / max(height, 1))
    ox, oy = 32, 57
    p = lambda source: (ox + source["x"] * scale, oy + source["y"] * scale)
    a, b, c = points["ramp_start"], points["ramp_end"], points["base_end"]
    d, s = points["support_hinge"], points["support_foot"]
    drawing.add(Line(16, oy, 493, oy, strokeColor=muted, strokeWidth=.6))
    drawing.add(Line(*p(a), *p(c), strokeColor=edge, strokeWidth=2))
    drawing.add(Line(*p(a), *p(b), strokeColor=surface, strokeWidth=7))
    drawing.add(Line(*p(a), *p(b), strokeColor=edge, strokeWidth=1))
    drawing.add(Line(*p(s), *p(d), strokeColor=surface, strokeWidth=7))
    drawing.add(Line(*p(s), *p(d), strokeColor=edge, strokeWidth=1))
    drawing.add(Line(p(b)[0], p(b)[1], p(b)[0], oy, strokeColor=muted, strokeWidth=.5, strokeDashArray=[2, 2]))
    for name, source, dx, dy in (("A", a, -8, 5), ("B", b, 5, 5), ("C — конец основания", c, 5, 5), ("D", d, -3, 9), ("S", s, -3, -12)):
        x, y = p(source)
        drawing.add(String(x + dx, y + dy, name, fontName=font, fontSize=7, fillColor=edge))
    drawing.add(Line(p(d)[0], p(d)[1], p(d)[0], p(d)[1], strokeColor=accent, strokeWidth=6))
    drawing.add(String(18, 193, "Геометрический профиль пандуса", fontName=font, fontSize=10, fillColor=edge))
    drawing.add(String(p(d)[0] - 10, p(d)[1] + 17, "D — шарнир, 75%", textAnchor="end", fontName=font, fontSize=7, fillColor=accent))
    drawing.add(String(p(s)[0] - 10, oy + 11, "упор", textAnchor="end", fontName=font, fontSize=7, fillColor=accent))
    drawing.add(String(p(b)[0] + 10, oy + height * scale / 2, f"высота {_number(height)} см", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String((p(a)[0] + p(d)[0]) / 2 - 12, (p(a)[1] + p(d)[1]) / 2 + 14, f"A→D {_number(geometry['measurements']['ramp_start_to_hinge_cm'])} см", textAnchor="middle", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String((p(a)[0] + p(s)[0]) / 2, oy - 14, f"A→S {_number(geometry['measurements']['ramp_start_to_support_foot_cm'])} см", textAnchor="middle", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String((p(s)[0] + p(c)[0]) / 2, oy - 14, f"S→C {_number(geometry['measurements']['support_foot_to_base_end_cm'])} см", textAnchor="middle", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String(p(a)[0] + 42, oy + 8, f"наклон {_number(result['angle_deg'])}°", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String((p(s)[0] + p(d)[0]) / 2 + 12, (p(s)[1] + p(d)[1]) / 2 + 7, f"D→S {_number(geometry['measurements']['support_length_cm'])} см", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String((p(s)[0] + p(d)[0]) / 2 + 12, (p(s)[1] + p(d)[1]) / 2 - 5, f"{_number(geometry['support']['floor_angle_deg'])}° к полу", fontName=font, fontSize=7, fillColor=muted))
    drawing.add(String(p(s)[0], oy - 29, "S — опора стойки", textAnchor="middle", fontName=font, fontSize=7, fillColor=muted))
    vx = ox + points["vertical_projection"]["x"] * scale
    cx = p(c)[0]
    dimension_y = oy - 32
    drawing.add(Line(cx, dimension_y, vx, dimension_y, strokeColor=accent, strokeWidth=.7))
    drawing.add(Line(cx, dimension_y - 4, cx, dimension_y + 4, strokeColor=accent, strokeWidth=.7))
    drawing.add(Line(vx, dimension_y - 4, vx, dimension_y + 4, strokeColor=accent, strokeWidth=.7))
    drawing.add(String((cx + vx) / 2, dimension_y - 11, f"отступ {_number(geometry['base_vertical_offset_cm'])} см", textAnchor="middle", fontName=font, fontSize=7, fillColor=accent))
    drawing.add(String(18, 9, "Стойка идёт от опоры S вверх-вправо к шарниру D; точка C обозначает конец основания.", fontName=font, fontSize=7, fillColor=muted))
    return drawing


def _captured_profile(brief):
    value = getattr(brief, "profile_image", "")
    if not value:
        return None
    raw = base64.b64decode(value.split(",", 1)[1])
    image = Image(BytesIO(raw), width=509, height=304)
    image.hAlign = "LEFT"
    return image


def build_brief_pdf(brief):
    """Create a customer-readable specification from server-calculated values."""
    result = brief.result
    geometry = result["geometry"]
    font = _font_name()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595.28, 841.89), leftMargin=43, rightMargin=43, topMargin=43, bottomMargin=43)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RampTitle", fontName=font, fontSize=17, leading=23, textColor=colors.HexColor("#294b3b"), spaceAfter=10))
    styles.add(ParagraphStyle(name="RampHeading", fontName=font, fontSize=10, leading=13, textColor=colors.HexColor("#294b3b"), spaceBefore=9, spaceAfter=5))
    styles.add(ParagraphStyle(name="RampText", fontName=font, fontSize=8, leading=10))
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
             p("Геометрия изделия", "RampHeading"), _captured_profile(brief) or _geometry_sheet(result, font),
             p("Параметры изделия", "RampHeading")]
    compact_rows = []
    for index in range(0, len(rows), 2):
        left = rows[index]
        right = rows[index + 1] if index + 1 < len(rows) else ("", "")
        compact_rows.append([p(left[0]), p(left[1]), p(right[0]), p(right[1])])
    table = Table(compact_rows, colWidths=[142, 102, 142, 123], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f3f6f3")]), ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#cbd5ce")), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(table)
    if result["has_slats"]:
        story.extend([p("Расположение реек", "RampHeading"), p(", ".join(_number(n) for n in result["step_positions_cm"]) + " см от нижнего края")])
    story.extend([p("Комментарий заказчика", "RampHeading"), p(brief.message or "Нет комментария"), Spacer(1, 14),
                  p("Размеры и стоимость рассчитаны по выбранным параметрам. Перед изготовлением детали заказа согласуются с мастером.", "RampSmall")])
    doc.build(story)
    return buffer.getvalue()
