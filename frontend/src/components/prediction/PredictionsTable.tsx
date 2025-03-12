import { format } from "date-fns";
import { PredictionWithDetails } from "../../types/prediction";

export const PredictionsTable = ({
  predictions,
}: {
  predictions: Record<number, PredictionWithDetails>;
}) => {
  const sortedPredictions = Object.values(predictions).sort(
    (a, b) => b.round_id - a.round_id
  );

  if (sortedPredictions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        No predictions made yet
      </div>
    );
  }

  return (
    <div className="mt-8 overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-800">
        <thead>
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Epoch
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Round
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Prediction
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Price Change
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Result
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Time
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {sortedPredictions.map((prediction) => {
            const priceChange =
              prediction.ending_price - prediction.starting_price;
            const priceChangePercent =
              (priceChange / prediction.starting_price) * 100;
            const isCompleted = prediction.round_status === "completed";

            return (
              <tr key={prediction.round_id} className="hover:bg-gray-800/30">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  #{prediction.epoch_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  #{prediction.round_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${
                      prediction.direction === "up"
                        ? "bg-green-500/20 text-green-100"
                        : "bg-red-500/20 text-red-100"
                    }`}
                  >
                    {prediction.direction.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {isCompleted && (
                    <span
                      className={
                        priceChange >= 0 ? "text-green-400" : "text-red-400"
                      }
                    >
                      {priceChange >= 0 ? "+" : ""}
                      {priceChange.toFixed(2)}
                      <span className="text-gray-500 ml-1">
                        ({priceChangePercent >= 0 ? "+" : ""}
                        {priceChangePercent.toFixed(2)}%)
                      </span>
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {isCompleted ? (
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                      ${
                        prediction.is_correct
                          ? "bg-green-500/20 text-green-100"
                          : "bg-red-500/20 text-red-100"
                      }`}
                    >
                      {prediction.is_correct ? "WIN" : "LOSS"}
                    </span>
                  ) : prediction.round_status === "calculating" ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-100">
                      CALCULATING
                    </span>
                  ) : null}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${
                      prediction.round_status === "completed"
                        ? "bg-gray-500/20 text-gray-100"
                        : prediction.round_status === "active"
                        ? "bg-purple-500/20 text-purple-100"
                        : prediction.round_status === "calculating"
                        ? "bg-blue-500/20 text-blue-100"
                        : prediction.round_status === "locked"
                        ? "bg-yellow-500/20 text-yellow-100"
                        : "bg-gray-500/20 text-gray-100"
                    }`}
                  >
                    {prediction.round_status.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                  {format(new Date(prediction.created_at), "MMM d, HH:mm")}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
