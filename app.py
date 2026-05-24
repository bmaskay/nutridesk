"""
app.py — NutriDesk Router (Streamlit 1.37+)
Routing via st.navigation() — sidebar is rendered automatically by Streamlit.
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

# ── Login gate ────────────────────────────────────────────────────────────────

def check_password():
    if st.session_state.get("authenticated"):
        return
    st.title("🌿 Āhāra by Asha")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

check_password()

init_db()

# ── Routing ──────────────────────────────────────────────────────────────────

pages_list = [
    st.Page("pages/home.py",            title="Home",       icon="🏠", default=True),
    st.Page("pages/1_📋_Intake.py",     title="New Client", icon="📋"),
    st.Page("pages/2_🍽️_Meal_Plan.py", title="Meal Plan",  icon="🍽️"),
    st.Page("pages/3_👥_Clients.py",    title="Clients",    icon="👥"),
    st.Page("pages/4_📈_Progress.py",   title="Progress",   icon="📈"),
    st.Page("pages/5_💪_Exercise_Plan.py", title="Exercise",   icon="💪"),
]

pg = st.navigation(pages_list, position="hidden")

with st.sidebar:
    st.markdown("### 🌿 NutriDesk")
    for _p in pages_list:
        st.page_link(_p)
    st.divider()
    st.caption("NutriDesk v2.0 · Āhāra by Asha")

# ── Run the selected page ─────────────────────────────────────────────────────

pg.run()
