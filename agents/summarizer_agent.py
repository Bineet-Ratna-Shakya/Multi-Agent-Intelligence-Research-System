# Summarizer Agent

import json
from typing import Dict, Any, List
from datetime import datetime
import re
from agents.base_agent import BaseAgent
from transformers import pipeline

class SummarizerAgent(BaseAgent):
    
    def __init__(self, memory=None):
        super().__init__("SummarizerAgent", memory)
        self.logger.info("Initializing SummarizerAgent with BART for better summarization...")
        
        try:
            from transformers import pipeline
            self.summarizer = pipeline(
                "summarization", 
                model="facebook/bart-large-cnn",
                device=-1,  
                max_length=150,
                min_length=50,
                do_sample=False
            )
            self.logger.info("BART summarization model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load BART model: {e}")
            self.summarizer = None
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        search_results = task.get("search_results", [])
        product_category = task.get("product_category", "")
        
        if not search_results:
            return {
                "success": False,
                "error": "No search results provided for summarization",
                "summaries": []
            }
        
        self.log_interaction("summarization_task", {
            "num_results": len(search_results),
            "product_category": product_category
        })
        
        try:
            summaries = []
            
            for result in search_results:
                if not result.get("success", False):
                    continue
                
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                
                summary = self._summarize_content(title, content, url, product_category)
                if summary:
                    summaries.append(summary)
            
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
            error_result = {
                "success": False,
                "error": str(e),
                "summaries": []
            }
            
            self.log_interaction("summarization_error", {
                "error": str(e)
            })
            
            return error_result
    
    def _summarize_content(self, title: str, content: str, url: str, product_category: str) -> Dict[str, Any]:
        if not content or len(content.strip()) < 50:
            return None
            
        memory_key = f"summary_{hash(content[:500])}"
        cached_summary = self.memory.retrieve(memory_key)
        if cached_summary:
            return cached_summary
        
        try:
            product_name = self._extract_product_name(title, content, product_category)
            
            if self.summarizer:
                important_content = self._extract_important_content(title, content, product_name)
                
                summary_result = self.summarizer(important_content)
                summary_text = summary_result[0]['summary_text']
                
                summary_text = self._enhance_summary_with_key_points(summary_text, content, product_name)
                
                date = self._extract_date_from_content(f"{title} {content}")
                
                summary_data = {
                    "product": product_name,
                    "summary": summary_text,
                    "source": url,
                    "date": date,
                    "relevant": True
                }
            else:
                summary_data = self._simple_extraction_fallback(title, content, url, product_category)
            
            self.memory.store(memory_key, summary_data)
            return summary_data
            
        except Exception as e:
            self.logger.error(f"Failed to summarize content from {url}: {str(e)}")
            return self._simple_extraction_fallback(title, content, url, product_category)
    
    def _extract_product_name(self, title: str, content: str, product_category: str) -> str:
        text = f"{title} {content}".lower()
        
        product_patterns = {
            "consumer_electronics": [
                # iPhone patterns
                (r'iphone\s*(\d+(?:\s*pro)?(?:\s*max)?)', r'iPhone \1'),
                (r'ipad\s*(\w+)', r'iPad \1'),
                (r'macbook\s*(\w+)', r'MacBook \1'),
                (r'apple\s*watch\s*(\w+)', r'Apple Watch \1'),
                (r'airpods\s*(\w+)', r'AirPods \1'),
                # Samsung patterns
                (r'galaxy\s*s(\d+)', r'Galaxy S\1'),
                (r'galaxy\s*note\s*(\d+)', r'Galaxy Note \1'),
                # General patterns
                ("iphone", "iPhone"),
                ("ipad", "iPad"),
                ("macbook", "MacBook"),
                ("samsung galaxy", "Samsung Galaxy"),
                ("pixel", "Google Pixel"),
                ("surface", "Microsoft Surface")
            ],
            "ai_productivity": [
                # Notion patterns
                (r'notion\s*ai\s*(\d+\.?\d*)', r'Notion AI \1'),
                (r'notion\s*q&a', r'Notion Q&A'),
                (r'notion\s*calendar', r'Notion Calendar'),
                (r'notion\s*database', r'Notion Database'),
                (r'notion\s*templates', r'Notion Templates'),
                (r'notion\s*api', r'Notion API'),
                # ChatGPT patterns
                (r'gpt-?(\d+)', r'GPT-\1'),
                (r'chatgpt\s*(\d+\.?\d*)', r'ChatGPT \1'),
                (r'chatgpt\s*plus', r'ChatGPT Plus'),
                (r'chatgpt\s*enterprise', r'ChatGPT Enterprise'),
                # Other AI tools
                (r'github\s*copilot\s*(\w+)', r'GitHub Copilot \1'),
                (r'claude\s*(\d+)', r'Claude \1'),
                (r'microsoft\s*365\s*copilot', r'Microsoft 365 Copilot'),
                # Fallback patterns
                ("notion ai", "Notion AI"),
                ("chatgpt", "ChatGPT"),
                ("github copilot", "GitHub Copilot"),
                ("claude", "Claude"),
                ("microsoft 365", "Microsoft 365")
            ],
            "devops_platforms": [
                # GitHub patterns
                (r'github\s*actions\s*(\w+)', r'GitHub Actions \1'),
                (r'github\s*copilot\s*(\w+)', r'GitHub Copilot \1'),
                (r'github\s*enterprise', r'GitHub Enterprise'),
                # GitLab patterns
                (r'gitlab\s*(\d+\.?\d*)', r'GitLab \1'),
                (r'gitlab\s*ci/cd', r'GitLab CI/CD'),
                # Other platforms
                (r'jenkins\s*(\d+\.?\d*)', r'Jenkins \1'),
                (r'docker\s*(\w+)', r'Docker \1'),
                (r'kubernetes\s*(\d+\.?\d*)', r'Kubernetes \1'),
                # Fallback patterns
                ("github", "GitHub"),
                ("gitlab", "GitLab"),
                ("jenkins", "Jenkins"),
                ("docker", "Docker"),
                ("kubernetes", "Kubernetes")
            ]
        }
        
        patterns = product_patterns.get(product_category, [])
        
        import re
        for pattern_tuple in patterns:
            if isinstance(pattern_tuple, tuple) and len(pattern_tuple) == 2:
                regex_pattern, replacement = pattern_tuple
                match = re.search(regex_pattern, text, re.IGNORECASE)
                if match:
                    try:
                        return re.sub(regex_pattern, replacement, match.group(0), flags=re.IGNORECASE).title()
                    except:
                        continue
        
        for pattern in patterns:
            if isinstance(pattern, str) and pattern in text:
                return pattern.title()
        
        if title:
            version_match = re.search(r'(\w+(?:\s+\w+)*)\s+(\d+\.?\d*|\w+\s+\w+)', title, re.IGNORECASE)
            if version_match:
                return version_match.group(0).title()
            
            words = title.strip().split()[:3]
            meaningful_words = [w for w in words if len(w) > 2 and w.lower() not in ['the', 'and', 'for', 'with', 'new']]
            if meaningful_words:
                return " ".join(meaningful_words).title()
        
        return "Unknown Product"
    
    def _extract_date_from_content(self, content: str) -> str:
        import re
        from datetime import datetime, timedelta
        
        date_patterns = [
            (r'(\d{4}-\d{2}-\d{2})', 'iso'),  # YYYY-MM-DD
            (r'(\d{1,2}/\d{1,2}/\d{4})', 'us'),  # MM/DD/YYYY
            (r'(\d{1,2}-\d{1,2}-\d{4})', 'dash'),  # MM-DD-YYYY
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', 'month_name'),
            (r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', 'day_month'),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})', 'month_abbr')
        ]
        
        for pattern, format_type in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if format_type == 'iso':
                    return match.group(1)
                elif format_type == 'month_name' or format_type == 'month_abbr':
                    month_str = match.group(1)
                    day = match.group(2)
                    year = match.group(3)
                    
                    # Convert month name to number
                    month_map = {
                        'january': '01', 'jan': '01', 'february': '02', 'feb': '02',
                        'march': '03', 'mar': '03', 'april': '04', 'apr': '04',
                        'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
                        'august': '08', 'aug': '08', 'september': '09', 'sep': '09',
                        'october': '10', 'oct': '10', 'november': '11', 'nov': '11',
                        'december': '12', 'dec': '12'
                    }
                    
                    month_num = month_map.get(month_str.lower(), '01')
                    return f"{year}-{month_num}-{day.zfill(2)}"
                else:
                    try:
                        if format_type == 'us':
                            parts = match.group(1).split('/')
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        elif format_type == 'dash':
                            parts = match.group(1).split('-')
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    except:
                        continue
        
        content_lower = content.lower()
        today = datetime.now()
        
        if 'today' in content_lower:
            return today.strftime('%Y-%m-%d')
        elif 'yesterday' in content_lower:
            yesterday = today - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
        elif 'this week' in content_lower:
            return today.strftime('%Y-%m-%d')
        elif 'last week' in content_lower:
            week_ago = today - timedelta(days=7)
            return week_ago.strftime('%Y-%m-%d')
        
        current_year = today.year
        if str(current_year) in content or str(current_year-1) in content:
            return f"{current_year}-01-01" 
        
        return "unknown"
    
    def _simple_extraction_fallback(self, title: str, content: str, url: str, product_category: str) -> Dict[str, Any]:
        product_name = self._extract_product_name(title, content, product_category)
        
        # Create a simple summary from the first few sentences
        sentences = content.split('.')[:3]  # Take first 3 sentences
        simple_summary = '. '.join(sentences).strip()
        if len(simple_summary) > 200:
            simple_summary = simple_summary[:200] + "..."
        
        return {
            "product": product_name,
            "summary": simple_summary or "Content available but could not be summarized",
            "source": url,
            "date": self._extract_date_from_content(content),
            "relevant": True
        }
    
    def _extract_important_content(self, title: str, content: str, product_name: str) -> str:
        
        importance_categories = {
            'announcements': ['announce', 'launch', 'release', 'introduce', 'unveil', 'debut'],
            'features': ['feature', 'capability', 'function', 'technology', 'innovation', 'improvement'],
            'specifications': ['spec', 'specification', 'performance', 'speed', 'capacity', 'size', 'weight'],
            'pricing': ['price', 'cost', 'dollar', '$', 'pricing', 'expensive', 'cheap', 'affordable'],
            'availability': ['available', 'shipping', 'preorder', 'pre-order', 'order', 'buy', 'purchase'],
            'comparisons': ['versus', 'vs', 'compare', 'better', 'faster', 'slower', 'competitor'],
            'updates': ['update', 'upgrade', 'version', 'new', 'latest', 'recent', 'change'],
            'reviews': ['review', 'rating', 'score', 'opinion', 'verdict', 'recommendation']
        }
        
        sentences = content.replace('\n', '. ').split('.')
        important_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            importance_score = 0
            sentence_lower = sentence.lower()
            
            if product_name.lower() in sentence_lower:
                importance_score += 3
            
            for category, keywords in importance_categories.items():
                if any(keyword in sentence_lower for keyword in keywords):
                    importance_score += 2
                    break
            
            import re
            if re.search(r'\d+', sentence):
                importance_score += 1
            
            if importance_score >= 3:
                important_sentences.append((sentence, importance_score))
        
        important_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [sent[0] for sent in important_sentences[:8]]  # Take top 8 sentences
        
        if not top_sentences:
            top_sentences = [s.strip() for s in sentences[:6] if len(s.strip()) > 20]
        
        important_text = f"{title}. {'. '.join(top_sentences)}"
        
        if len(important_text) > 1000:
            important_text = important_text[:1000]
            last_period = important_text.rfind('.')
            if last_period > 500:  
                important_text = important_text[:last_period + 1]
        
        return important_text
    
    def _enhance_summary_with_key_points(self, summary: str, full_content: str, product_name: str) -> str:        
        key_info = {}
        content_lower = full_content.lower()
        
        import re
        price_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'[\d,]+\s*dollars?',
            r'price.*?\$[\d,]+',
            r'costs?.*?\$[\d,]+'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            if matches:
                key_info['pricing'] = matches[0]
                break
        
        date_patterns = [
            r'(?:available|release[ds]?|launch(?:es|ed)?|shipping)\s+(?:on\s+)?([A-Za-z]+ \d{1,2},? \d{4})',
            r'([A-Za-z]+ \d{4})',
            r'(\d{4})',
            r'(Q[1-4] \d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            if matches:
                key_info['release_date'] = matches[0]
                break
        
        spec_patterns = [
            r'(\d+(?:\.\d+)?\s*(?:GB|TB|MB|GHz|MHz|inch|inches|core|cores|MP|megapixel))',
            r'(\d+(?:\.\d+)?\s*hour[s]?\s*battery)',
            r'(A\d+\s*(?:Bionic|chip|processor))',
            r'(\d+nm\s*process)'
        ]
        
        specs = []
        for pattern in spec_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            specs.extend(matches[:2]) 
        
        if specs:
            key_info['specifications'] = ', '.join(specs[:3])
        
        enhanced_summary = summary
        
        if key_info.get('pricing') and 'price' not in summary.lower() and '$' not in summary:
            enhanced_summary += f" Pricing: {key_info['pricing']}."
        
        if key_info.get('release_date') and not any(word in summary.lower() for word in ['available', 'release', 'launch']):
            enhanced_summary += f" Release: {key_info['release_date']}."
        
        if key_info.get('specifications') and not any(word in summary.lower() for word in ['gb', 'ghz', 'inch', 'core']):
            enhanced_summary += f" Key specs: {key_info['specifications']}."
        
        return enhanced_summary

    def _clean_summary_text(self, summary_text: str, product_name: str) -> str:
        summary_text = summary_text.replace("This article discusses", "")
        summary_text = summary_text.replace("The article explains", "")
        summary_text = summary_text.replace("According to the article", "")
        
        if product_name.lower() not in summary_text.lower() and product_name != "Unknown Product":
            summary_text = f"{product_name}: {summary_text}"
        
        summary_text = ' '.join(summary_text.split())
        if summary_text:
            summary_text = summary_text[0].upper() + summary_text[1:]
        
        return summary_text