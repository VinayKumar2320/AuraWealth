import os
from dotenv import load_dotenv

load_dotenv()

# App Config
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# OpenAI API config (optional, falls back to mock AI text if missing)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Alpaca API config (optional, falls back to mock pricing streams if missing)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Default Stock pool for the micro-investing system
STOCK_POOL = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", 
    "META", "GOOGL", "UNH", "JPM", "LLY"
]
