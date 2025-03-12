import { useState } from "react";
import { useAccount, useBalance, useWriteContract } from "wagmi";
import { parseEther } from "viem";
import { LoadingSpinner } from "../LoadingSpinner";
import { STAKING_CONTRACT } from "@/config/constants";
import predictPoolAbi from "@/utils/predictPoolAbi.json";
import { BalanceDisplay } from "@/components/staking/BalanceDisplay";

interface StakeFormProps {
  stakedBalance: bigint | undefined;
}

export const StakeForm = ({ stakedBalance }: StakeFormProps) => {
  const [stakeAmount, setStakeAmount] = useState("");
  const { address } = useAccount();

  // Get user's MON balance
  const { data: balance } = useBalance({
    address,
  });

  const {
    writeContract: stake,
    isPending: isLoading,
    isSuccess,
  } = useWriteContract();

  const handleStake = () => {
    if (!stakeAmount || !stake) return;
    stake({
      address: STAKING_CONTRACT,
      abi: predictPoolAbi,
      functionName: "depositNative",
      args: [address],
      value: stakeAmount ? parseEther(stakeAmount) : undefined,
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === "" || /^\d*\.?\d*$/.test(value)) {
      setStakeAmount(value);
    }
  };

  const isAmountValid = () => {
    if (!stakeAmount || !balance) return false;
    try {
      return parseFloat(stakeAmount) <= parseFloat(balance.formatted);
    } catch {
      return false;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">
          Stake Your MON to Predict
        </h2>

        <div className="space-y-2">
          <label
            htmlFor="stakeAmount"
            className="block text-sm font-medium text-gray-300"
          >
            Amount to Stake
          </label>
          <div className="relative rounded-xl shadow-sm">
            <input
              type="text"
              id="stakeAmount"
              value={stakeAmount}
              onChange={handleInputChange}
              className="block w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="0.0"
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-4">
              <span className="text-gray-400">MON</span>
            </div>
          </div>
          <BalanceDisplay
            balance={balance?.value}
            stakedBalance={stakedBalance}
          />
        </div>
      </div>

      <button
        onClick={handleStake}
        disabled={!isAmountValid() || isLoading}
        className={`w-full py-3 px-4 rounded-xl text-white font-medium transition-all duration-200
          ${
            isAmountValid() && !isLoading
              ? "bg-purple-600 hover:bg-purple-700 shadow-lg shadow-purple-500/20"
              : "bg-gray-700 cursor-not-allowed"
          }`}
      >
        {isLoading ? (
          <div className="flex items-center justify-center space-x-2">
            <LoadingSpinner size={5} />
            <span>Staking...</span>
          </div>
        ) : (
          "Stake MON"
        )}
      </button>

      {isSuccess && (
        <div className="p-4 bg-green-900/20 border border-green-800 rounded-xl">
          <p className="text-green-400 text-sm">
            Successfully staked {stakeAmount} MON!
          </p>
        </div>
      )}
    </div>
  );
};
