import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
PRIVATE_KEY = open('rsa.pem', 'r').read()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SIMILARITY_THRESHOLD = 0.5