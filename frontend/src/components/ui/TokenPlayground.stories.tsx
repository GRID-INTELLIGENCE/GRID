import type { Meta, StoryObj } from "@storybook/react-vite";
import tokens from "../../tokens/tokens.json";

const meta = {
  title: "Design System/TokenPlayground",
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

function ColorSwatch({ name, value }: { name: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <div
        className="h-10 w-10 shrink-0 rounded-md border border-[var(--border)]"
        style={{ backgroundColor: value }}
      />
      <div className="flex flex-col">
        <code className="text-xs font-medium">--{name}</code>
        <span className="text-xs text-[var(--muted-foreground)]">{value}</span>
      </div>
    </div>
  );
}

/** Interactive palette showing all GRID design tokens. */
export const Colors: Story = {
  render: () => (
    <Section title="Colors">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {Object.entries(tokens.themes.dark).map(([name, value]) => (
          <ColorSwatch key={name} name={name} value={value as string} />
        ))}
      </div>
    </Section>
  ),
};

export const Spacing: Story = {
  render: () => (
    <Section title="Spacing Scale">
      <div className="flex flex-col gap-2">
        {Object.entries(tokens.space).map(([name, value]) => (
          <div key={name} className="flex items-center gap-3">
            <code className="w-24 text-xs font-medium">--space-{name}</code>
            <div
              className="h-4 rounded-sm bg-[var(--primary)]"
              style={{ width: value }}
            />
            <span className="text-xs text-[var(--muted-foreground)]">
              {value}
            </span>
          </div>
        ))}
      </div>
    </Section>
  ),
};

export const Radii: Story = {
  render: () => (
    <Section title="Border Radius">
      <div className="flex flex-wrap gap-4">
        {Object.entries(tokens.radius).map(([name, value]) => (
          <div key={name} className="flex flex-col items-center gap-2">
            <div
              className="h-16 w-16 border-2 border-[var(--primary)] bg-[var(--primary)]/10"
              style={{ borderRadius: value }}
            />
            <div className="flex flex-col items-center">
              <code className="text-xs font-medium">--radius-{name}</code>
              <span className="text-xs text-[var(--muted-foreground)]">
                {value}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Section>
  ),
};

export const Typography: Story = {
  render: () => (
    <Section title="Typography">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold">Font Families</h3>
          <p style={{ fontFamily: tokens.typography["font-family"] }}>
            Inter (sans-serif) — The quick brown fox jumps over the lazy dog
          </p>
          <p
            style={{
              fontFamily: tokens.typography["font-family-mono"],
            }}
          >
            JetBrains Mono — const grid = new Intelligence();
          </p>
        </div>

        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold">Font Sizes</h3>
          {Object.entries(tokens.typography)
            .filter(([k]) => k.startsWith("font-size"))
            .map(([name, value]) => (
              <div key={name} className="flex items-baseline gap-3">
                <code className="w-40 shrink-0 text-xs font-medium">
                  --typography-{name}
                </code>
                <span style={{ fontSize: value }}>{value} — Sample text</span>
              </div>
            ))}
        </div>

        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold">Font Weights</h3>
          {Object.entries(tokens.typography)
            .filter(([k]) => k.startsWith("font-weight"))
            .map(([name, value]) => (
              <div key={name} className="flex items-baseline gap-3">
                <code className="w-48 shrink-0 text-xs font-medium">
                  --typography-{name}
                </code>
                <span style={{ fontWeight: Number(value) }}>
                  {name.replace("font-weight-", "")} ({value})
                </span>
              </div>
            ))}
        </div>
      </div>
    </Section>
  ),
};

export const Shadows: Story = {
  render: () => (
    <Section title="Shadows">
      <div className="flex flex-wrap gap-6">
        {Object.entries(tokens.shadow).map(([name, value]) => (
          <div key={name} className="flex flex-col items-center gap-2">
            <div
              className="h-20 w-20 rounded-lg bg-[var(--card)]"
              style={{ boxShadow: value }}
            />
            <div className="flex flex-col items-center">
              <code className="text-xs font-medium">--shadow-{name}</code>
              <span className="max-w-[160px] truncate text-xs text-[var(--muted-foreground)]">
                {value}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Section>
  ),
};

export const ZIndex: Story = {
  render: () => (
    <Section title="Z-Index Layers">
      <div className="flex flex-col gap-1">
        {Object.entries(tokens["z-index"])
          .sort(([, a], [, b]) => Number(a) - Number(b))
          .map(([name, value]) => (
            <div key={name} className="flex items-center gap-3">
              <code className="w-36 text-xs font-medium">--z-index-{name}</code>
              <div
                className="h-4 rounded-sm bg-[var(--primary)]/60"
                style={{ width: `${Number(value) * 0.5}px` }}
              />
              <span className="text-xs text-[var(--muted-foreground)]">
                {value}
              </span>
            </div>
          ))}
      </div>
    </Section>
  ),
};
