# Deployment Guide for PredictPool Backend

This guide explains how to deploy the PredictPool backend to Render.com using Docker.

## Prerequisites

- A Render.com account
- Your environment variables (CONTRACT_ADDRESS, PRIVATE_KEY, RPC_URL, etc.)
- Your code pushed to a Git repository (GitHub, GitLab, etc.)

## Preparation Steps

### 1. Prepare the Build Environment

Before deploying to Render, you need to make sure the ABI files are available in your repository:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Make the preparation script executable:
   ```bash
   chmod +x prepare_docker_build.sh
   ```

3. Run the preparation script:
   ```bash
   ./prepare_docker_build.sh
   ```

This script will copy the ABI files from the parent directory to the backend/abi directory, making them available during the Docker build.

4. Commit the changes to your repository:
   ```bash
   git add abi/
   git commit -m "Add ABI files for Docker deployment"
   git push
   ```

## Deployment Steps

### 1. Create a New Web Service on Render

1. Log in to your Render dashboard
2. Click on "New +" and select "Web Service"
3. Connect your Git repository
4. Navigate to the repository containing your PredictPool backend

### 2. Configure the Web Service

Fill in the following details:

- **Name**: `predict-pool-backend` (or your preferred name)
- **Environment**: `Docker`
- **Branch**: `main` (or your preferred branch)
- **Root Directory**: `backend` (if your Dockerfile is in a subdirectory)
- **Docker Command**: Leave empty (it will use the CMD from your Dockerfile)

### 3. Add Environment Variables

Add the following environment variables in the Render dashboard:

- `CONTRACT_ADDRESS`: Your deployed PredictVault contract address
- `PRIVATE_KEY`: Private key for contract interactions
- `RPC_URL`: Ethereum RPC endpoint
- `SYMBOL`: The trading pair symbol (e.g., ETHUSDT)
- `DATABASE_PATH`: `/data/database.db`
- `DEBUG`: `False` (for production)
- `HOST`: `0.0.0.0`
- `PORT`: `10000` (Render assigns a PORT env var, but you can override it)
- `EPOCH_DURATION_SECONDS`: `600` (or your preferred value)
- `EPOCH_LOCK_SECONDS`: `10` (or your preferred value)
- `EPOCH_CALCULATING_SECONDS`: `10` (or your preferred value)
- `ROUNDS_COUNT`: `10` (or your preferred value)
- `ROUND_LOCK_PERCENTAGE`: `0.5` (or your preferred value)
- `ROUND_CALCULATING_SECONDS`: `10` (or your preferred value)

### 4. Configure Persistent Disk

For database persistence:

1. Scroll down to the "Disks" section
2. Enable the disk
3. Set the path to `/data`
4. Choose an appropriate size (1GB should be sufficient to start)

### 5. Deploy the Service

1. Click "Create Web Service"
2. Render will build and deploy your Docker container
3. Once deployed, you can access your API at the provided URL

## Monitoring and Logs

- Monitor your service from the Render dashboard
- View logs by clicking on your service and selecting the "Logs" tab
- Set up alerts for service health

## Updating the Deployment

To update your deployment:

1. Push changes to your Git repository
2. Render will automatically rebuild and deploy the updated version

## Troubleshooting

If you encounter issues:

1. Check the logs in the Render dashboard
2. Verify your environment variables are correctly set
3. Ensure your Dockerfile is properly configured
4. Check that your persistent disk is mounted correctly

## Local Testing Before Deployment

Before deploying to Render, test your Docker setup locally:

```bash
# Build and run using docker-compose
cd backend
docker-compose up --build

# Test the API
curl http://localhost:5000/api/health
```

If everything works locally but not on Render, check for environment-specific issues.