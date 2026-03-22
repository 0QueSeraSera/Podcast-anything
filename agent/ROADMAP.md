# Agent Development Roadmap

## Context

This roadmap assumes:

- Single-user project (no multi-tenant requirements for now)
- Next major milestone: mobile phone access + chat/questioning workflow
- Existing stack remains: FastAPI backend + Next.js frontend

## Product Goals

1. Let the user open Podcast-Anything on a phone over LAN and complete the full flow.
2. Add a chat experience to ask follow-up questions about a selected repository/podcast.
3. Keep answers grounded in selected files and generated script content.
4. Preserve simplicity while creating a clean upgrade path to multi-user later.

## Roadmap Levels

## Level 1: Stabilize Current Core (Immediate)

### Why

Mobile + chat should not be built on top of known blocking issues.

### Deliverables

- Fix `POST /podcast/create` behavior so API semantics are consistent (background job or clearly synchronous UI flow).
- Fix TTS chunk handling so full text is returned (not only first chunk).
- Fix frontend directory selection logic in file tree.

### Exit Criteria

- Podcast generation is reliable for long content.
- File selection behavior is deterministic for folder-level toggles.
- UI status and backend status contract are aligned.

## Level 2: Mobile Connectivity Baseline

### Deliverables

- Backend binding and docs for LAN access (`0.0.0.0`, phone-access URL).
- Frontend env setup for mobile API target.
- CORS tightened to known frontend origins (instead of wildcard in non-dev mode).
- Basic mobile UX pass for key screens:
  - Home
  - Select
  - Generate
  - Podcast

### Exit Criteria

- A phone on the same network can complete analyze -> select -> generate -> play.
- No desktop-only layout breaks on small screens.

## Level 3: Chat MVP (Context-Aware, Single User)

### Backend Deliverables

- Add chat session/message APIs:
  - `POST /api/v1/chat/sessions`
  - `POST /api/v1/chat/{session_id}/messages`
  - `GET /api/v1/chat/{session_id}/messages`
- Optional streaming endpoint (recommended):
  - `GET /api/v1/chat/{session_id}/stream` (SSE)
- Persist chat in SQLite:
  - `chat_sessions`
  - `chat_messages`
  - links to `repo_id`, `podcast_id`, selected files, script path

### Frontend Deliverables

- Add chat panel on podcast page:
  - user question input
  - answer rendering
  - conversation history
- Handle loading/errors/retry cleanly on mobile.

### Exit Criteria

- User can ask questions after generation and see persistent history after refresh.

## Level 4: Grounded Q&A Quality

### Deliverables

- Build context retrieval pipeline:
  - source: selected files + generated script + repo metadata
  - chunking + simple relevance ranking
- Prompting policy:
  - answer from context first
  - explicitly say when context is insufficient
- Add source references in response payload (file path + snippet metadata).

### Exit Criteria

- Answers are traceable to concrete context.
- Hallucination rate is materially reduced for codebase questions.

## Level 5: Mobile-First Chat Experience

### Deliverables

- Conversational UX upgrades:
  - quick actions: "Explain architecture", "Find entry points", "Summarize this module"
  - sticky follow-up input + keyboard-safe layout
- PWA upgrades:
  - install prompt polish
  - resilient reconnect behavior for chat streaming
- Save/export:
  - export chat transcript with podcast metadata

### Exit Criteria

- Chat on phone feels reliable and fast over normal home/office network.

## Technical Plan

## Data Model (SQLite, initial)

- `chat_sessions`
  - `id`, `created_at`, `updated_at`
  - `repo_id`, `podcast_id`
  - `title`
- `chat_messages`
  - `id`, `session_id`
  - `role` (`user`/`assistant`/`system`)
  - `content`
  - `sources_json` (optional)
  - `created_at`
- Optional `context_snapshots`
  - immutable snapshot of selected files/script path used by a session

## API Contract Principles

- Keep current `/api/v1` namespace.
- Return stable JSON envelopes for chat endpoints.
- Include typed error codes for frontend branching.
- Prefer SSE for streaming responses; fallback to non-stream response path.

## Testing Roadmap

1. Backend unit tests:
   - chat session CRUD
   - retrieval ranking behavior
   - prompt assembly and source attribution
2. Backend integration tests:
   - end-to-end chat message flow with persisted history
3. Frontend integration tests:
   - chat panel rendering, retry, history restore
4. E2E (full-stack):
   - generate podcast -> ask question -> refresh -> history remains
   - mobile viewport coverage

## Delivery Sequence (Suggested)

1. Stabilization fixes (Level 1)
2. Mobile baseline (Level 2)
3. Chat API + SQLite persistence (Level 3 backend first)
4. Chat UI wiring (Level 3 frontend)
5. Retrieval grounding + source attribution (Level 4)
6. Mobile UX polish + PWA/chat resilience (Level 5)

## Out of Scope (for now)

- Multi-user auth and permissions
- Cloud deployment hardening
- Vector DB infrastructure
- Real-time collaboration

## Success Metrics

- Time to first answer in chat: acceptable on local hardware/network
- Q&A grounding: responses include source pointers in most technical answers
- Mobile completion rate: full journey works without desktop
- Regression rate: existing generation/playback flow remains stable
