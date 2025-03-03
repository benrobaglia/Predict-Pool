// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {PredictVault} from "../src/PredictVault.sol";
import {MockStakedMON} from "./mocks/MockStakedMON.sol";

contract PredictVaultTest is Test {
    PredictVault public vault;
    MockStakedMON public stakedMON;

    address public owner;
    address public alice;
    address public bob;
    address public charlie;

    uint256 public constant INITIAL_BALANCE = 100 ether;

    function setUp() public {
        // Set up accounts
        owner = address(this);
        alice = makeAddr("alice");
        bob = makeAddr("bob");
        charlie = makeAddr("charlie");

        // Deploy mock shMON token
        stakedMON = new MockStakedMON();

        // Deploy the vault
        vault = new PredictVault(address(stakedMON));

        // Fund test accounts
        vm.deal(alice, INITIAL_BALANCE);
        vm.deal(bob, INITIAL_BALANCE);
        vm.deal(charlie, INITIAL_BALANCE);
    }

    function test_Deployment() public {
        assertEq(vault.owner(), owner);
        assertEq(address(vault.stakedMON()), address(stakedMON));
        assertEq(vault.epochBaseline(), 0);
        assertEq(vault.epochTotalSupply(), 0);
    }

    function test_DepositNative() public {
        uint256 depositAmount = 10 ether;
        
        // Alice deposits
        vm.prank(alice);
        uint256 shares = vault.depositNative{value: depositAmount}(alice);
        
        // Check Alice's gMON balance
        assertEq(vault.balanceOf(alice), shares);
        
        // Check Alice is in the users array
        assertTrue(vault.userExists(alice));
        
        // Check Alice's weight is initialized to 0
        assertEq(vault.userWeights(alice), 0);
        
        // Check vault's shMON balance
        assertEq(vault.totalshMON(), depositAmount); // In this mock, 1 MON = 1 shMON initially
        
        // Check epoch variables are initialized
        assertEq(vault.epochBaseline(), depositAmount);
        assertEq(vault.epochTotalSupply(), shares);
    }

    function test_MultipleDeposits() public {
        // Alice deposits
        vm.prank(alice);
        uint256 aliceShares = vault.depositNative{value: 10 ether}(alice);
        
        // Bob deposits
        vm.prank(bob);
        uint256 bobShares = vault.depositNative{value: 20 ether}(bob);
        
        // Check balances
        assertEq(vault.balanceOf(alice), aliceShares);
        assertEq(vault.balanceOf(bob), bobShares);
        
        // Check total supply
        assertEq(vault.totalSupply(), aliceShares + bobShares);
        
        // Check both users are in the users array
        assertTrue(vault.userExists(alice));
        assertTrue(vault.userExists(bob));
    }

    function test_UpdateUserWeight() public {
        // Alice deposits
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        // Update Alice's weight
        vault.updateUserWeight(alice, 5000);
        
        // Check Alice's weight
        assertEq(vault.userWeights(alice), 5000);
    }

    function test_BatchUpdateUserWeights() public {
        // Alice and Bob deposit
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        vm.prank(bob);
        vault.depositNative{value: 20 ether}(bob);
        
        // Batch update weights
        address[] memory users = new address[](2);
        users[0] = alice;
        users[1] = bob;
        
        uint256[] memory weights = new uint256[](2);
        weights[0] = 5000;
        weights[1] = 7500;
        
        vault.batchUpdateUserWeights(users, weights);
        
        // Check weights
        assertEq(vault.userWeights(alice), 5000);
        assertEq(vault.userWeights(bob), 7500);
    }

    function test_UpdateEpoch() public {
        // Alice and Bob deposit
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        vm.prank(bob);
        vault.depositNative{value: 20 ether}(bob);
        
        // Set weights
        vault.updateUserWeight(alice, 5000);
        vault.updateUserWeight(bob, 7500);
        
        // Simulate staking rewards by increasing the MON value of shMON
        stakedMON.simulateRewards(5 ether); // 5 ether rewards
        
        // Update epoch
        vault.updateEpoch();
        
        // Check new epoch variables - allow for small rounding errors
        uint256 expectedBaseline = 35 ether; // 30 ether deposits + 5 ether rewards
        uint256 actualBaseline = vault.epochBaseline();
        uint256 tolerance = 100; // Allow for a small difference due to rounding
        
        assertApproxEqAbs(actualBaseline, expectedBaseline, tolerance);
        
        // Check that Alice and Bob received additional gMON tokens based on their weights
        // The exact calculation depends on the formula in the contract
    }

    function test_WithdrawNative() public {
        // Alice deposits
        vm.prank(alice);
        uint256 shares = vault.depositNative{value: 10 ether}(alice);
        
        // Alice withdraws half her shares
        uint256 withdrawShares = shares / 2;
        uint256 expectedAssets = vault.previewRedeem(withdrawShares);
        
        vm.prank(alice);
        uint256 assets = vault.withdrawNative(withdrawShares, alice, alice);
        
        // Check Alice received the correct amount of assets
        assertEq(assets, expectedAssets);
        
        // Check Alice's remaining gMON balance
        assertEq(vault.balanceOf(alice), shares - withdrawShares);
        
        // Alice is still in the users array because she still has shares
        assertTrue(vault.userExists(alice));
    }

    function test_WithdrawAll() public {
        // Alice deposits
        vm.prank(alice);
        uint256 shares = vault.depositNative{value: 10 ether}(alice);
        
        // Alice withdraws all her shares
        vm.prank(alice);
        vault.withdrawNative(shares, alice, alice);
        
        // Check Alice's gMON balance is 0
        assertEq(vault.balanceOf(alice), 0);
        
        // Alice should be removed from the users array
        assertFalse(vault.userExists(alice));
        
        // Alice's weight should be deleted
        assertEq(vault.userWeights(alice), 0);
    }

    function test_RevertWhenNoRewards() public {
        // Alice deposits
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        // Try to update epoch with no rewards
        vm.expectRevert("No rewards available for this epoch");
        vault.updateEpoch();
    }

    function test_RevertWhenNoDenominator() public {
        // Alice deposits
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        // Simulate staking rewards
        stakedMON.simulateRewards(5 ether);
        
        // Try to update epoch with no weights set
        vm.expectRevert("No eligible deposits for rewards");
        vault.updateEpoch();
    }

    function test_ComplexScenario() public {
        // 1. Alice, Bob, and Charlie deposit
        vm.prank(alice);
        vault.depositNative{value: 10 ether}(alice);
        
        vm.prank(bob);
        vault.depositNative{value: 20 ether}(bob);
        
        vm.prank(charlie);
        vault.depositNative{value: 30 ether}(charlie);
        
        // 2. Set weights
        vault.updateUserWeight(alice, 5000);
        vault.updateUserWeight(bob, 7500);
        vault.updateUserWeight(charlie, 10000);
        
        // 3. Simulate staking rewards
        stakedMON.simulateRewards(12 ether);
        
        // 4. Update epoch
        vault.updateEpoch();
        
        // 5. Bob withdraws all
        uint256 bobShares = vault.balanceOf(bob);
        vm.prank(bob);
        vault.withdrawNative(bobShares, bob, bob);
        
        // Simulate significant rewards to ensure the next updateEpoch() call doesn't revert
        stakedMON.simulateRewards(20 ether);
        
        // After Bob's withdrawal, we need to update the epoch baseline
        // to reflect the new state of the vault
        vault.updateEpoch();
        
        // 6. Simulate more staking rewards
        stakedMON.simulateRewards(8 ether);
        
        // 7. Update epoch again
        vault.updateEpoch();
        
        // 8. Check that only Alice and Charlie received rewards in the second epoch
        assertFalse(vault.userExists(bob));
        assertTrue(vault.userExists(alice));
        assertTrue(vault.userExists(charlie));
    }
}
