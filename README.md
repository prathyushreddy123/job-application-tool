# Job Application Tool

Semi-automated job application tool with a Tinder-style card review interface. Auto-fills job application forms using stored profile data, then presents each application for human approval before submission.

## Architecture

```
React (Card Stack UI)
        ↓ WebSocket + REST
FastAPI (Playwright, form filling, audit logging)
        ↓ HTTP webhooks
n8n (Google Sheets sync, notifications, scheduling)
        ↓
Google Sheets (job listings, status tracking)
```

**Stack:** Python FastAPI + React (Tailwind CSS) + Playwright + n8n (Docker)

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for n8n)

### 2. Backend Setup

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate   # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. n8n Setup

```bash
docker run -d --name n8n --restart unless-stopped \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

See [n8n/README.md](n8n/README.md) for workflow import and Google Sheets configuration.

### 5. Configuration

```bash
cp .env.example .env
# Edit .env with your settings (API key, Gemini key, etc.)
```

### 6. Run

```bash
# Terminal 1: Backend
source venv/bin/activate
python -m backend.main serve

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Demo Mode

Run without n8n or Google Sheets using mock data:

1. Start the backend: `python -m backend.main serve`
2. Start the frontend: `cd frontend && npm run dev`
3. Open the UI → check "Demo" → click "Start"
4. Review 5 sample applications using keyboard or buttons

## Usage

### Card Review Interface

| Action | Keyboard | Button |
|--------|----------|--------|
| Approve & submit | `Enter` or `→` | Green "Approve" button |
| Skip application | `←` or `S` | Gray "Skip" button |
| Emergency stop | `Esc` | Red "STOP" button |
| View screenshot | `Space` | — |
| Toggle edit mode | `E` | — |

### Workflow

1. Add job URLs to Google Sheets (status = "new")
2. n8n syncs new jobs to FastAPI every 5 minutes
3. Playwright opens each job URL and auto-fills the form
4. Review each application in the card UI
5. Approve to submit, or skip for later
6. Status updates sync back to Google Sheets

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/jobs` | List all jobs |
| POST | `/api/jobs/{id}/approve` | Approve and submit |
| POST | `/api/jobs/{id}/skip` | Skip application |
| POST | `/api/automation/start` | Start processing (?demo, ?dry_run) |
| POST | `/api/automation/stop` | Emergency stop |
| GET | `/api/automation/status` | Pipeline status |
| GET | `/api/stats` | Application statistics |
| POST | `/api/webhooks/jobs-sync` | n8n job sync webhook |
| WS | `/ws/updates` | Real-time status updates |

All endpoints (except `/health` and webhooks) require `X-API-Key: dev-key` header.

## Testing

```bash
# Backend tests (104 tests)
source venv/bin/activate
python -m pytest backend/tests/ -v

# Frontend build check
cd frontend && npm run build
```

## Project Structure

```
├── backend/
│   ├── main.py                    # FastAPI app, CLI entrypoint
│   ├── config.py                  # Pydantic settings
│   ├── auth.py                    # API key authentication
│   ├── job_store.py               # In-memory job storage
│   ├── websocket_manager.py       # WebSocket broadcast
│   ├── demo.py                    # Mock job data for demo mode
│   ├── profile.py                 # Profile/answers loading
│   ├── audit.py                   # Audit log writing
│   ├── stats.py                   # Statistics aggregation
│   ├── gemini_client.py           # Gemini AI for custom questions
│   ├── n8n_client.py              # n8n webhook client
│   ├── models/job.py              # Job, FilledField models
│   ├── automation/
│   │   ├── browser.py             # Playwright browser manager
│   │   ├── form_filler.py         # Fill-ahead pipeline
│   │   ├── rate_limiter.py        # Per-domain rate limiting
│   │   └── adapters/
│   │       ├── base.py            # Base ATS adapter
│   │       └── greenhouse.py      # Greenhouse adapter
│   ├── routes/
│   │   ├── jobs.py                # Job CRUD endpoints
│   │   ├── automation.py          # Start/stop/status
│   │   ├── webhooks.py            # n8n webhook receiver
│   │   └── stats.py               # Statistics endpoint
│   └── tests/                     # 104 unit + integration tests
├── frontend/
│   └── src/
│       ├── App.tsx                # Main layout
│       ├── components/
│       │   ├── CardStack.tsx      # Card stack with stacked visual
│       │   ├── ApplicationCard.tsx # Job card with form preview
│       │   ├── FormPreview.tsx    # Field list with status icons
│       │   ├── ProgressSidebar.tsx # Counts, activity, shortcuts
│       │   ├── TopBar.tsx         # Start button, mode toggles
│       │   ├── PanicButton.tsx    # Emergency stop button
│       │   └── ScreenshotModal.tsx # Screenshot overlay
│       ├── hooks/
│       │   ├── useJobs.ts         # Job state + WebSocket
│       │   └── useKeyboard.ts     # Keyboard shortcuts
│       └── lib/
│           ├── api.ts             # REST API client
│           ├── types.ts           # TypeScript interfaces
│           └── websocket.ts       # WebSocket client
├── n8n/
│   ├── README.md                  # n8n setup guide
│   └── workflows/                 # 4 importable workflow JSONs
├── data/
│   ├── answers.json               # Profile/form answers
│   ├── mock-jobs.json             # Demo mode data
│   └── audit/                     # Submission audit logs
└── docs/
    ├── completed-tasks.md         # Development changelog
    ├── troubleshooting.md         # Issue resolution log
    └── e2e-test-checklist.md      # E2E test procedure
```

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| n8n | http://localhost:5678 |


#### ● Now run the final full E2E test:              
                                      
● Bash(lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null; sleep 1 && cd S/home/prat/ai/job-application-tool && source /home/prat/ai/job-application-tool/venv/bin/ac…)                      
  ⎿  Running in the background (↓ to manage)                                                                                                                                                   
  ⎿  You've hit your limit · resets 1am (America/New_York)
