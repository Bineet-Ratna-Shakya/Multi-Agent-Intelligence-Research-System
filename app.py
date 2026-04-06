# Streamlit UI - AI Bookkeeping Agent (Gemini-powered)

import streamlit as st
import json
import os
import pandas as pd
import traceback
from datetime import datetime
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import DEFAULT_CSV_PATH, GEMINI_API_KEY

st.set_page_config(page_title="AI Bookkeeping Agent", page_icon="$", layout="wide", initial_sidebar_state="expanded")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "csv_path" not in st.session_state:
    st.session_state.csv_path = DEFAULT_CSV_PATH


@st.cache_resource
def get_coordinator():
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    return CoordinatorAgent()


def analyze(query: str, csv_path: str):
    coordinator = get_coordinator()
    return coordinator.execute({"query": query.strip(), "csv_path": csv_path})


# ── Sidebar ──

with st.sidebar:
    st.header("AI Bookkeeping Agent")
    st.caption("Powered by Gemini 2.0 Flash")

    # API key check
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your-api-key-here":
        st.error("GEMINI_API_KEY not set in .env file")
        api_key_input = st.text_input("Enter Gemini API Key:", type="password")
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.success("Key set for this session!")
            st.rerun()

    uploaded = st.file_uploader("Upload your CSV", type=["csv"],
                                 help="Optional - uses demo data if empty")
    if uploaded:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "uploaded.csv")
        with open(path, "wb") as f:
            f.write(uploaded.getvalue())
        st.session_state.csv_path = path
        st.success("CSV loaded!")

    st.divider()
    st.markdown("**Try asking:**")

    suggestions = [
        "What's my biggest expense category this month?",
        "Break down my income sources",
        "Am I profitable? What's my margin?",
        "How much am I spending on marketing? Is it worth it?",
        "Any suspicious or unusual transactions?",
        "What should I cut to save money?",
        "Compare my payroll vs marketing costs",
        "Give me a full financial health check",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"btn_{s}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.caption("Data Preview")
    try:
        df = pd.read_csv(st.session_state.csv_path)
        st.dataframe(df.head(8), use_container_width=True, height=250)
    except Exception:
        st.warning("Could not preview CSV")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ── Main Chat ──

st.title("AI Bookkeeping Agent")

# Render history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get query
query = st.chat_input("Ask anything about your finances...")
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is analyzing your transactions..."):
            result = analyze(query, st.session_state.csv_path)

        if result["success"]:
            report = result["report"]
            insights = report.get("insights", [])

            full_response = ""

            for insight in insights:
                answer = insight.get("answer", "")
                itype = insight.get("type", "")

                if itype == "red_flags":
                    st.warning("**Red Flags Detected:**")
                    st.markdown(answer)
                    full_response += f"\n\n**Red Flags:**\n{answer}"
                    continue

                st.markdown(answer)
                full_response += answer

                # Show chart
                chart_data = insight.get("chart_data", {})
                chart_type = insight.get("chart_type")

                if chart_data and chart_type in ("bar", "comparison"):
                    chart_df = pd.DataFrame(
                        list(chart_data.items()), columns=["Category", "Amount"]
                    ).set_index("Category")
                    st.bar_chart(chart_df)
                elif chart_data and chart_type == "line":
                    chart_df = pd.DataFrame(
                        list(chart_data.items()), columns=["Date", "Amount"]
                    ).set_index("Date")
                    st.line_chart(chart_df)

            # Show which model was used
            st.caption(f"Model: {result['stats'].get('model', 'gemini')} | Transactions: {result['stats'].get('transactions_loaded', '?')}")

            # Download
            report_json = json.dumps(report, indent=2, default=str)
            st.download_button("Download Report", data=report_json,
                               file_name=f"report_{datetime.now().strftime('%H%M%S')}.json",
                               mime="application/json")

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": full_response or "Analysis complete."
            })
        else:
            err = result.get("error", "Unknown error")
            if "GEMINI_API_KEY" in err:
                st.error("Gemini API key not configured. Add it in the sidebar or in your .env file.")
            else:
                st.error(f"Error: {err}")
            st.session_state.chat_history.append({"role": "assistant", "content": f"Error: {err}"})

# Welcome
if not st.session_state.chat_history:
    st.info("Ask anything about your finances. This agent uses **Gemini 2.0 Flash** to actually reason about your data - not just pattern matching.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**1. TransactionAgent**\n\nGemini categorizes your transactions intelligently")
    with col2:
        st.markdown("**2. AnalystAgent**\n\nGemini reasons about your question and generates insights")
    with col3:
        st.markdown("**3. VerifierAgent**\n\nGemini audits for red flags and anomalies")
