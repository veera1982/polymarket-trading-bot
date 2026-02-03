import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    POLYMARKET_API_URL = os.getenv('POLYMARKET_API_URL', 'https://gamma-api.polymarket.com')
    POLYMARKET_GRAPHQL_URL = os.getenv('POLYMARKET_GRAPHQL_URL', 'https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic')
    
    # Wallet Configuration
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
    
    # Trading Configuration
    MAX_TRADE_AMOUNT = float(os.getenv('MAX_TRADE_AMOUNT', 5.0))
    DEFAULT_TRADE_AMOUNT = float(os.getenv('DEFAULT_TRADE_AMOUNT', 0.8))
    PROBABILITY_THRESHOLD = float(os.getenv('PROBABILITY_THRESHOLD', 0.7))
    WATCH_DURATION_SECONDS = int(os.getenv('WATCH_DURATION_SECONDS', 300))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading_bot.log')
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY is required for trading")
        if not cls.WALLET_ADDRESS:
            raise ValueError("WALLET_ADDRESS is required for trading")
        return True
