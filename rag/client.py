import os
from dotenv import load_dotenv
from google import genai
import chromadb
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_PATH = PROJECT_ROOT / "chroma_data"

chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))