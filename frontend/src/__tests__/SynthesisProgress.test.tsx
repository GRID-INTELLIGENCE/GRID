import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SynthesisProgress } from "@/components/mycelium/SynthesisProgress";

describe("SynthesisProgress", () => {
  it("renders nothing when not active", () => {
    const { container } = render(<SynthesisProgress active={false} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders a status element when active", () => {
    render(<SynthesisProgress active={true} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("starts with 'Reading...' phase", () => {
    render(<SynthesisProgress active={true} />);
    expect(screen.getByText("Reading...")).toBeInTheDocument();
  });

  it("has accessible aria-live attribute", () => {
    render(<SynthesisProgress active={true} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("has accessible aria-label", () => {
    render(<SynthesisProgress active={true} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-label", "Reading your text");
  });

  it("advances to 'Analyzing...' phase after delay", async () => {
    render(<SynthesisProgress active={true} />);

    // Wait past first phase (1200ms)
    await new Promise((r) => setTimeout(r, 1400));

    expect(screen.getByText("Analyzing...")).toBeInTheDocument();
  });

  it("resets to first phase when deactivated and reactivated", async () => {
    const { rerender } = render(<SynthesisProgress active={true} />);
    await new Promise((r) => setTimeout(r, 1400));

    rerender(<SynthesisProgress active={false} />);
    // Wait for async reset
    await new Promise((r) => setTimeout(r, 50));
    rerender(<SynthesisProgress active={true} />);

    expect(screen.getByText("Reading...")).toBeInTheDocument();
  });
});
