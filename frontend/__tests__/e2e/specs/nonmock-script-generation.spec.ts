import { expect, test } from '@playwright/test'

test.describe('Non-mock full-stack script pipeline', () => {
  test('generates script from real GitHub repo and exposes script output', async ({ page, request }) => {
    test.setTimeout(600_000)
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
    await page.getByRole('checkbox').first().check()
    await expect(page.getByRole('button', { name: /generate podcast/i })).toBeEnabled()

    await page.getByRole('button', { name: /generate podcast/i }).click()
    await expect
      .poll(() => page.url(), { timeout: 420_000 })
      .toMatch(/\/(generate\?podcast_id=|podcast\/)([^/?#]+)/)

    const currentUrl = page.url()
    const podcastRouteMatch = currentUrl.match(/\/podcast\/([^/?#]+)/)
    const generateRouteMatch = currentUrl.match(/[?&]podcast_id=([^&]+)/)
    const podcastId = podcastRouteMatch?.[1] || generateRouteMatch?.[1]
    expect(podcastId).toBeTruthy()
    const resolvedPodcastId = podcastId as string

    await expect
      .poll(
        async () => {
          const statusResp = await request.get(
            `http://127.0.0.1:8000/api/v1/podcast/${resolvedPodcastId}/status`
          )
          if (!statusResp.ok()) {
            return `http-${statusResp.status()}`
          }
          const statusJson = await statusResp.json()
          return String(statusJson.status || '').toLowerCase()
        },
        { timeout: 420_000 }
      )
      .toBe('completed')

    const audioResp = await request.get(`http://127.0.0.1:8000/api/v1/podcast/${resolvedPodcastId}/audio`)
    expect(audioResp.ok()).toBeTruthy()
    const audioBody = await audioResp.body()
    expect(audioBody.length).toBeGreaterThan(512)

    await page.goto(`/podcast/${resolvedPodcastId}`)
    await expect(page.getByText(/chapters/i)).toBeVisible()

    const scriptResp = await request.get(
      `http://127.0.0.1:8000/api/v1/podcast/${resolvedPodcastId}/script`
    )
    expect(scriptResp.ok()).toBeTruthy()

    const scriptJson = await scriptResp.json()
    expect(scriptJson.content).toContain('#')
    expect(scriptJson.content.length).toBeGreaterThan(50)
  })
})
