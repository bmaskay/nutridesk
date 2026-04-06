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

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",       # Linux (Debian/Ubuntu)
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts",
    "/Library/Fonts",                          # macOS system-wide
    _os.path.expanduser("~/Library/Fonts"),    # macOS user
    "/System/Library/Fonts/Supplemental",      # macOS (Arial, Verdana, etc.)
    "/System/Library/Fonts",
    "C:\\Windows\\Fonts",                      # Windows
]
_REG_NAMES  = ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "Verdana.ttf"]
_BOLD_NAMES = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "Verdana Bold.ttf"]

def _find_font(names):
    for d in _FONT_DIRS:
        for n in names:
            p = _os.path.join(d, n)
            if _os.path.isfile(p):
                return p
    return None

_font_reg  = _find_font(_REG_NAMES)
_font_bold = _find_font(_BOLD_NAMES)

try:
    if not (_font_reg and _font_bold):
        raise FileNotFoundError("No suitable Unicode font found")
    pdfmetrics.registerFont(TTFont("DV",      _font_reg))
    pdfmetrics.registerFont(TTFont("DV-Bold", _font_bold))
    BODY_FONT      = "DV"
    BODY_FONT_BOLD = "DV-Bold"
except Exception:
    BODY_FONT      = "Helvetica"
    BODY_FONT_BOLD = "Helvetica-Bold"

# ── Brand colours ──────────────────────────────────────────────────────────
GREEN_DARK  = HexColor("#2D6A4F")
GREEN_MID   = HexColor("#40916C")
GREEN_PALE  = HexColor("#D8F3DC")
CREAM       = HexColor("#FBF7F2")
CREAM_DARK  = HexColor("#F0E8DC")
TEXT_MID    = HexColor("#4B5563")
TEXT_LIGHT  = HexColor("#9CA3AF")
ORANGE      = HexColor("#D97706")
WHITE       = colors.white
BLACK       = colors.black

W, H = A4
MARGIN = 2.2 * cm


def _styles():
    s = {}
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName=BODY_FONT_BOLD,
        fontSize=32, textColor=WHITE, alignment=TA_CENTER, spaceAfter=6,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName=BODY_FONT,
        fontSize=14, textColor=GREEN_PALE, alignment=TA_CENTER, spaceAfter=4,
    )
    s["cover_handle"] = ParagraphStyle(
        "cover_handle", fontName=BODY_FONT,
        fontSize=9, textColor=GREEN_PALE, alignment=TA_CENTER,
    )
    s["section"] = ParagraphStyle(
        "section", fontName=BODY_FONT_BOLD,
        fontSize=13, textColor=GREEN_DARK, spaceAfter=6, spaceBefore=14,
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
    return s


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=GREEN_PALE, spaceAfter=6)


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
        author="Ahara by Asha",
    )

    s = _styles()
    story = []

    # ── Cover page ───────────────────────────────────────────────────────────

    story.append(Spacer(1, 4 * cm))

    # Top brand block: NutriDesk (large) + Ahara by Asha below
    cover_brand = Table(
        [[Paragraph("NutriDesk", s["cover_title"])],
         [Paragraph("Āhāra by Asha", ParagraphStyle(
             "ca", fontName=BODY_FONT, fontSize=15, textColor=GREEN_PALE,
             alignment=TA_CENTER, spaceAfter=2)
         )],
         [Paragraph("@Asha.Nutrition", ParagraphStyle(
             "ch", fontName=BODY_FONT, fontSize=10, textColor=GREEN_PALE,
             alignment=TA_CENTER)
         )],
        ],
        colWidths=[W - 2 * MARGIN]
    )
    cover_brand.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GREEN_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("LINEBELOW",     (0, -1), (-1, -1), 4, GREEN_MID),
    ]))
    story.append(cover_brand)

    story.append(Spacer(1, 2.5 * cm))

    # "Personalised Nutrition Report For" label
    story.append(Paragraph(
        "PERSONALISED NUTRITION REPORT",
        ParagraphStyle("ct2", fontName=BODY_FONT_BOLD, fontSize=10,
                       textColor=TEXT_LIGHT, alignment=TA_CENTER,
                       spaceAfter=8)
    ))

    # Client name — large and prominent
    story.append(Paragraph(
        client.get("name", "Client"),
        ParagraphStyle("cn", fontName=BODY_FONT_BOLD, fontSize=28,
                       textColor=GREEN_DARK, alignment=TA_CENTER, spaceAfter=8)
    ))

    story.append(Spacer(1, 0.5 * cm))

    # Goal + date row
    goal_str = client.get("goal", "")
    story.append(Paragraph(
        f"Goal: {goal_str}     |     Prepared: {date.today().strftime('%d %B %Y')}",
        ParagraphStyle("cg", fontName=BODY_FONT, fontSize=10,
                       textColor=TEXT_MID, alignment=TA_CENTER)
    ))

    story.append(PageBreak())

    # ── Section 1: Client Profile ─────────────────────────────────────────

    story.append(Paragraph("Client Profile", s["section"]))
    story.append(_hr())

    profile_data = [
        ["Name",        client.get("name", "—")],
        ["Gender",      client.get("gender", "—")],
        ["Date of Birth", client.get("dob", "—")],
        ["Age",         f"{assessment.get('age', '—')} years"],
        ["Height",      f"{client.get('height_cm', '—')} cm"],
        ["Current Weight", f"{client.get('weight_kg', '—')} kg"],
        ["Goal",        client.get("goal", "—")],
        ["Activity Level", client.get("activity_level", "—")],
        ["Diet Type",   client.get("diet_type", "—")],
        ["Medical Conditions",
         ", ".join(client.get("medical_conditions", [])) or "None reported"],
    ]
    story.append(_stat_table(profile_data))

    # ── Section 2: Assessment ──────────────────────────────────────────────

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Nutritional Assessment", s["section"]))
    story.append(_hr())

    bmi_cat = assessment.get("bmi_category", "")
    bmi_val = assessment.get("bmi", 0)
    ideal_l = assessment.get("ideal_weight_low", 0)
    ideal_h = assessment.get("ideal_weight_high", 0)

    assess_data = [
        ["BMI",             f"{bmi_val}  ({bmi_cat})"],
        ["Ideal Weight Range", f"{ideal_l} – {ideal_h} kg"],
        ["BMR (Basal Metabolic Rate)", f"{assessment.get('bmr', 0)} kcal/day"],
        ["TDEE (Total Daily Energy)", f"{assessment.get('tdee', 0)} kcal/day"],
        ["Goal Adjustment", f"{assessment.get('goal_adjustment', 0):+.0f} kcal/day"],
        ["Daily Calorie Target", f"{assessment.get('target_calories', 0)} kcal/day"],
        ["Protein Target",  f"{assessment.get('protein_g', 0)} g/day"],
        ["Carbohydrate Target", f"{assessment.get('carbs_g', 0)} g/day"],
        ["Fat Target",      f"{assessment.get('fat_g', 0)} g/day"],
        ["Daily Hydration", f"{assessment.get('hydration_L', 0)} L/day"],
    ]
    story.append(_stat_table(assess_data))

    # ── Diet duration box ─────────────────────────────────────────────────
    goal      = client.get("goal", "")
    weight    = client.get("weight_kg", 0) or 0
    ideal_low = assessment.get("ideal_weight_low", 0)
    kg_to_go  = max(0, round(weight - ideal_low, 1)) if goal in ("Fat loss", "Mild fat loss") else 0
    weekly_r  = 0.5 if goal == "Fat loss" else 0.25 if goal == "Mild fat loss" else 0
    if weekly_r and kg_to_go:
        weeks_est  = round(kg_to_go / weekly_r)
        months_est = round(weeks_est / 4.3, 1)
        duration_text = (
            f"To reach your target weight of {ideal_low} kg, "
            f"follow this plan for approximately "
            f"{weeks_est} weeks ({months_est} months) "
            f"at the recommended rate of {weekly_r} kg/week."
        )
    elif goal in ("Lean muscle gain", "Muscle gain"):
        duration_text = (
            "Muscle gain is a gradual process. Follow this nutrition plan for at least "
            "12–16 weeks, paired with consistent resistance training, before reassessing."
        )
    else:
        duration_text = (
            "Follow this nutrition plan consistently for at least 4 weeks before "
            "reassessing calorie targets and making adjustments."
        )

    duration_table = Table(
        [[Paragraph(f"How long to follow: {duration_text}", s["body"])]],
        colWidths=[W - 2 * MARGIN]
    )
    duration_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#F0FDF4")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, GREEN_MID),
    ]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(duration_table)

    # ── Section 3: 7-Day Meal Plan ─────────────────────────────────────────

    story.append(PageBreak())
    story.append(Paragraph("7-Day Meal Plan", s["section"]))
    story.append(_hr())
    story.append(Paragraph(
        "Lunch and dinner show two options — choose either on the day. "
        "Calorie values are approximate per serving.",
        s["small"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]

    col_w = [(W - 2 * MARGIN - 2.5 * cm) / 3]
    col_widths = [2.5 * cm] + col_w * 3

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
            ("BACKGROUND",   (0, 0), (0, 0), GREEN_MID),
            ("BACKGROUND",   (1, 0), (-1, 0), CREAM),
            *treat_styles,                          # treat meal cells: amber tint
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",   (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID",         (0, 0), (-1, -1), 0.4, CREAM_DARK),
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

    # ── Section 4: Snack Swaps ─────────────────────────────────────────────

    story.append(PageBreak())
    story.append(Paragraph("Healthy Snack Swaps", s["section"]))
    story.append(_hr())
    story.append(Paragraph(
        "Replace common high-calorie snacks with these practitioner-approved alternatives:",
        s["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    for snack in snack_swaps[:5]:
        kcal = snack.get("calories", 0)
        prot = snack.get("protein_g", 0)
        serv = snack.get("serving_description", "")
        story.append(Paragraph(
            f"• <b>{snack['name_en']}</b>"
            + f" — {kcal} kcal · {prot}g protein · {serv}",
            s["body"]
        ))

    # ── Section 5: Supplement Recommendations ─────────────────────────────

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Supplement Recommendations", s["section"]))
    story.append(_hr())

    conditions = client.get("medical_conditions", [])
    supplements = [
        ("Vitamin D3 + K2", "Essential for South Asians — most are deficient. Take 1000–2000 IU D3 daily with a fatty meal."),
        ("Vitamin B12", "Critical if vegetarian/vegan or eating minimal red meat. 500 mcg daily or as advised."),
        ("Omega-3 (Fish Oil)", "2–3 g EPA+DHA daily. Anti-inflammatory, supports fat loss and heart health."),
        ("Magnesium Glycinate", "Supports sleep, stress, and blood sugar regulation. 200–400 mg before bed."),
    ]
    if "PCOS" in conditions:
        supplements.append(("Inositol (Myo + D-Chiro)", "4g myo-inositol + 400mg D-chiro-inositol daily. Evidence-based for PCOS insulin sensitivity."))
    if "Diabetes / pre-diabetes" in conditions:
        supplements.append(("Chromium Picolinate", "200–400 mcg daily. Supports blood glucose regulation. Consult your physician."))
    if "Hypothyroidism / thyroid" in conditions:
        supplements.append(("Selenium", "200 mcg daily. Supports thyroid hormone conversion. Avoid mega-dosing."))

    for name, detail in supplements:
        story.append(Paragraph(f"• <b>{name}</b> — {detail}", s["body"]))

    story.append(Paragraph(
        "<i>Note: Always consult a physician before starting supplements, especially if on medication.</i>",
        s["small"]
    ))

    # ── Section 6: Personal Fat Loss Rules ────────────────────────────────

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Your Personal Fat Loss Rules", s["section"]))
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
        story.append(Paragraph(f"• {r}", s["body"]))

    # ── Section 7: Realistic Timeline ─────────────────────────────────────

    goal = client.get("goal", "")
    weight = client.get("weight_kg", 0)

    if goal in ("Fat loss", "Mild fat loss") and weight:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Realistic Timeline", s["section"]))
        story.append(_hr())

        ideal_low  = assessment.get("ideal_weight_low", 0)
        kg_to_lose = max(0, round(weight - ideal_low, 1))
        weekly     = 0.5 if goal == "Fat loss" else 0.25
        weeks      = round(kg_to_lose / weekly) if weekly else 0
        months     = round(weeks / 4.3, 1)

        timeline_data = [
            ["Current Weight",         f"{weight} kg"],
            ["Target Weight (ideal)",  f"{ideal_low} kg"],
            ["Fat to Lose",            f"{kg_to_lose} kg"],
            ["Estimated Rate",         f"{weekly} kg/week (sustainable)"],
            ["Estimated Duration",     f"{weeks} weeks (~{months} months)"],
        ]
        story.append(_stat_table(timeline_data))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            "Sustainable fat loss is 0.25–0.5 kg per week. Faster loss risks muscle loss, "
            "metabolic adaptation, and nutrient deficiencies. Slow and steady wins this race.",
            s["small"]
        ))

    # ── Section 8: Exercise Plan ───────────────────────────────────────────

    story.append(PageBreak())
    story.append(Paragraph("Exercise Plan", s["section"]))
    story.append(_hr())

    fitness_level  = client.get("fitness_level") or "Moderate"
    exercise_notes = client.get("exercise_notes") or ""

    _rounds_map = {"Beginner": 1, "Moderate": 2, "Advanced": 3}
    _skips_map  = {"Beginner": 200, "Moderate": 350, "Advanced": 500}
    _steps_map  = {"Beginner": 7000, "Moderate": 8500, "Advanced": 10000}

    _rounds = _rounds_map.get(fitness_level, 2)
    _skips  = _skips_map.get(fitness_level, 350)
    _steps  = _steps_map.get(fitness_level, 8500)

    story.append(Paragraph(
        f"Fitness Level: <b>{fitness_level}</b> &nbsp;|&nbsp; "
        f"Circuit Rounds: <b>{_rounds}</b> &nbsp;|&nbsp; "
        f"Daily Skipping: <b>{_skips:,} skips</b> &nbsp;|&nbsp; "
        f"Step Target: <b>{_steps:,} steps/day</b>",
        s["body"]
    ))
    if exercise_notes:
        story.append(Paragraph(f"Notes: {exercise_notes}", s["small"]))

    story.append(Spacer(1, 0.3 * cm))

    # Daily movement targets
    story.append(Paragraph("Daily Movement", s["subsection"] if "subsection" in s else s["body"]))
    _move_rules = [
        "Daily skipping and step targets apply on all exercise days (5–6 days per week).",
        "After Breakfast — 10-minute stroll",
        "After Lunch — 15-minute stroll",
        "After Snack — 10-minute stroll",
        "After Dinner — 15–20 minute stroll",
        "For every 1 hour of sitting, move around for at least 1–2 minutes.",
    ]
    for mr in _move_rules:
        story.append(Paragraph(f"• {mr}", s["body"]))

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

    _GREEN_DARK  = HexColor("#2D6A4F")
    _GREEN_LIGHT = HexColor("#D8F3DC")
    _CREAM       = HexColor("#FBF7F2")

    for rnum in range(1, _rounds + 1):
        story.append(Spacer(1, 0.25 * cm))
        eff = _rep_scale[rnum][fitness_level]

        _circ_data = [[
            Paragraph(f"<b>{_round_names[rnum]}</b>", s["body"]),
            Paragraph("<b>Exercise</b>", s["body"]),
            Paragraph("<b>Reps / Duration</b>", s["body"]),
        ]]
        for i, (ex_name, reps_d) in enumerate(_circuit):
            reps_val = reps_d[eff]
            reps_str = reps_val if isinstance(reps_val, str) else f"{reps_val} reps"
            _circ_data.append([
                Paragraph("", s["small"]),
                Paragraph(ex_name, s["body"]),
                Paragraph(reps_str, s["body"]),
            ])

        _circ_table = Table(_circ_data, colWidths=[2.5 * cm, 10 * cm, 4 * cm])
        _circ_table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), _GREEN_DARK),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), BODY_FONT_BOLD),
            ("FONTNAME",    (0, 1), (-1, -1), BODY_FONT),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_CREAM, colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#E5D9CC")),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(_circ_table)

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Rest 60–90 seconds between rounds. Aim for 5–6 sessions per week. "
        "Combine with your daily walk targets for best results.",
        s["small"]
    ))

    # ── Section 9: Lifestyle Guidelines ───────────────────────────────────

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Lifestyle Guidelines", s["section"]))
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
        story.append(Paragraph(f"• {rule}", s["body"]))

    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("<b>Avoid completely:</b>", s["body"]))

    _client_diet = client.get("diet_type", "Non-vegetarian")
    _avoid = [
        "Maida and its products", "Fried food", "Oily food", "Sugar and sweets",
        "Fruit juices (fresh or packaged)", "Bakery items", "Pineapple", "Raw papaya",
        "Packaged and processed food", "Packet soup", "Cold drinks", "Alcohol", "Smoking / tobacco",
    ]
    if _client_diet not in ("Vegetarian", "Vegan", "Eggetarian"):
        _avoid.insert(7, "Processed meat")

    story.append(Paragraph("  ".join(f"• {a}" for a in _avoid), s["body"]))

    # Condition-specific notes
    _client_conds = client.get("medical_conditions", [])
    if "PCOS" in _client_conds:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "<b>PCOS note:</b> Consistency in sleep timing and stress management is especially "
            "important — cortisol spikes worsen hormonal imbalance.",
            s["body"]
        ))
    if any("diabetes" in c.lower() for c in _client_conds):
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "<b>Diabetes note:</b> Walk within 15 minutes of finishing a meal to help blunt "
            "post-meal glucose spikes. Never skip meals.",
            s["body"]
        ))
    if any("thyroid" in c.lower() for c in _client_conds):
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "<b>Thyroid note:</b> Take thyroid medication on an empty stomach 30–60 minutes "
            "before breakfast. Avoid large amounts of raw cruciferous vegetables.",
            s["body"]
        ))

    # ── Footer note ────────────────────────────────────────────────────────

    story.append(Spacer(1, 1 * cm))
    story.append(_hr())
    story.append(Paragraph(
        f"This report was prepared by Āhāra by Asha on {date.today().strftime('%d %B %Y')}. "
        "It is intended as personalised dietary guidance and does not replace medical advice. "
        "Please consult a physician for any medical conditions.",
        s["small"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
