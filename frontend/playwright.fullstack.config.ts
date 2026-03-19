import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './__tests__/e2e',
  testMatch: ['**/fullstack-*.spec.ts'],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 90_000,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command:
        "bash -lc 'if [ -x .venv/bin/python ]; then .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000; elif [ -x venv/bin/python ]; then venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000; else python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000; fi'",
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/health',
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: {
        E2E_MOCK_PIPELINE: 'true',
        DASHSCOPE_API_KEY: 'test-key',
      },
    },
    {
      command: 'npm run dev',
      cwd: '.',
      url: 'http://127.0.0.1:3000',
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: {
        NEXT_PUBLIC_API_URL: 'http://127.0.0.1:8000',
      },
    },
  ],
})
