const { test, expect } = require("@playwright/test");
test("Arabic/English, safe process text, local charts and responsive layout", async ({
  page,
}, testInfo) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.locator("#connection")).toHaveText("متصل");
  await expect(page.locator("#gpus .gpu-title")).toHaveText("A40");
  await expect(page.locator("#processes")).toContainText(
    "<script>unsafe</script>",
  );
  await expect(page.locator("#processes script")).toHaveCount(0);
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("#summary .card")).toHaveCount(8);
  await expect(page.locator("#chart-gpu")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: testInfo.outputPath("dashboard-ar.png"),
    fullPage: true,
  });
  await page.locator("#language").click();
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator("h1")).toHaveText(
    "Your server. Every resource. One view.",
  );
  await page.locator("#window").selectOption("7d");
  await expect(page.locator("#history-status")).toContainText("1800");
  await page.locator("#theme").click();
  await expect(page.locator("body")).toHaveClass("light");
  await page.screenshot({
    path: testInfo.outputPath("dashboard-en.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
