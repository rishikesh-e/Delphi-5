import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file. Please set it.")

MODEL_NAME = "llama-3.1-8b-instant"
TEMPERATURE = 0.5

MAX_WORD_LIMIT = 200

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = DATA_DIR / "debate_history.db"
CHROMA_PERSIST_DIRECTORY = DATA_DIR / "vector_store"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

class Colors:
    FINANCE = '\033[94m'
    RISK = '\033[91m'
    ETHICS = '\033[92m'
    DEVIL = '\033[93m'
    MODERATOR = '\033[95m'
    TOOL = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
