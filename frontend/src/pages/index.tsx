import type { NextPage } from "next";
import Head from "next/head";
import { useAccount, useReadContract } from "wagmi";
import predictPoolAbi from "../utils/predictPoolAbi.json";
import { StakeForm } from "@/components/staking/StakeForm";
import { WithdrawForm } from "@/components/staking/WithdrawForm";
import { STAKING_CONTRACT } from "@/config/constants";
import { Layout } from "@/components/layout/Layout";

const Home: NextPage = () => {
  const { address } = useAccount();

  const { data: stakedBalance, isLoading: isStakedBalanceLoading } =
    useReadContract({
      address: STAKING_CONTRACT,
      abi: predictPoolAbi,
      functionName: "balanceOf",
      args: [address],
      query: {
        enabled: !!address,
      },
    });

  return (
    <Layout>
      <Head>
        <title>Predict Pool</title>
        <meta
          content="Stake your MON tokens to participate in predictions and earn rewards."
          name="description"
        />
        <link href="/favicon.ico" rel="icon" />
      </Head>

      <div className="bg-gray-800 rounded-2xl shadow-xl border border-gray-700 p-8 max-w-2xl mx-auto">
        <StakeForm stakedBalance={stakedBalance as bigint | undefined} />
      </div>

      <div className="bg-gray-800 rounded-2xl shadow-xl border border-gray-700 p-8 mt-6 max-w-2xl mx-auto">
        <WithdrawForm stakedBalance={stakedBalance as bigint | undefined} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8 max-w-2xl mx-auto">
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-2">
            About Staking
          </h3>
          <p className="text-gray-400">
            Stake your MON tokens to participate in predictions and earn
            rewards.
          </p>
        </div>

        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Rewards</h3>
          <p className="text-gray-400">
            Earn rewards based on your prediction accuracy and staked amount.
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default Home;
