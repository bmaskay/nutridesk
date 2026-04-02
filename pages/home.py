"""
home.py — NutriDesk Home Dashboard
Practitioner summary: client count, plan count, recent clients, quick actions.
Called by app.py via st.navigation() / pg.run(). Do NOT call st.set_page_config() here.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.database import get_all_clients, get_all_meal_plans
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
- **Intake first** — Complete the full 4-section intake before generating a meal plan.
- **Two lunch/dinner options** — Clients can choose on the day. Ensures flexibility without breaking their macro targets.
- **Re-generate plans** — Each generation shuffles recipes. Run 2–3 times and pick the best fit for your client.
- **PDF report** — Available on the Meal Plan page once a plan is generated. Send directly to clients.
- **Progress tracking** — Log weekly weigh-ins under 📈 Progress to track trends over time.
- **Biomarkers** — Record blood work results on the Progress page for comprehensive monitoring.
    """)
