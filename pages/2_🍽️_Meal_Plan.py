"""
2_Meal_Plan.py — Meal Plan Generator
Generates a 7-day personalised meal plan for a selected client.
Shows 2 options for lunch and dinner. Allows PDF export.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import get_all_clients, get_client, save_meal_plan, get_latest_meal_plan
from utils.calculations import full_assessment, GOAL_ADJUSTMENTS
from utils.meal_planner import generate_meal_plan, plan_daily_totals, snack_swap_suggestions
from utils.pdf_generator import generate_pdf
from utils.header import render_header

render_header("Meal Plan")

st.markdown("""
<style>
  .meal-card { background: #FBF7F2; border: 1px solid #E5D9CC; border-radius: 10px;
               padding: 12px 14px; margin-bottom: 8px; }
  .meal-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                letter-spacing: 1px; color: #40916C; }
  .recipe-name { font-size: 0.95rem; font-weight: 600; color: #1A1A1A; }
  .recipe-meta { font-size: 0.78rem; color: #6B7280; }
  .option-badge { background: #D8F3DC; color: #2D6A4F; font-size: 0.68rem;
                  font-weight: 700; padding: 2px 8px; border-radius: 10px;
                  display: inline-block; margin-bottom: 4px; }
  .target-bar { background: #F0E8DC; border-radius: 8px; padding: 10px 14px;
                border: 1px solid #E5D9CC; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🍽️ Meal Plan Generator")
st.markdown("---")

# ── Client selector ───────────────────────────────────────────────────────────

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

col_sel, col_btn = st.columns([3, 1])
with col_sel:
    selected_label = st.selectbox("Select Client", list(client_options.keys()),
                                  index=list(client_options.keys()).index(default_key))
client_id = client_options[selected_label]
client = get_client(client_id)
assessment = full_assessment(client)

# ── Assessment summary ─────────────────────────────────────────────────────────

with st.container():
    st.markdown(
        f"<div class='target-bar'>"
        f"<b>{client['name']}</b> &nbsp;·&nbsp; "
        f"BMI {assessment['bmi']} ({assessment['bmi_category']}) &nbsp;·&nbsp; "
        f"Target: <b>{assessment['target_calories']} kcal/day</b> &nbsp;·&nbsp; "
        f"Protein: <b>{assessment['protein_g']}g</b> &nbsp;·&nbsp; "
        f"Carbs: <b>{assessment['carbs_g']}g</b> &nbsp;·&nbsp; "
        f"Fat: <b>{assessment['fat_g']}g</b> &nbsp;·&nbsp; "
        f"Water: <b>{assessment['hydration_L']} L/day</b>"
        f"</div>",
        unsafe_allow_html=True
    )

# ── Generate controls ─────────────────────────────────────────────────────────

col_g1, col_g2, col_g3 = st.columns([1, 1, 2])
with col_g1:
    if st.button("🔄 Generate New Plan", width="stretch", type="primary"):
        with st.spinner("Building your meal plan..."):
            plan = generate_meal_plan(client, assessment)
            swaps = snack_swap_suggestions(client)
            save_meal_plan(client_id, plan, {
                "calories": assessment["target_calories"],
                "protein":  assessment["protein_g"],
                "carbs":    assessment["carbs_g"],
                "fat":      assessment["fat_g"],
            })
            st.session_state["current_plan"] = plan
            st.session_state["current_swaps"] = swaps
            st.session_state["plan_client_id"] = client_id
        st.success("✅ Plan generated and saved!")

with col_g2:
    if st.button("📂 Load Last Plan", width="stretch"):
        saved = get_latest_meal_plan(client_id)
        if saved:
            st.session_state["current_plan"] = saved["plan"]
            st.session_state["current_swaps"] = snack_swap_suggestions(client)
            st.session_state["plan_client_id"] = client_id
            st.success(f"Loaded plan from {saved['created_at'][:10]}")
        else:
            st.info("No saved plan found for this client.")

# ── Plan display ──────────────────────────────────────────────────────────────

plan = st.session_state.get("current_plan")
swaps = st.session_state.get("current_swaps", [])
plan_client = st.session_state.get("plan_client_id")

if plan and plan_client == client_id:
    st.markdown("---")
    st.markdown(f"### 7-Day Plan for {client['name']}")

    DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]

    def recipe_card(recipe: dict, option_label: str = ""):
        if not recipe:
            return ""
        name_en = recipe.get("name_en", "")
        name_ne = recipe.get("name_ne", "")
        kcal    = recipe.get("calories", 0)
        prot    = recipe.get("protein_g", 0)
        serv    = recipe.get("serving_description", "")
        prep    = recipe.get("prep_time_mins", "")
        method  = recipe.get("cooking_method", "")
        badge   = f"<span class='option-badge'>{option_label}</span><br>" if option_label else ""
        ne_str  = f" <span style='color:#9CA3AF;font-size:0.82rem'>({name_ne})</span>" if name_ne else ""
        return (
            f"<div class='meal-card'>"
            f"{badge}"
            f"<div class='recipe-name'>{name_en}{ne_str}</div>"
            f"<div class='recipe-meta'>{kcal} kcal &nbsp;·&nbsp; {prot}g protein"
            f"{f' &nbsp;·&nbsp; {serv}' if serv else ''}"
            f"{f' &nbsp;·&nbsp; {prep} min' if prep else ''}"
            f"{f' · {method}' if method else ''}</div>"
            f"</div>"
        )

    for day in DAYS_ORDER:
        if day not in plan:
            continue
        dp = plan[day]
        totals = plan_daily_totals(dp)

        with st.expander(
            f"**{day}** — est. {totals['calories']} kcal · "
            f"{totals['protein_g']}g protein",
            expanded=(day == "Monday")
        ):
            bc, lc, dc, sc = st.columns([1, 1.3, 1.3, 0.8])

            with bc:
                st.markdown("<div class='meal-label'>🌅 Breakfast</div>", unsafe_allow_html=True)
                for r in dp.get("breakfast", []):
                    st.markdown(recipe_card(r), unsafe_allow_html=True)

            with lc:
                st.markdown("<div class='meal-label'>☀️ Lunch</div>", unsafe_allow_html=True)
                lunch = dp.get("lunch", [])
                for i, r in enumerate(lunch):
                    st.markdown(recipe_card(r, f"Option {'A' if i==0 else 'B'}"), unsafe_allow_html=True)

            with dc:
                st.markdown("<div class='meal-label'>🌙 Dinner</div>", unsafe_allow_html=True)
                dinner = dp.get("dinner", [])
                for i, r in enumerate(dinner):
                    st.markdown(recipe_card(r, f"Option {'A' if i==0 else 'B'}"), unsafe_allow_html=True)

            with sc:
                st.markdown("<div class='meal-label'>🫘 Snack</div>", unsafe_allow_html=True)
                for r in dp.get("snack", []):
                    st.markdown(recipe_card(r), unsafe_allow_html=True)

    # ── Snack swaps section ────────────────────────────────────────────────────

    st.markdown("---")
    with st.expander("💡 Healthy Snack Swaps", expanded=False):
        st.markdown("Replace your usual snacks with these better options:")
        for s in swaps:
            st.markdown(
                f"**{s['name_en']}**"
                + (f" ({s['name_ne']})" if s.get("name_ne") else "")
                + f" — {s.get('calories',0)} kcal · {s.get('protein_g',0)}g protein"
                + (f" · {s.get('serving_description','')}" if s.get("serving_description") else "")
            )

    # ── PDF Export ────────────────────────────────────────────────────────────

    st.markdown("---")
    st.markdown("### 📄 Export Report")

    if st.button("📥 Generate PDF Report", width="content"):
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = generate_pdf(
                    client=client,
                    assessment=assessment,
                    plan=plan,
                    snack_swaps=swaps,
                )
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"NutriDesk_{client['name'].replace(' ','_')}_Plan.pdf",
                    mime="application/pdf",
                    width="content",
                )
            except Exception as e:
                st.error(f"PDF generation error: {e}")

else:
    st.info("👆 Click **Generate New Plan** or **Load Last Plan** to get started.")
