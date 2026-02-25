"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import type { SearchResponse, SearchHit } from "@/lib/types";

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults(null);
      return;
    }
    try {
      const data = await api.get<SearchResponse>("/search", {
        q,
        limit: "5",
      });
      setResults(data);
      setOpen(true);
    } catch {
      setResults(null);
    }
  }, []);

  const handleChange = (value: string) => {
    setQuery(value);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => doSearch(value), 300);
  };

  const handleSelect = (hit: SearchHit) => {
    setOpen(false);
    setQuery("");
    setResults(null);
    if (hit.type === "predictor") {
      router.push(`/predictor/${hit.slug_or_symbol}`);
    } else {
      router.push(`/stock/${hit.slug_or_symbol}`);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const allResults = [
    ...(results?.predictors ?? []),
    ...(results?.stocks ?? []),
  ];

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
        <Input
          placeholder="Search..."
          className="h-9 w-48 pl-8 md:w-64"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          onFocus={() => {
            if (results && allResults.length > 0) setOpen(true);
          }}
        />
      </div>

      {open && allResults.length > 0 && (
        <div className="absolute top-10 z-50 w-full rounded-md border bg-popover p-1 shadow-md">
          {results!.predictors.length > 0 && (
            <div>
              <p className="px-2 py-1 text-xs font-medium text-muted-foreground">
                Predictors
              </p>
              {results!.predictors.map((hit) => (
                <button
                  key={hit.id}
                  className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                  onClick={() => handleSelect(hit)}
                >
                  <span className="truncate font-medium">{hit.name}</span>
                  {hit.sub_type && (
                    <span className="text-xs text-muted-foreground">
                      {hit.sub_type}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
          {results!.stocks.length > 0 && (
            <div>
              <p className="px-2 py-1 text-xs font-medium text-muted-foreground">
                Stocks
              </p>
              {results!.stocks.map((hit) => (
                <button
                  key={hit.id}
                  className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                  onClick={() => handleSelect(hit)}
                >
                  <span className="font-mono text-xs">
                    {hit.slug_or_symbol}
                  </span>
                  <span className="truncate">{hit.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
