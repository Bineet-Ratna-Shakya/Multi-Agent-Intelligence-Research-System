# Script Reference

This document provides an overview of key Python scripts in this repository, their responsibilities, configuration parameters, and sample usage.


## 1. `main.py`
**Location:** Root directory

**Purpose:**
- Entry point for running the full multi-agent pipeline.
- Initializes the coordinator agent and triggers execution.

> Note: Ensure `config.py` is set up before running.

## 2. `config.py`
**Location:** Root directory

**Purpose:**
- Centralized configuration for API keys, timeouts, limits, and logging.

**Key Settings:**
- `MAX_SEARCH_RESULTS` (int): Default maximum number of search results.
- `MAX_RETRY_ATTEMPTS` (int): Number of retries for external calls.
- `SEARCH_TIMEOUT` (int): Timeout (seconds) for search and extraction.
- `PRODUCT_CATEGORIES` (dict): Supported product category codes and labels.
- `LOG_LEVEL`, `LOG_FORMAT`: Logging configuration.

**Customization:**
2. Set environment variables or edit `config.py` directly.


## 3. Agents (Folder: `agents/`)
Each agent inherits from `BaseAgent` and implements `execute(task)`.

### 3.1 `search_agent.py`
**Responsibilities:**
- Receives a search query and optional `product_category`.
- Uses `SearchTool` to fetch and extract content from web sources.
- Applies relevance scoring and caching via memory.
- Returns a structured result dict.

**Key Methods:**
- `execute(task)` – Main entry; logs, checks cache, runs search, filters results.
- `_enhance_query(query, category)` – Augments query with category-specific terms.
- `_filter_results(results, category)` – Scores and ranks raw extractions.


---

## 4. Search Tool (Folder: `tools/`)
### 4.1 `search_tool.py`
**Responsibilities:**
- Interfaces with DuckDuckGo (via `duckduckgo_search`) and HTTP/Playwright pipelines.
- Performs three-tiered web search: general, news, and blogs.
- Ensures source diversity and filters duplicates.
- Extracts textual content via:
  - Direct HTTP requests + BeautifulSoup
  - Newspaper3k
  - PDF parsing (PyPDF2)
  - Headless browser scraping (Playwright)

**Key Functions:**
- `search_and_extract(query, max_results)` – Orchestrates search & content extraction.
- `search_web(query, max_results)` – Returns raw search hits.
- `extract_simple_requests(url)`, `extract_with_newspaper(url)`, `extract_pdf_content(url)`, `extract_content(url)` – Content extraction.

**Dependencies:**
- `duckduckgo_search`
- `playwright`
- `beautifulsoup4`
- `PyPDF2`
- `newspaper3k`

---

## 5. Additional Agents


## 6. Logging & Memory (Folder: `utils/`)
- `utils/logger.py` – Logging setup (using `logging` module).
- `utils/memory.py` – Simple in-memory or persistent cache implementation.


**End of Script Reference**
