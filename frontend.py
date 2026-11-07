"""Streamlit frontend for Ashwani's LangGraph + MCP travel planner."""
from __future__ import annotations
import asyncio
import uuid
from datetime import datetime

import streamlit as st
from config import PROJECT_ROOT, env
from main import graph_runtime, initial_state
from pdf_export import build_travel_pdf

st.set_page_config(page_title="Ashwani AI Travel Planner", page_icon="✈️", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #080d14;
}

/* ── Hero ── */
.hero-wrapper {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 2rem;
    height: 280px;
}
.hero-bg {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    filter: brightness(0.35);
    position: absolute;
    top: 0; left: 0;
}
.hero-content {
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
}
.hero-badge {
    background: rgba(58,123,213,0.25);
    border: 1px solid rgba(58,123,213,0.5);
    color: #7ab8f5 !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.9rem;
    display: inline-block;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.6rem;
    line-height: 1.2;
}
.hero-sub {
    color: #94adc8;
    font-size: 1rem;
    max-width: 560px;
}

/* ── Input card ── */
.input-card {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
}
.input-label {
    color: #7ab8f5;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Quick destinations ── */
.dest-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.2rem;
}
.dest-chip {
    background: #111b2b;
    border: 1px solid #1e3050;
    color: #f7fdf4;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
}
.dest-chip:hover { background: #1a2e47; border-color: #3a7bd5; color: #fff; }

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 50%, #0a3d75 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2.5rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    box-shadow: 0 0 24px rgba(26,107,191,0.35), 0 4px 15px rgba(0,0,0,0.4) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 0 40px rgba(26,107,191,0.6), 0 6px 20px rgba(0,0,0,0.5) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #2278d4 0%, #1057a0 50%, #0d4a8a 100%) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* ── Agent status cards ── */
[data-testid="stStatusWidget"] {
    background: #0e1a2e !important;
    border: 1px solid #1e3050 !important;
    border-radius: 12px !important;
}
[data-testid="stStatusWidget"] > div:first-child {
    background: #0e1a2e !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: #0a1520 !important;
    color: #ffffff !important;
    padding: 0.25rem 0.5rem !important;
}
[data-testid="stStatusWidget"] * { color: #ffffff !important; }
[data-testid="stStatusWidget"] a { color: #4ea8f0 !important; }
[data-testid="stStatusWidget"] hr { border-color: #1e3050 !important; }

/* ── Section headers ── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2e44;
}
.sec-head span { font-size: 1.15rem; font-weight: 600; color: #e0edf8; }

/* ── Metric bar ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-box {
    flex: 1;
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val { font-size: 1.8rem; font-weight: 700; color: #4ea8f0; }
.metric-lbl { font-size: 0.78rem; color: #5a7a96; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Final plan ── */
.final-card {
    background: linear-gradient(160deg, #0c1a2e 0%, #0a1520 100%);
    border: 1px solid #1e3a5c;
    border-left: 4px solid #3a7bd5;
    border-radius: 14px;
    padding: 1.8rem;
    line-height: 1.8;
    color: #cce0f5;
    font-size: 0.95rem;
}

/* ── Save bar ── */
.save-bar {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    color: #5a8ab0;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #090e18 !important;
    border-right: 1px solid #141f30 !important;
}
.sidebar-chip {
    background: #0e1a2b;
    border: 1px solid #1a2e44;
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.83rem;
    color: #7aa8cc;
}
.sidebar-title { color: #e0edf8; font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem; }

/* Hide branding */
#MainMenu, footer, header { visibility: hidden; }

/* Textarea */
.stTextArea textarea {
    background: #0a1520 !important;
    border: 1px solid #1e2e44 !important;
    border-radius: 10px !important;
    color: #e8f4ff !important;
    font-size: 0.95rem !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border-color: #3a7bd5 !important;
    box-shadow: 0 0 0 2px rgba(58,123,213,0.2) !important;
}
.stTextArea textarea::placeholder { color: #4a6a85 !important; }

/* Text input (sidebar User ID field) */
input[type="text"], .stTextInput input {
    background: #0e1a2b !important;
    border: 1px solid #1a2e44 !important;
    border-radius: 8px !important;
    color: #e0edf8 !important;
}
input[type="text"]:focus, .stTextInput input:focus {
    border-color: #3a7bd5 !important;
    box-shadow: 0 0 0 2px rgba(58,123,213,0.2) !important;
}
input[type="text"]::placeholder { color: #3a5570 !important; }

/* All Streamlit labels — dark bg → light text */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
    color: #7ab8f5 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
}

/* General markdown / paragraph text */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: #cce0f5 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #e8f4ff !important; }
.stMarkdown code {
    background: #0e1a2b !important;
    color: #7ab8f5 !important;
    padding: 0.15em 0.4em;
    border-radius: 4px;
}

/* Metric labels — was #5a7a96 (too dim on dark bg) */
.metric-lbl { color: #7aa8cc !important; }

/* Save bar — was #5a8ab0 (slightly dim) */
.save-bar { color: #8ab8d8 !important; }
.save-bar code { color: #7ab8f5 !important; background: #0a1520 !important; }

/* Streamlit warning / info / success on dark bg */
.stAlert { background: #0e1a2b !important; border-radius: 10px !important; }
.stAlert p, .stAlert div { color: #e0edf8 !important; }

/* Sidebar text & dividers */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: #a0c4e0 !important; }
section[data-testid="stSidebar"] hr { border-color: #1a2e44 !important; }

/* Download button — light bg → dark text  */
div[data-testid="stDownloadButton"] > button {
    background: #1a3a5c !important;
    color: #e8f4ff !important;
    border: 1px solid #2a5080 !important;
    border-radius: 10px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# Frontend for the four-agent MCP version.
AGENT_META = {
    "flight_agent": ("✈️", "Flight Agent"),
    "hotel_agent": ("🏨", "Hotel Agent"),
    "weather_agent": ("🌤️", "Weather Agent"),
    "itinerary_agent": ("🗓️", "Itinerary Agent"),
}

if "trip_request" not in st.session_state:
    st.session_state.trip_request = ""

with st.sidebar:
    st.markdown("<div class='sidebar-title'>🌍 Ashwani AI Travel Planner</div>", unsafe_allow_html=True)
    st.caption("LangGraph + MCP demonstration")
    st.divider()
    st.markdown("<div class='sidebar-title'>Powered by</div>", unsafe_allow_html=True)
    for tech in ["LangGraph + PostgreSQL", "MCP (three integrations)", "Groq · " + env('GROQ_MODEL', 'openai/gpt-oss-120b'), "Tavily", "AviationStack", "OpenWeatherMap"]:
        st.markdown(f"<div class='sidebar-chip'>{tech}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Agent Pipeline</div>", unsafe_allow_html=True)
    for icon, label in AGENT_META.values():
        st.markdown(f"<div class='sidebar-chip'>{icon} {label}</div>", unsafe_allow_html=True)
    st.caption("Research only: no reservations or price guarantees.")

st.markdown("""
<div class="hero-wrapper">
  <img class="hero-bg" src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1400&q=80" alt="airplane"/>
  <div class="hero-content">
    <div class="hero-badge">MCP + LANGGRAPH MULTI-AGENT WORKFLOW</div>
    <div class="hero-title">✈️ Ashwani AI Travel Planner</div>
    <div class="hero-sub">Research flights, hotels and short-range weather; generate an itinerary and export a PDF.</div>
  </div>
</div>
""", unsafe_allow_html=True)

DESTINATIONS = [
    ("Tokyo", "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=300&q=70"),
    ("Paris", "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=300&q=70"),
    ("Bangkok", "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=300&q=70"),
    ("Rome", "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=300&q=70"),
    ("Dubai", "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=300&q=70"),
]
cols = st.columns(len(DESTINATIONS))
for col, (name, img_url) in zip(cols, DESTINATIONS):
    with col:
        # Only static trusted markup, not LLM text.
        st.markdown(
            f'<div style="height:90px;border-radius:10px;overflow:hidden;position:relative">'
            f'<img src="{img_url}" style="width:100%;height:100%;object-fit:cover;filter:brightness(.55)"/>'
            f'<b style="position:absolute;bottom:8px;left:0;right:0;text-align:center;color:white">{name}</b></div>',
            unsafe_allow_html=True,
        )

st.markdown("<div class='input-label'>Describe your trip</div>", unsafe_allow_html=True)
QUICK = [
    "7-day Japan trip departing Hyderabad under ₹200,000",
    "Paris 5-day trip departing Mumbai under ₹250,000",
    "Dubai weekend departing Hyderabad under ₹60,000",
    "Bangkok 5-day trip departing Delhi under ₹80,000",
]
quick_cols = st.columns(len(QUICK))
for i, (col, prompt) in enumerate(zip(quick_cols, QUICK)):
    with col:
        if st.button(["Japan", "Paris", "Dubai", "Bangkok"][i], key=f"quick_{i}"):
            st.session_state.trip_request = prompt

request = st.text_area(
    "Travel request", key="trip_request", height=110,
    placeholder="Plan a 7-day Japan trip from Hyderabad including flights, hotels and sightseeing...",
)
generate = st.button("🚀 Generate My Travel Plan", use_container_width=True, type="primary")


async def _execute(query: str, thread_id: str, status) -> dict:
    collected = {
        "flight_results": "", "hotel_results": "", "weather_results": "",
        "itinerary": "", "llm_calls": 0,
    }
    completed = []
    async with graph_runtime() as app:
        async for chunk in app.astream(
            initial_state(query),
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue
                completed.append(node)
                for field in ("flight_results", "hotel_results", "weather_results", "itinerary"):
                    if field in update:
                        collected[field] = str(update[field])
                # Node deltas: llm_calls uses operator.add in TravelState.
                collected['llm_calls'] += int(update.get('llm_calls', 0))
                icon, name = AGENT_META.get(node, ("⚙️", node))
                with status:
                    st.write(f"{icon} {name} completed")
    collected['completed_nodes'] = completed
    return collected


if generate:
    if not request.strip():
        st.warning("Please enter a travel request before generating.")
    else:
        thread_id = str(uuid.uuid4())  # new checkpoint thread for each new plan
        with st.status("Running agent workflow...", expanded=True) as status:
            try:
                collected = asyncio.run(_execute(request.strip(), thread_id, status))
                status.update(label="Agent workflow completed", state="complete", expanded=False)
                stamp = datetime.now()
                pdf_data = build_travel_pdf(request.strip(), thread_id, collected, stamp)
                filename = f"travel_plan_{stamp:%Y%m%d_%H%M%S_%f}.pdf"
                save_dir = PROJECT_ROOT / 'travel_plans'
                save_dir.mkdir(parents=True, exist_ok=True)
                (save_dir / filename).write_bytes(pdf_data)
                st.session_state.last_result = {
                    'collected': collected,
                    'thread_id': thread_id,
                    'pdf': pdf_data,
                    'file_name': filename,
                }
            except Exception as exc:
                status.update(label="Agent workflow failed", state="error", expanded=True)
                st.error(f"Workflow could not finish ({type(exc).__name__}). Check the terminal and MCP configuration.")

result = st.session_state.get('last_result')
if result:
    data = result['collected']
    st.divider()
    st.subheader('🤖 Agent results')
    for label, field in [
        ('Flight Agent', 'flight_results'),
        ('Hotel Agent', 'hotel_results'),
        ('Weather Agent', 'weather_results'),
        ('Itinerary Agent', 'itinerary'),
    ]:
        with st.expander(label, expanded=(field == 'itinerary')):
            st.markdown(data.get(field) or '_No results available._')
    m1, m2, m3 = st.columns(3)
    m1.metric('Completed agents', len(data.get('completed_nodes', [])))
    m2.metric('Successful LLM responses', data.get('llm_calls', 0))
    m3.metric('Thread', result['thread_id'][:8])
    st.caption('AI output may be inaccurate. Verify prices, availability, visa rules, and weather for your actual dates.')
    st.download_button(
        '⬇️ Download PDF Plan', data=result['pdf'], file_name=result['file_name'],
        mime='application/pdf', use_container_width=True,
    )
    st.caption(f"Auto-saved locally: travel_plans/{result['file_name']}")
