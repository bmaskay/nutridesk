"""
home.py — NutriDesk Home Dashboard
Practitioner summary: client count, plan count, recent clients, quick actions.
Called by app.py via st.navigation() / pg.run(). Do NOT call st.set_page_config() here.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime, date, timedelta
from utils.database import get_all_clients, get_all_meal_plans, get_sessions, get_latest_meal_plan
from utils.header import render_header

render_header()

st.markdown("""
<style>
  [data-testid="metric-container"] {
    background: #F9F5EF; border: 1px solid #E5D9CC;
    border-radius: 10px; padding: 12px 16px;
  }
</style>
""", unsafe_allow_html=True)

# ── Page heading ──────────────────────────────────────────────────────────────

st.markdown("### Practitioner Dashboard")
st.markdown("---")

# ── Metrics row ──────────────────────────────────────────────────────────────

clients = get_all_clients()
total_clients = len(clients)

total_plans = 0
for c in clients:
    plans = get_all_meal_plans(c["id"])
    total_plans += len(plans)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Clients", total_clients)
col2.metric("Meal Plans Generated", total_plans)
col3.metric("Recipes in Library", 81)
col4.metric("App Version", "1.0")

st.markdown("---")

# ── Action items ──────────────────────────────────────────────────────────────
# Scan for clients that need attention: no plan yet, or no check-in in 4+ weeks

STALE_DAYS = 28  # flag clients with no check-in in this many days

no_plan_clients       = []
stale_checkin_clients = []
cutoff = date.today() - timedelta(days=STALE_DAYS)

for c in clients:
    # No meal plan yet?
    cplans = get_all_meal_plans(c["id"])
    if not cplans:
        no_plan_clients.append(c)

    # Last check-in stale?
    sessions = get_sessions(c["id"])
    if sessions:
        last_date_str = sessions[-1].get("session_date", "")
        try:
            last_date = date.fromisoformat(last_date_str)
            if last_date < cutoff:
                stale_checkin_clients.append((c, last_date))
        except Exception:
            pass

has_action_items = no_plan_clients or stale_checkin_clients

if has_action_items:
    st.markdown("### 🔔 Needs Attention")
    if no_plan_clients:
        st.markdown(f"**{len(no_plan_clients)} client(s) have no meal plan yet:**")
        for c in no_plan_clients:
            ac1, ac2 = st.columns([3, 1])
            with ac1:
                st.markdown(
                    f"<div style='background:#FFF7ED;border:1px solid #FED7AA;"
                    f"border-radius:8px;padding:8px 14px;font-size:0.9rem'>"
                    f"🍽️ <b>{c['name']}</b> — no plan generated yet</div>",
                    unsafe_allow_html=True,
                )
            with ac2:
                if st.button("Generate →", key=f"home_plan_{c['id']}", width="stretch"):
                    st.session_state["active_client_id"] = c["id"]
                    st.switch_page("pages/2_🍽️_Meal_Plan.py")

    if stale_checkin_clients:
        st.markdown(f"**{len(stale_checkin_clients)} client(s) haven't checked in recently:**")
        for c, last_date in stale_checkin_clients:
            days_ago = (date.today() - last_date).days
            ac1, ac2 = st.columns([3, 1])
            with ac1:
                st.markdown(
                    f"<div style='background:#F0F9FF;border:1px solid #BAE6FD;"
                    f"border-radius:8px;padding:8px 14px;font-size:0.9rem'>"
                    f"📅 <b>{c['name']}</b> — last check-in {days_ago} days ago "
                    f"({last_date.strftime('%-d %b')})</div>",
                    unsafe_allow_html=True,
                )
            with ac2:
                if st.button("Log →", key=f"home_progress_{c['id']}", width="stretch"):
                    st.session_state["active_client_id"] = c["id"]
                    st.switch_page("pages/4_📈_Progress.py")

    st.markdown("---")

# ── Recent clients table ──────────────────────────────────────────────────────

st.markdown("### Recent Clients")

if not clients:
    st.info("No clients yet. Use **📋 New Client** to add your first client.")
else:
    import pandas as pd

    df = pd.DataFrame(clients)
    df = df.rename(columns={
        "id":         "ID",
        "name":       "Name",
        "gender":     "Gender",
        "weight_kg":  "Weight (kg)",
        "goal":       "Goal",
        "created_at": "Added",
    })
    df["Added"] = pd.to_datetime(df["Added"]).dt.strftime("%d %b %Y")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ── Quick actions ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Quick Actions")

qc1, qc2, qc3 = st.columns(3)
with qc1:
    if st.button("➕  Add New Client", width="stretch"):
        st.switch_page("pages/1_📋_Intake.py")

with qc2:
    if st.button("🍽️  Generate Meal Plan", width="stretch"):
        st.switch_page("pages/2_🍽️_Meal_Plan.py")

with qc3:
    if st.button("👥  View All Clients", width="stretch"):
        st.switch_page("pages/3_👥_Clients.py")

# ── Tips panel ────────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("💡 Practitioner Tips", expanded=False):
    st.markdown("""
- **Intake first** — Complete the full intake before generating a meal plan.
- **Two lunch/dinner options** — Clients can choose on the day. Flexibility without breaking macro targets.
- **Swap individual meals** — On the Meal Plan page, use the 🔄 button on any recipe card to swap just that one meal.
- **Re-generate plans** — Each generation shuffles recipes. Run 2–3 times and pick the best fit.
- **PDF report** — Available on the Meal Plan page once a plan is generated. Send directly to clients.
- **Progress tracking** — Log weekly weigh-ins under 📈 Progress. The dashboard flags anyone overdue.
- **Biomarkers** — Record blood work results on the Progress page for comprehensive monitoring.
    """)
