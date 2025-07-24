# Multi-Agent-Intelligence-Research-System
### A Python-based multi-agent framework for automated competitive intelligence and product update reporting. The system orchestrates agents to search, summarize and verify information on the latest product developments across categories.

## Project Workflow
The system follows these detailed steps and components:

1. **Initialization** (in `main.py` / `app.py`)
   - Load environment variables
   - Configure logging 
   - Instantiate `CoordinatorAgent`

2. **Query Coordination**
   - `CoordinatorAgent` parses CLI args or Streamlit inputs.
   - Defines `query` string and selects `product_category` from `config.PRODUCT_CATEGORIES`.

3. **Search Phase**
   - `SearchAgent.search(query)` is invoked by coordinator.
   - Internally uses `tools.search_tool.SearchTool` methods:
     - `_search_general()` via `duckduckgo_search.DDGS` for web results.
     - `_search_news()` filtering by domains and using `requests` + `BeautifulSoup`.
     - `_search_blogs()` crawling blog domains with `playwright.async_api` and `bs4`.
     - `_search_pdf()` extracting text from PDFs using `requests` + `PyPDF2`.
   - Results are normalized into a list of dicts (`title`, `url`, `snippet`).

4. **Summarization Phase**
   - `SummarizerAgent.execute()` receives raw results.
   - Uses `transformers.pipeline('summarization', model='facebook/bart-large-cnn')` for text condensing.

5. **Verification Phase**
   - Initializes a Hugging Face text-generation pipeline and uses LangChain’s zero-shot classifier under the hood.
    - Instantiates a distilgpt2 text-generation pipeline on the CPU
    - Creates a ZeroShotClassificationChain, passing in the DistilGPT-2 pipeline as its LLM
    - Runs the chain to assign the best matching label to a given piece of text

6. **Aggregation & Reporting**
   - Verified summaries returned to `CoordinatorAgent`.
   - Aggregated into final JSON report with timestamp (`datetime.now()`) and saved under `reports/`.
   - In Streamlit UI, results rendered via `streamlit` components.

## Features
- Modular agents for search, summarization, and verification
- Caching and memory support to optimize repeated queries
- Streamlit-based web UI for interactive use
- Configurable search sources and product categories

## Prerequisites
- Python 3.8 or higher
- Git
- (Optional) Virtual environment tool (venv, conda)

## Technical Tools Used
- Language: Python 3.8+
- Frameworks: Streamlit (UI), Playwright (browser automation)
- APIs/Tools: DuckDuckGo Search, Requests, BeautifulSoup, PyPDF2
- Embedding: N/A (no vector embedding component)
- LLMs: facebook/bart-large-cnn (summarization), distilgpt2 (verification text generation)

## Installation
1. Clone the repository:
   ```powershell
   git clone https://github.com/Bineet-Ratna-Shakya/Multi-Agent-Intelligence-Research-System.git
   cd Multi-Agent-Intelligence-Research-System
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv; .\\venv\\Scripts\\Activate.ps1
   ```
3. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Install and initialize Playwright browsers:
   ```powershell
   playwright install
   ```

## Configuration
All settings can be overridden by creating a `.env` file in the project root. Define any parameters you wish to customize, or change the hardcoded config file.

## Usage

### Command-line Interface
Run the main application:
```powershell
python main.py --query "<SEARCH_QUERY>" --category "<CATEGORY_KEY>"
```
Replace `<SEARCH_QUERY>` and `<CATEGORY_KEY>` with your  search term and category identifier. The processed results will be saved to the `reports/` directory.

### Web Interface (Streamlit)
Start the interactive UI:
```powershell
streamlit run app.py
```

## Reports
Generated reports are stored under `reports/` and named like:
```
competitive_intelligence_{CATEGORY}_{YYYYMMDD_HHMMSS}.json
```
You can customize output paths and formats via `main.py` arguments.

## Project Structure
```
.
agents/
base_agent.py
coordinator_agent.py
search_agent.py
summarizer_agent.py
verifier_agent.py

tools/
search_tool.py

utils/
logger.py
memory.py

config.py
main.py
app.py
requirements.txt
README.md

docs/
scripts_README.md
```

## Agents
- **BaseAgent**: Abstract agent with logging and memory utilities.
- **CoordinatorAgent**: Orchestrates tasks across other agents.
- **SearchAgent**: Enhances and executes search queries via `SearchTool`.
- **SummarizerAgent**: Summarizes content using Hugging Face Transformers.
- **VerifierAgent**: Verifies summary reliability using trusted sources and LLM.

## Tools
- **SearchTool**: Interfaces with DuckDuckGo, Playwright, and PDF parsers to fetch diverse results.

## Utilities
- **Logger**: Configurable logging to console and file.
- **Memory**: In-memory caching of interactions and results.


## Architecture & Agent Design
The system is organized into the following components:

- **Entry Points**
  - `main.py`: Command-line interface for automated research tasks
  - `app.py`: Streamlit-based web application for interactive use

- **Configuration**
  - `config.py`: Loads environment variables and defines global settings

- **Utilities**
  - `utils.logger`: Sets up structured logging
  - `utils.memory`: Provides in-memory caching and session state

- **Tools**
  - `tools/search_tool.py`: Implements web, news, blog, and PDF search using external libraries
    - Uses `duckduckgo_search`, `requests`, `BeautifulSoup`, `playwright`, and `PyPDF2`

- **Agents**
  - `agents/base_agent.py`: Abstract base class with logging and memory support
  - `agents/coordinator_agent.py`: Orchestrates the pipeline and aggregates results
  - `agents/search_agent.py`: Enhances and delegates search queries to the SearchTool
  - `agents/summarizer_agent.py`: Summarizes text using a transformer model
  - `agents/verifier_agent.py`: Verifies content using a text-generation LLM and zero-shot classification

## Known Limitations & TODO
- Add unit and integration tests for each agent and tool module
- Improve error handling and retry strategies for network operations
- Support additional search sources (APIs, databases, etc.)
- Allow configurable output formats (CSV, HTML, etc.)
- Implement authentication for protected or rate-limited APIs
- Guardrails for Hallucinations