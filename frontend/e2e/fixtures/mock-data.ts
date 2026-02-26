import type {
  AnnouncementResponse,
  AuthUser,
  LeaderboardEntry,
  PlatformStatsResponse,
  SearchResponse,
} from "../../lib/types";

export const mockStats: PlatformStatsResponse = {
  total_predictions: 1245,
  total_predictors: 87,
  total_stocks: 312,
  avg_accuracy_pct: "62.4",
  total_evaluated: 890,
};

function makeEntry(i: number): LeaderboardEntry {
  return {
    predictor_id: `pred-${i}`,
    predictor_name: `Analyst ${i}`,
    predictor_slug: `analyst-${i}`,
    predictor_type: "individual",
    total_predictions: 50 - i,
    hits: 30 - i,
    misses: 10,
    partial_hits: 5,
    accuracy_pct: `${80 - i * 2}.0`,
    avg_deviation_pct: `${3 + i * 0.5}`,
    streak_current: 5 - Math.min(i, 4),
  };
}

export const mockLeaderboard: LeaderboardEntry[] = Array.from(
  { length: 5 },
  (_, i) => makeEntry(i + 1),
);

/** 21 entries — enough to trigger "Next" pagination (PAGE_SIZE = 20, fetch 21). */
export const mockLeaderboard21: LeaderboardEntry[] = Array.from(
  { length: 21 },
  (_, i) => makeEntry(i + 1),
);

export const mockSearchResponse: SearchResponse = {
  predictors: [
    {
      id: "p1",
      name: "Motilal Oswal",
      slug_or_symbol: "motilal-oswal",
      type: "predictor",
      sub_type: "brokerage",
    },
  ],
  stocks: [
    {
      id: "s1",
      name: "Reliance Industries",
      slug_or_symbol: "RELIANCE",
      type: "stock",
      sub_type: null,
    },
  ],
};

export const mockAnnouncement: AnnouncementResponse = {
  text: "Enex is now in public beta! Feedback welcome.",
  type: "info",
};

export const mockAuthUser: AuthUser = {
  id: "user-1",
  email: "test@enex.in",
  phone: null,
  name: "Test User",
  avatar_url: null,
  role: "user",
  is_email_verified: true,
  is_phone_verified: false,
  auth_methods: ["email"],
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  last_login_at: "2025-06-01T00:00:00Z",
};
