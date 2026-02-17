/* ═══════════════════════════════════════════════════════════════
 * AUTO-GENERATED from tokens.json — do not edit manually.
 * Run `npm run generate:tokens` to regenerate.
 * ═══════════════════════════════════════════════════════════════ */

import tokens from "./tokens.json";

export type ColorToken = keyof typeof tokens.color;
export type RadiusToken = keyof typeof tokens.radius;
export type SpaceToken = keyof typeof tokens.space;
export type TypographyToken = keyof typeof tokens.typography;
export type ZIndexToken = keyof (typeof tokens)["z-index"];
export type ShadowToken = keyof typeof tokens.shadow;
export type TransitionToken = keyof typeof tokens.transition;

/** Get a CSS variable reference for a color token */
export function colorVar(token: ColorToken): string {
  return `var(--${token})`;
}

/** Get a CSS variable reference for a radius token */
export function radiusVar(token: RadiusToken): string {
  return `var(--radius-${token})`;
}

/** Get a CSS variable reference for a space token */
export function spaceVar(token: SpaceToken): string {
  return `var(--space-${token})`;
}

export { tokens };
export default tokens;
