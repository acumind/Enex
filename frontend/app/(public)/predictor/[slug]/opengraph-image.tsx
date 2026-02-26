import { ImageResponse } from "next/og";
import type { PredictorResponse, ScorecardResponse } from "@/lib/types";

export const alt = "Predictor Profile — Enex";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function OGImage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const predictor = await fetchJSON<PredictorResponse>(`/predictors/${slug}`);
  const scorecard = predictor
    ? await fetchJSON<ScorecardResponse>(`/scorecards/${predictor.id}`)
    : null;

  const name = predictor?.name ?? slug;
  const type = predictor?.type?.replace("_", " ") ?? "Analyst";
  const accuracy = scorecard?.accuracy_pct
    ? `${parseFloat(scorecard.accuracy_pct).toFixed(1)}%`
    : "N/A";
  const total = scorecard?.total_predictions ?? "N/A";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background:
            "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
          color: "white",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 16,
          }}
        >
          <div
            style={{
              fontSize: 18,
              color: "#38bdf8",
              textTransform: "capitalize",
              background: "rgba(56,189,248,0.1)",
              padding: "6px 16px",
              borderRadius: 20,
            }}
          >
            {type}
          </div>
        </div>
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            letterSpacing: "-0.02em",
            marginBottom: 32,
            textAlign: "center",
            maxWidth: 900,
          }}
        >
          {name}
        </div>
        <div
          style={{
            display: "flex",
            gap: 64,
            marginBottom: 40,
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div style={{ fontSize: 40, fontWeight: 700 }}>{accuracy}</div>
            <div style={{ fontSize: 18, color: "#94a3b8" }}>Accuracy</div>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div style={{ fontSize: 40, fontWeight: 700 }}>{total}</div>
            <div style={{ fontSize: 18, color: "#94a3b8" }}>Predictions</div>
          </div>
        </div>
        <div style={{ fontSize: 20, color: "#64748b" }}>enex.in</div>
      </div>
    ),
    { ...size },
  );
}
