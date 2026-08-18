import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [],
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
    css: false,
    passWithNoTests: true,
    // tests/e2e/**  usa el test runner de Playwright, no vitest -- sin este exclude, vitest los
    // recolecta igual (coinciden con el glob *.spec.ts por defecto) y fallan con "did not expect
    // test.beforeEach() to be called here" porque no corren dentro del fixture de Playwright.
    exclude: ["node_modules/**", "tests/e2e/**"],
    coverage: {
      reporter: ["text", "lcov"],
      exclude: ["node_modules/", ".next/", "tests/", "*.config.*"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
