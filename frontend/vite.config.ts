/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    // `e2e/` son pruebas de Playwright (`npm run e2e`), no de Vitest —
    // sin este exclude, Vitest las recoge también por el patrón
    // `*.spec.ts` por omisión y truena porque no corren bajo su runner.
    exclude: ["**/node_modules/**", "e2e/**"],
  },
});
