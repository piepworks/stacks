// @ts-check
import { test, expect } from '@playwright/test';

test('settings page / light mode', async ({ page }) => {
  await page.goto('./settings');
  await page.emulateMedia({ colorScheme: 'light' });
  await expect(page).toHaveScreenshot('settings-page-light.png', {
    fullPage: true,
  });
});

test('settings page / dark mode', async ({ page }) => {
  await page.goto('./settings');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page).toHaveScreenshot('settings-page-dark.png', {
    fullPage: true,
  });
});
