import { ImageResponse } from "next/og";
import type { StockResponse } from "@/lib/types";

export const alt = "Stock — Enex";
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
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const stock = await fetchJSON<StockResponse>(`/stocks/${symbol}`);

  const name = stock?.name ?? symbol;
  const sym = stock?.symbol ?? symbol;
  const sector = stock?.sector ?? "";
  const exchange = stock?.exchange ?? "NSE";

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
              color: "#a78bfa",
              background: "rgba(167,139,250,0.1)",
              padding: "6px 16px",
              borderRadius: 20,
            }}
          >
            {exchange}
          </div>
        </div>
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            letterSpacing: "-0.02em",
            marginBottom: 12,
            textAlign: "center",
            maxWidth: 900,
          }}
        >
          {name}
        </div>
        <div
          style={{
            fontSize: 28,
            color: "#94a3b8",
            marginBottom: 16,
          }}
        >
          {sym}
        </div>
        {sector && (
          <div
            style={{
              fontSize: 22,
              color: "#64748b",
              marginBottom: 40,
            }}
          >
            {sector}
          </div>
        )}
        <div style={{ fontSize: 20, color: "#64748b" }}>enex.in</div>
      </div>
    ),
    { ...size },
  );
}
