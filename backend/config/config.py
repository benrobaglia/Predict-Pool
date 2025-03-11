import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Blockchain configuration
RPC_URL = os.getenv('RPC_URL', 'http://localhost:8545')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
STAKED_MON_ADDRESS = os.getenv('STAKED_MON_ADDRESS')
SYMBOL = os.getenv('SYMBOL')

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')

# Application configuration
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))

# Price API configuration
PRICE_API_URL = os.getenv('PRICE_API_URL', 'https://api.binance.com/api/v3/ticker/price?symbol=')

# Epoch and round configuration
EPOCH_DURATION_SECONDS = int(os.getenv('EPOCH_DURATION_SECONDS', '600'))
EPOCH_LOCK_SECONDS = int(os.getenv('EPOCH_LOCK_SECONDS', '10'))
EPOCH_CALCULATING_SECONDS = int(os.getenv('EPOCH_CALCULATING_SECONDS', '10'))
ROUNDS_COUNT = int(os.getenv('ROUNDS_COUNT', '10'))
ROUND_LOCK_PERCENTAGE = float(os.getenv('ROUND_LOCK_SECONDS', '0.5'))
ROUND_CALCULATING_SECONDS = int(os.getenv('ROUND_CALCULATING_SECONDS', '10'))

proxy_user = os.getenv("PROXY_USER")
proxy_password = os.getenv("PROXY_PASSWORD")
proxy_ip = os.getenv("PROXY_IP")
proxy_port = os.getenv("PROXY_PORT")

PROXY = {
    "https": f"http://{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}"
}