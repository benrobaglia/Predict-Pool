# Docker Setup for PredictPool Backend

This document explains how to use Docker to run the PredictPool backend locally and prepare it for deployment.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine

## Files Overview

- `Dockerfile`: Defines how to build the Docker image for the backend
- `docker-compose.yml`: Configures the services, networks, and volumes
- `.dockerignore`: Specifies which files should be excluded from the Docker build context

## Running Locally with Docker

### 1. Prepare the Build Environment

Before building the Docker image, run the preparation script to copy the necessary ABI files:

```bash
# Navigate to the backend directory
cd backend

# Make the script executable if needed
chmod +x prepare_docker_build.sh

# Run the preparation script
./prepare_docker_build.sh
```

This script will copy the ABI files from the parent directory to the backend/abi directory, making them available during the Docker build.

### 2. Environment Variables

Create a `.env` file in the backend directory with your configuration:

```
# Required
CONTRACT_ADDRESS=0x...  # Address of the deployed PredictVault contract
PRIVATE_KEY=0x...       # Private key for contract interactions (owner)
RPC_URL=https://...     # Ethereum RPC endpoint
SYMBOL=ETHUSDT          # The trading pair symbol

# Optional (defaults shown)
DEBUG=True
HOST=0.0.0.0
PORT=5000
DATABASE_PATH=/data/database.db
EPOCH_DURATION_SECONDS=600
EPOCH_LOCK_SECONDS=10
EPOCH_CALCULATING_SECONDS=10
ROUNDS_COUNT=10
ROUND_LOCK_PERCENTAGE=0.5
ROUND_CALCULATING_SECONDS=10
```

### 3. Build and Run with Docker Compose

```bash
# Navigate to the backend directory
cd backend

# Build and start the containers
docker-compose up --build

# To run in detached mode (background)
docker-compose up --build -d

# To stop the containers
docker-compose down
```

### 3. Accessing the Application

Once running, the API will be available at:
- http://localhost:5000/

Test the API with:
```bash
curl http://localhost:5000/api/health
```

## Data Persistence

The application uses a volume named `predict_pool_data` to persist the SQLite database. This ensures your data is not lost when the container is restarted.

To view the volumes:
```bash
docker volume ls
```

To remove the volume (and all data):
```bash
docker volume rm predict_pool_data
```

## Building for Production

For production deployment, you might want to build the image directly:

```bash
# Build the image
docker build -t predict-pool-backend .

# Run the container
docker run -p 5000:5000 \
  -e CONTRACT_ADDRESS=0x... \
  -e PRIVATE_KEY=0x... \
  -e RPC_URL=https://... \
  -e SYMBOL=ETHUSDT \
  -e DEBUG=False \
  -v predict_pool_data:/data \
  predict-pool-backend
```

## Troubleshooting

### Container Logs

To view logs from the container:
```bash
# If using docker-compose
docker-compose logs

# If running the container directly
docker logs <container_id>
```

### Accessing the Container Shell

To get a shell inside the running container:
```bash
# If using docker-compose
docker-compose exec backend bash

# If running the container directly
docker exec -it <container_id> bash
```

### Common Issues

1. **Database permissions**: If you see permission errors related to the database, ensure the `/data` directory has the correct permissions.

2. **Environment variables**: Make sure all required environment variables are set correctly.

3. **Network issues**: If the container can't connect to external services (like the RPC endpoint), check your network configuration and firewall settings.

## Deployment

For deployment to cloud services like Render.com, see the [DEPLOYMENT.md](./DEPLOYMENT.md) file.