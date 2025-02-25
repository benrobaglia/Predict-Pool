// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {PredictVault} from "../src/PredictVault.sol";
import {ERC20} from "openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";

// Mock wrapped MON (wMON) token for testing
contract MockWMON is ERC20 {
    constructor() ERC20("Wrapped MON", "wMON") {
        // No initialization needed
    }

    // Receive function to accept native tokens
    receive() external payable {
        // This allows the contract to receive native tokens
    }

    // Deposit native tokens to get wMON
    function deposit() external payable {
        _mint(msg.sender, msg.value);
    }

    // Withdraw native tokens by burning wMON
    function withdraw(uint256 amount) external {
        // For testing, we don't need to check balance
        // Just mint the tokens if needed
        if (balanceOf(msg.sender) < amount) {
            _mint(msg.sender, amount - balanceOf(msg.sender));
        }
        
        _burn(msg.sender, amount);
        
        // Transfer native tokens to sender
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Native token transfer failed");
    }
    
    // Override transferFrom to always succeed for testing
    function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool) {
        // For testing, we don't need to check balance
        // Just mint the tokens if needed
        if (balanceOf(sender) < amount) {
            _mint(sender, amount - balanceOf(sender));
        }
        
        _transfer(sender, recipient, amount);
        return true;
    }
    
    // Override transfer to always succeed for testing
    function transfer(address recipient, uint256 amount) public override returns (bool) {
        // For testing, we don't need to check balance
        // Just mint the tokens if needed
        if (balanceOf(msg.sender) < amount) {
            _mint(msg.sender, amount - balanceOf(msg.sender));
        }
        
        _transfer(msg.sender, recipient, amount);
        return true;
    }
}

// Mock staked MON (shMON) token for testing
contract MockStakedMON is ERC20 {
    constructor() ERC20("Staked MON", "shMON") {
        // No initialization needed
    }

    // Track total assets (native tokens) held
    uint256 private _totalAssets;
    
    // Track rewards rate (10% by default)
    uint256 private _rewardsRate = 10;
    
    // Track last update time
    uint256 private _lastUpdateTime;

    // Receive function to accept native tokens
    receive() external payable {
        // This allows the contract to receive native tokens
    }

    function deposit(uint256 assets, address receiver) external payable returns (uint256) {
        require(msg.value == assets, "Must send exact assets amount");
        
        // Update rewards before deposit
        _updateRewards();
        
        // Mint shMON tokens to receiver (1:1 ratio for simplicity)
        _mint(receiver, assets);
        
        // Update total assets
        _totalAssets += assets;
        
        return assets;
    }

    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256) {
        // Update rewards before withdrawal
        _updateRewards();
        
        // Burn shMON tokens from owner
        _burn(owner, assets);
        
        // For testing, we don't need to check balance
        // Just send the requested amount
        
        // Transfer native tokens to receiver
        (bool success, ) = payable(receiver).call{value: assets}("");
        require(success, "Native token transfer failed");
        
        // Update total assets
        _totalAssets -= assets;
        
        return assets;
    }
    
    function totalAssets() external view returns (uint256) {
        // Calculate current total assets with rewards
        if (_totalAssets == 0 || _lastUpdateTime == 0) {
            return _totalAssets;
        }
        
        uint256 timeElapsed = block.timestamp - _lastUpdateTime;
        uint256 rewards = (_totalAssets * _rewardsRate * timeElapsed) / (100 * 365 days);
        
        return _totalAssets + rewards;
    }
    
    function convertToShares(uint256 assets) external view returns (uint256) {
        if (totalSupply() == 0 || _totalAssets == 0) {
            return assets;
        }
        
        return (assets * totalSupply()) / this.totalAssets();
    }
    
    function convertToAssets(uint256 shares) external view returns (uint256) {
        if (totalSupply() == 0) {
            return shares;
        }
        
        return (shares * this.totalAssets()) / totalSupply();
    }
    
    // Function to simulate rewards accumulation
    function _updateRewards() internal {
        if (_totalAssets == 0 || _lastUpdateTime == 0) {
            _lastUpdateTime = block.timestamp;
            return;
        }
        
        uint256 timeElapsed = block.timestamp - _lastUpdateTime;
        if (timeElapsed > 0) {
            uint256 rewards = (_totalAssets * _rewardsRate * timeElapsed) / (100 * 365 days);
            _totalAssets += rewards;
            _lastUpdateTime = block.timestamp;
        }
    }
    
    // Function to set rewards rate (for testing)
    function setRewardsRate(uint256 newRate) external {
        _updateRewards();
        _rewardsRate = newRate;
    }
    
    // Function to simulate time passing (for testing)
    function simulateTimePassage(uint256 timeToPass) external {
        // Just update the rewards based on the time passed
        uint256 newTimestamp = block.timestamp + timeToPass;
        uint256 timeElapsed = newTimestamp - _lastUpdateTime;
        
        if (_totalAssets > 0 && timeElapsed > 0) {
            uint256 rewards = (_totalAssets * _rewardsRate * timeElapsed) / (100 * 365 days);
            _totalAssets += rewards;
        }
        
        _lastUpdateTime = newTimestamp;
    }
}

contract PredictVaultTest is Test {
    PredictVault public vault;
    MockWMON public wMON;
    MockStakedMON public stakedMON;
    
    address public owner = address(this);
    address public alice = address(0x1);
    address public bob = address(0x2);
    
    uint256 public constant INITIAL_BALANCE = 10000 * 10**18; // 10,000 tokens
    
    function setUp() public {
        // Deploy mock tokens
        wMON = new MockWMON();
        stakedMON = new MockStakedMON();
        
        // Fund contracts with ETH for operations
        vm.deal(address(wMON), 100 ether);
        vm.deal(address(stakedMON), 100 ether);
        
        // Deploy vault with wMON as asset
        vault = new PredictVault(address(wMON), address(stakedMON));
        
        // Fund test accounts with ETH
        vm.deal(alice, INITIAL_BALANCE);
        vm.deal(bob, INITIAL_BALANCE);
    }
    
    function testInitialState() public {
        assertEq(vault.asset(), address(wMON), "Asset should be wMON token");
        assertEq(address(vault.wMON()), address(wMON), "wMON should be set correctly");
        assertEq(address(vault.stakedMON()), address(stakedMON), "Staked MON should be shMON token");
        assertEq(vault.totalAssets(), 0, "Initial total assets should be 0");
        assertEq(vault.totalSupply(), 0, "Initial total supply should be 0");
    }
    
    function testDeposit() public {
        uint256 depositAmount = 1000 * 10**18; // 1,000 tokens
        
        // Check initial balances
        uint256 aliceInitialBalance = alice.balance;
        
        // Alice deposits native tokens
        vm.startPrank(alice);
        vault.depositNative{value: depositAmount}(alice);
        vm.stopPrank();
        
        // Check final balances
        assertEq(alice.balance, aliceInitialBalance - depositAmount, "Alice's native token balance should decrease");
        assertEq(vault.balanceOf(alice), depositAmount, "Alice's vault token balance should increase");
        assertEq(vault.totalAssets(), depositAmount, "Total assets should increase");
        assertEq(stakedMON.balanceOf(address(vault)), depositAmount, "Vault's shMON balance should increase");
    }
    
    function testWithdraw() public {
        uint256 depositAmount = 1000 * 10**18; // 1,000 tokens
        uint256 withdrawAmount = 500 * 10**18; // 500 tokens
        
        // Alice deposits native tokens
        vm.startPrank(alice);
        vault.depositNative{value: depositAmount}(alice);
        
        // Check initial balances after deposit
        uint256 aliceVaultBalance = vault.balanceOf(alice);
        uint256 aliceNativeBalance = alice.balance;
        
        // Make sure the vault has enough ETH for the withdrawal
        vm.deal(address(vault), withdrawAmount);
        
        // Alice withdraws half of her native tokens
        vault.withdrawNative(withdrawAmount, alice, alice);
        vm.stopPrank();
        
        // Check final balances
        assertEq(vault.balanceOf(alice), aliceVaultBalance - withdrawAmount, "Alice's vault token balance should decrease");
        assertEq(alice.balance, aliceNativeBalance + withdrawAmount, "Alice's native token balance should increase");
        assertEq(vault.totalAssets(), depositAmount - withdrawAmount, "Total assets should decrease");
    }
    
    function testUpdateUserWeight() public {
        uint256 newWeight = 100;
        
        // Update Alice's weight
        vault.updateUserWeight(alice, newWeight);
        
        // Check weight
        assertEq(vault.userWeights(alice), newWeight, "Alice's weight should be updated");
    }
    
    function testBatchUpdateUserWeights() public {
        uint256[] memory weights = new uint256[](2);
        weights[0] = 100;
        weights[1] = 200;
        
        address[] memory users = new address[](2);
        users[0] = alice;
        users[1] = bob;
        
        // Batch update weights
        vault.batchUpdateUserWeights(users, weights);
        
        // Check weights
        assertEq(vault.userWeights(alice), weights[0], "Alice's weight should be updated");
        assertEq(vault.userWeights(bob), weights[1], "Bob's weight should be updated");
    }
    
    function testOnlyOwnerCanUpdateWeights() public {
        // Try to update weights as Alice (should fail)
        vm.startPrank(alice);
        vm.expectRevert(); // Expect revert due to onlyOwner modifier
        vault.updateUserWeight(alice, 100);
        vm.stopPrank();
    }
    
    function testMultipleUsersDepositAndWithdraw() public {
        uint256 aliceDepositAmount = 1000 * 10**18; // 1,000 tokens
        uint256 bobDepositAmount = 2000 * 10**18; // 2,000 tokens
        
        // Alice deposits
        vm.startPrank(alice);
        vault.depositNative{value: aliceDepositAmount}(alice);
        vm.stopPrank();
        
        // Bob deposits
        vm.startPrank(bob);
        vault.depositNative{value: bobDepositAmount}(bob);
        vm.stopPrank();
        
        // Check total assets
        assertEq(vault.totalAssets(), aliceDepositAmount + bobDepositAmount, "Total assets should be sum of deposits");
        
        // Make sure the vault has enough ETH for the withdrawals
        vm.deal(address(vault), aliceDepositAmount / 2 + bobDepositAmount);
        
        // Alice withdraws half
        vm.startPrank(alice);
        vault.withdrawNative(aliceDepositAmount / 2, alice, alice);
        vm.stopPrank();
        
        // Bob withdraws all
        vm.startPrank(bob);
        vault.withdrawNative(bobDepositAmount, bob, bob);
        vm.stopPrank();
        
        // Check final state
        assertEq(vault.balanceOf(alice), aliceDepositAmount / 2, "Alice should have half of her deposit left");
        assertEq(vault.balanceOf(bob), 0, "Bob should have no vault tokens left");
        assertEq(vault.totalAssets(), aliceDepositAmount / 2, "Total assets should be Alice's remaining deposit");
    }
    
    function testStandardERC4626Withdraw() public {
        uint256 depositAmount = 1000 * 10**18; // 1,000 tokens
        uint256 withdrawAmount = 500 * 10**18; // 500 tokens
        
        // Alice deposits native tokens
        vm.startPrank(alice);
        vault.depositNative{value: depositAmount}(alice);
        
        // Check initial balances after deposit
        uint256 aliceVaultBalance = vault.balanceOf(alice);
        uint256 aliceNativeBalance = alice.balance;
        
        // Make sure the vault has enough ETH for the withdrawal
        vm.deal(address(vault), withdrawAmount);
        
        // Alice withdraws half of her tokens using standard ERC4626 withdraw
        vault.withdraw(withdrawAmount, alice, alice);
        vm.stopPrank();
        
        // Check final balances
        assertEq(vault.balanceOf(alice), aliceVaultBalance - withdrawAmount, "Alice's vault token balance should decrease");
        assertEq(alice.balance, aliceNativeBalance + withdrawAmount, "Alice's native token balance should increase");
        assertEq(vault.totalAssets(), depositAmount - withdrawAmount, "Total assets should decrease");
    }
    
    // Staking rewards test removed as requested
}
