## Foundry-Monad# PredictVault - ERC4626 Vault for MON Tokens

PredictVault is an ERC4626-compliant vault contract that accepts MON token deposits, automatically stakes them in shMON, and manages user withdrawal requests. It also allows an off-chain algorithm to update user weights via administrative functions.

## Project Overview

This project implements a vault contract that:

1. Accepts MON token deposits and automatically stakes them in shMON
2. Manages user withdrawal requests
3. Allows an off-chain algorithm to update user weights via administrative functions

## Technical Architecture

The project is built using:

- **Solidity**: Version 0.8.20
- **Foundry**: For development, testing, and deployment
- **OpenZeppelin Contracts**: For ERC4626, ERC20, and other standard implementations

### Key Components

- **PredictVault.sol**: The main vault contract that implements the ERC4626 standard
- **IStakedMON**: Interface for interacting with the shMON staking contract

## Development Setup

### Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation)
- [Solidity](https://docs.soliditylang.org/en/v0.8.20/)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd predict-pool
   ```

2. Install dependencies:
   ```bash
   forge install
   ```

3. Build the project:
   ```bash
   forge build --use solc:0.8.20
   ```

### Testing

Run the tests:

```bash
forge test --use solc:0.8.20
```

For verbose output:

```bash
forge test --use solc:0.8.20 -v
```

## Deployment

### Monad Testnet

To deploy to the Monad testnet:

1. Update the token addresses in `script/PredictVault.s.sol`:
   ```solidity
   address constant MON_TOKEN = address(0); // Replace with actual MON token address
   address constant STAKED_MON = address(0); // Replace with actual shMON token address
   ```

2. Deploy using Foundry:
   ```bash
   forge script script/PredictVault.s.sol:DeployPredictVault --rpc-url https://testnet-rpc.monad.xyz --private-key <your-private-key> --broadcast --use solc:0.8.20
   ```

## Contract Usage

### Depositing Tokens

Users can deposit MON tokens into the vault:

```solidity
// Approve the vault to spend MON tokens
monToken.approve(vaultAddress, amount);

// Deposit tokens into the vault
vault.deposit(amount, receiverAddress);
```

### Withdrawing Tokens

Users can withdraw their tokens:

```solidity
// Withdraw tokens from the vault
vault.withdraw(amount, receiverAddress, ownerAddress);
```

### Updating User Weights

The contract owner can update user weights:

```solidity
// Update a single user's weight
vault.updateUserWeight(userAddress, newWeight);

// Update multiple users' weights in a batch
vault.batchUpdateUserWeights(userAddresses, newWeights);
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

> [!NOTE]  
> In this foundry template the default chain is `monadTestnet`, if you wish to change it change the network in `foundry.toml`

<h4 align="center">
  <a href="https://docs.monad.xyz">Monad Documentation</a> | <a href="https://book.getfoundry.sh/">Foundry Documentation</a> | 
   <a href="https://github.com/monad-developers/foundry-monad/issues">Report Issue</a>
</h4>

_Foundry-Monad is a Foundry template with Monad configuration. So developers don't have to do the initial configuration in Foundry for Monad network._

**Foundry is a blazing fast, portable and modular toolkit for Ethereum application development written in Rust.**

Foundry consists of:

-   **Forge**: Ethereum testing framework (like Truffle, Hardhat and DappTools).
-   **Cast**: Swiss army knife for interacting with EVM smart contracts, sending transactions and getting chain data.
-   **Anvil**: Local Ethereum node, akin to Ganache, Hardhat Network.
-   **Chisel**: Fast, utilitarian, and verbose solidity REPL.

## Requirements

Before you begin, you need to install the following tools:

-   Rust
-   Cargo
-   [Foundryup](https://book.getfoundry.sh/getting-started/installation)

## Quickstart

To get started, follow the steps below:

1. You can either clone this repo using the below command:

```sh
git clone https://github.com/monad-developers/foundry-monad
```

or

You can do it manually using the below set of commands:

```sh
mkdir [project_name] && cd [project_name] && forge init --template monad-developers/foundry-monad
```

The foundry project is now ready to be used!

## Examples

### Compile

```shell
forge compile
```

### Build

```shell
forge build
```

### Test

```shell
forge test
```

### Deploy and Verify

```shell
forge create \
  --private-key <your_private_key> \
  src/Counter.sol:Counter \
  --broadcast \
  --verify \
  --verifier sourcify \
  --verifier-url https://sourcify-api-monad.blockvision.org
```

### Deploy

```shell
forge create --private-key <your_private_key> src/Counter.sol:Counter --broadcast
```

### Verify Contract

```shell
forge verify-contract \
  <contract_address> \
  src/Counter.sol:Counter \
  --chain 10143 \
  --verifier sourcify \
  --verifier-url https://sourcify-api-monad.blockvision.org
```

### Format

```shell
forge fmt
```

### Gas Snapshots

```shell
forge snapshot
```

### Anvil

```shell
anvil
```

### Cast

```shell
cast <subcommand>
```

### Help

```shell
forge --help
```

```shell
anvil --help
```

```shell
cast --help
```
