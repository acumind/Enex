import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent } from "@/test/test-utils";
import { ThemeToggle } from "./theme-toggle";

// Mock the store module
const mockSetMode = vi.fn();
vi.mock("@/lib/stores", () => ({
  useThemeStore: (selector: (s: { mode: string; setMode: typeof mockSetMode }) => unknown) =>
    selector({ mode: "light", setMode: mockSetMode }),
}));

describe("ThemeToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a button with aria-label 'Toggle theme'", () => {
    render(<ThemeToggle />);
    expect(screen.getByRole("button", { name: "Toggle theme" })).toBeInTheDocument();
  });

  it("calls setMode on click", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole("button", { name: "Toggle theme" }));
    expect(mockSetMode).toHaveBeenCalled();
  });
});
