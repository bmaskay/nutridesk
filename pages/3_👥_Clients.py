"""
3_Clients.py — Client Management (v2)
Side-by-side layout: client list (left) + tabbed detail panel (right).
All client interactions — progress, exercise, edits — happen here.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
from utils.database import (
    get_all_clients, get_client, delete_client,
    add_session, get_sessions,
    add_biomarkers, get_biomarkers,
    get_personalization, save_personalization,
)
from utils.calculations import full_assessment, calculate_bmi, bmi_category
from utils.personalization import build_personalized_plan, _parse_conditions
from utils.personalization_library import EXERCISES, LIFESTYLE_GUIDELINES, AVOID_ITEMS, SNACK_OPTIONS
from utils.header import render_header

render_header("Clients")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="metric-container"] {
    background:#F9F5EF; border:1px solid #E5D9CC;
    border-radius:10px; padding:10px 14px;
  }
  .target-bar {
    background:#F0E8DC; border-radius:8px; padding:10px 14px;
    border:1px solid #E5D9CC; margin-bottom:12px;
  }
  .bmi-pill {
    display:inline-block; border-radius:10px; padding:2px 8px;
    font-size:0.70rem; font-weight:600;
  }
  .ex-card {
    background:#FBF7F2; border:1px solid #E5D9CC; border-radius:10px;
    padding:12px 14px; margin-bottom:8px;
  }
  .ex-label {
    font-size:0.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:1px; color:#40916C; margin-bottom:2px;
  }
  .highlight-rule {
    background:#D8F3DC; border-radius:6px; padding:6px 12px;
    color:#1B4332; font-weight:600; font-size:0.88rem;
    display:block; margin-bottom:6px;
  }
  .normal-rule {
    background:#F9F5F0; border-radius:6px; padding:6px 12px;
    color:#374151; font-size:0.88rem; display:block; margin-bottom:6px;
  }
  .avoid-tag {
    background:#FEE2E2; color:#991B1B; border-radius:4px;
    padding:2px 8px; font-size:0.78rem; font-weight:600;
    display:inline-block; margin:3px;
  }
  .snack-card {
    background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px;
    padding:10px 14px; margin-bottom:8px;
  }
  .mod-note {
    background:#FEF9C3; border-radius:6px; padding:6px 10px;
    font-size:0.80rem; color:#713F12; margin-top:4px;
  }
  .section-banner {
    background:linear-gradient(135deg,#2D6A4F 0%,#40916C 100%);
    color:white; border-radius:10px; padding:10px 16px;
    font-weight:700; font-size:1.0rem; margin-bottom:12px;
  }
  .note-card {
    background:#F9F5EF; border:1px solid #E5D9CC; border-radius:8px;
    padding:8px 12px; margin-bottom:6px; font-size:0.85rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Load clients ──────────────────────────────────────────────────────────────
clients_all = get_all_clients()

if not clients_all:
    st.info("No clients yet. Add your first client via 📋 New Client.")
    if st.button("➕ Add Client"):
        st.switch_page("pages/1_📋_Intake.py")
    st.stop()

# ── Top bar ───────────────────────────────────────────────────────────────────
top1, top2, top3 = st.columns([2.5, 1.5, 1])
with top1:
    search_q = st.text_input("🔍", placeholder="Search by name, goal, diet…",
                              label_visibility="collapsed")
with top2:
    sort_by = st.selectbox(
        "Sort", ["Date added (newest)", "Name A–Z", "BMI ↑", "BMI ↓"],
        label_visibility="collapsed"
    )
with top3:
    if st.button("➕ New Client", use_container_width=True):
        st.session_state.pop("edit_client_id", None)
        st.switch_page("pages/1_📋_Intake.py")

# ── Filter + sort ─────────────────────────────────────────────────────────────
clients = list(clients_all)

if search_q:
    q = search_q.lower()
    clients = [c for c in clients if
               q in c["name"].lower()
               or q in (c.get("goal") or "").lower()
               or q in (c.get("diet_type") or "").lower()]

if sort_by == "Name A–Z":
    clients = sorted(clients, key=lambda c: c["name"].lower())
elif sort_by == "BMI ↑":
    clients = sorted(clients, key=lambda c: calculate_bmi(
        c.get("weight_kg") or 0, c.get("height_cm") or 1))
elif sort_by == "BMI ↓":
    clients = sorted(clients, key=lambda c: calculate_bmi(
        c.get("weight_kg") or 0, c.get("height_cm") or 1), reverse=True)

# ── Selected client state ─────────────────────────────────────────────────────
if "cl_selected_id" not in st.session_state:
    st.session_state["cl_selected_id"] = clients[0]["id"] if clients else None

# Reset if selected client was deleted
valid_ids = {c["id"] for c in clients_all}
if st.session_state["cl_selected_id"] not in valid_ids:
    st.session_state["cl_selected_id"] = clients[0]["id"] if clients else None

selected_id = st.session_state["cl_selected_id"]

if "cl_confirm_delete_id" not in st.session_state:
    st.session_state["cl_confirm_delete_id"] = None

# ── Layout ────────────────────────────────────────────────────────────────────
col_list, col_detail = st.columns([1, 2.5], gap="medium")

# =============================================================================
# LEFT: CLIENT LIST
# =============================================================================
with col_list:
    st.markdown(f"**{len(clients)} client(s)**")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    for c in clients:
        bmi_val = calculate_bmi(c.get("weight_kg") or 0, c.get("height_cm") or 1)
        bmi_bg, bmi_fg = (
            ("#D8F3DC", "#2D6A4F") if bmi_val < 23
            else ("#FEF3C7", "#D97706") if bmi_val < 27.5
            else ("#FEE2E2", "#DC2626")
        )
        is_selected = c["id"] == selected_id

        with st.container(border=True):
            name_col, bmi_col = st.columns([3, 1.3])
            with name_col:
                name_prefix = "🟢 " if is_selected else ""
                name_color  = "#2D6A4F" if is_selected else "#1A1A1A"
                st.markdown(
                    f"<div style='font-size:1rem;font-weight:700;color:{name_color}'>"
                    f"{name_prefix}{c['name']}</div>",
                    unsafe_allow_html=True,
                )
            with bmi_col:
                st.markdown(
                    f"<div style='text-align:right'>"
                    f"<span style='background:{bmi_bg};color:{bmi_fg};border-radius:8px;"
                    f"padding:2px 9px;font-size:0.72rem;font-weight:600'>BMI {bmi_val}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"<div style='font-size:0.82rem;color:#6B7280;margin:2px 0 12px'>"
                f"{c.get('goal','—')}</div>",
                unsafe_allow_html=True,
            )

            btn_sel, btn_del = st.columns([4, 1])
            with btn_sel:
                if st.button(
                    "▶ Selected" if is_selected else "Select",
                    key=f"sel_{c['id']}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["cl_selected_id"] = c["id"]
                    st.session_state["cl_confirm_delete_id"] = None
                    st.rerun()
            with btn_del:
                if st.button("🗑", key=f"delbtn_{c['id']}", use_container_width=True):
                    st.session_state["cl_confirm_delete_id"] = c["id"]
                    st.rerun()

            # Inline delete confirmation
            if st.session_state["cl_confirm_delete_id"] == c["id"]:
                full_del = get_client(c["id"])
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.warning(f"Delete **{full_del['name']}**? All data removed permanently.")
                typed = st.text_input(
                    "Type exact name to confirm:",
                    key=f"deltype_{c['id']}",
                    placeholder=full_del["name"],
                )
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("✅ Delete", key=f"delconfirm_{c['id']}", type="primary", use_container_width=True):
                        if typed.strip().lower() == full_del["name"].strip().lower():
                            delete_client(c["id"])
                            st.session_state["cl_confirm_delete_id"] = None
                            if st.session_state.get("cl_selected_id") == c["id"]:
                                remaining = [x for x in clients_all if x["id"] != c["id"]]
                                st.session_state["cl_selected_id"] = remaining[0]["id"] if remaining else None
                            st.rerun()
                        else:
                            st.error("Name doesn't match.")
                with dc2:
                    if st.button("✖ Cancel", key=f"delcancel_{c['id']}", use_container_width=True):
                        st.session_state["cl_confirm_delete_id"] = None
                        st.rerun()

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# =============================================================================
# RIGHT: CLIENT DETAIL PANEL
# =============================================================================
with col_detail:
    if not selected_id:
        st.info("Select a client from the left to view their details.")
        st.stop()

    client = get_client(selected_id)
    if not client:
        st.warning("Client not found.")
        st.stop()

    assessment = full_assessment(client)

    # Client header
    st.markdown(
        f"<div class='target-bar'>"
        f"<b style='font-size:1.1rem'>{client['name']}</b> &nbsp;·&nbsp; "
        f"BMI {assessment['bmi']} ({assessment['bmi_category']}) &nbsp;·&nbsp; "
        f"Target: <b>{assessment['target_calories']} kcal</b> &nbsp;·&nbsp; "
        f"P: {assessment['protein_g']}g · C: {assessment['carbs_g']}g · F: {assessment['fat_g']}g"
        f"</div>",
        unsafe_allow_html=True,
    )

    tab_overview, tab_progress, tab_exercise = st.tabs([
        "📋 Overview & Edit",
        "📈 Progress & Weight",
        "💪 Exercise Plan",
    ])

    # =========================================================================
    # TAB 1 — OVERVIEW & EDIT
    # =========================================================================
    with tab_overview:
        age     = assessment["age"]
        bmi     = assessment["bmi"]
        bmi_cat = assessment["bmi_category"]
        bmi_color = (
            "#D8F3DC;color:#2D6A4F" if bmi < 23
            else "#FEF3C7;color:#D97706" if bmi < 27.5
            else "#FEE2E2;color:#DC2626"
        )

        qa1, qa2, _ = st.columns([1, 1, 1])
        with qa1:
            if st.button("✏️ Full Edit", key="ov_edit_btn", use_container_width=True):
                st.session_state["edit_client_id"] = selected_id
                st.switch_page("pages/1_📋_Intake.py")
        with qa2:
            if st.button("📊 Plan Builder", key="ov_plan_btn", use_container_width=True):
                st.session_state["active_client_id"] = selected_id
                st.switch_page("pages/plan_builder.py")

        st.markdown("---")

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown("**Contact**")
            st.write(f"📧 {client.get('email','—')}")
            st.write(f"📱 {client.get('phone','—')}")
            st.write(f"🎂 DOB: {client.get('dob','—')} ({age} yrs)")

            st.markdown("**Body Stats**")
            st.write(f"Height: {client.get('height_cm','—')} cm")
            st.write(f"Weight: {client.get('weight_kg','—')} kg")
            st.write(f"Ideal: {assessment['ideal_weight_low']}–{assessment['ideal_weight_high']} kg")
            st.markdown(
                f"<span class='bmi-pill' style='background:{bmi_color}'>"
                f"BMI {bmi} — {bmi_cat}</span>",
                unsafe_allow_html=True,
            )

        with d2:
            st.markdown("**Lifestyle**")
            st.write(f"Activity: {client.get('activity_level','—')}")
            st.write(f"Sleep: {client.get('sleep_hrs','—')} hrs")
            st.write(f"Stress: {client.get('stress_level','—')}")
            st.write(f"Water: {client.get('water_intake_l', client.get('water_intake_L','—'))} L/day")
            st.write(f"Occupation: {client.get('occupation','—')}")

            st.markdown("**Medical**")
            conds = client.get("medical_conditions", [])
            st.write(", ".join(conds) if conds else "None reported")

            st.markdown("**Goal**")
            st.write(client.get("goal", "—"))

        with d3:
            st.markdown("**Nutrition Targets**")
            st.write(f"BMR: {assessment['bmr']} kcal")
            st.write(f"TDEE: {assessment['tdee']} kcal")
            st.write(f"Target: **{assessment['target_calories']} kcal**")
            st.write(f"Protein: {assessment['protein_g']}g")
            st.write(f"Carbs: {assessment['carbs_g']}g")
            st.write(f"Fat: {assessment['fat_g']}g")
            st.write(f"Water: {assessment['hydration_L']} L")

            st.markdown("**Food Preferences**")
            st.write(f"Diet: {client.get('diet_type','—')}")
            cuisines = client.get("cuisine_pref", [])
            st.write(f"Cuisines: {', '.join(cuisines) if cuisines else '—'}")
            allergies = client.get("allergies", [])
            st.write(f"Allergies: {', '.join(allergies) if allergies else 'None'}")

        # Session notes
        st.markdown("---")
        st.markdown("#### 📝 Session Notes")
        _sessions_ov = get_sessions(selected_id)

        if _sessions_ov:
            for _s in reversed(_sessions_ov[-5:]):
                _date_s = _s.get("session_date", "")
                _note   = (_s.get("notes") or "").strip()
                _wt     = _s.get("weight_kg")
                _wt_str = f" · {_wt} kg" if _wt else ""
                if _note or _wt:
                    _body = _note if _note else "<i style='color:#9CA3AF'>No text note</i>"
                    st.markdown(
                        f"<div class='note-card'>"
                        f"<b style='color:#40916C'>{_date_s}{_wt_str}</b><br>{_body}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                "<div style='color:#9CA3AF;font-size:0.85rem'>No session notes yet.</div>",
                unsafe_allow_html=True,
            )

        nc1, nc2, nc3 = st.columns([2, 1, 1])
        with nc1:
            _new_note = st.text_input(
                "Note", key=f"ov_note_{selected_id}",
                placeholder="e.g. Client responding well to plan"
            )
        with nc2:
            _new_wt = st.number_input(
                "Weight (kg)", key=f"ov_wt_{selected_id}",
                min_value=0.0, max_value=300.0, value=0.0, step=0.1, format="%.1f"
            )
        with nc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Add Note", key=f"ov_savenote_{selected_id}"):
                wt_val = _new_wt if _new_wt > 0 else None
                if _new_note.strip() or wt_val:
                    add_session(selected_id, wt_val, _new_note.strip())
                    st.success("Note saved!")
                    st.rerun()
                else:
                    st.warning("Enter a note or weight first.")

    # =========================================================================
    # TAB 2 — PROGRESS & WEIGHT
    # =========================================================================
    with tab_progress:
        import pandas as pd
        import altair as alt

        sessions        = get_sessions(selected_id)
        starting_weight = client.get("weight_kg") or 0
        weight_sessions = [s for s in sessions if s.get("weight_kg")]
        current_weight  = weight_sessions[-1]["weight_kg"] if weight_sessions else starting_weight
        total_lost      = round(starting_weight - current_weight, 1)
        current_bmi     = calculate_bmi(current_weight, client.get("height_cm") or 1)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Starting",  f"{starting_weight} kg")
        m2.metric("Current",   f"{current_weight} kg",
                  delta=f"{-total_lost:.1f} kg" if total_lost != 0 else None,
                  delta_color="normal")
        m3.metric("Lost",      f"{abs(total_lost)} kg" if total_lost > 0 else "—")
        m4.metric("BMI",       f"{current_bmi}", bmi_category(current_bmi))
        m5.metric("Check-ins", len(weight_sessions))

        # Trend interpretation
        if len(weight_sessions) >= 2:
            from datetime import datetime as _dt
            _ideal_low  = assessment["ideal_weight_low"]
            _ideal_high = assessment["ideal_weight_high"]
            _goal       = client.get("goal", "")

            try:
                _first_date = _dt.fromisoformat(weight_sessions[0]["session_date"]).date()
                _last_date  = _dt.fromisoformat(weight_sessions[-1]["session_date"]).date()
            except Exception:
                _first_date = _last_date = date.today()

            _weeks  = max((_last_date - _first_date).days / 7, 0.01)
            _change = round((weight_sessions[-1]["weight_kg"] or 0) - (weight_sessions[0]["weight_kg"] or 0), 1)
            _rate   = round(_change / _weeks, 2)

            _interp = []
            if total_lost > 0:
                if -0.6 <= _rate <= -0.1:
                    _interp.append(
                        f"✅ **On track** — {client['name']} has lost **{total_lost} kg** "
                        f"over {_weeks:.1f} weeks (~{abs(_rate)} kg/week), within the healthy rate."
                    )
                elif _rate < -0.6:
                    _interp.append(
                        f"⚡ **Fast loss** — {abs(_rate)} kg/week exceeds the 0.5 kg/week ceiling. "
                        f"Check protein intake and watch for signs of muscle loss."
                    )
                else:
                    _interp.append(
                        f"📉 **Slow progress** — {abs(_rate)} kg/week. "
                        f"May reflect water fluctuation or a need to reassess calorie targets."
                    )
            elif total_lost < -0.5:
                _interp.append(
                    f"📈 **Weight gain of {abs(total_lost)} kg** since starting. "
                    f"Review adherence and calorie targets."
                )
            else:
                _interp.append(
                    f"⚖️ **Weight stable** — less than 0.5 kg change. "
                    + ("Goal met for maintenance." if "Maintain" in _goal
                       else "Check adherence if fat loss is the goal.")
                )

            if current_weight > (_ideal_high or 0) + 1:
                _gap = round(current_weight - _ideal_high, 1)
                if _rate and _rate < 0:
                    _wks = round(_gap / abs(_rate))
                    _interp.append(
                        f"🎯 **{_gap} kg from healthy range** ({_ideal_low}–{_ideal_high} kg). "
                        f"At this rate, ~{_wks} more weeks."
                    )
                else:
                    _interp.append(
                        f"🎯 **{_gap} kg from healthy range** ({_ideal_low}–{_ideal_high} kg)."
                    )
            elif (_ideal_low or 0) <= current_weight <= (_ideal_high or 999):
                _interp.append(
                    f"🌟 **{client['name']} is within the healthy weight range** "
                    f"({_ideal_low}–{_ideal_high} kg)."
                )

            for _part in _interp:
                st.markdown(
                    f"<div style='background:#F0F9FF;border-left:3px solid #38BDF8;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;margin-bottom:6px;"
                    f"font-size:0.88rem;color:#0C4A6E'>{_part}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        ptab_wt, ptab_bio = st.tabs(["⚖️ Weight Tracking", "🩺 Biomarkers"])

        # Weight Tracking
        with ptab_wt:
            ideal_l = assessment["ideal_weight_low"]
            ideal_h = assessment["ideal_weight_high"]

            col_form, col_chart = st.columns([1, 2])
            with col_form:
                st.markdown("#### Log a Check-in")
                with st.form(f"cl_checkin_{selected_id}"):
                    ci_wt = st.number_input(
                        "Weight (kg)", min_value=30.0, max_value=250.0,
                        value=float(current_weight) if current_weight else 70.0,
                        step=0.1, format="%.1f"
                    )
                    ci_notes  = st.text_area(
                        "Notes", placeholder="e.g. Feeling great, slightly bloated…", height=80
                    )
                    submit_ci = st.form_submit_button("✅ Save Check-in", use_container_width=True)

                if submit_ci:
                    add_session(selected_id, ci_wt, ci_notes)
                    st.success(f"Check-in saved: {ci_wt} kg")
                    st.rerun()

                st.info(f"🎯 Ideal range: **{ideal_l} – {ideal_h} kg**")

            with col_chart:
                st.markdown("#### Weight Trend")
                if not weight_sessions:
                    st.info("No check-ins with weight logged yet.")
                else:
                    df = pd.DataFrame(weight_sessions)
                    df["session_date"] = pd.to_datetime(df["session_date"])
                    df = df.sort_values("session_date")

                    base = alt.Chart(df).mark_line(
                        color="#2D6A4F", strokeWidth=2.5, point=True
                    ).encode(
                        x=alt.X("session_date:T", title="Date",
                                axis=alt.Axis(format="%d %b")),
                        y=alt.Y(
                            "weight_kg:Q", title="Weight (kg)",
                            scale=alt.Scale(
                                domain=[max(30, float(df["weight_kg"].min()) - 3),
                                        float(df["weight_kg"].max()) + 3]
                            )
                        ),
                        tooltip=[
                            alt.Tooltip("session_date:T", title="Date", format="%d %b %Y"),
                            alt.Tooltip("weight_kg:Q", title="Weight (kg)"),
                        ]
                    )
                    target_df = pd.DataFrame({
                        "date": [df["session_date"].min(), df["session_date"].max()],
                        "low":  [ideal_l, ideal_l],
                        "high": [ideal_h, ideal_h],
                    })
                    band = alt.Chart(target_df).mark_area(
                        color="#D8F3DC", opacity=0.4
                    ).encode(x="date:T", y="low:Q", y2="high:Q")

                    st.altair_chart((band + base).properties(height=280), use_container_width=True)

                    disp = df[["session_date", "weight_kg", "notes"]].copy()
                    disp.columns = ["Date", "Weight (kg)", "Notes"]
                    disp["Date"] = disp["Date"].dt.strftime("%d %b %Y")
                    st.dataframe(
                        disp.sort_values("Date", ascending=False),
                        use_container_width=True, hide_index=True
                    )

        # Biomarkers
        with ptab_bio:
            col_bform, col_bdata = st.columns([1, 2])

            with col_bform:
                st.markdown("#### Log Biomarkers")
                with st.form(f"cl_bm_{selected_id}"):
                    b_date_val      = st.date_input("Test Date", value=date.today())
                    fasting_glucose = st.number_input("Fasting Glucose (mmol/L)", 0.0, 30.0, 0.0, step=0.1)
                    hba1c           = st.number_input("HbA1c (%)",                0.0, 20.0, 0.0, step=0.1)
                    cholesterol     = st.number_input("Total Cholesterol (mmol/L)",0.0, 15.0, 0.0, step=0.1)
                    hdl             = st.number_input("HDL (mmol/L)",              0.0,  5.0, 0.0, step=0.1)
                    ldl             = st.number_input("LDL (mmol/L)",              0.0, 10.0, 0.0, step=0.1)
                    triglycerides   = st.number_input("Triglycerides (mmol/L)",    0.0, 15.0, 0.0, step=0.1)
                    tsh             = st.number_input("TSH (mIU/L)",               0.0, 20.0, 0.0, step=0.01)
                    vitamin_d       = st.number_input("Vitamin D (nmol/L)",        0.0,300.0, 0.0, step=1.0)
                    b12             = st.number_input("B12 (pmol/L)",              0.0,1500.0,0.0, step=1.0)
                    ferritin        = st.number_input("Ferritin (μg/L)",           0.0,500.0, 0.0, step=1.0)
                    b_notes         = st.text_area("Notes", height=80)
                    submit_bm       = st.form_submit_button("✅ Save Biomarkers", use_container_width=True)

                if submit_bm:
                    bm_data = {"recorded_date": str(b_date_val), "notes": b_notes}
                    for k, v in [
                        ("fasting_glucose", fasting_glucose), ("hba1c", hba1c),
                        ("total_cholesterol", cholesterol), ("hdl", hdl), ("ldl", ldl),
                        ("triglycerides", triglycerides), ("tsh", tsh),
                        ("vitamin_d", vitamin_d), ("b12", b12), ("ferritin", ferritin),
                    ]:
                        if v > 0:
                            bm_data[k] = v
                    add_biomarkers(selected_id, bm_data)
                    st.success("Biomarkers saved!")
                    st.rerun()

            with col_bdata:
                st.markdown("#### Biomarker History")
                biomarkers = get_biomarkers(selected_id)
                if not biomarkers:
                    st.info("No biomarker records yet.")
                else:
                    bdf = pd.DataFrame(biomarkers)
                    bdf["recorded_date"] = pd.to_datetime(bdf["recorded_date"])
                    bdf = bdf.sort_values("recorded_date", ascending=False)

                    marker_cols = [
                        "fasting_glucose", "hba1c", "total_cholesterol",
                        "hdl", "ldl", "triglycerides", "tsh", "vitamin_d", "b12", "ferritin"
                    ]
                    display_cols = ["recorded_date"]
                    for col in marker_cols:
                        if col in bdf.columns and bdf[col].notna().any() and (bdf[col] > 0).any():
                            display_cols.append(col)

                    show_df = bdf[display_cols + (["notes"] if "notes" in bdf.columns else [])].copy()
                    show_df["recorded_date"] = show_df["recorded_date"].dt.strftime("%d %b %Y")
                    show_df.columns = [c.replace("_", " ").title() for c in show_df.columns]
                    st.dataframe(show_df, use_container_width=True, hide_index=True)

                    with st.expander("📋 Reference Ranges"):
                        st.markdown("""
| Marker | Normal Range |
|---|---|
| Fasting Glucose | 3.9–5.5 mmol/L |
| HbA1c | < 5.7% (non-diabetic) |
| Total Cholesterol | < 5.2 mmol/L |
| HDL | > 1.0 (M) / > 1.2 (F) mmol/L |
| LDL | < 3.4 mmol/L |
| Triglycerides | < 1.7 mmol/L |
| TSH | 0.4–4.0 mIU/L |
| Vitamin D | 75–200 nmol/L |
| B12 | 200–900 pmol/L |
| Ferritin | 30–300 μg/L |
""")

    # =========================================================================
    # TAB 3 — EXERCISE PLAN
    # =========================================================================
    with tab_exercise:
        fitness_level = client.get("fitness_level") or "Moderate"
        diet_type     = client.get("diet_type", "Non-vegetarian")
        _ex_key       = f"cl_ex_{selected_id}"

        if _ex_key not in st.session_state:
            saved_ex = get_personalization(selected_id)
            if saved_ex and saved_ex.get("exercises"):
                st.session_state[_ex_key] = saved_ex
            else:
                st.session_state[_ex_key] = build_personalized_plan(client)

        ex_plan   = st.session_state[_ex_key]
        conds_str = ", ".join(client.get("medical_conditions") or []) or "None"

        st.markdown(
            f"<div class='section-banner'>👤 {client['name']} &nbsp;·&nbsp; "
            f"Fitness: {fitness_level} &nbsp;·&nbsp; "
            f"Diet: {diet_type} &nbsp;·&nbsp; Conditions: {conds_str}</div>",
            unsafe_allow_html=True,
        )

        col_ref, col_sav = st.columns([3, 1])
        with col_ref:
            if st.button("🔄 Re-generate from client profile", key=f"cl_regen_{selected_id}"):
                st.session_state[_ex_key] = build_personalized_plan(client)
                st.rerun()
        with col_sav:
            if st.button("💾 Save", type="primary", key=f"cl_save_ex_top_{selected_id}"):
                save_personalization(selected_id, st.session_state[_ex_key])
                st.success("Saved!")
                st.rerun()

        st.markdown("---")

        # Exercises
        with st.expander("🏋️ Exercise Circuit", expanded=True):
            exercises      = ex_plan["exercises"]
            selected_names = {e["name"] for e in exercises}

            for i, ex in enumerate(exercises):
                col_ex, col_swap, col_rm = st.columns([4, 3, 1])
                with col_ex:
                    reps = ex.get("active_reps", str(ex["reps"].get(fitness_level, "—")))
                    st.markdown(
                        f"<div class='ex-card'>"
                        f"<div class='ex-label'>{ex['category'].upper()}</div>"
                        f"<div style='font-weight:700'>{ex['name']}</div>"
                        f"<div style='font-size:0.84rem;color:#4B5563'>{reps}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if ex.get("modification"):
                        client_conds = _parse_conditions(client)
                        if any(cc in client_conds for cc in ex.get("modification_for", [])):
                            st.markdown(
                                f"<div class='mod-note'>⚠️ {ex['modification']}</div>",
                                unsafe_allow_html=True,
                            )
                with col_swap:
                    swap_opts = [
                        e["name"] for e in EXERCISES
                        if e["category"] == ex["category"] and e["name"] not in selected_names
                    ]
                    if swap_opts:
                        sc = st.selectbox(
                            "Swap with", ["— keep —"] + swap_opts,
                            key=f"cl_swex_{i}_{selected_id}"
                        )
                        if sc != "— keep —" and st.button("Apply", key=f"cl_apex_{i}_{selected_id}"):
                            repl = next(e for e in EXERCISES if e["name"] == sc)
                            rv   = repl["reps"].get(fitness_level, repl["reps"].get("Moderate"))
                            rs   = f"{rv} reps" if repl["unit"] == "reps" else str(rv)
                            ne   = dict(repl)
                            ne["active_reps"]  = rs
                            ne["active_level"] = fitness_level
                            st.session_state[_ex_key]["exercises"][i] = ne
                            st.rerun()
                    else:
                        st.caption("No swaps in this category")
                with col_rm:
                    if st.button("🗑", key=f"cl_rmex_{i}_{selected_id}"):
                        st.session_state[_ex_key]["exercises"].pop(i)
                        st.rerun()

            st.markdown("**➕ Add exercise:**")
            ca, ce, cb = st.columns([2, 3, 1])
            with ca:
                add_cat = st.selectbox(
                    "Category", ["cardio", "core", "strength", "flexibility"],
                    key=f"cl_acat_{selected_id}", label_visibility="collapsed"
                )
            with ce:
                aopts = [
                    e["name"] for e in EXERCISES
                    if e["category"] == add_cat
                    and e["name"] not in {x["name"] for x in exercises}
                ]
                if aopts:
                    add_choice = st.selectbox(
                        "Exercise", aopts,
                        key=f"cl_achoice_{selected_id}", label_visibility="collapsed"
                    )
                else:
                    add_choice = None
                    st.caption("All exercises in this category already added")
            with cb:
                st.markdown("<br>", unsafe_allow_html=True)
                if add_choice and st.button("Add", key=f"cl_addbtn_{selected_id}"):
                    ne2   = next(e for e in EXERCISES if e["name"] == add_choice)
                    rv2   = ne2["reps"].get(fitness_level, ne2["reps"].get("Moderate"))
                    rs2   = f"{rv2} reps" if ne2["unit"] == "reps" else str(rv2)
                    entry = dict(ne2)
                    entry["active_reps"]  = rs2
                    entry["active_level"] = fitness_level
                    st.session_state[_ex_key]["exercises"].append(entry)
                    st.rerun()

        # Lifestyle Guidelines
        with st.expander("🌿 Lifestyle Guidelines", expanded=False):
            guidelines = ex_plan["guidelines"]

            for i, g in enumerate(guidelines):
                gc, gd = st.columns([10, 1])
                with gc:
                    cls = "highlight-rule" if g.get("highlight") else "normal-rule"
                    st.markdown(
                        f"<span class='{cls}'>{g['icon']} {g['text']}</span>",
                        unsafe_allow_html=True,
                    )
                with gd:
                    if st.button("✕", key=f"cl_dg_{i}_{selected_id}"):
                        st.session_state[_ex_key]["guidelines"].pop(i)
                        st.rerun()

            st.markdown("---")
            current_texts = {g["text"] for g in guidelines}
            add_gopts = {
                (f"{g['icon']} {g['text'][:80]}…" if len(g["text"]) > 80
                 else f"{g['icon']} {g['text']}"): g
                for g in LIFESTYLE_GUIDELINES if g["text"] not in current_texts
            }
            if add_gopts:
                gl1, gl2 = st.columns([5, 1])
                with gl1:
                    gc_choice = st.selectbox(
                        "Add from library", list(add_gopts.keys()),
                        key=f"cl_gsel_{selected_id}"
                    )
                with gl2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Add", key=f"cl_gadd_{selected_id}"):
                        st.session_state[_ex_key]["guidelines"].append(dict(add_gopts[gc_choice]))
                        st.rerun()

            ci2, ct2 = st.columns([1, 4])
            with ci2:
                cicon = st.text_input("Icon", value="💡", max_chars=4, key=f"cl_gicon_{selected_id}")
            with ct2:
                ctext = st.text_area(
                    "Custom guideline", key=f"cl_gtext_{selected_id}",
                    placeholder="Type a personalised guideline…"
                )
            if st.button("Add custom", key=f"cl_gcust_{selected_id}"):
                if ctext.strip():
                    st.session_state[_ex_key]["guidelines"].append({
                        "icon": cicon or "💡",
                        "text": ctext.strip(),
                        "highlight": False,
                        "conditions": [],
                        "lifestyle_tags": [],
                    })
                    st.rerun()

        # Avoid List
        with st.expander("🚫 Avoid Completely", expanded=False):
            avoid_items = ex_plan["avoid_items"]  # list of strings
            cur_avoids  = set(avoid_items)

            acols = st.columns(2)
            for i, item in enumerate(avoid_items):
                with acols[i % 2]:
                    st.markdown(
                        f"<span class='avoid-tag'>🚫 {item}</span>",
                        unsafe_allow_html=True,
                    )
                    if st.button("✕ Remove", key=f"cl_av_{i}_{selected_id}"):
                        st.session_state[_ex_key]["avoid_items"].pop(i)
                        st.rerun()

            st.markdown("---")
            av_opts = [a["name"] for a in AVOID_ITEMS if a["name"] not in cur_avoids]
            if av_opts:
                al1, al2 = st.columns([5, 1])
                with al1:
                    av_pick = st.selectbox(
                        "Add from library", av_opts, key=f"cl_avsel_{selected_id}"
                    )
                with al2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Add", key=f"cl_avadd_{selected_id}"):
                        st.session_state[_ex_key]["avoid_items"].append(av_pick)
                        st.rerun()

            ca2, cb2 = st.columns([5, 1])
            with ca2:
                cav = st.text_input(
                    "Custom avoid item", key=f"cl_cavcust_{selected_id}",
                    placeholder="e.g. Mango (high sugar for diabetics)"
                )
            with cb2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"cl_cavbtn_{selected_id}"):
                    if cav.strip() and cav.strip() not in cur_avoids:
                        st.session_state[_ex_key]["avoid_items"].append(cav.strip())
                        st.rerun()

        # Snack Options
        with st.expander("🥜 Snack Options", expanded=False):
            snacks  = ex_plan["snacks"]  # list of dicts: name + desc
            is_veg  = diet_type in ("Vegetarian", "Vegan", "Eggetarian")

            for i, snack in enumerate(snacks):
                sc1, sc2 = st.columns([10, 1])
                with sc1:
                    st.markdown(
                        f"<div class='snack-card'><b>{snack['name']}</b><br>"
                        f"<span style='color:#4B5563;font-size:0.85rem'>"
                        f"{snack.get('desc','')}</span></div>",
                        unsafe_allow_html=True,
                    )
                with sc2:
                    if st.button("✕", key=f"cl_sn_{i}_{selected_id}"):
                        st.session_state[_ex_key]["snacks"].pop(i)
                        st.rerun()

            cur_snacks = {s["name"] for s in snacks}
            sadd_opts  = {
                f"{s['name']} — {s['desc']}": s
                for s in SNACK_OPTIONS
                if s["name"] not in cur_snacks and (not is_veg or s.get("veg", True))
            }
            if sadd_opts:
                sl1, sl2 = st.columns([6, 1])
                with sl1:
                    sp = st.selectbox("Add snack", list(sadd_opts.keys()), key=f"cl_snasel_{selected_id}")
                with sl2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Add", key=f"cl_snaadd_{selected_id}"):
                        st.session_state[_ex_key]["snacks"].append(dict(sadd_opts[sp]))
                        st.rerun()

            sn1, sn2, sn3 = st.columns([3, 4, 1])
            with sn1:
                csn = st.text_input("Custom snack name", key=f"cl_csnname_{selected_id}")
            with sn2:
                csd = st.text_input("Why it works", key=f"cl_csndesc_{selected_id}")
            with sn3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"cl_csnadd_{selected_id}"):
                    if csn.strip():
                        st.session_state[_ex_key]["snacks"].append({
                            "name": csn.strip(), "desc": csd.strip(),
                            "conditions": [], "veg": True,
                        })
                        st.rerun()

        # Bottom save
        st.markdown("---")
        if st.button(
            "💾 Save Exercise & Lifestyle Plan", type="primary",
            key=f"cl_save_ex_bot_{selected_id}", use_container_width=True
        ):
            save_personalization(selected_id, st.session_state[_ex_key])
            st.success("✅ Exercise & Lifestyle plan saved — it will be included in the PDF.")
            st.rerun()
