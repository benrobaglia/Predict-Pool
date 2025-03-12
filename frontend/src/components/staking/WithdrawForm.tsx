import { useState } from "react";
import { useAccount, useWriteContract } from "wagmi";
import { parseEther, formatEther } from "viem";
import { LoadingSpinner } from "../LoadingSpinner";
import { STAKING_CONTRACT } from "@/config/constants";
import predictPoolAbi from "@/utils/predictPoolAbi.json";

interface WithdrawFormProps {
  stakedBalance: bigint | undefined;
}

export const WithdrawForm = ({ stakedBalance }: WithdrawFormProps) => {
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const { address } = useAccount();

  const {
    writeContract: withdraw,
    isPending: isWithdrawLoading,
    isSuccess: isWithdrawSuccess,
  } = useWriteContract();

  const handleWithdraw = () => {
    if (!withdrawAmount || !withdraw || !stakedBalance) return;
    const shares = parseEther(withdrawAmount);
    if (shares > stakedBalance) return;

    withdraw({
      address: STAKING_CONTRACT,
      abi: predictPoolAbi,
      functionName: "withdrawNative",
      args: [shares, address, address],
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === "" || /^\d*\.?\d*$/.test(value)) {
      setWithdrawAmount(value);
    }
  };

  const isAmountValid = () => {
    if (!withdrawAmount || !stakedBalance) return false;
    try {
      return (
        parseFloat(withdrawAmount) <= parseFloat(formatEther(stakedBalance))
      );
    } catch {
      return false;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">
          Withdraw Your Staked MON
        </h2>

        <div className="space-y-2">
          <label
            htmlFor="withdrawAmount"
            className="block text-sm font-medium text-gray-300"
          >
            Amount to Withdraw
          </label>
          <div className="relative rounded-xl shadow-sm">
            <input
              type="text"
              id="withdrawAmount"
              value={withdrawAmount}
              onChange={handleInputChange}
              className="block w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="0.0"
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-4">
              <span className="text-gray-400">gMON</span>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={handleWithdraw}
        disabled={!isAmountValid() || isWithdrawLoading}
        className={`w-full py-3 px-4 rounded-xl text-white font-medium transition-all duration-200
          ${
            isAmountValid() && !isWithdrawLoading
              ? "bg-purple-600 hover:bg-purple-700 shadow-lg shadow-purple-500/20"
              : "bg-gray-700 cursor-not-allowed"
          }`}
      >
        {isWithdrawLoading ? (
          <div className="flex items-center justify-center space-x-2">
            <LoadingSpinner />
            <span>Withdrawing...</span>
          </div>
        ) : (
          "Withdraw MON"
        )}
      </button>

      {isWithdrawSuccess && (
        <div className="p-4 bg-green-900/20 border border-green-800 rounded-xl">
          <p className="text-green-400 text-sm">
            Successfully withdrew {withdrawAmount} gMON!
          </p>
        </div>
      )}
    </div>
  );
};
