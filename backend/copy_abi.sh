#!/bin/bash

# Create abi directory if it doesn't exist
mkdir -p /app/abi

# Check if ABI files exist in the parent directory
if [ -d "../abi" ]; then
    echo "Copying ABI files from parent directory..."
    cp -v ../abi/*.json /app/abi/ 2>/dev/null || echo "No ABI files found in parent directory"
else
    echo "ABI directory not found in parent directory"
fi

# Check if we have the ABI files in the current directory
if [ -d "./abi" ]; then
    echo "Copying ABI files from current directory..."
    cp -v ./abi/*.json /app/abi/ 2>/dev/null || echo "No ABI files found in current directory"
fi

# List the ABI files
echo "ABI files in /app/abi:"
ls -la /app/abi/