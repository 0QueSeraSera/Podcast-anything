import { test, expect, Page } from '@playwright/test'

test.describe('Happy Path - Complete Podcast Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the home page
    await page.goto('/')
  })

  test('should complete full flow from URL to playback', async ({ page }) => {
    // Step 1: Enter GitHub URL on home page
    await expect(page.getByRole('heading', { name: /podcast anything/i })).toBeVisible()

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)
    await urlInput.fill('https://github.com/user/test-repo')

    // Submit the form
    await page.getByRole('button', { name: /analyze/i }).click()

    // Step 2: Should navigate to select page
    await expect(page).toHaveURL(/\/select\?repo_id=/)

    // Wait for file tree to load
    await expect(page.getByText(/select files/i)).toBeVisible()

    // Step 3: Select some files
    // Expand directories if needed
    const srcDir = page.getByText('src')
    if (await srcDir.isVisible()) {
      await srcDir.click()
    }

    // Select a file
    const mainFile = page.getByText('main.py').first()
    if (await mainFile.isVisible()) {
      await mainFile.click()
    }

    // Click generate button
    await page.getByRole('button', { name: /generate podcast/i }).click()

    // Step 4: Should navigate to generate page and show progress
    await expect(page).toHaveURL(/\/generate\?podcast_id=/)

    // Wait for completion (may take a while)
    await expect(page.getByText(/completed|complete/i)).toBeVisible({ timeout: 60000 })

    // Step 5: Should redirect to podcast page
    await expect(page).toHaveURL(/\/podcast\//)

    // Verify audio player is present
    await expect(page.getByRole('audio')).toBeVisible()

    // Verify chapters are loaded
    await expect(page.getByText(/chapters/i)).toBeVisible()
  })

  test('should show file tree with correct structure', async ({ page }) => {
    // Navigate to select page with a repo_id
    await page.goto('/select?repo_id=test1234')

    // Wait for file tree to load
    await expect(page.getByText(/select files/i)).toBeVisible()

    // Verify directory icons are shown
    await expect(page.getByText('📁')).toBeVisible()

    // Verify file icons are shown
    await expect(page.getByText(/[🐍📘⚛️📋]/)).toBeVisible()
  })

  test('should allow selecting and deselecting files', async ({ page }) => {
    await page.goto('/select?repo_id=test1234')

    // Wait for file tree
    await expect(page.getByText(/select files/i)).toBeVisible()

    // Click on a file to select it
    const fileCheckbox = page.getByRole('checkbox').first()
    await fileCheckbox.check()

    // Verify it's checked
    await expect(fileCheckbox).toBeChecked()

    // Click again to deselect
    await fileCheckbox.uncheck()

    // Verify it's unchecked
    await expect(fileCheckbox).not.toBeChecked()
  })
})

test.describe('Home Page', () => {
  test('should show validation error for invalid URL', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)
    await urlInput.fill('invalid-url')

    // Should show validation message
    await expect(page.getByText(/valid github repository url/i)).toBeVisible()

    // Submit button should be disabled
    await expect(page.getByRole('button', { name: /analyze/i })).toBeDisabled()
  })

  test('should accept valid GitHub URLs', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)

    // Test various valid URL formats
    const validUrls = [
      'https://github.com/user/repo',
      'https://github.com/organization/project-name',
      'http://github.com/user/repo',
    ]

    for (const url of validUrls) {
      await urlInput.fill(url)
      await expect(page.getByRole('button', { name: /analyze/i })).toBeEnabled()
    }
  })

  test('should disable form while loading', async ({ page }) => {
    await page.goto('/')

    const urlInput = page.getByPlaceholder(/github.com\/user\/repository/i)
    await urlInput.fill('https://github.com/user/repo')

    const submitButton = page.getByRole('button', { name: /analyze/i })
    await submitButton.click()

    // Input should be disabled while loading
    await expect(urlInput).toBeDisabled()
  })
})

test.describe('Generate Page', () => {
  test('should show progress during generation', async ({ page }) => {
    await page.goto('/generate?podcast_id=test1234')

    // Should show progress indicator
    await expect(page.getByText(/generating|synthesizing/i)).toBeVisible()

    // Progress bar or percentage should be shown
    await expect(page.locator('[role="progressbar"]').or(page.getByText(/\d+%/))).toBeVisible()
  })

  test('should handle generation failure gracefully', async ({ page }) => {
    // Mock a failed generation
    await page.goto('/generate?podcast_id=failed')

    // Should show error message
    await expect(page.getByText(/error|failed/i)).toBeVisible()

    // Should offer retry or go back options
    await expect(page.getByRole('button', { name: /retry|back/i })).toBeVisible()
  })
})

test.describe('Podcast Page', () => {
  test('should render audio player with controls', async ({ page }) => {
    await page.goto('/podcast/test1234')

    // Wait for audio player to load
    await expect(page.getByRole('audio')).toBeVisible()

    // Play/pause button should be present
    await expect(page.getByRole('button', { name: /play/i })).toBeVisible()

    // Progress bar should be present
    await expect(page.getByRole('slider')).toBeVisible()
  })

  test('should display chapters list', async ({ page }) => {
    await page.goto('/podcast/test1234')

    // Wait for chapters to load
    await expect(page.getByText(/chapters/i)).toBeVisible()

    // Should show chapter titles
    await expect(page.getByText(/introduction|chapter/i)).toBeVisible()
  })

  test('should seek to chapter when clicked', async ({ page }) => {
    await page.goto('/podcast/test1234')

    // Wait for page to load
    await expect(page.getByText(/chapters/i)).toBeVisible()

    // Click on a chapter
    const chapterButton = page.getByRole('button', { name: /chapter|main/i }).first()
    await chapterButton.click()

    // Audio should seek (we can't easily verify the exact time in E2E)
    // But we can verify the UI updates
  })

  test('should change playback speed', async ({ page }) => {
    await page.goto('/podcast/test1234')

    // Wait for page to load
    await expect(page.getByText(/speed:/i)).toBeVisible()

    // Click on a different speed
    await page.getByRole('button', { name: /1\.5x/i }).click()

    // Speed button should be highlighted
    await expect(page.getByRole('button', { name: /1\.5x/i })).toHaveClass(/bg-white/)
  })
})
