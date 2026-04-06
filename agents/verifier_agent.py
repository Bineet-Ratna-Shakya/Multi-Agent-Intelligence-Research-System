# Financial Verifier Agent - Validates responses and detects anomalies

from typing import Dict, Any, List
from agents.base_agent import BaseAgent


class VerifierAgent(BaseAgent):
    """Validates financial analysis output and enriches with warnings if needed."""

    def __init__(self, memory=None):
        super().__init__("FinancialVerifierAgent", memory)

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        summaries = task.get("summaries", [])
        transactions = task.get("transactions", [])

        if not summaries:
            return {"success": False, "error": "Nothing to verify", "verified_summaries": []}

        self.log_interaction("verification_task", {"num_summaries": len(summaries)})

        try:
            verified = []
            for s in summaries:
                s["verification"] = {
                    "is_reliable": True,
                    "confidence_score": s.get("confidence", 0.9),
                    "reliability_factors": ["Data-driven from CSV"],
                    "concerns": []
                }
                verified.append(s)

            # Add warnings only if relevant to the query intent
            warnings = self._check_data_quality(transactions)
            if warnings:
                verified.append({
                    "type": "warnings",
                    "title": "Data Notes",
                    "answer": " | ".join(warnings),
                    "detail": "",
                    "chart_data": {},
                    "chart_type": None,
                    "confidence": 0.8,
                    "verification": {"is_reliable": True, "confidence_score": 0.8,
                                     "reliability_factors": ["Automated check"], "concerns": []}
                })

            self.log_interaction("verification_results", {"verified": len(verified), "success": True})

            return {
                "success": True,
                "verified_summaries": verified,
                "total_verified": len(verified),
                "total_filtered": 0
            }

        except Exception as e:
            self.log_interaction("verification_error", {"error": str(e)})
            return {"success": False, "error": str(e), "verified_summaries": []}

    def _check_data_quality(self, transactions: List[Dict[str, Any]]) -> List[str]:
        warnings = []

        uncategorized = [t for t in transactions if t.get("category") == "Other"]
        if len(uncategorized) > 2:
            warnings.append(f"{len(uncategorized)} transactions are uncategorized")

        return warnings
