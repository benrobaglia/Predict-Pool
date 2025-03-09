#!/usr/bin/env python3
"""
Test script to verify weight updates from backend to smart contract.
This script directly tests the blockchain module's update_user_weights function.
"""

import sys
import os
import logging
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import backend modules
import blockchain
import models
import config

# Fix ABI path issue
try:
    with open('abi/PredictVault_abi.json', 'r') as f:
        blockchain.contract_abi = json.load(f)
except FileNotFoundError:
    logger.error("PredictVault_abi.json not found in abi/ directory.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test user addresses (replace with actual addresses that have deposited to the contract)
TEST_USERS = [
    '0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5',
    '0x209ebD2cA4d5FfF84356948D75fD73883361F49B'
]

def test_weight_update():
    """
    Test the weight update process from backend to smart contract.
    
    This function:
    1. Gets the list of test users
    2. Assigns weights to these users
    3. Updates the weights on the blockchain
    4. Verifies that the weights were correctly updated
    """
    logger.info("Starting weight update test")
    
    # For testing, assign simple weights: 60/40 split
    addresses = TEST_USERS
    weights = [60, 40]  # 60% for first user, 40% for second user
    
    logger.info(f"Test users: {addresses}")
    logger.info(f"Assigned weights: {weights}")
    
    # Get current weights from blockchain
    logger.info("Current weights on blockchain:")
    for i, address in enumerate(addresses):
        current_weight = blockchain.get_user_weight(address)
        logger.info(f"  User {address}: {current_weight}")
    
    # Update weights on the blockchain
    logger.info("Updating weights on the blockchain...")
    success = blockchain.update_user_weights(addresses, weights)
    
    if not success:
        logger.error("Failed to update weights on the blockchain")
        return False
    
    logger.info("Weights updated successfully on the blockchain")
    
    # Verify that weights were correctly updated
    logger.info("Verifying weights on the blockchain...")
    all_correct = True
    
    for i, address in enumerate(addresses):
        expected_weight = weights[i]
        actual_weight = blockchain.get_user_weight(address)
        
        if actual_weight != expected_weight:
            logger.error(f"Weight mismatch for user {address}: expected {expected_weight}, got {actual_weight}")
            all_correct = False
        else:
            logger.info(f"Weight verified for user {address}: {actual_weight}")
    
    if all_correct:
        logger.info("All weights were correctly updated on the blockchain")
        return True
    else:
        logger.error("Some weights were not correctly updated on the blockchain")
        return False

if __name__ == "__main__":
    # Run the test
    success = test_weight_update()
    
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1)
