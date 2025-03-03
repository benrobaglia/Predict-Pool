// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {ERC20} from "openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";

/**
 * @title MockStakedMON
 * @dev Mock implementation of the shMON (staked MON) token for testing purposes.
 * This mock simulates the behavior of a staking token that accrues rewards over time.
 */
contract MockStakedMON is ERC20 {
    uint256 private _totalAssets;
    uint256 private _exchangeRate = 1e18; // 1:1 initially (1 MON = 1 shMON)

    constructor() ERC20("Staked MON", "shMON") {}

    /**
     * @dev Deposit MON and receive shMON in return.
     * @param assets Amount of MON to deposit.
     * @param receiver Address to receive the shMON tokens.
     * @return shares Amount of shMON tokens minted.
     */
    function deposit(uint256 assets, address receiver) external payable returns (uint256 shares) {
        require(msg.value == assets, "Must send exact amount");
        
        shares = convertToShares(assets);
        _mint(receiver, shares);
        _totalAssets += assets;
        
        return shares;
    }

    /**
     * @dev Withdraw MON by burning shMON.
     * @param assets Amount of MON to withdraw.
     * @param receiver Address to receive the MON tokens.
     * @param owner Address that owns the shMON tokens.
     * @return shares Amount of shMON tokens burned.
     */
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares) {
        shares = convertToShares(assets);
        
        _burn(owner, shares);
        _totalAssets -= assets;
        
        // Transfer MON to receiver
        (bool success, ) = payable(receiver).call{value: assets}("");
        require(success, "Transfer failed");
        
        return shares;
    }

    /**
     * @dev Returns the total amount of MON managed by the contract.
     * @return The total assets.
     */
    function totalAssets() external view returns (uint256) {
        return _totalAssets;
    }

    /**
     * @dev Converts a given amount of MON assets to shMON shares.
     * @param assets Amount of MON to convert.
     * @return shares Equivalent amount of shMON shares.
     */
    function convertToShares(uint256 assets) public view returns (uint256 shares) {
        return (assets * 1e18) / _exchangeRate;
    }

    /**
     * @dev Converts a given amount of shMON shares to MON assets.
     * @param shares Amount of shMON to convert.
     * @return assets Equivalent amount of MON assets.
     */
    function convertToAssets(uint256 shares) public view returns (uint256 assets) {
        return (shares * _exchangeRate) / 1e18;
    }

    /**
     * @dev Simulates staking rewards by increasing the exchange rate.
     * This function is for testing purposes only.
     * @param rewardAmount Amount of MON rewards to simulate.
     */
    function simulateRewards(uint256 rewardAmount) external {
        require(_totalAssets > 0, "No assets to reward");
        
        // Increase total assets by the reward amount
        _totalAssets += rewardAmount;
        
        // Update exchange rate
        // New exchange rate = (total assets * 1e18) / total supply
        _exchangeRate = (_totalAssets * 1e18) / totalSupply();
    }

    /**
     * @dev Returns the current exchange rate between MON and shMON.
     * @return The exchange rate (1e18 precision).
     */
    function getExchangeRate() external view returns (uint256) {
        return _exchangeRate;
    }

    /**
     * @dev Receive function to accept ETH.
     */
    receive() external payable {}
}
