# Transaction Agent - Loads CSV, categorizes using Gemini LLM

import pandas as pd
import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.llm import ask
from config import DEFAULT_CSV_PATH, EXPENSE_CATEGORIES, INCOME_CATEGORIES


class SearchAgent(BaseAgent):
    """Loads transactions and uses Gemini to intelligently categorize them."""

    def __init__(self, memory=None):
        super().__init__("TransactionAgent", memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        csv_path = task.get("csv_path", DEFAULT_CSV_PATH)
        query = task.get("query", "")

        self.log_interaction("transaction_task", {"csv_path": csv_path, "query": query})

        try:
            df = pd.read_csv(csv_path)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            transactions = self._to_dicts(df)

            # Use LLM to categorize transactions
            categorized = self._categorize_with_llm(transactions)

            stats = self._compute_stats(categorized)

            result = {
                "success": True,
                "query": query,
                "transactions": categorized,
                "total_transactions": len(categorized),
                "summary_stats": stats,
                "available_categories": self._get_categories(categorized)
            }

            self.log_interaction("transaction_results", {"total": len(categorized), "success": True})
            return result

        except Exception as e:
            self.log_interaction("transaction_error", {"error": str(e)})
            return {"success": False, "error": str(e), "transactions": [], "summary_stats": {}}

    def _to_dicts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": str(row.get("date", ""))[:10],
                "description": str(row.get("description", "")),
                "amount": float(row.get("amount", 0)),
                "type": str(row.get("type", "")).lower()
            })
        return records

    def _categorize_with_llm(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use Gemini to categorize all transactions at once."""

        # Check cache first
        cache_key = f"categorized_{hash(str([(t['description'], t['amount']) for t in transactions]))}"
        cached = self.memory.retrieve(cache_key)
        if cached:
            self.logger.info("Using cached categorization")
            return cached

        expense_cats = list(EXPENSE_CATEGORIES.keys())
        income_cats = list(INCOME_CATEGORIES.keys())

        # Build the transaction list for the prompt
        txn_lines = []
        for i, t in enumerate(transactions):
            txn_lines.append(f'{i}|{t["description"]}|{t["amount"]}|{t["type"]}')

        prompt = f"""Categorize each transaction below.

For expenses, use one of: {', '.join(expense_cats)}
For income, use one of: {', '.join(income_cats)}

Transactions (index|description|amount|type):
{chr(10).join(txn_lines)}

Respond with ONLY a JSON array of category strings, one per transaction, in the same order.
Example: ["Marketing", "Client Payments", "Payroll", ...]

JSON array:"""

        try:
            response = ask(prompt, system_instruction="You are a financial categorization agent. Respond only with valid JSON.")

            # Parse the response - extract JSON array
            text = response.strip()
            # Find the JSON array in the response
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                categories = json.loads(text[start:end])
            else:
                raise ValueError("No JSON array found in response")

            if len(categories) != len(transactions):
                self.logger.warning(f"LLM returned {len(categories)} categories for {len(transactions)} transactions, falling back")
                raise ValueError("Category count mismatch")

            # Apply categories
            for i, t in enumerate(transactions):
                t["category"] = categories[i]

            self.logger.info(f"LLM categorized {len(transactions)} transactions")

        except Exception as e:
            self.logger.warning(f"LLM categorization failed: {e}, using keyword fallback")
            for t in transactions:
                desc = t["description"].lower()
                if t["type"] == "income" or t["amount"] > 0:
                    t["category"] = self._keyword_match(desc, INCOME_CATEGORIES)
                else:
                    t["category"] = self._keyword_match(desc, EXPENSE_CATEGORIES)

        self.memory.store(cache_key, transactions)
        return transactions

    def _keyword_match(self, description: str, category_map: Dict[str, List[str]]) -> str:
        for category, keywords in category_map.items():
            for keyword in keywords:
                if keyword in description:
                    return category
        return "Other"

    def _get_categories(self, transactions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        return {
            "expense": sorted(set(t["category"] for t in transactions if t["amount"] < 0)),
            "income": sorted(set(t["category"] for t in transactions if t["amount"] > 0))
        }

    def _compute_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not transactions:
            return {}

        total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
        total_expenses = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)

        expense_by_cat = {}
        income_by_cat = {}
        for t in transactions:
            if t["amount"] < 0:
                expense_by_cat[t["category"]] = expense_by_cat.get(t["category"], 0) + abs(t["amount"])
            else:
                income_by_cat[t["category"]] = income_by_cat.get(t["category"], 0) + t["amount"]

        biggest = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else "N/A"

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net": round(total_income - total_expenses, 2),
            "expense_by_category": {k: round(v, 2) for k, v in sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)},
            "income_by_category": {k: round(v, 2) for k, v in sorted(income_by_cat.items(), key=lambda x: x[1], reverse=True)},
            "biggest_expense_category": biggest,
            "biggest_expense_amount": round(expense_by_cat.get(biggest, 0), 2),
            "transaction_count": len(transactions),
            "expense_count": len([t for t in transactions if t["amount"] < 0]),
            "income_count": len([t for t in transactions if t["amount"] > 0])
        }
