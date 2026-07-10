import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const e2eDbPath = path.join(rootDir, "e2e", ".tmp", "e2e.db");
const venvPython = path.join(
  rootDir,
  ".venv",
  process.platform === "win32" ? "Scripts" : "bin",
  process.platform === "win32" ? "python.exe" : "python",
);
const backendRunner = path.join(rootDir, "e2e", "run_backend.py");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5174",
    trace: "on-first-retry",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command: `${JSON.stringify(venvPython)} ${JSON.stringify(backendRunner)}`,
      cwd: rootDir,
      url: "http://127.0.0.1:5000/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        FLASK_ENV: "development",
        PYTHONPATH: path.join(rootDir, "backend"),
        DATABASE_PATH: e2eDbPath,
        SECRET_KEY: "e2e-secret-key",
        PRICE_PROVIDER: "static",
        NEWS_PROVIDER: "static",
        AI_PROVIDER: "template",
        MEME_PROVIDER: "static",
        CORS_ORIGINS: "http://127.0.0.1:5174,http://localhost:5174",
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
      cwd: path.join(rootDir, "frontend"),
      url: "http://127.0.0.1:5174",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_BASE_URL: "http://127.0.0.1:5000",
      },
    },
  ],
});
