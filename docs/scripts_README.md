# Script Reference

This document provides an overview of key Python scripts in this repository, their responsibilities, configuration parameters, and sample usage.


## 1. main.py
**Location:** Root directory

**Purpose:**
- Entry point for running the full multi-agent pipeline.
- Parses command-line arguments (`query`, `product_category`, optionally `--output`).
- Initializes `CoordinatorAgent`, executes the task, and saves the report.

## 2. config.py
**Location:** Root directory

**Purpose:**
- Centralized configuration for API keys, timeouts, limits, product categories, and logging.

**Key Settings:**
- `MAX_SEARCH_RESULTS` (int): Default maximum number of search results per query.
- `MAX_RETRY_ATTEMPTS` (int): Number of retries for web/API calls.
- `SEARCH_TIMEOUT` (int): Timeout (seconds) for HTTP requests and extraction.
- `PRODUCT_CATEGORIES` (dict): Supported category codes and user-friendly labels.
- `LOG_LEVEL`, `LOG_FORMAT`: Controls verbosity and format of logs.

**Customization:**
2. Set environment variables or edit `config.py` directly.


## 3. Agents (Folder: agents/)
All agents extend `BaseAgent` and implement an `execute(task: Dict[str, Any]) -> Dict[str, Any]` method.

### 3.1 base_agent.py
**Location:** agents/base_agent.py
**Responsibilities:**
- Abstract base class for all agents.
- Sets up a named logger and shared `SimpleMemory` store.
- Provides `log_interaction(type, data)` and retrieval of past interactions.


### 3.2 search_agent.py
**Location:** agents/search_agent.py
**Responsibilities:**
- Enhances and caches search queries using `SimpleMemory`.
- Invokes `SearchTool.search_and_extract()` to perform multi-source web search.
- Filters, scores, and returns up to `MAX_SEARCH_RESULTS` items.

### 3.3 summarizer_agent.py
**Location:** agents/summarizer_agent.py
**Responsibilities:**
- Summarizes raw content using a transformer-based model (e.g., BART).
- Extracts product names and dates from text.
- Caches and returns a list of summaries with metadata.

### 3.4 verifier_agent.py
**Location:** agents/verifier_agent.py
**Responsibilities:**
- Verifies summary reliability via:
  - Trusted domain checks
  - Content quality analysis
  - Product relevance scoring
  - Date validity
  - Optional LLM-based cross-check
- Computes a normalized `confidence_score` and flags unreliable items.

### 3.5 coordinator_agent.py
**Location:** agents/coordinator_agent.py
**Responsibilities:**
- Orchestrates Search → Summarize → Verify workflow.
- Logs each step and aggregates results.
- Generates a final report (JSON or Markdown) sorted by confidence.

## 4. Search Tool (Folder: tools/)
### 4.1 search_tool.py
**Responsibilities:**
- Performs tiered searches (general, news, blogs) using:
  - DuckDuckGo API (`duckduckgo_search`)
  - HTTP requests + BeautifulSoup
  - Newspaper3k
  - PDF parsing (PyPDF2)
  - Optional Playwright headless scraping
- Ensures domain diversity, removes duplicates, and extracts page content.

**Dependencies:**


---

## 6. Logging & Memory (Folder: `utils/`)
- `utils/logger.py` – Logging setup (using `logging` module).
- `utils/memory.py` – Simple in-memory or persistent cache implementation.

**End of Script Reference**
