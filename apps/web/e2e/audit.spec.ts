// The audit sheet on the demo build (web-screens.md, /runs/[runId]/audit): a decided run as a
// printed record, opened from its run view's receipt.
import { expect, test } from '@playwright/test';

test("a decided run's audit sheet, opened from its run view, is the record to print", async ({
  page,
}) => {
  await page.goto('/runs/run-0142');
  await page.getByRole('button', { name: 'Audit' }).click();
  const sheet = page.getByRole('article', { name: 'Audit sheet' });
  await expect(sheet).toBeVisible();
  await expect(page).toHaveURL(/\/runs\/run-0142\/audit$/);
  for (const text of [
    'Internal',
    'Released by Asha Rao',
    '0604 685d 984d 94b4',
    'R2 · Ratio within its limit',
    '3f9a 21c0 7be4 d815',
    'Ledger entry 1042',
  ])
    await expect(sheet).toContainText(text);
  await expect(page.getByRole('button', { name: 'Print' })).toHaveCount(1);
});
