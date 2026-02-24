import type { Meta, StoryObj } from "@storybook/react-vite";
import { NetworkViz } from "./NetworkViz";

const meta = {
  title: "Mycelium/NetworkViz",
  component: NetworkViz,
  args: {
    concepts: ["cache", "recursion", "api", "database", "encryption", "auth"],
  },
} satisfies Meta<typeof NetworkViz>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const FewNodes: Story = {
  args: { concepts: ["cache", "api"] },
};

export const ManyNodes: Story = {
  args: {
    concepts: [
      "cache",
      "recursion",
      "api",
      "database",
      "encryption",
      "auth",
      "routing",
      "middleware",
      "queue",
      "stream",
      "buffer",
      "protocol",
    ],
  },
};

export const SingleNode: Story = {
  args: { concepts: ["cache"] },
};
