import { useRef, useEffect, useState } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import { RoundCard } from "@/components/prediction/RoundCard";
import { PredictionsTable } from "@/components/prediction/PredictionsTable";
import { useRounds } from "@/hooks/useRounds";
import { usePredictions } from "@/hooks/usePredictions";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { start } from "repl";
import Link from "next/link";

const RoundsTimeline = () => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { rounds, relevantRound, upcomingEpochs } = useRounds();
  const { userPredictions, submitPrediction, error } = usePredictions(rounds);
  const [nextEpochTimer, setNextEpochTimer] = useState<string>("");

  useEffect(() => {
    if (scrollContainerRef.current && relevantRound) {
      const container = scrollContainerRef.current;
      const relevantCard = container.querySelector(
        `[data-round-id="${relevantRound.id}"]`
      );

      if (relevantCard) {
        const containerPadding = 128;
        const containerWidth = container.clientWidth - containerPadding * 2;
        const cardLeft = (relevantCard as HTMLElement).offsetLeft;
        const cardWidth = (relevantCard as HTMLElement).offsetWidth;
        const scrollPosition =
          cardLeft - containerWidth / 2 - containerPadding + cardWidth / 2;

        container.scrollTo({
          left: Math.max(0, scrollPosition),
          behavior: "smooth",
        });
      }
    }
  }, [relevantRound?.id]);

  const handleScroll = (direction: "left" | "right") => {
    if (!scrollContainerRef.current) return;
    const scrollAmount = 300;
    const container = scrollContainerRef.current;
    const newScrollPosition =
      direction === "left"
        ? container.scrollLeft - scrollAmount
        : container.scrollLeft + scrollAmount;

    container.scrollTo({
      left: newScrollPosition,
      behavior: "smooth",
    });
  };

  function formatTimeLeft(startTime: string): string {
    // Get current time in UTC
    const now =
      new Date().getTime() + new Date().getTimezoneOffset() * 60 * 1000;
    // Convert the date string to UTC milliseconds timestamp
    const startTimestamp = new Date(startTime).getTime();
    const difference = startTimestamp - now;

    if (difference <= 0) return "Starting soon";

    const minutes = Math.floor((difference / 1000 / 60) % 60);
    const seconds = Math.floor((difference / 1000) % 60);

    // Pad seconds with leading zero if needed
    const formattedSeconds = seconds.toString().padStart(2, "0");
    const formattedMinutes = minutes.toString().padStart(2, "0");

    return `${formattedMinutes}:${formattedSeconds}`;
  }

  // Add useEffect for timer
  useEffect(() => {
    const updateTimer = () => {
      if (upcomingEpochs.length > 0) {
        setNextEpochTimer(formatTimeLeft(upcomingEpochs[0].start_time));
      }
    };

    // Initial update
    updateTimer();

    // Update every second
    const timerInterval = setInterval(updateTimer, 1000);

    return () => clearInterval(timerInterval);
  }, [upcomingEpochs]);

  if (rounds.length === 0) {
    return (
      <div className="flex justify-center items-center h-screen">
        <LoadingSpinner size={20} />
      </div>
    );
  }
  return (
    <div className="space-y-12">
      {/* Show error message if exists */}
      {error && (
        <div className="mx-8 p-4 bg-red-900/50 border border-red-700 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
          <Link
            href="/"
            className="text-red-200 text-sm hover:text-red-300 transition-colors font-bold underline"
          >
            Stake tokens to participate
          </Link>
        </div>
      )}

      {/* Epochs Section */}
      <div className="space-y-8">
        {/* Current Epoch */}
        <div className="relative">
          <h2 className="text-xl text-center font-semibold text-gray-100 mb-4 px-8">
            EPOCH #{relevantRound?.epoch_id}
          </h2>

          <div className="relative w-screen -mx-8">
            {/* Existing gradient overlays */}
            <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-gray-900 to-transparent z-10" />
            <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-gray-900 to-transparent z-10" />

            {/* Navigation arrows - unchanged */}
            <div className="absolute top-1/2 left-8 -translate-y-1/2 z-20">
              <button
                onClick={() => handleScroll("left")}
                className="p-2 rounded-full bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
                aria-label="Scroll left"
              >
                <ChevronLeftIcon className="w-6 h-6 text-gray-300" />
              </button>
            </div>
            <div className="absolute top-1/2 right-8 -translate-y-1/2 z-20">
              <button
                onClick={() => handleScroll("right")}
                className="p-2 rounded-full bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
                aria-label="Scroll right"
              >
                <ChevronRightIcon className="w-6 h-6 text-gray-300" />
              </button>
            </div>

            {/* Rounds carousel with round counter */}
            <div
              ref={scrollContainerRef}
              className="flex gap-6 overflow-x-auto px-32 py-4 scroll-smooth"
              style={{
                paddingRight: "calc(128px + 280px)",
                // Custom scrollbar styles
                scrollbarWidth: "thin",
                scrollbarColor: "rgb(75 85 99) transparent",
              }}
            >
              <style jsx>{`
                div::-webkit-scrollbar {
                  height: 6px;
                }
                div::-webkit-scrollbar-track {
                  background: transparent;
                }
                div::-webkit-scrollbar-thumb {
                  background-color: rgb(75 85 99);
                  border-radius: 20px;
                }
              `}</style>
              {rounds.map((round, index) => (
                <div
                  key={round.id}
                  className="flex flex-col items-center gap-2"
                >
                  <span className="text-sm text-gray-400">
                    Round {index + 1} of {rounds.length}
                  </span>
                  <RoundCard
                    round={round}
                    isRelevant={relevantRound?.id === round.id}
                    onPredictionSubmit={submitPrediction}
                    userPrediction={userPredictions[round.id]}
                    data-round-id={round.id}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Future Epochs */}
        <h4 className="text-sm text-gray-400">
          To participate in the upcoming epochs you should already have staked
          your tokens.
        </h4>
        {upcomingEpochs.map((epoch) => (
          <div key={epoch.id} className="px-8">
            <div className="flex flex-col justify-center items-center border border-gray-800 rounded-lg p-6 space-y-2">
              <h3 className="text-lg font-medium text-gray-200">
                EPOCH #{epoch.id}
              </h3>
              <p className="text-sm text-gray-400">
                Starts in {nextEpochTimer}
              </p>
              <p className="text-sm text-gray-400">Rounds #10</p>
            </div>
          </div>
        ))}
      </div>

      {/* Predictions Table Section */}
      <div className="px-8">
        <h2 className="text-xl font-semibold text-gray-100 mb-4">
          Your Predictions
        </h2>
        <PredictionsTable predictions={userPredictions} />
      </div>
    </div>
  );
};

export default RoundsTimeline;
