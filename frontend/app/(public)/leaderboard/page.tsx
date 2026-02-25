import type { Metadata } from "next";
import { LeaderboardClient } from "./leaderboard-client";

export const metadata: Metadata = {
  title: "Leaderboard — Enex",
  description:
    "Analyst accuracy rankings for Indian equity market predictions. See who makes the best stock calls.",
};

export default function LeaderboardPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">Leaderboard</h1>
      <LeaderboardClient />
    </div>
  );
}
