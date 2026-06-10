import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "")
ADMIN_ID            = int(os.getenv("ADMIN_ID", "0"))

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GEMINI_MODEL = "google/gemini-2.5-flash-lite"

MIN_ODDS       = 1.50
TOP_BETS_COUNT = 5
CACHE_HOURS    = 6
