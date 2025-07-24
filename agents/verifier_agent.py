# Verifier Agent

from typing import Dict, Any, List
from datetime import datetime
import re
from agents.base_agent import BaseAgent
from transformers import pipeline

class VerifierAgent(BaseAgent):    
    def __init__(self, memory=None):
        super().__init__("VerifierAgent", memory)
        self.llm = pipeline("text-generation", model="distilgpt2", device=-1) 
        
        self.trusted_domains = [
            "techcrunch.com", "theverge.com", "arstechnica.com", "wired.com",
            "engadget.com", "zdnet.com", "cnet.com", "reuters.com", "bloomberg.com",
            "github.com", "medium.com", "dev.to", "hackernews.com"
        ]
        
        self.suspicious_indicators = [
            "click here", "amazing deal", "limited time", "act now",
            "guaranteed", "miracle", "secret", "exclusive offer"
        ]
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        summaries = task.get("summaries", [])
        product_category = task.get("product_category", "")
        
        if not summaries:
            return {
                "success": False,
                "error": "No summaries provided for verification",
                "verified_summaries": []
            }
        
        self.log_interaction("verification_task", {
            "num_summaries": len(summaries),
            "product_category": product_category
        })
        
        try:
            verified_summaries = []
            
            for summary in summaries:
                if summary and summary.get("relevant", True):
                    verification_result = self._verify_summary(summary, product_category)
                    
                    if verification_result["is_reliable"]:
                        summary["verification"] = verification_result
                        verified_summaries.append(summary)
            
            result = {
                "success": True,
                "verified_summaries": verified_summaries,
                "total_verified": len(verified_summaries),
                "total_filtered": len(summaries) - len(verified_summaries)
            }
            
            self.log_interaction("verification_results", {
                "total_verified": len(verified_summaries),
                "total_filtered": len(summaries) - len(verified_summaries),
                "success": True
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "verified_summaries": []
            }
            
            self.log_interaction("verification_error", {
                "error": str(e)
            })
            
            return error_result
    
    def _verify_summary(self, summary: Dict[str, Any], product_category: str) -> Dict[str, Any]:
        source_url = summary.get("source", "")
        product = summary.get("product", "")
        summary_text = summary.get("summary", summary.get("update", "")) 
        
        memory_key = f"verification_{hash(str(summary))}"
        cached_verification = self.memory.retrieve(memory_key)
        
        if cached_verification:
            self.logger.info(f"Using cached verification for {source_url}")
            return cached_verification
        
        verification_result = {
            "is_reliable": True,
            "confidence_score": 0.5,
            "reliability_factors": [],
            "concerns": []
        }
        
        source_score = self._check_source_reliability(source_url)
        verification_result["confidence_score"] += source_score
        
        if source_score > 0:
            verification_result["reliability_factors"].append("Trusted domain")
        elif source_score < 0:
            verification_result["concerns"].append("Untrusted or suspicious domain")
        
        content_score = self._check_content_quality(summary_text)
        verification_result["confidence_score"] += content_score
        
        if content_score > 0:
            verification_result["reliability_factors"].append("High-quality content")
        elif content_score < 0:
            verification_result["concerns"].append("Low-quality or suspicious content")
        
        relevance_score = self._check_product_relevance(product, summary_text, product_category)
        verification_result["confidence_score"] += relevance_score
        
        if relevance_score > 0:
            verification_result["reliability_factors"].append("Highly relevant to category")
        elif relevance_score < 0:
            verification_result["concerns"].append("Low relevance to product category")
        
        date_score = self._check_date_validity(summary.get("date", ""))
        verification_result["confidence_score"] += date_score
        
        if date_score > 0:
            verification_result["reliability_factors"].append("Recent and valid date")
        elif date_score < 0:
            verification_result["concerns"].append("Invalid or very old date")
        
        # LLM verification
        if 0.3 <= verification_result["confidence_score"] <= 0.7:
            llm_verification = self._llm_verify_content(summary, product_category)
            verification_result["confidence_score"] += llm_verification["score"]
            verification_result["reliability_factors"].extend(llm_verification["factors"])
            verification_result["concerns"].extend(llm_verification["concerns"])
        
        verification_result["is_reliable"] = verification_result["confidence_score"] >= 0.4
        
        verification_result["confidence_score"] = max(0, min(1, verification_result["confidence_score"]))
        
        self.memory.store(memory_key, verification_result)
        
        return verification_result
    
    def _check_source_reliability(self, url: str) -> float:
        if not url:
            return -0.2
        
        url_lower = url.lower()
        
        # Check trusted domains
        for domain in self.trusted_domains:
            if domain in url_lower:
                return 0.3
        
        suspicious_patterns = [
            "bit.ly", "tinyurl", "clickbait", "ads", "affiliate",
            "promo", "deal", "discount"
        ]
        
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return -0.3
        
        if url.startswith("https://"):
            return 0.1
        
        return 0.0
    
    def _check_content_quality(self, content: str) -> float:
        """Check content quality indicators."""
        if not content:
            return -0.3
        
        content_lower = content.lower()
        score = 0.0
        
        for indicator in self.suspicious_indicators:
            if indicator in content_lower:
                score -= 0.1
        
        quality_indicators = [
            "announced", "released", "updated", "launched", "introduced",
            "features", "version", "improvement", "enhancement"
        ]
        
        for indicator in quality_indicators:
            if indicator in content_lower:
                score += 0.05
        
        if len(content) < 50:
            score -= 0.1
        elif len(content) > 100:
            score += 0.1
        
        return min(0.3, max(-0.3, score))
    
    def _check_product_relevance(self, product: str, update: str, category: str) -> float:
        if not product or product.lower() == "unknown":
            return -0.1
        
        combined_text = f"{product} {update}".lower()
        
        category_keywords = {
            "ai_productivity": [
                "ai", "artificial intelligence", "chatgpt", "notion", "grammarly",
                "productivity", "automation", "assistant", "writing", "analysis"
            ],
            "devops_platforms": [
                "devops", "github", "vercel", "netlify", "docker", "kubernetes",
                "deployment", "ci/cd", "pipeline", "infrastructure", "cloud"
            ],
            "consumer_electronics": [
                "phone", "laptop", "tablet", "smartphone", "computer", "device",
                "processor", "camera", "display", "battery", "specs"
            ]
        }
        
        keywords = category_keywords.get(category, [])
        
        matches = sum(1 for keyword in keywords if keyword in combined_text)
        
        if matches >= 3:
            return 0.2
        elif matches >= 1:
            return 0.1
        else:
            return -0.1
    
    def _check_date_validity(self, date_str: str) -> float:
        if not date_str or date_str == "unknown":
            return 0.0
        
        try:
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                date_parts = date_str.split('-')
                year = int(date_parts[0])
                current_year = datetime.now().year
                
                if year == current_year:
                    return 0.2
                elif year == current_year - 1:
                    return 0.1
                elif year < current_year - 2:
                    return -0.1
                elif year > current_year:
                    return -0.2
            
            return 0.0
            
        except:
            return -0.1
    
    def _llm_verify_content(self, summary: Dict[str, Any], product_category: str) -> Dict[str, Any]:
        try:
            user_prompt = f"""Evaluate this product update summary for {product_category}:
            
Product: {summary.get('product', 'Unknown')}
Company: {summary.get('company', 'Unknown')}
Update: {summary.get('update', '')}
Date: {summary.get('date', 'unknown')}
Source: {summary.get('source', '')}

IMPORTANT: Respond ONLY with valid JSON. No explanations or thoughts.

Required format:
{{"score": 0.1, "factors": ["factor1", "factor2"], "concerns": ["concern1"]}}

Score: float between -0.3 and 0.3
Factors: positive aspects (max 3)
Concerns: negative aspects (max 3)

JSON Response:"""

            response = self.llm(user_prompt, max_new_tokens=150, do_sample=False, pad_token_id=50256)
            generated_text = response[0]["generated_text"]
            
            assistant_response = generated_text[len(user_prompt):].strip()
            
            import json
            json_start = assistant_response.find('{')
            json_end = assistant_response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = assistant_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = {}
                
            return {
                "score": float(result.get("score", 0.0)),
                "factors": result.get("factors", []),
                "concerns": result.get("concerns", [])
            }
        except Exception as e:
            self.logger.warning(f"LLM verification failed: {str(e)}")
            return {
                "score": 0.0,
                "factors": [],
                "concerns": ["LLM verification failed"]
            }

