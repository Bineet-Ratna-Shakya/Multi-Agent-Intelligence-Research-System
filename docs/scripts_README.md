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


## 4. Search Tool (Folder: `tools/`)
### 4.1 `search_tool.py`
**Responsibilities:**
- Interfaces with DuckDuckGo (via `duckduckgo_search`) and HTTP/Playwright pipelines.
- three-tiered web search: general, news, and blogs.
- Ensures source diversity and filters duplicates.
- Extracts textual content via:
  - Direct HTTP requests + BeautifulSoup
  - Newspaper3k
  - PDF parsing (PyPDF2)
  - Headless browser scraping (Playwright)


**Dependencies:**

---

## 5. Additional Agents

### 5.1 `base_agent.py`
**Location:** `agents/base_agent.py`

**Purpose:**
- Defines `BaseAgent` abstract class with core functionality:
  - Initialization with name, logger, and memory.



### 5.2 `coordinator_agent.py`
**Location:** `agents/coordinator_agent.py`

**Purpose:**
- Orchestrates the workflow across agents.
- Loads configuration and initializes individual agents.
- Dispatches tasks to `SearchAgent`, `SummarizerAgent`, and `VerifierAgent`.


### 5.3 `summarizer_agent.py`
**Location:** `agents/summarizer_agent.py`

**Purpose:**
- Uses a transformer-based model (e.g., BART) to condense content.
- Caches summaries in memory to avoid reprocessing.
- Extracts dates and product names, cleans summary text.


### 5.4 `verifier_agent.py`
**Location:** `agents/verifier_agent.py`

**Purpose:**
- Validates the accuracy and consistency of summaries.
- Checks factual claims against source content or external APIs.
- Returns a verification report with success status and issues.



## 6. Logging & Memory (Folder: `utils/`)
- `utils/logger.py` – Logging setup (using `logging` module).
- `utils/memory.py` – Simple in-memory or persistent cache implementation.


**End of Script Reference**
