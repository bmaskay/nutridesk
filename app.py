"""
app.py — NutriDesk Router (Streamlit 1.37+)
Routing via st.navigation() — sidebar is rendered automatically by Streamlit.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from utils.database import init_db

# ── Global page config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NutriDesk — Āhāra by Asha",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Login gate ────────────────────────────────────────────────────────────────
# Password is cached in a browser cookie so returning visitors on the same
# browser don't have to re-type it on every refresh/new tab. The cookie is
# still checked against the real secret every time — changing APP_PASSWORD
# invalidates any cached cookie.

_AUTH_COOKIE = "nd_auth_pw"


def _remember_password_js(password: str):
    components.html(
        f"""<script>
        parent.document.cookie =
            "{_AUTH_COOKIE}=" + encodeURIComponent("{password}") +
            "; max-age=" + (60 * 60 * 24 * 30) + "; path=/; SameSite=Lax";
        </script>""",
        height=0,
    )


def check_password():
    if st.session_state.get("authenticated"):
        # Refresh the cookie on every authenticated render (never right before a
        # rerun, so there's no race between the script mounting and the page
        # tearing down — see the login branch below for why that matters).
        _remember_password_js(st.secrets["APP_PASSWORD"])
        return

    try:
        cached_pw = st.context.cookies.get(_AUTH_COOKIE)
    except Exception:
        cached_pw = None
    if cached_pw and cached_pw == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        return

    st.title("🌿 Āhāra by Asha")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
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
    st.Page("pages/home.py",          title="Home",         icon="🏠", default=True),
    st.Page("pages/1_📋_Intake.py",   title="New Client",   icon="📋"),
    st.Page("pages/3_👥_Clients.py",  title="Clients",      icon="👥"),
    st.Page("pages/plan_builder.py",  title="Plan Builder", icon="📊"),
]

pg = st.navigation(pages_list, position="hidden")

with st.sidebar:
    st.markdown("### 🌿 NutriDesk")
    for _p in pages_list:
        st.page_link(_p)
    st.divider()
    st.caption("NutriDesk v2.1 · Āhāra by Asha")

# ── Run the selected page ─────────────────────────────────────────────────────

pg.run()
