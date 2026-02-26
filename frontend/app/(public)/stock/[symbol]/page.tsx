import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { StockResponse, SearchResponse } from "@/lib/types";
import { StockClient } from "./stock-client";

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

export const dynamicParams = true;

export async function generateStaticParams(): Promise<{ symbol: string }[]> {
  try {
    const res = await fetch(`${API_BASE}/search?q=%25&limit=50`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    const data: SearchResponse = await res.json();
    return data.stocks.map((s) => ({ symbol: s.slug_or_symbol }));
  } catch {
    return [];
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const stock = await fetchJSON<StockResponse>(`/stocks/${symbol}`);
  if (!stock) return { title: "Stock — Enex" };
  const description = `Analyst predictions and accuracy for ${stock.name} (${stock.symbol}) on Enex.`;
  return {
    title: `${stock.name} (${stock.symbol}) — Enex`,
    description,
    openGraph: {
      title: `${stock.name} (${stock.symbol}) — Enex`,
      description,
      type: "article",
    },
  };
}

export default async function StockPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const stock = await fetchJSON<StockResponse>(`/stocks/${symbol}`);
  if (!stock) notFound();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <StockClient stock={stock} symbol={symbol} />
    </div>
  );
}
