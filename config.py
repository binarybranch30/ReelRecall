from dotenv import load_dotenv 
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SESSION_PATH = os.path.join(DATA_DIR, "session.json")
DB_PATH = os.path.join(DATA_DIR, "reels.db")

load_dotenv()

username = os.getenv("IG_USERNAME")
password = os.getenv("IG_PASSWORD")
if username is None or password is None:
    raise ValueError("IG_USERNAME and IG_PASSWORD must be set in the .env file")
    print("error")
