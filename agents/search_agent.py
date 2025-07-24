# Search Agent
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from tools.search_tool import SearchTool
from config import MAX_SEARCH_RESULTS

class SearchAgent(BaseAgent):    
    def __init__(self, memory=None):
        super().__init__("SearchAgent", memory)
        self.search_tool = SearchTool()
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query = task.get("query", "")
        product_category = task.get("product_category", "")
        max_results = task.get("max_results", MAX_SEARCH_RESULTS)
        
        if not query:
            return {
                "success": False,
                "error": "No search query provided",
                "results": []
            }
        
        self.log_interaction("search_task", {
            "query": query,
            "product_category": product_category,
            "max_results": max_results
        })
        
        memory_key = f"search_results_{hash(query)}"
        cached_results = self.memory.retrieve(memory_key)
        
        if cached_results:
            self.logger.info(f"Using cached results for query: {query}")
            return cached_results
        
        enhanced_query = self._enhance_query(query, product_category)
        
        try:
            search_results = self.search_tool.search_and_extract(enhanced_query, max_results)
            
            filtered_results = self._filter_results(search_results, product_category)
            
            result = {
                "success": True,
                "query": query,
                "enhanced_query": enhanced_query,
                "results": filtered_results,
                "total_found": len(filtered_results)
            }
            
            self.memory.store(memory_key, result)
            
            self.log_interaction("search_results", {
                "query": query,
                "total_found": len(filtered_results),
                "success": True
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
            
            self.log_interaction("search_error", {
                "query": query,
                "error": str(e)
            })
            
            return error_result
    
    def _enhance_query(self, query: str, product_category: str) -> str:
        if not product_category:
            return query
        
        main_product = query.strip()
        
        enhanced_terms = [
            "new features",
            "product update", 
            "release announcement",
            "latest version",
            "new capabilities"
        ]
        
        category_enhancements = {
            "ai_productivity": [
                "AI features",
                "productivity updates", 
                "new tools",
                "integration announcement"
            ],
            "devops_platforms": [
                "platform update",
                "new deployment features",
                "CI/CD improvements",
                "developer tools"
            ],
            "consumer_electronics": [
                "device announcement",
                "specifications",
                "launch event",
                "product reveal"
            ]
        }
        
        category_terms = category_enhancements.get(product_category, [])
        
        enhanced_query = f'"{main_product}" {enhanced_terms[0]} {category_terms[0] if category_terms else ""}'
        
        self.logger.info(f"Enhanced query from '{query}' to '{enhanced_query}'")
        return enhanced_query
    
    def _filter_results(self, results: List[Dict[str, Any]], product_category: str) -> List[Dict[str, Any]]:
        filtered = []
        domains_seen = set()
        
        for result in results:
            if not result.get("success", False):
                result["relevance_score"] = 0
                filtered.append(result)
                continue
            
            content = result.get("content", "").lower()
            title = result.get("title", "").lower()
            domain = result.get("domain", "")
            
            domain_count = sum(1 for r in filtered if r.get("domain") == domain)
            if domain_count >= 3:
                continue
            
            relevance_score = 1  
            
            search_type = result.get("search_type", "general")
            if search_type == "news":
                relevance_score += 0.5
            elif search_type == "blog":
                relevance_score += 0.3
            
            extraction_method = result.get("extraction_method", "")
            if extraction_method == "newspaper":
                relevance_score += 0.3
            elif extraction_method == "pdf":
                relevance_score += 0.4
            
            content_length = len(content)
            if content_length > 1000:
                relevance_score += 0.5
            elif content_length > 500:
                relevance_score += 0.3
            
            if content_length < 100:
                relevance_score -= 0.2
            
            relevance_score = max(0.1, relevance_score)
            
            result["relevance_score"] = relevance_score
            filtered.append(result)
        
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered