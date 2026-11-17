import { defineConfig, devices } from '@playwright/test';
import { ACCOUNTS } from './e2e/account';

const port = 4310;
// The sign-in tests run on the dev server, the build that signs in on the 4CE server (ADR-0046),
// which sends /api to a throwaway 4CE server.
const devPort = 4311;
const serverPort = 4312;
const desktop = { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } };
const signIn = /sign-in\.spec\.ts$/;

export default defineConfig({
  testDir: 'e2e',
  forbidOnly: !!process.env.CI,
  use: { baseURL: `http://localhost:${port}` },
  projects: [
    { name: 'desktop', testIgnore: signIn, use: desktop },
    {
      name: 'tablet',
      testIgnore: signIn,
      use: { ...devices['Desktop Chrome'], viewport: { width: 820, height: 1180 }, hasTouch: true },
    },
    {
      name: 'server',
      testMatch: signIn,
      use: { ...desktop, baseURL: `http://localhost:${devPort}` },
    },
  ],
  webServer: [
    // Tests run against the production build, the same files 4ce-server serves.
    {
      // A demo build: until the 4CE API serves every screen the app runs on the fake data source,
      // which a plain production build refuses (src/lib/data/source.ts).
      // VITE_4CE_DEMO goes through env, not a VAR=value prefix, which cmd.exe on Windows can't run.
      command: `npm run build && npm run preview -- --port ${port} --strictPort`,
      env: { VITE_4CE_DEMO: '1' },
      port,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `node e2e/server.ts ${serverPort}`,
      env: { E2E_ACCOUNTS: JSON.stringify(ACCOUNTS) },
      url: `http://127.0.0.1:${serverPort}/api/health`,
      timeout: 120_000,
      reuseExistingServer: false,
    },
    {
      command: `npm run dev -- --port ${devPort} --strictPort`,
      env: { API_TARGET: `http://127.0.0.1:${serverPort}`, VITE_4CE_DEMO: '' },
      port: devPort,
      reuseExistingServer: false,
    },
  ],
});
