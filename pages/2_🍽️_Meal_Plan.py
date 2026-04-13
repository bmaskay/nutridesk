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
from utils.meal_planner import generate_meal_plan, plan_daily_totals, snack_swap_suggestions, build_grocery_list, swap_single_recipe
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
            from datetime import datetime as _dt
            _saved_dt = _dt.fromisoformat(saved["created_at"])
            _delta = _dt.now() - _saved_dt
            if _delta.days == 0:
                _when = "earlier today"
            elif _delta.days == 1:
                _when = "yesterday"
            elif _delta.days < 7:
                _when = f"{_delta.days} days ago"
            elif _delta.days < 14:
                _when = "last week"
            else:
                _when = _saved_dt.strftime("%-d %b")
            st.success(f"✅ Plan loaded — saved {_when} ({_saved_dt.strftime('%-d %b')})")
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

    def recipe_card_html(recipe: dict, option_label: str = "") -> str:
        """Return HTML string for a recipe card (no swap button)."""
        if not recipe:
            return ""
        name_en = recipe.get("name_en", "")
        name_ne = recipe.get("name_ne", "")
        kcal    = recipe.get("calories", 0)
        prot    = recipe.get("protein_g", 0)
        carbs   = recipe.get("carbs_g", 0)
        fat     = recipe.get("fat_g", 0)
        serv    = recipe.get("serving_description", "")
        prep    = recipe.get("prep_time_mins", "")
        method  = recipe.get("cooking_method", "")
        tags    = recipe.get("dietary_tags", [])
        ingr    = recipe.get("key_ingredients", [])
        badge   = f"<span class='option-badge'>{option_label}</span><br>" if option_label else ""
        ne_str  = f" <span style='color:#9CA3AF;font-size:0.82rem'>({name_ne})</span>" if name_ne else ""
        tag_html = ""
        if tags:
            tag_html = " ".join(
                f"<span style='background:#F0FFF4;color:#276749;border:1px solid #C6F6D5;"
                f"border-radius:8px;font-size:0.65rem;padding:1px 6px'>{t}</span>"
                for t in tags[:3]
            )
        ingr_html = ""
        if ingr:
            ingr_html = (
                f"<div style='font-size:0.72rem;color:#9CA3AF;margin-top:4px'>"
                f"🧂 {', '.join(ingr[:5])}"
                + (" ..." if len(ingr) > 5 else "")
                + "</div>"
            )
        _tag_div  = f"<div style='margin-top:5px'>{tag_html}</div>" if tag_html else ""
        _meta_serv   = f" &nbsp;·&nbsp; {serv}" if serv else ""
        _meta_prep   = f" &nbsp;·&nbsp; {prep} min" if prep else ""
        _meta_method = f" · {method}" if method else ""
        return (
            f"<div class='meal-card'>"
            f"{badge}"
            f"<div class='recipe-name'>{name_en}{ne_str}</div>"
            f"<div class='recipe-meta'>{kcal} kcal &nbsp;·&nbsp; {prot}g P &nbsp;·&nbsp; "
            f"{carbs}g C &nbsp;·&nbsp; {fat}g F"
            f"{_meta_serv}{_meta_prep}{_meta_method}</div>"
            f"{_tag_div}"
            f"{ingr_html}"
            f"</div>"
        )

    def render_slot(day: str, slot: str, recipes: list, icon: str, label: str,
                    multi_option: bool = False):
        """Render a meal slot column with recipe cards and per-card swap buttons."""
        st.markdown(f"<div class='meal-label'>{icon} {label}</div>", unsafe_allow_html=True)
        if not recipes:
            st.markdown(
                "<div style='color:#9CA3AF;font-size:0.8rem;padding:6px'>—</div>",
                unsafe_allow_html=True
            )
            return
        for i, r in enumerate(recipes):
            opt_label = f"Option {'A' if i == 0 else 'B'}" if multi_option else ""
            st.markdown(recipe_card_html(r, opt_label), unsafe_allow_html=True)
            # Swap button per recipe
            _btn_key = f"swap_{day}_{slot}_{i}"
            if st.button("🔄 Swap", key=_btn_key, help=f"Replace this {label.lower()} with a different option"):
                updated = swap_single_recipe(
                    plan=st.session_state["current_plan"],
                    day=day, slot=slot, position=i,
                    client=client, assessment=assessment,
                )
                st.session_state["current_plan"] = updated
                st.rerun()

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
                render_slot(day, "breakfast", dp.get("breakfast", []),
                            "🌅", "Breakfast", multi_option=False)
            with lc:
                render_slot(day, "lunch", dp.get("lunch", []),
                            "☀️", "Lunch", multi_option=True)
            with dc:
                render_slot(day, "dinner", dp.get("dinner", []),
                            "🌙", "Dinner", multi_option=True)
            with sc:
                render_slot(day, "snack", dp.get("snack", []),
                            "🫘", "Snack", multi_option=False)

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

    # ── Grocery list ─────────────────────────────────────────────────────────

    st.markdown("---")
    with st.expander("🛒 Weekly Grocery List", expanded=False):
        grocery = build_grocery_list(plan)
        if grocery:
            st.markdown(
                "<div style='font-size:0.82rem;color:#6B7280;margin-bottom:10px'>"
                "Based on Option A meals across the 7-day plan. Quantities are per serving — "
                "adjust based on household size."
                "</div>",
                unsafe_allow_html=True
            )
            gcols = st.columns(2)
            groups = list(grocery.items())
            half = (len(groups) + 1) // 2
            for col_idx, col in enumerate(gcols):
                with col:
                    for group, items in groups[col_idx * half : (col_idx + 1) * half]:
                        st.markdown(f"**{group}**")
                        for item in items:
                            st.markdown(f"- {item}")
                        st.markdown("")
        else:
            st.info("Generate a plan first to see the grocery list.")

    # ── Lifestyle guidelines ──────────────────────────────────────────────────

    st.markdown("---")
    _diet_type  = client.get("diet_type", "Non-vegetarian")
    _conditions = client.get("medical_conditions", [])

    _lifestyle_rules = [
        ("💧", "Drink at least 2–3 litres of water a day", True),
        ("🥗", "Eat slowly and chew very well — at least 20–30 times per bite", False),
        ("⏰", "Stick to your meal timings consistently", False),
        ("🌅", "Get sunlight exposure at sunrise and sunset", False),
        ("😴", "At least 6–8 hours of sleep is mandatory", True),
        ("📱", "No gadgets 30 minutes before sleeping", False),
        ("🌙", "Finish dinner 2–3 hours before bedtime", False),
        ("⏱️", "Fixed sleep and wake-up time every day", False),
        ("🪑", "Move 1–2 minutes for every 1 hour of sitting", False),
        ("🛢️", "Use only 3–4 tsp of cold-pressed oil per day (mustard / olive / ghee)", False),
    ]

    _avoid_items = [
        "Maida & products", "Fried food", "Sugar & sweets",
        "Fruit juices", "Bakery items", "Packaged food", "Cold drinks",
    ]
    if _diet_type not in ("Vegetarian", "Vegan", "Eggetarian"):
        _avoid_items.append("Processed meat")

    with st.expander("🌿 Lifestyle Guidelines", expanded=False):
        st.markdown(
            "These rules work alongside your meal plan. Small daily habits "
            "compound into big results."
        )
        for icon, text, highlight in _lifestyle_rules:
            if highlight:
                st.markdown(
                    f"<div style='background:#D8F3DC;border-radius:6px;padding:5px 10px;"
                    f"margin:4px 0;font-weight:600;color:#1B4332'>{icon} {text}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"{icon} {text}")

        st.markdown("**🚫 Avoid:** " + " · ".join(_avoid_items))

        if "PCOS" in _conditions:
            st.info("💡 **PCOS:** Consistent sleep timing and stress management are critical — cortisol spikes worsen hormonal balance. Prioritise low-GI carbohydrates and spread protein across all meals to support insulin sensitivity.")
        if any("diabetes" in c.lower() for c in _conditions):
            st.info("💡 **Diabetes / pre-diabetes:** Walk within 15 minutes of finishing a meal to blunt post-meal glucose spikes. Favour complex carbs (dal, oats, brown rice) over refined ones. Avoid fruit juice — eat whole fruit instead.")
        if any("thyroid" in c.lower() for c in _conditions):
            st.info("💡 **Thyroid:** Take thyroid medication on an empty stomach 30–60 minutes before breakfast. Limit raw cruciferous vegetables (cabbage, cauliflower) in large quantities — cooking neutralises goitrogens. Brazil nuts (1–2/day) support selenium intake.")
        if "Hypertension" in _conditions:
            st.info("💡 **Hypertension:** Keep sodium low — avoid added salt, pickles, papads, and packaged sauces. Increase potassium-rich foods: banana, sweet potato, spinach, dal. Limit caffeine to 1–2 cups/day.")
        if "High cholesterol" in _conditions:
            st.info("💡 **High cholesterol:** Reduce saturated fat (limit ghee to 1 tsp/day, avoid fried food). Increase soluble fibre: oats, flaxseed, and legumes actively lower LDL. Aim for omega-3 rich foods — fish, walnuts, flaxseed.")
        if "IBS / digestive issues" in _conditions:
            st.info("💡 **IBS:** Eat at regular times and chew thoroughly — 20+ times per bite. Avoid raw onion, garlic, and large portions of legumes if they trigger symptoms. Cooked vegetables are better tolerated than raw. Probiotic-rich foods (dahi/curd) may help.")
        if "Anaemia / iron deficiency" in _conditions:
            st.info("💡 **Anaemia:** Pair iron-rich foods (spinach, dal, meat) with Vitamin C sources (lemon, tomato, amla) to improve absorption. Avoid tea or coffee within 1 hour of meals — tannins block iron uptake.")
        if "Fatty liver" in _conditions:
            st.info("💡 **Fatty liver:** Strictly avoid alcohol, sugar, and fructose (including fruit juice). Focus on liver-supporting foods: green vegetables, cruciferous veg, garlic, turmeric. Calorie deficit is the primary treatment — this meal plan already applies that.")
        if "Kidney disease" in _conditions:
            st.warning("⚠️ **Kidney disease:** Protein, potassium, and phosphorus limits require specialist review. Please do not rely on standard macro targets — consult a renal dietitian before finalising this plan.")

        if st.button("💪 See full Exercise Plan", key="goto_exercise"):
            st.switch_page("pages/5_💪_Exercise_Plan.py")

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
