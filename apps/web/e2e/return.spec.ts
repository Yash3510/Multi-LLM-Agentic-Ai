// Return with a reason on the demo build (web-screens.md, the sign-off panel): the person at the
// gate sends the work back with a reason from the chat's panel, and the reason shows under the
// answer and in the run view's Sign-off stage.
import { expect, test } from '@playwright/test';

const REASON = 'Say how the ratio was rounded.';

test('a run returned from the chat shows its reason in the chat and in its run view', async ({
  page,
}) => {
  // The fake plays the run at real pace: about fifteen seconds to the gate.
  test.slow();
  await page.goto('/c/c-0143');
  const message = page.getByRole('textbox', { name: 'Message' });
  await message.fill('Is the ratio within the limit?');
  await message.press('Enter');

  const review = page.getByRole('region', { name: 'Review before release' });
  await review.getByRole('button', { name: 'Return' }).click({ timeout: 45_000 });
  await review.getByRole('textbox', { name: 'Why it goes back' }).fill(REASON);
  await review.getByRole('button', { name: 'Return it' }).click();
  await expect(review).toBeHidden();
  await expect(page.getByText(`Returned by Asha Rao: ${REASON}`)).toBeVisible();

  await page.getByRole('link', { name: 'View run' }).click();
  await expect(
    page.getByRole('tabpanel', { name: 'Sign-off details' }).getByText(/^Returned by Asha Rao/),
  ).toContainText(REASON);
  await expect(page.getByRole('tab', { name: /^Sign-off/ })).toHaveAccessibleName(/returned/);
});
