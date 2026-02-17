import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Mock login endpoint
  await page.route('**/api/v1/auth/login', async route => {
    const json = {
      success: true,
      data: {
        access_token: 'fake_jwt_token',
        refresh_token: 'fake_refresh_token',
        token_type: 'bearer',
        scopes: ['read', 'write'],
        user: { id: '1', email: 'harry@hogwarts.edu' }
      }
    };
    await route.fulfill({ json });
  });

  // Mock validate endpoint
  await page.route('**/api/v1/auth/validate', async route => {
    const json = {
      success: true,
      data: {
        valid: true,
        user_id: '1',
        email: 'harry@hogwarts.edu',
        scopes: ['read', 'write']
      }
    };
    await route.fulfill({ json });
  });
});

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Hogwarts Registry')).toBeVisible();
});

test('login flow', async ({ page }) => {
  await page.goto('/');

  // Fill login form
  await page.getByLabel('Wizard Name').fill('Harry Potter');
  await page.getByLabel('Secret Incantation').fill('Alohomora');

  // Click login
  await page.click('button[type="submit"]');

  // Should redirect to dashboard and show user info/depart button
  // We mock validate so it should stay logged in.
  await expect(page.getByText('Depart')).toBeVisible();
});
