import { defineConfig, devices } from '@playwright/test';

const port = 4310;

export default defineConfig({
  testDir: 'e2e',
  forbidOnly: !!process.env.CI,
  use: { baseURL: `http://localhost:${port}` },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'tablet',
      use: { ...devices['Desktop Chrome'], viewport: { width: 820, height: 1180 }, hasTouch: true },
    },
  ],
  // Tests run against the production build, the same files 4ce-server serves.
  webServer: {
    // A demo build: until the 4CE API client exists the app runs on the fake data source, which a
    // plain production build refuses (src/lib/data/source.ts).
    command: `VITE_4CE_DEMO=1 npm run build && npm run preview -- --port ${port} --strictPort`,
    port,
    reuseExistingServer: !process.env.CI,
  },
});
