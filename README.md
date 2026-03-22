# Podcast-Anything

Convert GitHub repositories into educational audio explanations (like a programming tutorial/podcast).

## Features

- **AI-Powered Analysis**: Uses Claude Code CLI to analyze codebases
- **Educational Scripts**: Generates tutorial-style explanations
- **High-Quality TTS**: Alibaba Cloud DashScope for natural-sounding audio
- **Chapter Markers**: Navigate audio by topic
- **PWA Support**: Install on mobile for offline listening

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Claude Code CLI (`claude`) installed and available in `PATH` (for code analysis/script generation)
- API Keys:
  - Alibaba Cloud DashScope API key (for TTS)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.local.example .env.local

# Run the development server
npm run dev
```

### Using Docker

```bash
# Build and run backend
cd backend
docker build -t podcast-anything-backend .
docker run -p 8000:8000 --env-file .env podcast-anything-backend
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/repository/analyze` | Clone and analyze repo |
| GET | `/api/v1/repository/{id}/structure` | Get file tree |
| POST | `/api/v1/podcast/create` | Queue generation job (returns `202`) |
| GET | `/api/v1/podcast/{id}/status` | Check progress |
| GET | `/api/v1/podcast/{id}/audio` | Stream/download audio |
| GET | `/api/v1/podcast/{id}/chapters` | Get chapter metadata |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Frontend       │◄───►│  Backend API     │◄───►│  Claude Code    │
│  (Next.js PWA)  │     │  (FastAPI)       │     │  CLI            │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Alibaba Cloud   │
                        │  TTS (DashScope) │
                        └──────────────────┘
```

## Development

See [ROADMAP.md](./ROADMAP.md) for the project roadmap and implementation progress.

See [CLAUDE.md](./CLAUDE.md) for Claude Code instructions.

## Testing

### Full-stack E2E automation

Run this from `frontend`:

```bash
npm run test:e2e:fullstack
```

Prerequisites for the command above:
- Run `npm install` in `frontend` (installs Playwright binaries in `node_modules`).
- Create backend venv and install backend deps in `backend` (`python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`).

This command starts:
- backend on `127.0.0.1:8000` with `E2E_MOCK_PIPELINE=true` (prefers `backend/venv/bin/python` when present)
- frontend on `127.0.0.1:3000` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`

It automates the full user journey:
paste GitHub URL -> analyze -> select files -> enter scope instruction -> generate podcast -> verify podcast page/audio/chapters.

### Non-mock full-stack pipeline (real GitHub + Claude CLI)

Run this from `frontend`:

```bash
npm run test:e2e:nonmock
```

What it does:
- uses real repository analysis (no `E2E_MOCK_PIPELINE`)
- uses real Claude CLI script generation
- skips TTS with `E2E_SKIP_TTS=true` so you can inspect script output quickly

Optional override for repo URL:

```bash
NONMOCK_E2E_REPO_URL=https://github.com/octocat/Hello-World npm run test:e2e:nonmock
```

Inspect raw Claude script output after generation:
- file output directory: `CLAUDE_OUTPUT_DIR` (default: `/tmp/podcast-anything/claude-output`)
- API endpoint: `GET /api/v1/podcast/{podcast_id}/script`

## License

MIT
