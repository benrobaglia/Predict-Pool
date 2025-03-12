import { UseBalanceReturnType } from "wagmi";
import { LoadingSpinner } from "../LoadingSpinner";
import { formatEther, GetBalanceReturnType } from "viem";

interface BalanceDisplayProps {
  balance: bigint | undefined;
  stakedBalance: bigint | undefined;
  isStakedBalanceLoading?: boolean;
}

export const BalanceDisplay = ({
  balance,
  stakedBalance,
  isStakedBalanceLoading,
}: BalanceDisplayProps) => {
  return (
    <div className="flex flex-col space-y-1 w-full">
      {balance ? (
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Wallet Balance:</span>
          <span className="text-gray-300">
            {balance ? formatEther(balance) : "0"} MON
          </span>
        </div>
      ) : null}
      {isStakedBalanceLoading ? (
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Staked Balance:</span>
          <LoadingSpinner />
        </div>
      ) : (
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Staked Balance:</span>
          <span className="text-gray-300">
            {stakedBalance ? formatEther(stakedBalance) : "0"} gMON
          </span>
        </div>
      )}
    </div>
  );
};
