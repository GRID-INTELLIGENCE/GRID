import type { Meta, StoryObj } from "@storybook/react-vite";
import { SynthesisProgress } from "./SynthesisProgress";

const meta = {
  title: "Mycelium/SynthesisProgress",
  component: SynthesisProgress,
  argTypes: {
    active: { control: "boolean" },
  },
  args: {
    active: true,
  },
} satisfies Meta<typeof SynthesisProgress>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Active: Story = {};

export const Inactive: Story = {
  args: { active: false },
};
