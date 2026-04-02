"""
app.py — NutriDesk Router (Streamlit 1.37+)
Defines routing via st.navigation() and renders sidebar nav explicitly via st.page_link().
position="hidden" suppresses the auto-nav so we control the sidebar ourselves.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from utils.database import init_db

# ── Global page config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NutriDesk — Āhāra by Asha",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Routing ──────────────────────────────────────────────────────────────────

pg = st.navigation(
    [
        st.Page("pages/home.py",            title="Home",       icon="🏠", default=True),
        st.Page("pages/1_📋_Intake.py",     title="New Client", icon="📋"),
        st.Page("pages/2_🍽️_Meal_Plan.py", title="Meal Plan",  icon="🍽️"),
        st.Page("pages/3_👥_Clients.py",    title="Clients",    icon="👥"),
        st.Page("pages/4_📈_Progress.py",   title="Progress",   icon="📈"),
    ]
)

# ── Sidebar footer ────────────────────────────────────────────────────────────

with st.sidebar:
    st.divider()
    st.caption("NutriDesk v1.0 · Āhāra by Asha · 2026")

# ── Run the selected page ─────────────────────────────────────────────────────

pg.run()
