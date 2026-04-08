/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "./",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "dist/renderer",
    emptyOutDir: true,
    // Production optimizations
    minify: "esbuild", // Faster than terser
    sourcemap: process.env.NODE_ENV === "production" ? "hidden" : true,
    rollupOptions: {
      output: {
        // Optimize chunk splitting for better caching
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (
              id.includes("react-dom/") ||
              id.includes("react/") ||
              id.includes("react-router-dom")
            ) {
              return "react-vendor";
            }
            if (id.includes("@tanstack/react-query")) {
              return "query-vendor";
            }
            if (
              id.includes("lucide-react") ||
              id.includes("clsx") ||
              id.includes("class-variance-authority") ||
              id.includes("tailwind-merge")
            ) {
              return "ui-vendor";
            }
          }
          if (id.includes("src/lib/grid-client")) {
            return "grid-client";
          }
          if (id.includes("src/lib/state-persistence")) {
            return "state-persistence";
          }
          if (
            id.includes("src/lib/analytics") ||
            id.includes("src/hooks/use-analytics")
          ) {
            return "analytics";
          }
        },
        // Optimize asset naming for caching
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split(".") ?? [];
          const extType = info[info.length - 1];
          if (
            /\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name ?? "")
          ) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/\.(css)$/i.test(assetInfo.name ?? "")) {
            return `assets/css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
        chunkFileNames: "assets/js/[name]-[hash].js",
        entryFileNames: "assets/js/[name]-[hash].js",
      },
    },
    // Performance optimizations
    reportCompressedSize: false, // Faster builds
    chunkSizeWarningLimit: 1000, // Warn on large chunks
    cssCodeSplit: true, // Split CSS for better caching
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "json-summary"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/__tests__/**",
        "src/**/*.stories.{ts,tsx}",
        "src/**/*.d.ts",
        "src/main.tsx",
        "src/tokens/index.ts",
      ],
    },
  },
});
