import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory or backend directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    PROJECT_NAME: str = "Smart Vendor–Shopkeeper Marketplace"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vendor_marketplace.db")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "gpt-4o-mini")
    
    # NMVE & Meta WhatsApp Cloud API Configuration
    WHATSAPP_API_KEY: str = os.getenv("WHATSAPP_API_KEY", "")
    WHATSAPP_BASE_URL: str = os.getenv("WHATSAPP_BASE_URL", "https://nmve.io/whatsapp/api/integrations/whatsapp/messages")
    WHATSAPP_CALLBACK_URL: str = os.getenv("WHATSAPP_CALLBACK_URL", "https://vendor-ntea.onrender.com/api/webhooks/whatsapp")
    WHATSAPP_TEST_MODE: bool = os.getenv("WHATSAPP_TEST_MODE", "false").lower() in ("true", "1", "yes")
    WHATSAPP_TEST_NUMBER: str = os.getenv("WHATSAPP_TEST_NUMBER", "9064148052")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "smart_vendor_marketplace_secure_token_2026")
    META_GRAPH_API_VERSION: str = "v19.0"
    
    # Port & Host
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = "0.0.0.0"
    
    # Demo Mode: Can simulate sending, delivery, read, and incoming replies
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

settings = Settings()
