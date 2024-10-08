// @ts-check
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('./accounts/login/');
  await page
    .getByLabel('Email address')
    .fill(`${process.env.PLAYWRIGHT_USERNAME}`);
  await page.getByLabel('Password').fill(`${process.env.PLAYWRIGHT_PASSWORD}`);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.locator('h1')).toContainText('Reading');

  await page.context().storageState({ path: authFile });
});
