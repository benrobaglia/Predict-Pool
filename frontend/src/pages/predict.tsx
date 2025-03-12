import RoundsTimeline from "@/components/prediction/RoundsTimeline";
import { Layout } from "@/components/layout/Layout";
import TradingViewWidget from "@/components/TradingView";
const PredictionPage = () => {
  return (
    <Layout>
      <div className="bg-gray-900/50 rounded-2xl p-8 overflow-hidden">
        <TradingViewWidget />
        <RoundsTimeline />
      </div>
    </Layout>
  );
};

export default PredictionPage;
