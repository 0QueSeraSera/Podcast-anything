import { http, HttpResponse, delay } from 'msw'

const API_BASE = '/api/v1'

// In-memory store for podcast states in tests
const podcastStates = new Map<string, any>()

export const podcastHandlers = [
  // POST /api/v1/podcast/create
  http.post(`${API_BASE}/podcast/create`, async ({ request }) => {
    const body = await request.json() as { repo_id: string; selected_files: string[]; title?: string }

    if (body.repo_id === 'not-found') {
      return HttpResponse.json(
        { detail: 'Repository not found' },
        { status: 400 }
      )
    }

    const podcastId = `pod${Date.now().toString(36)}`

    // Initialize podcast state
    podcastStates.set(podcastId, {
      podcast_id: podcastId,
      status: 'pending',
      progress: 0,
      current_step: 'Pending',
    })

    return HttpResponse.json({
      podcast_id: podcastId,
      status: 'pending',
      message: 'Podcast generation started',
    })
  }),

  // GET /api/v1/podcast/:podcastId/status
  http.get(`${API_BASE}/podcast/:podcastId/status`, async ({ params }) => {
    const { podcastId } = params

    if (podcastId === 'not-found') {
      return HttpResponse.json(
        { detail: 'Podcast not found' },
        { status: 404 }
      )
    }

    const state = podcastStates.get(podcastId as string)

    if (!state) {
      // Default response for unknown podcasts
      return HttpResponse.json({
        podcast_id: podcastId,
        status: 'completed',
        progress: 100,
        current_step: 'Completed',
        error: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    }

    // Simulate progress for testing
    if (state.status === 'pending') {
      state.status = 'generating_script'
      state.progress = 10
      state.current_step = 'Generating Script'
    } else if (state.status === 'generating_script') {
      state.status = 'synthesizing'
      state.progress = 50
      state.current_step = 'Synthesizing'
    } else if (state.status === 'synthesizing') {
      state.status = 'completed'
      state.progress = 100
      state.current_step = 'Completed'
    }

    return HttpResponse.json({
      ...state,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }),

  // GET /api/v1/podcast/:podcastId/audio
  http.get(`${API_BASE}/podcast/:podcastId/audio`, ({ params }) => {
    const { podcastId } = params

    if (podcastId === 'not-ready') {
      return HttpResponse.json(
        { detail: 'Audio not found or not ready' },
        { status: 404 }
      )
    }

    // Return a minimal valid MP3 file (just headers, not playable)
    const mockMp3 = new Uint8Array([
      0x49, 0x44, 0x33, // ID3
      0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ID3 header
      0xFF, 0xFB, 0x90, 0x00, // MP3 frame header
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])

    return new HttpResponse(mockMp3, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Disposition': `attachment; filename="podcast-${podcastId}.mp3"`,
      },
    })
  }),

  // GET /api/v1/podcast/:podcastId/chapters
  http.get(`${API_BASE}/podcast/:podcastId/chapters`, ({ params }) => {
    const { podcastId } = params

    if (podcastId === 'not-found') {
      return HttpResponse.json(
        { detail: 'Podcast not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      podcast_id: podcastId,
      chapters: [
        {
          id: 1,
          title: 'Introduction',
          start_time: 0,
          end_time: 60,
          description: 'Welcome and overview',
        },
        {
          id: 2,
          title: 'Main Content',
          start_time: 60,
          end_time: 180,
          description: 'Core concepts explained',
        },
        {
          id: 3,
          title: 'Conclusion',
          start_time: 180,
          end_time: 240,
          description: 'Summary and next steps',
        },
      ],
    })
  }),
]

// Helper to reset podcast states between tests
export function resetPodcastStates() {
  podcastStates.clear()
}
