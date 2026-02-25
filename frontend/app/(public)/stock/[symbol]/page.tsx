import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { StockResponse } from "@/lib/types";
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

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const stock = await fetchJSON<StockResponse>(`/stocks/${symbol}`);
  if (!stock) return { title: "Stock — Enex" };
  return {
    title: `${stock.name} (${stock.symbol}) — Enex`,
    description: `Analyst predictions and accuracy for ${stock.name} (${stock.symbol}) on Enex.`,
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
