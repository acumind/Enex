import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type {
  PredictorResponse,
  ScorecardResponse,
  SearchResponse,
} from "@/lib/types";
import { PredictorProfileClient } from "./predictor-profile-client";

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

export async function generateStaticParams(): Promise<{ slug: string }[]> {
  try {
    const res = await fetch(`${API_BASE}/search?q=%25&limit=50`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    const data: SearchResponse = await res.json();
    return data.predictors.map((p) => ({ slug: p.slug_or_symbol }));
  } catch {
    return [];
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const predictor = await fetchJSON<PredictorResponse>(
    `/predictors/${slug}`,
  );
  if (!predictor) return { title: "Predictor — Enex" };
  const description = `${predictor.name} prediction accuracy, scorecard, and history on Enex.`;
  return {
    title: `${predictor.name} — Enex`,
    description,
    openGraph: {
      title: `${predictor.name} — Enex`,
      description,
      type: "profile",
    },
  };
}

export default async function PredictorProfilePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const predictor = await fetchJSON<PredictorResponse>(
    `/predictors/${slug}`
  );
  if (!predictor) notFound();

  const scorecard = await fetchJSON<ScorecardResponse>(
    `/scorecards/${predictor.id}`
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <PredictorProfileClient
        predictor={predictor}
        scorecard={scorecard}
        slug={slug}
      />
    </div>
  );
}
