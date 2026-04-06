# Gemini LLM wrapper (using google-genai SDK)

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL
from utils.logger import setup_logger

logger = setup_logger("LLM")

_client = None


def get_client():
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY not set. Add it to your .env file:\n"
                "GEMINI_API_KEY=your-actual-key\n\n"
                "Get one free at: https://aistudio.google.com/app/apikey"
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(f"Gemini client initialized: {GEMINI_MODEL}")
    return _client


def ask(prompt: str, system_instruction: str = None) -> str:
    """Send a prompt to Gemini and return the text response."""
    client = get_client()

    config = None
    if system_instruction:
        config = types.GenerateContentConfig(system_instruction=system_instruction)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config
    )
    return response.text
