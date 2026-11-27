// Evidence review on the demo build (web-screens.md, /evidence/[evidenceId]): what was read from a
// page, checked against the page itself, reached from the run view's Analyst stage.
import { expect, test } from '@playwright/test';

const REPORT = 'CASE-0142 second batch report';

test("the stored run's evidence opens from its Analyst stage, boxes in step with the list", async ({
  page,
}) => {
  await page.goto('/runs/run-0142');
  await page.getByRole('tab', { name: /^Analyst/ }).click();
  await page.getByRole('link', { name: `Review what was read from ${REPORT}` }).click();
  await expect(page).toHaveURL(/\/evidence\/ev-0142-2$/);
  await expect(page.getByRole('img', { name: `Page 1 of ${REPORT}` })).toBeVisible();
  await page.getByRole('button', { name: 'Box 2: Ratio, 82.5 %' }).click();
  const row = page.getByRole('button', { name: /^2 Ratio/ });
  await expect(row).toHaveAttribute('aria-pressed', 'true');
  await expect(row).toContainText('check');
});

test('an address with ?box= opens the evidence with that box selected', async ({ page }) => {
  await page.goto('/evidence/ev-0142-2?box=3');
  await expect(page.getByRole('button', { name: 'Box 3: Duration, 42 s' })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
});

test('?page= opens a page, and ?box= opens the page its box is on', async ({ page }) => {
  await page.goto('/evidence/ev-0142-2?page=2');
  await expect(page.getByRole('img', { name: `Page 2 of ${REPORT}` })).toBeVisible();
  await expect(page.getByText('Page 2 of 2')).toBeVisible();
  await page.goto('/evidence/ev-0142-2?box=4');
  await expect(page.getByRole('button', { name: 'Box 4: Temperature, 21 °C' })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
});

test('zoomed in by keyboard, the page pans with the arrow keys from a box', async ({ page }) => {
  await page.goto('/evidence/ev-0142-2');
  await page.getByRole('button', { name: 'Zoom in' }).focus();
  await page.keyboard.press('Enter');
  await page.keyboard.press('Enter');
  await expect(page.getByText('Zoom 200%')).toBeVisible();
  const frame = page.getByRole('img', { name: `Page 1 of ${REPORT}` }).locator('xpath=../..');
  await page.getByRole('button', { name: 'Box 1: Batch, Second' }).focus();
  const before = await frame.evaluate((element) => element.scrollTop);
  await page.keyboard.press('ArrowDown');
  await expect.poll(() => frame.evaluate((element) => element.scrollTop)).toBeGreaterThan(before);
});

test('Verify says who verified an observation, still shown on another page and back', async ({
  page,
}) => {
  await page.goto('/evidence/ev-0142-2');
  const verified = page.getByText(/^Verified by Asha Rao, /);
  await expect(verified).toHaveCount(1);
  await page.getByRole('button', { name: 'Verify 2: Ratio' }).click();
  await expect(verified).toHaveCount(2);
  await page.getByRole('button', { name: 'Next page' }).click();
  await page.getByRole('button', { name: 'Previous page' }).click();
  await expect(verified).toHaveCount(2);
  await expect(page.getByRole('button', { name: 'Verify 2: Ratio' })).toHaveCount(0);
});
