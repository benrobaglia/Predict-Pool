import { useState, useEffect, useRef } from "react";
import { useAccount, useSignMessage } from "wagmi";
import { PredictionWithDetails, Prediction, Round } from "@/types/prediction";

export const usePredictions = (rounds: Round[]) => {
  const { address } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const [userPredictions, setUserPredictions] = useState<
    Record<number, PredictionWithDetails>
  >({});
  const [error, setError] = useState<string | null>(null);
  const previousActiveRoundRef = useRef<number | null>(null);

  const fetchUserPredictions = async () => {
    if (!address) {
      console.error("No address found");
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/users/${address}/predictions`
      );
      if (!response.ok) return;

      const predictions = await response.json();
      const predictionsMap = predictions.reduce(
        (
          acc: Record<number, PredictionWithDetails>,
          pred: PredictionWithDetails
        ) => {
          acc[pred.round_id] = pred;
          return acc;
        },
        {}
      );

      setUserPredictions(predictionsMap);
    } catch (error) {
      console.error("Error fetching user predictions:", error);
    }
  };

  const submitPrediction = async (
    direction: "up" | "down",
    roundId: number
  ) => {
    if (!address) {
      console.error("No address found");
      return;
    }

    try {
      setError(null); // Clear any previous errors
      const message = `Predict ${direction} for round ${roundId}`;
      const signature = await signMessageAsync({ message });

      const prediction: Prediction = {
        address: address,
        round_id: roundId,
        direction,
        signature,
      };

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/predictionsv2`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(prediction),
        }
      );

      if (response.status === 403) {
        const errorData = await response.json();
        setError(errorData.error || "You are not eligible to make predictions");
        return;
      }

      if (!response.ok) throw new Error("Failed to submit prediction");
      await fetchUserPredictions();
    } catch (error) {
      console.error("Error submitting prediction:", error);
    }
  };

  useEffect(() => {
    if (address) {
      fetchUserPredictions();
    }
  }, [address]);

  useEffect(() => {
    const activeRound = rounds.find((round) => round.status === "active");
    const activeRoundId = activeRound?.id;

    if (activeRoundId && previousActiveRoundRef.current !== activeRoundId) {
      previousActiveRoundRef.current = activeRoundId;
      fetchUserPredictions();
    }
  }, [rounds, address]);

  return { userPredictions, submitPrediction, error };
};
