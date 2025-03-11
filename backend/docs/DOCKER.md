# Docker Setup for PredictPool Backend

This document explains how to set up and run the PredictPool backend using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git repository cloned to your local machine

## Configuration

1. Navigate to the Docker directory:
   ```bash
   cd backend/docker
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your values:
   ```bash
   nano .env
   ```

   Required environment variables:
   - `CONTRACT_ADDRESS`: Address of the deployed PredictVault contract
   - `PRIVATE_KEY`: Private key for contract interactions (owner)
   - `RPC_URL`: Ethereum RPC endpoint
   - `SYMBOL`: Symbol for price API (e.g., MONUSDT)

   If you're using a proxy, these are also required:
   - `PROXY_USER`: Proxy username
   - `PROXY_PASSWORD`: Proxy password
   - `PROXY_IP`: Proxy IP address
   - `PROXY_PORT`: Proxy port

## Building and Running

1. Prepare the Docker build:
   ```bash
   chmod +x prepare_docker_build.sh
   ./prepare_docker_build.sh
   ```

   This script:
   - Creates the necessary package structure
   - Copies all source files, config files, and ABI files
   - Copies Docker-specific files like run.py and docker-entrypoint.sh

2. Build the Docker image:
   ```bash
   docker-compose build
   ```

3. Run the container:
   ```bash
   docker-compose up -d
   ```

4. Check the logs:
   ```bash
   docker-compose logs -f
   ```

5. Stop the container when done:
   ```bash
   docker-compose down
   ```

## Troubleshooting

### Import Errors

If you see errors like `ModuleNotFoundError: No module named 'backend'`, it means the Docker container is having issues with the Python package structure. The `run.py` script should automatically fix the imports, but if it doesn't:

1. Check that the prepare_docker_build.sh script ran successfully
2. Verify that all __init__.py files were created
3. Check the Docker logs for specific error messages

### Database Issues

If you're having issues with the database:

1. The database is stored in a Docker volume named `predict_pool_data`
2. You can check the volume with `docker volume ls`
3. To reset the database, remove the volume with `docker volume rm predict_pool_data`

### ABI File Issues

If you're having issues with the ABI files:

1. Make sure the ABI files exist in the `backend/abi` directory
2. Run the copy_abi.sh script manually: `./copy_abi.sh`
3. Check the Docker logs for ABI-related error messages

## Custom Modifications

If you need to make custom modifications to the Docker setup:

1. Edit the files in the `backend/docker` directory
2. Run the prepare_docker_build.sh script again
3. Rebuild and restart the container:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d