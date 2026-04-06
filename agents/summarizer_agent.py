# Financial Summarizer Agent - Uses Gemini to actually reason about finances

import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.llm import ask

SYSTEM_PROMPT = """You are an expert AI financial analyst and bookkeeping assistant.

You analyze transaction data and provide clear, actionable financial insights.
You answer the user's specific question - don't dump everything, be focused and conversational.
Use numbers, percentages, and comparisons. Be direct.

When you respond:
- Answer the specific question asked, don't give a generic overview unless asked
- Use **bold** for important numbers and categories
- Be concise but thorough
- If you spot something concerning, flag it
- Give actionable advice when appropriate
"""


class SummarizerAgent(BaseAgent):
    """Uses Gemini to actually reason about financial data and answer questions."""

    def __init__(self, memory=None):
        super().__init__("FinancialAnalystAgent", memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        transactions = task.get("transactions", [])
        stats = task.get("summary_stats", {})
        query = task.get("query", "")

        if not transactions:
            return {"success": False, "error": "No transactions to analyze", "summaries": []}

        self.log_interaction("analysis_task", {"query": query, "num_transactions": len(transactions)})

        try:
            # Build context for the LLM
            data_context = self._build_context(transactions, stats)

            # Ask Gemini to answer the user's question
            prompt = f"""Here is the financial data:

{data_context}

User's question: {query}

Analyze the data and answer their question. Be specific with numbers. Format your response in markdown."""

            response = ask(prompt, system_instruction=SYSTEM_PROMPT)

            # Also ask for structured chart data if relevant
            chart_data = self._get_chart_data(query, stats, transactions)

            result = {
                "success": True,
                "summaries": [{
                    "type": "llm_analysis",
                    "title": "Financial Analysis",
                    "answer": response,
                    "detail": "",
                    "chart_data": chart_data.get("data", {}),
                    "chart_type": chart_data.get("type"),
                    "confidence": 1.0
                }],
                "total_summarized": 1,
                "intent": "llm_analysis"
            }

            self.log_interaction("analysis_results", {"success": True})
            return result

        except Exception as e:
            self.log_interaction("analysis_error", {"error": str(e)})
            return {"success": False, "error": str(e), "summaries": []}

    def _build_context(self, transactions: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Build a concise data summary for the LLM prompt."""
        lines = []

        # Summary stats
        lines.append("## Summary Statistics")
        lines.append(f"- Total Income: ${stats.get('total_income', 0):,.2f}")
        lines.append(f"- Total Expenses: ${stats.get('total_expenses', 0):,.2f}")
        lines.append(f"- Net Profit/Loss: ${stats.get('net', 0):,.2f}")
        lines.append(f"- Total Transactions: {stats.get('transaction_count', 0)}")
        lines.append("")

        # Expense breakdown
        expense_map = stats.get("expense_by_category", {})
        if expense_map:
            lines.append("## Expenses by Category")
            for cat, amt in expense_map.items():
                lines.append(f"- {cat}: ${amt:,.2f}")
            lines.append("")

        # Income breakdown
        income_map = stats.get("income_by_category", {})
        if income_map:
            lines.append("## Income by Source")
            for cat, amt in income_map.items():
                lines.append(f"- {cat}: ${amt:,.2f}")
            lines.append("")

        # Individual transactions
        lines.append("## All Transactions")
        lines.append("Date | Description | Amount | Category")
        lines.append("---|---|---|---")
        for t in transactions:
            lines.append(f"{t['date']} | {t['description']} | ${t['amount']:,.2f} | {t['category']}")

        return "\n".join(lines)

    def _get_chart_data(self, query: str, stats: Dict[str, Any],
                         transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine what chart to show based on the query."""
        q = query.lower()

        # Expense-related → show expense breakdown chart
        if any(w in q for w in ["expense", "spend", "cost", "biggest", "most money", "where"]):
            return {"data": stats.get("expense_by_category", {}), "type": "bar"}

        # Income-related → show income chart
        if any(w in q for w in ["income", "revenue", "earning", "money com"]):
            return {"data": stats.get("income_by_category", {}), "type": "bar"}

        # Profit → show income vs expenses
        if any(w in q for w in ["profit", "loss", "net", "bottom line"]):
            return {
                "data": {"Income": stats.get("total_income", 0), "Expenses": stats.get("total_expenses", 0)},
                "type": "bar"
            }

        # Trend → show daily spending
        if any(w in q for w in ["trend", "over time", "daily"]):
            daily = {}
            for t in transactions:
                d = t["date"]
                if t["amount"] < 0:
                    daily[d] = daily.get(d, 0) + abs(t["amount"])
            return {"data": dict(sorted(daily.items())), "type": "line"}

        # Default → expense breakdown
        return {"data": stats.get("expense_by_category", {}), "type": "bar"}
