# Financial Summarizer Agent - Query-aware financial analysis

import re
from typing import Dict, Any, List, Tuple
from agents.base_agent import BaseAgent


# Maps query intent to what kind of response to generate
INTENT_PATTERNS = [
    # (intent_name, patterns, required_context)
    ("biggest_expense",    [r"biggest\s+expense", r"largest\s+expense", r"most\s+spend", r"top\s+expense", r"highest\s+expense", r"where.*most.*money\s+go"], "expenses"),
    ("smallest_expense",   [r"smallest\s+expense", r"least\s+spend", r"lowest\s+expense"], "expenses"),
    ("category_detail",    [r"(marketing|payroll|operations|software|travel|professional|finance)\b"], "category"),
    ("income_breakdown",   [r"income\b", r"revenue\b", r"earning", r"money\s+com", r"how\s+much.*mak", r"where.*income"], "income"),
    ("expense_breakdown",  [r"expense\s+breakdown", r"all\s+expenses", r"spending\s+breakdown", r"where.*spend"], "expenses"),
    ("profit_loss",        [r"profit", r"loss", r"net\b", r"bottom\s+line", r"how.*doing\s+financial"], "profit"),
    ("compare_categories", [r"compare", r"versus", r"vs\b", r"which.*more", r"which.*less"], "compare"),
    ("trend",              [r"trend", r"over\s+time", r"growing", r"increasing", r"decreasing", r"week.*over"], "trend"),
    ("anomaly",            [r"unusual", r"anomal", r"weird", r"strange", r"outlier", r"flag", r"suspicious"], "anomaly"),
    ("count",              [r"how\s+many\s+transaction", r"number\s+of", r"total\s+transaction", r"count"], "count"),
    ("overview",           [r"overview", r"summary", r"full.*report", r"everything", r"all\b", r"general", r"overall"], "overview"),
    ("single_transaction", [r"biggest\s+single", r"largest\s+single", r"largest\s+transaction", r"most\s+expensive"], "single"),
]


class SummarizerAgent(BaseAgent):
    """Understands the user's financial query and generates a focused, relevant answer."""

    def __init__(self, memory=None):
        super().__init__("FinancialSummarizerAgent", memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        transactions = task.get("transactions", [])
        all_transactions = task.get("all_transactions", transactions)
        stats = task.get("summary_stats", {})
        all_stats = task.get("all_stats", stats)
        query = task.get("query", "")
        available_categories = task.get("available_categories", {})

        if not transactions:
            return {"success": False, "error": "No transactions to analyze", "summaries": []}

        self.log_interaction("summarization_task", {"query": query, "num_transactions": len(transactions)})

        try:
            intent, matched_category = self._detect_intent(query, available_categories)
            self.logger.info(f"Detected intent: {intent}, category: {matched_category}")

            response = self._generate_response(intent, matched_category, query,
                                                 transactions, all_transactions, stats, all_stats)

            self.log_interaction("summarization_results", {"intent": intent, "success": True})

            return {
                "success": True,
                "intent": intent,
                "summaries": [response],
                "total_summarized": 1
            }

        except Exception as e:
            self.log_interaction("summarization_error", {"error": str(e)})
            return {"success": False, "error": str(e), "summaries": []}

    def _detect_intent(self, query: str, available_categories: Dict) -> Tuple[str, str]:
        query_lower = query.lower().strip()

        # Check for specific category mention first
        matched_category = None
        all_cats = available_categories.get("expense", []) + available_categories.get("income", [])
        for cat in all_cats:
            if cat.lower() in query_lower:
                matched_category = cat
                break

        # Match intent patterns
        for intent_name, patterns, _ in INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if intent_name == "category_detail" and not matched_category:
                        # Extract category from the regex match
                        m = re.search(pattern, query_lower)
                        if m:
                            matched_category = m.group(1).title()
                            if matched_category == "Professional":
                                matched_category = "Professional Services"
                    return intent_name, matched_category

        # If a category was mentioned but no other intent, show category detail
        if matched_category:
            return "category_detail", matched_category

        return "overview", None

    def _generate_response(self, intent: str, category: str, query: str,
                            transactions: List, all_transactions: List,
                            stats: Dict, all_stats: Dict) -> Dict[str, Any]:

        handlers = {
            "biggest_expense": self._handle_biggest_expense,
            "smallest_expense": self._handle_smallest_expense,
            "category_detail": self._handle_category_detail,
            "income_breakdown": self._handle_income,
            "expense_breakdown": self._handle_expense_breakdown,
            "profit_loss": self._handle_profit_loss,
            "compare_categories": self._handle_compare,
            "anomaly": self._handle_anomaly,
            "count": self._handle_count,
            "single_transaction": self._handle_single_transaction,
            "trend": self._handle_trend,
            "overview": self._handle_overview,
        }

        handler = handlers.get(intent, self._handle_overview)
        return handler(query=query, category=category, transactions=transactions,
                       all_transactions=all_transactions, stats=stats, all_stats=all_stats)

    # ── Response Handlers ──────────────────────────────────────────

    def _handle_biggest_expense(self, **ctx) -> Dict:
        stats = ctx["stats"]
        cat = stats.get("biggest_expense_category", "N/A")
        amt = stats.get("biggest_expense_amount", 0)
        total = stats.get("total_expenses", 1)
        pct = (amt / total * 100) if total > 0 else 0
        expense_map = stats.get("expense_by_category", {})

        ranking = "\n".join(f"  {i+1}. **{c}** — ${a:,.2f} ({a/total*100:.0f}%)"
                            for i, (c, a) in enumerate(expense_map.items()))

        return {
            "type": "biggest_expense",
            "title": "Biggest Expense Category",
            "answer": (
                f"Your biggest expense category is **{cat}** at **${amt:,.2f}**, "
                f"which is **{pct:.0f}%** of your total spending (${total:,.2f})."
            ),
            "detail": f"Full ranking:\n{ranking}",
            "chart_data": expense_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _handle_smallest_expense(self, **ctx) -> Dict:
        expense_map = ctx["stats"].get("expense_by_category", {})
        if not expense_map:
            return self._simple("No expenses found.", "smallest_expense")
        items = sorted(expense_map.items(), key=lambda x: x[1])
        cat, amt = items[0]
        return {
            "type": "smallest_expense",
            "title": "Smallest Expense Category",
            "answer": f"Your smallest expense category is **{cat}** at **${amt:,.2f}**.",
            "detail": "",
            "chart_data": expense_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _handle_category_detail(self, **ctx) -> Dict:
        category = ctx["category"]
        txns = [t for t in ctx["all_transactions"] if t["category"].lower() == category.lower()]

        if not txns:
            return self._simple(f"No transactions found in the **{category}** category.", "category_detail")

        total = sum(abs(t["amount"]) for t in txns)
        count = len(txns)
        items = "\n".join(f"  - {t['date']}: {t['description']} — ${abs(t['amount']):,.2f}" for t in txns)

        return {
            "type": "category_detail",
            "title": f"{category} Transactions",
            "answer": f"You have **{count}** transactions in **{category}** totaling **${total:,.2f}**.",
            "detail": f"Transactions:\n{items}",
            "chart_data": {},
            "chart_type": None,
            "confidence": 1.0
        }

    def _handle_income(self, **ctx) -> Dict:
        stats = ctx["stats"]
        total = stats.get("total_income", 0)
        income_map = stats.get("income_by_category", {})
        count = stats.get("income_count", 0)

        breakdown = "\n".join(f"  - **{c}**: ${a:,.2f}" for c, a in income_map.items())

        return {
            "type": "income_breakdown",
            "title": "Income Breakdown",
            "answer": f"Total income: **${total:,.2f}** across **{count}** transactions.",
            "detail": f"By source:\n{breakdown}" if breakdown else "",
            "chart_data": income_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _handle_expense_breakdown(self, **ctx) -> Dict:
        stats = ctx["stats"]
        total = stats.get("total_expenses", 0)
        expense_map = stats.get("expense_by_category", {})
        count = stats.get("expense_count", 0)

        breakdown = "\n".join(
            f"  - **{c}**: ${a:,.2f} ({a/total*100:.0f}%)" for c, a in expense_map.items()
        ) if total > 0 else ""

        return {
            "type": "expense_breakdown",
            "title": "Expense Breakdown",
            "answer": f"Total expenses: **${total:,.2f}** across **{count}** transactions in **{len(expense_map)}** categories.",
            "detail": f"By category:\n{breakdown}" if breakdown else "",
            "chart_data": expense_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _handle_profit_loss(self, **ctx) -> Dict:
        stats = ctx["stats"]
        net = stats.get("net", 0)
        income = stats.get("total_income", 0)
        expenses = stats.get("total_expenses", 0)
        margin = (net / income * 100) if income > 0 else 0

        status = "in the green" if net > 0 else "in the red"
        emoji_word = "Profit" if net > 0 else "Loss"

        return {
            "type": "profit_loss",
            "title": f"Net {emoji_word}",
            "answer": (
                f"You're **{status}** with a net **{emoji_word.lower()}** of **${abs(net):,.2f}**.\n\n"
                f"Income: ${income:,.2f} | Expenses: ${expenses:,.2f} | Margin: {margin:.1f}%"
            ),
            "detail": "",
            "chart_data": {"Income": income, "Expenses": expenses},
            "chart_type": "comparison",
            "confidence": 1.0
        }

    def _handle_compare(self, **ctx) -> Dict:
        expense_map = ctx["stats"].get("expense_by_category", {})
        if len(expense_map) < 2:
            return self._simple("Not enough categories to compare.", "compare")

        items = list(expense_map.items())
        top, bottom = items[0], items[-1]

        return {
            "type": "compare_categories",
            "title": "Category Comparison",
            "answer": (
                f"**{top[0]}** is your highest expense at ${top[1]:,.2f}, "
                f"while **{bottom[0]}** is the lowest at ${bottom[1]:,.2f}. "
                f"That's a **{top[1]/max(bottom[1],0.01):.1f}x** difference."
            ),
            "detail": "\n".join(f"  - **{c}**: ${a:,.2f}" for c, a in items),
            "chart_data": expense_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _handle_anomaly(self, **ctx) -> Dict:
        txns = ctx["transactions"]
        expenses = [t for t in txns if t["amount"] < 0]

        if not expenses:
            return self._simple("No expenses to check for anomalies.", "anomaly")

        amounts = [abs(t["amount"]) for t in expenses]
        avg = sum(amounts) / len(amounts)

        outliers = [(t, abs(t["amount"]) / avg) for t in expenses if abs(t["amount"]) > avg * 2.5]
        outliers.sort(key=lambda x: x[1], reverse=True)

        if not outliers:
            return self._simple(
                f"No anomalies detected. All expenses are within normal range (avg: ${avg:,.2f}).",
                "anomaly"
            )

        lines = [f"  - **{t['description']}**: ${abs(t['amount']):,.2f} ({ratio:.1f}x avg)"
                 for t, ratio in outliers]

        return {
            "type": "anomaly",
            "title": "Anomaly Detection",
            "answer": f"Found **{len(outliers)}** unusual transaction(s) (>{2.5:.0f}x the average of ${avg:,.2f}):",
            "detail": "\n".join(lines),
            "chart_data": {},
            "chart_type": None,
            "confidence": 0.9
        }

    def _handle_count(self, **ctx) -> Dict:
        stats = ctx["stats"]
        return {
            "type": "count",
            "title": "Transaction Count",
            "answer": (
                f"**{stats.get('transaction_count', 0)}** total transactions: "
                f"**{stats.get('income_count', 0)}** income, "
                f"**{stats.get('expense_count', 0)}** expenses."
            ),
            "detail": "",
            "chart_data": {"Income": stats.get("income_count", 0), "Expenses": stats.get("expense_count", 0)},
            "chart_type": "comparison",
            "confidence": 1.0
        }

    def _handle_single_transaction(self, **ctx) -> Dict:
        stats = ctx["stats"]
        txns = ctx["transactions"]

        largest_exp = max((t for t in txns if t["amount"] < 0), key=lambda t: abs(t["amount"]), default=None)
        largest_inc = max((t for t in txns if t["amount"] > 0), key=lambda t: t["amount"], default=None)

        parts = []
        if largest_exp:
            parts.append(f"Largest single expense: **{largest_exp['description']}** — ${abs(largest_exp['amount']):,.2f} on {largest_exp['date']}")
        if largest_inc:
            parts.append(f"Largest single income: **{largest_inc['description']}** — ${largest_inc['amount']:,.2f} on {largest_inc['date']}")

        return {
            "type": "single_transaction",
            "title": "Largest Transactions",
            "answer": "\n\n".join(parts) if parts else "No transactions found.",
            "detail": "",
            "chart_data": {},
            "chart_type": None,
            "confidence": 1.0
        }

    def _handle_trend(self, **ctx) -> Dict:
        txns = sorted(ctx["transactions"], key=lambda t: t["date"])

        # Group by date
        daily = {}
        for t in txns:
            d = t["date"]
            if d not in daily:
                daily[d] = {"income": 0, "expenses": 0}
            if t["amount"] > 0:
                daily[d]["income"] += t["amount"]
            else:
                daily[d]["expenses"] += abs(t["amount"])

        dates = sorted(daily.keys())
        if len(dates) < 2:
            return self._simple("Not enough data points for trend analysis.", "trend")

        first_half = dates[:len(dates)//2]
        second_half = dates[len(dates)//2:]

        exp_first = sum(daily[d]["expenses"] for d in first_half)
        exp_second = sum(daily[d]["expenses"] for d in second_half)

        direction = "increasing" if exp_second > exp_first else "decreasing"
        change = abs(exp_second - exp_first)

        return {
            "type": "trend",
            "title": "Spending Trend",
            "answer": (
                f"Spending is **{direction}**. First half of period: ${exp_first:,.2f}, "
                f"second half: ${exp_second:,.2f} (change: ${change:,.2f})."
            ),
            "detail": f"Analyzed {len(dates)} days from {dates[0]} to {dates[-1]}.",
            "chart_data": {d: daily[d]["expenses"] for d in dates},
            "chart_type": "line",
            "confidence": 0.85
        }

    def _handle_overview(self, **ctx) -> Dict:
        stats = ctx["stats"]
        net = stats.get("net", 0)
        income = stats.get("total_income", 0)
        expenses = stats.get("total_expenses", 0)
        expense_map = stats.get("expense_by_category", {})
        top_cat = list(expense_map.items())[0] if expense_map else ("N/A", 0)

        return {
            "type": "overview",
            "title": "Financial Overview",
            "answer": (
                f"**Income**: ${income:,.2f} | **Expenses**: ${expenses:,.2f} | "
                f"**Net {'Profit' if net > 0 else 'Loss'}**: ${abs(net):,.2f}\n\n"
                f"Top expense: **{top_cat[0]}** (${top_cat[1]:,.2f}). "
                f"Analyzed **{stats.get('transaction_count', 0)}** transactions."
            ),
            "detail": "",
            "chart_data": expense_map,
            "chart_type": "bar",
            "confidence": 1.0
        }

    def _simple(self, text: str, intent: str) -> Dict:
        return {"type": intent, "title": intent.replace("_", " ").title(),
                "answer": text, "detail": "", "chart_data": {}, "chart_type": None, "confidence": 1.0}
