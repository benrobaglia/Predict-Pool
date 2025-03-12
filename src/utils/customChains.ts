import { defineChain } from "viem";

// TODO: Add Chain details here.
export const monadTestnet = defineChain({
  id: 10143,
  name: "Monad Testnet",
  nativeCurrency: { name: "Monad", symbol: "MON", decimals: 18 },
  rpcUrls: {
    default: {
      // TODO: Add Monad RPC URL
      http: ["https://testnet-rpc.monad.xyz"],
    },
  },
  blockExplorers: {
    default: {
      name: "Monad Testnet Blockscout",
      // TODO: Add Explorer URL
      url: "https://testnet.monadexplorer.com",
    },
  },
});

// export const monadHardhat = defineChain({
//   id: 31337,
//   name: "Monad Hardhat",
//   nativeCurrency: { name: "Monad", symbol: "MON", decimals: 18 },
//   rpcUrls: { default: { http: ["http://localhost:8545"] } },
// });
