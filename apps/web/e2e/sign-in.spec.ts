// Signing in against a real 4CE server (e2e/server.ts) through the dev server's /api proxy: the
// server's own messages, staying signed in across a reload, and signing out.
import { expect, test, type Page } from '@playwright/test';
import { ACCOUNTS } from './account';

const [ada, grace] = ACCOUNTS;
const WRONG = 'The email or password is wrong.';

async function signIn(page: Page, email: string, password: string) {
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

async function signOut(page: Page) {
  await page.getByRole('button', { name: `User menu: ${ada.name}` }).click();
  await page.getByRole('menuitem', { name: 'Sign Out' }).click();
}

test('signs in, stays signed in across a reload, and signs out', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\/auth$/);

  await signIn(page, ada.email, 'not the password');
  await expect(page.getByRole('alert')).toHaveText(WRONG);
  await expect(page.getByLabel('Email')).toHaveValue(ada.email);
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('');

  await signIn(page, ada.email, ada.password);
  const menu = page.getByRole('button', { name: `User menu: ${ada.name}` });
  await expect(menu).toBeVisible();
  await page.reload();
  await expect(menu).toBeVisible();

  // A sign-out the server never receives says so, and the person stays signed in.
  await page.route('**/api/auth/signout', (route) => route.abort());
  await signOut(page);
  await expect(page.getByText("Can't reach the 4CE server.")).toBeVisible();
  await expect(menu).toBeVisible();
  await page.unroute('**/api/auth/signout');

  await signOut(page);
  await expect(page).toHaveURL(/\/auth$/);
  await page.reload();
  await expect(page).toHaveURL(/\/auth$/);
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
});

test('a locked account says when to try again', async ({ page }) => {
  await page.goto('/auth');
  // Typing clears the last message, so each one shown is that attempt's answer.
  for (const attempt of [1, 2, 3, 4, 5]) {
    await signIn(page, grace.email, `wrong password ${attempt}`);
    await expect(page.getByRole('alert')).toHaveText(WRONG);
  }
  await signIn(page, grace.email, grace.password);
  await expect(page.getByRole('alert')).toHaveText(
    'Too many failed sign-ins. Try again in 15 minutes.',
  );
});
