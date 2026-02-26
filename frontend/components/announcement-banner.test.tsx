import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { AnnouncementBanner } from "./announcement-banner";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  localStorage.clear();
});

describe("AnnouncementBanner", () => {
  it("renders nothing when no announcement is returned", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });
    const { container } = render(<AnnouncementBanner />);
    // Wait for effect to settle
    await new Promise((r) => setTimeout(r, 50));
    expect(container.innerHTML).toBe("");
  });

  it("renders announcement text", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ text: "System maintenance tonight", type: "info" }),
    });

    render(<AnnouncementBanner />);
    await waitFor(() => {
      expect(screen.getByText("System maintenance tonight")).toBeInTheDocument();
    });
  });

  it("dismisses announcement and stores in localStorage", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ text: "Hello World", type: "warning" }),
    });

    const user = userEvent.setup();
    render(<AnnouncementBanner />);

    await waitFor(() => {
      expect(screen.getByText("Hello World")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Dismiss" }));

    // Text should be gone
    expect(screen.queryByText("Hello World")).not.toBeInTheDocument();

    // localStorage should have the dismiss key
    const keys = Object.keys(localStorage);
    const dismissKey = keys.find((k) => k.startsWith("announcement_dismissed_"));
    expect(dismissKey).toBeDefined();
  });

  it("stays dismissed if already dismissed in localStorage", async () => {
    // Pre-set the dismiss key — we need to compute the same hash as the component
    // The hash function: (hash << 5) - hash + char for each char, then toString(36)
    const text = "Already seen";
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    localStorage.setItem(`announcement_dismissed_${hash.toString(36)}`, "1");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ text, type: "info" }),
    });

    const { container } = render(<AnnouncementBanner />);
    // Wait for effect to settle
    await new Promise((r) => setTimeout(r, 100));
    expect(container.querySelector("[class*=border-b]")).not.toBeInTheDocument();
  });

  it("renders nothing when announcement text is empty", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ text: "", type: "info" }),
    });

    const { container } = render(<AnnouncementBanner />);
    await new Promise((r) => setTimeout(r, 50));
    expect(container.innerHTML).toBe("");
  });
});
