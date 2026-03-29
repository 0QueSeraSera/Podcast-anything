# Execution Checklist (P0 / P1 / P2)

Source roadmap: `agent/NEXT_LEVEL_ROADMAP.md`

Conventions:

- Priority: `P0` (must-do now), `P1` (next), `P2` (polish/upgrade)
- Effort: `S` (<=0.5d), `M` (1-2d), `L` (3-5d)
- Status: `[ ]` todo, `[x]` done

---

## P0: Stabilize Core + Mobile Baseline

### PA-001 Fix podcast creation contract
- Priority: `P0`
- Effort: `M`
- Depends on: none
- [x] Make `/api/v1/podcast/create` either truly async/background or explicitly synchronous in API + UI.
- [x] Ensure returned status matches real backend state.
- [x] Add integration test for long-running generation behavior.
- DoD: API contract and frontend polling flow are consistent and test-covered.

### PA-002 Fix TTS multi-chunk truncation
- Priority: `P0`
- Effort: `M`
- Depends on: none
- [x] Concatenate all successful TTS chunks (instead of returning first chunk only).
- [x] Preserve duration/chapter correctness after fix.
- [x] Add unit tests for 2+ chunk synthesis output.
- DoD: long scripts generate full audio content end-to-end.

### PA-003 Fix file-tree directory selection logic
- Priority: `P0`
- Effort: `S`
- Depends on: none
- [x] Remove direct mutation of `selectedFiles` in child component.
- [x] Implement deterministic directory select/deselect behavior.
- [x] Add unit tests for folder toggle with nested files.
- DoD: folder selection is stable and reproducible in UI tests.

### PA-004 Stop unnecessary status polling on terminal states
- Priority: `P0`
- Effort: `S`
- Depends on: `PA-001`
- [x] Stop polling when status is `completed` or `failed`.
- [x] Add UI fallback action for `failed` (retry or return).
- [x] Add integration test validating poll stop behavior.
- DoD: no repeated requests after terminal state.

### PA-005 LAN mobile access setup
- Priority: `P0`
- Effort: `S`
- Depends on: none
- [x] Add run instructions for backend on `0.0.0.0`.
- [x] Add frontend env guidance for phone-accessible API URL.
- [ ] Verify flow from physical phone on same network.
- DoD: analyze -> generate -> play works from mobile browser.

### PA-006 CORS hardening for non-dev
- Priority: `P0`
- Effort: `S`
- Depends on: `PA-005`
- [x] Replace wildcard CORS with env-based allowlist.
- [x] Keep dev convenience mode configurable.
- [x] Add config docs in README.
- DoD: known origins pass; unknown origins blocked in non-dev mode.

### PA-007 P0 regression test pass
- Priority: `P0`
- Effort: `M`
- Depends on: `PA-001`..`PA-006`
- [x] Run backend unit/integration tests.
- [x] Run frontend unit/integration tests.
- [x] Run one full-stack E2E happy path.
- DoD: all critical tests green with no new flaky failures.

---

## P1: Chat MVP (Single-User, Persistent)

### PA-101 Add SQLite persistence scaffold
- Priority: `P1`
- Effort: `M`
- Depends on: `P0`
- [x] Choose lightweight DB approach (sqlite3 or SQLAlchemy).
- [x] Add migration/init path for local DB file.
- [x] Add repository layer for chat sessions/messages.
- DoD: DB file initializes automatically and stores data.

### PA-102 Define chat data schema
- Priority: `P1`
- Effort: `S`
- Depends on: `PA-101`
- [x] Create `chat_sessions` schema.
- [x] Create `chat_messages` schema.
- [x] Add optional context snapshot fields (`repo_id`, `podcast_id`, selected files, script path).
- DoD: schema supports persistent threaded chat.

### PA-103 Chat session API
- Priority: `P1`
- Effort: `S`
- Depends on: `PA-101`, `PA-102`
- [x] Implement `POST /api/v1/chat/sessions`.
- [x] Implement `GET /api/v1/chat/{session_id}/messages`.
- [x] Add request/response schemas and error codes.
- DoD: session creation and history retrieval work.

### PA-104 Chat message API (non-streaming)
- Priority: `P1`
- Effort: `M`
- Depends on: `PA-103`
- [x] Implement `POST /api/v1/chat/{session_id}/messages`.
- [x] Persist user and assistant messages.
- [x] Return assistant answer with optional source metadata.
- DoD: end-to-end ask/answer with persistence.

### PA-105 Build context pack from repo + script
- Priority: `P1`
- Effort: `M`
- Depends on: `PA-104`
- [x] Load selected files and script output for session context.
- [x] Add token/size guardrails to prevent oversized prompts.
- [x] Add deterministic fallback when script/context is missing.
- DoD: answers are grounded in available local context.

### PA-106 Add podcast-page chat panel
- Priority: `P1`
- Effort: `M`
- Depends on: `PA-103`, `PA-104`
- [x] Render message history.
- [x] Add question input + submit + loading/error UI.
- [x] Preserve conversation on refresh via session id.
- DoD: user can ask and see persistent history from podcast page.

### PA-107 Link podcast flow to chat session
- Priority: `P1`
- Effort: `S`
- Depends on: `PA-106`
- [x] Create/reuse chat session when entering podcast page.
- [x] Bind session to `podcast_id` and associated `repo_id`.
- [x] Handle missing podcast/session recovery.
- DoD: one coherent conversation per podcast context.

### PA-108 P1 test coverage
- Priority: `P1`
- Effort: `M`
- Depends on: `PA-101`..`PA-107`
- [x] Backend tests for chat persistence and API routes.
- [x] Frontend integration tests for chat panel behavior.
- [ ] One E2E: generate podcast -> ask question -> refresh -> history retained.
- DoD: chat MVP is reliably test-covered.

---

## P2: Grounding Quality + Mobile Chat Polish

### PA-201 Add retrieval ranking layer
- Priority: `P2`
- Effort: `M`
- Depends on: `P1`
- [x] Chunk files/script into retrieval units.
- [x] Implement simple relevance ranking (keyword + section weighting).
- [x] Pass top-K chunks into answer prompt.
- DoD: context selection is explicit and repeatable.

### PA-202 Add source citations in responses
- Priority: `P2`
- Effort: `S`
- Depends on: `PA-201`
- [x] Return source pointers (file path, section/chunk id).
- [x] Render citations in frontend answer cards.
- [x] Add tests for citation presence.
- DoD: technical answers can be traced to source context.

### PA-203 SSE streaming answers
- Priority: `P2`
- Effort: `M`
- Depends on: `PA-104`
- [x] Add `GET /api/v1/chat/{session_id}/stream`.
- [x] Add frontend streaming renderer + cancel/retry behavior.
- [x] Ensure persistence captures final assistant message.
- DoD: incremental token streaming works on desktop and phone.

### PA-204 Mobile chat UX pass
- Priority: `P2`
- Effort: `M`
- Depends on: `PA-106`, `PA-203`
- [x] Keyboard-safe layout and sticky input on mobile.
- [x] Quick action prompts (architecture, entry points, summary).
- [x] Improve loading and offline/reconnect states.
- DoD: chat use on phone is smooth for normal sessions.

### PA-205 Export chat transcript
- Priority: `P2`
- Effort: `S`
- Depends on: `PA-106`
- [x] Add endpoint/UI to export transcript (markdown/json).
- [x] Include podcast metadata and citation links.
- DoD: user can save/share chat learning session.

### PA-206 Observability and performance guardrails
- Priority: `P2`
- Effort: `M`
- Depends on: `P1`
- [x] Add structured logs around chat latency, prompt size, error rates.
- [x] Add timeout and retry policy for chat generation calls.
- [ ] Document expected local performance envelope.
- DoD: chat behavior is diagnosable and bounded.

---

## Suggested Milestone Cuts

### Milestone A (Ship fast, high value)
- `PA-001` to `PA-007`

### Milestone B (Chat MVP usable)
- `PA-101` to `PA-108`

### Milestone C (Quality and polish)
- `PA-201` to `PA-206`

---

## Immediate Start Queue (Recommended)

1. `PA-002` Fix TTS multi-chunk truncation
2. `PA-003` Fix file-tree selection
3. `PA-001` Align podcast create contract
4. `PA-005` LAN mobile baseline
