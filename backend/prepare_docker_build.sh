#!/bin/bash

# This script prepares the Docker build context by copying necessary files

# Create abi directory if it doesn't exist
mkdir -p ./abi

# Check if ABI files exist in the parent directory
if [ -d "../abi" ]; then
    echo "Copying ABI files from parent directory..."
    cp -v ../abi/*.json ./abi/ 2>/dev/null || echo "No ABI files found in parent directory"
else
    echo "ABI directory not found in parent directory"
fi

echo "ABI files in ./abi:"
ls -la ./abi/

echo "Ready to build Docker image. Run:"
echo "docker-compose build"
echo "docker-compose up"