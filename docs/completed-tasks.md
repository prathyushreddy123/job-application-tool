# Completed Tasks

Running log of all completed development tasks.

---

## 2026-02-19: PRD & CLAUDE.md Deep-Dive Interview Update

**What was done:** Conducted 8-round detailed interview covering 28 design decisions. Updated PRD (v1.4 → v1.5) and rewrote CLAUDE.md with all decisions.

**Key decisions documented:**
- Pipeline fill-ahead (2-3 buffer), re-fill on approve, Gemini AI fallback for custom questions
- shadcn/ui + Tailwind, progress sidebar, toast notifications, screenshot on Space key
- n8n dedup + UUID generation, ATS auto-detect from URL, per-domain rate limits
- Persistent Playwright browser profile, simple API key auth, demo mode
- Unit tests for critical paths, timing data in audit logs, /api/stats endpoint

**Files changed:**
- `prd.md` — 18 edits across sections 3, 4, 7, 8, 9, 10, 11, 12, 17, 18
- `CLAUDE.md` — Full rewrite with architecture, structure, commands, behavior docs
- `docs/completed-tasks.md` — Created
- `docs/troubleshooting.md` — Created

---

## 2026-02-19: Phase 1 — Project Scaffolding & Configuration

**What was done:** Created the full project skeleton — backend (FastAPI + config + CLI), frontend (Vite + React + TypeScript + Tailwind), data files, and gitignore.

**Verified:**
- Backend `/health` endpoint returns 200
- Frontend builds and serves at :5173
- Config loads from env vars correctly

**Files created:**
- `.gitignore`, `.env.example`
- `backend/config.py` — Pydantic BaseSettings with all env vars
- `backend/main.py` — FastAPI app with /health, CLI entrypoint (serve/apply/--demo/--dry-run)
- `backend/requirements.txt` — All Python dependencies
- `backend/__init__.py`, `models/__init__.py`, `automation/__init__.py`, `adapters/__init__.py`, `routes/__init__.py`, `tests/__init__.py`
- `frontend/` — Full Vite + React + TS + Tailwind scaffold with API proxy config
- `data/answers.json` — Profile template with custom_answers section
- `data/mock-jobs.json` — 5 mock Greenhouse jobs for demo mode
- `data/audit/.gitkeep`, `credentials/.gitkeep`

---

## 2026-02-19: Phase 2 — Data Models, Profile, Audit, Stats + Tests

**What was done:** Built the core data layer — Pydantic models, profile loading with dot-path traversal and answer bank search, audit logging with timing data, and stats aggregation. All 16 unit tests passing.

**Files created:**
- `backend/models/job.py` — Job, FilledField, JobTiming, JobStatus models
- `backend/profile.py` — load_profile, get_answer, search_answer_bank
- `backend/audit.py` — write_audit_log, list_audit_logs
- `backend/stats.py` — get_stats (aggregates from audit logs)
- `backend/tests/test_profile.py` — 10 tests
- `backend/tests/test_audit.py` — 4 tests
- `backend/tests/test_stats.py` — 2 tests

---

## 2026-02-19: Phase 3 — ATS Detection & Greenhouse Adapter

**What was done:** Built the adapter abstraction layer, Greenhouse-specific form filling adapter with comprehensive field/label maps, ATS auto-detection from URL patterns, and factory function. 30 new tests (46 total), all passing.

**Files created:**
- `backend/automation/adapters/base.py` — BaseAdapter ABC (detect, fill_form, submit, navigate_pages, detect_custom_questions)
- `backend/automation/adapters/greenhouse.py` — GreenhouseAdapter with FIELD_MAP (14 entries), LABEL_MAP (40+ entries), match_label_to_dotpath, fill_form, multi-page navigation, custom question detection
- `backend/automation/ats_detect.py` — detect_ats_type (URL patterns for 4 ATS), get_adapter factory
- `backend/tests/test_ats_detect.py` — 13 tests (URL detection, adapter factory)
- `backend/tests/test_greenhouse.py` — 17 tests (field map completeness, dotpath resolution, label matching)

---

## 2026-02-19: Phase 4 — Playwright Browser Manager & Form Pipeline

**What was done:** Built browser lifecycle management with persistent sessions, the fill-ahead pipeline with asyncio.Queue-based buffer, re-fill-on-approve with retry logic, and per-domain rate limiting. 13 new tests (59 total), all passing.

**Troubleshooting:** RateLimiter._get_domain returned empty string for malformed URLs instead of "unknown" — fixed by adding empty hostname check.

**Files created:**
- `backend/automation/browser.py` — BrowserManager (persistent user_data_dir, screenshot, bring_to_front, random_delay)
- `backend/automation/form_filler.py` — FormFillingPipeline (fill-ahead buffer, refill_and_submit with retry-once, auto-stop on 3 failures)
- `backend/automation/rate_limiter.py` — RateLimiter (per-domain, 1-hour sliding window, async wait)
- `backend/tests/test_rate_limiter.py` — 11 tests
- `backend/tests/test_form_filler.py` — 2 tests (status, queue empty)

---

## 2026-02-19: Phase 5 — Gemini Client & n8n Client

**What was done:** Built external service clients — Gemini AI for custom question fallback and n8n webhook client with offline resilience. n8n verified running live on localhost:5678. 7 new tests (66 total), all passing.

**Files created:**
- `backend/gemini_client.py` — GeminiClient (Gemini 2.0 Flash, 10s timeout, prompt with profile+job context)
- `backend/n8n_client.py` — N8nClient (webhook POST, queue + exponential backoff retry, health check loop)
- `backend/tests/test_gemini_client.py` — 3 tests (no key, generate without key, prompt building)
- `backend/tests/test_n8n_client.py` — 4 tests (init, queue on failure, offline/online health check)

---

## 2026-02-19: Phase 6 — FastAPI Routes, WebSocket & Auth

**What was done:** Wired all backend pieces into a running API server. All endpoints verified working in demo mode with curl. API key auth rejects invalid keys. WebSocket endpoint ready. 9 new tests (75 total), all passing.

**Endpoints verified:**
- `GET /health` — 200
- `POST /api/automation/start?demo=true` — loads 5 mock jobs
- `GET /api/jobs` — returns jobs with filled fields
- `POST /api/jobs/{id}/approve` — marks submitted (demo), triggers re-fill+submit (real)
- `POST /api/jobs/{id}/skip` — marks skipped
- `GET /api/automation/status` — pipeline status, n8n online, job counts
- `GET /api/stats` — aggregated audit stats
- `POST /api/webhooks/jobs-sync` — n8n job sync receiver
- `WS /ws/updates` — real-time broadcast
- Auth: 401 on wrong X-API-Key

**Files created/modified:**
- `backend/auth.py`, `backend/job_store.py`, `backend/websocket_manager.py`, `backend/demo.py`
- `backend/routes/jobs.py`, `automation.py`, `webhooks.py`, `stats.py`
- `backend/main.py` — rewritten with AppState, startup/shutdown, all routers
- `backend/tests/test_job_store.py` — 9 tests

---

## 2026-02-19: Phase 7 — Frontend Card Stack, Sidebar, Keyboard

**What was done:** Built the full React frontend with Tinder-style card review interface. All components wired together with keyboard shortcuts, WebSocket real-time updates, toasts, and progress sidebar. Frontend builds cleanly. 75 backend tests still passing.

**Components created:**
- `CardStack.tsx` — Main view with stacked card visual, empty/ready states
- `ApplicationCard.tsx` — Header (company, title, ATS badge), FormPreview, action buttons with keyboard hints
- `FormPreview.tsx` — Field list with status icons (Check/AlertTriangle/Bot/X), inline-editable AI fields
- `ProgressSidebar.tsx` — Counts, n8n status indicator, recent activity feed, keyboard shortcuts legend
- `PanicButton.tsx` — Fixed-position red stop button (visible when running)
- `ScreenshotModal.tsx` — Overlay for Space-key screenshot view
- `TopBar.tsx` — Start button, Demo/Dry Run toggles

**Hooks & Libraries:**
- `useKeyboard.ts` — Global keyboard shortcuts (Enter/ArrowRight=approve, ArrowLeft/S=skip, Esc=panic, Space=screenshot, E=edit)
- `useJobs.ts` — Job state management, WebSocket subscription, fallback polling every 5s
- `lib/api.ts` — API client with X-API-Key header
- `lib/websocket.ts` — WebSocket client with auto-reconnect every 3s
- `lib/types.ts` — TypeScript interfaces matching backend models

**Troubleshooting:** `useRef()` without initial argument fails in strict TypeScript mode — fixed by passing `undefined` explicitly.

---

## 2026-02-19: Phase 8 — End-to-End Integration & Demo Polish

**What was done:** Wired WebSocket events to toast notifications, added auto-stop on empty queue, fixed WebSocket URL for WSL2 compatibility, added error handling to TopBar start flow. Full E2E test suite (19 tests) all passing.

**Changes:**
- `App.tsx` — WebSocket connect on mount, toast notifications for all WS events (automation_started/stopped, job_submitted/failed, jobs_synced), auto-stop when queue empty
- `TopBar.tsx` — Error/warning toasts on start failure or no jobs available
- `lib/websocket.ts` — WebSocket URL uses `location.host` instead of hardcoded port (WSL2/proxy compatible)
- `vite.config.ts` — Added `host: '0.0.0.0'` for WSL2 access from Windows browser
- `backend/routes/automation.py` — Stop resets `settings.demo` and `settings.dry_run` (fixed in E2E testing)

**E2E tests verified (19/19 pass):**
- Health, auth (reject no key, reject bad key), jobs CRUD
- Demo start (5 jobs), approve, skip, status, stats
- Stop and status-after-stop, webhook sync, 404 handling
- WebSocket connectivity and message reception
- Frontend HTML, proxy to /api/jobs, proxy to /api/automation/status
