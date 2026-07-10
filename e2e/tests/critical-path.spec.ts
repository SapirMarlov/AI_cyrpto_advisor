import { expect, test } from "@playwright/test";

test("signup onboarding dashboard vote logout", async ({ page }) => {
  const email = `e2e_${Date.now()}@example.com`;
  const password = "password123";

  await page.goto("/signup");
  await expect(page.getByRole("heading", { name: "AI Crypto Advisor" })).toBeVisible();

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL(/\/onboarding/);
  await expect(page.getByText(/What crypto assets/i)).toBeVisible();

  await page.getByLabel("Bitcoin").click();
  await page.getByLabel("HODLer").click();
  await page.getByLabel("Market News").click();
  await page.getByRole("button", { name: "Finish onboarding" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: "AI Crypto Advisor" })).toBeVisible();
  await expect(page.getByText("Market news")).toBeVisible();
  await expect(page.getByText("Coin prices")).toBeVisible();
  await expect(page.getByText("AI insight")).toBeVisible();
  await expect(page.getByText("Meme of the day")).toBeVisible();

  await expect(page.getByText("E2E Bitcoin briefing")).toBeVisible();
  await page.getByRole("button", { name: "Thumbs up" }).first().click();
  // Vote success leaves no error alert on the news vote controls.
  await expect(page.locator('[role="alert"]')).toHaveCount(0);

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "AI Crypto Advisor" })).toBeVisible();
});
