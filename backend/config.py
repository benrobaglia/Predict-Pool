import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Blockchain configuration
RPC_URL = os.getenv('RPC_URL', 'http://localhost:8545')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
STAKED_MON_ADDRESS = os.getenv('STAKED_MON_ADDRESS')

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')

# Application configuration
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))

# Price API configuration
PRICE_API_URL = os.getenv('PRICE_API_URL', 'https://api.binance.com/api/v3/ticker/price?symbol=')

# Epoch and round configuration
EPOCH_DURATION_DAYS = int(os.getenv('EPOCH_DURATION_DAYS', '7'))
ROUND_DURATION_HOURS = int(os.getenv('ROUND_DURATION_HOURS', '4'))
