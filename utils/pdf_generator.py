"""
pdf_generator.py — Professional PDF report for NutriDesk
Uses ReportLab. Produces a branded multi-page PDF with:
  - Cover page
  - Client assessment summary (BMI, BMR, TDEE, macros, hydration)
  - 7-day meal plan table (2 lunch/dinner options per day)
  - Snack swap suggestions
  - Supplement recommendations
  - Personal fat loss rules & realistic timeline
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register Unicode fonts for full IAST support (ā, Ā, etc.) ─────────────
import os as _os

# Bundled fonts (project/fonts/) take priority so the app is self-contained
_BUNDLED = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "fonts")

_FONT_DIRS = [
    _BUNDLED,                                  # Bundled with project (always first)
    "/usr/share/fonts/truetype/dejavu",        # Linux (Debian/Ubuntu)
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts",
    "/Library/Fonts",                          # macOS system-wide
    _os.path.expanduser("~/Library/Fonts"),    # macOS user
    "/System/Library/Fonts/Supplemental",      # macOS (Arial, Verdana, etc.)
    "/System/Library/Fonts",
    "C:\\Windows\\Fonts",                      # Windows
]
_REG_NAMES     = ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "Verdana.ttf"]
_BOLD_NAMES    = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "Verdana Bold.ttf"]
_ITALIC_NAMES  = ["DejaVuSans-Oblique.ttf", "Arial Italic.ttf", "ariali.ttf", "Verdana Italic.ttf"]

def _find_font(names):
    for d in _FONT_DIRS:
        for n in names:
            p = _os.path.join(d, n)
            if _os.path.isfile(p):
                return p
    return None

_font_reg    = _find_font(_REG_NAMES)
_font_bold   = _find_font(_BOLD_NAMES)
_font_italic = _find_font(_ITALIC_NAMES)

try:
    if not (_font_reg and _font_bold):
        raise FileNotFoundError("No suitable Unicode font found")
    pdfmetrics.registerFont(TTFont("DV",         _font_reg))
    pdfmetrics.registerFont(TTFont("DV-Bold",    _font_bold))
    if _font_italic:
        pdfmetrics.registerFont(TTFont("DV-Italic", _font_italic))
    BODY_FONT        = "DV"
    BODY_FONT_BOLD   = "DV-Bold"
    BODY_FONT_ITALIC = "DV-Italic" if _font_italic else "DV"
except Exception:
    BODY_FONT        = "Helvetica"
    BODY_FONT_BOLD   = "Helvetica-Bold"
    BODY_FONT_ITALIC = "Helvetica-Oblique"

# ── Brand colours ──────────────────────────────────────────────────────────
GREEN_DARKEST = HexColor("#1E5C40")
GREEN_DARK  = HexColor("#2D6A4F")
GREEN_MID   = HexColor("#40916C")
GREEN_LIGHT = HexColor("#52B788")
GREEN_PALE  = HexColor("#D8F3DC")
CREAM       = HexColor("#FBF7F2")
CREAM_DARK  = HexColor("#F0E8DC")
CREAM_MID   = HexColor("#EDE0D0")
TEXT_DARK   = HexColor("#111827")
TEXT_MID    = HexColor("#4B5563")
TEXT_LIGHT  = HexColor("#9CA3AF")
ORANGE      = HexColor("#D97706")
AMBER_PALE  = HexColor("#FFF7ED")
WHITE       = colors.white
BLACK       = colors.black

W, H = A4
MARGIN = 2.2 * cm


def _styles():
    s = {}
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName=BODY_FONT_BOLD,
        fontSize=30, textColor=WHITE, alignment=TA_CENTER, spaceAfter=4,
        leading=36,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName=BODY_FONT,
        fontSize=14, textColor=GREEN_PALE, alignment=TA_CENTER, spaceAfter=4,
    )
    s["cover_handle"] = ParagraphStyle(
        "cover_handle", fontName=BODY_FONT,
        fontSize=9, textColor=GREEN_PALE, alignment=TA_CENTER,
    )
    s["table_hdr"] = ParagraphStyle(
        "table_hdr", fontName=BODY_FONT_BOLD,
        fontSize=9, textColor=HexColor("#F0FDF4"),  # off-white on dark green
    )
    s["ex_badge"] = ParagraphStyle(
        "ex_badge", fontName=BODY_FONT_BOLD,
        fontSize=7, textColor=GREEN_MID, alignment=TA_CENTER,
    )
    s["disclaimer"] = ParagraphStyle(
        "disclaimer", fontName=BODY_FONT_ITALIC,
        fontSize=8, textColor=TEXT_LIGHT, leading=12, spaceAfter=4,
    )
    s["section"] = ParagraphStyle(
        "section", fontName=BODY_FONT_BOLD,
        fontSize=12, textColor=GREEN_DARK, spaceAfter=4, spaceBefore=10,
    )
    s["body"] = ParagraphStyle(
        "body", fontName=BODY_FONT,
        fontSize=9.5, textColor=TEXT_MID, leading=14, spaceAfter=4,
    )
    s["small"] = ParagraphStyle(
        "small", fontName=BODY_FONT,
        fontSize=8.5, textColor=TEXT_LIGHT, leading=12,
    )
    s["label"] = ParagraphStyle(
        "label", fontName=BODY_FONT_BOLD,
        fontSize=9, textColor=GREEN_MID, spaceAfter=2,
    )
    s["day_header"] = ParagraphStyle(
        "day_header", fontName=BODY_FONT_BOLD,
        fontSize=9, textColor=WHITE,
    )
    s["recipe_name"] = ParagraphStyle(
        "recipe_name", fontName=BODY_FONT_BOLD,
        fontSize=8.5, textColor=TEXT_MID,
    )
    s["recipe_meta"] = ParagraphStyle(
        "recipe_meta", fontName=BODY_FONT,
        fontSize=7.5, textColor=TEXT_LIGHT,
    )
    s["treat_badge"] = ParagraphStyle(
        "treat_badge", fontName=BODY_FONT_BOLD,
        fontSize=7.5, textColor=HexColor("#92400E"),
    )
    s["timeline_box"] = ParagraphStyle(
        "timeline_box", fontName=BODY_FONT_BOLD,
        fontSize=10, textColor=GREEN_DARK, alignment=TA_CENTER,
    )
    # Bullet with hanging indent — second line aligns with text, not bullet
    s["bullet"] = ParagraphStyle(
        "bullet", fontName=BODY_FONT,
        fontSize=9.5, textColor=TEXT_MID, leading=14, spaceAfter=5,
        leftIndent=14, firstLineIndent=-14,
    )
    s["bullet_bold"] = ParagraphStyle(
        "bullet_bold", fontName=BODY_FONT_BOLD,
        fontSize=9.5, textColor=TEXT_MID, leading=14, spaceAfter=5,
        leftIndent=14, firstLineIndent=-14,
    )
    s["subheading"] = ParagraphStyle(
        "subheading", fontName=BODY_FONT_BOLD,
        fontSize=10, textColor=GREEN_DARK, spaceAfter=3, spaceBefore=8,
    )
    return s


def _decode_list(val):
    """Return a comma-joined string from a list or JSON-encoded list string."""
    import json as _json
    if isinstance(val, list):
        return ", ".join(str(v) for v in val if v)
    if isinstance(val, str):
        try:
            parsed = _json.loads(val)
            if isinstance(parsed, list):
                return ", ".join(str(v) for v in parsed if v)
        except Exception:
            pass
        return val
    return ""


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=GREEN_PALE, spaceAfter=6)


def _section_heading(text: str, s: dict):
    """Section heading with a left green accent bar."""
    inner = Table(
        [[Paragraph("", ParagraphStyle("_sa")),
          Paragraph(text, s["section"])]],
        colWidths=[0.28 * cm, W - 2 * MARGIN - 0.28 * cm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), GREEN_MID),
        ("BACKGROUND",    (1, 0), (1, -1), WHITE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (1, 0), (1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return inner


def _stat_table(data: list[tuple], col_widths=None):
    """Two-column label/value table for stats."""
    col_widths = col_widths or [7 * cm, 8 * cm]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), BODY_FONT),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 0), (0, -1), GREEN_DARK),
        ("TEXTCOLOR",   (1, 0), (1, -1), TEXT_MID),
        ("FONTNAME",    (0, 0), (0, -1), BODY_FONT_BOLD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, CREAM]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.3, CREAM_DARK),
    ]))
    return table


def _recipe_cell(recipes: list[dict], label_a: str, label_b: str, s: dict):
    """Build a cell showing Option A / Option B recipes."""
    content = []
    for i, (recipe, label) in enumerate(zip(recipes, [label_a, label_b])):
        if not recipe:
            continue
        name_ne = recipe.get("name_ne", "")
        kcal    = recipe.get("calories", 0)
        prot    = recipe.get("protein_g", 0)
        desc    = recipe.get("serving_description", "")
        line1 = f"<b>{label}:</b> {recipe['name_en']}"
        if name_ne:
            line1 += f" ({name_ne})"
        content.append(Paragraph(line1, s["recipe_name"]))
        content.append(Paragraph(
            f"{kcal} kcal · {prot}g protein · {desc}", s["recipe_meta"]
        ))
        if i == 0 and len(recipes) > 1:
            content.append(Spacer(1, 3))
    return content


def generate_pdf(
    client: dict,
    assessment: dict,
    plan: dict,
    snack_swaps: list[dict],
    output_path: str = None,
) -> bytes:
    """
    Generate the PDF report and either save to output_path or return bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"NutriDesk Report – {client.get('name', '')}",
        author="Āhāra by Asha",
    )

    s = _styles()
    story = []

    # ── Cover page ───────────────────────────────────────────────────────────

    story.append(Spacer(1, 2.5 * cm))

    # ── Hero brand block ──────────────────────────────────────────────────
    _CW = W - 2 * MARGIN
    hero_data = [
        [Paragraph("NutriDesk", ParagraphStyle(
            "cv_t", fontName=BODY_FONT_BOLD, fontSize=30,
            textColor=WHITE, alignment=TA_CENTER, leading=36, spaceAfter=0,
        ))],
        [Paragraph("Ahara by Asha", ParagraphStyle(
            "cv_s", fontName=BODY_FONT, fontSize=13,
            textColor=GREEN_PALE, alignment=TA_CENTER, leading=18, spaceAfter=0,
        ))],
        [Paragraph("@Asha.Nutrition", ParagraphStyle(
            "cv_h", fontName=BODY_FONT, fontSize=9,
            textColor=HexColor("#B7DFC7"), alignment=TA_CENTER, leading=14, spaceAfter=0,
        ))],
    ]
    hero = Table(hero_data, colWidths=[_CW])
    hero.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GREEN_DARKEST),
        ("TOPPADDING",    (0, 0), (-1, 0),  22),
        ("TOPPADDING",    (0, 1), (-1, 1),   6),
        ("TOPPADDING",    (0, 2), (-1, 2),   4),
        ("BOTTOMPADDING", (0, 0), (-1, 0),   0),
        ("BOTTOMPADDING", (0, 1), (-1, 1),   0),
        ("BOTTOMPADDING", (0, 2), (-1, 2),  22),
        ("LEFTPADDING",   (0, 0), (-1, -1), 24),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 24),
    ]))
    story.append(hero)

    story.append(Spacer(1, 1.8 * cm))

    # ── Client name section ───────────────────────────────────────────────
    story.append(Paragraph(
        "PERSONALISED NUTRITION REPORT",
        ParagraphStyle("ct2", fontName=BODY_FONT_BOLD, fontSize=8,
                       textColor=TEXT_LIGHT, alignment=TA_CENTER,
                       spaceAfter=6, letterSpacing=2),
    ))
    story.append(Paragraph(
        client.get("name", "Client"),
        ParagraphStyle("cn", fontName=BODY_FONT_BOLD, fontSize=28,
                       textColor=GREEN_DARK, alignment=TA_CENTER,
                       spaceAfter=4, leading=34),
    ))
    story.append(Spacer(1, 1.4 * cm))

    # ── Three-column summary strip ─────────────────────────────────────────
    _goal_str = client.get("goal", "")
    _kcal_str = f"{assessment.get('target_calories', 0):.0f} kcal/day"
    _date_str = date.today().strftime("%d %B %Y")

    def _cover_col(top_label, value, sub=""):
        return [
            Paragraph(top_label, ParagraphStyle(
                "csl", fontName=BODY_FONT_BOLD, fontSize=7,
                textColor=TEXT_LIGHT, alignment=TA_CENTER,
                leading=10, spaceAfter=4,
            )),
            Paragraph(value, ParagraphStyle(
                "csv", fontName=BODY_FONT_BOLD, fontSize=13,
                textColor=GREEN_DARK, alignment=TA_CENTER,
                leading=16, spaceAfter=5,
            )),
            Paragraph(sub, ParagraphStyle(
                "css", fontName=BODY_FONT, fontSize=8,
                textColor=TEXT_LIGHT, alignment=TA_CENTER,
                leading=11,
            )),
        ]

    strip_data = [[
        _cover_col("GOAL", _goal_str),
        _cover_col("CALORIE TARGET", _kcal_str),
        _cover_col("REPORT DATE", _date_str),
    ]]
    cover_strip = Table(strip_data, colWidths=[_CW / 3] * 3)
    cover_strip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CREAM),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, CREAM_DARK),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, CREAM_DARK),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE",     (0, 0), (-1, 0),  2, GREEN_MID),
    ]))
    story.append(cover_strip)

    story.append(Spacer(1, 0.8 * cm))

    # ── Quick stats row (BMI, protein, water) ─────────────────────────────
    _bmi    = assessment.get("bmi", "—")
    _prot   = assessment.get("protein_g", "—")
    _water  = assessment.get("hydration_L", "—")
    _tdee   = assessment.get("tdee", "—")

    qs_data = [[
        _cover_col("BMI", str(_bmi), assessment.get("bmi_category", "")),
        _cover_col("PROTEIN", f"{_prot}g/day", "Daily target"),
        _cover_col("WATER", f"{_water}L/day", "Daily target"),
        _cover_col("TDEE", f"{_tdee} kcal", "Maintenance"),
    ]]
    qs = Table(qs_data, colWidths=[_CW / 4] * 4)
    qs.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 1, CREAM_DARK),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, CREAM_DARK),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(qs)

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Prepared by Āhāra by Asha  ·  This report is for personal use only  ·  Not a substitute for medical advice",
        ParagraphStyle("cv_disc", fontName=BODY_FONT_ITALIC, fontSize=7.5,
                       textColor=TEXT_LIGHT, alignment=TA_CENTER),
    ))

    story.append(PageBreak())

    # ── Page 2: Client Profile & Nutrition Targets ───────────────────────────

    story.append(_section_heading("Client Profile", s))
    story.append(_hr())

    bmi_cat = assessment.get("bmi_category", "")
    bmi_val = assessment.get("bmi", 0)
    ideal_l = assessment.get("ideal_weight_low", 0)
    ideal_h = assessment.get("ideal_weight_high", 0)
    _conds  = _decode_list(client.get("medical_conditions", [])) or "None reported"

    _COL_L = 5.5 * cm
    _COL_R = W - 2 * MARGIN - _COL_L

    profile_rows = [
        ["Name",            client.get("name", "—")],
        ["Age / Gender",    f"{assessment.get('age','—')} yrs  ·  {client.get('gender','—')}"],
        ["Height / Weight", f"{client.get('height_cm','—')} cm  ·  {client.get('weight_kg','—')} kg"],
        ["BMI",             f"{bmi_val}  ({bmi_cat})"],
        ["Ideal weight",    f"{ideal_l}–{ideal_h} kg"],
        ["Goal",            client.get("goal", "—")],
        ["Diet type",       client.get("diet_type", "—")],
        ["Activity level",  client.get("activity_level", "—").split("(")[0].strip()],
        ["Medical",         _conds],
        ["BMR / TDEE",      f"{assessment.get('bmr',0)} kcal  ·  {assessment.get('tdee',0)} kcal"],
        ["Calorie target",  f"{assessment.get('target_calories',0)} kcal/day"],
        ["Protein",         f"{assessment.get('protein_g',0)} g/day"],
        ["Carbs",           f"{assessment.get('carbs_g',0)} g/day"],
        ["Fat",             f"{assessment.get('fat_g',0)} g/day"],
        ["Water",           f"{assessment.get('hydration_L',0)} L/day"],
    ]

    profile_table = Table(profile_rows, colWidths=[_COL_L, _COL_R])
    profile_table.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (-1, -1), BODY_FONT),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("FONTNAME",       (0, 0), (0, -1),  BODY_FONT_BOLD),
        ("TEXTCOLOR",      (0, 0), (0, -1),  GREEN_DARK),
        ("TEXTCOLOR",      (1, 0), (1, -1),  TEXT_MID),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, CREAM]),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("GRID",           (0, 0), (-1, -1), 0.3, CREAM_DARK),
        # Highlight the calorie target row
        ("BACKGROUND",     (0, 10), (-1, 10), HexColor("#E9F5EC")),
        ("FONTNAME",       (1, 10), (1, 10),  BODY_FONT_BOLD),
    ]))
    story.append(profile_table)

    # ── Macros Breakdown ──────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(_section_heading("Macro Breakdown", s))
    story.append(_hr())

    _p_g   = assessment.get("protein_g", 0) or 0
    _c_g   = assessment.get("carbs_g", 0)   or 0
    _f_g   = assessment.get("fat_g", 0)     or 0
    _kcal  = assessment.get("target_calories", 1) or 1
    _p_cal = round(_p_g * 4)
    _c_cal = round(_c_g * 4)
    _f_cal = round(_f_g * 9)
    _p_pct = round(_p_cal / _kcal * 100)
    _c_pct = round(_c_cal / _kcal * 100)
    _f_pct = round(_f_cal / _kcal * 100)

    # Header row + data rows
    _macro_hdr = ParagraphStyle("mh", fontName=BODY_FONT_BOLD, fontSize=8.5,
                                textColor=HexColor("#F0FDF4"))
    _macro_body = ParagraphStyle("mb", fontName=BODY_FONT, fontSize=8.5,
                                 textColor=TEXT_MID)
    _macro_data = [
        [Paragraph("Macro",       _macro_hdr),
         Paragraph("Amount",      _macro_hdr),
         Paragraph("Calories",    _macro_hdr),
         Paragraph("% of Total",  _macro_hdr)],
        [Paragraph("Protein",     _macro_body),
         Paragraph(f"{_p_g} g",   _macro_body),
         Paragraph(f"{_p_cal} kcal", _macro_body),
         Paragraph(f"{_p_pct}%",  _macro_body)],
        [Paragraph("Carbohydrates", _macro_body),
         Paragraph(f"{_c_g} g",   _macro_body),
         Paragraph(f"{_c_cal} kcal", _macro_body),
         Paragraph(f"{_c_pct}%",  _macro_body)],
        [Paragraph("Fat",         _macro_body),
         Paragraph(f"{_f_g} g",   _macro_body),
         Paragraph(f"{_f_cal} kcal", _macro_body),
         Paragraph(f"{_f_pct}%",  _macro_body)],
    ]
    _BAR_WIDTHS = [4.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]
    _macro_table = Table(_macro_data, colWidths=_BAR_WIDTHS)
    _macro_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  GREEN_DARKEST),
        ("BACKGROUND",    (0, 1), (-1, 1),  HexColor("#F0FDF4")),
        ("BACKGROUND",    (0, 2), (-1, 2),  HexColor("#FFFDF0")),
        ("BACKGROUND",    (0, 3), (-1, 3),  HexColor("#FEF9EC")),
        ("FONTNAME",      (0, 0), (-1, -1), BODY_FONT),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, HexColor("#E5D9CC")),
        ("LINEBELOW",     (0, 0), (-1, 0),  1, GREEN_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("FONTNAME",      (1, 1), (1, -1),  BODY_FONT_BOLD),
    ]))
    story.append(_macro_table)
    story.append(Paragraph(
        "Protein 4 kcal/g · Carbohydrates 4 kcal/g · Fat 9 kcal/g",
        ParagraphStyle("mn", fontName=BODY_FONT, fontSize=7.5,
                       textColor=TEXT_LIGHT, spaceAfter=2)
    ))

    # ── 7-Day Meal Plan — own page ────────────────────────────────────────

    story.append(PageBreak())
    story.append(_section_heading("7-Day Meal Plan", s))
    story.append(_hr())
    story.append(Paragraph(
        "Lunch and dinner each show two options — choose either on the day. "
        "Calorie values are approximate per serving.",
        s["small"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]

    col_w = [(W - 2 * MARGIN - 3.1 * cm) / 3]
    col_widths = [3.1 * cm] + col_w * 3

    for day in DAYS_ORDER:
        if day not in plan:
            continue
        dp = plan[day]

        breakfast = dp.get("breakfast", [])
        lunch     = dp.get("lunch", [])
        dinner    = dp.get("dinner", [])
        snack     = dp.get("snack", [])

        def recipe_cell(recipes, slots=2):
            if not recipes:
                return [Paragraph("—", s["recipe_meta"])]
            out = []
            labels = ["Option A", "Option B"]
            for i, r in enumerate(recipes[:slots]):
                kcal  = r.get("calories", 0)
                prot  = r.get("protein_g", 0)
                serv  = r.get("serving_description", "")
                label = labels[i] if slots > 1 else ""
                prefix = f"<b>{label}:</b> " if label else ""
                # Treat meal badge (before recipe name)
                if r.get("treat_meal"):
                    out.append(Paragraph("** Treat Meal **", s["treat_badge"]))
                out.append(Paragraph(f"{prefix}{r['name_en']}", s["recipe_name"]))
                out.append(Paragraph(
                    f"{kcal} kcal  |  {prot}g protein"
                    + (f"  |  {serv}" if serv else ""),
                    s["recipe_meta"]
                ))
                if i == 0 and len(recipes) > 1:
                    out.append(Spacer(1, 2))
            return out

        header_cell = Paragraph(day, s["day_header"])

        row = [
            [header_cell],
            recipe_cell(breakfast, slots=1),
            recipe_cell(lunch, slots=2),
            recipe_cell(dinner, slots=2),
        ]

        # Detect treat meals in each slot for cell colouring
        TREAT_AMBER = HexColor("#FFF7ED")
        def _has_treat(recipes): return any(r.get("treat_meal") for r in recipes)
        treat_styles = []
        if _has_treat(breakfast): treat_styles.append(("BACKGROUND", (1,0), (1,0), TREAT_AMBER))
        if _has_treat(lunch):     treat_styles.append(("BACKGROUND", (2,0), (2,0), TREAT_AMBER))
        if _has_treat(dinner):    treat_styles.append(("BACKGROUND", (3,0), (3,0), TREAT_AMBER))

        day_table = Table(
            [row], colWidths=col_widths,
            repeatRows=0,
        )
        day_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), GREEN_DARK),
            ("BACKGROUND",    (1, 0), (-1, 0), WHITE),
            *treat_styles,
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
            ("GRID",          (0, 0), (-1, -1), 0.4, CREAM_DARK),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.8, CREAM_MID),
        ]))

        # Column headers row (only for first day)
        if day == DAYS_ORDER[0]:
            hdr_row = [
                Paragraph("", s["small"]),
                Paragraph("BREAKFAST", s["label"]),
                Paragraph("LUNCH", s["label"]),
                Paragraph("DINNER", s["label"]),
            ]
            hdr_table = Table([hdr_row], colWidths=col_widths)
            hdr_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), GREEN_PALE),
                ("FONTNAME",     (0, 0), (-1, -1), BODY_FONT_BOLD),
                ("FONTSIZE",     (0, 0), (-1, -1), 8),
                ("TEXTCOLOR",    (0, 0), (-1, -1), GREEN_DARK),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
                ("LEFTPADDING",  (0, 0), (-1, -1), 6),
                ("GRID",         (0, 0), (-1, -1), 0.4, CREAM_DARK),
            ]))
            story.append(KeepTogether([hdr_table, day_table]))
        else:
            story.append(day_table)

        story.append(Spacer(1, 0.15 * cm))

    # ── Page: Guidance (Snack Swaps + Supplements + Fat Loss Rules + Lifestyle) ──

    story.append(PageBreak())

    # ── Snack Swaps ────────────────────────────────────────────────────────
    story.append(_section_heading("Snack Swaps", s))
    story.append(_hr())
    story.append(Paragraph(
        "Replace your usual snacks with these better options. Each fits your calorie "
        "target while keeping protein high.",
        s["small"]
    ))
    story.append(Spacer(1, 0.15 * cm))

    if snack_swaps:
        _sw_hdr_style = ParagraphStyle("swh", fontName=BODY_FONT_BOLD, fontSize=8.5,
                                       textColor=HexColor("#F0FDF4"))
        _sw_body_style = ParagraphStyle("swb", fontName=BODY_FONT, fontSize=8.5,
                                        textColor=TEXT_MID)
        _sw_data = [[
            Paragraph("Snack Option", _sw_hdr_style),
            Paragraph("Calories", _sw_hdr_style),
            Paragraph("Protein", _sw_hdr_style),
            Paragraph("Serving", _sw_hdr_style),
        ]]
        for snack in snack_swaps[:5]:
            _sw_data.append([
                Paragraph(snack["name_en"], _sw_body_style),
                Paragraph(f"{snack.get('calories', 0)} kcal", _sw_body_style),
                Paragraph(f"{snack.get('protein_g', 0)}g", _sw_body_style),
                Paragraph(snack.get("serving_description", "—"), _sw_body_style),
            ])
        _CW_local = W - 2 * MARGIN
        _sw_table = Table(_sw_data, colWidths=[_CW_local*0.40, _CW_local*0.18,
                                               _CW_local*0.14, _CW_local*0.28])
        _sw_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  GREEN_DARK),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, CREAM]),
            ("FONTNAME",      (0, 0), (-1, -1), BODY_FONT),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("GRID",          (0, 0), (-1, -1), 0.4, CREAM_DARK),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(_sw_table)

    # ── Supplement Recommendations ─────────────────────────────────────────
    story.append(Spacer(1, 0.35 * cm))
    story.append(_section_heading("Supplement Recommendations", s))
    story.append(_hr())

    conditions = _decode_list(client.get("medical_conditions", [])).split(", ") if client.get("medical_conditions") else []
    supplements = [
        ("Vitamin D3 + K2", "Essential for South Asians. 1000–2000 IU D3 daily with a fatty meal."),
        ("Vitamin B12",      "Critical if vegetarian/vegan. 500 mcg daily or as advised."),
        ("Omega-3 (Fish Oil)", "2–3 g EPA+DHA daily. Anti-inflammatory, supports fat loss and heart health."),
        ("Magnesium Glycinate", "200–400 mg before bed. Supports sleep, stress, and blood sugar."),
    ]
    if "PCOS" in conditions:
        supplements.append(("Inositol (Myo + D-Chiro)", "4g myo + 400mg D-chiro daily. Evidence-based for PCOS insulin sensitivity."))
    if "Diabetes / pre-diabetes" in conditions:
        supplements.append(("Chromium Picolinate", "200–400 mcg daily. Supports glucose regulation — consult your physician."))
    if "Hypothyroidism / thyroid" in conditions:
        supplements.append(("Selenium", "200 mcg daily. Supports thyroid hormone conversion."))

    _sup_hdr = ParagraphStyle("suph", fontName=BODY_FONT_BOLD, fontSize=8.5,
                               textColor=HexColor("#F0FDF4"))
    _sup_name = ParagraphStyle("supn", fontName=BODY_FONT_BOLD, fontSize=8.5,
                                textColor=GREEN_DARK)
    _sup_detail = ParagraphStyle("supd", fontName=BODY_FONT, fontSize=8.5,
                                  textColor=TEXT_MID, leading=12)
    _sup_data = [[
        Paragraph("Supplement", _sup_hdr),
        Paragraph("Recommendation", _sup_hdr),
    ]]
    for name, detail in supplements:
        _sup_data.append([
            Paragraph(name, _sup_name),
            Paragraph(detail, _sup_detail),
        ])
    _CW_local = W - 2 * MARGIN
    _sup_table = Table(_sup_data, colWidths=[_CW_local * 0.35, _CW_local * 0.65])
    _sup_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  GREEN_DARK),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, CREAM]),
        ("FONTNAME",      (0, 0), (-1, -1), BODY_FONT),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, CREAM_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(_sup_table)
    story.append(Spacer(1, 0.12 * cm))
    story.append(Paragraph(
        "Always consult a physician before starting supplements, especially if on medication.",
        s["small"]
    ))

    # ── Fat Loss Rules ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.35 * cm))
    story.append(_section_heading("Your Fat Loss Rules", s))
    story.append(_hr())

    rules = [
        "Eat protein at every meal — it keeps you full and protects muscle while you lose fat.",
        "Drink your daily water target before 7 PM to avoid night-time trips to the bathroom.",
        "No skipping meals — eating less often slows your metabolism and leads to overeating later.",
        "Choose home-cooked options at least 5 out of 7 days. Restaurant meals average 30–40% more calories than they look.",
        "Treat meals are planned, not spontaneous — one enjoyable meal per week, not per day.",
        "Sleep 7–8 hours. Poor sleep raises cortisol, increases cravings for carbs and sugar, and stalls fat loss.",
        "Track your weight weekly (same day, same time, after bathroom). Ignore day-to-day fluctuations.",
        "Progress photos every 4 weeks tell more than the scale — muscle gain can mask fat loss on the scale.",
    ]
    for r in rules:
        story.append(Paragraph(f"• {r}", s["bullet"]))

    # ── Lifestyle Guidelines ───────────────────────────────────────────────
    story.append(Spacer(1, 0.35 * cm))
    story.append(_section_heading("Lifestyle Guidelines", s))
    story.append(_hr())

    _lifestyle = [
        "Drink at least 2–3 litres of water a day",
        "Eat slowly and chew your food very well (at least 20–30 times per bite)",
        "Stick to your meal timings — consistent eating windows support metabolism",
        "Expose yourself to sunlight at sunrise and sunset",
        "At least 6–8 hours of sleep is mandatory",
        "No gadgets 30 minutes before going to sleep",
        "Finish dinner 2–3 hours before bedtime",
        "Fixed sleeping and waking time every day — even on weekends",
        "For every 1 hour of sitting, move around for at least 1–2 minutes",
        "Use only 3–4 tsp of cold-pressed oil per day (mustard / olive / ghee)",
    ]
    for rule in _lifestyle:
        story.append(Paragraph(f"• {rule}", s["bullet"]))

    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Avoid completely:", s["subheading"]))

    _client_diet = client.get("diet_type", "Non-vegetarian")
    _avoid = [
        "Maida and its products", "Fried food", "Oily food", "Sugar and sweets",
        "Fruit juices (fresh or packaged)", "Bakery items", "Pineapple", "Raw papaya",
        "Packaged and processed food", "Packet soup", "Cold drinks", "Alcohol", "Smoking / tobacco",
    ]
    if _client_diet not in ("Vegetarian", "Vegan", "Eggetarian"):
        _avoid.insert(7, "Processed meat")
    for a in _avoid:
        story.append(Paragraph(f"• {a}", s["bullet"]))

    # Condition-specific notes
    _client_conds = _decode_list(client.get("medical_conditions", [])).split(", ") if client.get("medical_conditions") else []
    _cond_notes = []
    if "PCOS" in _client_conds:
        _cond_notes.append(("<b>PCOS note:</b> Consistency in sleep timing and stress management is "
                            "especially important — cortisol spikes worsen hormonal imbalance."))
    if any("diabetes" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Diabetes note:</b> Walk within 15 minutes of finishing a meal to help "
                            "blunt post-meal glucose spikes. Never skip meals."))
    if any("thyroid" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Thyroid note:</b> Take thyroid medication on an empty stomach 30–60 "
                            "minutes before breakfast. Avoid large amounts of raw cruciferous vegetables."))
    if any("hypertension" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Hypertension note:</b> Limit sodium to under 2,000 mg/day. Favour "
                            "home-cooked meals. Increase potassium-rich foods (banana, sweet potato, "
                            "spinach) and maintain consistent meal timings."))
    if any("cholesterol" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>High cholesterol note:</b> Favour unsaturated fats (mustard oil, olive "
                            "oil) over saturated fats. Increase soluble fibre from oats, legumes, and "
                            "vegetables. Aim for 25–35 g of fibre daily."))
    if any("ibs" in c.lower() or "digestive" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>IBS / Digestive note:</b> Eat slowly and chew thoroughly. Avoid very "
                            "spicy or high-fat dishes during flare-ups. Cooked vegetables are better "
                            "tolerated than raw."))
    if any("anaemia" in c.lower() or "iron" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Anaemia / Iron note:</b> Pair iron-rich foods (dal, spinach, meat, "
                            "chana) with vitamin C sources (lemon, amla, tomato). Avoid tea or coffee "
                            "within one hour of meals — tannins inhibit iron uptake."))
    if any("fatty liver" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Fatty liver note:</b> Avoid fried foods, refined sugars, and alcohol "
                            "completely. Prioritise high-fibre vegetables, legumes, and lean protein."))
    if any("kidney" in c.lower() for c in _client_conds):
        _cond_notes.append(("<b>Kidney disease — specialist guidance required:</b> Kidney disease "
                            "requires a tailored renal diet. Consult a nephrologist or renal dietitian "
                            "before following any meal plan."))
    if _cond_notes:
        story.append(Spacer(1, 0.2 * cm))
        for note in _cond_notes:
            story.append(Paragraph(f"• {note}", s["bullet"]))

    # ── Realistic Timeline ─────────────────────────────────────────────────
    goal = client.get("goal", "")
    weight = client.get("weight_kg", 0)

    if goal in ("Fat loss", "Mild fat loss") and weight:
        story.append(Spacer(1, 0.35 * cm))
        story.append(_section_heading("Realistic Timeline", s))
        story.append(_hr())

        ideal_low  = assessment.get("ideal_weight_low", 0)
        kg_to_lose = max(0, round(weight - ideal_low, 1))
        weekly     = 0.5 if goal == "Fat loss" else 0.25
        weeks      = round(kg_to_lose / weekly) if weekly else 0
        months     = round(weeks / 4.3, 1)

        timeline_data = [
            ["Current Weight",        f"{weight} kg"],
            ["Target Weight (ideal)", f"{ideal_low} kg"],
            ["Fat to Lose",           f"{kg_to_lose} kg"],
            ["Estimated Rate",        f"{weekly} kg/week (sustainable)"],
            ["Estimated Duration",    f"{weeks} weeks (~{months} months)"],
        ]
        story.append(_stat_table(timeline_data))
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph(
            "Sustainable fat loss is 0.25–0.5 kg per week. Faster loss risks muscle loss, "
            "metabolic adaptation, and nutrient deficiencies. Slow and steady wins this race.",
            s["small"]
        ))

    # ── Exercise Plan page ─────────────────────────────────────────────────

    story.append(PageBreak())
    story.append(_section_heading("Exercise Plan", s))
    story.append(_hr())

    fitness_level  = client.get("fitness_level") or "Moderate"
    exercise_notes = client.get("exercise_notes") or ""

    _rounds_map = {"Beginner": 1, "Moderate": 2, "Advanced": 3}
    _skips_map  = {"Beginner": 200, "Moderate": 350, "Advanced": 500}
    _steps_map  = {"Beginner": 7000, "Moderate": 8500, "Advanced": 10000}

    _rounds = _rounds_map.get(fitness_level, 2)
    _skips  = _skips_map.get(fitness_level, 350)
    _steps  = _steps_map.get(fitness_level, 8500)

    # ── Fitness summary: 4-column stat bar (no mid-item line breaks) ───────
    _CW_local = W - 2 * MARGIN
    _fit_lbl = ParagraphStyle("fitl", fontName=BODY_FONT_BOLD, fontSize=7.5,
                               textColor=TEXT_LIGHT, alignment=TA_CENTER, leading=10, spaceAfter=3)
    _fit_val = ParagraphStyle("fitv", fontName=BODY_FONT_BOLD, fontSize=12,
                               textColor=GREEN_DARK, alignment=TA_CENTER, leading=15, spaceAfter=0)
    _fit_data = [[
        [Paragraph("FITNESS LEVEL",   _fit_lbl), Paragraph(fitness_level,       _fit_val)],
        [Paragraph("CIRCUIT ROUNDS",  _fit_lbl), Paragraph(str(_rounds),        _fit_val)],
        [Paragraph("DAILY SKIPPING",  _fit_lbl), Paragraph(f"{_skips:,} skips", _fit_val)],
        [Paragraph("STEP TARGET",     _fit_lbl), Paragraph(f"{_steps:,}/day",   _fit_val)],
    ]]
    _fit_table = Table(_fit_data, colWidths=[_CW_local / 4] * 4)
    _fit_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CREAM),
        ("BOX",           (0, 0), (-1, -1), 1, CREAM_DARK),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, CREAM_DARK),
        ("LINEABOVE",     (0, 0), (-1, 0),  2, GREEN_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(_fit_table)

    if exercise_notes:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(f"Notes: {exercise_notes}", s["small"]))

    story.append(Spacer(1, 0.3 * cm))

    # Daily movement targets
    story.append(Paragraph("Daily Movement", s["subheading"]))
    _move_rules = [
        "Daily skipping and step targets apply on all exercise days (5–6 days per week).",
        "After Breakfast — 10-minute stroll",
        "After Lunch — 15-minute stroll",
        "After Snack — 10-minute stroll",
        "After Dinner — 15–20 minute stroll",
        "For every 1 hour of sitting, move around for at least 1–2 minutes.",
    ]
    for mr in _move_rules:
        story.append(Paragraph(f"• {mr}", s["bullet"]))

    story.append(Spacer(1, 0.35 * cm))

    # Circuit exercises
    _circuit = [
        ("Jumping Jacks",                  {"Beginner": "30", "Moderate": "40", "Advanced": "50"}),
        ("Crunches",                        {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Leg Raise",                       {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Elbow-to-Knee Oblique Crunches",  {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Russian Twist (2L bottle)",       {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Leg Straight Hold",               {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}),
        ("Heel Touch",                      {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Cross Leg",                       {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Bicycle Crunches",                {"Beginner":  "8", "Moderate": "10", "Advanced": "12"}),
        ("Plank",                           {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}),
    ]
    _rep_scale = {
        1: {"Beginner": "Beginner", "Moderate": "Moderate", "Advanced": "Advanced"},
        2: {"Beginner": "Beginner", "Moderate": "Beginner",  "Advanced": "Moderate"},
        3: {"Beginner": "Beginner", "Moderate": "Beginner",  "Advanced": "Beginner"},
    }
    _round_names = {1: "Round 1", 2: "Round 2", 3: "Round 3"}

    _EX_CREAM = HexColor("#FBF7F2")
    _ex_badge = {
        "Jumping Jacks":                 "CARDIO",
        "Crunches":                      "CORE",
        "Leg Raise":                     "CORE",
        "Elbow-to-Knee Oblique Crunches":"OBLIQUE",
        "Russian Twist (2L bottle)":     "OBLIQUE",
        "Leg Straight Hold":             "HOLD",
        "Heel Touch":                    "OBLIQUE",
        "Cross Leg":                     "CORE",
        "Bicycle Crunches":              "CARDIO",
        "Plank":                         "PLANK",
    }

    for rnum in range(1, _rounds + 1):
        story.append(Spacer(1, 0.25 * cm))
        eff = _rep_scale[rnum][fitness_level]

        _circ_data = [[
            Paragraph(_round_names[rnum], s["table_hdr"]),
            Paragraph("Exercise",         s["table_hdr"]),
            Paragraph("Reps / Duration",  s["table_hdr"]),
        ]]
        for ex_name, reps_d in _circuit:
            reps_val = reps_d[eff]
            reps_str = reps_val if isinstance(reps_val, str) else f"{reps_val} reps"
            badge = _ex_badge.get(ex_name, "")
            _circ_data.append([
                Paragraph(badge,    s["ex_badge"]),
                Paragraph(ex_name,  s["body"]),
                Paragraph(reps_str, s["body"]),
            ])

        _circ_table = Table(_circ_data, colWidths=[2.5 * cm, 10 * cm, 4 * cm])
        _circ_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  GREEN_DARK),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  BODY_FONT_BOLD),
            ("FONTNAME",       (0, 1), (-1, -1), BODY_FONT),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_EX_CREAM, colors.white]),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#E5D9CC")),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether([_circ_table]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Rest 60–90 seconds between rounds. Aim for 5–6 sessions per week. "
        "Combine with your daily walk targets for best results.",
        s["small"]
    ))

    # ── Disclaimer ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(_hr())
    story.append(_section_heading("Disclaimer", s))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"This report was prepared by Ahara by Asha on {date.today().strftime('%d %B %Y')}. "
        "It is intended as personalised dietary and lifestyle guidance based on the information "
        "provided at the time of assessment. This report does not constitute medical advice and "
        "is not a substitute for consultation with a qualified physician or healthcare provider. "
        "Individual results may vary. Please consult your doctor before making any significant "
        "changes to your diet, exercise routine, or supplement intake, particularly if you have "
        "an existing medical condition or are on medication.",
        s["disclaimer"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
