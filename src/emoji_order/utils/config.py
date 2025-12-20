import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Coinbase
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")

    # Home Assistant
    HA_URL = os.getenv("HA_URL", "http://localhost:8123")
    HA_TOKEN = os.getenv("HA_TOKEN")

    # Messaging
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # App
    APP_HOST = os.getenv("APP_HOST", "localhost")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
