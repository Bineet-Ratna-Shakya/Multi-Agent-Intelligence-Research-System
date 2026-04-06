# Configuration for AI Bookkeeping Agent

import os
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# Data
DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "transactions.csv")

# Agent settings
MAX_RETRY_ATTEMPTS = 3

EXPENSE_CATEGORIES = {
    "Marketing": ["ads", "campaign", "seo", "brochure", "linkedin", "facebook", "google ads", "marketing"],
    "Operations": ["hosting", "aws", "cloud", "internet", "electricity", "office supplies", "postage", "courier", "shipping", "domain"],
    "Payroll": ["salary", "employee", "freelance", "developer payment"],
    "Software": ["subscription", "slack", "zoom", "github", "figma", "notion", "dropbox"],
    "Travel": ["travel", "flight", "hotel", "meals", "conference"],
    "Professional Services": ["consulting", "advisory", "tax", "insurance", "training", "course", "registration"],
    "Finance": ["bank", "interest", "charges", "service charge"],
    "Other": []
}

INCOME_CATEGORIES = {
    "Client Payments": ["client payment"],
    "Revenue": ["revenue", "sales", "product sales", "subscription revenue"],
    "Consulting": ["consulting"],
    "Other Income": ["refund", "interest income"]
}

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
