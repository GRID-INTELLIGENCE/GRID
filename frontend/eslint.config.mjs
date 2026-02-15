// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(// Global ignores
{
  ignores: [
    "dist/",
    "release/",
    "node_modules/",
    "storybook-static/",
    "scripts/",
    "*.config.*",
  ],
}, // Base JS recommended rules
js.configs.recommended, // TypeScript strict + stylistic
...tseslint.configs.strict, ...tseslint.configs.stylistic, // React hooks
{
  plugins: { "react-hooks": reactHooks },
  rules: reactHooks.configs.recommended.rules,
}, // React Refresh (Vite HMR)
{
  plugins: { "react-refresh": reactRefresh },
  rules: {
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
  },
}, // Project-wide overrides
{
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
  },
  rules: {
    // Allow _ prefixed unused vars (common pattern for destructuring)
    "@typescript-eslint/no-unused-vars": [
      "error",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
    // Allow empty interfaces for extension patterns
    "@typescript-eslint/no-empty-interface": "off",
    // Allow non-null assertions in IPC code where we check upstream
    "@typescript-eslint/no-non-null-assertion": "warn",
  },
}, // Electron main process files — looser rules for Node APIs
{
  files: ["electron/**/*.ts"],
  rules: {
    "@typescript-eslint/no-require-imports": "off",
  },
}, storybook.configs["flat/recommended"]);
