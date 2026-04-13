"""
3_Clients.py — Client Management
View, search, edit and delete clients.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import get_all_clients, get_client, delete_client, add_session, get_sessions
from utils.calculations import full_assessment, calculate_age
from utils.header import render_header

render_header("Clients")

st.markdown("""
<style>
  .client-card { background: #FBF7F2; border: 1px solid #E5D9CC; border-radius: 12px;
                 padding: 16px 18px; margin-bottom: 12px; }
  .client-name { font-size: 1.05rem; font-weight: 700; color: #1A1A1A; }
  .client-meta { font-size: 0.82rem; color: #6B7280; margin-top: 2px; }
  .bmi-pill { display: inline-block; border-radius: 10px; padding: 2px 10px;
              font-size: 0.72rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 👥 Client Directory")
st.markdown("---")

clients = get_all_clients()

if not clients:
    st.info("No clients yet. Add your first client via 📋 New Client.")
    if st.button("➕ Add Client"):
        st.switch_page("pages/1_📋_Intake.py")
    st.stop()

# ── Search + sort + header actions ───────────────────────────────────────────

col_search, col_sort, col_add = st.columns([2.5, 1.5, 1])
with col_search:
    search_q = st.text_input("🔍 Search clients", placeholder="Name, goal, gender...")
with col_sort:
    sort_by = st.selectbox(
        "Sort by",
        ["Date added (newest)", "Date added (oldest)", "Name A–Z", "Name Z–A",
         "Goal", "BMI (low→high)", "BMI (high→low)"],
        label_visibility="collapsed",
    )
with col_add:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ New Client", width="stretch"):
        st.session_state.pop("edit_client_id", None)
        st.switch_page("pages/1_📋_Intake.py")

if search_q:
    q = search_q.lower()
    clients = [c for c in clients if
               q in c["name"].lower()
               or q in (c.get("goal") or "").lower()
               or q in (c.get("gender") or "").lower()]

# ── Apply sort ────────────────────────────────────────────────────────────────
from utils.calculations import calculate_bmi

if sort_by == "Date added (oldest)":
    clients = sorted(clients, key=lambda c: c.get("created_at", ""))
elif sort_by == "Name A–Z":
    clients = sorted(clients, key=lambda c: c["name"].lower())
elif sort_by == "Name Z–A":
    clients = sorted(clients, key=lambda c: c["name"].lower(), reverse=True)
elif sort_by == "Goal":
    clients = sorted(clients, key=lambda c: c.get("goal") or "")
elif sort_by == "BMI (low→high)":
    clients = sorted(clients, key=lambda c: calculate_bmi(
        c.get("weight_kg") or 0, c.get("height_cm") or 1))
elif sort_by == "BMI (high→low)":
    clients = sorted(clients, key=lambda c: calculate_bmi(
        c.get("weight_kg") or 0, c.get("height_cm") or 1), reverse=True)
# "Date added (newest)" is already the default DB order — no change needed

st.markdown(f"**{len(clients)} client(s)** &nbsp;·&nbsp; sorted by *{sort_by}*")
st.markdown("---")

# ── Confirm delete state ──────────────────────────────────────────────────────

if "confirm_delete_id" not in st.session_state:
    st.session_state["confirm_delete_id"] = None

# ── Client cards ──────────────────────────────────────────────────────────────

for c in clients:
    full = get_client(c["id"])
    if not full:
        continue
    assessment = full_assessment(full)
    bmi = assessment["bmi"]
    bmi_cat = assessment["bmi_category"]
    age = assessment["age"]

    bmi_color = "#D8F3DC;color:#2D6A4F" if bmi < 23 else "#FEF3C7;color:#D97706" if bmi < 27.5 else "#FEE2E2;color:#DC2626"

    with st.container():
        st.markdown(
            f"<div class='client-card'>"
            f"<div class='client-name'>{full['name']}</div>"
            f"<div class='client-meta'>"
            f"{full.get('gender','—')} &nbsp;·&nbsp; {age} yrs &nbsp;·&nbsp; "
            f"{full.get('weight_kg','—')} kg &nbsp;·&nbsp; {full.get('height_cm','—')} cm "
            f"&nbsp;·&nbsp; <b>Goal:</b> {full.get('goal','—')} "
            f"&nbsp;·&nbsp; <span class='bmi-pill' style='background:{bmi_color}'>"
            f"BMI {bmi} — {bmi_cat}</span>"
            f"</div>"
            f"<div class='client-meta' style='margin-top:4px'>"
            f"<b>Diet:</b> {full.get('diet_type','—')} "
            f"&nbsp;·&nbsp; <b>Target:</b> {assessment['target_calories']} kcal "
            f"&nbsp;·&nbsp; <b>Added:</b> {full.get('created_at','')[:10]}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        btn_c1, btn_c2, btn_c3, btn_c4, _ = st.columns([1, 1, 1, 1, 4])

        with btn_c1:
            if st.button("📋 Edit", key=f"edit_{c['id']}", width="stretch"):
                st.session_state["edit_client_id"] = c["id"]
                st.switch_page("pages/1_📋_Intake.py")

        with btn_c2:
            if st.button("🍽️ Plan", key=f"plan_{c['id']}", width="stretch"):
                st.session_state["active_client_id"] = c["id"]
                st.switch_page("pages/2_🍽️_Meal_Plan.py")

        with btn_c3:
            if st.button("📈 Progress", key=f"progress_{c['id']}", width="stretch"):
                st.session_state["active_client_id"] = c["id"]
                st.switch_page("pages/4_📈_Progress.py")

        with btn_c4:
            delete_key = f"del_{c['id']}"
            if st.session_state["confirm_delete_id"] == c["id"]:
                if st.button("⚠️ Confirm Delete", key=f"confirm_{c['id']}",
                             width="stretch"):
                    delete_client(c["id"])
                    st.session_state["confirm_delete_id"] = None
                    st.success(f"Deleted {full['name']}.")
                    st.rerun()
            else:
                if st.button("🗑 Delete", key=delete_key, width="stretch"):
                    st.session_state["confirm_delete_id"] = c["id"]
                    st.rerun()

        # Detail expander
        with st.expander(f"↳ Full Profile — {full['name']}", expanded=False):
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Contact**")
                st.write(f"📧 {full.get('email','—')}")
                st.write(f"📱 {full.get('phone','—')}")
                st.write(f"🎂 DOB: {full.get('dob','—')}")

                st.markdown("**Body Stats**")
                st.write(f"Height: {full.get('height_cm','—')} cm")
                st.write(f"Weight: {full.get('weight_kg','—')} kg")
                st.write(f"Ideal range: {assessment['ideal_weight_low']}–{assessment['ideal_weight_high']} kg")

            with d2:
                st.markdown("**Lifestyle**")
                st.write(f"Activity: {full.get('activity_level','—')}")
                st.write(f"Sleep: {full.get('sleep_hrs','—')} hrs")
                st.write(f"Stress: {full.get('stress_level','—')}")
                st.write(f"Water: {full.get('water_intake_L','—')} L/day")
                st.write(f"Occupation: {full.get('occupation','—')}")

                st.markdown("**Medical**")
                conds = full.get("medical_conditions", [])
                st.write(", ".join(conds) if conds else "None reported")

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
                st.write(f"Diet: {full.get('diet_type','—')}")
                cuisines = full.get("cuisine_pref", [])
                st.write(f"Cuisines: {', '.join(cuisines) if cuisines else '—'}")
                allergies = full.get("allergies", [])
                st.write(f"Allergies: {', '.join(allergies) if allergies else 'None'}")

            # ── Session Notes ─────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 📝 Session Notes")
            _sessions = get_sessions(full["id"])
            if _sessions:
                for _s in reversed(_sessions[-5:]):  # show last 5, newest first
                    _date = _s.get("session_date","")
                    _note = _s.get("notes","").strip()
                    _wt   = _s.get("weight_kg")
                    _wt_str = f" · {_wt} kg" if _wt else ""
                    if _note or _wt:
                        _note_body = _note if _note else "<i style='color:#9CA3AF'>No text note</i>"
                        st.markdown(
                            f"<div style='background:#F9F5EF;border:1px solid #E5D9CC;"
                            f"border-radius:8px;padding:8px 12px;margin-bottom:6px;"
                            f"font-size:0.85rem'>"
                            f"<b style='color:#40916C'>{_date}{_wt_str}</b><br>"
                            f"{_note_body}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.markdown(
                    "<div style='color:#9CA3AF;font-size:0.85rem'>No session notes yet.</div>",
                    unsafe_allow_html=True
                )

            _note_key  = f"snote_{full['id']}"
            _wt_key    = f"swt_{full['id']}"
            _note_cols = st.columns([2, 1, 1])
            with _note_cols[0]:
                _new_note = st.text_input(
                    "Note", key=_note_key,
                    placeholder="e.g. Client responded well, increased protein target"
                )
            with _note_cols[1]:
                _new_wt = st.number_input(
                    "Weight (kg)", key=_wt_key,
                    min_value=0.0, max_value=300.0, value=0.0, step=0.1, format="%.1f"
                )
            with _note_cols[2]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Add Note", key=f"savenote_{full['id']}"):
                    wt_val = _new_wt if _new_wt > 0 else None
                    if _new_note.strip() or wt_val:
                        add_session(full["id"], wt_val, _new_note.strip())
                        st.success("Note saved!")
                        st.rerun()
                    else:
                        st.warning("Enter a note or weight first.")

        st.markdown("")
