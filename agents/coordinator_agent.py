# Coordinator Agent 

import json
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from agents.search_agent import SearchAgent
from agents.summarizer_agent import SummarizerAgent
from agents.verifier_agent import VerifierAgent
from utils.memory import SimpleMemory
from config import PRODUCT_CATEGORIES

class CoordinatorAgent(BaseAgent):
    
    def __init__(self, memory=None):
        super().__init__("CoordinatorAgent", memory)
        
        shared_memory = memory or SimpleMemory()
        
        self.search_agent = SearchAgent(shared_memory)
        self.summarizer_agent = SummarizerAgent(shared_memory)
        self.verifier_agent = VerifierAgent(shared_memory)
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query = task.get("query", "")
        product_category = task.get("product_category", "")
        
        if not query:
            return {
                "success": False,
                "error": "No query provided",
                "report": None
            }
        
        if product_category not in PRODUCT_CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid product category. Must be one of: {list(PRODUCT_CATEGORIES.keys())}",
                "report": None
            }
        
        self.log_interaction("coordination_start", {
            "query": query,
            "product_category": product_category,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            self.logger.info("Step 1: Searching for relevant sources...")
            search_task = {
                "query": query,
                "product_category": product_category
            }
            
            search_result = self.search_agent.execute(search_task)
            
            if not search_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Search failed: {search_result.get('error', 'Unknown error')}",
                    "report": None
                }
            
            search_results = search_result.get("results", [])
            
            if not search_results:
                return {
                    "success": False,
                    "error": "No relevant sources found",
                    "report": None
                }
            
            self.logger.info("Step 2: Summarizing content...")
            summarization_task = {
                "search_results": search_results,
                "product_category": product_category
            }
            
            summarization_result = self.summarizer_agent.execute(summarization_task)
            
            if not summarization_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Summarization failed: {summarization_result.get('error', 'Unknown error')}",
                    "report": None
                }
            
            summaries = summarization_result.get("summaries", [])
            
            if not summaries:
                return {
                    "success": False,
                    "error": "No summaries generated",
                    "report": None
                }
            
            self.logger.info("Step 3: Verifying information...")
            verification_task = {
                "summaries": summaries,
                "product_category": product_category
            }
            
            verification_result = self.verifier_agent.execute(verification_task)
            
            if not verification_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Verification failed: {verification_result.get('error', 'Unknown error')}",
                    "report": None
                }
            
            verified_summaries = verification_result.get("verified_summaries", [])
            
            self.logger.info("Step 4: Generating final report...")
            report = self._generate_report(
                query=query,
                product_category=product_category,
                search_stats=search_result,
                summaries=verified_summaries,
                verification_stats=verification_result
            )
            
            result = {
                "success": True,
                "report": report,
                "stats": {
                    "sources_found": len(search_results),
                    "summaries_generated": len(summaries),
                    "summaries_verified": len(verified_summaries),
                    "summaries_filtered": len(summaries) - len(verified_summaries)
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
            error_result = {
                "success": False,
                "error": str(e),
                "report": None
            }
            
            self.log_interaction("coordination_error", {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return error_result
    
    def _generate_report(self, query: str, product_category: str, search_stats: Dict[str, Any], 
                        summaries: List[Dict[str, Any]], verification_stats: Dict[str, Any]) -> Dict[str, Any]:
        
        summaries.sort(key=lambda x: x.get("verification", {}).get("confidence_score", 0), reverse=True)
        
        report = {
            "metadata": {
                "query": query,
                "product_category": product_category,
                "category_name": PRODUCT_CATEGORIES.get(product_category, "Unknown"),
                "generated_at": datetime.now().isoformat(),
                "total_sources": search_stats.get("total_found", 0),
                "verified_updates": len(summaries)
            },
            "updates": []
        }
        
        for summary in summaries:
            update_entry = {
                "product": summary.get("product", "Unknown"),
                "summary": summary.get("summary", summary.get("update", "")),  
                "source": summary.get("source", ""),
                "date": summary.get("date", "unknown")
            }
            
            report["updates"].append(update_entry)
        
        report["summary"] = {
            "total_updates_found": len(summaries),
            "products_mentioned": len(set(s.get("product", "Unknown") for s in summaries if s.get("product") != "Unknown")),
            "recent_updates": len([s for s in summaries if s.get("date", "").startswith("2024") or s.get("date", "").startswith("2025")])
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], format: str = "json", filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_safe = report["metadata"]["query"].replace(" ", "_").replace("/", "_")[:20]
            filename = f"competitive_intelligence_{query_safe}_{timestamp}"
        
        if format.lower() == "json":
            filepath = f"reports/{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == "markdown":
            filepath = f"reports/{filename}.md"
            markdown_content = self._generate_markdown_report(report)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Report saved to: {filepath}")
        return filepath
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        metadata = report["metadata"]
        updates = report["updates"]
        summary = report["summary"]
        
        markdown = f"""# Competitive Intelligence Report
        
## Query Information
- **Query**: {metadata["query"]}
- **Product Category**: {metadata["category_name"]}
- **Generated**: {metadata["generated_at"]}
- **Total Sources Analyzed**: {metadata["total_sources"]}
- **Verified Updates**: {metadata["verified_updates"]}

## Summary Statistics
- **Total Updates Found**: {summary["total_updates_found"]}
- **Products Mentioned**: {summary["products_mentioned"]}
- **Recent Updates (2024-2025)**: {summary["recent_updates"]}

## Product Updates

"""
        
        for i, update in enumerate(updates, 1):
            markdown += f"""### {i}. {update["product"]}

**Summary**: {update["summary"]}

**Date**: {update["date"]}
**Source**: [{update["source"]}]({update["source"]})

---

"""
        
        return markdown

