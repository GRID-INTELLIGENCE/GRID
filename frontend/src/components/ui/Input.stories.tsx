import type { Meta, StoryObj } from "@storybook/react-vite";
import { Input } from "./input";

const meta = {
  title: "UI/Input",
  component: Input,
  argTypes: {
    type: {
      control: "select",
      options: ["text", "email", "password", "number", "search", "url"],
    },
    disabled: { control: "boolean" },
    placeholder: { control: "text" },
  },
  args: {
    type: "text",
    placeholder: "Enter text...",
    disabled: false,
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithValue: Story = {
  args: { defaultValue: "Hello, GRID" },
};

export const Password: Story = {
  args: { type: "password", placeholder: "Enter password..." },
};

export const Search: Story = {
  args: { type: "search", placeholder: "Search intelligence..." },
};

export const Disabled: Story = {
  args: { disabled: true, placeholder: "Disabled input" },
};

export const DisabledWithValue: Story = {
  args: { disabled: true, defaultValue: "Cannot edit this" },
};

/** Multiple input types for visual comparison. */
export const AllTypes: Story = {
  render: () => (
    <div className="flex w-[320px] flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Text
        <Input type="text" placeholder="Enter text..." />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Email
        <Input type="email" placeholder="user@grid.local" />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Password
        <Input type="password" placeholder="••••••••" />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Number
        <Input type="number" placeholder="0" />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Search
        <Input type="search" placeholder="Search..." />
      </label>
    </div>
  ),
};
