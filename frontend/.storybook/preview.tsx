import type { Preview } from "@storybook/react-vite";
import { ThemeProvider } from "../src/context/ThemeContext";
import { AnalyticsProvider } from "../src/context/AnalyticsContext";
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
      <ThemeProvider>
        <AnalyticsProvider>
          <div className="min-h-screen bg-[var(--background)] p-6 text-[var(--foreground)]">
            <Story />
          </div>
        </AnalyticsProvider>
      </ThemeProvider>
    ),
  ],
};

export default preview;
