# Streamlit UI - AI Bookkeeping Agent (Conversational)

import streamlit as st
import json
import os
import pandas as pd
import traceback
from datetime import datetime
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import DEFAULT_CSV_PATH

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
    task = {"query": query.strip(), "csv_path": csv_path}
    return coordinator.execute(task)


# ── Sidebar ──────────────────────────────────────────────────────

with st.sidebar:
    st.header("AI Bookkeeping Agent")

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
        "What's my biggest expense category?",
        "Show me income breakdown",
        "What's my net profit?",
        "How much on marketing?",
        "Any unusual transactions?",
        "Compare my expense categories",
        "Show me spending trends",
        "How many transactions do I have?",
        "Tell me about payroll expenses",
        "What's my largest single expense?",
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


# ── Main Chat ────────────────────────────────────────────────────

st.title("AI Bookkeeping Agent")

# Render chat history (without charts - just text)
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get query from chat input or sidebar button
query = st.chat_input("Ask about your finances...")
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    # User message
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            result = analyze(query, st.session_state.csv_path)

        if result["success"]:
            report = result["report"]
            insights = report.get("insights", [])
            stats = report.get("financial_stats", {})
            intent = report.get("intent", "overview")

            # Build the text response
            response_parts = []

            for insight in insights:
                answer = insight.get("answer", "")
                detail = insight.get("detail", "")
                title = insight.get("title", "")

                if insight.get("type") == "warnings":
                    st.caption(f"Note: {answer}")
                    continue

                st.markdown(f"**{title}**")
                st.markdown(answer)
                response_parts.append(f"**{title}**: {answer}")

                if detail:
                    with st.expander("Details"):
                        st.markdown(detail)

                # Show chart if data exists
                chart_data = insight.get("chart_data", {})
                chart_type = insight.get("chart_type")

                if chart_data and chart_type == "bar":
                    chart_df = pd.DataFrame(
                        list(chart_data.items()), columns=["Category", "Amount"]
                    ).set_index("Category")
                    st.bar_chart(chart_df)

                elif chart_data and chart_type == "comparison":
                    chart_df = pd.DataFrame(
                        list(chart_data.items()), columns=["Type", "Amount"]
                    ).set_index("Type")
                    st.bar_chart(chart_df)

                elif chart_data and chart_type == "line":
                    chart_df = pd.DataFrame(
                        list(chart_data.items()), columns=["Date", "Amount"]
                    ).set_index("Date")
                    st.line_chart(chart_df)

            # Download
            report_json = json.dumps(report, indent=2, default=str)
            st.download_button("Download Report", data=report_json,
                               file_name=f"report_{datetime.now().strftime('%H%M%S')}.json",
                               mime="application/json")

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "\n\n".join(response_parts) if response_parts else "Analysis complete."
            })
        else:
            err = f"Error: {result.get('error', 'Unknown')}"
            st.error(err)
            st.session_state.chat_history.append({"role": "assistant", "content": err})

# Welcome screen
if not st.session_state.chat_history:
    st.info("Ask a question about your finances, or click a suggestion in the sidebar.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**TransactionAgent**\n\nLoads & categorizes your transactions")
    with col2:
        st.markdown("**SummarizerAgent**\n\nAnswers your specific question")
    with col3:
        st.markdown("**VerifierAgent**\n\nValidates data & flags anomalies")
