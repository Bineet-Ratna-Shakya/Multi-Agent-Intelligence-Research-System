# Financial Coordinator Agent - Orchestrates the financial analysis pipeline

import json
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from agents.search_agent import SearchAgent
from agents.summarizer_agent import SummarizerAgent
from agents.verifier_agent import VerifierAgent
from utils.memory import SimpleMemory


class CoordinatorAgent(BaseAgent):

    def __init__(self, memory=None):
        super().__init__("CoordinatorAgent", memory)

        shared_memory = memory or SimpleMemory()

        self.transaction_agent = SearchAgent(shared_memory)
        self.summarizer_agent = SummarizerAgent(shared_memory)
        self.verifier_agent = VerifierAgent(shared_memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query = task.get("query", "")
        csv_path = task.get("csv_path", None)

        if not query:
            return {"success": False, "error": "No query provided", "report": None}

        self.log_interaction("coordination_start", {
            "query": query,
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Step 1: Load and categorize transactions
            self.logger.info("Step 1: Loading and categorizing transactions...")
            txn_task = {"query": query}
            if csv_path:
                txn_task["csv_path"] = csv_path

            txn_result = self.transaction_agent.execute(txn_task)

            if not txn_result.get("success"):
                return {"success": False, "error": f"Transaction loading failed: {txn_result.get('error')}", "report": None}

            transactions = txn_result.get("transactions", [])
            stats = txn_result.get("summary_stats", {})

            if not transactions:
                return {"success": False, "error": "No transactions found in CSV", "report": None}

            # Step 2: Generate financial summaries and insights
            self.logger.info("Step 2: Generating financial insights...")
            summary_task = {
                "transactions": transactions,
                "summary_stats": stats,
                "query": query
            }

            summary_result = self.summarizer_agent.execute(summary_task)

            if not summary_result.get("success"):
                return {"success": False, "error": f"Summarization failed: {summary_result.get('error')}", "report": None}

            summaries = summary_result.get("summaries", [])

            # Step 3: Verify and detect anomalies
            self.logger.info("Step 3: Verifying and detecting anomalies...")
            verify_task = {
                "summaries": summaries,
                "transactions": transactions
            }

            verify_result = self.verifier_agent.execute(verify_task)

            if not verify_result.get("success"):
                return {"success": False, "error": f"Verification failed: {verify_result.get('error')}", "report": None}

            verified_summaries = verify_result.get("verified_summaries", [])

            # Step 4: Generate report
            self.logger.info("Step 4: Generating report...")
            report = self._generate_report(query, transactions, stats, verified_summaries)

            result = {
                "success": True,
                "report": report,
                "stats": {
                    "transactions_loaded": len(transactions),
                    "summaries_generated": len(summaries),
                    "summaries_verified": len(verified_summaries),
                    "anomalies_found": verify_result.get("anomalies_found", 0)
                }
            }

            self.log_interaction("coordination_complete", {
                "query": query,
                "success": True,
                "stats": result["stats"],
                "timestamp": datetime.now().isoformat()
            })

            return result

        except Exception as e:
            self.log_interaction("coordination_error", {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return {"success": False, "error": str(e), "report": None}

    def _generate_report(self, query: str, transactions: List[Dict[str, Any]],
                          stats: Dict[str, Any],
                          summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "metadata": {
                "query": query,
                "generated_at": datetime.now().isoformat(),
                "total_transactions": len(transactions),
                "period": f"{transactions[0]['date']} to {transactions[-1]['date']}" if transactions else "N/A"
            },
            "financial_stats": stats,
            "insights": [
                {
                    "title": s.get("title", ""),
                    "type": s.get("type", ""),
                    "summary": s.get("summary", ""),
                    "confidence": s.get("verification", {}).get("confidence_score", 0.9)
                }
                for s in summaries
            ],
            "transactions": transactions
        }

    def save_report(self, report: Dict[str, Any], format: str = "json", filename: str = None) -> str:
        import os
        os.makedirs("reports", exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"financial_report_{timestamp}"

        if format.lower() == "json":
            filepath = f"reports/{filename}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        elif format.lower() == "markdown":
            filepath = f"reports/{filename}.md"
            md = self._generate_markdown_report(report)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Report saved to: {filepath}")
        return filepath

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        meta = report["metadata"]
        stats = report["financial_stats"]
        insights = report["insights"]

        md = f"""# Financial Analysis Report

## Overview
- **Query**: {meta["query"]}
- **Period**: {meta["period"]}
- **Generated**: {meta["generated_at"]}
- **Transactions Analyzed**: {meta["total_transactions"]}

## Financial Summary
| Metric | Amount |
|--------|--------|
| Total Income | ${stats.get('total_income', 0):,.2f} |
| Total Expenses | ${stats.get('total_expenses', 0):,.2f} |
| Net Profit/Loss | ${stats.get('net', 0):,.2f} |

## Expense Breakdown
| Category | Amount |
|----------|--------|
"""
        for cat, amt in stats.get("expense_by_category", {}).items():
            md += f"| {cat} | ${amt:,.2f} |\n"

        md += "\n## Income Breakdown\n| Source | Amount |\n|--------|--------|\n"
        for cat, amt in stats.get("income_by_category", {}).items():
            md += f"| {cat} | ${amt:,.2f} |\n"

        md += "\n## Insights\n\n"
        for insight in insights:
            md += f"### {insight['title']}\n{insight['summary']}\n\n"

        return md
