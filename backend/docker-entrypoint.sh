#!/bin/bash
set -e

# Print environment variables (excluding sensitive ones)
echo "Starting PredictPool Backend with the following configuration:"
echo "HOST: $HOST"
echo "PORT: $PORT"
echo "DEBUG: $DEBUG"
echo "DATABASE_PATH: $DATABASE_PATH"
echo "SYMBOL: $SYMBOL"
echo "RPC_URL: $RPC_URL"
echo "CONTRACT_ADDRESS: $CONTRACT_ADDRESS"
echo "EPOCH_DURATION_SECONDS: $EPOCH_DURATION_SECONDS"
echo "EPOCH_LOCK_SECONDS: $EPOCH_LOCK_SECONDS"
echo "EPOCH_CALCULATING_SECONDS: $EPOCH_CALCULATING_SECONDS"
echo "ROUNDS_COUNT: $ROUNDS_COUNT"
echo "ROUND_LOCK_PERCENTAGE: $ROUND_LOCK_PERCENTAGE"
echo "ROUND_CALCULATING_SECONDS: $ROUND_CALCULATING_SECONDS"

# Check for required environment variables
if [ -z "$CONTRACT_ADDRESS" ]; then
    echo "ERROR: CONTRACT_ADDRESS environment variable is required"
    exit 1
fi

if [ -z "$PRIVATE_KEY" ]; then
    echo "ERROR: PRIVATE_KEY environment variable is required"
    exit 1
fi

if [ -z "$RPC_URL" ]; then
    echo "ERROR: RPC_URL environment variable is required"
    exit 1
fi

if [ -z "$SYMBOL" ]; then
    echo "ERROR: SYMBOL environment variable is required"
    exit 1
fi

# Check if ABI files exist
if [ ! -f "/app/abi/PredictVault_abi.json" ]; then
    echo "WARNING: PredictVault_abi.json not found in /app/abi/"
    echo "Checking alternative locations..."
    
    if [ -f "../abi/PredictVault_abi.json" ]; then
        echo "Found PredictVault_abi.json in ../abi/"
        mkdir -p /app/abi
        cp ../abi/PredictVault_abi.json /app/abi/
    else
        echo "WARNING: PredictVault_abi.json not found. The application may not function correctly."
    fi
fi

# Start the application
echo "Starting the application..."
exec python app.py