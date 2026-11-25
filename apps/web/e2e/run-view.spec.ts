// The run view on the demo build (web-screens.md, /runs/[runId]): a stored run's stages open one
// at a time from the rail, by pointer or keyboard, above its receipt; a question asked in the
// chat opens there live and can be cancelled, and the chat still has it afterwards.
import { expect, test } from '@playwright/test';

test('a stored run opens each stage from the rail, above its receipt', async ({ page }) => {
  await page.goto('/runs/run-0142');
  const rail = page.getByRole('tablist', { name: 'Agent chain' });
  await expect(rail.getByRole('tab', { name: /^Sign-off/ })).toHaveAttribute(
    'aria-selected',
    'true',
  );
  await expect(page.getByRole('group', { name: 'How this answer was produced' })).toBeVisible();

  await rail.getByRole('tab', { name: /^Analyst/ }).click();
  const analyst = page.getByRole('tabpanel', { name: 'Analyst details' });
  await expect(analyst.getByText('Reader: searching the knowledge base')).toBeVisible();
  await expect(analyst.getByText('knowledge_search')).toBeVisible();
  await expect(analyst.getByRole('button', { name: 'Toggle 2 sources' })).toBeVisible();

  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Enter');
  const author = page.getByRole('tabpanel', { name: 'Author details' });
  await expect(author.getByRole('cell', { name: '82.5 %' })).toBeVisible();
});

test('a question asked in the chat opens in its run view live, and Cancel stops it', async ({
  page,
}) => {
  await page.goto('/c/c-0143');
  const message = page.getByRole('textbox', { name: 'Message' });
  await message.fill('Is the ratio within the limit?');
  await message.press('Enter');

  await page.getByRole('link', { name: 'View run' }).click();
  await expect(page).toHaveURL(/\/runs\/[\w-]+$/);
  const cancel = page.getByRole('button', { name: 'Cancel run' });
  await cancel.click();
  await expect(page.getByRole('button', { name: 'Toggle status history' })).toHaveText(
    /^Stopped after/,
  );
  await expect(cancel).toBeHidden();

  await page.getByRole('link', { name: 'Open the conversation' }).click();
  // The URL changes before the page is swapped in, so wait for the chat's own composer.
  await expect(message).toBeVisible();
  await expect(page.getByText('Is the ratio within the limit?')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Toggle status history' }).last()).toHaveText(
    /^Stopped after/,
  );
});

test('a run that does not exist is not found', async ({ page }) => {
  await page.goto('/runs/no-such-run');
  await expect(page.getByText('Run not found')).toBeVisible();
});
