import { useState, useEffect } from "react";
import { Round, Epoch } from "@/types/prediction";

interface EpochData {
  id: number;
  start_time: string;
  rounds: number;
}

export const useRounds = () => {
  const [rounds, setRounds] = useState<Round[]>([]);
  const [relevantRound, setRelevantRound] = useState<Round | null>(null);
  const [upcomingEpochs, setUpcomingEpochs] = useState<EpochData[]>([]);

  const fetchCurrentEpoch = async (): Promise<Epoch | null> => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/epochs/current`
      );
      if (!response.ok) {
        console.warn("No current epoch found");
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching current epoch:", error);
      return null;
    }
  };

  const fetchEpochRounds = async (epochId: number): Promise<Round[]> => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/epochs/${epochId}/rounds`
      );
      if (!response.ok) {
        console.warn("No rounds found for epoch");
        return [];
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching epoch rounds:", error);
      return [];
    }
  };

  const fetchRoundsData = async () => {
    const currentEpoch = await fetchCurrentEpoch();
    if (!currentEpoch) return;

    const epochRounds = await fetchEpochRounds(currentEpoch.id);
    setRounds(epochRounds);

    const relevantRound = epochRounds.find((round) =>
      ["active", "calculating", "locked"].includes(round.status)
    );
    setRelevantRound(relevantRound || null);
  };

  useEffect(() => {
    fetchRoundsData();
    const interval = setInterval(fetchRoundsData, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchUpcomingEpochs = async () => {
      if (!relevantRound?.epoch_id) return;

      try {
        const nextTwoEpochs = await Promise.all([
          fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/epochs/${
              relevantRound.epoch_id + 1
            }`
          ).then((res) => res.json()),
          // fetch(
          //   `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/epochs/${
          //     relevantRound.epoch_id + 2
          //   }`
          // ).then((res) => res.json()),
        ]);
        setUpcomingEpochs(nextTwoEpochs);
      } catch (error) {
        console.error("Failed to fetch upcoming epochs:", error);
      }
    };

    fetchUpcomingEpochs();
  }, [relevantRound?.epoch_id]);

  return {
    rounds: rounds.sort((a, b) => a.id - b.id),
    relevantRound,
    upcomingEpochs,
  };
};
