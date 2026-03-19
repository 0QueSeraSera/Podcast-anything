import { expect, test } from '@playwright/test'

test.describe('Non-mock full-stack script pipeline', () => {
  test('generates script from real GitHub repo and exposes script output', async ({ page, request }) => {
    const repoUrl = process.env.NONMOCK_E2E_REPO_URL || 'https://github.com/octocat/Hello-World'

    await page.goto('/')

    await page.getByPlaceholder(/github\.com\/user\/repository/i).fill(repoUrl)
    await page.getByRole('button', { name: /^analyze$/i }).click()

    await expect(page).toHaveURL(/\/select\?repo_id=/, { timeout: 60_000 })

    // Keep selection empty to include full repository.
    await page
      .getByPlaceholder(/focus on api flow/i)
      .fill('Focus on architecture and data flow. Skip deployment details.')
    await page.getByRole('button', { name: /^send$/i }).click()

    await page.getByRole('button', { name: /generate podcast/i }).click()
    await expect(page).toHaveURL(/\/podcast\/([^/?#]+)/, { timeout: 180_000 })

    const currentUrl = page.url()
    const match = currentUrl.match(/\/podcast\/([^/?#]+)/)
    expect(match).toBeTruthy()
    const podcastId = match![1]

    await expect(page.getByText(/chapters/i)).toBeVisible()

    const scriptResp = await request.get(`http://127.0.0.1:8000/api/v1/podcast/${podcastId}/script`)
    expect(scriptResp.ok()).toBeTruthy()

    const scriptJson = await scriptResp.json()
    expect(scriptJson.content).toContain('#')
    expect(scriptJson.content.length).toBeGreaterThan(50)
  })
})
