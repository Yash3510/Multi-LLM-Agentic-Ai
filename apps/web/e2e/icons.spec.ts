import { expect, test, type Page } from '@playwright/test';

// Every icon sits inside its button, link or menu row; an icon-only one is centred in it.
async function misfits(page: Page) {
  return page.evaluate(() => {
    const out: string[] = [];
    for (const box of document.querySelectorAll('button, a, [role=menuitem]')) {
      const r = box.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      for (const svg of box.querySelectorAll('svg')) {
        const q = svg.getBoundingClientRect();
        if (!q.width || getComputedStyle(svg.parentElement ?? svg).opacity === '0') continue;
        const spill = Math.max(
          r.left - q.left,
          q.right - r.right,
          r.top - q.top,
          q.bottom - r.bottom,
        );
        const off = box.textContent?.trim()
          ? 0
          : Math.abs((q.top + q.bottom) / 2 - (r.top + r.bottom) / 2);
        if (spill > 0.5 || off > 1.5) {
          const name = (box.getAttribute('aria-label') ?? box.textContent ?? '').trim();
          out.push(`${name.slice(0, 40)}: spill ${spill.toFixed(1)}, off-centre ${off.toFixed(1)}`);
        }
      }
    }
    return out;
  });
}

test('icons fit their buttons on /ui', async ({ page }) => {
  await page.goto('/ui');
  await page.waitForLoadState('networkidle');
  expect(await misfits(page)).toEqual([]);
});

test('icons fit their buttons on the main screens', async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto('/auth');
  await page.waitForSelector('input[type="password"]');
  // The demo build runs on the fake source: any account signs in; these are not real credentials.
  const name = page.locator('input[autocomplete="name"]');
  if (await name.count()) await name.fill('Asha Rao');
  await page.locator('input[type="email"]').fill('asha.rao@example.test');
  await page.locator('input[type="password"]').fill('demo-only-1');
  await page.locator('button[type="submit"]').first().click();
  await page.waitForURL((url) => !url.pathname.startsWith('/auth'));
  for (const route of ['/', '/workspace/models', '/admin/users', '/notes', '/calendar']) {
    await page.goto(route);
    await page.waitForLoadState('networkidle');
    expect(await misfits(page), route).toEqual([]);
  }
});
