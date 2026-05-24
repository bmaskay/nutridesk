"""
5_Exercise_Plan.py — Personalised Exercise Plan & Lifestyle Guidelines
Review, swap, and save exercises, guidelines, snack swaps, and avoid items
before generating a PDF — mirroring the meal plan workflow.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import get_all_clients, get_client, get_personalization, save_personalization
from utils.personalization import (
    build_personalized_plan, build_default_exercises,
    build_default_guidelines, build_default_avoid_items, build_default_snacks
)
from utils.personalization_library import EXERCISES, LIFESTYLE_GUIDELINES, AVOID_ITEMS, SNACK_OPTIONS
from utils.header import render_header

render_header("Exercise & Lifestyle Plan")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .ex-card  { background:#FBF7F2; border:1px solid #E5D9CC; border-radius:10px;
              padding:14px 16px; margin-bottom:10px; }
  .ex-label { font-size:0.72rem; font-weight:700; text-transform:uppercase;
              letter-spacing:1px; color:#40916C; margin-bottom:4px; }
  .ex-title { font-size:1.0rem; font-weight:700; color:#1A1A1A; }
  .ex-sub   { font-size:0.84rem; color:#4B5563; }
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
  .section-banner { background:linear-gradient(135deg,#2D6A4F 0%,#40916C 100%);
                    color:white; border-radius:10px; padding:10px 16px;
                    font-weight:700; font-size:1.0rem; margin-bottom:12px; }
  .mod-note { background:#FEF9C3; border-radius:6px; padding:6px 10px;
              font-size:0.80rem; color:#713F12; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ── Client selector ───────────────────────────────────────────────────────────
st.markdown("## 💪 Exercise & Lifestyle Plan")
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
selected_label = st.selectbox(
    "Select Client", list(client_options.keys()),
    index=list(client_options.keys()).index(default_key)
)
client_id = client_options[selected_label]
client = get_client(client_id)

fitness_level = client.get("fitness_level") or "Moderate"
diet_type = client.get("diet_type", "Non-vegetarian")

# ── Load or generate plan ─────────────────────────────────────────────────────
plan_key = f"personalization_{client_id}"

if plan_key not in st.session_state:
    # Try to load saved plan from Supabase first
    saved = get_personalization(client_id)
    if saved and saved["exercises"]:
        st.session_state[plan_key] = saved
    else:
        # Auto-generate from client profile
        st.session_state[plan_key] = build_personalized_plan(client)

plan = st.session_state[plan_key]

# ── Header bar ────────────────────────────────────────────────────────────────
conds = client.get("medical_conditions") or []
conds_str = ", ".join(conds) if conds else "None"
st.markdown(
    f"<div class='section-banner'>"
    f"👤 {client['name']} &nbsp;·&nbsp; "
    f"Fitness: {fitness_level} &nbsp;·&nbsp; "
    f"Diet: {diet_type} &nbsp;·&nbsp; "
    f"Conditions: {conds_str}"
    f"</div>",
    unsafe_allow_html=True
)

col_refresh, col_save = st.columns([3, 1])
with col_refresh:
    if st.button("🔄 Re-generate from client profile", help="Regenerates the plan from scratch based on client data"):
        st.session_state[plan_key] = build_personalized_plan(client)
        st.rerun()
with col_save:
    if st.button("💾 Save plan", type="primary", help="Save customised plan to database"):
        save_personalization(client_id, st.session_state[plan_key])
        st.success("Plan saved!")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — EXERCISES
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🏋️ Exercise Circuit", expanded=True):
    st.markdown(
        "Review and customise the exercises below. Swap any exercise using the dropdown. "
        "Changes are saved when you click **Save plan**."
    )

    exercises = plan["exercises"]

    # All available exercise names for swap dropdown (excluding already selected ones)
    selected_names = {e["name"] for e in exercises}

    for i, ex in enumerate(exercises):
        with st.container():
            col_ex, col_swap, col_remove = st.columns([4, 3, 1])

            with col_ex:
                reps = ex.get("active_reps", ex["reps"].get(fitness_level, "—"))
                st.markdown(
                    f"<div class='ex-card'>"
                    f"<div class='ex-label'>{ex['category'].upper()}</div>"
                    f"<div class='ex-title'>{ex['name']}</div>"
                    f"<div class='ex-sub'>{reps}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                # Show modification note if applicable
                if ex.get("modification"):
                    from utils.personalization import _parse_conditions
                    client_conditions = _parse_conditions(client)
                    if any(c in client_conditions for c in ex.get("modification_for", [])):
                        st.markdown(
                            f"<div class='mod-note'>⚠️ Modification recommended: {ex['modification']}</div>",
                            unsafe_allow_html=True
                        )

            with col_swap:
                # Build swap options: exercises in same category not already selected
                swap_options = [
                    e["name"] for e in EXERCISES
                    if e["category"] == ex["category"] and e["name"] not in selected_names
                ]
                if swap_options:
                    swap_choice = st.selectbox(
                        "Swap with", ["— keep current —"] + swap_options,
                        key=f"swap_ex_{i}_{client_id}"
                    )
                    if swap_choice != "— keep current —":
                        if st.button("Apply", key=f"apply_ex_{i}_{client_id}"):
                            # Find the replacement exercise
                            replacement = next(e for e in EXERCISES if e["name"] == swap_choice)
                            reps_val = replacement["reps"].get(fitness_level, replacement["reps"].get("Moderate"))
                            unit = replacement["unit"]
                            reps_str = f"{reps_val} reps" if unit == "reps" else str(reps_val)
                            new_ex = dict(replacement)
                            new_ex["active_reps"] = reps_str
                            new_ex["active_level"] = fitness_level
                            st.session_state[plan_key]["exercises"][i] = new_ex
                            st.rerun()
                else:
                    st.caption("No swaps available in this category")

            with col_remove:
                if st.button("🗑", key=f"remove_ex_{i}_{client_id}",
                             help="Remove this exercise"):
                    st.session_state[plan_key]["exercises"].pop(i)
                    st.rerun()

    # Add exercise
    st.markdown("**➕ Add an exercise:**")
    col_add_cat, col_add_ex, col_add_btn = st.columns([2, 3, 1])
    with col_add_cat:
        add_cat = st.selectbox("Category", ["cardio", "core", "strength", "flexibility"],
                               key=f"add_cat_{client_id}")
    with col_add_ex:
        add_options = [
            e["name"] for e in EXERCISES
            if e["category"] == add_cat and e["name"] not in {x["name"] for x in exercises}
        ]
        if add_options:
            add_choice = st.selectbox("Exercise", add_options, key=f"add_choice_{client_id}")
        else:
            st.caption("All exercises in this category already added")
            add_choice = None
    with col_add_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if add_choice and st.button("Add", key=f"add_ex_btn_{client_id}"):
            new_ex = next(e for e in EXERCISES if e["name"] == add_choice)
            reps_val = new_ex["reps"].get(fitness_level, new_ex["reps"].get("Moderate"))
            reps_str = f"{reps_val} reps" if new_ex["unit"] == "reps" else str(reps_val)
            entry = dict(new_ex)
            entry["active_reps"] = reps_str
            entry["active_level"] = fitness_level
            st.session_state[plan_key]["exercises"].append(entry)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — LIFESTYLE GUIDELINES
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🌿 Lifestyle Guidelines", expanded=False):
    st.markdown(
        "These guidelines have been selected based on the client's conditions and lifestyle. "
        "Remove any that don't apply, or add from the full library below."
    )

    guidelines = plan["guidelines"]

    for i, g in enumerate(guidelines):
        col_g, col_del = st.columns([10, 1])
        with col_g:
            css_class = "highlight-rule" if g.get("highlight") else "normal-rule"
            st.markdown(
                f"<span class='{css_class}'>{g['icon']} {g['text']}</span>",
                unsafe_allow_html=True
            )
        with col_del:
            if st.button("✕", key=f"del_guide_{i}_{client_id}",
                         help="Remove this guideline"):
                st.session_state[plan_key]["guidelines"].pop(i)
                st.rerun()

    # Add guideline from library
    st.markdown("---")
    st.markdown("**➕ Add a guideline from library:**")
    current_texts = {g["text"] for g in guidelines}
    add_guide_options = [
        f"{g['icon']} {g['text'][:80]}..." if len(g["text"]) > 80 else f"{g['icon']} {g['text']}"
        for g in LIFESTYLE_GUIDELINES if g["text"] not in current_texts
    ]
    add_guide_map = {
        (f"{g['icon']} {g['text'][:80]}..." if len(g["text"]) > 80 else f"{g['icon']} {g['text']}"): g
        for g in LIFESTYLE_GUIDELINES if g["text"] not in current_texts
    }

    if add_guide_options:
        col_gadd, col_gbtn = st.columns([5, 1])
        with col_gadd:
            guide_choice = st.selectbox(
                "Select guideline", add_guide_options,
                key=f"add_guide_sel_{client_id}"
            )
        with col_gbtn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key=f"add_guide_btn_{client_id}"):
                st.session_state[plan_key]["guidelines"].append(
                    dict(add_guide_map[guide_choice])
                )
                st.rerun()
    else:
        st.caption("All guidelines from library are already included")

    # Custom guideline
    st.markdown("**✏️ Or write a custom guideline:**")
    custom_icon = st.text_input("Icon (emoji)", value="💡", max_chars=4,
                                 key=f"custom_icon_{client_id}")
    custom_text = st.text_area("Guideline text", key=f"custom_text_{client_id}",
                                placeholder="Enter a personalised guideline for this client...")
    if st.button("Add custom guideline", key=f"add_custom_guide_{client_id}"):
        if custom_text.strip():
            st.session_state[plan_key]["guidelines"].append({
                "icon": custom_icon or "💡",
                "text": custom_text.strip(),
                "highlight": False,
                "conditions": [],
                "lifestyle_tags": [],
            })
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — AVOID COMPLETELY
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🚫 Avoid Completely", expanded=False):
    st.markdown("Review the avoid list. Add or remove items as needed for this client.")

    avoid_items = plan["avoid_items"]

    # Display as removable tags
    cols = st.columns(2)
    for i, item in enumerate(avoid_items):
        with cols[i % 2]:
            col_tag, col_x = st.columns([5, 1])
            with col_tag:
                st.markdown(
                    f"<span class='avoid-tag'>{item}</span>",
                    unsafe_allow_html=True
                )
            with col_x:
                if st.button("✕", key=f"del_avoid_{i}_{client_id}"):
                    st.session_state[plan_key]["avoid_items"].pop(i)
                    st.rerun()

    st.markdown("---")
    # Add from library
    current_avoids = set(avoid_items)
    avoid_add_options = [
        a["name"] for a in AVOID_ITEMS
        if a["name"] not in current_avoids
    ]
    if avoid_add_options:
        col_aadd, col_abtn = st.columns([5, 1])
        with col_aadd:
            avoid_choice = st.selectbox("Add from library", avoid_add_options,
                                         key=f"add_avoid_sel_{client_id}")
        with col_abtn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key=f"add_avoid_btn_{client_id}"):
                st.session_state[plan_key]["avoid_items"].append(avoid_choice)
                st.rerun()

    # Custom avoid item
    col_custom_avoid, col_custom_btn = st.columns([5, 1])
    with col_custom_avoid:
        custom_avoid = st.text_input("Or type a custom item to avoid",
                                      key=f"custom_avoid_{client_id}",
                                      placeholder="e.g. Mango (high sugar for this client)")
    with col_custom_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key=f"add_custom_avoid_{client_id}"):
            if custom_avoid.strip() and custom_avoid.strip() not in current_avoids:
                st.session_state[plan_key]["avoid_items"].append(custom_avoid.strip())
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — SNACK SWAPS
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🥜 Snack Swap Options", expanded=False):
    st.markdown(
        "These snack options are tailored to the client's conditions and diet type. "
        "These appear in the PDF as alternatives to their main meal plan snacks."
    )

    snacks = plan["snacks"]
    is_veg = diet_type in ("Vegetarian", "Vegan", "Eggetarian")

    for i, snack in enumerate(snacks):
        with st.container():
            col_snack, col_del_snack = st.columns([10, 1])
            with col_snack:
                st.markdown(
                    f"<div class='snack-card'>"
                    f"<b>{snack['name']}</b><br>"
                    f"<span style='color:#4B5563;font-size:0.85rem'>{snack['desc']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_del_snack:
                if st.button("✕", key=f"del_snack_{i}_{client_id}"):
                    st.session_state[plan_key]["snacks"].pop(i)
                    st.rerun()

    # Add snack
    st.markdown("---")
    current_snack_names = {s["name"] for s in snacks}
    snack_add_options = [
        s for s in SNACK_OPTIONS
        if s["name"] not in current_snack_names
        and (not is_veg or s["veg"])
    ]
    if snack_add_options:
        snack_display = {f"{s['name']} — {s['desc']}": s for s in snack_add_options}
        col_sadd, col_sbtn = st.columns([6, 1])
        with col_sadd:
            snack_choice = st.selectbox(
                "Add snack from library",
                list(snack_display.keys()),
                key=f"add_snack_sel_{client_id}"
            )
        with col_sbtn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key=f"add_snack_btn_{client_id}"):
                st.session_state[plan_key]["snacks"].append(
                    dict(snack_display[snack_choice])
                )
                st.rerun()

    # Custom snack
    col_sc, col_sd, col_sdbtn = st.columns([3, 4, 1])
    with col_sc:
        custom_snack_name = st.text_input("Custom snack name",
                                           key=f"custom_snack_name_{client_id}")
    with col_sd:
        custom_snack_desc = st.text_input("Why it works (description)",
                                           key=f"custom_snack_desc_{client_id}")
    with col_sdbtn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key=f"add_custom_snack_{client_id}"):
            if custom_snack_name.strip():
                st.session_state[plan_key]["snacks"].append({
                    "name": custom_snack_name.strip(),
                    "desc": custom_snack_desc.strip(),
                    "conditions": [],
                    "veg": True,
                })
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SAVE REMINDER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
col_s1, col_s2 = st.columns([3, 1])
with col_s2:
    if st.button("💾 Save plan", type="primary", key="save_plan_bottom"):
        save_personalization(client_id, st.session_state[plan_key])
        st.success("✅ Plan saved! It will be used when generating the PDF.")
with col_s1:
    st.caption(
        "Save before generating the PDF. The plan is client-specific and "
        "persists across sessions."
    )
