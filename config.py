import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
DIRECTORY_DATA_FILE = DATA_DIR / "hospital_directory.json"

# Ensure essential directories exist
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

# Admin Security
ADMIN_PIN = os.getenv("ADMIN_PIN", "1234").strip()

# Chunking and Retrieval settings
CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 150  # characters
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_RETRIEVAL = 4
SIMILARITY_THRESHOLD = 0.35  # Cosine distance / relevance threshold

