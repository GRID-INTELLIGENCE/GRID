import type { Meta, StoryObj } from "@storybook/react-vite";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./card";
import { Button } from "./button";

const meta = {
  title: "UI/Card",
  component: Card,
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>
          A short description of the card content.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          This is the card body. It can contain any content you need.
        </p>
      </CardContent>
    </Card>
  ),
};

export const WithAction: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Intelligence Report</CardTitle>
        <CardDescription>Weekly threat assessment summary</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-sm">
          3 new threat indicators detected across monitored channels.
        </p>
        <div className="flex gap-2">
          <Button size="sm">View Report</Button>
          <Button size="sm" variant="outline">
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  ),
};

export const Minimal: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p className="text-sm">A card with only content, no header.</p>
      </CardContent>
    </Card>
  ),
};

export const Grid: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4">
      {["Alpha", "Bravo", "Charlie", "Delta"].map((name) => (
        <Card key={name}>
          <CardHeader>
            <CardTitle>{name}</CardTitle>
            <CardDescription>Module status: active</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-[var(--muted-foreground)]">
              Last updated 2 min ago
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  ),
};
