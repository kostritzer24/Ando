import { defineConfig, devices } from "@playwright/test";

/**
 * No está conectado a CI todavía (docs/fase-3-cimientos-plan.md, sección
 * 4): se agrega el job cuando exista el primer flujo real que probar con
 * el backend y el frontend levantados juntos. Por ahora se corre a mano
 * con `npm run e2e` contra un backend local con la semilla de la Fase 3
 * (`manage.py seed_fase3`).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: {
    baseURL: "http://localhost:5173",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
  },
});
