import { Round, PredictionWithDetails } from "@/types/prediction";
import { useState, useEffect } from "react";

interface RoundCardProps {
  round: Round;
  isRelevant: boolean;
  onPredictionSubmit: (
    direction: "up" | "down",
    roundId: number
  ) => Promise<void>;
  userPrediction?: PredictionWithDetails;
}
export const RoundCard = ({
  round,
  isRelevant,
  onPredictionSubmit,
  userPrediction,
  ...props
}: RoundCardProps & { [key: string]: any }) => {
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  // Fetch current ETH price
  const fetchCurrentPrice = async () => {
    try {
      const response = await fetch(
        `https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT`
      );
      if (!response.ok) return;
      const data = await response.json();
      setCurrentPrice(parseFloat(data.price)); // Parse string price to float
    } catch (error) {
      console.error("Error fetching current price:", error);
    }
  };

  // Set up polling for price updates when round is active
  useEffect(() => {
    if (round.status === "active") {
      fetchCurrentPrice();
      const interval = setInterval(fetchCurrentPrice, 2000); // Update every 2 seconds
      return () => clearInterval(interval);
    }
  }, [round.status]);

  // Calculate and update remaining time
  useEffect(() => {
    if (round.status === "active") {
      const updateTimeRemaining = () => {
        const now = Date.now();
        // Parse the start time as UTC
        const [datePart, timePart] = round.start_time.split(" ");
        const roundStartTime = Date.UTC(
          parseInt(datePart.split("-")[0]), // year
          parseInt(datePart.split("-")[1]) - 1, // month (0-based)
          parseInt(datePart.split("-")[2]), // day
          parseInt(timePart.split(":")[0]), // hour
          parseInt(timePart.split(":")[1]), // minute
          parseInt(timePart.split(":")[2] || "0") // second
        );

        const timeSinceStart = (now - roundStartTime) / 1000; // Convert to seconds
        const remaining = Math.max(0, 30 - Math.floor(timeSinceStart));

        // Debug logs
        console.log({
          now,
          roundStartTime,
          timeSinceStartSeconds: timeSinceStart,
          remaining,
          startTimeStr: round.start_time,
          nowLocal: new Date().toLocaleString(),
          startTimeLocal: new Date(roundStartTime).toLocaleString(),
          nowUTC: new Date().toUTCString(),
          startTimeUTC: new Date(roundStartTime).toUTCString(),
        });

        setTimeRemaining(remaining);

        // If time is up, you might want to trigger a status update
        if (remaining === 0) {
          // Optional: You could emit an event or callback to parent component
          // to update the round status
        }
      };

      updateTimeRemaining();
      const timer = setInterval(updateTimeRemaining, 1000);
      return () => clearInterval(timer);
    } else {
      setTimeRemaining(null); // Reset timer when round is not active
    }
  }, [round.status, round.start_time]);

  const getStatusStyles = () => {
    switch (round.status) {
      case "completed":
      case "scheduled":
        return "bg-gray-800/30 hover:bg-gray-800/40";
      case "active":
        return "bg-purple-500/20 hover:bg-purple-500/30 ring-2 ring-purple-500";
      case "calculating":
        return "bg-blue-500/20 hover:bg-blue-500/30 ring-2 ring-blue-500";
      case "locked":
        return "bg-amber-500/20 hover:bg-amber-500/30 ring-2 ring-amber-500";
      default:
        return "bg-gray-800/30 hover:bg-gray-800/40";
    }
  };

  const getStatusBadgeStyles = () => {
    switch (round.status) {
      case "completed":
      case "scheduled":
        return "bg-gray-700/50 text-gray-300";
      case "active":
        return "bg-purple-500 text-white";
      case "calculating":
        return "bg-blue-500 text-white";
      case "locked":
        return "bg-amber-500 text-white";
      default:
        return "bg-gray-700/50 text-gray-300";
    }
  };

  const getStatusTextColor = () => {
    switch (round.status) {
      case "active":
        return "text-purple-100";
      case "calculating":
        return "text-blue-100";
      case "locked":
        return "text-amber-100";
      default:
        return "text-gray-100";
    }
  };

  const canPredict = round.status === "active";

  return (
    <div
      {...props}
      className={`
        min-w-[280px] p-4 rounded-lg transition-all duration-300
        ${getStatusStyles()}
        ${isRelevant ? "transform scale-105 z-10" : "opacity-75"}
      `}
    >
      <div className="flex justify-between items-center mb-4">
        <span
          className={`text-sm ${
            isRelevant ? getStatusTextColor() : "text-gray-300"
          }`}
        >
          Round #{round.id}
        </span>
        <span
          className={`
            text-xs px-3 py-1 rounded-md
            ${getStatusBadgeStyles()}
          `}
        >
          {round.status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Starting Price</span>
          <span
            className={`font-medium ${
              isRelevant ? getStatusTextColor() : "text-gray-100"
            }`}
          >
            ${round.starting_price.toFixed(2)}
          </span>
        </div>

        {/* Updated current price display with fixed decimal places */}
        {round.status === "active" && currentPrice && (
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Current Price</span>
            <div className="flex items-center space-x-2">
              <span
                className={`font-medium ${
                  isRelevant ? getStatusTextColor() : "text-gray-100"
                }`}
              >
                ${currentPrice.toFixed(2)}
              </span>
              {round.starting_price && (
                <span
                  className={`text-sm ${
                    currentPrice >= round.starting_price
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  (
                  {(
                    ((currentPrice - round.starting_price) /
                      round.starting_price) *
                    100
                  ).toFixed(2)}
                  %)
                </span>
              )}
            </div>
          </div>
        )}

        {round.ending_price > 0 && (
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Ending Price</span>
            <span
              className={`font-medium ${
                isRelevant ? getStatusTextColor() : "text-gray-100"
              }`}
            >
              ${round.ending_price.toFixed(2)}
            </span>
          </div>
        )}
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Lock Time</span>
          <div className="flex items-center space-x-2">
            <span
              className={`font-medium ${
                isRelevant ? getStatusTextColor() : "text-gray-100"
              }`}
            >
              {new Date(round.lock_start).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {round.status === "active" && timeRemaining !== null && (
              <span className="text-amber-400 text-sm">
                ({timeRemaining}s remaining)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Prediction buttons will now only show for active rounds */}
      {canPredict && (
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => onPredictionSubmit("up", round.id)}
            disabled={!!userPrediction}
            className={`
              flex-1 py-2 px-4 rounded-md text-sm font-medium
              ${
                userPrediction?.direction === "up"
                  ? "bg-green-500/50 text-green-100"
                  : "bg-green-500/20 hover:bg-green-500/30 text-green-100"
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            UP
          </button>
          <button
            onClick={() => onPredictionSubmit("down", round.id)}
            disabled={!!userPrediction}
            className={`
              flex-1 py-2 px-4 rounded-md text-sm font-medium
              ${
                userPrediction?.direction === "down"
                  ? "bg-red-500/50 text-red-100"
                  : "bg-red-500/20 hover:bg-red-500/30 text-red-100"
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            DOWN
          </button>
        </div>
      )}
    </div>
  );
};
