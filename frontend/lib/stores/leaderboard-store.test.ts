import { describe, it, expect, beforeEach } from "vitest";
import { useLeaderboardStore } from "./leaderboard-store";

describe("useLeaderboardStore", () => {
  beforeEach(() => {
    // Reset store state between tests
    useLeaderboardStore.setState({
      predictorType: "all",
      sortBy: "accuracy",
    });
    localStorage.clear();
  });

  it("has correct initial state", () => {
    const state = useLeaderboardStore.getState();
    expect(state.predictorType).toBe("all");
    expect(state.sortBy).toBe("accuracy");
  });

  it("setPredictorType updates predictorType", () => {
    useLeaderboardStore.getState().setPredictorType("brokerage");
    expect(useLeaderboardStore.getState().predictorType).toBe("brokerage");
  });

  it("setSortBy updates sortBy", () => {
    useLeaderboardStore.getState().setSortBy("streak");
    expect(useLeaderboardStore.getState().sortBy).toBe("streak");
  });

  it("persists to localStorage under 'enex-leaderboard' key", () => {
    useLeaderboardStore.getState().setPredictorType("individual");
    const stored = JSON.parse(
      localStorage.getItem("enex-leaderboard") || "{}",
    );
    expect(stored.state.predictorType).toBe("individual");
  });
});
