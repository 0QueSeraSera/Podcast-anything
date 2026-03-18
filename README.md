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
| POST | `/api/v1/podcast/create` | Start generation job |
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

## License

MIT
