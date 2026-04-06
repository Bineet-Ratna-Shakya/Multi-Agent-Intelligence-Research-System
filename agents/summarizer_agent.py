# Financial Summarizer Agent - Generates insights from categorized transactions

from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent


class SummarizerAgent(BaseAgent):
    """Analyzes categorized transactions and generates financial insights."""

    def __init__(self, memory=None):
        super().__init__("FinancialSummarizerAgent", memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        transactions = task.get("transactions", [])
        stats = task.get("summary_stats", {})
        query = task.get("query", "")

        if not transactions:
            return {
                "success": False,
                "error": "No transactions provided for summarization",
                "summaries": []
            }

        self.log_interaction("summarization_task", {
            "num_transactions": len(transactions),
            "query": query
        })

        try:
            summaries = self._generate_financial_summaries(transactions, stats, query)

            result = {
                "success": True,
                "summaries": summaries,
                "total_summarized": len(summaries)
            }

            self.log_interaction("summarization_results", {
                "total_summarized": len(summaries),
                "success": True
            })

            return result

        except Exception as e:
            self.log_interaction("summarization_error", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "summaries": []
            }

    def _generate_financial_summaries(self, transactions: List[Dict[str, Any]],
                                       stats: Dict[str, Any],
                                       query: str) -> List[Dict[str, Any]]:
        summaries = []

        # Overall financial health summary
        net = stats.get("net", 0)
        total_income = stats.get("total_income", 0)
        total_expenses = stats.get("total_expenses", 0)

        health_status = "profitable" if net > 0 else "operating at a loss"
        summaries.append({
            "type": "overview",
            "title": "Financial Overview",
            "summary": (
                f"This period shows total income of ${total_income:,.2f} and total expenses of "
                f"${total_expenses:,.2f}, resulting in a net {'profit' if net > 0 else 'loss'} "
                f"of ${abs(net):,.2f}. The business is currently {health_status}."
            ),
            "confidence": 1.0
        })

        # Expense breakdown summary
        expense_by_cat = stats.get("expense_by_category", {})
        if expense_by_cat:
            top_cats = list(expense_by_cat.items())[:3]
            breakdown_lines = [f"{cat}: ${amt:,.2f}" for cat, amt in top_cats]
            biggest = top_cats[0] if top_cats else ("N/A", 0)
            summaries.append({
                "type": "expense_breakdown",
                "title": "Top Expense Categories",
                "summary": (
                    f"The biggest expense category is **{biggest[0]}** at ${biggest[1]:,.2f}. "
                    f"Top 3 expense categories: {', '.join(breakdown_lines)}. "
                    f"Together they represent "
                    f"${sum(amt for _, amt in top_cats):,.2f} of total spending."
                ),
                "confidence": 1.0
            })

        # Income breakdown summary
        income_by_cat = stats.get("income_by_category", {})
        if income_by_cat:
            top_income = list(income_by_cat.items())[:3]
            income_lines = [f"{cat}: ${amt:,.2f}" for cat, amt in top_income]
            summaries.append({
                "type": "income_breakdown",
                "title": "Income Sources",
                "summary": (
                    f"Revenue streams: {', '.join(income_lines)}. "
                    f"The primary income source is **{top_income[0][0]}** "
                    f"contributing ${top_income[0][1]:,.2f}."
                ),
                "confidence": 1.0
            })

        # Query-specific insight
        if query:
            query_summary = self._answer_query(query, transactions, stats)
            if query_summary:
                summaries.append(query_summary)

        # Actionable recommendations
        recommendations = self._generate_recommendations(stats)
        if recommendations:
            summaries.append(recommendations)

        return summaries

    def _answer_query(self, query: str, transactions: List[Dict[str, Any]],
                       stats: Dict[str, Any]) -> Dict[str, Any]:
        query_lower = query.lower()

        # Handle "biggest expense category" type queries
        if "biggest" in query_lower and "expense" in query_lower:
            cat = stats.get("biggest_expense_category", "N/A")
            amt = stats.get("biggest_expense_amount", 0)
            expense_by_cat = stats.get("expense_by_category", {})
            total_exp = stats.get("total_expenses", 1)
            pct = (amt / total_exp * 100) if total_exp > 0 else 0
            return {
                "type": "query_answer",
                "title": f"Answer: {query}",
                "summary": (
                    f"Your biggest expense category this month is **{cat}** "
                    f"at **${amt:,.2f}**, which is {pct:.1f}% of total expenses. "
                    f"Full expense breakdown: "
                    + ", ".join(f"{k}: ${v:,.2f}" for k, v in expense_by_cat.items())
                    + "."
                ),
                "confidence": 1.0
            }

        # Handle income queries
        if "income" in query_lower or "revenue" in query_lower or "earning" in query_lower:
            total_income = stats.get("total_income", 0)
            income_by_cat = stats.get("income_by_category", {})
            return {
                "type": "query_answer",
                "title": f"Answer: {query}",
                "summary": (
                    f"Total income this period: **${total_income:,.2f}**. "
                    + "Breakdown: "
                    + ", ".join(f"{k}: ${v:,.2f}" for k, v in income_by_cat.items())
                    + "."
                ),
                "confidence": 1.0
            }

        # Handle spending/cost queries
        if "spend" in query_lower or "cost" in query_lower or "expense" in query_lower:
            total_expenses = stats.get("total_expenses", 0)
            expense_by_cat = stats.get("expense_by_category", {})
            return {
                "type": "query_answer",
                "title": f"Answer: {query}",
                "summary": (
                    f"Total expenses this period: **${total_expenses:,.2f}**. "
                    + "Breakdown by category: "
                    + ", ".join(f"{k}: ${v:,.2f}" for k, v in expense_by_cat.items())
                    + "."
                ),
                "confidence": 1.0
            }

        # Handle profit/loss queries
        if "profit" in query_lower or "loss" in query_lower or "net" in query_lower:
            net = stats.get("net", 0)
            return {
                "type": "query_answer",
                "title": f"Answer: {query}",
                "summary": (
                    f"Net {'profit' if net > 0 else 'loss'} this period: **${abs(net):,.2f}**. "
                    f"(Income: ${stats.get('total_income', 0):,.2f}, "
                    f"Expenses: ${stats.get('total_expenses', 0):,.2f})"
                ),
                "confidence": 1.0
            }

        # Generic fallback
        return {
            "type": "query_answer",
            "title": f"Answer: {query}",
            "summary": (
                f"Based on {len(transactions)} transactions: "
                f"Income ${stats.get('total_income', 0):,.2f}, "
                f"Expenses ${stats.get('total_expenses', 0):,.2f}, "
                f"Net ${stats.get('net', 0):,.2f}. "
                f"Biggest expense: {stats.get('biggest_expense_category', 'N/A')} "
                f"(${stats.get('biggest_expense_amount', 0):,.2f})."
            ),
            "confidence": 0.8
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        expense_by_cat = stats.get("expense_by_category", {})
        total_expenses = stats.get("total_expenses", 1)
        total_income = stats.get("total_income", 0)
        net = stats.get("net", 0)

        tips = []

        # Check if any category dominates spending
        for cat, amt in expense_by_cat.items():
            pct = (amt / total_expenses * 100) if total_expenses > 0 else 0
            if pct > 30:
                tips.append(f"**{cat}** accounts for {pct:.0f}% of expenses - consider reviewing for optimization.")

        # Check profit margin
        if total_income > 0:
            margin = (net / total_income) * 100
            if margin < 20:
                tips.append(f"Profit margin is only {margin:.1f}% - aim for at least 20%.")
            elif margin > 40:
                tips.append(f"Strong profit margin of {margin:.1f}% - well managed!")

        if not tips:
            tips.append("Spending appears balanced across categories.")

        return {
            "type": "recommendations",
            "title": "Actionable Recommendations",
            "summary": " ".join(tips),
            "confidence": 0.9
        }
