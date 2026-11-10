const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./tests/browser",
  timeout: 30000,
  use: { baseURL: "http://127.0.0.1:5501", headless: true },
  webServer: {
    command:
      ".venv/bin/python -m uvicorn tests.ui_app:app --host 127.0.0.1 --port 5501 --no-access-log",
    url: "http://127.0.0.1:5501/",
    reuseExistingServer: false,
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1100 } } },
    {
      name: "mobile",
      use: { viewport: { width: 390, height: 844 }, isMobile: true },
    },
  ],
});
