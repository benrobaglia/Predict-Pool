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

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`:
   ```
   # Required
   CONTRACT_ADDRESS=0x...  # Address of the deployed PredictVault contract
   PRIVATE_KEY=0x...       # Private key for contract interactions (owner)
   RPC_URL=https://...     # Ethereum RPC endpoint
   ```

3. Run the backend:
   ```bash
   cd backend
   python app.py
   ```

## Project Structure

```
predict-pool/
├── .env                    # Environment variables
├── foundry.toml            # Foundry configuration
├── src/
│   └── PredictVault.sol    # Main vault contract
├── script/
│   └── PredictVault.s.sol  # Deployment script
├── test/
│   └── PredictVault.t.sol  # Contract tests
└── backend/               # Python backend
    ├── app.py             # Main Flask application
    ├── models.py          # Database models
    ├── blockchain.py      # Contract interaction
    ├── routes.py          # API endpoints
    ├── tasks.py           # Scheduled tasks
    ├── utils.py           # Utility functions
    ├── config.py          # Configuration
    └── requirements.txt   # Python dependencies
```

## Deployment

### Smart Contract

Deploy to the Monad testnet:

```bash
forge script script/PredictVault.s.sol:DeployPredictVault --rpc-url https://testnet-rpc.monad.xyz --private-key <your-private-key> --broadcast --use solc:0.8.20
```

### Backend

For production deployment, consider using:
- Gunicorn as a WSGI server
- Nginx as a reverse proxy
- Systemd for process management

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

> [!NOTE]  
> In this foundry template the default chain is `monadTestnet`, if you wish to change it change the network in `foundry.toml`

<h4 align="center">
  <a href="https://docs.monad.xyz">Monad Documentation</a> | <a href="https://book.getfoundry.sh/">Foundry Documentation</a> | 
   <a href="https://github.com/monad-developers/foundry-monad/issues">Report Issue</a>
</h4>
