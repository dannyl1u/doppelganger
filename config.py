import os

from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
PRIVATE_KEY = open("rsa.pem", "r").read()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
SIMILARITY_THRESHOLD = os.getenv("SIMILARITY_THRESHOLD")
