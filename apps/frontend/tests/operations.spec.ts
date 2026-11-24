import { test, expect } from "@playwright/test";

test("command centre displays backend data, map and exports", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Command centre", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("CAMERA NETWORK", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "CAM-01", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "CAM-02", exact: true }).click();
  await expect(page.getByLabel("Select camera")).toHaveValue("cam-02");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export data", exact: true }).click();
  expect((await download).suggestedFilename()).toContain(".json");
  expect(errors).toEqual([]);
  await page.screenshot({
    path: "../../docs/screenshots/command-centre.jpg",
    fullPage: true,
  });
});

test("synthetic scenario creates linked incidents, investigations and operator reviews", async ({
  page,
  request,
}) => {
  await request.post("/api/v1/demo/reset", { data: {} });
  await request.post("/api/v1/demo/control", { data: { speed: 5 } });
  await expect
    .poll(
      async () => {
        const response = await request.get("/api/v1/snapshot");
        return (await response.json()).correlations.length;
      },
      { timeout: 45000 },
    )
    .toBeGreaterThan(0);
  await request.post("/api/v1/demo/control", { data: { paused: true } });
  await page.goto("/");
  await expect(page.getByText("CAMERA NETWORK", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^Incidents/ }).click();
  await page.locator(".register-item").first().click();
  await expect(
    page.getByRole("heading", { name: "Observed evidence" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Investigate incident", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Grounded observations" }),
  ).toBeVisible();
  await expect(page.locator(".grounded-claim a").first()).toContainText("REF");
  await page
    .getByPlaceholder("Record your assessment and any missing context…")
    .fill("Synthetic E2E verification");
  await page.getByRole("button", { name: "Verify", exact: true }).click();
  await expect(page.locator(".detail-top .badge.verified")).toBeVisible();
  await page.getByRole("button", { name: "Resolve", exact: true }).click();
  await expect(page.locator(".detail-top .badge.resolved")).toBeVisible();
  await page.screenshot({
    path: "../../docs/screenshots/investigation.jpg",
    fullPage: true,
  });
});

test("surveillance, forecasts and configurable ROI render live data", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("CAMERA NETWORK", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Surveillance", exact: true }).click();
  await expect(page.locator(".surveillance-grid .panel")).toHaveCount(4);
  await page
    .getByRole("button", { name: "Inspect East concourse", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Intelligence", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Zone risk comparison" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(4);
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .locator(".zone-list")
    .getByRole("button", { name: "Configure" })
    .first()
    .click();
  await expect(
    page.getByLabel("ROI polygon · normalized [x,y] coordinates"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(
    page.getByRole("button", { name: "Save intelligence settings" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Save intelligence settings" })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Intelligence settings saved",
  );
});

test("mobile layout keeps navigation and camera workflows usable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("CAMERA NETWORK", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Surveillance", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Add camera", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add camera", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../../docs/screenshots/mobile-surveillance.jpg",
    fullPage: true,
  });
});
