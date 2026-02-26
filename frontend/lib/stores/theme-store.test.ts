import { describe, it, expect, beforeEach } from "vitest";
import { useThemeStore } from "./theme-store";

describe("useThemeStore", () => {
  beforeEach(() => {
    useThemeStore.setState({ mode: "system" });
    localStorage.clear();
  });

  it("has initial mode 'system'", () => {
    expect(useThemeStore.getState().mode).toBe("system");
  });

  it("setMode updates to 'dark'", () => {
    useThemeStore.getState().setMode("dark");
    expect(useThemeStore.getState().mode).toBe("dark");
  });

  it("setMode updates to 'light'", () => {
    useThemeStore.getState().setMode("light");
    expect(useThemeStore.getState().mode).toBe("light");
  });

  it("persists to localStorage under 'enex-theme' key", () => {
    useThemeStore.getState().setMode("dark");
    const stored = JSON.parse(localStorage.getItem("enex-theme") || "{}");
    expect(stored.state.mode).toBe("dark");
  });
});
