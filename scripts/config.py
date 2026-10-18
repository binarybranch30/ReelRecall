from dotenv import load_dotenv 
import os

load_dotenv()

username = os.getenv("IG_USERNAME")
password = os.getenv("IG_PASSWORD")
if username is None or password is None:
    raise ValueError("IG_USERNAME and IG_PASSWORD must be set in the .env file")
    print("error")
