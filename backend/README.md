# PredictPool Backend

A Python Flask backend for the PredictPool dapp, where users can stake MON tokens and predict price movements to earn rewards.

## Overview

This backend provides:
- API endpoints for interacting with the PredictPool smart contract
- Management of epochs and prediction rounds
- User prediction tracking and evaluation
- Weight calculation for reward distribution
- Scheduled tasks for price fetching and epoch/round processing

## Setup

### Prerequisites

- Python 3.8+
- PredictVault smart contract deployed (address in .env file)
- Access to an Ethereum RPC endpoint

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables in the `.env` file:

```
# Required
CONTRACT_ADDRESS=0x...  # Address of the deployed PredictVault contract
PRIVATE_KEY=0x...       # Private key for contract interactions (owner)
RPC_URL=https://...     # Ethereum RPC endpoint

# Optional (defaults shown)
DEBUG=True
HOST=0.0.0.0
PORT=5000
DATABASE_PATH=database.db
EPOCH_DURATION_DAYS=7
ROUND_DURATION_HOURS=4
```

### Running the Backend

Start the Flask server:

```bash
python app.py
```

The server will:
1. Initialize the database if it doesn't exist
2. Start the scheduler for background tasks
3. Begin listening for API requests

## API Endpoints

### Health Check
- `GET /api/health` - Check if the API is running

### Epochs
- `GET /api/epochs/current` - Get current active epoch
- `GET /api/epochs/<epoch_id>` - Get epoch by ID
- `GET /api/epochs` - Get all epochs

### Rounds
- `GET /api/rounds/current` - Get current active round
- `GET /api/rounds/<round_id>` - Get round by ID
- `GET /api/epochs/<epoch_id>/rounds` - Get all rounds for an epoch

### Predictions
- `POST /api/predictions` - Create a new prediction
  - Required fields: `address`, `round_id`, `direction`, `signature`
- `GET /api/users/<address>/predictions` - Get all predictions for a user
- `GET /api/rounds/<round_id>/predictions` - Get all predictions for a round

### User Stats
- `GET /api/users/<address>/stats` - Get user stats for current epoch
- `GET /api/users/<address>/stats/<epoch_id>` - Get user stats for a specific epoch

### Leaderboard
- `GET /api/leaderboard` - Get leaderboard for current epoch
- `GET /api/leaderboard/<epoch_id>` - Get leaderboard for a specific epoch

### Contract Data
- `GET /api/contract/info` - Get contract information

## Authentication

API endpoints that modify data require authentication using Ethereum signatures:

1. Client creates a message: `Predict up for round 1`
2. Client signs message with their Ethereum wallet
3. Client sends the signature along with the request
4. Server verifies the signature matches the claimed address

## Database

The backend uses SQLite for simplicity. The database schema includes:

- `users` - User wallet addresses
- `epochs` - Epoch periods
- `rounds` - Prediction rounds within epochs
- `predictions` - User predictions for rounds
- `user_epoch_stats` - User performance statistics for epochs

In order to connect DB using DBeaver (or similar):
- Navigate to project folder in your machine -> backend -> database.db and copy the path
- Open DBeaver and establish new SQLite connection
- Paste the path copied earlier

It will looks something like `/path_to_project/Predict-Pool/backend/database.db`

## Scheduled Tasks

The backend runs several scheduled tasks:

- Price fetching (every 5 minutes)
- Round processing (every 10 minutes)
- Epoch processing (every hour)

## Development

For local development:

1. Deploy the PredictVault contract to a local blockchain (e.g., Hardhat, Ganache)
2. Update the `.env` file with the contract address and RPC URL
3. Run the backend with `DEBUG=True` for detailed logging
