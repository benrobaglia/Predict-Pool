// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {ERC4626} from "openzeppelin-contracts/contracts/token/ERC20/extensions/ERC4626.sol";
import {ERC20} from "openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "openzeppelin-contracts/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IStakedMON
 * @dev Interface for the shMON (staked MON) token contract
 */
interface IStakedMON {
    function deposit(uint256 assets, address receiver) external payable returns (uint256);
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256);
    function totalAssets() external view returns (uint256);
    function convertToShares(uint256 assets) external view returns (uint256);
    function convertToAssets(uint256 shares) external view returns (uint256);
}

/**
 * @title IWMON
 * @dev Interface for the wMON (wrapped MON) token contract
 */
interface IWMON is IERC20 {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
}

/**
 * @title PredictVault
 * @dev ERC4626 vault that accepts MON, wraps to wMON, then stakes to shMON.
 * Unstakes shMON back to MON for user withdrawals.
 */
contract PredictVault is ERC4626, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // The shMON token contract
    IStakedMON public immutable stakedMON;
    
    // The wMON token contract
    IWMON public immutable wMON;
    
    // Mapping to store user weights (updated by off-chain algorithm)
    mapping(address => uint256) public userWeights;
    
    // Events
    event UserWeightUpdated(address indexed user, uint256 newWeight);
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event Wrapped(uint256 amount);
    event Unwrapped(uint256 amount);
    
    /**
     * @dev Constructor
     * @param _wMON The wMON token address
     * @param _stakedMON The shMON token address
     */
    constructor(
        address _wMON,
        address _stakedMON
    ) ERC4626(IERC20(_wMON)) ERC20("Predict Vault MON", "pvMON") Ownable(msg.sender) {
        require(_wMON != address(0), "wMON address cannot be zero");
        require(_stakedMON != address(0), "stakedMON address cannot be zero");
        
        wMON = IWMON(_wMON);
        stakedMON = IStakedMON(_stakedMON);
        
        // Approve the stakedMON contract to spend wMON tokens
        IERC20(_wMON).approve(_stakedMON, type(uint256).max);
    }
    
    /**
     * @dev Updates a user's weight
     * @param user The user address
     * @param weight The new weight
     */
    function updateUserWeight(address user, uint256 weight) external onlyOwner {
        userWeights[user] = weight;
        emit UserWeightUpdated(user, weight);
    }
    
    /**
     * @dev Batch update user weights
     * @param users Array of user addresses
     * @param weights Array of weights
     */
    function batchUpdateUserWeights(
        address[] calldata users,
        uint256[] calldata weights
    ) external onlyOwner {
        require(users.length == weights.length, "Array lengths must match");
        
        for (uint256 i = 0; i < users.length; i++) {
            userWeights[users[i]] = weights[i];
            emit UserWeightUpdated(users[i], weights[i]);
        }
    }
    
    /**
     * @dev Returns the total assets managed by the vault
     * @return The total assets
     */
    function totalAssets() public view override returns (uint256) {
        return stakedMON.convertToAssets(totalSupply());
    }
    
    /**
     * @dev Receives native MON and automatically wraps it to wMON,
     * except when called from the withdraw function of wMON.
     */
    receive() external payable {
        // Only wrap if not called from wMON.withdraw
        if (msg.value > 0 && msg.sender != address(wMON)) {
            wMON.deposit{value: msg.value}();
            emit Wrapped(msg.value);
        }
    }
    
    /**
     * @dev Deposit native MON, wrap it to wMON, and stake in shMON.
     * @param receiver The address to receive the shares
     * @return shares The amount of shares minted
     */
    function depositNative(address receiver) external payable returns (uint256 shares) {
        uint256 assets = msg.value;
        require(assets > 0, "Cannot deposit 0 assets");

        // Wrap native MON to wMON
        wMON.deposit{value: assets}();
        emit Wrapped(assets);

        // Approve staking contract to use wMON
        IERC20(address(wMON)).approve(address(stakedMON), assets);

        // Calculate shares based on wrapped tokens
        shares = previewDeposit(assets);

        // Deposit into vault and stake
        _deposit(msg.sender, receiver, assets, shares);

        return shares;
    }
    
    /**
     * @dev Internal deposit logic
     */
    function _deposit(
        address caller,
        address receiver,
        uint256 assets,
        uint256 shares
    ) internal override nonReentrant {
        // Call standard ERC4626 deposit flow
        super._deposit(caller, receiver, assets, shares);

        // Unwrap wMON back to MON
        wMON.withdraw(assets);
        emit Unwrapped(assets);

        // Stake MON for shMON
        stakedMON.deposit{value: assets}(assets, address(this));
        emit Staked(receiver, assets);
    }
    
    /**
     * @dev Withdraw native MON from the vault
     * @param assets The amount of assets to withdraw
     * @param receiver The address to receive the assets
     * @param owner The address that owns the shares
     * @return shares The amount of shares burned
     */
    function withdrawNative(
        uint256 assets,
        address receiver,
        address owner
    ) external nonReentrant returns (uint256 shares) {
        shares = previewWithdraw(assets);

        if (msg.sender != owner) {
            uint256 allowed = allowance(owner, msg.sender);
            if (allowed != type(uint256).max) {
                _spendAllowance(owner, msg.sender, shares);
            }
        }

        // Burn shares
        _burn(owner, shares);

        // Unstake shMON to get MON
        stakedMON.withdraw(assets, address(this), address(this));
        emit Unstaked(owner, assets);

        // Transfer MON directly to receiver
        (bool success, ) = payable(receiver).call{value: assets}("");
        require(success, "Native token transfer failed");

        return shares;
    }
    
    /**
     * @dev Internal withdraw logic
     */
    function _withdraw(
        address caller,
        address receiver,
        address owner,
        uint256 assets,
        uint256 shares
    ) internal override nonReentrant {
        _burn(owner, shares);

        // Unstake shMON to MON
        stakedMON.withdraw(assets, address(this), address(this));
        emit Unstaked(owner, assets);

        // Transfer MON to receiver
        (bool success, ) = payable(receiver).call{value: assets}("");
        require(success, "Native token transfer failed");
    }
}
