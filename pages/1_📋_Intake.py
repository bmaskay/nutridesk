"""
1_Intake.py — New Client Intake Form (4 sections)
Section 1: Basic Stats  |  Section 2: Lifestyle
Section 3: Food Preferences  |  Section 4: Snack Habits
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
from utils.database import create_client, update_client, get_client, add_biomarkers, get_biomarkers
from utils.calculations import (
    full_assessment, calculate_age, calculate_bmi, bmi_category,
    ACTIVITY_MULTIPLIERS, GOAL_ADJUSTMENTS
)
from utils.header import render_header

render_header("New Client Intake")

st.markdown("""
<style>
  div[data-testid="stExpander"] { border: 1px solid #E5D9CC; border-radius: 10px; margin-bottom: 12px; }
  .legend-box { background:#F9F5EF; border:1px solid #E5D9CC; border-radius:8px;
                padding:8px 14px; font-size:0.78rem; margin-bottom:10px; }
  .macro-header { background:#D8F3DC; border-radius:8px; padding:8px 14px;
                  font-size:0.82rem; font-weight:700; color:#2D6A4F; margin-bottom:6px; }
  .explain-box { background:#F0F9FF; border-left:3px solid #38BDF8; border-radius:0 6px 6px 0;
                 padding:8px 12px; font-size:0.78rem; color:#0369A1; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ── Check if editing existing client ─────────────────────────────────────────

existing_client = None
edit_id = st.session_state.get("edit_client_id")
if edit_id:
    existing_client = get_client(edit_id)

# Pull most recent biomarker record for prefill (edit mode)
existing_bm: dict = {}
if existing_client:
    bm_records = get_biomarkers(existing_client["id"])
    if bm_records:
        existing_bm = bm_records[-1]  # most recent record

def prefill(key, default=""):
    if existing_client:
        return existing_client.get(key, default)
    return default

# ── None auto-deselect helpers ────────────────────────────────────────────────

def _none_deselect(key, none_label):
    """When a real option is added alongside None, remove None automatically.
    When None is newly selected alongside real options, clear the real options."""
    current = st.session_state.get(key, [])
    prev_key = key + "_prev"
    prev = st.session_state.get(prev_key, [])
    if none_label in current and len(current) > 1:
        if none_label in prev:
            # None was already there — user added a real option → drop None
            st.session_state[key] = [v for v in current if v != none_label]
        else:
            # None was just selected — user wants to clear all → keep only None
            st.session_state[key] = [none_label]
    st.session_state[prev_key] = list(st.session_state.get(key, current))

def _on_med_change():
    _none_deselect("_med_sel", "None reported")

def _on_allergy_change():
    _none_deselect("_allergy_sel", "None")

# ── Height sync helpers ───────────────────────────────────────────────────────

def _cm_from_ftin(ft, ins): return round(ft * 30.48 + ins * 2.54, 1)
def _ftin_from_cm(cm):
    t = cm / 2.54
    return int(t // 12), int(t % 12)

# Initialise height session state (keyed by client so edit doesn't bleed across)
_h_key = f"_hcm_{edit_id or 'new'}"
if _h_key not in st.session_state:
    _h0 = float(prefill("height_cm", 160.0) or 160.0)
    _ft0, _in0 = _ftin_from_cm(_h0)
    st.session_state[_h_key] = _h0
    st.session_state["_h_cm"]  = _h0
    st.session_state["_h_ft"]  = _ft0
    st.session_state["_h_in"]  = _in0

def _on_cm_change():
    cm = st.session_state["_h_cm"]
    st.session_state[_h_key] = cm
    ft, ins = _ftin_from_cm(cm)
    st.session_state["_h_ft"] = ft
    st.session_state["_h_in"] = ins

def _on_ftin_change():
    cm = _cm_from_ftin(st.session_state["_h_ft"], st.session_state["_h_in"])
    st.session_state[_h_key] = cm
    st.session_state["_h_cm"] = cm

# ── Header ────────────────────────────────────────────────────────────────────

if existing_client:
    st.markdown(f"## ✏️ Edit Client — {existing_client.get('name', '')}")
else:
    st.markdown("## 📋 New Client Intake")
st.markdown("Complete all four sections before generating a meal plan.")

# Field legend
st.markdown(
    "<div class='legend-box'>"
    "🔴 <b style='color:#DC2626'>Red label</b> = Required &nbsp;&nbsp;"
    "🔵 <b style='color:#2563EB'>Blue label</b> = Optional"
    "</div>",
    unsafe_allow_html=True
)

st.markdown("---")

# ── Progress steps ────────────────────────────────────────────────────────────

# Step bar — Section 1 shows ✅ once client name has been entered
_name_filled = bool(st.session_state.get("intake_name", "").strip())
_steps = [
    ("1", "Basic Stats",  _name_filled),
    ("2", "Lifestyle",    False),
    ("3", "Food Prefs",   False),
    ("4", "Snacks",       False),
    ("5", "Exercise",     False),
    ("6", "Biomarkers",   False),
]
_step_cols = st.columns(6)
for _col, (_num, _label, _done) in zip(_step_cols, _steps):
    _bg   = "#2D6A4F" if _done else "#D8F3DC"
    _fg   = "white"   if _done else "#2D6A4F"
    _icon = "✅" if _done else _num
    _col.markdown(
        f"<div style='background:{_bg};color:{_fg};padding:7px 4px;border-radius:8px;"
        f"text-align:center;font-size:0.78rem;font-weight:600'>"
        f"{_icon} · {_label}</div>",
        unsafe_allow_html=True,
    )
st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Basic Stats
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📊 Section 1 — Basic Stats", expanded=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        name = st.text_input(
            ":red[Full Name ✱]", value=prefill("name"), placeholder="e.g. Priya Sharma",
            key="intake_name"
        )
        gender = st.selectbox(
            ":red[Gender ✱]", ["Female", "Male", "Other"],
            index=["Female", "Male", "Other"].index(prefill("gender", "Female"))
        )
        dob_val = prefill("dob")
        try:
            dob_default = date.fromisoformat(dob_val) if dob_val else date(1990, 1, 1)
        except Exception:
            dob_default = date(1990, 1, 1)
        dob = st.date_input(
            ":red[Date of Birth ✱]", value=dob_default,
            min_value=date(1940, 1, 1), max_value=date.today()
        )

    with c2:
        # ── Height: cm primary, ft/in bidirectional sync ──────────────────────
        h_cm_col, h_ft_col, h_in_col = st.columns([1.3, 0.7, 0.7])
        with h_cm_col:
            st.number_input(
                ":red[Height (cm) ✱]",
                min_value=100.0, max_value=220.0,
                step=0.5, format="%.1f",
                key="_h_cm", on_change=_on_cm_change
            )
        with h_ft_col:
            st.number_input("ft", min_value=3, max_value=7, step=1,
                            key="_h_ft", on_change=_on_ftin_change)
        with h_in_col:
            st.number_input("in", min_value=0, max_value=11, step=1,
                            key="_h_in", on_change=_on_ftin_change)
        height_cm = st.session_state[_h_key]

        weight_kg = st.number_input(
            ":red[Current Weight (kg) ✱]",
            min_value=30.0, max_value=250.0,
            value=float(prefill("weight_kg", 65.0) or 65.0),
            step=0.1, format="%.1f"
        )
        phone = st.text_input(
            ":blue[Phone]", value=prefill("phone"), placeholder="+977 98XXXXXXXX"
        )

    with c3:
        email = st.text_input(
            ":blue[Email]", value=prefill("email"), placeholder="client@example.com"
        )
        goal = st.selectbox(
            ":red[Primary Goal ✱]",
            list(GOAL_ADJUSTMENTS.keys()),
            index=list(GOAL_ADJUSTMENTS.keys()).index(prefill("goal", "Fat loss"))
            if prefill("goal") in GOAL_ADJUSTMENTS else 0
        )

    # ── Live BMI preview ───────────────────────────────────────────────────
    age_preview = calculate_age(str(dob))
    if height_cm and weight_kg:
        bmi_p     = calculate_bmi(weight_kg, height_cm)
        bmi_cat_p = bmi_category(bmi_p)
        bmi_color = "#2D6A4F" if bmi_p < 23 else "#D97706" if bmi_p < 27.5 else "#DC2626"
        st.markdown(
            f"<div style='background:#F9F5EF;border:1px solid #E5D9CC;border-radius:8px;"
            f"padding:10px 16px;display:inline-block;margin-top:8px'>"
            f"<b>BMI:</b> <span style='color:{bmi_color};font-size:1.1rem'><b>{bmi_p}</b></span>"
            f"&nbsp;·&nbsp; {bmi_cat_p} &nbsp;·&nbsp; Age: {age_preview} yrs</div>",
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Lifestyle
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("🌙 Section 2 — Lifestyle", expanded=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        activity_level = st.selectbox(
            ":red[Activity Level ✱]",
            list(ACTIVITY_MULTIPLIERS.keys()),
            index=list(ACTIVITY_MULTIPLIERS.keys()).index(
                prefill("activity_level", "Lightly active (light exercise 1–3 days/wk)")
            ) if prefill("activity_level") in ACTIVITY_MULTIPLIERS else 1
        )
        occupation = st.text_input(
            ":blue[Occupation]", value=prefill("occupation"),
            placeholder="e.g. Office worker, Teacher, Student"
        )

    with c2:
        sleep_hrs = st.slider(
            ":blue[Average Sleep (hrs/night)]", 4.0, 10.0,
            float(prefill("sleep_hrs", 7.0) or 7.0), step=0.5
        )
        stress_level = st.selectbox(
            ":blue[Stress Level]",
            ["Low", "Moderate", "High", "Very High"],
            index=["Low", "Moderate", "High", "Very High"].index(
                prefill("stress_level", "Moderate")
            ) if prefill("stress_level") in ["Low", "Moderate", "High", "Very High"] else 1
        )

    with c3:
        water_intake = st.number_input(
            ":blue[Current Water Intake (L/day)]", 0.5, 6.0,
            float(prefill("water_intake_L", 1.5) or 1.5), step=0.25
        )

        # Medical conditions with "None reported" option
        MEDICAL_CONDITIONS_LIST = [
            "None reported",
            "Diabetes / pre-diabetes",
            "PCOS",
            "Hypothyroidism / thyroid",
            "Hypertension",
            "High cholesterol",
            "IBS / digestive issues",
            "Anaemia / iron deficiency",
            "Kidney disease",
            "Fatty liver",
        ]
        med_default_raw = prefill("medical_conditions", [])
        if not med_default_raw:
            med_default_raw = ["None reported"]
        if "_med_sel" not in st.session_state:
            st.session_state["_med_sel"] = [m for m in med_default_raw if m in MEDICAL_CONDITIONS_LIST]
            st.session_state["_med_sel_prev"] = list(st.session_state["_med_sel"])
        medical_conditions_raw = st.multiselect(
            ":blue[Medical Conditions]",
            MEDICAL_CONDITIONS_LIST,
            key="_med_sel",
            on_change=_on_med_change,
        )
        # Strip "None reported" before saving
        medical_conditions = [m for m in medical_conditions_raw if m != "None reported"]

    # Medical details (optional free text)
    med_details = st.text_area(
        ":blue[Medical Condition Details]",
        value=prefill("notes", ""),
        placeholder="e.g. HbA1c 6.2, on Metformin 500mg; irregular cycles for 8 months...",
        height=70,
        help="Optional: add detail about diagnoses, medications, or lab results here."
    )

    # ── Menstrual cycle awareness (female / other clients only) ───────────────
    cycle_status = prefill("cycle_status", "")
    if gender in ("Female", "Other"):
        CYCLE_OPTIONS = [
            "—",
            "Regular (21–35 day cycle)",
            "Irregular / unpredictable",
            "Post-menopausal",
            "On oral contraceptives / hormonal therapy",
            "Currently pregnant / postpartum",
            "Prefer not to say",
        ]
        _cycle_default = cycle_status if cycle_status in CYCLE_OPTIONS else "—"
        cycle_status = st.selectbox(
            ":blue[Menstrual Cycle Status]",
            CYCLE_OPTIONS,
            index=CYCLE_OPTIONS.index(_cycle_default),
            help="Optional — helps flag that weight fluctuations around cycle days are normal.",
        )
        if cycle_status == "—":
            cycle_status = ""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Food Preferences
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("🥗 Section 3 — Food Preferences", expanded=True):
    c1, c2 = st.columns(2)

    with c1:
        diet_type = st.selectbox(
            ":red[Diet Type ✱]",
            ["Non-vegetarian", "Vegetarian", "Eggetarian", "Vegan"],
            index=["Non-vegetarian", "Vegetarian", "Eggetarian", "Vegan"].index(
                prefill("diet_type", "Non-vegetarian")
            ) if prefill("diet_type") in ["Non-vegetarian", "Vegetarian", "Eggetarian", "Vegan"] else 0
        )
        CUISINES = ["Nepali", "Newari", "South Asian", "Pan-Asian",
                    "Chinese", "International", "Continental"]
        cuisine_default = prefill("cuisine_pref", ["Nepali"])
        cuisine_pref = st.multiselect(
            ":blue[Preferred Cuisines]",
            CUISINES,
            default=[c for c in cuisine_default if c in CUISINES]
        )
        meal_frequency = st.selectbox(
            ":blue[Meals per Day]", [2, 3, 4, 5],
            index=[2, 3, 4, 5].index(int(prefill("meal_frequency", 3) or 3))
        )

        # When fewer than 3 meals, let the practitioner choose which slots to use
        ALL_SLOTS = ["Breakfast", "Lunch", "Dinner"]
        _slot_raw = prefill("meal_slots", ALL_SLOTS)
        if not _slot_raw:
            _slot_raw = ALL_SLOTS
        # Clamp saved default to the expected number of slots so Streamlit never
        # receives more default items than the multiselect allows
        if meal_frequency == 2:
            _slot_default = [m for m in _slot_raw if m in ALL_SLOTS][:2]
            if len(_slot_default) < 2:
                _slot_default = ["Lunch", "Dinner"]   # sensible fallback
            meal_slots = st.multiselect(
                ":blue[Which 2 meals?]",
                ALL_SLOTS,
                default=_slot_default,
                help="Choose exactly 2 meal slots for this client's daily plan."
            )
            if len(meal_slots) != 2:
                st.caption("⚠ Select exactly 2 meals.")
                meal_slots = _slot_default   # keep old value until corrected
        elif meal_frequency == 1:
            _valid = [m for m in _slot_raw if m in ALL_SLOTS]
            _single = _valid[0] if _valid else "Lunch"
            _pick = st.selectbox(
                ":blue[Which meal?]", ALL_SLOTS,
                index=ALL_SLOTS.index(_single),
                help="The one main meal this client eats per day."
            )
            meal_slots = [_pick]
        else:
            meal_slots = ALL_SLOTS  # 3+ meals always uses all three

    with c2:
        # Allergies with "None" option
        ALLERGIES_LIST = ["None", "Gluten", "Dairy / Lactose", "Eggs",
                          "Nuts", "Shellfish", "Soy", "Fish", "Sesame"]
        allergy_default_raw = prefill("allergies", [])
        if not allergy_default_raw:
            allergy_default_raw = ["None"]
        if "_allergy_sel" not in st.session_state:
            st.session_state["_allergy_sel"] = [a for a in allergy_default_raw if a in ALLERGIES_LIST]
            st.session_state["_allergy_sel_prev"] = list(st.session_state["_allergy_sel"])
        allergies_raw = st.multiselect(
            ":blue[Food Allergies / Intolerances]",
            ALLERGIES_LIST,
            key="_allergy_sel",
            on_change=_on_allergy_change,
        )
        allergies = [a for a in allergies_raw if a != "None"]

        dislikes = st.text_input(
            ":blue[Food Dislikes (comma-separated)]",
            value=", ".join(prefill("dislikes", [])) if isinstance(prefill("dislikes", []), list)
            else prefill("dislikes", ""),
            placeholder="e.g. bitter gourd, fish sauce, mushroom"
        )

    st.markdown(":blue[**Vegetable Preferences**]")
    VEGS = ["Spinach", "Cauliflower", "Potato", "Pumpkin", "Radish", "Mushroom",
            "Beans", "Peas", "Broccoli", "Cabbage", "Carrot", "Bitter gourd",
            "Bottle gourd", "Eggplant", "Tomato", "Cucumber", "Yam"]
    veg_default = prefill("veg_choices", [])
    veg_choices = st.multiselect(
        "Vegetables", VEGS,
        default=[v for v in veg_default if v in VEGS],
        label_visibility="collapsed"
    )

    if diet_type == "Non-vegetarian":
        st.markdown(":blue[**Meat / Protein Preferences**]")
        MEATS = ["Chicken", "Buff (Buffalo)", "Mutton / Goat", "Fish",
                 "Prawns", "Eggs", "Pork", "Duck"]
        meat_default = prefill("meat_choices", [])
        meat_choices = st.multiselect(
            "Meats", MEATS,
            default=[m for m in meat_default if m in MEATS],
            label_visibility="collapsed"
        )
    else:
        meat_choices = []

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Snack Habits
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("🫘 Section 4 — Snack Habits", expanded=True):
    c1, c2 = st.columns(2)

    with c1:
        snack_frequency = st.selectbox(
            ":blue[Snack Frequency per Day]", [0, 1, 2, 3],
            index=int(prefill("snack_frequency", 1) or 1)
        )

    with c2:
        SNACK_TYPES = ["Biscuits / crackers", "Chips / namkeen", "Fruits",
                       "Nuts / seeds", "Yoghurt / curd", "Bread / roti",
                       "Sweets / mithai", "Tea / coffee with snacks",
                       "Protein bars", "Nothing — I skip snacks"]
        snack_default = prefill("snack_types", [])
        snack_types = st.multiselect(
            ":blue[Usual Snack Types]",
            SNACK_TYPES,
            default=[s for s in snack_default if s in SNACK_TYPES]
        )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: Exercise & Fitness
# ─────────────────────────────────────────────────────────────────────────────

fitness_level  = "Moderate"
exercise_notes = ""

with st.expander("💪 Section 5 — Exercise & Fitness", expanded=False):
    st.markdown(
        "<div class='legend-box'>"
        "Used to tailor the exercise circuit intensity and lifestyle plan shown "
        "in the <b>💪 Exercise Plan</b> page and included in the PDF report."
        "</div>",
        unsafe_allow_html=True,
    )

    fitness_level = st.selectbox(
        "Fitness Level",
        ["Beginner", "Moderate", "Advanced"],
        index=["Beginner", "Moderate", "Advanced"].index(
            prefill("fitness_level", "Moderate") or "Moderate"
        ),
        help="Beginner = 1 round · Moderate = 2 rounds · Advanced = all 3 rounds of the circuit",
    )

    exercise_notes = st.text_area(
        "Exercise Limitations / Notes :blue[(optional)]",
        value=prefill("exercise_notes", ""),
        placeholder="e.g. knee pain — avoid high-impact; prefers morning workouts",
        height=80,
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Baseline Biomarkers (optional)
# ─────────────────────────────────────────────────────────────────────────────

# Initialize biomarker variables before expander (Streamlit state safety)
bm_fasting_glucose = 0.0
bm_hba1c = 0.0
bm_cholesterol = 0.0
bm_hdl = 0.0
bm_ldl = 0.0
bm_triglycerides = 0.0
bm_tsh = 0.0
bm_vitamin_d = 0.0
bm_b12 = 0.0
bm_ferritin = 0.0
bm_notes = ""

with st.expander("🩺 Section 6 — Baseline Biomarkers (optional)", expanded=False):
    st.markdown(
        "<div class='legend-box'>"
        "Record baseline blood work if available now. These will appear in the "
        "<b>📈 Progress</b> tracker and can be updated at any future visit. "
        "Leave a field at <b>0</b> to skip it."
        "</div>",
        unsafe_allow_html=True,
    )

    bm_c1, bm_c2, bm_c3 = st.columns(3)

    with bm_c1:
        st.markdown(":blue[**Blood Sugar**]")
        bm_fasting_glucose = st.number_input(
            "Fasting Glucose (mmol/L)", min_value=0.0, max_value=30.0,
            value=float(existing_bm.get("fasting_glucose") or 0.0),
            step=0.1, format="%.1f"
        )
        bm_hba1c = st.number_input(
            "HbA1c (%)", min_value=0.0, max_value=20.0,
            value=float(existing_bm.get("hba1c") or 0.0),
            step=0.1, format="%.1f"
        )
        st.markdown(":blue[**Thyroid**]")
        bm_tsh = st.number_input(
            "TSH (mIU/L)", min_value=0.0, max_value=20.0,
            value=float(existing_bm.get("tsh") or 0.0),
            step=0.01, format="%.2f"
        )

    with bm_c2:
        st.markdown(":blue[**Lipid Panel**]")
        bm_cholesterol = st.number_input(
            "Total Cholesterol (mmol/L)", min_value=0.0, max_value=15.0,
            value=float(existing_bm.get("total_cholesterol") or 0.0),
            step=0.1, format="%.1f"
        )
        bm_hdl = st.number_input(
            "HDL (mmol/L)", min_value=0.0, max_value=5.0,
            value=float(existing_bm.get("hdl") or 0.0),
            step=0.1, format="%.1f"
        )
        bm_ldl = st.number_input(
            "LDL (mmol/L)", min_value=0.0, max_value=10.0,
            value=float(existing_bm.get("ldl") or 0.0),
            step=0.1, format="%.1f"
        )
        bm_triglycerides = st.number_input(
            "Triglycerides (mmol/L)", min_value=0.0, max_value=15.0,
            value=float(existing_bm.get("triglycerides") or 0.0),
            step=0.1, format="%.1f"
        )

    with bm_c3:
        st.markdown(":blue[**Micronutrients**]")
        bm_vitamin_d = st.number_input(
            "Vitamin D (nmol/L)", min_value=0.0, max_value=300.0,
            value=float(existing_bm.get("vitamin_d") or 0.0),
            step=1.0, format="%.0f"
        )
        bm_b12 = st.number_input(
            "B12 (pmol/L)", min_value=0.0, max_value=1500.0,
            value=float(existing_bm.get("b12") or 0.0),
            step=1.0, format="%.0f"
        )
        bm_ferritin = st.number_input(
            "Ferritin (μg/L)", min_value=0.0, max_value=500.0,
            value=float(existing_bm.get("ferritin") or 0.0),
            step=1.0, format="%.0f"
        )

    bm_notes = st.text_input(
        ":blue[Lab / Notes]",
        value=existing_bm.get("notes", ""),
        placeholder="e.g. Fasting 8 hrs · XYZ Diagnostics · 2026-03-15"
    )

# ── Save ─────────────────────────────────────────────────────────────────────

st.markdown("---")
col_save, col_cancel = st.columns([1, 3])

with col_save:
    save_label = "💾 Update Client" if existing_client else "💾 Save Client"
    save_clicked = st.button(save_label, width="stretch", type="primary")

with col_cancel:
    if existing_client and st.button("✖ Cancel"):
        st.session_state.pop("edit_client_id", None)
        st.switch_page("pages/3_👥_Clients.py")

if save_clicked:
    if not name:
        st.error("Please enter the client's name.")
    else:
        dislikes_list = [d.strip() for d in dislikes.split(",") if d.strip()]

        client_data = {
            "name":            name,
            "email":           email,
            "phone":           phone,
            "dob":             str(dob),
            "gender":          gender,
            "height_cm":       height_cm,
            "weight_kg":       weight_kg,
            "goal":            goal,
            "activity_level":  activity_level,
            "occupation":      occupation,
            "sleep_hrs":       sleep_hrs,
            "stress_level":    stress_level,
            "water_intake_L":  water_intake,
            "diet_type":       diet_type,
            "cuisine_pref":    cuisine_pref,
            "allergies":       allergies,
            "dislikes":        dislikes_list,
            "meal_frequency":  meal_frequency,
            "meal_slots":      meal_slots,
            "veg_choices":     veg_choices,
            "meat_choices":    meat_choices,
            "snack_frequency": snack_frequency,
            "snack_types":     snack_types,
            "medical_conditions": medical_conditions,
            "notes":           med_details,
            "fitness_level":   fitness_level,
            "exercise_notes":  exercise_notes,
            "cycle_status":    cycle_status if gender in ("Female", "Other") else "",
        }

        if existing_client:
            update_client(edit_id, client_data)
            saved_client_id = edit_id
            st.success(f"✅ {name}'s profile updated!")
            st.session_state.pop("edit_client_id", None)
        else:
            new_id = create_client(client_data)
            saved_client_id = new_id
            st.success(f"✅ {name} saved! (Client ID: {new_id})")
            st.session_state["active_client_id"] = new_id
            # Reset height state for next new client
            st.session_state.pop(f"_hcm_new", None)

        # ── Save baseline biomarkers if any non-zero values entered ────────────
        bm_payload = {}
        for field, val in [
            ("fasting_glucose", bm_fasting_glucose), ("hba1c", bm_hba1c),
            ("total_cholesterol", bm_cholesterol),   ("hdl", bm_hdl),
            ("ldl", bm_ldl), ("triglycerides", bm_triglycerides),
            ("tsh", bm_tsh), ("vitamin_d", bm_vitamin_d),
            ("b12", bm_b12), ("ferritin", bm_ferritin),
        ]:
            if val > 0:
                bm_payload[field] = val
        if bm_payload:
            if bm_notes:
                bm_payload["notes"] = bm_notes
            add_biomarkers(saved_client_id, bm_payload)

        # ── Assessment preview ─────────────────────────────────────────────
        client_data["dob"] = str(dob)
        assessment = full_assessment(client_data)

        st.markdown("---")
        st.markdown("### 📊 Assessment Summary")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("BMI", f"{assessment['bmi']}", assessment['bmi_category'])
        m4.metric("Calorie Target", f"{assessment['target_calories']} kcal")
        m5.metric("Daily Water", f"{assessment['hydration_L']} L")

        # BMR with explanation
        with m2:
            st.metric("BMR", f"{assessment['bmr']} kcal")
        with m3:
            st.metric("TDEE", f"{assessment['tdee']} kcal")

        # ── Plain-language interpretation ──────────────────────────────────
        _adj   = assessment["goal_adjustment"]
        _goal  = client_data.get("goal", "")
        _wt    = client_data.get("weight_kg", 0)
        _ideal_low  = assessment["ideal_weight_low"]
        _ideal_high = assessment["ideal_weight_high"]
        _weekly_rate = 0.5 if _goal == "Fat loss" else 0.25 if _goal == "Mild fat loss" else 0
        _kg_to_target = max(round(_wt - _ideal_high, 1), 0) if _wt > _ideal_high else 0

        if _adj < 0:
            _goal_sentence = (
                f"To reach their goal, {name} needs to eat roughly "
                f"<b>{assessment['target_calories']} kcal/day</b> — that's "
                f"{abs(_adj)} kcal below their daily burn. At this deficit, expect "
                f"<b>~{_weekly_rate} kg/week</b> of loss."
            )
            if _kg_to_target > 0:
                _weeks_est = round(_kg_to_target / _weekly_rate)
                _goal_sentence += (
                    f" To reach the healthy weight range of {_ideal_low}–{_ideal_high} kg "
                    f"would take roughly <b>{_weeks_est} weeks</b>."
                )
        elif _adj > 0:
            _goal_sentence = (
                f"{name}'s target is <b>{assessment['target_calories']} kcal/day</b> — "
                f"{_adj} kcal above their daily burn to support muscle gain."
            )
        else:
            _goal_sentence = (
                f"{name}'s target of <b>{assessment['target_calories']} kcal/day</b> "
                f"matches their daily burn — designed to maintain current weight."
            )

        st.markdown(
            "<div class='explain-box'>"
            f"{_goal_sentence}"
            f"<br><br><span style='opacity:0.8'><b>BMR</b> (Basal Metabolic Rate) — "
            f"{assessment['bmr']} kcal, the calories the body burns at complete rest. "
            f"<b>TDEE</b> — {assessment['tdee']} kcal, BMR scaled by activity level.</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # ── Red flag / referral prompt ─────────────────────────────────────
        _bmi       = assessment["bmi"]
        _conditions = [c for c in client_data.get("medical_conditions", []) if c]
        _bmi_flag  = _bmi >= 32.5
        _multi_cond = len(_conditions) >= 2
        if _bmi_flag or _multi_cond:
            _flag_reasons = []
            if _bmi >= 32.5:
                _flag_reasons.append(f"BMI {_bmi} (Asian obese range)")
            if _multi_cond:
                _flag_reasons.append(f"{len(_conditions)} concurrent medical conditions")
            st.warning(
                "⚠️ **Clinical note:** " + " · ".join(_flag_reasons) + ". "
                "Consider confirming GP clearance before starting a significant calorie "
                "restriction. Nutritional intervention is appropriate alongside — not instead "
                "of — medical management.",
                icon=None,
            )

        # ── Kidney disease advisory ────────────────────────────────────────
        if "Kidney disease" in _conditions:
            st.error(
                "🩺 **Kidney disease flagged:** Protein targets and potassium/phosphorus "
                "intake require specialist dietitian review. Do not apply standard macro "
                "splits — please refer to a renal dietitian or nephrologist."
            )

        # ── Cycle-aware note ───────────────────────────────────────────────
        _cycle = client_data.get("cycle_status", "")
        if _cycle in ("Irregular / unpredictable", "On oral contraceptives / hormonal therapy"):
            st.info(
                "🔵 **Cycle note:** Weight fluctuations of 1–3 kg are normal across the "
                "menstrual cycle due to water retention, particularly in the luteal phase "
                "(week before a period). Advise the client to weigh in at the same phase "
                "each month for a fair comparison — day 1–3 of the cycle is usually the "
                "most stable window."
            )
        elif _cycle == "Post-menopausal":
            st.info(
                "🔵 **Post-menopausal:** Fat redistribution to the abdomen is common after "
                "menopause due to lower oestrogen. Waist circumference is a more meaningful "
                "marker than BMI alone. Protein targets are especially important to preserve "
                "muscle mass."
            )
        elif _cycle == "Currently pregnant / postpartum":
            st.warning(
                "⚠️ **Pregnant / postpartum:** Standard calorie restriction is not appropriate. "
                "Please refer to current pregnancy nutrition guidelines or an obstetric dietitian."
            )

        # Suggested Macros
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='macro-header'>📐 Suggested Daily Macros — targets calculated from your calorie goal</div>",
            unsafe_allow_html=True
        )
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Protein", f"{assessment['protein_g']} g",
                   help="Prioritised higher during fat loss to preserve muscle mass.")
        mc2.metric("Carbohydrates", f"{assessment['carbs_g']} g",
                   help="Primary energy source. Includes rice, roti, dal, fruits, and vegetables.")
        mc3.metric("Fat", f"{assessment['fat_g']} g",
                   help="Essential for hormones, absorption of fat-soluble vitamins, and satiety.")

        st.info(
            f"💡 Ideal weight range for {name}: "
            f"**{assessment['ideal_weight_low']}–{assessment['ideal_weight_high']} kg** "
            f"(based on healthy BMI 18.5–22.9 for Asian body types)"
        )

        if st.button("➡️ Generate Meal Plan Now"):
            st.switch_page("pages/2_🍽️_Meal_Plan.py")
