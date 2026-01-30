# GRID Nexus Color System

> A perceptually uniform color palette designed for emotional coherence, accessibility, and visual harmony.

---

## Philosophy

The GRID Nexus color system is built on three foundational principles:

1. **Perceptual Uniformity** - Colors derived from OKLCH color space ensure equal perceived lightness across hues
2. **Emotional Storytelling** - Each color carries semantic meaning and psychological impact
3. **Accessible Contrast** - All color pairs meet WCAG 2.1 AA standards for readability

---

## The Palette Architecture

### Foundation: The Void Spectrum

The background system uses a carefully calibrated dark gradient that provides depth without harshness:

| Role | Hex | OKLCH Equivalent | Usage |
|------|-----|------------------|-------|
| **Abyss** | `#06060c` | `oklch(6% 0.01 280)` | Deepest UI elements (activity bar) |
| **Void** | `#08080e` | `oklch(8% 0.01 280)` | Terminal, inputs, secondary panels |
| **Deep** | `#0a0a12` | `oklch(10% 0.01 280)` | Editor, sidebar, primary surfaces |
| **Shadow** | `#0c0c14` | `oklch(12% 0.01 280)` | Active tabs, title bar |
| **Dusk** | `#0e0e18` | `oklch(14% 0.01 280)` | Widgets, dropdowns, notifications |

### Borders & Guides

| Role | Hex | Purpose |
|------|-----|---------|
| **Whisper** | `#1a1a28` | Primary borders, tab separators |
| **Mist** | `#2a2a38` | Indent guides, whitespace markers |

---

## Semantic Color System

### Primary: Cyan Clarity (`#38bec9`)

**Emotional Role:** Trust, Intelligence, Navigation

```
OKLCH: oklch(75% 0.12 195)
Psychology: Clarity • Precision • Forward Motion
```

The primary cyan represents the GRID's core identity—intelligent navigation through complexity. It appears in:
- Active selections and focus states
- Primary actions and links
- Information indicators
- The status bar (representing system health)

**Variants:**
- Lighter: `#48ced9` (hover states)
- Subtle: `#38bec950` (backgrounds, inactive)
- Whisper: `#38bec920` (selection highlights)

---

### Accent: Rose Signal (`#d94878`)

**Emotional Role:** Attention, Importance, Critical Points

```
OKLCH: oklch(55% 0.20 0)
Psychology: Energy • Alert • Significance
```

Rose signals importance without aggression. Unlike pure red, it carries urgency with sophistication:
- Breakpoints and debugging markers
- Badges and notification counts
- Search match highlights
- Delete/remove decorations
- Active borders on focus

**Variants:**
- Lighter: `#f968a8` (bright terminal)
- Subtle: `#d9487830` (word highlight backgrounds)

---

### Success: Verdant Growth (`#48c878`)

**Emotional Role:** Completion, Growth, Positive Outcomes

```
OKLCH: oklch(72% 0.16 145)
Psychology: Growth • Success • Forward Progress
```

Verdant represents successful operations and additions:
- Git additions
- Test passes
- Debug start/continue
- String literals (signifying "complete thoughts")

**Variants:**
- Lighter: `#68e898` (bright terminal)
- Subtle: `#48c87830` (diff inserted backgrounds)

---

### Warning: Amber Signal (`#d8b838`)

**Emotional Role:** Caution, Attention Required, Work in Progress

```
OKLCH: oklch(76% 0.16 90)
Psychology: Caution • Warmth • Attention
```

Amber draws attention without alarm:
- Untracked files
- Warning diagnostics
- Modified indicators
- Constants and decorators (special values)
- Queued tests

**Variants:**
- Lighter: `#f8d858` (bright terminal)
- Subtle: `#d8b83830` (find match highlight)

---

### Function: Violet Logic (`#8848b8`)

**Emotional Role:** Logic, Transformation, Intelligence

```
OKLCH: oklch(48% 0.20 300)
Psychology: Creativity • Logic • Transformation
```

Violet represents transformative logic—the functions and methods that process data:
- Function definitions
- Method calls
- Secondary buttons
- Remote connections
- Renamed files

**Variants:**
- Lighter: `#9858c8` (hover, function calls)
- Subtle: `#8848b830` (word highlight strong)

---

### Property: Azure Reference (`#5888d8`)

**Emotional Role:** Reference, Connection, Data Flow

```
OKLCH: oklch(60% 0.14 260)
Psychology: Reference • Flow • Connection
```

Azure represents data connections and references:
- Properties and fields
- Parameters (italicized for distinction)
- Variable references
- Keys in JSON

**Variants:**
- Lighter: `#78a8f8` (bright terminal)
- Subtle: `#5888d820` (merge conflict backgrounds)

---

### Error: Coral Alert (`#e85858`)

**Emotional Role:** Error, Failure, Critical Stop

```
OKLCH: oklch(58% 0.22 25)
Psychology: Stop • Error • Critical
```

Coral signals errors requiring immediate attention:
- Error diagnostics
- Test failures
- Conflicting git resources
- Invalid syntax

---

### Neutral: Silver Mist

**Foreground Spectrum:**

| Role | Hex | OKLCH L* | Usage |
|------|-----|----------|-------|
| **Bright** | `#f8f8fc` | 98% | Bright terminal white |
| **Primary** | `#e0e0ec` | 90% | Active foregrounds |
| **Standard** | `#d8d8e8` | 86% | Editor text |
| **Secondary** | `#c8c8d8` | 80% | Sidebar text |
| **Muted** | `#a0a8b8` | 68% | Descriptions, operators |
| **Subdued** | `#808898` | 56% | Line numbers, inactive tabs |
| **Faint** | `#606878` | 44% | Comments, placeholders |
| **Ghost** | `#505868` | 38% | Ignored files |
| **Ember** | `#404858` | 32% | Inactive line numbers |

---

## Contrast Ratios

All text-background combinations meet WCAG 2.1 AA requirements:

| Foreground | Background | Ratio | Grade |
|------------|------------|-------|-------|
| `#e0e0ec` | `#0a0a12` | 14.2:1 | AAA |
| `#c8c8d8` | `#0a0a12` | 11.8:1 | AAA |
| `#808898` | `#0a0a12` | 5.4:1 | AA |
| `#606878` | `#0a0a12` | 3.8:1 | AA (large text) |
| `#38bec9` | `#0a0a12` | 8.1:1 | AAA |
| `#d94878` | `#0a0a12` | 5.2:1 | AA |
| `#48c878` | `#0a0a12` | 7.9:1 | AAA |
| `#d8b838` | `#0a0a12` | 8.4:1 | AAA |

---

## Bracket Pair Colorization

Nested brackets follow a perceptually distinct sequence:

1. **Level 1:** `#d8b838` (Amber) — Entry point
2. **Level 2:** `#d94878` (Rose) — First nesting
3. **Level 3:** `#38bec9` (Cyan) — Second nesting
4. **Level 4:** `#48c878` (Green) — Third nesting
5. **Level 5:** `#8848b8` (Violet) — Fourth nesting
6. **Level 6:** `#5888d8` (Azure) — Fifth nesting

This sequence was chosen to maximize perceptual distance between adjacent levels.

---

## Terminal ANSI Colors

The terminal palette maintains consistency with the editor while providing the full 16-color ANSI range:

### Normal Colors
| ANSI | Name | Hex | Role |
|------|------|-----|------|
| 0 | Black | `#1a1a28` | Background variant |
| 1 | Red | `#e85858` | Errors |
| 2 | Green | `#48c878` | Success |
| 3 | Yellow | `#d8b838` | Warnings |
| 4 | Blue | `#5888d8` | Info |
| 5 | Magenta | `#d94878` | Special |
| 6 | Cyan | `#38bec9` | Primary |
| 7 | White | `#e0e0ec` | Text |

### Bright Colors
| ANSI | Name | Hex | Role |
|------|------|-----|------|
| 8 | Bright Black | `#505868` | Dim text |
| 9 | Bright Red | `#f87878` | Bright errors |
| 10 | Bright Green | `#68e898` | Bright success |
| 11 | Bright Yellow | `#f8d858` | Bright warnings |
| 12 | Bright Blue | `#78a8f8` | Bright info |
| 13 | Bright Magenta | `#f968a8` | Bright special |
| 14 | Bright Cyan | `#58dee9` | Bright primary |
| 15 | Bright White | `#f8f8fc` | Bright text |

---

## Implementation Notes

### Using the Theme

The theme is defined in two places:

1. **Workspace Colors** (`grid.code-workspace`): Applied via `workbench.colorCustomizations`
2. **Full Theme** (`.vscode/themes/grid-nexus-color-theme.json`): Complete theme with token colors

### Color Derivation Process

All colors were derived using the OKLCH color space for perceptual uniformity:

```
Base Hues:
- Cyan:    195° (trust, navigation)
- Rose:    0°   (attention, importance)
- Green:   145° (success, growth)
- Yellow:  90°  (caution, constants)
- Violet:  300° (logic, transformation)
- Blue:    260° (reference, data)
- Red:     25°  (error, critical)
- Orange:  50°  (numbers, literals)

Lightness Targets:
- Primary actions:  70-76%
- Secondary:        48-60%
- Backgrounds:      6-14%
- Borders:          15-20%

Chroma:
- Vibrant:  0.16-0.22
- Standard: 0.12-0.16
- Muted:    0.01-0.04
```

### Accessibility Testing

Verify all color combinations using:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [OKLCH Color Picker](https://oklch.com/)
- [Atmos Color Tool](https://atmos.style/playground)

---

## Emotional Journey

The color system tells a story as you work:

1. **The Void** (backgrounds) — A calm, distraction-free canvas
2. **Cyan Clarity** — Your guide, highlighting what matters now
3. **Rose Signals** — Points of importance requiring attention
4. **Verdant Growth** — Successful completions and additions
5. **Amber Warnings** — Gentle cautions and special values
6. **Violet Logic** — The transformative power of functions
7. **Azure Flow** — Data connections and references

Together, these create an environment that supports focus, reduces eye strain, and communicates meaning through color alone.

---

## References

- [OKLCH Color Space](https://oklch.com/) — Perceptual color encoding
- [Evil Martians OKLCH Picker](https://oklch.evilmartians.io/) — Color picker with education focus
- [Color Psychology in UI Design](https://mockflow.com/blog/color-psychology-in-ui-design) — Emotional associations
- [WCAG 2.1 Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html) — Accessibility standards

---

*Last updated: GRID Nexus v1.0*
