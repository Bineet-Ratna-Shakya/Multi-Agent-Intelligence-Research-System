# Financial Coordinator Agent - Orchestrates the real LLM pipeline

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

        self.log_interaction("start", {"query": query, "timestamp": datetime.now().isoformat()})

        try:
            # Step 1: Load + categorize transactions (LLM-powered)
            self.logger.info("Step 1: Loading and categorizing transactions with Gemini...")
            txn_task = {"query": query}
            if csv_path:
                txn_task["csv_path"] = csv_path

            txn_result = self.transaction_agent.execute(txn_task)
            if not txn_result.get("success"):
                return {"success": False, "error": f"Load failed: {txn_result.get('error')}", "report": None}

            transactions = txn_result.get("transactions", [])
            stats = txn_result.get("summary_stats", {})

            if not transactions:
                return {"success": False, "error": "No transactions found", "report": None}

            # Step 2: LLM-powered analysis of the user's question
            self.logger.info("Step 2: Gemini analyzing your question...")
            summary_result = self.summarizer_agent.execute({
                "transactions": transactions,
                "summary_stats": stats,
                "query": query,
                "available_categories": txn_result.get("available_categories", {})
            })

            if not summary_result.get("success"):
                return {"success": False, "error": f"Analysis failed: {summary_result.get('error')}", "report": None}

            # Step 3: LLM-powered verification + red flag detection
            self.logger.info("Step 3: Gemini verifying and checking for red flags...")
            verify_result = self.verifier_agent.execute({
                "summaries": summary_result.get("summaries", []),
                "transactions": transactions,
                "summary_stats": stats
            })

            verified = verify_result.get("verified_summaries", summary_result.get("summaries", []))

            # Build report
            report = {
                "metadata": {
                    "query": query,
                    "generated_at": datetime.now().isoformat(),
                    "total_transactions": len(transactions),
                    "period": f"{transactions[0]['date']} to {transactions[-1]['date']}" if transactions else "N/A",
                    "model": "gemini-2.0-flash"
                },
                "financial_stats": stats,
                "intent": summary_result.get("intent", "llm_analysis"),
                "insights": verified,
                "transactions": transactions
            }

            result = {
                "success": True,
                "report": report,
                "stats": {
                    "transactions_loaded": len(transactions),
                    "categories_found": len(stats.get("expense_by_category", {})) + len(stats.get("income_by_category", {})),
                    "intent": summary_result.get("intent", "llm_analysis"),
                    "model": "gemini-2.0-flash"
                }
            }

            self.log_interaction("complete", {"query": query, "success": True})
            return result

        except Exception as e:
            self.log_interaction("error", {"query": query, "error": str(e)})
            return {"success": False, "error": str(e), "report": None}

    def save_report(self, report: Dict[str, Any], format: str = "json", filename: str = None) -> str:
        import os
        os.makedirs("reports", exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"financial_report_{timestamp}"

        if format == "json":
            filepath = f"reports/{filename}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        elif format == "markdown":
            filepath = f"reports/{filename}.md"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self._to_markdown(report))
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Report saved: {filepath}")
        return filepath

    def _to_markdown(self, report: Dict) -> str:
        meta = report["metadata"]
        md = f"# Financial Report\n\n**Query**: {meta['query']}\n**Period**: {meta.get('period')}\n**Model**: {meta.get('model')}\n\n"
        for ins in report.get("insights", []):
            md += f"## {ins.get('title', '')}\n{ins.get('answer', '')}\n\n"
        return md
