import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { monadTestnet } from "./utils/customChains";

export const config = getDefaultConfig({
  appName: "RainbowKit App",
  projectId: "YOUR_PROJECT_ID",
  chains: [monadTestnet],
  ssr: true,
});
