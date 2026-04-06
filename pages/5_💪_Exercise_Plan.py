"""
5_Exercise_Plan.py — Exercise Plan & Lifestyle Guidelines for NutriDesk

Shows a 3-round bodyweight circuit adapted to the client's fitness level,
daily movement targets, post-meal walk schedule, and lifestyle rules
aligned with their meal plan.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import get_all_clients, get_client
from utils.header import render_header

render_header("Exercise Plan")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .ex-card  { background: #FBF7F2; border: 1px solid #E5D9CC; border-radius: 10px;
              padding: 14px 16px; margin-bottom: 10px; }
  .ex-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
              letter-spacing: 1px; color: #40916C; margin-bottom: 4px; }
  .ex-title { font-size: 1.0rem; font-weight: 700; color: #1A1A1A; }
  .ex-sub   { font-size: 0.84rem; color: #4B5563; }
  .round-header { background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%);
                  color: white; border-radius: 8px; padding: 8px 14px;
                  font-weight: 700; font-size: 0.9rem; margin-bottom: 8px; }
  .lifestyle-item { padding: 6px 0; border-bottom: 1px solid #F0E8DC;
                    font-size: 0.88rem; color: #374151; }
  .lifestyle-item:last-child { border-bottom: none; }
  .highlight-rule { background: #D8F3DC; border-radius: 6px; padding: 4px 10px;
                    color: #1B4332; font-weight: 600; font-size: 0.88rem; }
  .warn-rule { background: #FEF9C3; border-radius: 6px; padding: 4px 10px;
               color: #713F12; font-size: 0.88rem; }
  .avoid-tag { background: #FEE2E2; color: #991B1B; border-radius: 4px;
               padding: 2px 8px; font-size: 0.78rem; font-weight: 600;
               display: inline-block; margin: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Circuit data ──────────────────────────────────────────────────────────────
CIRCUIT = [
    ("Jumping Jacks",                  {"Beginner": 30,  "Moderate": 40,  "Advanced": 50}),
    ("Crunches",                       {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Leg Raise",                      {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Elbow-to-Knee Oblique Crunches", {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Russian Twist (2L bottle)",      {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Leg Straight Hold",              {"Beginner": "45 sec", "Moderate": "45 sec", "Advanced": "1 min"}),
    ("Heel Touch",                     {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Cross Leg",                      {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Bicycle Crunches",               {"Beginner":  8,  "Moderate": 10,  "Advanced": 12}),
    ("Plank",                          {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}),
]

ROUNDS_BY_LEVEL = {"Beginner": 1, "Moderate": 2, "Advanced": 3}
SKIPS_BY_LEVEL  = {"Beginner": 200, "Moderate": 350, "Advanced": 500}
STEPS_BY_LEVEL  = {"Beginner": 7000, "Moderate": 8500, "Advanced": 10000}

# Post-meal strolls (from the balanced meal plan)
POST_MEAL_WALKS = [
    ("After Breakfast", "10 mins"),
    ("After Lunch",     "15 mins"),
    ("After Snack",     "10 mins"),
    ("After Dinner",    "15–20 mins"),
]

# Lifestyle rules — tagged by relevance
LIFESTYLE_RULES = [
    {"icon": "💧", "text": "Drink at least 2–3 litres of water a day",
     "tag": "always", "highlight": True},
    {"icon": "🥗", "text": "Eat slowly and chew your food very well (at least 20–30 times per bite)",
     "tag": "always", "highlight": False},
    {"icon": "⏰", "text": "Stick to your meal timings — consistent eating windows support metabolism",
     "tag": "always", "highlight": False},
    {"icon": "🌅", "text": "Expose yourself to sunlight at sunrise and sunset — supports Vitamin D and circadian rhythm",
     "tag": "always", "highlight": False},
    {"icon": "😴", "text": "At least 6–8 hours of sleep is mandatory",
     "tag": "always", "highlight": True},
    {"icon": "📱", "text": "No gadgets 30 minutes before going to sleep",
     "tag": "always", "highlight": False},
    {"icon": "🌙", "text": "Finish dinner 2–3 hours before bedtime",
     "tag": "always", "highlight": False},
    {"icon": "⏱️", "text": "Fixed sleeping and waking time every day — even on weekends",
     "tag": "always", "highlight": False},
    {"icon": "🪑", "text": "For every 1 hour of sitting, move around for at least 1–2 minutes",
     "tag": "always", "highlight": False},
    {"icon": "🛢️", "text": "Use only 3–4 tsp of cold-pressed mustard oil, olive oil, or ghee per day",
     "tag": "always", "highlight": False},
]

AVOID_ITEMS = [
    "Maida & its products", "Fried food", "Oily food", "Sugar & sweets",
    "Fruit juices (fresh or packaged)", "Bakery items", "Pineapple", "Raw papaya",
    "Processed meat", "Packaged / instant food", "Packet soup", "Cold drinks",
    "Alcohol", "Smoking / tobacco",
]

# ── Client selector ───────────────────────────────────────────────────────────
st.markdown("## 💪 Exercise Plan")
st.markdown("---")

clients = get_all_clients()
if not clients:
    st.warning("No clients found. Please add a client first via 📋 New Client.")
    if st.button("➕ Add Client"):
        st.switch_page("pages/1_📋_Intake.py")
    st.stop()

client_options = {f"{c['name']} (ID {c['id']})": c["id"] for c in clients}
default_client = st.session_state.get("active_client_id")
default_key = next(
    (k for k, v in client_options.items() if v == default_client),
    list(client_options.keys())[0]
)

selected_label = st.selectbox("Select Client", list(client_options.keys()),
                               index=list(client_options.keys()).index(default_key))
client_id = client_options[selected_label]
client    = get_client(client_id)

fitness_level  = client.get("fitness_level") or "Moderate"
exercise_notes = client.get("exercise_notes") or ""
diet_type      = client.get("diet_type", "Non-vegetarian")
conditions     = client.get("medical_conditions", [])
rounds         = ROUNDS_BY_LEVEL.get(fitness_level, 2)
skips          = SKIPS_BY_LEVEL.get(fitness_level, 350)
steps          = STEPS_BY_LEVEL.get(fitness_level, 8500)

# ── Daily targets bar ─────────────────────────────────────────────────────────
st.markdown(
    f"<div style='background:#D8F3DC;border:1px solid #B7E4C7;border-radius:10px;"
    f"padding:12px 16px;margin-bottom:16px;'>"
    f"<b>{client['name']}</b> &nbsp;·&nbsp; "
    f"Fitness Level: <b>{fitness_level}</b> &nbsp;·&nbsp; "
    f"Rounds: <b>{rounds}</b> &nbsp;·&nbsp; "
    f"Daily Skipping: <b>{skips:,}</b> &nbsp;·&nbsp; "
    f"Step Target: <b>{steps:,} steps/day</b>"
    f"</div>",
    unsafe_allow_html=True,
)

if exercise_notes:
    st.info(f"📝 Notes: {exercise_notes}")

# ── Daily movement targets ────────────────────────────────────────────────────
with st.expander("🏃 Daily Movement Targets", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div class='ex-card'>"
            f"<div class='ex-label'>Skipping</div>"
            f"<div class='ex-title'>{skips:,} skips</div>"
            f"<div class='ex-sub'>Daily, before or after circuit</div>"
            f"</div>", unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div class='ex-card'>"
            f"<div class='ex-label'>Steps</div>"
            f"<div class='ex-title'>{steps:,} steps</div>"
            f"<div class='ex-sub'>Target per day including walks</div>"
            f"</div>", unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<div class='ex-card'>"
            f"<div class='ex-label'>Weekly frequency</div>"
            f"<div class='ex-title'>5–6 days/week</div>"
            f"<div class='ex-sub'>Minimum 30 min exercise per session</div>"
            f"</div>", unsafe_allow_html=True
        )

    st.markdown("**🚶 Post-Meal Walks (follow after every meal):**")
    walk_cols = st.columns(4)
    for i, (meal, duration) in enumerate(POST_MEAL_WALKS):
        with walk_cols[i]:
            st.markdown(
                f"<div class='ex-card' style='text-align:center'>"
                f"<div class='ex-label'>{meal}</div>"
                f"<div class='ex-title'>{duration}</div>"
                f"</div>", unsafe_allow_html=True
            )

# ── Circuit ───────────────────────────────────────────────────────────────────
with st.expander("🔄 Bodyweight Circuit", expanded=True):
    st.markdown(
        f"Complete **{rounds} round{'s' if rounds > 1 else ''}** of the circuit below. "
        f"Rest 60–90 seconds between rounds."
    )

    for round_num in range(1, rounds + 1):
        round_labels = {1: "Round 1 — Full Power", 2: "Round 2 — Stay Strong", 3: "Round 3 — Finish Hard"}
        st.markdown(
            f"<div class='round-header'>🔁 {round_labels.get(round_num, f'Round {round_num}')}</div>",
            unsafe_allow_html=True
        )

        # Reps decrease each round: R1 = Advanced reps, R2 = Moderate, R3 = Beginner
        round_level_map = {1: fitness_level, 2: "Beginner" if fitness_level == "Advanced" else "Beginner",
                           3: "Beginner"}
        # Simpler: reps scale down by round
        rep_scale = {1: {"Beginner": "Beginner", "Moderate": "Moderate", "Advanced": "Advanced"},
                     2: {"Beginner": "Beginner", "Moderate": "Beginner",  "Advanced": "Moderate"},
                     3: {"Beginner": "Beginner", "Moderate": "Beginner",  "Advanced": "Beginner"}}

        effective_level = rep_scale[round_num][fitness_level]

        cols = st.columns(2)
        for idx, (exercise, reps_dict) in enumerate(CIRCUIT):
            reps = reps_dict[effective_level]
            reps_str = str(reps) if isinstance(reps, str) else f"{reps} reps"
            with cols[idx % 2]:
                st.markdown(
                    f"<div class='ex-card'>"
                    f"<div class='ex-title'>{exercise}</div>"
                    f"<div class='ex-sub'>{reps_str}</div>"
                    f"</div>", unsafe_allow_html=True
                )

        st.markdown("")  # spacer between rounds

# ── Lifestyle guidelines ──────────────────────────────────────────────────────
with st.expander("🌿 Lifestyle Guidelines", expanded=False):
    st.markdown(
        "These guidelines are tailored to support your meal plan and health goals. "
        "Consistency here is just as important as diet."
    )

    for rule in LIFESTYLE_RULES:
        # Highlight water and sleep as critical
        if rule["highlight"]:
            st.markdown(
                f"<div class='lifestyle-item'>"
                f"<span class='highlight-rule'>{rule['icon']} {rule['text']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='lifestyle-item'>{rule['icon']} {rule['text']}</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("**🚫 Avoid completely:**")

    # Filter avoid list — skip processed meat reminder for vegetarians
    avoid_filtered = AVOID_ITEMS.copy()
    if diet_type in ("Vegetarian", "Vegan", "Eggetarian"):
        avoid_filtered = [a for a in avoid_filtered if "meat" not in a.lower()]

    st.markdown(
        " ".join(f"<span class='avoid-tag'>{item}</span>" for item in avoid_filtered),
        unsafe_allow_html=True
    )

    st.markdown("")
    st.markdown(
        "<div class='warn-rule'>⚠️ Use only 3–4 tsp of good oil per day total (mustard / olive / ghee). "
        "Always use a non-stick pan to reduce oil needs.</div>",
        unsafe_allow_html=True
    )

    st.markdown("")
    # Condition-specific reminders
    if "PCOS" in conditions:
        st.info("💡 PCOS note: Consistency in sleep timing and stress management is especially critical — cortisol spikes worsen hormonal imbalance.")
    if any("diabetes" in c.lower() for c in conditions):
        st.info("💡 Diabetes note: Walk within 15 minutes of finishing a meal to blunt post-meal glucose spikes. Never skip meals.")
    if any("thyroid" in c.lower() for c in conditions):
        st.info("💡 Thyroid note: Take medication on empty stomach 30–60 mins before breakfast. Avoid raw cruciferous vegetables in large amounts.")
