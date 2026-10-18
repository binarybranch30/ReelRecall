from dotenv import load_dotenv 
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSION_PATH = DATA_DIR / "session.json"
DB_PATH = DATA_DIR / "reels.db"

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

for name, value in (("IG_USERNAME", IG_USERNAME), ("IG_PASSWORD", IG_PASSWORD)):
    if not value:
        raise ValueError(f"{name} is not set in .env")



