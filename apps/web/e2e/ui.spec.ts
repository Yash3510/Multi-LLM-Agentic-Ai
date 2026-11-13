// Smoke test for the design reference: it renders in both themes, on desktop and tablet, without a
// single console error or uncaught exception.
import { expect, test } from '@playwright/test';

for (const theme of ['light', 'dark'] as const) {
  test(`/ui renders in ${theme} with no console errors`, async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));

    // The stored choice is what app.html reads before first paint.
    await page.addInitScript((value) => {
      try {
        localStorage.setItem('4ce.theme', value);
      } catch {
        // Storage blocked: the test below then fails on the theme, which is the right signal.
      }
    }, theme);

    await page.goto('/ui');
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(page.getByRole('heading', { level: 1, name: 'Design reference' })).toBeVisible();
    expect(await page.locator('main section h2').count()).toBeGreaterThanOrEqual(6);

    // Run every motion demo to the end, so a broken one shows up as an error here. Working dots and
    // skeleton sheens loop by design, so only finite animations have to finish.
    await page.getByRole('button', { name: 'Replay motion' }).click();
    await page.waitForFunction(
      () =>
        document
          .getAnimations()
          .every((animation) => animation.effect?.getComputedTiming().iterations === Infinity),
      null,
      { timeout: 10_000 },
    );

    expect(errors).toEqual([]);
  });
}
