# AI Bookkeeping Agent

A multi-agent financial intelligence system that analyzes your transactions using AI. Upload a CSV of income/expenses and ask natural-language questions like *"What's my biggest expense category this month?"*

Built by **Bineet Shakya** — originally a competitive intelligence system, now reimagined as an AI-powered bookkeeping assistant.

## How It Works

The system uses a 3-agent pipeline orchestrated by a coordinator:

| Agent | Role |
|-------|------|
| **TransactionAgent** | Loads CSV, categorizes each transaction (Marketing, Operations, Payroll, Software, Travel, etc.) |
| **SummarizerAgent** | Generates financial insights, answers natural-language queries, creates recommendations |
| **VerifierAgent** | Validates categorizations, detects anomalies, flags unusual spending patterns |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# Or use the CLI
python main.py -q "What's my biggest expense category this month?"
```

## Example Queries

- "What's my biggest expense category this month?"
- "Show me my income breakdown"
- "What's my net profit?"
- "How much am I spending on marketing?"
- "Give me a full financial overview"

## CSV Format

Your transactions CSV should have these columns:

```csv
date,description,amount,type
2026-04-01,Google Ads Campaign,-1200.00,expense
2026-04-01,Client Payment - Acme Corp,5000.00,income
```

- **date**: YYYY-MM-DD format
- **description**: Transaction description
- **amount**: Negative for expenses, positive for income
- **type**: `income` or `expense`

A demo dataset with 40 mock transactions is included in `data/transactions.csv`.

## Deployment on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the main file
4. Deploy!

## Project Structure

```
├── agents/
│   ├── base_agent.py           # Abstract base class
│   ├── search_agent.py         # TransactionAgent - CSV loading & categorization
│   ├── summarizer_agent.py     # Financial insights & query answering
│   ├── verifier_agent.py       # Anomaly detection & validation
│   └── coordinator_agent.py    # Pipeline orchestration
├── data/
│   └── transactions.csv        # Mock transaction data
├── utils/
│   ├── logger.py               # Logging
│   └── memory.py               # In-memory caching
├── app.py                      # Streamlit web UI
├── main.py                     # CLI entry point
├── config.py                   # Configuration
└── requirements.txt            # Dependencies
```

## License

MIT
