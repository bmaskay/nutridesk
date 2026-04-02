"""
Test banner — run with: python -m streamlit run test_banner.py
"""
import streamlit as st
from utils.header import render_header

st.set_page_config(page_title="NutriDesk · Āhāra by Asha", page_icon="🌿", layout="wide")
render_header("Test Page")

st.markdown("### Dashboard")
st.write("Banner should show 🌿 leaf + NutriDesk + Āhāra by Asha on left, @Asha.Nutrition on right.")
st.write("Tab icon should be a green leaf 🌿")
