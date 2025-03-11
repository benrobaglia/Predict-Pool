# PredictPool - Prediction Dapp for MON Token Staking

PredictPool is a dapp where users can stake their native MON tokens in a vault and gamble their staking rewards by predicting the future price of MON (up or down). At the end of each epoch, user accuracy scores are normalized to determine reward weights.

## Project Overview

This project consists of two main components:

1. **Smart Contract (PredictVault)**: An ERC4626-compliant vault that accepts MON token deposits, automatically stakes them in shMON, and distributes rewards based on user weights.

2. **Python Backend**: A Flask-based backend that manages epochs, rounds, user predictions, and calculates weights based on prediction accuracy.

## Smart Contract

The PredictVault contract is built using:

- **Solidity**: Version 0.8.20
- **Foundry**: For development, testing, and deployment
- **OpenZeppelin Contracts**: For ERC20 and other standard implementations

### Key Features

- Accepts native MON token deposits and automatically stakes them in shMON
- Issues gMON tokens as shares in the vault
- Distributes staking rewards based on user weights
- Allows an off-chain algorithm to update user weights via administrative functions

## Backend

The Python backend provides:

- API endpoints for interacting with the PredictPool smart contract
- Management of epochs and prediction rounds
- User prediction tracking and evaluation
- Weight calculation for reward distribution
- Scheduled tasks for price fetching and epoch/round processing

### Technology Stack

- **Flask**: Lightweight web framework
- **SQLite**: Simple file-based database
- **Web3.py**: For blockchain interaction
- **APScheduler**: For scheduled tasks
- **Backoff**: For retry logic with exponential backoff

## Project Structure

```
predict-pool/
├── .gitignore                # Git ignore file
├── foundry.toml              # Foundry configuration
├── README.md                 # Project documentation
├── abi/                      # Contract ABI files
│   └── PredictVault_abi.json # Main vault contract ABI
├── src/                      # Smart contract source code
│   └── PredictVault.sol      # Main vault contract
├── script/                   # Deployment scripts
│   └── PredictVault.s.sol    # Deployment script
├── test/                     # Contract tests
│   └── PredictVault.t.sol    # Contract tests
└── backend/                  # Python backend
    ├── __init__.py           # Package initialization
    ├── run.py                # Main entry point
    ├── verify_imports.py     # Import verification script
    ├── .dockerignore         # Docker ignore file
    ├── .gitignore            # Git ignore file
    ├── copy_abi.sh           # Script to copy ABI files
    ├── abi/                  # Contract ABI files (copy)
    │   └── PredictVault_abi.json # Main vault contract ABI
    ├── config/               # Configuration files
    │   ├── __init__.py       # Package initialization
    │   ├── .env.example      # Example environment variables
    │   ├── config.py         # Configuration module
    │   └── requirements.txt  # Python dependencies
    ├── docker/               # Docker configuration
    │   ├── .env.example      # Example environment variables for Docker
    │   ├── docker-compose.yml # Docker Compose configuration
    │   ├── docker-entrypoint.sh # Docker entrypoint script
    │   ├── Dockerfile        # Docker image definition
    │   ├── prepare_docker_build.sh # Docker build preparation script
    │   └── run.py            # Docker-specific entry point
    ├── docs/                 # Documentation
    │   ├── DOCKER.md         # Docker setup documentation
    │   └── API.md            # API documentation
    ├── src/                  # Backend source code
    │   ├── __init__.py       # Package initialization
    │   ├── app.py            # Main Flask application
    │   ├── blockchain.py     # Contract interaction
    │   ├── models.py         # Database models
    │   ├── routes.py         # API endpoints
    │   ├── tasks.py          # Scheduled tasks
    │   └── utils.py          # Utility functions
    └── tests/                # Backend tests
        ├── __init__.py       # Package initialization
        └── test_weight_update.py # Weight update test
```

## API Endpoints

The backend provides the following API endpoints:

### Health Check
- `GET /api/health`: Check if the API is running

### Epochs
- `GET /api/epochs/current`: Get the current active epoch
- `GET /api/epochs/<epoch_id>`: Get a specific epoch by ID
- `GET /api/epochs`: Get all epochs

### Rounds
- `GET /api/rounds/current`: Get the current active round
- `GET /api/rounds/<round_id>`: Get a specific round by ID
- `GET /api/epochs/<epoch_id>/rounds`: Get all rounds for an epoch

### Predictions
- `POST /api/predictionsv2`: Create a new prediction (authenticated)
- `GET /api/users/<address>/predictions`: Get all predictions for a user
- `GET /api/rounds/<round_id>/predictions`: Get all predictions for a round

### User Stats
- `GET /api/users/<address>/stats`: Get user stats for the current epoch
- `GET /api/users/<address>/stats/<epoch_id>`: Get user stats for a specific epoch

### Leaderboard
- `GET /api/leaderboard`: Get leaderboard for the current epoch
- `GET /api/leaderboard/<epoch_id>`: Get leaderboard for a specific epoch

### Contract Data
- `GET /api/contract/info`: Get contract information
- `GET /api/rewards/apy`: Get rewards and APY for all users

## Development Setup

### Smart Contract

1. Install Foundry:
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. Build the contract:
   ```bash
   forge build --use solc:0.8.20
   ```

3. Run tests:
   ```bash
   forge test --use solc:0.8.20
   ```

### Backend

1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   cd backend
   pip install -r config/requirements.txt
   ```

3. Copy the ABI files:
   ```bash
   cd backend
   ./copy_abi.sh
   ```

4. Create a `.env` file in the `backend/config` directory based on `.env.example`:
   ```
   # Required
   CONTRACT_ADDRESS=0x...  # Address of the deployed PredictVault contract
   PRIVATE_KEY=0x...       # Private key for contract interactions (owner)
   RPC_URL=https://...     # Ethereum RPC endpoint
   SYMBOL=MONUSDT          # Symbol for price API
   DATABASE_PATH=database.db # Path to SQLite database
   
   # Optional
   DEBUG=True              # Enable debug mode
   HOST=0.0.0.0            # Host to bind to
   PORT=5000               # Port to listen on
   
   # Epoch and round configuration
   EPOCH_DURATION_SECONDS=600
   EPOCH_LOCK_SECONDS=10
   EPOCH_CALCULATING_SECONDS=10
   ROUNDS_COUNT=10
   ROUND_LOCK_PERCENTAGE=0.5
   ROUND_CALCULATING_SECONDS=10
   
   # Proxy configuration (if needed)
   PROXY_USER=             # Proxy username
   PROXY_PASSWORD=         # Proxy password
   PROXY_IP=               # Proxy IP address
   PROXY_PORT=             # Proxy port
   ```

5. Run the backend:
   ```bash
   cd backend
   python run.py
   ```

## Running Tests

### Smart Contract Tests

```bash
forge test --use solc:0.8.20
```

### Backend Tests

```bash
cd backend
python -m tests.test_weight_update
```

## Deployment

### Smart Contract

Deploy to the Monad testnet:

```bash
forge script script/PredictVault.s.sol:DeployPredictVault --rpc-url https://testnet-rpc.monad.xyz --private-key <your-private-key> --broadcast --use solc:0.8.20
```

### Backend

#### Using Docker

For detailed Docker setup instructions, see [Docker Documentation](backend/docs/DOCKER.md).

Quick start:

```bash
# Set up environment variables
cd backend/docker
cp .env.example .env
nano .env  # Edit with your values

# Build and run
chmod +x prepare_docker_build.sh
./prepare_docker_build.sh
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop when done
docker-compose down
```

The following environment variables are required:
- `CONTRACT_ADDRESS`: Address of the deployed PredictVault contract
- `PRIVATE_KEY`: Private key for contract interactions (owner)
- `RPC_URL`: Ethereum RPC endpoint
- `SYMBOL`: Symbol for price API (e.g., MONUSDT)

If you're using a proxy, these are also required:
- `PROXY_USER`: Proxy username
- `PROXY_PASSWORD`: Proxy password
- `PROXY_IP`: Proxy IP address
- `PROXY_PORT`: Proxy port

#### Manual Deployment

For production deployment, consider using:
- Gunicorn as a WSGI server
- Nginx as a reverse proxy
- Systemd for process management

Example systemd service file:
```ini
[Unit]
Description=PredictPool Backend
After=network.target

[Service]
User=predictpool
WorkingDirectory=/path/to/predict-pool/backend
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "backend.src.app:create_app()"
Restart=on-failure
Environment=PYTHONPATH=/path/to/predict-pool

[Install]
WantedBy=multi-user.target
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

> [!NOTE]  
> In this foundry template the default chain is `monadTestnet`, if you wish to change it change the network in `foundry.toml`

<h4 align="center">
  <a href="https://docs.monad.xyz">Monad Documentation</a> | <a href="https://book.getfoundry.sh/">Foundry Documentation</a> | 
   <a href="https://github.com/monad-developers/foundry-monad/issues">Report Issue</a>
</h4>
