"use client";

import { useEffect } from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useThemeStore } from "@/lib/stores";

export function ThemeToggle() {
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);

  useEffect(() => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

    function apply() {
      const dark =
        mode === "dark" || (mode === "system" && prefersDark.matches);
      document.documentElement.classList.toggle("dark", dark);
    }

    apply();
    prefersDark.addEventListener("change", apply);
    return () => prefersDark.removeEventListener("change", apply);
  }, [mode]);

  const isDark =
    typeof window !== "undefined"
      ? document.documentElement.classList.contains("dark")
      : false;

  const toggle = () => {
    setMode(isDark ? "light" : "dark");
  };

  return (
    <Button variant="ghost" size="sm" onClick={toggle} aria-label="Toggle theme">
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}
