import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MyceliumPage } from "@/pages/MyceliumPage";
import { renderWithProviders } from "./test-utils";
import {
  mockMyceliumSynthesize,
  mockMyceliumExplore,
  mockMyceliumFeedback,
  mockMyceliumConcepts,
} from "./setup";

describe("MyceliumPage", () => {
  it("renders the page header and input area", () => {
    renderWithProviders(<MyceliumPage />);
    expect(screen.getByText("Mycelium")).toBeInTheDocument();
    expect(
      screen.getByText("Paste text. Get the essence.")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Text to synthesize")).toBeInTheDocument();
  });

  it("shows the Synthesize button disabled when input is empty", () => {
    renderWithProviders(<MyceliumPage />);
    const btn = screen.getByRole("button", { name: /synthesize/i });
    expect(btn).toBeDisabled();
  });

  it("enables the Synthesize button when text is entered", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "The speed of light is constant.");

    const btn = screen.getByRole("button", { name: /synthesize/i });
    expect(btn).toBeEnabled();
  });

  it("displays character count when text is entered", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Hello world");
    expect(screen.getByText(/11 chars/)).toBeInTheDocument();
  });

  it("displays word count and reading time when text is entered", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Hello world");
    expect(screen.getByText(/2 words/)).toBeInTheDocument();
    expect(screen.getByText(/1 min read/)).toBeInTheDocument();
  });

  it("calls synthesize and displays the gist", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Electromagnetic radiation is a form of energy.");

    const btn = screen.getByRole("button", { name: /synthesize/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockMyceliumSynthesize).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(
        screen.getByText("Light is electromagnetic radiation.")
      ).toBeInTheDocument();
    });
  });

  it("displays highlights after synthesis", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    await user.type(
      screen.getByLabelText("Text to synthesize"),
      "Some physics text here."
    );
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    await waitFor(() => {
      expect(screen.getByText("electromagnetic")).toBeInTheDocument();
      expect(screen.getByText("radiation")).toBeInTheDocument();
    });
  });

  it("shows depth control with three options", () => {
    renderWithProviders(<MyceliumPage />);
    expect(
      screen.getByRole("radio", { name: /espresso/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /americano/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /cold brew/i })
    ).toBeInTheDocument();
  });

  it("switches depth when clicking a depth option", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const espresso = screen.getByRole("radio", { name: /espresso/i });
    await user.click(espresso);
    expect(espresso).toHaveAttribute("aria-checked", "true");
  });

  it("opens accessibility settings panel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const settingsBtn = screen.getByLabelText("Accessibility settings");
    await user.click(settingsBtn);

    expect(screen.getByText("Sensory Profile")).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /default sensory profile/i })
    ).toBeInTheDocument();
  });

  it("shows feedback bar after synthesis", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    await user.type(
      screen.getByLabelText("Text to synthesize"),
      "Physics content."
    );
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    await waitFor(() => {
      expect(
        screen.getByLabelText("Make this easier to understand")
      ).toBeInTheDocument();
      expect(screen.getByLabelText("Show me more detail")).toBeInTheDocument();
    });
  });

  it("clears input and results when Clear is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Some text to clear.");
    expect(screen.getByText("Clear")).toBeInTheDocument();

    await user.click(screen.getByText("Clear"));
    expect(textarea).toHaveValue("");
  });

  it("loads concepts on mount", async () => {
    renderWithProviders(<MyceliumPage />);
    await waitFor(() => {
      expect(mockMyceliumConcepts).toHaveBeenCalled();
    });
  });

  // ── P3.1: Ctrl+Enter keyboard shortcut ──────────────────────────
  it("triggers synthesis on Ctrl+Enter", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Quantum physics is fascinating.");

    mockMyceliumSynthesize.mockClear();
    await user.keyboard("{Control>}{Enter}{/Control}");

    await waitFor(() => {
      expect(mockMyceliumSynthesize).toHaveBeenCalled();
    });
  });

  // ── P3.2: Error state rendering ─────────────────────────────────
  it("displays error state when synthesis fails", async () => {
    const user = userEvent.setup();
    mockMyceliumSynthesize.mockRejectedValueOnce(
      new Error("Backend unavailable")
    );

    renderWithProviders(<MyceliumPage />);

    const textarea = screen.getByLabelText("Text to synthesize");
    await user.type(textarea, "Some text that will fail.");
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText("Backend unavailable")).toBeInTheDocument();
    });
  });

  // ── P3.3: Concept exploration flow ──────────────────────────────
  it("explores a concept when clicking a keyword, then closes it", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    // Synthesize first
    await user.type(
      screen.getByLabelText("Text to synthesize"),
      "Explain electromagnetic radiation."
    );
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText("electromagnetic")).toBeInTheDocument();
    });

    // Click keyword to explore
    mockMyceliumExplore.mockClear();
    await user.click(screen.getByLabelText(/keyword: electromagnetic/i));

    await waitFor(() => {
      expect(mockMyceliumExplore).toHaveBeenCalledWith("electromagnetic");
    });

    // LensCard should appear (it's a region with aria-label)
    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: /exploring: cache/i })
      ).toBeInTheDocument();
    });

    // Close the lens card
    await user.click(screen.getByLabelText("Close concept explorer"));

    await waitFor(() => {
      expect(
        screen.queryByRole("region", { name: /exploring: cache/i })
      ).not.toBeInTheDocument();
    });
  });

  // ── P3.4: Feedback button depth adjustment ──────────────────────
  it("calls feedback and re-synthesizes when clicking Simpler", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    // Synthesize first
    await user.type(
      screen.getByLabelText("Text to synthesize"),
      "Complex physics text."
    );
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    // Wait for feedback bar
    await waitFor(() => {
      expect(
        screen.getByLabelText("Make this easier to understand")
      ).toBeInTheDocument();
    });

    mockMyceliumFeedback.mockClear();
    mockMyceliumSynthesize.mockClear();

    // Click "Simpler"
    await user.click(screen.getByLabelText("Make this easier to understand"));

    await waitFor(() => {
      expect(mockMyceliumFeedback).toHaveBeenCalledWith(true, false);
    });

    // Should re-synthesize with adjusted depth
    await waitFor(() => {
      expect(mockMyceliumSynthesize).toHaveBeenCalled();
    });
  });

  it("calls feedback and re-synthesizes when clicking Deeper", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MyceliumPage />);

    await user.type(
      screen.getByLabelText("Text to synthesize"),
      "Simple physics text."
    );
    await user.click(screen.getByRole("button", { name: /synthesize/i }));

    await waitFor(() => {
      expect(screen.getByLabelText("Show me more detail")).toBeInTheDocument();
    });

    mockMyceliumFeedback.mockClear();
    mockMyceliumSynthesize.mockClear();

    await user.click(screen.getByLabelText("Show me more detail"));

    await waitFor(() => {
      expect(mockMyceliumFeedback).toHaveBeenCalledWith(false, true);
    });

    await waitFor(() => {
      expect(mockMyceliumSynthesize).toHaveBeenCalled();
    });
  });
});
