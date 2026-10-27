"""BuildSense AI: Streamlit front end.

Runs the same feature logic as the FastAPI backend (backend/app/services.py)
directly, so it deploys on Streamlit Community Cloud as a single app.
Set ANTHROPIC_API_KEY in the app's Secrets for live AI; without it the app
runs in mock mode with sample data.
"""

import asyncio
import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Streamlit secrets -> environment, before the backend config is imported.
try:
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_MODEL", "CLAUDE_EFFORT", "CLAUDE_FALLBACKS", "MOCK_MODE"):
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
except FileNotFoundError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app import config, llm, services  # noqa: E402
from app.llm import AIError, image_block  # noqa: E402

st.set_page_config(page_title="BuildSense AI", page_icon="🏗️", layout="wide")

st.markdown(
    """
    <style>
      [data-testid="stMetricValue"] { font-size: 1.5rem; }
      .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

SEVERITY_ICON = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴", "good": "🟢", "caution": "🟡",
                 "unsuitable": "🔴", "compliant": "🟢", "partial": "🟡", "non_compliant": "🔴", "not_visible": "⚪",
                 "on_track": "🟢", "at_risk": "🟡", "delayed": "🔴", "within_budget": "🟢", "tight": "🟡",
                 "over_budget": "🔴", "positive": "🟢", "neutral": "⚪", "negative": "🔴"}


def tag(value: str) -> str:
    return f"{SEVERITY_ICON.get(value, '⚪')} {value.replace('_', ' ').capitalize()}"


def money(n: float, currency: str = "INR") -> str:
    symbol = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
    return f"{symbol}{n:,.0f}"


def run(coro):
    """Run an async service call; returns (data, mode) or (None, None) after showing the error."""
    llm._client = None  # the async client is tied to an event loop; make a fresh one per call
    try:
        with st.spinner("Analysing…"):
            return asyncio.run(coro)
    except (AIError, services.LocationNotFound) as e:
        st.error(str(e))
    return None, None


def read_image(upload) -> dict | None:
    if upload is None:
        return None
    data = upload.getvalue()
    if len(data) > config.MAX_IMAGE_BYTES:
        st.error("Image is larger than 5 MB.")
        return None
    return image_block(data, upload.type)


def mock_notice(mode):
    if mode == "mock":
        st.warning("Mock mode: sample output. Add ANTHROPIC_API_KEY to the app's Secrets for live AI analysis.")


def bullets(items, empty="None"):
    st.markdown("\n".join(f"- {x}" for x in items) if items else f"_{empty}_")


# ---------------------------------------------------------------- pages


def page_home():
    st.title("🏗️ Construction Intelligence Platform")
    st.caption("Multimodal AI decision support for construction planning, execution and monitoring.")
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(FEATURE_INFO):
        with cols[i % 3].container(border=True):
            st.markdown(f"### {icon} {name}")
            st.write(desc)
    st.subheader("How it works")
    st.markdown(
        "1. **Input**: site photos, notes or project data  \n"
        "2. **Prompt**: the app validates input and builds a task-specific prompt  \n"
        "3. **Multimodal LLM**: Claude analyses text and images together  \n"
        "4. **JSON contract**: output is forced into a fixed schema and validated  \n"
        "5. **Dashboard**: results rendered as metrics, tables and charts"
    )
    st.caption("AI output supports professional judgement and does not replace inspection by a qualified engineer.")


def page_safety():
    st.title("🦺 Site Safety Monitoring")
    left, right = st.columns([1, 2], gap="large")
    with left:
        upload = st.file_uploader("Site photo", type=["jpg", "jpeg", "png", "webp", "gif"])
        if upload:
            st.image(upload, use_container_width=True)
        context = st.text_area("Site context", placeholder="e.g. 3rd floor slab, shuttering in progress")
        go = st.button("Analyse safety", type="primary", disabled=upload is None, use_container_width=True)
    with right:
        if not go:
            st.info("Upload a site photo to get a PPE and hazard assessment.")
            return
        img = read_image(upload)
        if not img:
            return
        data, mode = run(services.safety(img, context))
        if not data:
            return
        mock_notice(mode)
        c = st.columns(4)
        c[0].metric("Safety score", f"{data.safety_score}/100")
        c[1].metric("Overall risk", tag(data.overall_risk_level))
        c[2].metric("Workers visible", data.workers_visible)
        c[3].metric("Hazards", len(data.hazards))
        st.write(data.summary)
        st.subheader("Immediate actions")
        bullets(data.immediate_actions)
        st.subheader("Hazards")
        for h in data.hazards:
            with st.expander(f"{tag(h.severity)} · {h.type}"):
                st.write(h.description)
                st.caption(f"📍 {h.location}")
                st.write(f"**Recommendation:** {h.recommendation}")
        st.subheader("PPE compliance")
        st.dataframe(pd.DataFrame([{"Item": p.item, "Status": tag(p.status), "Note": p.note} for p in data.ppe_compliance]),
                     hide_index=True, use_container_width=True)
        st.subheader("Violations")
        bullets(data.violations)


def page_cracks():
    st.title("🧱 Crack Detection & Analysis")
    left, right = st.columns([1, 2], gap="large")
    with left:
        upload = st.file_uploader("Crack photo", type=["jpg", "jpeg", "png", "webp", "gif"])
        if upload:
            st.image(upload, use_container_width=True)
        structure = st.selectbox("Structural element", ["Wall", "Column", "Beam", "Slab", "Foundation", "Pavement", "Bridge deck", "Other"])
        notes = st.text_area("Notes", placeholder="e.g. appeared after monsoon, building 15 years old",
                             help="A coin or tape measure in the photo helps estimate width.")
        go = st.button("Analyse crack", type="primary", disabled=upload is None, use_container_width=True)
    with right:
        if not go:
            st.info("Upload a close-up of a crack to classify it and get repair guidance.")
            return
        img = read_image(upload)
        if not img:
            return
        data, mode = run(services.cracks(img, structure, notes))
        if not data:
            return
        mock_notice(mode)
        c = st.columns(4)
        c[0].metric("Crack detected", "Yes" if data.crack_detected else "No")
        c[1].metric("Severity", tag(data.severity))
        c[2].metric("Width", f"{data.estimated_width_mm} mm", f"{data.estimated_length_cm} cm long", delta_color="off")
        c[3].metric("Urgency", data.urgency.replace("_", " ").capitalize())
        if data.needs_engineer_inspection:
            st.error("A structural engineer should inspect this in person.")
        st.write(data.summary)
        st.dataframe(pd.DataFrame({"": ["Type", "Pattern", "Material"], "Value": [data.crack_type, data.pattern, data.material]}),
                     hide_index=True, use_container_width=True)
        st.subheader("Structural risk")
        st.write(data.structural_risk)
        a, b = st.columns(2)
        with a:
            st.subheader("Probable causes")
            bullets(data.probable_causes)
        with b:
            st.subheader("Recommended repairs")
            bullets(data.recommended_repairs)


def page_valuation():
    st.title("🏠 Real Estate Valuation")
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("valuation"):
            location = st.text_input("Location", "Baner, Pune")
            a, b = st.columns(2)
            ptype = a.selectbox("Type", ["Apartment", "Villa", "Independent house", "Plot", "Commercial"])
            area = b.number_input("Area (sq ft)", min_value=1, value=1100)
            beds = a.number_input("Bedrooms", min_value=0, value=2)
            baths = b.number_input("Bathrooms", min_value=0, value=2)
            age = a.number_input("Age (years)", min_value=0, value=5)
            condition = b.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor"], index=1)
            amenities = st.multiselect("Amenities", ["Parking", "Lift", "Security", "Power backup", "Gym", "Swimming pool", "Garden", "Clubhouse"],
                                       default=["Parking", "Lift"])
            notes = st.text_area("Notes", placeholder="e.g. corner unit, metro 500 m away")
            go = st.form_submit_button("Estimate value", type="primary", use_container_width=True)
    with right:
        if not go:
            st.info("Fill in the property details to get a market valuation.")
            return
        if len(location.strip()) < 2:
            st.error("Enter a location.")
            return
        req = services.ValuationRequest(location=location, property_type=ptype, area_sqft=area, bedrooms=beds,
                                        bathrooms=baths, age_years=age, condition=condition, amenities=amenities, notes=notes)
        data, mode = run(services.valuation(req))
        if not data:
            return
        mock_notice(mode)
        c = st.columns(4)
        c[0].metric("Estimated value", money(data.estimated_value_mid, data.currency))
        c[1].metric("Price / sq ft", money(data.price_per_sqft, data.currency))
        c[2].metric("Monthly rent", money(data.estimated_monthly_rent, data.currency))
        c[3].metric("Confidence", data.confidence.capitalize())
        st.caption(f"Range: {money(data.estimated_value_low, data.currency)} – {money(data.estimated_value_high, data.currency)}")
        st.subheader("Value drivers")
        st.dataframe(pd.DataFrame([{"Factor": d.factor, "Impact": tag(d.impact), "Note": d.note} for d in data.key_value_drivers]),
                     hide_index=True, use_container_width=True)
        st.subheader("Market outlook")
        st.write(data.market_outlook)
        a, b = st.columns(2)
        with a:
            st.subheader("Recommendations")
            bullets(data.recommendations)
        with b:
            st.subheader("Assumptions")
            bullets(data.assumptions)


def page_planning():
    st.title("📐 Construction Project Planning")
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("planning"):
            name = st.text_input("Project name", placeholder="optional")
            a, b = st.columns(2)
            ptype = a.selectbox("Type", ["Residential", "Commercial", "Industrial", "Infrastructure"])
            location = b.text_input("Location", "Jaipur")
            area = a.number_input("Plot area (sq ft)", min_value=1, value=1500)
            floors = b.number_input("Floors", min_value=1, value=2)
            budget = a.number_input("Budget", min_value=1, value=7_000_000, step=100_000)
            currency = b.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "AED"])
            start = st.date_input("Start date", value=None)
            reqs = st.text_area("Requirements", placeholder="e.g. 3BHK per floor, basement parking, solar roof")
            go = st.form_submit_button("Generate plan", type="primary", use_container_width=True)
    with right:
        if not go:
            st.info("Describe the project to generate a phased schedule, resources and risks.")
            return
        req = services.PlanRequest(project_name=name, project_type=ptype, location=location or "Unknown", plot_area_sqft=area,
                                   floors=floors, budget=budget, currency=currency,
                                   start_date=start.isoformat() if start else None, requirements=reqs)
        data, mode = run(services.planning(req))
        if not data:
            return
        mock_notice(mode)
        st.subheader(data.project_title)
        st.write(data.summary)
        c = st.columns(4)
        c[0].metric("Duration", f"{data.total_duration_weeks} weeks")
        c[1].metric("Estimated cost", money(data.estimated_cost_total, data.currency))
        c[2].metric("Budget", tag(data.budget_status))
        c[3].metric("Phases", len(data.phases))

        st.subheader("Timeline")
        df = pd.DataFrame([{"Phase": p.name, "Start": p.start_week - 1, "End": p.start_week - 1 + p.duration_weeks,
                            "Weeks": p.duration_weeks} for p in data.phases])
        chart = alt.Chart(df).mark_bar(cornerRadius=4, color="#e8730c").encode(
            x=alt.X("Start:Q", title="Week"), x2="End:Q",
            y=alt.Y("Phase:N", sort=None, title=None), tooltip=["Phase", "Weeks"],
        ).properties(height=40 * len(df) + 20)
        st.altair_chart(chart, use_container_width=True)

        st.subheader("Phases")
        for p in data.phases:
            with st.expander(f"{p.name} · week {p.start_week} · {p.duration_weeks}w · {money(p.estimated_cost, data.currency)}"):
                bullets(p.tasks)
                st.caption("Milestones: " + "; ".join(p.milestones))
        a, b = st.columns(2)
        with a:
            st.subheader("Labour")
            st.dataframe(pd.DataFrame([{"Role": l.role, "Count": l.count} for l in data.labor]), hide_index=True, use_container_width=True)
        with b:
            st.subheader("Materials")
            st.dataframe(pd.DataFrame([{"Item": m.item, "Quantity": f"{m.quantity:,.0f} {m.unit}"} for m in data.materials]),
                         hide_index=True, use_container_width=True)
        st.subheader("Equipment")
        bullets(data.equipment)
        st.subheader("Risks")
        st.dataframe(pd.DataFrame([{"Risk": r.risk, "Likelihood": tag(r.likelihood), "Impact": tag(r.impact), "Mitigation": r.mitigation}
                                   for r in data.risks]), hide_index=True, use_container_width=True)


SAMPLE_NOTES = """Columns C4 to C9 cast on 2nd floor. Shuttering for slab ~80% done.
Cement truck didn't come, supplier says tomorrow. Only 30 bags left.
Seepage seen in basement retaining wall near grid B2.
14 labour present, 2 absent. One worker without helmet near the hoist, warned."""


def page_daily():
    st.title("📋 Daily Site Assistant")
    left, right = st.columns([1, 2], gap="large")
    with left:
        project = st.text_input("Project", placeholder="optional")
        notes = st.text_area("Today's raw site notes", height=200, placeholder=SAMPLE_NOTES,
                             help="Write the way you would in a WhatsApp message; the AI will structure it.")
        upload = st.file_uploader("Site photo (optional)", type=["jpg", "jpeg", "png", "webp", "gif"])
        use_sample = st.checkbox("Use sample notes")
        go = st.button("Create daily report", type="primary", use_container_width=True)
    with right:
        if not go:
            st.info("Paste today's notes to get a structured daily progress report.")
            return
        text = SAMPLE_NOTES if use_sample and not notes.strip() else notes
        if not text.strip():
            st.error("Site notes are required.")
            return
        data, mode = run(services.daily(text, project, read_image(upload)))
        if not data:
            return
        mock_notice(mode)
        st.subheader(f"Daily report · {data.date}")
        st.markdown(f"**Status:** {tag(data.progress_status)}")
        st.write(data.summary)
        a, b = st.columns(2)
        with a:
            st.subheader("Work completed")
            bullets(data.work_completed)
        with b:
            st.subheader("Tomorrow's plan")
            bullets(data.tomorrow_plan)
        st.subheader("Issues")
        if data.issues:
            st.dataframe(pd.DataFrame([{"Issue": i.issue, "Priority": tag(i.priority), "Owner": i.suggested_owner} for i in data.issues]),
                         hide_index=True, use_container_width=True)
        else:
            st.write("_No issues reported._")
        a, b = st.columns(2)
        with a:
            st.subheader("Safety reminders")
            bullets(data.safety_reminders)
        with b:
            st.subheader("Material requests")
            bullets(data.material_requests)


def page_weather():
    st.title("🌦 Weather-Aware Advisory")
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("weather"):
            location = st.text_input("Site location", "Mumbai", help="City or town name. Forecast data from Open-Meteo.")
            activities = st.multiselect("Planned activities",
                                        ["Concrete pouring", "Excavation", "Roofing", "Crane lifting", "Painting (exterior)", "Brickwork", "Steel erection"],
                                        default=["Concrete pouring", "Roofing"])
            go = st.form_submit_button("Get advisory", type="primary", use_container_width=True)
    with right:
        if not go:
            st.info("Choose a location and activities for a 7-day work advisory.")
            return
        if len(location.strip()) < 2 or not activities:
            st.error("Enter a location and pick at least one activity.")
            return
        data, mode = run(services.weather(services.WeatherRequest(location=location, activities=activities)))
        if not data:
            return
        mock_notice(mode)
        st.subheader(data.location)
        st.write(data.forecast_summary)
        cols = st.columns(len(data.days))
        for col, d in zip(cols, data.days):
            with col.container(border=True):
                st.markdown(f"**{pd.Timestamp(d.date).strftime('%a %d')}**")
                st.caption(d.condition)
                st.markdown(f"{d.temp_max_c:.0f}° / {d.temp_min_c:.0f}°")
                st.caption(f"💧 {d.precipitation_mm} mm  \n💨 {d.wind_kmh:.0f} km/h")
                st.markdown(tag(d.work_suitability))
        st.subheader("Activity advice")
        for a in data.activity_advice:
            with st.container(border=True):
                st.markdown(f"**{a.activity}**")
                st.write(a.recommendation)
                if a.best_days:
                    st.caption("Best days: " + ", ".join(a.best_days))
        st.subheader("Precautions")
        bullets(data.precautions)


STARTERS = [
    "What is the minimum curing period for M25 concrete?",
    "How do I check the quality of TMT bars on site?",
    "What cover should I give to a column in a coastal area?",
]


def page_knowledge():
    st.title("📘 Construction Knowledge Assistant")
    history = st.session_state.setdefault("chat", [])

    for m in history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    question = st.chat_input("Ask a construction question…")
    if not history and not question:
        st.caption("Try one of these:")
        for s in STARTERS:
            if st.button(s):
                question = s
    if not question:
        return

    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    turns = [services.ChatTurn(role=m["role"], content=m["content"]) for m in history[:-1]]
    data, mode = run(services.knowledge(services.KnowledgeRequest(question=question, history=turns)))
    if not data:
        history.pop()
        return
    parts = [data.answer]
    if data.key_points:
        parts.append("**Key points**\n" + "\n".join(f"- {k}" for k in data.key_points))
    if data.related_codes_and_standards:
        parts.append("📘 " + " · ".join(data.related_codes_and_standards))
    parts.append(f"_Confidence: {data.confidence}_" + ("  ·  _mock mode_" if mode == "mock" else ""))
    if data.follow_up_questions:
        parts.append("**You could also ask:**\n" + "\n".join(f"- {q}" for q in data.follow_up_questions))
    answer = "\n\n".join(parts)
    history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)


# ---------------------------------------------------------------- navigation

FEATURE_INFO = [
    ("🦺", "Safety Monitoring", "PPE compliance and hazard detection from site photos."),
    ("🧱", "Crack Analysis", "Classify cracks, assess structural risk and plan repairs."),
    ("🏠", "Property Valuation", "Market value range, rent and value drivers."),
    ("📐", "Project Planning", "Phased schedule, cost, resources and risks."),
    ("📋", "Daily Site Assistant", "Turn rough notes into a structured daily report."),
    ("🌦", "Weather Advisory", "7-day work suitability by activity, from a live forecast."),
    ("📘", "Knowledge Assistant", "Ask about codes, materials and site practice."),
]

PAGES = {
    "🏠 Dashboard": page_home,
    "🦺 Safety Monitoring": page_safety,
    "🧱 Crack Analysis": page_cracks,
    "🏘 Property Valuation": page_valuation,
    "📐 Project Planning": page_planning,
    "📋 Daily Site Assistant": page_daily,
    "🌦 Weather Advisory": page_weather,
    "📘 Knowledge Assistant": page_knowledge,
}

with st.sidebar:
    st.markdown("## 🏗️ BuildSense **AI**")
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.divider()
    if config.MOCK_MODE:
        st.warning("Mock mode (no API key)")
    else:
        st.success(f"Live · {config.CLAUDE_MODEL}")

PAGES[choice]()
