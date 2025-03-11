import logging
import json
from datetime import datetime
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        try:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%b %d, %Y %H:%M:%S')
        except ValueError:
            return timestamp
    return timestamp

def format_address(address, short=True):
    """Format Ethereum address for display"""
    if not address:
        return ''
    
    if short:
        return f"{address[:6]}...{address[-4:]}"
    return address

def format_price(price, decimals=2):
    """Format price for display"""
    if price is None:
        return 'N/A'
    
    try:
        return f"${float(price):.{decimals}f}"
    except (ValueError, TypeError):
        return str(price)

def format_percentage(value, decimals=2):
    """Format percentage for display"""
    if value is None:
        return 'N/A'
    
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)

def to_wei(amount, decimals=18):
    """Convert amount to wei"""
    if amount is None:
        return 0
    
    try:
        return int(float(amount) * (10 ** decimals))
    except (ValueError, TypeError):
        return 0

def from_wei(amount, decimals=18):
    """Convert wei to amount"""
    if amount is None:
        return 0
    
    try:
        return float(amount) / (10 ** decimals)
    except (ValueError, TypeError):
        return 0

def is_valid_address(address):
    """Check if address is valid Ethereum address"""
    if not address:
        return False
    
    try:
        return Web3.is_address(address)
    except:
        return False

def is_valid_signature(message, signature, address):
    """Check if signature is valid for address"""
    if not message or not signature or not address:
        return False
    
    try:
        from eth_account.messages import encode_defunct
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == address.lower()
    except Exception as e:
        logger.error(f"Error validating signature: {e}")
        return False

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json(data):
    """Convert data to JSON string"""
    return json.dumps(data, default=json_serial)

def from_json(json_str):
    """Convert JSON string to data"""
    try:
        return json.loads(json_str)
    except:
        return None

def calculate_time_remaining(end_time):
    """Calculate time remaining until end_time"""
    if isinstance(end_time, str):
        try:
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return 'Invalid time format'
    
    now = datetime.now()
    if now >= end_time:
        return 'Ended'
    
    delta = end_time - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_price_change(start_price, end_price):
    """Calculate price change percentage"""
    if start_price is None or end_price is None or start_price == 0:
        return 0
    
    try:
        return (float(end_price) - float(start_price)) / float(start_price)
    except (ValueError, TypeError):
        return 0

def get_price_direction(start_price, end_price):
    """Get price direction (up or down)"""
    if start_price is None or end_price is None:
        return 'unknown'
    
    try:
        if float(end_price) > float(start_price):
            return 'up'
        elif float(end_price) < float(start_price):
            return 'down'
        else:
            return 'unchanged'
    except (ValueError, TypeError):
        return 'unknown'
