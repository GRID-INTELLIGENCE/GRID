import type { Meta, StoryObj } from "@storybook/react-vite";
import { Badge } from "./badge";

const meta = {
  title: "UI/Badge",
  component: Badge,
  argTypes: {
    variant: {
      control: "select",
      options: [
        "default",
        "secondary",
        "success",
        "warning",
        "destructive",
        "outline",
      ],
    },
  },
  args: {
    children: "Badge",
    variant: "default",
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Secondary: Story = {
  args: { variant: "secondary", children: "Secondary" },
};

export const Success: Story = {
  args: { variant: "success", children: "Online" },
};

export const Warning: Story = {
  args: { variant: "warning", children: "Degraded" },
};

export const Destructive: Story = {
  args: { variant: "destructive", children: "Critical" },
};

export const Outline: Story = {
  args: { variant: "outline", children: "v1.0.0" },
};

/** All variants side-by-side for visual comparison. */
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Badge variant="default">Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="success">Online</Badge>
      <Badge variant="warning">Degraded</Badge>
      <Badge variant="destructive">Critical</Badge>
      <Badge variant="outline">v1.0.0</Badge>
    </div>
  ),
};

/** Badges used as status indicators. */
export const StatusIndicators: Story = {
  render: () => (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Badge variant="success">Active</Badge>
        <span className="text-sm">RAG Pipeline</span>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="warning">Pending</Badge>
        <span className="text-sm">Cognitive Engine</span>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="destructive">Error</Badge>
        <span className="text-sm">MCP Server</span>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="secondary">Disabled</Badge>
        <span className="text-sm">Telemetry</span>
      </div>
    </div>
  ),
};
