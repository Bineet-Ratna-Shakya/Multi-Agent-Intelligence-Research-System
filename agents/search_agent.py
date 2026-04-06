# Transaction Agent - Reads CSV and categorizes transactions using LLM

import pandas as pd
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from config import DEFAULT_CSV_PATH, EXPENSE_CATEGORIES, INCOME_CATEGORIES


class SearchAgent(BaseAgent):
    """Loads transactions from CSV and categorizes them using keyword matching + LLM."""

    def __init__(self, memory=None):
        super().__init__("TransactionAgent", memory)
        self.expense_categories = EXPENSE_CATEGORIES
        self.income_categories = INCOME_CATEGORIES

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        csv_path = task.get("csv_path", DEFAULT_CSV_PATH)
        query = task.get("query", "")

        self.log_interaction("transaction_task", {
            "csv_path": csv_path,
            "query": query
        })

        try:
            df = pd.read_csv(csv_path)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            categorized = self._categorize_transactions(df)

            result = {
                "success": True,
                "query": query,
                "transactions": categorized,
                "total_transactions": len(categorized),
                "summary_stats": self._compute_stats(categorized)
            }

            self.log_interaction("transaction_results", {
                "total": len(categorized),
                "success": True
            })

            return result

        except Exception as e:
            self.log_interaction("transaction_error", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "transactions": [],
                "summary_stats": {}
            }

    def _categorize_transactions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        categorized = []

        for _, row in df.iterrows():
            desc = str(row.get("description", "")).lower()
            amount = float(row.get("amount", 0))
            txn_type = str(row.get("type", "")).lower()

            if txn_type == "income" or amount > 0:
                category = self._match_category(desc, self.income_categories)
            else:
                category = self._match_category(desc, self.expense_categories)

            categorized.append({
                "date": str(row.get("date", ""))[:10],
                "description": row.get("description", ""),
                "amount": amount,
                "type": txn_type,
                "category": category
            })

        return categorized

    def _match_category(self, description: str, category_map: Dict[str, List[str]]) -> str:
        desc_lower = description.lower()
        for category, keywords in category_map.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
        return "Other"

    def _compute_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
        total_expenses = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)

        expense_by_cat = {}
        income_by_cat = {}

        for t in transactions:
            if t["amount"] < 0:
                cat = t["category"]
                expense_by_cat[cat] = expense_by_cat.get(cat, 0) + abs(t["amount"])
            else:
                cat = t["category"]
                income_by_cat[cat] = income_by_cat.get(cat, 0) + t["amount"]

        biggest_expense_cat = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else "N/A"

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net": round(total_income - total_expenses, 2),
            "expense_by_category": {k: round(v, 2) for k, v in sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)},
            "income_by_category": {k: round(v, 2) for k, v in sorted(income_by_cat.items(), key=lambda x: x[1], reverse=True)},
            "biggest_expense_category": biggest_expense_cat,
            "biggest_expense_amount": round(expense_by_cat.get(biggest_expense_cat, 0), 2),
            "transaction_count": len(transactions)
        }
