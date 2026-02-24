import type { Meta, StoryObj } from "@storybook/react-vite";
import { UsageInsights } from "./UsageInsights";

const meta = {
  title: "UI/UsageInsights",
  component: UsageInsights,
} satisfies Meta<typeof UsageInsights>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
