"""
plan_builder.py — Full Plan Builder
Multi-tab wizard: Meal Plan → Exercise & Lifestyle → Generate PDF.
Navigate freely between tabs. PDF skips sections not completed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import (
    get_all_clients, get_client, save_meal_plan, get_latest_meal_plan,
    get_biomarkers, get_personalization, save_personalization
)
from utils.calculations import full_assessment, GOAL_ADJUSTMENTS
from utils.meal_planner import (
    generate_meal_plan, plan_daily_totals, snack_swap_suggestions,
    build_grocery_list, swap_single_recipe
)
from utils.pdf_generator import generate_pdf
from utils.personalization import build_personalized_plan, _parse_conditions
from utils.personalization_library import EXERCISES, LIFESTYLE_GUIDELINES, AVOID_ITEMS, SNACK_OPTIONS
from utils.header import render_header

render_header("Plan Builder")

st.markdown("""
<style>
  .meal-card { background:#FBF7F2; border:1px solid #E5D9CC; border-radius:10px;
               padding:12px 14px; margin-bottom:8px; }
  .meal-label { font-size:0.72rem; font-weight:700; text-transform:uppercase;
                letter-spacing:1px; color:#40916C; }
  .recipe-name { font-size:0.95rem; font-weight:600; color:#1A1A1A; }
  .recipe-meta { font-size:0.78rem; color:#6B7280; }
  .option-badge { background:#D8F3DC; color:#2D6A4F; font-size:0.68rem;
                  font-weight:700; padding:2px 8px; border-radius:10px;
                  display:inline-block; margin-bottom:4px; }
  .target-bar { background:#F0E8DC; border-radius:8px; padding:10px 14px;
                border:1px solid #E5D9CC; margin-bottom:12px; }
  .status-done { background:#D8F3DC; color:#1B4332; border-radius:6px;
                 padding:4px 12px; font-size:0.82rem; font-weight:600; display:inline-block; }
  .status-todo { background:#F3F4F6; color:#6B7280; border-radius:6px;
                 padding:4px 12px; font-size:0.82rem; display:inline-block; }
  .ex-card { background:#FBF7F2; border:1px solid #E5D9CC; border-radius:10px;
             padding:12px 14px; margin-bottom:8px; }
  .ex-label { font-size:0.72rem; font-weight:700; text-transform:uppercase;
              letter-spacing:1px; color:#40916C; margin-bottom:2px; }
  .highlight-rule { background:#D8F3DC; border-radius:6px; padding:6px 12px;
                    color:#1B4332; font-weight:600; font-size:0.88rem;
                    display:block; margin-bottom:6px; }
  .normal-rule { background:#F9F5F0; border-radius:6px; padding:6px 12px;
                 color:#374151; font-size:0.88rem; display:block; margin-bottom:6px; }
  .avoid-tag { background:#FEE2E2; color:#991B1B; border-radius:4px;
               padding:2px 8px; font-size:0.78rem; font-weight:600;
               display:inline-block; margin:3px; }
  .snack-card { background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px;
                padding:10px 14px; margin-bottom:8px; }
  .mod-note { background:#FEF9C3; border-radius:6px; padding:6px 10px;
              font-size:0.80rem; color:#713F12; margin-top:4px; }
  .section-banner { background:linear-gradient(135deg,#2D6A4F 0%,#40916C 100%);
                    color:white; border-radius:10px; padding:10px 16px;
                    font-weight:700; font-size:1.0rem; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

# ── Client selector ───────────────────────────────────────────────────────────
st.markdown("## 📊 Plan Builder")

clients = get_all_clients()
if not clients:
    st.warning("No clients yet. Add one via 📋 New Client.")
    if st.button("➕ Add Client"):
        st.switch_page("pages/1_📋_Intake.py")
    st.stop()

client_options = {f"{c['name']} (ID {c['id']})": c["id"] for c in clients}
default_id = st.session_state.get("active_client_id")
default_key = next(
    (k for k, v in client_options.items() if v == default_id),
    list(client_options.keys())[0]
)
selected_label = st.selectbox(
    "Client", list(client_options.keys()),
    index=list(client_options.keys()).index(default_key)
)
client_id = client_options[selected_label]
st.session_state["active_client_id"] = client_id
client = get_client(client_id)
assessment = full_assessment(client)

# ── Session state keys (client-scoped) ────────────────────────────────────────
_plan_key   = f"pb_plan_{client_id}"
_swaps_key  = f"pb_swaps_{client_id}"
_ex_key     = f"pb_exercise_{client_id}"

# ── Status helpers ────────────────────────────────────────────────────────────
meal_done     = bool(st.session_state.get(_plan_key))
exercise_done = bool(
    st.session_state.get(_ex_key) or
    (get_personalization(client_id) or {}).get("exercises")
)

# ── Status bar ────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='target-bar'>"
    f"<b>{client['name']}</b> &nbsp;·&nbsp; "
    f"BMI {assessment['bmi']} ({assessment['bmi_category']}) &nbsp;·&nbsp; "
    f"Target: <b>{assessment['target_calories']} kcal</b> &nbsp;·&nbsp; "
    f"P: {assessment['protein_g']}g · C: {assessment['carbs_g']}g · F: {assessment['fat_g']}g"
    f"</div>",
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)
with c1:
    cls = "status-done" if meal_done else "status-todo"
    lbl = "✅ Meal Plan done" if meal_done else "⬜ Meal Plan pending"
    st.markdown(f"<span class='{cls}'>{lbl}</span>", unsafe_allow_html=True)
with c2:
    cls = "status-done" if exercise_done else "status-todo"
    lbl = "✅ Exercise & Lifestyle done" if exercise_done else "⬜ Exercise & Lifestyle — optional"
    st.markdown(f"<span class='{cls}'>{lbl}</span>", unsafe_allow_html=True)
with c3:
    cls = "status-done" if meal_done else "status-todo"
    lbl = "✅ Ready to export PDF" if meal_done else "⬜ Complete Meal Plan to export"
    st.markdown(f"<span class='{cls}'>{lbl}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_meal, tab_exercise, tab_pdf = st.tabs([
    f"🍽️ Meal Plan {'✅' if meal_done else ''}",
    f"💪 Exercise & Lifestyle {'✅' if exercise_done else ''}",
    f"📄 Generate PDF {'✅' if meal_done else '🔒'}",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — MEAL PLAN
# ═════════════════════════════════════════════════════════════════════════════
with tab_meal:

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("🔄 Generate New Plan", type="primary", use_container_width=True):
            with st.spinner(f"Building meal plan for {client['name']}…"):
                plan  = generate_meal_plan(client, assessment)
                swaps = snack_swap_suggestions(client)
                save_meal_plan(client_id, plan, {
                    "calories": assessment["target_calories"],
                    "protein":  assessment["protein_g"],
                    "carbs":    assessment["carbs_g"],
                    "fat":      assessment["fat_g"],
                })
                st.session_state[_plan_key]  = plan
                st.session_state[_swaps_key] = swaps
            st.success("✅ Plan generated and saved!")
            st.rerun()

    with col_g2:
        if st.button("📂 Load Last Saved Plan", use_container_width=True):
            saved = get_latest_meal_plan(client_id)
            if saved:
                st.session_state[_plan_key]  = saved["plan"]
                st.session_state[_swaps_key] = snack_swap_suggestions(client)
                st.success("✅ Last plan loaded.")
                st.rerun()
            else:
                st.info("No saved plan found. Generate one first.")

    # Auto-load on first visit
    if not st.session_state.get(_plan_key):
        saved = get_latest_meal_plan(client_id)
        if saved:
            st.session_state[_plan_key]  = saved["plan"]
            st.session_state[_swaps_key] = snack_swap_suggestions(client)
        elif st.session_state.pop("auto_generate_plan", False):
            with st.spinner(f"Building meal plan for {client['name']}…"):
                _p  = generate_meal_plan(client, assessment)
                _sw = snack_swap_suggestions(client)
                save_meal_plan(client_id, _p, {
                    "calories": assessment["target_calories"],
                    "protein":  assessment["protein_g"],
                    "carbs":    assessment["carbs_g"],
                    "fat":      assessment["fat_g"],
                })
                st.session_state[_plan_key]  = _p
                st.session_state[_swaps_key] = _sw

    plan  = st.session_state.get(_plan_key)
    swaps = st.session_state.get(_swaps_key, [])

    if not plan:
        st.info("👆 Click **Generate New Plan** to get started.")
    else:
        st.markdown(f"### 7-Day Plan for {client['name']}")
        DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        def recipe_card_html(recipe, option_label=""):
            if not recipe: return ""
            badge = f"<span class='option-badge'>{option_label}</span><br>" if option_label else ""
            ne = f" <span style='color:#9CA3AF;font-size:0.82rem'>({recipe.get('name_ne','')})</span>" if recipe.get('name_ne') else ""
            tags = " ".join(
                f"<span style='background:#F0FFF4;color:#276749;border:1px solid #C6F6D5;border-radius:8px;font-size:0.65rem;padding:1px 6px'>{t}</span>"
                for t in recipe.get("dietary_tags",[])[:3]
            )
            return (
                f"<div class='meal-card'>{badge}"
                f"<div class='recipe-name'>{recipe.get('name_en','')}{ne}</div>"
                f"<div class='recipe-meta'>{recipe.get('calories',0)} kcal · "
                f"{recipe.get('protein_g',0)}g P · {recipe.get('carbs_g',0)}g C · {recipe.get('fat_g',0)}g F"
                + (f" · {recipe.get('serving_description','')}" if recipe.get('serving_description') else "")
                + (f" · {recipe.get('prep_time_mins','')} min" if recipe.get('prep_time_mins') else "")
                + f"</div>"
                + (f"<div style='margin-top:5px'>{tags}</div>" if tags else "")
                + "</div>"
            )

        def render_slot(day, slot, recipes, icon, label, multi=False):
            st.markdown(f"<div class='meal-label'>{icon} {label}</div>", unsafe_allow_html=True)
            if not recipes:
                st.markdown("<div style='color:#9CA3AF;font-size:0.8rem;padding:6px'>—</div>", unsafe_allow_html=True)
                return
            for i, r in enumerate(recipes):
                opt = f"Option {'A' if i==0 else 'B'}" if multi else ""
                st.markdown(recipe_card_html(r, opt), unsafe_allow_html=True)
                if st.button("🔄 Swap", key=f"pb_swap_{day}_{slot}_{i}_{client_id}"):
                    updated = swap_single_recipe(
                        plan=st.session_state[_plan_key],
                        day=day, slot=slot, position=i,
                        client=client, assessment=assessment
                    )
                    st.session_state[_plan_key] = updated
                    st.rerun()

        for day in DAYS:
            if day not in plan: continue
            dp = plan[day]
            totals = plan_daily_totals(dp)
            with st.expander(f"**{day}** — {totals['calories']} kcal · {totals['protein_g']}g protein",
                             expanded=(day=="Monday")):
                bc, lc, dc, sc = st.columns([1,1.3,1.3,0.8])
                with bc: render_slot(day,"breakfast",dp.get("breakfast",[]),"🌅","Breakfast")
                with lc: render_slot(day,"lunch",dp.get("lunch",[]),"☀️","Lunch",multi=True)
                with dc: render_slot(day,"dinner",dp.get("dinner",[]),"🌙","Dinner",multi=True)
                with sc: render_slot(day,"snack",dp.get("snack",[]),"🫘","Snack")

        st.markdown("---")
        with st.expander("💡 Healthy Snack Swaps", expanded=False):
            for s in swaps:
                st.markdown(
                    f"**{s['name_en']}**"
                    + (f" ({s['name_ne']})" if s.get('name_ne') else "")
                    + f" — {s.get('calories',0)} kcal · {s.get('protein_g',0)}g protein"
                    + (f" · {s.get('serving_description','')}" if s.get('serving_description') else "")
                )

        with st.expander("🛒 Weekly Grocery List", expanded=False):
            grocery = build_grocery_list(plan)
            if grocery:
                gcols = st.columns(2)
                groups = list(grocery.items())
                half = (len(groups)+1)//2
                for ci, col in enumerate(gcols):
                    with col:
                        for group, items in groups[ci*half:(ci+1)*half]:
                            st.markdown(f"**{group}**")
                            for item in items: st.markdown(f"- {item}")
                            st.markdown("")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — EXERCISE & LIFESTYLE
# ═════════════════════════════════════════════════════════════════════════════
with tab_exercise:

    fitness_level = client.get("fitness_level") or "Moderate"
    diet_type     = client.get("diet_type","Non-vegetarian")

    # Load or build personalization
    if _ex_key not in st.session_state:
        saved_ex = get_personalization(client_id)
        if saved_ex and saved_ex.get("exercises"):
            st.session_state[_ex_key] = saved_ex
        else:
            st.session_state[_ex_key] = build_personalized_plan(client)

    ex_plan = st.session_state[_ex_key]

    conds_str = ", ".join(client.get("medical_conditions") or []) or "None"
    st.markdown(
        f"<div class='section-banner'>👤 {client['name']} · Fitness: {fitness_level} · Diet: {diet_type} · Conditions: {conds_str}</div>",
        unsafe_allow_html=True
    )

    col_ref, col_sav = st.columns([3,1])
    with col_ref:
        if st.button("🔄 Re-generate from client profile", key=f"regen_ex_{client_id}"):
            st.session_state[_ex_key] = build_personalized_plan(client)
            st.rerun()
    with col_sav:
        if st.button("💾 Save", type="primary", key=f"save_ex_top_{client_id}"):
            save_personalization(client_id, st.session_state[_ex_key])
            st.success("Saved!")
            st.rerun()

    st.markdown("---")

    # ── Exercises ────────────────────────────────────────────────────────
    with st.expander("🏋️ Exercise Circuit", expanded=True):
        exercises = ex_plan["exercises"]
        selected_names = {e["name"] for e in exercises}

        for i, ex in enumerate(exercises):
            col_ex, col_swap, col_rm = st.columns([4,3,1])
            with col_ex:
                reps = ex.get("active_reps", str(ex["reps"].get(fitness_level,"—")))
                st.markdown(
                    f"<div class='ex-card'><div class='ex-label'>{ex['category'].upper()}</div>"
                    f"<div style='font-weight:700'>{ex['name']}</div>"
                    f"<div style='font-size:0.84rem;color:#4B5563'>{reps}</div></div>",
                    unsafe_allow_html=True
                )
                if ex.get("modification"):
                    client_conds = _parse_conditions(client)
                    if any(c in client_conds for c in ex.get("modification_for",[])):
                        st.markdown(f"<div class='mod-note'>⚠️ {ex['modification']}</div>", unsafe_allow_html=True)
            with col_swap:
                swap_opts = [e["name"] for e in EXERCISES if e["category"]==ex["category"] and e["name"] not in selected_names]
                if swap_opts:
                    sc = st.selectbox("Swap with",["— keep —"]+swap_opts, key=f"pb_swex_{i}_{client_id}")
                    if sc != "— keep —" and st.button("Apply", key=f"pb_apex_{i}_{client_id}"):
                        repl = next(e for e in EXERCISES if e["name"]==sc)
                        rv = repl["reps"].get(fitness_level, repl["reps"].get("Moderate"))
                        rs = f"{rv} reps" if repl["unit"]=="reps" else str(rv)
                        ne = dict(repl); ne["active_reps"]=rs; ne["active_level"]=fitness_level
                        st.session_state[_ex_key]["exercises"][i] = ne
                        st.rerun()
                else:
                    st.caption("No swaps in this category")
            with col_rm:
                if st.button("🗑", key=f"pb_rmex_{i}_{client_id}"):
                    st.session_state[_ex_key]["exercises"].pop(i); st.rerun()

        st.markdown("**➕ Add exercise:**")
        ca, ce, cb = st.columns([2,3,1])
        with ca: add_cat = st.selectbox("Cat",["cardio","core","strength","flexibility"], key=f"pb_acat_{client_id}")
        with ce:
            aopts = [e["name"] for e in EXERCISES if e["category"]==add_cat and e["name"] not in {x["name"] for x in exercises}]
            add_choice = st.selectbox("Exercise", aopts, key=f"pb_achoice_{client_id}") if aopts else None
            if not aopts: st.caption("All added")
        with cb:
            st.markdown("<br>", unsafe_allow_html=True)
            if add_choice and st.button("Add", key=f"pb_addbtn_{client_id}"):
                ne2 = next(e for e in EXERCISES if e["name"]==add_choice)
                rv2 = ne2["reps"].get(fitness_level, ne2["reps"].get("Moderate"))
                rs2 = f"{rv2} reps" if ne2["unit"]=="reps" else str(rv2)
                entry = dict(ne2); entry["active_reps"]=rs2; entry["active_level"]=fitness_level
                st.session_state[_ex_key]["exercises"].append(entry); st.rerun()

    # ── Lifestyle Guidelines ──────────────────────────────────────────────
    with st.expander("🌿 Lifestyle Guidelines", expanded=False):
        guidelines = ex_plan["guidelines"]
        for i, g in enumerate(guidelines):
            gc, gd = st.columns([10,1])
            with gc:
                cls = "highlight-rule" if g.get("highlight") else "normal-rule"
                st.markdown(f"<span class='{cls}'>{g['icon']} {g['text']}</span>", unsafe_allow_html=True)
            with gd:
                if st.button("✕", key=f"pb_dg_{i}_{client_id}"):
                    st.session_state[_ex_key]["guidelines"].pop(i); st.rerun()

        st.markdown("---")
        current_texts = {g["text"] for g in guidelines}
        add_gopts = {
            (f"{g['icon']} {g['text'][:80]}..." if len(g["text"])>80 else f"{g['icon']} {g['text']}"): g
            for g in LIFESTYLE_GUIDELINES if g["text"] not in current_texts
        }
        if add_gopts:
            gl1, gl2 = st.columns([5,1])
            with gl1: gc_choice = st.selectbox("Add from library", list(add_gopts.keys()), key=f"pb_gsel_{client_id}")
            with gl2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"pb_gadd_{client_id}"):
                    st.session_state[_ex_key]["guidelines"].append(dict(add_gopts[gc_choice])); st.rerun()

        ci2, ct2 = st.columns([1,4])
        with ci2: cicon = st.text_input("Icon",value="💡",max_chars=4,key=f"pb_gicon_{client_id}")
        with ct2: ctext = st.text_area("Custom guideline",key=f"pb_gtext_{client_id}",placeholder="Type a personalised guideline…")
        if st.button("Add custom",key=f"pb_gcust_{client_id}"):
            if ctext.strip():
                st.session_state[_ex_key]["guidelines"].append({"icon":cicon or "💡","text":ctext.strip(),"highlight":False,"conditions":[],"lifestyle_tags":[]}); st.rerun()

    # ── Avoid List ────────────────────────────────────────────────────────
    with st.expander("🚫 Avoid Completely", expanded=False):
        avoid_items = ex_plan["avoid_items"]
        acols = st.columns(2)
        for i, item in enumerate(avoid_items):
            with acols[i%2]:
                at, ax = st.columns([5,1])
                with at: st.markdown(f"<span class='avoid-tag'>{item}</span>", unsafe_allow_html=True)
                with ax:
                    if st.button("✕", key=f"pb_av_{i}_{client_id}"):
                        st.session_state[_ex_key]["avoid_items"].pop(i); st.rerun()

        st.markdown("---")
        cur_avoids = set(avoid_items)
        av_opts = [a["name"] for a in AVOID_ITEMS if a["name"] not in cur_avoids]
        if av_opts:
            al1, al2 = st.columns([5,1])
            with al1: av_pick = st.selectbox("Add from library", av_opts, key=f"pb_avsel_{client_id}")
            with al2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"pb_avadd_{client_id}"):
                    st.session_state[_ex_key]["avoid_items"].append(av_pick); st.rerun()
        ca2, cb2 = st.columns([5,1])
        with ca2: cav = st.text_input("Custom avoid item", key=f"pb_cavcust_{client_id}", placeholder="e.g. Mango (high sugar)")
        with cb2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key=f"pb_cavbtn_{client_id}"):
                if cav.strip() and cav.strip() not in cur_avoids:
                    st.session_state[_ex_key]["avoid_items"].append(cav.strip()); st.rerun()

    # ── Snack Swaps ───────────────────────────────────────────────────────
    with st.expander("🥜 Snack Options", expanded=False):
        snacks = ex_plan["snacks"]
        is_veg = diet_type in ("Vegetarian","Vegan","Eggetarian")
        for i, snack in enumerate(snacks):
            sc1, sc2 = st.columns([10,1])
            with sc1:
                st.markdown(
                    f"<div class='snack-card'><b>{snack['name']}</b><br>"
                    f"<span style='color:#4B5563;font-size:0.85rem'>{snack['desc']}</span></div>",
                    unsafe_allow_html=True
                )
            with sc2:
                if st.button("✕", key=f"pb_sn_{i}_{client_id}"):
                    st.session_state[_ex_key]["snacks"].pop(i); st.rerun()

        cur_snacks = {s["name"] for s in snacks}
        sadd_opts = {f"{s['name']} — {s['desc']}": s for s in SNACK_OPTIONS if s["name"] not in cur_snacks and (not is_veg or s["veg"])}
        if sadd_opts:
            sl1, sl2 = st.columns([6,1])
            with sl1: sp = st.selectbox("Add snack", list(sadd_opts.keys()), key=f"pb_snasel_{client_id}")
            with sl2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"pb_snaadd_{client_id}"):
                    st.session_state[_ex_key]["snacks"].append(dict(sadd_opts[sp])); st.rerun()
        sn1, sn2, sn3 = st.columns([3,4,1])
        with sn1: csn = st.text_input("Custom snack name", key=f"pb_csnname_{client_id}")
        with sn2: csd = st.text_input("Why it works", key=f"pb_csndesc_{client_id}")
        with sn3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key=f"pb_csnadd_{client_id}"):
                if csn.strip():
                    st.session_state[_ex_key]["snacks"].append({"name":csn.strip(),"desc":csd.strip(),"conditions":[],"veg":True}); st.rerun()

    st.markdown("---")
    if st.button("💾 Save Exercise & Lifestyle Plan", type="primary", key=f"save_ex_bot_{client_id}"):
        save_personalization(client_id, st.session_state[_ex_key])
        st.success("✅ Exercise & Lifestyle plan saved — it will be included in the PDF.")
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — GENERATE PDF
# ═════════════════════════════════════════════════════════════════════════════
with tab_pdf:

    st.markdown("### 📄 Review & Export")

    # Re-check status here (may have changed in other tabs this run)
    _cur_plan       = st.session_state.get(_plan_key)
    _cur_ex         = st.session_state.get(_ex_key)
    _saved_ex       = get_personalization(client_id)
    _meal_ready     = bool(_cur_plan)
    _exercise_saved = bool(_saved_ex and _saved_ex.get("exercises"))

    col_a, col_b = st.columns(2)
    with col_a:
        if _meal_ready:
            st.success("✅ Meal plan is ready")
        else:
            st.error("❌ No meal plan — go to the Meal Plan tab first")
    with col_b:
        if _exercise_saved:
            st.success("✅ Exercise & Lifestyle plan included")
        else:
            st.info("ℹ️ Exercise & Lifestyle not saved — this section will be skipped in the PDF")

    st.markdown("---")

    if not _meal_ready:
        st.warning("Generate and save a meal plan first before exporting.")
    else:
        _pdf_key   = f"pdf_bytes_{client_id}"
        _pdf_error = f"pdf_error_{client_id}"

        pdf_col, dl_col = st.columns([1,2])
        with pdf_col:
            if st.button("📥 Generate PDF", type="primary", use_container_width=True, key=f"gen_pdf_{client_id}"):
                st.session_state.pop(_pdf_key, None)
                st.session_state.pop(_pdf_error, None)
                with st.spinner("Generating PDF…"):
                    try:
                        pdf_bytes = generate_pdf(
                            client=client,
                            assessment=assessment,
                            plan=_cur_plan,
                            snack_swaps=st.session_state.get(_swaps_key, []),
                            biomarkers=get_biomarkers(client_id),
                            personalization=_saved_ex if _exercise_saved else None,
                            include_lifestyle=_exercise_saved,
                        )
                        st.session_state[_pdf_key] = pdf_bytes
                    except Exception as e:
                        import traceback
                        st.session_state[_pdf_error] = (str(e), traceback.format_exc())

        with dl_col:
            if st.session_state.get(_pdf_error):
                emsg, etb = st.session_state[_pdf_error]
                st.error(f"PDF error: {emsg}")
                with st.expander("Details"): st.code(etb)
            elif st.session_state.get(_pdf_key):
                fname = f"NutriDesk_{client['name'].replace(' ','_')}_Plan.pdf"
                st.download_button(
                    label="⬇️ Download PDF",
                    data=st.session_state[_pdf_key],
                    file_name=fname,
                    mime="application/pdf",
                    key=f"dl_pdf_{client_id}",
                    use_container_width=True,
                )
                st.caption(
                    "PDF includes: Meal plan"
                    + (", Exercise & Lifestyle" if _exercise_saved else "")
                    + " · Click to save."
                )
