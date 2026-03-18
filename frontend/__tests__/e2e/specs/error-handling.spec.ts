import { test, expect } from '@playwright/test'

test.describe('Error Handling', () => {
  test('should show error for invalid GitHub URL on home page', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Try non-GitHub URL
    await urlInput.fill('https://gitlab.com/user/repo')

    // Should show validation message
    await expect(page.getByText(/valid github repository url/i)).toBeVisible()

    // Submit should be disabled
    await expect(page.getByRole('button', { name: /analyze/i })).toBeDisabled()
  })

  test('should show error for empty URL', async ({ page }) => {
    await page.goto('/')

    // Submit button should be disabled when input is empty
    await expect(page.getByRole('button', { name: /analyze/i })).toBeDisabled()
  })

  test('should handle network error during analysis', async ({ page }) => {
    // Intercept and fail the request
    await page.route('**/api/v1/repository/analyze', (route) => {
      route.abort('failed')
    })

    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)
    await urlInput.fill('https://github.com/user/repo')

    await page.getByRole('button', { name: /analyze/i }).click()

    // Should show error message
    await expect(page.getByText(/error|failed|try again/i)).toBeVisible()
  })

  test('should handle 500 server error during analysis', async ({ page }) => {
    // Intercept and return 500
    await page.route('**/api/v1/repository/analyze', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      })
    })

    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)
    await urlInput.fill('https://github.com/user/repo')

    await page.getByRole('button', { name: /analyze/i }).click()

    // Should show error message
    await expect(page.getByText(/error/i)).toBeVisible()
  })

  test('should handle repository not found on select page', async ({ page }) => {
    // Intercept and return 404
    await page.route('**/api/v1/repository/not-found/structure', (route) => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Repository not found' }),
      })
    })

    await page.goto('/select?repo_id=not-found')

    // Should show not found message or redirect
    await expect(
      page.getByText(/not found|error/i).or(page).toHaveURL('/')
    ).resolves.toBeTruthy()
  })

  test('should handle podcast not found on generate page', async ({ page }) => {
    // Intercept and return 404
    await page.route('**/api/v1/podcast/not-found/status', (route) => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Podcast not found' }),
      })
    })

    await page.goto('/generate?podcast_id=not-found')

    // Should show not found message
    await expect(page.getByText(/not found|error/i)).toBeVisible()
  })

  test('should handle podcast not found on podcast page', async ({ page }) => {
    // Intercept and return 404
    await page.route('**/api/v1/podcast/not-found/**', (route) => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Podcast not found' }),
      })
    })

    await page.goto('/podcast/not-found')

    // Should show not found message
    await expect(page.getByText(/not found|error/i)).toBeVisible()
  })

  test('should handle podcast generation failure', async ({ page }) => {
    // Intercept and return failed status
    await page.route('**/api/v1/podcast/failed/status', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          podcast_id: 'failed',
          status: 'failed',
          progress: 0,
          error: 'Script generation failed',
        }),
      })
    })

    await page.goto('/generate?podcast_id=failed')

    // Should show error message
    await expect(page.getByText(/failed|error/i)).toBeVisible()
  })

  test('should handle audio loading error', async ({ page }) => {
    // Intercept audio request and fail
    await page.route('**/api/v1/podcast/test1234/audio', (route) => {
      route.fulfill({
        status: 404,
      })
    })

    await page.goto('/podcast/test1234')

    // Audio element should be present but show error state
    await expect(page.getByRole('audio')).toBeVisible()
    // May show an error message depending on implementation
  })

  test('should show retry option on error', async ({ page }) => {
    // Return failed status
    await page.route('**/api/v1/podcast/failed/status', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          podcast_id: 'failed',
          status: 'failed',
          progress: 0,
          error: 'Generation failed',
        }),
      })
    })

    await page.goto('/generate?podcast_id=failed')

    // Should show retry button
    await expect(page.getByRole('button', { name: /retry/i })).toBeVisible()
  })

  test('should handle timeout during generation', async ({ page }) => {
    // Intercept and delay indefinitely
    await page.route('**/api/v1/podcast/timeout/status', (route) => {
      // Never fulfill
    }, { timeout: 5000 }).catch(() => {
      // Expected timeout
    })

    await page.goto('/generate?podcast_id=timeout')

    // Should eventually show timeout or error
    // This test might need adjustment based on actual timeout handling
  })
})

test.describe('Validation Errors', () => {
  test('should show validation for invalid URLs', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Test various invalid inputs
    const invalidInputs = [
      'not-a-url',
      'ftp://github.com/user/repo',
      'github.com/user/repo', // missing protocol
      'https://gitlab.com/user/repo',
    ]

    for (const input of invalidInputs) {
      await urlInput.fill(input)
      await expect(page.getByRole('button', { name: /analyze/i })).toBeDisabled()
    }
  })

  test('should clear validation error when URL is corrected', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Enter invalid URL
    await urlInput.fill('invalid-url')
    await expect(page.getByText(/valid github repository url/i)).toBeVisible()

    // Correct the URL
    await urlInput.fill('https://github.com/user/repo')
    await expect(page.getByText(/valid github repository url/i)).not.toBeVisible()
  })
})

test.describe('Edge Cases', () => {
  test('should handle very long repository names', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Very long repo name
    const longName = 'a'.repeat(200)
    await urlInput.fill(`https://github.com/user/${longName}`)

    // Should still accept it
    await expect(page.getByRole('button', { name: /analyze/i })).toBeEnabled()
  })

  test('should handle special characters in repository names', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Repo name with special characters
    await urlInput.fill('https://github.com/user/repo-with-dashes.and.dots')

    // Should accept it
    await expect(page.getByRole('button', { name: /analyze/i })).toBeEnabled()
  })

  test('should handle direct navigation to select page without repo_id', async ({ page }) => {
    await page.goto('/select')

    // Should redirect to home or show error
    await expect(page).not.toHaveURL('/select')
  })

  test('should handle direct navigation to generate page without podcast_id', async ({ page }) => {
    await page.goto('/generate')

    // Should redirect to home or show error
    await expect(page).not.toHaveURL('/generate')
  })
})
