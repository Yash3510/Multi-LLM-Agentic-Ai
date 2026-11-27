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
