// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {PredictVault} from "../src/PredictVault.sol";

/**
 * @title DeployPredictVault
 * @dev Script to deploy the PredictVault contract
 */
contract DeployPredictVault is Script {
    function run() external {
        // Get staked MON address from environment variable
        address stakedMon = vm.envOr("STAKED_MON_ADDRESS", address(0));
        require(stakedMon != address(0), "STAKED_MON_ADDRESS not set in .env");
        console2.log("Using stakedMON at:", stakedMon);
        
        // Start broadcasting transactions
        vm.startBroadcast();

        // Deploy the PredictVault contract
        PredictVault vault = new PredictVault(
            stakedMon
        );

        // Log the deployed contract address
        console2.log("PredictVault deployed at:", address(vault));

        // Stop broadcasting transactions
        vm.stopBroadcast();
    }
}

/**
 * @title UpgradePredictVault
 * @dev Script to upgrade the PredictVault contract (for future use)
 */
contract UpgradePredictVault is Script {
    function run() external {
        // Get vault address from environment variable
        address predictVault = vm.envOr("PREDICT_VAULT_ADDRESS", address(0));
        
        // Ensure address is set
        require(predictVault != address(0), "PREDICT_VAULT_ADDRESS not set in .env");
        
        // Start broadcasting transactions
        vm.startBroadcast();

        // Implement upgrade logic here
        // For example, if using a proxy pattern, you would deploy a new implementation
        // and update the proxy to point to the new implementation

        // Stop broadcasting transactions
        vm.stopBroadcast();
    }
}
