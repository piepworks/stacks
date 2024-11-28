// @ts-check
import { test, expect } from '@playwright/test';

// Don't use default, logged-in state
test.use({ storageState: { cookies: [], origins: [] } });

test('log in page', async ({ page }) => {
  await page.goto('./');

  await expect(page).toHaveTitle('Stacks.');
  await page.getByRole('link', { name: 'Log in' }).click();
  await expect(page).toHaveURL('./accounts/login/');
});
