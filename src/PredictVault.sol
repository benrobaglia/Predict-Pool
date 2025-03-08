// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {ERC20} from "openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "openzeppelin-contracts/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";

/**
 * @title IStakedMON
 * @dev Interface for the shMON (staked MON) token contract.
 */
interface IStakedMON {
    function deposit(uint256 assets, address receiver) external payable returns (uint256);
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256);
    function totalAssets() external view returns (uint256);
    function convertToShares(uint256 assets) external view returns (uint256);
    function convertToAssets(uint256 shares) external view returns (uint256);
}

/**
 * @title PredictVault
 * @dev Vault that accepts native MON, stakes it to shMON, and manages user shares (gMON)
 *      along with off-chain managed weights and epoch-based reward distribution.
 */
contract PredictVault is ERC20, Ownable, ReentrancyGuard {
    // --- State Variables ---

    // The shMON token contract.
    IStakedMON public immutable stakedMON;
    
    // Mapping to store user weights (updated by an off-chain algorithm).
    mapping(address => uint256) public userWeights;
    
    // Active user tracking.
    address[] public users;
    mapping(address => bool) public userExists;
    
    // Epoch state variables:
    // epochBaseline: V^{MON}(0) — the vault’s total MON value at the start of the epoch.
    // epochTotalSupply: G_{tot}(0) — the total gMON supply at the start of the epoch.
    uint256 public epochBaseline;
    uint256 public epochTotalSupply;
    
    // --- Events ---
    event UserWeightUpdated(address indexed user, uint256 newWeight);
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event EpochUpdated(uint256 newEpochBaseline, uint256 newEpochTotalSupply);
    event EpochBaselineUpdated(uint256 oldBaseline, uint256 newBaseline, uint256 newTotalSupply);
    
    // --- Constructor ---
    /**
     * @dev Constructor.
     * @param _stakedMON The shMON token address.
     */
    constructor(address _stakedMON) ERC20("Gamble MON", "gMON") Ownable(msg.sender) {
        require(_stakedMON != address(0), "stakedMON address cannot be zero");
        stakedMON = IStakedMON(_stakedMON);
        // Epoch variables will be initialized on the first deposit.
        epochBaseline = 0;
        epochTotalSupply = 0;
    }
    
    function getUsers() external view returns (address[] memory) {
        return users;
    }

    // --- Weight Management Functions ---
    
    /**
     * @dev Updates a user's weight.
     * @param user The user address.
     * @param weight The new weight.
     */
    function updateUserWeight(address user, uint256 weight) external onlyOwner {
        userWeights[user] = weight;
        emit UserWeightUpdated(user, weight);
    }
    
    /**
     * @dev Batch update user weights.
     * @param _users Array of user addresses.
     * @param weights Array of weights.
     */
    function batchUpdateUserWeights(
        address[] calldata _users,
        uint256[] calldata weights
    ) external onlyOwner {
        require(_users.length == weights.length, "Array lengths must match");
        
        for (uint256 i = 0; i < _users.length; i++) {
            userWeights[_users[i]] = weights[i];
            emit UserWeightUpdated(_users[i], weights[i]);
        }
    }
    
    // --- Asset and Vault Value Functions ---
    
    /**
     * @dev Returns the total shMON tokens held by the vault.
     * @return The total shMON tokens.
     */
    function totalshMON() public view returns (uint256) {
        return IERC20(address(stakedMON)).balanceOf(address(this));
    }
    
    /**
     * @dev Returns the total assets (in MON) managed by the vault.
     * @return The total assets in MON.
     */
    function totalMON() public view returns (uint256) {
        return stakedMON.convertToAssets(totalshMON());
    }
    
    // --- Deposit Function ---
    
    /**
     * @dev Deposit native MON and stake directly in shMON.
     * @param receiver The address to receive the gMON shares.
     * @return shares The amount of gMON shares minted.
     */
    function depositNative(address receiver) external payable nonReentrant returns (uint256 shares) {
        uint256 assets = msg.value;
        require(assets > 0, "Cannot deposit 0 assets");

        // Stake MON for shMON.
        uint256 shMONReceived = stakedMON.deposit{value: assets}(assets, address(this));

        // Calculate gMON shares based on the shMON received
        uint256 total_gMON = totalSupply();
        uint256 totalShMON = totalshMON();
        
        // If this is the first deposit or there are no shMON tokens, use shMONReceived directly
        if (total_gMON == 0 || totalShMON == 0) {
            shares = shMONReceived;
        } else {
            // Otherwise calculate proportional shares based on the ratio of new shMON to total shMON
            shares = (shMONReceived * total_gMON) / totalShMON;
        }
        
        // Mint gMON shares to the receiver.
        _mint(receiver, shares);

        // Add user to active users list if not already present and initialize weight to 0
        // as they don't have access to staking rewards for the epoch in which they deposit.
        if (!userExists[receiver]) {
            users.push(receiver);
            userExists[receiver] = true;
            userWeights[receiver] = 0;
            emit UserWeightUpdated(receiver, 0);
        }

        emit Staked(receiver, shMONReceived);

        // Initialize epoch variables on the first deposit.
        if (epochTotalSupply == 0) {
            epochBaseline = totalMON();
            epochTotalSupply = totalSupply();
        }
        
        return shares;
    }
    
    // --- Epoch Update Function ---
    
    /**
     * @dev Update the epoch by computing and minting additional gMON tokens based on accrued rewards.
     * The additional gMON tokens for a user are computed as:
     *
     *    deltaG = epochTotalSupply * r_u^{MON} / epochBaseline
     *
     * where r_u^{MON} = rewardsMON * (w_u * d_u^{MON}) / (sum over all users of (w_u * d_u^{MON})),
     * and d_u^{MON} is approximated as:
     *
     *    d_u^{MON} = (userBalance * epochBaseline) / epochTotalSupply.
     *
     * This mechanism rewards users that were in the vault at the start of the epoch.
     */
    function updateEpoch() external onlyOwner nonReentrant {
        // 1. Get the current vault MON value (includes accrued rewards).
        uint256 newVaultMON = totalMON();
        
        // Since withdrawals update the epoch baseline, we should always have rewards here
        // unless there were no staking rewards during the epoch
        require(newVaultMON > epochBaseline, "No rewards available for this epoch");

        // 2. Calculate total rewards in MON generated during the epoch.
        uint256 rewardsMON = newVaultMON - epochBaseline; // R^{MON}

        // 3. Compute denominator: sum over all users of (userWeight * depositedMON)
        // where depositedMON is approximated as (userBalance * epochBaseline) / epochTotalSupply.
        uint256 denominator = 0;
        for (uint256 i = 0; i < users.length; i++) {
            address user = users[i];
            uint256 userBalance = balanceOf(user);
            
            // Skip users with zero balance
            if (userBalance == 0) continue;
            
            uint256 depositedMON = (userBalance * epochBaseline) / epochTotalSupply;
            denominator += userWeights[user] * depositedMON;
        }
        require(denominator > 0, "No eligible deposits for rewards");

        // 4. For each user, compute and mint the additional gMON tokens.
        for (uint256 i = 0; i < users.length; i++) {
            address user = users[i];
            uint256 userBalance = balanceOf(user);
            
            // Skip users with zero balance
            if (userBalance == 0) continue;
            
            uint256 depositedMON = (userBalance * epochBaseline) / epochTotalSupply;
            uint256 weightedDeposit = userWeights[user] * depositedMON;
            uint256 userRewardMON = (rewardsMON * weightedDeposit) / denominator;
            uint256 deltaG = (epochTotalSupply * userRewardMON) / epochBaseline;
            if (deltaG > 0) {
                _mint(user, deltaG);
            }
        }
        
        // 5. Update epoch variables for the next epoch.
        epochBaseline = totalMON();
        epochTotalSupply = totalSupply();
        
        emit EpochUpdated(epochBaseline, epochTotalSupply);
    }
    
    // --- Withdraw Function ---
    
    /**
     * @dev Withdraw native MON from the vault.
     * @param shares The amount of gMON shares to burn.
     * @param receiver The address that will receive the MON tokens.
     * @param owner The address that owns the gMON shares.
     * @return monAmount The amount of MON assets withdrawn.
     */
    function withdrawNative(
        uint256 shares,
        address receiver,
        address owner
    ) external nonReentrant returns (uint256 monAmount) {
        require(shares > 0, "Cannot withdraw 0 shares");
        
        // Calculate the amount of shMON corresponding to the shares
        uint256 _totalSupply = totalSupply();
        uint256 totalShMON = totalshMON();
        require(_totalSupply > 0, "Vault is empty");
        uint256 shMONAmount = (shares * totalShMON) / _totalSupply;
        require(shMONAmount > 0, "Insufficient assets");

        // If msg.sender is not the owner, enforce allowance spending.
        if (msg.sender != owner) {
            uint256 allowed = allowance(owner, msg.sender);
            if (allowed != type(uint256).max) {
                _spendAllowance(owner, msg.sender, shares);
            }
        }

        // Burn the gMON shares from the owner's balance.
        _burn(owner, shares);

        // Withdraw MON directly using the calculated shMON amount
        monAmount = stakedMON.withdraw(
            stakedMON.convertToAssets(shMONAmount), // Convert shMON to MON for the withdraw function
            address(this),
            address(this)
        );

        emit Unstaked(owner, monAmount);

        // Transfer the withdrawn MON to the receiver.
        (bool success, ) = payable(receiver).call{value: monAmount}("");
        require(success, "Native token transfer failed");
        
        // Remove user from active users list if they have no more shares
        if (balanceOf(owner) == 0 && userExists[owner]) {
            removeUser(owner);
        }

        // Update epoch baseline to reflect the withdrawal
        // This ensures that the next updateEpoch() call will correctly calculate rewards
        // based on the new vault value after the withdrawal
        if (epochBaseline > 0) {
            // Calculate the proportion of the vault that was withdrawn
            uint256 withdrawalProportion = (shares * 1e18) / (_totalSupply + shares);
            
            // Reduce the epoch baseline proportionally
            // We use the same proportion as the shares withdrawn to ensure consistency
            uint256 baselineReduction = (epochBaseline * withdrawalProportion) / 1e18;
            
            // Store the old baseline for the event
            uint256 oldBaseline = epochBaseline;
            
            // Update the epoch baseline
            epochBaseline = epochBaseline - baselineReduction;
            
            // Also update the epoch total supply to match the new total supply
            epochTotalSupply = totalSupply();
            
            // Emit an event to track the baseline update
            emit EpochBaselineUpdated(oldBaseline, epochBaseline, epochTotalSupply);
        }

        return monAmount;
    }
    
    /**
     * @dev Remove a user from the active users list.
     * @param user The address of the user to remove.
     */
    function removeUser(address user) internal {
        if (!userExists[user]) return;
        
        // Find the user in the array
        for (uint256 i = 0; i < users.length; i++) {
            if (users[i] == user) {
                // Replace with the last user and pop
                users[i] = users[users.length - 1];
                users.pop();
                // Also delete the user's weight to clean up storage
                delete userWeights[user];
                userExists[user] = false;
                break;
            }
        }
    }
    
    // --- Preview Functions (ERC4626 Style) ---
    
    /**
     * @dev Returns the number of gMON shares that would be minted for a given deposit of MON assets.
     * @param assets The amount of MON assets to deposit.
     * @return shares The number of gMON shares minted.
     */
    function previewDeposit(uint256 assets) public view returns (uint256 shares) {
        uint256 _totalMON = totalMON();
        uint256 _totalSupply = totalSupply();
        if (_totalSupply == 0 || _totalMON == 0) {
            shares = assets;
        } else {
            shares = (assets * _totalSupply) / _totalMON;
        }
    }
    
    /**
     * @dev Returns the amount of MON assets required to mint a given number of gMON shares.
     * @param shares The number of gMON shares to mint.
     * @return assets The amount of MON assets required.
     */
    function previewMint(uint256 shares) public view returns (uint256 assets) {
        uint256 _totalSupply = totalSupply();
        uint256 _totalMON = totalMON();
        if (_totalSupply == 0 || _totalMON == 0) {
            assets = shares;
        } else {
            assets = (shares * _totalMON) / _totalSupply;
        }
    }
    
    /**
     * @dev Returns the number of gMON shares that would be burned for a given withdrawal of MON assets.
     * @param assets The amount of MON assets to withdraw.
     * @return shares The corresponding amount of gMON shares.
     */
    function previewWithdraw(uint256 assets) public view returns (uint256 shares) {
        uint256 _totalMON = totalMON();
        uint256 _totalSupply = totalSupply();
        require(_totalMON > 0 && _totalSupply > 0, "Vault is empty");
        shares = (assets * _totalSupply) / _totalMON;
    }
    
    /**
     * @dev Returns the amount of MON assets that would be received for redeeming a given number of gMON shares.
     * @param shares The number of gMON shares to redeem.
     * @return assets The amount of MON assets that will be received.
     */
    function previewRedeem(uint256 shares) public view returns (uint256 assets) {
        uint256 _totalSupply = totalSupply();
        uint256 _totalMON = totalMON();
        require(_totalSupply > 0, "Vault is empty");
        assets = (shares * _totalMON) / _totalSupply;
    }
    
    /**
     * @dev Receive function to accept ETH transfers.
     */
    receive() external payable {}
}
