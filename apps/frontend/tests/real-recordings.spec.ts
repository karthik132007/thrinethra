import { test, expect } from "@playwright/test";

test("default workspace measures downloaded recordings instead of generating simulation", async ({
  page,
  request,
}) => {
  const before = await request.get("/api/v1/snapshot");
  const data = await before.json();
  expect(data.demo.enabled).toBe(false);
  expect(data.cameras).toHaveLength(4);
  expect(
    data.cameras.every((c: { source: string }) => c.source === "video"),
  ).toBe(true);
  await page.goto("/");
  await expect(
    page.getByText("REAL VIDEO INFERENCE", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Replay recordings", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "REC-WEST", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Replay recordings", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const response = await request.get("/api/v1/snapshot");
        return (await response.json()).latest.length;
      },
      { timeout: 90000 },
    )
    .toBe(4);
  const latest = await (await request.get("/api/v1/snapshot")).json();
  expect(
    latest.latest.every(
      (v: { provenance: string }) => v.provenance === "video_inference",
    ),
  ).toBe(true);
  expect(
    latest.latest.some(
      (v: { metrics: { count: number } }) => v.metrics.count > 0,
    ),
  ).toBe(true);
  await expect(page.getByText("SIMULATION", { exact: true })).toHaveCount(0);
  await page.screenshot({
    path: "../../docs/screenshots/real-command-centre.jpg",
    fullPage: true,
  });
});

test("operators inspect original footage and actual bounding boxes, forecasts and incident references", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await expect(
    page.getByText("REAL VIDEO INFERENCE", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Surveillance", exact: true }).click();
  await expect(page.locator(".surveillance-grid .panel")).toHaveCount(4);
  await expect(
    page.getByAltText("MOT17-04 · west view annotated feed"),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect MOT17-04 · west view", exact: true })
    .click();
  await page
    .getByText("Play source recording and inspect metadata", { exact: true })
    .click();
  await expect(page.getByLabel("Original recorded footage")).toBeVisible();
  await expect
    .poll(
      () =>
        page
          .getByLabel("Original recorded footage")
          .evaluate((v: HTMLVideoElement) => v.readyState),
      { timeout: 120000 },
    )
    .toBeGreaterThan(0);
  await expect(
    page.getByRole("link", { name: "Publisher source", exact: true }),
  ).toHaveAttribute("href", /motchallenge/);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.screenshot({
    path: "../../docs/screenshots/real-surveillance.jpg",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Intelligence", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Zone risk comparison" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(4);
  await expect
    .poll(
      async () => {
        const s = await (await request.get("/api/v1/snapshot")).json();
        return s.incidents.filter(
          (i: { event: { provenance: string } }) =>
            i.event.provenance === "video_inference",
        ).length;
      },
      { timeout: 60000 },
    )
    .toBeGreaterThan(0);
  await page.getByRole("button", { name: "Incidents", exact: true }).click();
  await page.locator(".register-item").first().click();
  await expect(
    page.getByRole("heading", { name: "Observed evidence" }),
  ).toBeVisible();
  expect(await page.locator(".evidence-card img").count()).toBeGreaterThan(0);
  await page
    .getByPlaceholder("What supports this alert, and what remains uncertain?")
    .fill("What measured evidence supports this alert?");
  await page
    .getByRole("button", {
      name: /^(Investigate incident|Re-run investigation)$/,
    })
    .click();
  await expect(
    page.getByRole("heading", { name: "Grounded observations" }),
  ).toBeVisible({ timeout: 150000 });
  await expect(page.locator(".grounded-claim a").first()).toContainText("REF");
  await page
    .getByPlaceholder("Record your assessment and any missing context…")
    .fill("Real-video browser verification; no response dispatched.");
  await page.getByRole("button", { name: "Verify", exact: true }).click();
  await expect(page.locator(".detail-top .badge.verified")).toBeVisible();
  await page.screenshot({
    path: "../../docs/screenshots/real-investigation.jpg",
    fullPage: true,
  });
});

test("real-video controls and source metadata remain usable on mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByText("REAL VIDEO INFERENCE", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Surveillance", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Add camera", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../../docs/screenshots/real-mobile.jpg",
    fullPage: true,
  });
});
