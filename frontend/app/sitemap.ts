import type { MetadataRoute } from "next";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://enex.in";

interface PredictorHit {
  slug_or_symbol: string;
}

interface StockHit {
  slug_or_symbol: string;
}

interface SearchResponse {
  predictors: PredictorHit[];
  stocks: StockHit[];
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: SITE_URL, changeFrequency: "daily", priority: 1 },
    {
      url: `${SITE_URL}/leaderboard`,
      changeFrequency: "daily",
      priority: 0.9,
    },
  ];

  // Fetch predictors and stocks for dynamic routes
  try {
    // Use search with a wildcard-ish query to get known entities
    // Alternatively fetch from dedicated listing endpoints
    const res = await fetch(`${API_BASE}/search?q=%25&limit=50`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return staticRoutes;
    const data: SearchResponse = await res.json();

    const predictorRoutes: MetadataRoute.Sitemap = data.predictors.map(
      (p) => ({
        url: `${SITE_URL}/predictor/${p.slug_or_symbol}`,
        changeFrequency: "weekly" as const,
        priority: 0.7,
      })
    );

    const stockRoutes: MetadataRoute.Sitemap = data.stocks.map((s) => ({
      url: `${SITE_URL}/stock/${s.slug_or_symbol}`,
      changeFrequency: "weekly" as const,
      priority: 0.6,
    }));

    return [...staticRoutes, ...predictorRoutes, ...stockRoutes];
  } catch {
    return staticRoutes;
  }
}
