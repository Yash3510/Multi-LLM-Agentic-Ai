// The sign-off page on the demo build (web-screens.md, /runs/[runId]/sign-off): the run view with
// the chat's sign-off panel docked, on the same run as the chat, so a release there shows in both.
import { expect, test } from '@playwright/test';

const GATE_LINE = 'The sign-off panel opens when the run reaches the gate.';

test('a run released on its sign-off page shows released in the chat too', async ({ page }) => {
  // The fake plays the run at real pace: about fifteen seconds to the gate.
  test.slow();
  await page.goto('/c/c-0143');
  const message = page.getByRole('textbox', { name: 'Message' });
  await message.fill('Is the ratio within the limit?');
  await message.press('Enter');
  await page.getByRole('link', { name: 'View run' }).click();

  await page.getByRole('link', { name: 'Review and decide' }).click({ timeout: 45_000 });
  await expect(page).toHaveURL(/\/runs\/[\w-]+\/sign-off$/);
  const review = page.getByRole('region', { name: 'Review before release' });
  // The line for a run that hasn't reached the gate must not appear between the decision and
  // the end of the run, even for a moment, so watch the page for it while releasing.
  await page.evaluate((line) => {
    Reflect.set(window, 'sawGateLine', false);
    new MutationObserver(() => {
      if (document.body.textContent?.includes(line)) Reflect.set(window, 'sawGateLine', true);
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }, GATE_LINE);
  await review.getByRole('textbox', { name: 'Type approve to release' }).fill('approve');
  await review.getByRole('button', { name: 'Approve' }).click();
  await expect(review).toBeHidden();
  await expect(page.getByText('7 steps in')).toBeVisible();
  await expect(
    page.getByRole('tabpanel', { name: 'Sign-off details' }).getByText(/^Released by Asha Rao/),
  ).toBeVisible();
  expect(await page.evaluate(() => Reflect.get(window, 'sawGateLine'))).toBe(false);

  await page.getByRole('link', { name: 'Open the conversation' }).click();
  // The URL changes before the page is swapped in, so wait for the chat's own composer.
  await expect(message).toBeVisible();
  await expect(page.getByRole('group', { name: 'How this answer was produced' })).toBeVisible();
});

test('a decided run has no sign-off panel', async ({ page }) => {
  await page.goto('/runs/run-0142/sign-off');
  await expect(page.getByRole('tablist', { name: 'Agent chain' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Review before release' })).toHaveCount(0);
  await expect(page.getByText(GATE_LINE)).toHaveCount(0);
});
