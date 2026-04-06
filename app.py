# Streamlit UI - AI Bookkeeping Agent

import streamlit as st
import json
import os
import pandas as pd
import traceback
from datetime import datetime
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import DEFAULT_CSV_PATH

st.set_page_config(
    page_title="AI Bookkeeping Agent",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.coordinator = None
    st.session_state.chat_history = []


@st.cache_resource
def setup_logging():
    try:
        os.makedirs("logs", exist_ok=True)
        return setup_logger("WebApp", "logs/webapp.log")
    except Exception as e:
        st.error(f"Failed to setup logging: {e}")
        return None


logger = setup_logging()


@st.cache_resource
def get_coordinator():
    try:
        os.makedirs("reports", exist_ok=True)
        return CoordinatorAgent()
    except Exception as e:
        st.error(f"Failed to initialize coordinator: {e}")
        if logger:
            logger.error(f"Failed to initialize coordinator: {e}")
        return None


def run_analysis(query, csv_path=None):
    try:
        coordinator = get_coordinator()
        if not coordinator:
            return False, "Failed to initialize the system"

        task = {"query": query.strip()}
        if csv_path:
            task["csv_path"] = csv_path

        result = coordinator.execute(task)

        if result["success"]:
            return True, result
        else:
            return False, result.get("error", "Unknown error occurred")

    except Exception as e:
        error_msg = f"System error: {str(e)}"
        if logger:
            logger.error(f"Analysis failed: {error_msg}\n{traceback.format_exc()}")
        return False, error_msg


def main():
    st.title("AI Bookkeeping Agent")
    st.markdown("**Multi-agent financial intelligence system - Analyze your transactions with AI.**")
    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        uploaded_file = st.file_uploader("Upload CSV (optional)", type=["csv"],
                                          help="Upload your own transactions CSV or use the built-in demo data")

        csv_path = DEFAULT_CSV_PATH
        if uploaded_file is not None:
            os.makedirs("data", exist_ok=True)
            upload_path = os.path.join("data", "uploaded_transactions.csv")
            with open(upload_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            csv_path = upload_path
            st.success("CSV uploaded!")

        st.divider()

        st.subheader("Quick Questions")
        quick_queries = [
            "What's my biggest expense category this month?",
            "Show me my income breakdown",
            "What's my net profit?",
            "How much am I spending on marketing?",
            "Give me a full financial overview"
        ]

        for q in quick_queries:
            if st.button(q, use_container_width=True):
                st.session_state["prefilled_query"] = q

        st.divider()

        # Show raw data preview
        st.subheader("Data Preview")
        try:
            preview_df = pd.read_csv(csv_path)
            st.dataframe(preview_df.head(10), use_container_width=True, height=300)
        except Exception as e:
            st.error(f"Could not load CSV: {e}")

    # Main chat area
    query = st.chat_input("Ask about your finances...")

    # Check for prefilled query from sidebar
    if "prefilled_query" in st.session_state:
        query = st.session_state.pop("prefilled_query")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if query:
        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Process and show response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your transactions..."):
                success, result_data = run_analysis(query, csv_path)

            if success:
                report = result_data["report"]
                stats = result_data["stats"]
                financial_stats = report.get("financial_stats", {})

                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Transactions", stats.get("transactions_loaded", 0))
                with col2:
                    st.metric("Total Income", f"${financial_stats.get('total_income', 0):,.2f}")
                with col3:
                    st.metric("Total Expenses", f"${financial_stats.get('total_expenses', 0):,.2f}")
                with col4:
                    net = financial_stats.get("net", 0)
                    st.metric("Net Profit/Loss", f"${net:,.2f}",
                              delta=f"{'Profit' if net > 0 else 'Loss'}")

                st.divider()

                # Show insights
                insights = report.get("insights", [])
                response_text = ""
                for insight in insights:
                    title = insight.get("title", "")
                    summary = insight.get("summary", "")
                    st.markdown(f"**{title}**")
                    st.markdown(summary)
                    st.markdown("")
                    response_text += f"**{title}**: {summary}\n\n"

                # Expense chart
                expense_by_cat = financial_stats.get("expense_by_category", {})
                if expense_by_cat:
                    st.divider()
                    st.markdown("**Expense Distribution**")
                    chart_df = pd.DataFrame(
                        list(expense_by_cat.items()),
                        columns=["Category", "Amount"]
                    )
                    st.bar_chart(chart_df.set_index("Category"))

                # Download button
                st.divider()
                report_json = json.dumps(report, indent=2)
                st.download_button(
                    "Download Full Report (JSON)",
                    data=report_json,
                    file_name=f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text or "Analysis complete. See the charts and metrics above."
                })
            else:
                error_msg = f"Analysis failed: {result_data}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    # Welcome screen when no query
    if not query and not st.session_state.chat_history:
        st.info("Ask a question about your finances using the chat input below, or click a quick question in the sidebar!")

        st.subheader("How It Works")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **1. TransactionAgent**
            Loads your CSV and categorizes each transaction (Marketing, Operations, Payroll, etc.)
            """)
        with col2:
            st.markdown("""
            **2. SummarizerAgent**
            Generates financial insights, answers your questions, and creates recommendations.
            """)
        with col3:
            st.markdown("""
            **3. VerifierAgent**
            Validates categorizations, detects anomalies, and flags unusual spending.
            """)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please refresh the page and try again.")
        if logger:
            logger.error(f"Application error: {str(e)}\n{traceback.format_exc()}")
