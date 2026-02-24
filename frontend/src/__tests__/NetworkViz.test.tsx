import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NetworkViz } from "@/components/mycelium/NetworkViz";

describe("NetworkViz", () => {
  it("renders nothing with empty concepts", () => {
    const { container } = render(<NetworkViz concepts={[]} />);
    expect(container.querySelector("svg")).toBeNull();
  });

  it("renders an SVG with the correct aria-label", () => {
    render(<NetworkViz concepts={["cache", "recursion"]} />);
    expect(
      screen.getByRole("img", { name: "Concept network visualization" })
    ).toBeInTheDocument();
  });

  it("renders nodes for each concept", () => {
    render(<NetworkViz concepts={["cache", "recursion", "api"]} />);
    expect(screen.getByText("cache")).toBeInTheDocument();
    expect(screen.getByText("recursion")).toBeInTheDocument();
    expect(screen.getByText("api")).toBeInTheDocument();
  });

  it("limits to 12 nodes maximum", () => {
    const concepts = Array.from({ length: 20 }, (_, i) => `concept${i}`);
    render(<NetworkViz concepts={concepts} />);

    // Only first 12 should render
    expect(screen.getByText("concept0")).toBeInTheDocument();
    expect(screen.getByText("concept11")).toBeInTheDocument();
    expect(screen.queryByText("concept12")).toBeNull();
  });

  it("replaces underscores with spaces in labels", () => {
    render(<NetworkViz concepts={["linked_list"]} />);
    expect(screen.getByText("linked list")).toBeInTheDocument();
  });

  it("truncates long concept names", () => {
    render(<NetworkViz concepts={["very_long_concept_name"]} />);
    expect(screen.getByText(/very long c\.\.\./)).toBeInTheDocument();
  });

  it("calls onConceptClick when a node is clicked", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    render(<NetworkViz concepts={["cache", "api"]} onConceptClick={handler} />);

    await user.click(screen.getByLabelText("Explore concept: cache"));
    expect(handler).toHaveBeenCalledWith("cache");
  });

  it("calls onConceptClick on Enter keypress", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    render(<NetworkViz concepts={["cache"]} onConceptClick={handler} />);

    const node = screen.getByLabelText("Explore concept: cache");
    node.focus();
    await user.keyboard("{Enter}");
    expect(handler).toHaveBeenCalledWith("cache");
  });

  it("renders edges between nodes", () => {
    const { container } = render(
      <NetworkViz concepts={["cache", "recursion", "api"]} />
    );
    const lines = container.querySelectorAll("line");
    expect(lines.length).toBeGreaterThan(0);
  });
});
