import os
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Gemini Config
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")

# Vector Database Config
CHROMA_DB_DIR = os.environ.get("CHROMA_DB_DIR", "./chroma_db")

# RAG Splitting Parameters
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 400))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 40))

# Retrieval and Escalation Thresholds
RETRIEVAL_CONFIDENCE_THRESHOLD = float(os.environ.get("RETRIEVAL_CONFIDENCE_THRESHOLD", 0.45))
MAX_CONSECUTIVE_FRUSTRATION = int(os.environ.get("MAX_CONSECUTIVE_FRUSTRATION", 2))

# Sensitive Keywords that trigger automatic escalation
SENSITIVE_KEYWORDS = [
    "refund", 
    "billing credit", 
    "sue", 
    "legal", 
    "lawyer",
    "duplicate charge", 
    "double charge",
    "overcharged", 
    "compromised", 
    "hacked", 
    "stolen credential",
    "unauthorized access",
    "fraud", 
    "delete account",
    "cancel account",
    "close account"
]

def call_gemini_with_backoff(func, *args, max_retries=5, **kwargs):
    import time
    import random
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "503" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "UNAVAILABLE" in err_msg:
                if attempt == max_retries - 1:
                    raise e
                sleep_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                time.sleep(sleep_time)
            else:
                raise e
