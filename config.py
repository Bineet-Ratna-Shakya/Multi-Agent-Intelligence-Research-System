# Configuration settings for the agent

import os
from dotenv import load_dotenv

load_dotenv()

MAX_SEARCH_RESULTS = 8  
MAX_RETRY_ATTEMPTS = 3
SEARCH_TIMEOUT = 30

PRODUCT_CATEGORIES = {
    "ai_productivity": "AI Productivity Tools",
    "devops_platforms": "DevOps Platforms", 
    "consumer_electronics": "Consumer Electronics"
}

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

