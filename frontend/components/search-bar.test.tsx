import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { SearchBar } from "./search-bar";

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    download: vi.fn(),
  },
}));

vi.mock("@/lib/api-client", () => ({
  api: mockApi,
}));

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

describe("SearchBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders search input", () => {
    render(<SearchBar />);
    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();
  });

  it("does not search for queries shorter than 2 characters", async () => {
    const user = userEvent.setup();
    render(<SearchBar />);
    await user.type(screen.getByPlaceholderText("Search..."), "a");
    // Wait for debounce
    await new Promise((r) => setTimeout(r, 400));
    expect(mockApi.get).not.toHaveBeenCalled();
  });

  it("searches after debounce (300ms) for queries >= 2 chars", async () => {
    const user = userEvent.setup();
    mockApi.get.mockResolvedValue({ predictors: [], stocks: [] });

    render(<SearchBar />);
    await user.type(screen.getByPlaceholderText("Search..."), "rel");
    await waitFor(() => expect(mockApi.get).toHaveBeenCalled(), {
      timeout: 1000,
    });
    expect(mockApi.get).toHaveBeenCalledWith("/search", {
      q: "rel",
      limit: "5",
    });
  });

  it("renders results dropdown with predictor and stock results", async () => {
    const user = userEvent.setup();
    mockApi.get.mockResolvedValue({
      predictors: [
        { id: "p1", name: "Motilal Oswal", slug_or_symbol: "motilal-oswal", type: "predictor", sub_type: "brokerage" },
      ],
      stocks: [
        { id: "s1", name: "Reliance Industries", slug_or_symbol: "RELIANCE", type: "stock", sub_type: null },
      ],
    });

    render(<SearchBar />);
    await user.type(screen.getByPlaceholderText("Search..."), "rel");
    await waitFor(() => {
      expect(screen.getByText("Motilal Oswal")).toBeInTheDocument();
      expect(screen.getByText("Reliance Industries")).toBeInTheDocument();
    });
  });

  it("navigates to predictor page on predictor selection", async () => {
    const user = userEvent.setup();
    mockApi.get.mockResolvedValue({
      predictors: [
        { id: "p1", name: "Analyst A", slug_or_symbol: "analyst-a", type: "predictor", sub_type: null },
      ],
      stocks: [],
    });

    render(<SearchBar />);
    await user.type(screen.getByPlaceholderText("Search..."), "ana");
    await waitFor(() => expect(screen.getByText("Analyst A")).toBeInTheDocument());
    await user.click(screen.getByText("Analyst A"));
    expect(mockPush).toHaveBeenCalledWith("/predictor/analyst-a");
  });

  it("navigates to stock page on stock selection", async () => {
    const user = userEvent.setup();
    mockApi.get.mockResolvedValue({
      predictors: [],
      stocks: [
        { id: "s1", name: "TCS", slug_or_symbol: "TCS", type: "stock", sub_type: null },
      ],
    });

    render(<SearchBar />);
    await user.type(screen.getByPlaceholderText("Search..."), "TCS");
    await waitFor(() => expect(screen.getByText("TCS", { selector: "span.truncate" })).toBeInTheDocument());
    const stockButtons = screen.getAllByRole("button");
    const tcsButton = stockButtons.find((btn) => btn.textContent?.includes("TCS"));
    await user.click(tcsButton!);
    expect(mockPush).toHaveBeenCalledWith("/stock/TCS");
  });

  it("clears query on selection", async () => {
    const user = userEvent.setup();
    mockApi.get.mockResolvedValue({
      predictors: [
        { id: "p1", name: "Test P", slug_or_symbol: "test-p", type: "predictor", sub_type: null },
      ],
      stocks: [],
    });

    render(<SearchBar />);
    const input = screen.getByPlaceholderText("Search...");
    await user.type(input, "test");
    await waitFor(() => expect(screen.getByText("Test P")).toBeInTheDocument());
    await user.click(screen.getByText("Test P"));
    expect(input).toHaveValue("");
  });
});
