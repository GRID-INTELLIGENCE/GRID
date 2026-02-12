import type { Preview } from "@storybook/react-vite";
import "../src/index.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      test: "todo",
    },
    backgrounds: { disable: true },
  },
  decorators: [
    (Story) => (
      <div className="dark min-h-screen bg-[var(--color-background)] p-6 text-[var(--color-foreground)]">
        <Story />
      </div>
    ),
  ],
};

export default preview;
