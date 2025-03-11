#!/bin/bash

# This script prepares the Docker build context by copying necessary files

# Create directories if they don't exist
mkdir -p ./abi
mkdir -p ./src
mkdir -p ./config
mkdir -p ./tests

# Copy __init__.py files
echo "# This file makes the directory a Python package" > ./__init__.py
echo "# This file makes the directory a Python package" > ./src/__init__.py
echo "# This file makes the directory a Python package" > ./config/__init__.py
echo "# This file makes the directory a Python package" > ./tests/__init__.py

# Copy Docker-specific files
cp -v ./run.py ../run.py 2>/dev/null || echo "run.py not found in Docker directory"
cp -v ./docker-entrypoint.sh ../docker-entrypoint.sh 2>/dev/null || echo "docker-entrypoint.sh not found in Docker directory"
cp -v ../copy_abi.sh ../copy_abi.sh 2>/dev/null || echo "copy_abi.sh not found in parent directory"
cp -v ./.env.example ../.env.example 2>/dev/null || echo ".env.example not found in Docker directory"

# Check if .env file exists and copy it if it does
if [ -f "./.env" ]; then
    echo "Copying .env file..."
    cp -v ./.env ../.env
fi

# Copy source files
echo "Copying source files..."
cp -v ../src/*.py ./src/ 2>/dev/null || echo "No source files found"

# Copy config files
echo "Copying config files..."
cp -v ../config/*.py ./config/ 2>/dev/null || echo "No config files found"
cp -v ../config/requirements.txt ./requirements.txt 2>/dev/null || echo "requirements.txt not found"

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