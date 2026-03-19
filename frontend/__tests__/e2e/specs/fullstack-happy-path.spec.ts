import { expect, test } from '@playwright/test'

test.describe('Full-stack E2E happy path', () => {
  test('pastes URL, scopes content, and generates podcast', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('heading', { name: /podcast-anything/i })).toBeVisible()

    await page
      .getByPlaceholder(/github\.com\/user\/repository/i)
      .fill('https://github.com/octocat/Hello-World')

    await page.getByRole('button', { name: /^analyze$/i }).click()

    await expect(page).toHaveURL(/\/select\?repo_id=/)
    await expect(page.getByText(/select files/i)).toBeVisible()

    await page.getByRole('button', { name: /main\.py/i }).click()
    await expect(page.getByText(/1 file selected/i)).toBeVisible()

    await page
      .getByPlaceholder(/focus on api flow/i)
      .fill('Focus on backend API flow and skip deployment details.')
    await page.getByRole('button', { name: /^send$/i }).click()

    await page.getByRole('button', { name: /generate podcast/i }).click()
    await expect(page).toHaveURL(/\/podcast\//, { timeout: 30_000 })

    const audio = page.locator('audio')
    await expect(audio).toHaveCount(1)
    await expect(audio).toHaveAttribute('src', /\/api\/v1\/podcast\/.+\/audio/)
    await expect(page.getByText(/chapters/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /core concepts/i })).toBeVisible()
  })
})
