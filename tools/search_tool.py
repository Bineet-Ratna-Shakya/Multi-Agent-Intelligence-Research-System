# search tool with multiple sources and PDF support.

import time
import asyncio
import requests
import PyPDF2
import io
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from utils.logger import setup_logger
from config import MAX_SEARCH_RESULTS, MAX_RETRY_ATTEMPTS, SEARCH_TIMEOUT

logger = setup_logger(__name__)

class SearchTool:
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Preferred domains
        self.news_domains = ['reuters.com', 'bbc.com', 'cnn.com', 'bloomberg.com', 'techcrunch.com', 'theverge.com', 'engadget.com', 'arstechnica.com']
        self.blog_domains = ['medium.com', 'dev.to', 'hackernoon.com', 'towardsdatascience.com']
        self.official_domains = ['apple.com', 'microsoft.com', 'google.com', 'github.com', 'openai.com']
        
        self.avoid_domains = set()
    
    def search_web(self, query: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict[str, Any]]:
        logger.info(f"Searching for: {query}")
        
        all_results = []
        
        try:
            #1 General web search
            general_results = self._search_general(query, max_results // 3)
            all_results.extend(general_results)
            
            #2 News-specific search
            news_results = self._search_news(query, max_results // 3)
            all_results.extend(news_results)
            
            #3 Blog and technical content search
            blog_results = self._search_blogs(query, max_results // 3)
            all_results.extend(blog_results)
            
            # Remove duplicates and filter
            unique_results = self._ensure_source_diversity(all_results, max_results)
            
            logger.info(f"Found {len(unique_results)} diverse search results")
            return unique_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def _search_general(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        try:
            results = []
            
            search_queries = [
                f"{query} new features announcement 2024 2025",
                f"{query} product update release notes",
                f"{query} latest version changelog",
                f'"{query}" official announcement',
                f"{query} new capabilities features launched"
            ]
            
            for search_query in search_queries[:3]:  # Limit
                try:
                    search_results = self.ddgs.text(search_query, max_results=max_results//2)
                    
                    for result in search_results:
                       
                        url = result.get("href", "")
                        title = result.get("title", "")
                        snippet = result.get("body", "")
                        
                        # Skip dupli URL
                        if any(r.get("url") == url for r in results):
                            continue
                        
                        
                        domain = urlparse(url).netloc.lower()
                        is_official = any(official in domain for official in self.official_domains)
                        is_news = any(news in domain for news in self.news_domains)
                        
                        update_keywords = ['update', 'new', 'release', 'launch', 'announce', 'feature', 'version']
                        has_update_keywords = any(keyword in title.lower() or keyword in snippet.lower() 
                                                for keyword in update_keywords)
                        
                        if is_official or is_news or has_update_keywords:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "Official" if is_official else "News" if is_news else "General Web",
                                "search_type": "general",
                                "priority": 3 if is_official else 2 if is_news else 1
                            })
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"Search query failed: {search_query} - {e}")
                    continue
            
            results.sort(key=lambda x: x.get("priority", 0), reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"General search failed: {str(e)}")
            return []
    
    def _search_news(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        try:
            results = []
            
            news_queries = [
                f"{query} product announcement news",
                f"{query} new features release news",
                f"{query} update launched today",
                f'"{query}" official news announcement',
                f"{query} product news 2024 2025"
            ]
            
            for news_query in news_queries[:2]:  # Limit queries
                try:
                    search_results = self.ddgs.news(news_query, max_results=max_results)
                    
                    for result in search_results:
                        url = result.get("url", "")
                        title = result.get("title", "")
                        snippet = result.get("body", "")
                        date = result.get("date", "")
                        
                        # Skip duplicates
                        if any(r.get("url") == url for r in results):
                            continue
                        
                        # Filter for relevant news
                        content_text = f"{title} {snippet}".lower()
                        product_keywords = query.lower().split()
                        update_keywords = ['release', 'launch', 'announce', 'introduce', 'unveil', 'feature', 'update', 'new']
                        
                        # Check if this is actually about the product and updates
                        has_product = any(keyword in content_text for keyword in product_keywords)
                        has_update = any(keyword in content_text for keyword in update_keywords)
                        
                        if has_product and has_update:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "News",
                                "search_type": "news",
                                "date": date,
                                "priority": 2
                            })
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"News search failed: {news_query} - {e}")
                    continue
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return []
    
    def _search_blogs(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        try:
            results = []
            # Add blog-specific keywords and site restrictions
            blog_queries = [
                f"{query} blog post review analysis",
                f"site:medium.com {query}",
                f"site:dev.to {query}",
                f"site:techcrunch.com {query}"
            ]
            
            for blog_query in blog_queries[:2]:  # Limit queries
                search_results = self.ddgs.text(blog_query, max_results=max_results//2)
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "Blog/Technical",
                        "search_type": "blog"
                    })
                    
                if len(results) >= max_results:
                    break
                    
            return results[:max_results]
        except Exception as e:
            logger.error(f"Blog search failed: {str(e)}")
            return []
    
    def _ensure_source_diversity(self, results: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        domain_count = {}
        diverse_results = []
        
        for result in results:
            url = result.get("url", "")
            if not url:
                continue
                
            domain = urlparse(url).netloc.lower()
            
            if domain_count.get(domain, 0) >= 3: 
                continue
                
            if len(diverse_results) > 0 and domain in self.avoid_domains and len(diverse_results) < max_results // 2:
                continue
                
            domain_count[domain] = domain_count.get(domain, 0) + 1
            diverse_results.append(result)
            
            if len(diverse_results) >= max_results // 2:
                self.avoid_domains.add(domain)
                
            if len(diverse_results) >= max_results:
                break
                
        return diverse_results
    
    async def extract_content(self, url: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            browser = None
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()
                    
                    page.set_default_timeout(20000)
                    await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    
                    await page.wait_for_timeout(2000)
                    
                    content = await page.evaluate("""
                        () => {
                            // Remove script and style elements
                            const scripts = document.querySelectorAll('script, style, nav, footer, aside, .ad, .advertisement');
                            scripts.forEach(el => el.remove());
                            
                            // Get main content area or body text
                            const selectors = ['main', 'article', '.content', '.post', '.article', '.entry-content', '#content'];
                            for (const selector of selectors) {
                                const element = document.querySelector(selector);
                                if (element && element.innerText.length > 200) {
                                    return element.innerText;
                                }
                            }
                            return document.body.innerText;
                        }
                    """)
                    
                    await browser.close()
                    browser = None
                    
                    if content and len(content.strip()) > 100:
                        return content.strip()[:3000] 
                    else:
                        logger.warning(f"Extracted content too short from {url}: {len(content) if content else 0} chars")
                        
            except Exception as e:
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)  
                
        logger.error(f"Failed to extract content from {url} after {max_retries} attempts")
        return ""
    
    def extract_pdf_content(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # PyPDF2
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            
            max_pages = min(5, len(pdf_reader.pages))
            
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            text = text.strip()[:5000]  # Limit PDF content
            logger.info(f"Extracted {len(text)} characters from PDF: {url}")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract PDF content from {url}: {str(e)}")
            return ""
    
    def extract_with_newspaper(self, url: str) -> str:
        try:
            from newspaper import Article
            
            article = Article(url)
            article.download()
            article.parse()
            
            content = f"{article.title}\n\n{article.text}"
            return content.strip()[:3000]
            
        except Exception as e:
            logger.error(f"Newspaper extraction failed for {url}: {str(e)}")
            return ""
    
    def extract_simple_requests(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                element.decompose()
            
            content_selectors = ['main', 'article', '.content', '.post', '.entry-content', '#content', '.article-body']
            content = ""
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                content = soup.get_text(separator=' ', strip=True)
            
            content = ' '.join(content.split())  
            return content[:3000] if content else ""
            
        except Exception as e:
            logger.error(f"Simple extraction failed for {url}: {str(e)}")
            return ""
    
    def search_and_extract(self, query: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict[str, Any]]:
        search_results = self.search_web(query, max_results)
        
        extracted_results = []
        for result in search_results:
            url = result.get("url", "")
            if not url:
                continue
                
            content = ""
            extraction_method = "failed"
            
            try:
                if url.lower().endswith('.pdf'):
                    content = self.extract_pdf_content(url)
                    extraction_method = "pdf"
                elif any(domain in url.lower() for domain in self.news_domains):
                    content = self.extract_with_newspaper(url)
                    if not content: 
                        content = self.extract_simple_requests(url)
                    extraction_method = "newspaper"
                else:
                    content = self.extract_simple_requests(url)
                    extraction_method = "requests"
                
                extracted_result = {
                    "success": bool(content and len(content.strip()) > 50),
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "content": content,
                    "source": result.get("source", "web_search"),
                    "search_type": result.get("search_type", "general"),
                    "extraction_method": extraction_method,
                    "domain": urlparse(url).netloc
                }
                extracted_results.append(extracted_result)
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to extract content from {url}: {str(e)}")
                extracted_results.append({
                    "success": False,
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "content": "",
                    "source": result.get("source", "web_search"),
                    "search_type": result.get("search_type", "general"),
                    "extraction_method": "failed",
                    "domain": urlparse(url).netloc,
                    "error": str(e)[:100]
                })
        
        successful_results = [r for r in extracted_results if r["success"]]
        logger.info(f"Successfully extracted content from {len(successful_results)}/{len(extracted_results)} sources")
        
        domains = set(r["domain"] for r in successful_results)
        logger.info(f"Content extracted from {len(domains)} unique domains: {list(domains)[:5]}")
        
        return extracted_results

