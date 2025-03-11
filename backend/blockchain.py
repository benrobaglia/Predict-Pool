from web3 import Web3
import json
import os
import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load ABI from the project root
try:
    # Try to load from relative path (for development)
    abi_path = '../abi/PredictVault_abi.json'
    if not os.path.exists(abi_path):
        # Try to load from absolute path (for Docker)
        abi_path = '/app/abi/PredictVault_abi.json'
    
    with open(abi_path, 'r') as f:
        contract_abi = json.load(f)
except FileNotFoundError:
    logger.error("PredictVault_abi.json not found. Make sure the file exists in the project root or /app/abi directory.")
    contract_abi = None

# Initialize Web3 connection
def get_web3():
    """Get Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        if not w3.is_connected():
            logger.error(f"Failed to connect to RPC URL: {config.RPC_URL}")
            return None
        return w3
    except Exception as e:
        logger.error(f"Error initializing Web3: {e}")
        return None

# Get contract instance
def get_contract():
    """Get contract instance"""
    w3 = get_web3()
    if not w3 or not contract_abi or not config.CONTRACT_ADDRESS:
        return None
    
    try:
        contract_address = Web3.to_checksum_address(config.CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        return contract
    except Exception as e:
        logger.error(f"Error getting contract instance: {e}")
        return None

# Update user weights
def update_user_weights(user_addresses, weights):
    """Update user weights on the contract"""
    w3 = get_web3()
    contract = get_contract()
    
    if not w3 or not contract or not config.PRIVATE_KEY:
        logger.error("Missing required configuration for blockchain interaction")
        return False
    
    try:
        # Convert addresses to checksum format
        checksum_addresses = [Web3.to_checksum_address(addr) for addr in user_addresses]
        
        # Prepare transaction
        account = w3.eth.account.from_key(config.PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build transaction
        tx = contract.functions.batchUpdateUserWeights(
            checksum_addresses, weights
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)       
         
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        logger.info(f"Transaction successful: {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        logger.error(f"Error updating user weights: {e}")
        return False

# Get total MON in vault
def get_total_mon():
    """Get total MON in vault"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        return contract.functions.totalMON().call()
    except Exception as e:
        logger.error(f"Error getting total MON: {e}")
        return 0

# Get total shMON in vault
def get_total_shmon():
    """Get total shMON in vault"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        return contract.functions.totalshMON().call()
    except Exception as e:
        logger.error(f"Error getting total shMON: {e}")
        return 0
    

# Get all users using the getUsers function from the smart contract
def get_users():
    """Get all users in Smart Contract"""
    contract = get_contract()
    if not contract:
        return []
    
    try:
        users = contract.functions.getUsers().call()
        logger.info(f"Fetched {len(users)} active users from smart contract that are eligible to predict")
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []
        

# Get user balance
def get_user_balance(address):
    """Get user gMON balance"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        checksum_address = Web3.to_checksum_address(address)
        return contract.functions.balanceOf(checksum_address).call()
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        return 0

# Get user weight
def get_user_weight(address):
    """Get user weight from contract"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        checksum_address = Web3.to_checksum_address(address)
        return contract.functions.userWeights(checksum_address).call()
    except Exception as e:
        logger.error(f"Error getting user weight: {e}")
        return 0

# Get epoch baseline
def get_epoch_baseline():
    """Get epoch baseline from contract"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        return contract.functions.epochBaseline().call()
    except Exception as e:
        logger.error(f"Error getting epoch baseline: {e}")
        return 0

# Get epoch total supply
def get_epoch_total_supply():
    """Get epoch total supply from contract"""
    contract = get_contract()
    if not contract:
        return 0
    
    try:
        return contract.functions.epochTotalSupply().call()
    except Exception as e:
        logger.error(f"Error getting epoch total supply: {e}")
        return 0

# Calculate user rewards and APY for an epoch
def calculate_users_rewards_and_apy(display_scale_factor=10):
    """
    Calculate all users rewards and APY for a completed epoch
    
    Args:
        display_scale_factor: Scale the display staking rewards (to show significant numbers as staking is not live on Monad yet)
        
    Returns:
        Dictionary with rewards and APY information for each user
    """
    # Validate display_scale_factor
    if display_scale_factor <= 0:
        logger.error(f"Invalid display_scale_factor: {display_scale_factor}. Must be positive.")
        return {"error": "display_scale_factor must be positive"}
    
    contract = get_contract()
    if not contract:
        logger.error("Contract not available. Check RPC connection and contract address.")
        return {"error": "Contract not available"}
    
    try:
        # Get epoch data
        current_total_mon = get_total_mon()
        epoch_baseline = get_epoch_baseline()
        epoch_total_supply = get_epoch_total_supply()
        
        # Get all users and their weights
        users = get_users()

        # If no rewards generated, return early
        if current_total_mon <= epoch_baseline:
            return {u: {
                        "rewards": 0,
                        "apy": 0,
                        "annualized_apy": 0,
                        "display_apy": 0,
                        "epoch_rewards": 0
                    }
                    for u in users
            }
        
        # 1. Calculate total rewards generated during the epoch
        epoch_rewards = current_total_mon - epoch_baseline
                
        # 2. Calculate denominator: sum of (weight * deposited_mon) for all users
        denominator = 0
        for user in users:
            user_balance = contract.functions.balanceOf(user).call()
            user_weight = contract.functions.userWeights(user).call()
            
            # Skip users with zero balance
            if user_balance == 0:
                continue
            
            # Calculate deposited MON using the formula from the smart contract
            deposited_mon = (user_balance * epoch_baseline) // epoch_total_supply
            denominator += user_weight * deposited_mon
        
        if denominator == 0:
            return {u: {
                        "rewards": 0,
                        "apy": 0,
                        "annualized_apy": 0,
                        "display_apy": 0,
                        "epoch_rewards": epoch_rewards
                    }
                    for u in users
            }
        
        result = {}
        for user_address in users:
            # Get user's balance and weight
            user_balance = contract.functions.balanceOf(user_address).call()
            user_weight = contract.functions.userWeights(user_address).call()
            
            # Calculate user's deposited MON
            deposited_mon = (user_balance * epoch_baseline) // epoch_total_supply
            
            # 3. Calculate user's rewards using the formula
            user_reward = (epoch_rewards * user_weight * deposited_mon) // denominator
            
            # 4. Calculate APY (rewards / deposited_mon)
            apy = 0
            if deposited_mon > 0:
                apy = (user_reward * 100) / deposited_mon  # As percentage
            
            # 5. Annualize the APY (1 epoch = 10 minutes, so multiply by 6*24*365)
            # This assumes 6 epochs per hour, 24 hours per day, 365 days per year
            annualized_apy = apy * 6 * 24 * 365
            
            # 6. Multiply by 10 for display (as per requirement)
            display_apy = annualized_apy * 10
            result[user_address] = {
                                    "rewards": user_reward,
                                    "apy": apy,
                                    "annualized_apy": annualized_apy,
                                    "display_apy": display_apy,
                                    "epoch_rewards": epoch_rewards
                                }
            
        return result
    
    except Exception as e:
        logger.error(f"Error calculating user rewards: {e}")
        return {"error": str(e)}

# Update epoch
def update_epoch():
    """Update epoch on the contract"""
    w3 = get_web3()
    contract = get_contract()
    
    if not w3 or not contract or not config.PRIVATE_KEY:
        logger.error("Missing required configuration for blockchain interaction")
        return False
    
    try:
        # Prepare transaction
        account = w3.eth.account.from_key(config.PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build transaction
        tx = contract.functions.updateEpoch().build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        logger.info(f"Epoch update transaction successful: {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        logger.error(f"Error updating epoch: {e}")
        return False
