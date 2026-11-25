// The chat on the demo build follows its run (web-data-contract.md): a run whose connection drops
// picks up again and reaches sign-off, and typing approve releases it with a receipt.
import { expect, test } from '@playwright/test';

test('a dropped connection resumes, and approve releases the answer', async ({ page }) => {
  // The fake plays the run at real pace: about fifteen seconds to sign-off.
  test.slow();
  await page.goto('/c/c-0143');
  const message = page.getByRole('textbox', { name: 'Message' });
  await message.fill('What happens if the connection drops?');
  await message.press('Enter');

  const review = page.getByRole('region', { name: 'Review before release' });
  await expect(review).toBeVisible({ timeout: 40_000 });
  await review.getByRole('textbox', { name: 'Type approve to release' }).fill('approve');
  await review.getByRole('button', { name: 'Approve' }).click();

  await expect(review).toBeHidden();
  await expect(page.getByRole('group', { name: 'How this answer was produced' })).toBeVisible();
});
