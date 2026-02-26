import { describe, it, expect } from "vitest";
import { cn } from "./utils";

describe("cn()", () => {
  it("merges classes", () => {
    expect(cn("text-sm", "font-bold")).toBe("text-sm font-bold");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "extra")).toBe("base extra");
  });

  it("deduplicates Tailwind classes (last wins)", () => {
    expect(cn("px-4", "px-2")).toBe("px-2");
  });

  it("handles undefined inputs", () => {
    expect(cn("base", undefined, "end")).toBe("base end");
  });

  it("handles null inputs", () => {
    expect(cn("base", null, "end")).toBe("base end");
  });

  it("handles empty string inputs", () => {
    expect(cn("base", "", "end")).toBe("base end");
  });

  it("returns empty string for no args", () => {
    expect(cn()).toBe("");
  });
});
