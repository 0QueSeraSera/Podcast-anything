// Podcast-related test fixtures

export const mockPodcastStatus = {
  podcast_id: 'pod1234',
  status: 'completed',
  progress: 100,
  current_step: 'Completed',
  error: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:05:00Z',
}

export const mockPendingStatus = {
  podcast_id: 'pod1234',
  status: 'pending',
  progress: 0,
  current_step: 'Pending',
  error: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockGeneratingStatus = {
  podcast_id: 'pod1234',
  status: 'generating_script',
  progress: 25,
  current_step: 'Generating Script',
  error: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
}

export const mockSynthesizingStatus = {
  podcast_id: 'pod1234',
  status: 'synthesizing',
  progress: 60,
  current_step: 'Synthesizing',
  error: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:02:00Z',
}

export const mockFailedStatus = {
  podcast_id: 'pod1234',
  status: 'failed',
  progress: 0,
  current_step: 'Failed',
  error: 'Script generation failed',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
}

export const mockChapters = [
  {
    id: 1,
    title: 'Introduction',
    start_time: 0,
    end_time: 60,
    description: 'Welcome and overview of the project',
  },
  {
    id: 2,
    title: 'Core Architecture',
    start_time: 60,
    end_time: 180,
    description: 'Understanding the main components',
  },
  {
    id: 3,
    title: 'Key Features',
    start_time: 180,
    end_time: 300,
    description: 'Exploring important functionality',
  },
  {
    id: 4,
    title: 'Conclusion',
    start_time: 300,
    end_time: 360,
    description: 'Summary and next steps',
  },
]

export const mockCreatePodcastResponse = {
  podcast_id: 'pod1234',
  status: 'pending',
  message: 'Podcast generation started',
}

export function createChapter(overrides = {}) {
  return {
    id: 1,
    title: 'Test Chapter',
    start_time: 0,
    end_time: 60,
    description: 'Test description',
    ...overrides,
  }
}

export function createChapters(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Chapter ${i + 1}`,
    start_time: i * 60,
    end_time: (i + 1) * 60,
    description: `Description for chapter ${i + 1}`,
  }))
}
