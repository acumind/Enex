"use client";

import { useEffect, useState } from "react";
import type { AnnouncementResponse } from "@/lib/types";

const STYLE_MAP: Record<string, string> = {
  info: "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200",
  warning:
    "bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-200",
  critical:
    "bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-200",
};

function hashText(text: string): string {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return hash.toString(36);
}

export function AnnouncementBanner() {
  const [announcement, setAnnouncement] =
    useState<AnnouncementResponse | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    fetch("/api/v1/announcement")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: AnnouncementResponse | null) => {
        if (data && data.text) {
          const key = `announcement_dismissed_${hashText(data.text)}`;
          if (typeof window !== "undefined" && localStorage.getItem(key)) {
            setDismissed(true);
          }
          setAnnouncement(data);
        }
      })
      .catch(() => {});
  }, []);

  if (!announcement || !announcement.text || dismissed) return null;

  const dismiss = () => {
    const key = `announcement_dismissed_${hashText(announcement.text)}`;
    localStorage.setItem(key, "1");
    setDismissed(true);
  };

  const style = STYLE_MAP[announcement.type] || STYLE_MAP.info;

  return (
    <div className={`border-b px-4 py-2 text-sm ${style}`}>
      <div className="container mx-auto flex items-center justify-between">
        <span>{announcement.text}</span>
        <button
          onClick={dismiss}
          className="ml-4 shrink-0 opacity-60 hover:opacity-100"
          aria-label="Dismiss"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
