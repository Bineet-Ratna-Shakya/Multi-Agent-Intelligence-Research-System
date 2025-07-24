# Multi-Agent-Intelligence-Research-System
# A Python-based multi-agent framework for automated competitive intelligence and product update reporting. The system orchestrates agents to search, summarize and verify information on the latest product developments across categories.

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

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Command-line Interface](#command-line-interface)
  - [Web Interface (Streamlit)](#web-interface-streamlit)
- [Project Structure](#project-structure)
- [Agents](#agents)
- [Tools](#tools)
- [Utilities](#utilities)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

## Features
- Modular agents for search, summarization, and verification
- Caching and memory support to optimize repeated queries
- Streamlit-based web UI for interactive use
- Configurable search sources and product categories

## Prerequisites
- Python 3.8 or higher
- Git
- (Optional) Virtual environment tool (venv, conda)

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

## Requirements

Install dependencies using:
```powershell
pip install -r requirements.txt
```

Core dependencies:
- requests
- PyPDF2
- duckduckgo_search
- playwright
- beautifulsoup4
- newspaper3k
- transformers
- torch
- streamlit
- python-dotenv





