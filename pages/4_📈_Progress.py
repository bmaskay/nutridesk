"""
4_Progress.py — Client Progress Tracking
Weight check-ins, trend chart, and biomarker logs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
from utils.database import (
    get_all_clients, get_client, add_session, get_sessions,
    add_biomarkers, get_biomarkers
)
from utils.calculations import full_assessment, calculate_bmi, bmi_category
from utils.header import render_header

render_header("Progress")

st.markdown("""
<style>
  [data-testid="metric-container"] { background: #F9F5EF; border: 1px solid #E5D9CC;
                                     border-radius: 10px; padding: 10px 14px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📈 Client Progress")
st.markdown("---")

# ── Client selector ───────────────────────────────────────────────────────────

clients = get_all_clients()
if not clients:
    st.info("No clients yet. Add a client first.")
    st.stop()

client_options = {f"{c['name']} (ID {c['id']})": c["id"] for c in clients}
default_id = st.session_state.get("active_client_id")
default_key = next(
    (k for k, v in client_options.items() if v == default_id),
    list(client_options.keys())[0]
)
selected_label = st.selectbox("Select Client", list(client_options.keys()),
                              index=list(client_options.keys()).index(default_key))
client_id = client_options[selected_label]
client = get_client(client_id)
assessment = full_assessment(client)

# ── Summary header ────────────────────────────────────────────────────────────

st.markdown(f"### {client['name']}")

sessions = get_sessions(client_id)
starting_weight = client.get("weight_kg", 0)
current_weight  = sessions[-1]["weight_kg"] if sessions else starting_weight
total_lost      = round(starting_weight - current_weight, 1) if sessions else 0
current_bmi     = calculate_bmi(current_weight, client.get("height_cm", 0))

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Starting Weight", f"{starting_weight} kg")
m2.metric("Current Weight",  f"{current_weight} kg",
          delta=f"{-total_lost:.1f} kg" if total_lost != 0 else None,
          delta_color="normal")
m3.metric("Total Lost",      f"{abs(total_lost)} kg" if total_lost > 0 else "—")
m4.metric("Current BMI",     f"{current_bmi}", bmi_category(current_bmi))
m5.metric("Check-ins",       len(sessions))

# ── Plain-language trend interpretation ───────────────────────────────────────
if len(sessions) >= 2:
    from datetime import datetime as _dt, timedelta as _td, date as _date

    # Overall trend
    _goal        = client.get("goal", "")
    _ideal_low   = assessment["ideal_weight_low"]
    _ideal_high  = assessment["ideal_weight_high"]
    _first_sess  = sessions[0]
    _last_sess   = sessions[-1]

    try:
        _first_date = _dt.fromisoformat(_first_sess["session_date"]).date()
        _last_date  = _dt.fromisoformat(_last_sess["session_date"]).date()
    except Exception:
        _first_date = _last_date = _date.today()

    _weeks_elapsed = max((_last_date - _first_date).days / 7, 0.01)
    _total_change  = round((_last_sess["weight_kg"] or 0) - (_first_sess["weight_kg"] or 0), 1)
    _weekly_avg    = round(_total_change / _weeks_elapsed, 2)

    # Compose interpretation
    _interp_parts = []

    if total_lost > 0:
        _rate_ok = -0.6 <= _weekly_avg <= -0.1
        _rate_fast = _weekly_avg < -0.6
        if _rate_ok:
            _interp_parts.append(
                f"✅ **On track** — {client['name']} has lost **{total_lost} kg** "
                f"over {_weeks_elapsed:.1f} weeks (~{abs(_weekly_avg)} kg/week), "
                f"which is within the healthy rate of 0.25–0.5 kg/week."
            )
        elif _rate_fast:
            _interp_parts.append(
                f"⚡ **Fast loss** — {abs(_weekly_avg)} kg/week is above the recommended "
                f"0.5 kg/week ceiling. Check for adequate protein intake and signs of "
                f"muscle loss (fatigue, strength decline). Consider easing the deficit."
            )
        else:
            _interp_parts.append(
                f"📉 **Slow progress** — {abs(_weekly_avg)} kg/week over "
                f"{_weeks_elapsed:.1f} weeks. This can reflect water fluctuation, "
                f"adherence variation, or a need to reassess calorie targets."
            )
    elif total_lost < -0.5:
        _interp_parts.append(
            f"📈 **Weight gain of {abs(total_lost)} kg** since starting. "
            f"If the goal is fat loss, review adherence and whether calorie targets "
            f"are being followed. Small gains (<1 kg) can be normal water retention."
        )
    else:
        _interp_parts.append(
            f"⚖️ **Weight stable** — less than 0.5 kg change since starting. "
            + ("This is the goal for a maintenance plan." if "Maintain" in _goal
               else "If fat loss is the goal, check that the calorie target and meal plan are being followed.")
        )

    # Proximity to ideal range
    if current_weight > _ideal_high + 1:
        _kg_gap = round(current_weight - _ideal_high, 1)
        if _weekly_avg and _weekly_avg < 0:
            _wks_left = round(_kg_gap / abs(_weekly_avg))
            _interp_parts.append(
                f"🎯 **{_kg_gap} kg from the healthy range** ({_ideal_low}–{_ideal_high} kg). "
                f"At the current rate, that's roughly **{_wks_left} more weeks**."
            )
        else:
            _interp_parts.append(
                f"🎯 **{_kg_gap} kg from the healthy range** ({_ideal_low}–{_ideal_high} kg)."
            )
    elif _ideal_low <= current_weight <= _ideal_high:
        _interp_parts.append(
            f"🌟 **{client['name']} is within the healthy weight range** "
            f"({_ideal_low}–{_ideal_high} kg). Focus on maintenance and body composition."
        )

    # Recency flag
    try:
        _days_since = (_date.today() - _last_date).days
        if _days_since > 28:
            _interp_parts.append(
                f"⏰ **Last check-in was {_days_since} days ago** — "
                f"a monthly weigh-in keeps progress data meaningful."
            )
    except Exception:
        pass

    if _interp_parts:
        for _part in _interp_parts:
            st.markdown(
                f"<div style='background:#F0F9FF;border-left:3px solid #38BDF8;"
                f"border-radius:0 6px 6px 0;padding:8px 14px;margin-bottom:6px;"
                f"font-size:0.88rem;color:#0C4A6E'>{_part}</div>",
                unsafe_allow_html=True,
            )

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_weight, tab_biomarkers = st.tabs(["⚖️ Weight Tracking", "🩺 Biomarkers"])

# ── Weight Tracking ───────────────────────────────────────────────────────────

with tab_weight:
    col_form, col_chart = st.columns([1, 2])

    with col_form:
        st.markdown("#### Log a Check-in")
        with st.form("checkin_form"):
            checkin_weight = st.number_input(
                "Weight (kg)", min_value=30.0, max_value=250.0,
                value=float(current_weight), step=0.1, format="%.1f"
            )
            checkin_notes = st.text_area("Notes", placeholder="e.g. Feeling great, slightly bloated...", height=80)
            submit_checkin = st.form_submit_button("✅ Save Check-in", width="stretch")

        if submit_checkin:
            add_session(client_id, checkin_weight, checkin_notes)
            st.success(f"Check-in saved: {checkin_weight} kg")
            st.rerun()

        # Ideal weight reminder
        ideal_l = assessment["ideal_weight_low"]
        ideal_h = assessment["ideal_weight_high"]
        st.info(f"🎯 Ideal weight range: **{ideal_l} – {ideal_h} kg**")

    with col_chart:
        st.markdown("#### Weight Trend")
        if not sessions:
            st.info("No check-ins logged yet. Log your first check-in to see the trend.")
        else:
            import pandas as pd

            df = pd.DataFrame(sessions)
            df["session_date"] = pd.to_datetime(df["session_date"])
            df = df.sort_values("session_date")

            # Chart with target line
            import altair as alt

            # Weight line
            base = alt.Chart(df).mark_line(
                color="#2D6A4F", strokeWidth=2.5, point=True
            ).encode(
                x=alt.X("session_date:T", title="Date", axis=alt.Axis(format="%d %b")),
                y=alt.Y("weight_kg:Q", title="Weight (kg)",
                        scale=alt.Scale(
                            domain=[max(30, float(df["weight_kg"].min()) - 3),
                                    float(df["weight_kg"].max()) + 3]
                        )),
                tooltip=[
                    alt.Tooltip("session_date:T", title="Date", format="%d %b %Y"),
                    alt.Tooltip("weight_kg:Q", title="Weight (kg)"),
                ]
            )

            # Ideal target band
            target_df = pd.DataFrame({
                "date": [df["session_date"].min(), df["session_date"].max()],
                "low":  [ideal_l, ideal_l],
                "high": [ideal_h, ideal_h],
            })
            band = alt.Chart(target_df).mark_area(
                color="#D8F3DC", opacity=0.4
            ).encode(
                x="date:T",
                y="low:Q",
                y2="high:Q",
            )

            chart = (band + base).properties(height=300)
            st.altair_chart(chart, width="stretch")

            # Data table
            display_df = df[["session_date", "weight_kg", "notes"]].copy()
            display_df.columns = ["Date", "Weight (kg)", "Notes"]
            display_df["Date"] = display_df["Date"].dt.strftime("%d %b %Y")
            display_df = display_df.sort_values("Date", ascending=False)
            st.dataframe(display_df, width="stretch", hide_index=True)

# ── Biomarkers ────────────────────────────────────────────────────────────────

with tab_biomarkers:
    col_bform, col_bdata = st.columns([1, 2])

    with col_bform:
        st.markdown("#### Log Biomarkers")
        with st.form("biomarker_form"):
            b_date = st.date_input("Test Date", value=date.today())
            fasting_glucose = st.number_input("Fasting Glucose (mmol/L)", 0.0, 30.0, 0.0, step=0.1)
            hba1c           = st.number_input("HbA1c (%)", 0.0, 20.0, 0.0, step=0.1)
            cholesterol     = st.number_input("Total Cholesterol (mmol/L)", 0.0, 15.0, 0.0, step=0.1)
            hdl             = st.number_input("HDL (mmol/L)", 0.0, 5.0, 0.0, step=0.1)
            ldl             = st.number_input("LDL (mmol/L)", 0.0, 10.0, 0.0, step=0.1)
            triglycerides   = st.number_input("Triglycerides (mmol/L)", 0.0, 15.0, 0.0, step=0.1)
            tsh             = st.number_input("TSH (mIU/L)", 0.0, 20.0, 0.0, step=0.01)
            vitamin_d       = st.number_input("Vitamin D (nmol/L)", 0.0, 300.0, 0.0, step=1.0)
            b12             = st.number_input("B12 (pmol/L)", 0.0, 1500.0, 0.0, step=1.0)
            ferritin        = st.number_input("Ferritin (μg/L)", 0.0, 500.0, 0.0, step=1.0)
            b_notes         = st.text_area("Notes", height=60)
            submit_bm = st.form_submit_button("✅ Save Biomarkers", width="stretch")

        if submit_bm:
            bm_data = {
                "recorded_date":   str(b_date),
                "notes":           b_notes,
            }
            # Only save non-zero values
            for k, v in [
                ("fasting_glucose", fasting_glucose), ("hba1c", hba1c),
                ("total_cholesterol", cholesterol), ("hdl", hdl),
                ("ldl", ldl), ("triglycerides", triglycerides),
                ("tsh", tsh), ("vitamin_d", vitamin_d),
                ("b12", b12), ("ferritin", ferritin),
            ]:
                if v > 0:
                    bm_data[k] = v
            add_biomarkers(client_id, bm_data)
            st.success("Biomarkers saved!")
            st.rerun()

    with col_bdata:
        st.markdown("#### Biomarker History")
        biomarkers = get_biomarkers(client_id)
        if not biomarkers:
            st.info("No biomarker records yet.")
        else:
            import pandas as pd

            bdf = pd.DataFrame(biomarkers)
            bdf["recorded_date"] = pd.to_datetime(bdf["recorded_date"])
            bdf = bdf.sort_values("recorded_date", ascending=False)

            # Display columns that have data
            display_cols = ["recorded_date"]
            marker_cols = [
                "fasting_glucose", "hba1c", "total_cholesterol",
                "hdl", "ldl", "triglycerides", "tsh", "vitamin_d", "b12", "ferritin"
            ]
            for col in marker_cols:
                if col in bdf.columns and bdf[col].notna().any() and (bdf[col] > 0).any():
                    display_cols.append(col)

            show_df = bdf[display_cols + (["notes"] if "notes" in bdf.columns else [])].copy()
            show_df["recorded_date"] = show_df["recorded_date"].dt.strftime("%d %b %Y")
            show_df.columns = [c.replace("_", " ").title() for c in show_df.columns]

            st.dataframe(show_df, width="stretch", hide_index=True)

            # Reference ranges info
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
