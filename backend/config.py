import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "vectordb"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Ensure directories exist
for d in [MODELS_DIR, DATA_DIR, UPLOADS_DIR, INDEX_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# App settings
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5-3b-instruct-q4_k_m.gguf")
API_HOST = os.getenv("HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
