# Podcast-Anything: Project Roadmap

## Overview

**Podcast-Anything** converts GitHub repositories into educational audio explanations (audiobook-style programming tutorials).

### Target Users
- Developers learning new codebases
- Code reviewers
- Students

### Core Value Proposition
Understand codebases while away from your computer (commuting, exercising).

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Frontend       │◄───►│  Backend API     │◄───►│  Claude Code    │
│  (Next.js PWA)  │     │  (FastAPI)       │     │  CLI (SDK)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Alibaba Cloud   │
                        │  TTS (DashScope) │
                        └──────────────────┘
```

---

## Processing Pipeline

### Phase 1: Repository Analysis
1. Clone repo to temp workspace
2. Claude Code: Analyze structure, identify key files
3. Return file tree → User selects files

### Phase 2: Script Generation
1. Claude Code: Read selected files
2. Generate educational script with chapters:
   - Introduction (project overview)
   - Chapter 1: Architecture
   - Chapter 2-N: Key components
   - Conclusion
3. User reviews/edits (optional)

### Phase 3: Audio Generation
1. Split script into chunks (~500 chars)
2. Alibaba TTS: Synthesize each chunk
3. Assemble segments with chapter markers
4. Return audio URL + chapter metadata

---

## MVP Features

- [x] GitHub URL input
- [x] File/folder selection (include/exclude)
- [x] Chapter/section markers
- [x] Playback speed control (0.5x - 2x)
- [x] PWA installability

---

## Implementation Phases

### Phase 0: Project Setup ✅
- [x] Create ROADMAP.md
- [x] Create CLAUDE.md
- [x] Initialize git repository
- [x] Create README.md

### Phase 1: Foundation ✅
- [x] Set up FastAPI project structure
- [x] Implement basic API endpoints (health, status)
- [x] Integrate Claude Code SDK, test repo analysis
- [x] Integrate Alibaba Cloud TTS, test synthesis

### Phase 2: Core Pipeline ✅
- [x] Build repository cloning and management
- [x] Build Claude-based repo analyzer
- [x] Build script generator with chapters
- [x] Build audio generation pipeline
- [x] Implement chapter marker embedding

### Phase 3: Frontend ✅
- [x] Set up Next.js project with PWA config
- [x] Build URL input and file selection UI
- [x] Build generation progress tracking
- [x] Build audio player with chapters + speed control
- [x] Add PWA offline support

### Phase 4: Polish
- [ ] Add caching layer (Redis)
- [ ] Implement async task queue (Celery)
- [ ] Add error handling and retries
- [x] Docker deployment
- [ ] Performance optimization

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/repository/analyze` | Clone and analyze repo |
| GET | `/api/v1/repository/{id}/structure` | Get file tree |
| POST | `/api/v1/podcast/create` | Start generation job |
| GET | `/api/v1/podcast/{id}/status` | Check progress |
| GET | `/api/v1/podcast/{id}/audio` | Stream/download audio |
| GET | `/api/v1/podcast/{id}/chapters` | Get chapter metadata |

---

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Claude Agent SDK
- Alibaba Cloud DashScope (TTS)
- pydub + mutagen (audio processing)
- GitPython

### Frontend
- Next.js 14 (App Router)
- React 18
- Wavesurfer.js (audio visualization)
- Zustand (state management)
- TailwindCSS

---

## Open Questions

1. **Authentication**: Anonymous vs user accounts?
2. **Storage**: S3, local, or Alibaba OSS for audio files?
3. **Rate Limiting**: Free tier limits?
