import { http, HttpResponse } from 'msw'

const API_BASE = '/api/v1'

export const repositoryHandlers = [
  // POST /api/v1/repository/analyze
  http.post(`${API_BASE}/repository/analyze`, async ({ request }) => {
    const body = await request.json() as { url: string }

    // Validate URL
    if (!body.url || !body.url.includes('github.com')) {
      return HttpResponse.json(
        { detail: 'Only GitHub repositories are supported' },
        { status: 400 }
      )
    }

    // Extract repo name from URL
    const urlParts = body.url.split('/')
    const repoName = urlParts[urlParts.length - 1]?.replace('.git', '') || 'unknown-repo'

    return HttpResponse.json({
      repo_id: 'test1234',
      name: repoName,
      description: `A sample repository for testing`,
      file_count: 15,
    })
  }),

  // GET /api/v1/repository/:repoId/structure
  http.get(`${API_BASE}/repository/:repoId/structure`, ({ params }) => {
    const { repoId } = params

    if (repoId === 'not-found') {
      return HttpResponse.json(
        { detail: 'Repository not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      repo_id: repoId,
      root: {
        name: 'sample-project',
        path: '.',
        is_dir: true,
        children: [
          {
            name: 'README.md',
            path: 'README.md',
            is_dir: false,
            children: null,
          },
          {
            name: 'main.py',
            path: 'main.py',
            is_dir: false,
            children: null,
          },
          {
            name: 'src',
            path: 'src',
            is_dir: true,
            children: [
              {
                name: '__init__.py',
                path: 'src/__init__.py',
                is_dir: false,
                children: null,
              },
              {
                name: 'utils.py',
                path: 'src/utils.py',
                is_dir: false,
                children: null,
              },
            ],
          },
        ],
      },
    })
  }),
]
