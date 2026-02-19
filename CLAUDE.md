# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Rules (MUST FOLLOW)

1. **Commit & push after every completed + tested task.** Once a task is done and tests pass, create a git commit with a clear message and push to remote. Do not batch multiple unrelated tasks into one commit.
2. **Maintain `docs/completed-tasks.md`** — After each task is finished, append a summary entry (date, task name, what was done, files changed). This serves as a running changelog.
3. **Maintain `docs/troubleshooting.md`** — When any issue is encountered and resolved during development, document it (problem, root cause, solution). This helps future sessions debug recurring issues.
4. These docs must be kept up to date as work progresses — not retroactively.

## Project Overview

Semi-automated job application tool with a Tinder-style card review interface. The tool auto-fills job application forms using stored profile data, then presents each application for human approval before submission.

## Architecture

**Stack:** Python FastAPI backend + React (shadcn/ui + Tailwind) frontend + n8n for workflow automation + Playwright for browser automation

```
React (Card Stack UI — shadcn/ui + Tailwind)
        ↓ WebSocket + REST (API key auth)
FastAPI (Playwright, form filling, audit logging, Gemini AI fallback)
        ↓ HTTP webhooks (queue + retry if offline)
n8n (Google Sheets sync, dedup, UUID gen, notifications, scheduling)
        ↓
Google Sheets (job listings, status tracking, UUID column)
```

**Key Design Decisions:**
- n8n handles all Google Sheets operations, deduplication, UUID generation, ATS auto-detection, and notifications
- Local files (answers.json, audit logs) use direct Python file I/O (MCP deferred to Phase 2)
- Playwright runs in headed mode with persistent `user_data_dir` for session/cookie persistence
- MVP focuses on Greenhouse ATS only; adapters for Workday, Lever planned later
- Each adapter owns its own hardcoded field label map
- Custom questions: pre-built answer bank in answers.json → Gemini free tier fallback
- Pipeline batch model: fill 2-3 forms ahead while user reviews current card
- Re-fill on approve guarantees form freshness; retry once on failure, then pause for manual intervention
- Simple API key auth on all endpoints
- Per-domain configurable rate limits
- Cover letters deferred from MVP entirely
- Single resume for MVP; data model designed for multiple (Phase 2)

## Dev Environment

- **Platform:** WSL2 (Linux)
- **Docker:** Only n8n runs in Docker; FastAPI + React run natively for fast iteration
- **Testing:** pytest (backend), Vitest (frontend), dry-run mode
- **Demo mode:** `--demo` flag loads mock jobs without n8n/Sheets

## Planned Project Structure

```
job-auto-apply/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration + env vars
│   ├── n8n_client.py           # HTTP client to call n8n webhooks (queue + retry)
│   ├── profile.py              # Load answers.json + answer bank
│   ├── audit.py                # Write audit logs with timing data
│   ├── stats.py                # Aggregate stats from audit logs
│   ├── gemini_client.py        # Gemini AI for custom question fallback
│   ├── models/job.py           # Job listing models (UUID-based ID)
│   ├── tests/                  # pytest unit tests
│   └── automation/
│       ├── browser.py          # Playwright management (persistent user_data_dir)
│       ├── form_filler.py      # Generic form detection + fill-ahead pipeline
│       └── adapters/
│           ├── base.py         # Base adapter
│           └── greenhouse.py   # Greenhouse adapter (owns its FIELD_MAP)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CardStack.tsx       # Main review interface
│   │   │   ├── ApplicationCard.tsx # Card with inline-editable AI fields
│   │   │   ├── ProgressSidebar.tsx # Always-visible batch progress
│   │   │   ├── FormPreview.tsx     # Screenshot modal (Space key)
│   │   │   └── PanicButton.tsx
│   │   ├── hooks/useKeyboard.ts
│   │   └── lib/toast.ts            # Toast notification system
│   ├── package.json
│   └── vite.config.ts
├── n8n/workflows/              # Exported n8n workflow JSONs
│   ├── sync-jobs.json          # Includes dedup + UUID gen + ATS auto-detect
│   ├── update-status.json
│   ├── error-notification.json
│   └── daily-summary.json
├── data/
│   ├── answers.json            # Form field responses + custom_answers bank
│   ├── resume.pdf
│   ├── mock-jobs.json          # Demo mode fixture data
│   ├── browser-profile/        # Persistent Playwright session (gitignored)
│   └── audit/                  # Submission logs with timing data
└── credentials/
```

## Development Commands

### Services

```bash
# n8n (Docker — only service in Docker)
docker run -d --name n8n --restart unless-stopped -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

# Backend (native WSL2)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Frontend (native WSL2)
cd frontend
npm install
npm run dev
```

### Running

```bash
# Start backend server
python -m backend.main serve

# Start in demo mode (no n8n/Sheets required)
python -m backend.main serve --demo

# Dry-run (no submissions)
python -m backend.main apply --dry-run

# Process specific job
python -m backend.main apply --url "https://..."
```

### Testing

```bash
# Backend unit tests
cd backend && pytest

# Frontend tests (if applicable)
cd frontend && npm test
```

### Service URLs

| Service | URL |
|---------|-----|
| n8n | http://localhost:5678 |
| FastAPI | http://localhost:8000 |
| React | http://localhost:5173 |

## Key API Endpoints

```
# All endpoints require X-API-Key header

GET  /api/jobs                    # Get cached jobs
POST /api/jobs/{id}/approve       # Re-fill + submit (UUID-based ID)
POST /api/jobs/{id}/skip          # Skip application
POST /api/automation/start        # Start batch processing (?demo=true)
POST /api/automation/stop         # Panic stop
GET  /api/stats                   # Aggregated stats from audit logs
POST /api/webhooks/jobs-sync      # n8n job sync webhook
WS   /ws/updates                  # Real-time status updates
```

## Key Environment Variables

```bash
API_KEY=secret                          # Simple API key auth
BROWSER_PROFILE_DIR=./data/browser-profile  # Persistent Playwright session
FILL_AHEAD_BUFFER=3                     # Forms to pre-fill ahead
GEMINI_API_KEY=key                      # For custom question AI fallback
RATE_LIMITS='{"greenhouse.io": 5}'      # Per-domain rate limits
```

## n8n Workflows

1. **Sync Jobs** - Polls Sheets every 5 min, deduplicates by URL, generates UUIDs, auto-detects ATS type, POSTs to FastAPI
2. **Update Status** - Webhook receives status updates, writes to Sheets
3. **Error Notification** - Sends email/Slack after 3 consecutive failures
4. **Daily Summary** - 6pm daily email with application counts

## Form Handling Strategy

1. **Adapter label map** — ATS-specific hardcoded field mappings (most reliable)
2. **Answer bank** — Pre-built Q&A pairs in `answers.json` for common custom questions
3. **Gemini fallback** — AI-generated answers for unmatched free-text questions (auto-filled, editable on card, flagged with 🤖)
4. **Skip & flag** — Unknown fields left blank, marked ⚠ in review UI
5. All submitted field values logged to `data/audit/` with timing phases
6. Screenshots captured of final form page before submission

## UI Behavior

- **Card stack** with keyboard shortcuts (Enter=approve, ←/S=skip, Esc=panic, Space=screenshot, E=edit)
- **Progress sidebar** always visible with counts
- **Toast + sidebar** notifications for submission results
- **Edit mode:** inline-editable fields on card + bring Playwright browser to front
- **Empty queue:** auto-stop + "All caught up!" + n8n notification
