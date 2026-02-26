import { create } from "zustand";
import { persist } from "zustand/middleware";

interface LeaderboardState {
  predictorType: string;
  sortBy: string;
  setPredictorType: (type: string) => void;
  setSortBy: (sort: string) => void;
}

export const useLeaderboardStore = create<LeaderboardState>()(
  persist(
    (set) => ({
      predictorType: "all",
      sortBy: "accuracy",
      setPredictorType: (predictorType) => set({ predictorType }),
      setSortBy: (sortBy) => set({ sortBy }),
    }),
    { name: "enex-leaderboard" },
  ),
);
