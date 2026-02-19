# Product Requirements Document: Automated Job Application Tool

**Version:** 1.5
**Date:** February 19, 2026
**Status:** Draft (Simplified MVP - n8n only, MCP deferred)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Personas](#2-user-personas)
3. [Core Features (MVP)](#3-core-features-mvp)
4. [Review UX Design](#4-review-ux-design)
5. [Technical Architecture](#5-technical-architecture)
6. [Data Flow](#6-data-flow)
7. [Google Sheets Structure](#7-google-sheets-structure)
8. [Answers Database Structure](#8-answers-database-structure)
9. [Testing Strategy](#9-testing-strategy)
10. [Rollback & Audit System](#10-rollback--audit-system)
11. [Emergency Controls](#11-emergency-controls)
12. [Challenges & Mitigations](#12-challenges--mitigations)
13. [Implementation Roadmap](#13-implementation-roadmap)
14. [Existing Tools Analysis](#14-existing-tools-analysis)
15. [Legal & Ethical Considerations](#15-legal--ethical-considerations)
16. [Success Metrics](#16-success-metrics)
17. [Integration Details (n8n in MVP, MCP in Phase 2)](#17-integration-details-n8n-in-mvp-mcp-in-phase-2)
18. [Appendix](#18-appendix)

---

## 1. Executive Summary

### Problem Statement

Job seekers spend an estimated 3-5 hours daily on repetitive application tasks:
- Copying personal information into similar forms
- Uploading the same resume and cover letter repeatedly
- Answering identical screening questions across portals
- Tracking application status across multiple spreadsheets

This manual process leads to application fatigue, inconsistent data entry, and missed opportunities due to volume limitations.

### Solution

A semi-automated job application tool that handles 80% of the application process by:
- Reading job listings from a centralized Google Sheet
- Auto-filling application forms with stored profile data
- Attaching resumes from local storage
- Tracking application status automatically in Google Sheets
- **Requiring human review before every submission (zero-tolerance for errors)**

### Target Market & Business Model

| Phase | Target | Timeline |
|-------|--------|----------|
| **Phase 1** | Personal use (active job search) | 2 weeks (prototype) |
| **Phase 2** | Portfolio/learning project showcase | Ongoing |
| **Phase 3** | Sellable product ($10-20/month) | 3-6 months |

### Value Proposition

| Metric | Manual Process | With Tool |
|--------|----------------|-----------|
| Time per application | 15-30 minutes | 2-5 minutes |
| Applications per day | 5-10 | 20-30 |
| Data entry errors | Frequent | Minimal (human-reviewed) |
| Tracking accuracy | Manual/forgotten | Automatic |

### Key Differentiator

**Best-in-class review UX** - Tinder-style card stack interface for rapid application approval. Users can review and approve 20-30 applications efficiently with keyboard shortcuts.

---

## 2. User Personas

### Primary: Active Job Seeker (Self)

**Situation:** Actively job hunting, needs tool working ASAP

**Goals:**
- Apply to 20-30 jobs per day efficiently
- Zero tolerance for application errors
- Track all applications in one place
- Reduce repetitive data entry fatigue

**Pain Points:**
- Spending 4+ hours daily on applications
- Losing track of which companies received applications
- Making typos when entering the same info repeatedly
- Concerned about TOS/legal risks with automation

**Tech Comfort:** Learning Python and React (will need guidance)

### Secondary: Future Paying Customer

**Situation:** Job seekers willing to pay $10-20/month for automation

**Goals:**
- Self-hosted option for privacy
- Simple setup and usage
- Reliable automation with human oversight

---

## 3. Core Features (MVP)

### 3.1 Input Management

#### Google Sheets Integration (Primary Data Source)
- **Read:** Pull job URLs, titles, companies, and metadata from designated sheet
- **Write:** Update status (applied/failed/skipped) and timestamps
- **Filter:** Process only rows matching specified criteria (status = "new")
- **No SQLite:** Sheets is the single source of truth for MVP

#### Local File Storage
- **Resume:** Single generic resume stored locally (PDF). Data model designed to support multiple role-specific resumes in Phase 2
- **Cover Letter:** Deferred entirely from MVP. If a form has a cover letter field, skip it and flag ⚠
- **No Google Drive:** Simplifies MVP, local files only

#### Answers Database
- JSON-based storage for common form field responses
- Support for nested data (education history, work experience)
- **Skip and flag:** Unknown fields left blank, marked for manual completion

### 3.2 Automation Engine

#### Browser Automation (Playwright)
- **Primary browser:** Chromium
- **Session persistence:** Persistent browser profile via Playwright `user_data_dir`
  - Default path: `./data/browser-profile/`
  - Configurable via `BROWSER_PROFILE_DIR` env var
  - Gitignored — contains cookies, login state, cached data
  - Survives restarts — no need to re-login between sessions
- **Headed mode:** Always visible for CAPTCHA handling
- **CAPTCHA handling:** Pop up browser window for user to solve, then continue

#### Form Detection & Auto-Fill
- Identify common field types (name, email, phone, address)
- Match form labels to stored answer database via adapter-specific hardcoded label maps
- Handle dropdowns, radio buttons, checkboxes, and text fields
- **Multi-page navigation:** Auto-detect and click "Next" buttons, fill each page sequentially, screenshot the final review page only

#### File Attachment Handling
- Detect upload buttons and file input fields
- Support native file input
- Handle common upload variations

#### ATS Adapters (MVP: Greenhouse Only)
- **Greenhouse:** First adapter - structured, predictable forms
- **Generic fallback:** Basic heuristic detection for direct sites
- Future: Workday, Lever, LinkedIn

#### ATS Auto-Detection
- Auto-detect ATS type from URL pattern (e.g., `boards.greenhouse.io` → greenhouse, `myworkdayjobs.com` → workday)
- If user explicitly sets `portal_type` in Google Sheets, respect their choice (manual override)
- If `portal_type` is blank, auto-detect fills it in

### 3.3 Tracking & Status Management

#### Automatic Status Updates (in Google Sheets)
- Mark jobs as "applied" on successful submission
- Mark as "failed" with error log on failures
- Mark as "skipped" for rejected/unknown forms

#### Form Data Logging
- Store all field values submitted per application (JSON)
- Enable audit trail and rollback investigation
- Screenshots of filled forms before submission

---

## 4. Review UX Design

### 4.1 Core Concept: Tinder-Style Card Stack

The primary differentiator is a fast, intuitive review interface for approving applications before submission.

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION REVIEW                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  CARD 3 of 15                        [GREENHOUSE]   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  Company:    TechCorp Inc                           │   │
│  │  Position:   Senior Software Engineer               │   │
│  │  Location:   Remote                                 │   │
│  │                                                     │   │
│  │  ─────────── FORM PREVIEW ───────────              │   │
│  │                                                     │   │
│  │  First Name:     Alex                    ✓         │   │
│  │  Last Name:      Johnson                 ✓         │   │
│  │  Email:          alex@email.com          ✓         │   │
│  │  Phone:          +1-555-123-4567         ✓         │   │
│  │  LinkedIn:       linkedin.com/in/alex    ✓         │   │
│  │  Years Exp:      5                       ✓         │   │
│  │  Sponsorship:    No                      ✓         │   │
│  │  Salary:         (skipped - unknown)     ⚠         │   │
│  │                                                     │   │
│  │  Resume:         resume_2026.pdf         ✓         │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│     [← SKIP]                              [APPROVE →]       │
│        (S)                                    (Enter)       │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│  Keyboard: ← Skip | → Approve | Enter Submit | Esc Stop    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Card Content

Each card displays:
- **Header:** Company name, job title, ATS type
- **Form Preview:** All filled field values with status indicators
  - ✓ = Successfully filled
  - ⚠ = Skipped/unknown field (needs manual attention)
  - ✗ = Failed to fill
- **Attachments:** Resume/cover letter status

### 4.3 Keyboard Shortcuts (Essential)

| Key | Action |
|-----|--------|
| `→` or `Enter` | Approve and auto-submit in background |
| `←` or `S` | Skip (mark as skipped in sheet) |
| `Escape` | Panic stop - halt all processing |
| `Space` | View full form screenshot |
| `E` | Edit/manually complete this application |

### 4.4 Approval Flow (Pipeline Model)

The tool uses a **fill-ahead pipeline** for throughput:
- While the user reviews the current card, the next **2-3 forms** are being filled in background browser contexts
- Forms are NOT filled all at once (prevents staleness)
- On **approve**, the form is **re-filled fresh** before submission (guarantees data freshness even if user took a break)
- If re-fill fails: **retry once automatically**, then **pause and show browser** for manual intervention

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Card Stack  │────▶│   Approve    │────▶│  Re-fill     │────▶│ Auto-Submit  │
│   (Review)   │     │   (Enter)    │     │  (Fresh)     │     │ (Background) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                                         │                      │
       │ Skip (←)                          Fail? Retry 1x              │
       ▼                                         │                      ▼
┌──────────────┐                         ┌──────────────┐     ┌──────────────┐
│ Mark Skipped │                         │ Pause + Show │     │ Mark Applied │
│  in Sheet    │                         │   Browser    │     │  in Sheet    │
└──────────────┘                         └──────────────┘     └──────────────┘
```

**Fill-ahead buffer:** 2-3 forms pre-filled while user reviews current card

### 4.5 UI Framework & Polish

**Framework:** shadcn/ui + Tailwind CSS
- Pre-built accessible components (cards, buttons, dialogs, toasts)
- Utility-first styling for rapid development
- Clean, modern look suitable for portfolio showcase

**Target: Clean Minimal**
- Simple, functional design
- Not ugly, but not over-polished
- Presentable for portfolio/demo purposes

### 4.6 Progress Sidebar (Always Visible)

An always-visible sidebar showing batch progress:
- Cards approved / skipped / failed / pending counts
- Currently filling (fill-ahead status)
- Submission results update in real-time

### 4.7 Notification System

- **Toast notifications:** Small popups in corner for immediate feedback ("✓ TechCorp submitted", "✗ DataInc failed"). Auto-dismiss after a few seconds
- **Sidebar updates:** Persistent history in the progress sidebar with colored status indicators
- Both systems work together — toasts for attention, sidebar for reference

### 4.8 Form Preview & Screenshots

- **Default view:** Structured field list with ✓/⚠/✗ indicators
- **Space key:** Opens full screenshot of the filled form in a modal overlay
- Screenshots captured of the final review page after auto-navigating all form pages

### 4.9 Edit Mode (E Key)

Pressing 'E' on a card provides two levels of editing:
1. **Inline edit on card:** Simple fields become editable text inputs directly in the React card UI
2. **Browser focus:** For complex edits, brings the Playwright browser window to the front so user can interact with the actual form

AI-generated fields (🤖) are always directly editable on the card without needing to press 'E'

---

## 5. Technical Architecture

### 5.1 Technology Stack (Simplified MVP)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend** | Python 3.11+ / FastAPI | Playwright orchestration, WebSocket to React |
| **Frontend** | React | Modern UI, component-based, card stack |
| **Browser Automation** | Playwright | Auto-wait, modern API, cross-browser |
| **Workflow Automation** | n8n (self-hosted) | Google Sheets, notifications, scheduling |
| **Local Files** | Direct file I/O | Simple JSON read/write (MCP deferred to Phase 2) |
| **Data Storage** | Google Sheets (via n8n) | Job listings and status tracking |
| **Development** | Windows | Primary development environment |

### 5.2 Why This Stack

| Component | Handles | Why This Choice |
|-----------|---------|-----------------|
| **n8n** | Sheets, Email, Slack, Cron | Built-in nodes, 100% reliable, saves ~400 lines |
| **Direct file I/O** | answers.json, audit logs | Simpler than MCP for MVP, fewer moving parts |
| **FastAPI** | Playwright, WebSocket | Real-time control, async support |
| **React** | Card stack UI | Best for interactive keyboard-driven UX |

### 5.3 What n8n Replaces (Code We Don't Write)

| Originally Planned | Now Handled By | Lines Saved |
|--------------------|----------------|-------------|
| `sheets/client.py` | n8n Google Sheets node | ~200 lines |
| `utils/notifications.py` | n8n Email/Slack nodes | ~100 lines |
| APScheduler setup | n8n Schedule trigger | ~50 lines |
| Google API OAuth | n8n built-in OAuth | ~100 lines |

### 5.4 What We Keep Simple (MCP Deferred)

| MVP Approach | Phase 2 (MCP) | Why Defer |
|--------------|---------------|-----------|
| `json.load()` / `json.dump()` | MCP Filesystem server | Fewer moving parts, faster MVP |
| Direct file paths | MCP file operations | MCP adds value when Claude needs access |

### 5.5 Project Structure (Simplified)

```
job-auto-apply/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration
│   ├── n8n_client.py           # HTTP client to call n8n webhooks
│   ├── profile.py              # Load answers.json (simple file I/O)
│   ├── audit.py                # Write audit logs (simple file I/O)
│   ├── models/
│   │   └── job.py              # Job listing models
│   ├── automation/
│   │   ├── browser.py          # Playwright management
│   │   ├── form_filler.py      # Generic form detection
│   │   └── adapters/
│   │       ├── base.py         # Base adapter
│   │       └── greenhouse.py   # Greenhouse adapter
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── CardStack.tsx   # Main review interface
│   │   │   ├── ApplicationCard.tsx
│   │   │   ├── FormPreview.tsx
│   │   │   └── PanicButton.tsx
│   │   └── hooks/
│   │       └── useKeyboard.ts  # Keyboard shortcuts
│   ├── package.json
│   └── vite.config.ts
├── n8n/
│   └── workflows/              # Exported n8n workflow JSONs
│       ├── sync-jobs.json
│       ├── update-status.json
│       ├── error-notification.json
│       └── daily-summary.json
├── data/
│   ├── answers.json            # Form answers (direct file read)
│   ├── resume.pdf              # Single resume
│   └── audit/                  # Submission logs (direct file write)
├── credentials/
│   └── .gitkeep
└── README.md
```

### 5.6 API Endpoints

```python
# FastAPI routes
# All endpoints require API key via X-API-Key header (simple auth)

# Job management (jobs come from n8n, not direct Sheets access)
GET  /api/jobs                    # Get cached jobs (synced from n8n)
POST /api/jobs/{id}/approve       # Approve and submit (triggers re-fill + submit)
POST /api/jobs/{id}/skip          # Skip application
GET  /api/jobs/{id}/preview       # Get form preview data

# Automation control
POST /api/automation/start        # Start processing batch (?demo=true for demo mode)
POST /api/automation/stop         # Panic stop
GET  /api/automation/status       # Current processing status

# Analytics
GET  /api/stats                   # Aggregate stats from audit logs (total applied, success rate, top skipped fields)

# n8n webhook receivers
POST /api/webhooks/jobs-sync      # n8n calls this with new jobs from Sheets
POST /api/webhooks/schedule       # n8n triggers scheduled runs

# WebSocket
WS   /ws/updates                  # Real-time status updates to React
```

### 5.7 n8n Workflows

```
WORKFLOW 1: Sync Jobs from Sheets
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Schedule Trigger│────▶│ Google Sheets   │────▶│ HTTP Request    │
│ (every 5 min)   │     │ Get rows where  │     │ POST /api/      │
│                 │     │ status = "new"  │     │ webhooks/jobs   │
└─────────────────┘     └─────────────────┘     └─────────────────┘

WORKFLOW 2: Update Job Status
┌─────────────────┐     ┌─────────────────┐
│ Webhook Trigger │────▶│ Google Sheets   │
│ /job-status     │     │ Update row      │
│ {id, status}    │     │ (applied/failed)│
└─────────────────┘     └─────────────────┘

WORKFLOW 3: Error Notification
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Webhook Trigger │────▶│ IF Node         │────▶│ Email + Slack   │
│ /job-failed     │     │ failures >= 3   │     │ "Paused - check │
│                 │     │                 │     │  errors"        │
└─────────────────┘     └─────────────────┘     └─────────────────┘

WORKFLOW 4: Daily Summary
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Cron Trigger    │────▶│ Google Sheets   │────▶│ Email           │
│ (6pm daily)     │     │ Count by status │     │ Daily report    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 5.8 Simple File I/O (MVP)

```python
# backend/profile.py - Simple, no MCP needed for MVP
import json
from pathlib import Path

DATA_DIR = Path("data")

def load_profile() -> dict:
    """Load user profile from answers.json"""
    with open(DATA_DIR / "answers.json") as f:
        return json.load(f)

def save_audit_log(job_id: str, data: dict):
    """Save audit log for an application"""
    audit_dir = DATA_DIR / "audit"
    audit_dir.mkdir(exist_ok=True)

    filename = f"{data['timestamp']}_{job_id}.json"
    with open(audit_dir / filename, "w") as f:
        json.dump(data, f, indent=2)
```

**Why this is fine for MVP:**
- FastAPI reads files directly - no need for MCP abstraction
- ~20 lines of code vs MCP client setup
- MCP adds value in Phase 2 when Claude assists with form matching

---

## 6. Data Flow

### 6.1 Simplified Architecture (MVP with n8n)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND                               │
│                    (Card Stack Review UI)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                              WebSocket + REST
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Playwright │  │  Greenhouse │  │  File I/O   │                 │
│  │   Browser   │  │   Adapter   │  │ (direct)    │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└───────────────────────────┬─────────────────┬───────────────────────┘
                            │                 │
              Webhooks (HTTP POST)      Direct read/write
                            │                 │
                            ▼                 ▼
                   ┌─────────────────┐  ┌─────────────────┐
                   │      n8n        │  │   Local Files   │
                   │ ┌─────────────┐ │  │ ┌─────────────┐ │
                   │ │Google Sheets│ │  │ │answers.json │ │
                   │ │(read/write) │ │  │ │audit/*.json │ │
                   │ ├─────────────┤ │  │ │resume.pdf   │ │
                   │ │ Email/Slack │ │  │ └─────────────┘ │
                   │ │  (alerts)   │ │  └─────────────────┘
                   │ ├─────────────┤ │
                   │ │Cron Triggers│ │
                   │ └─────────────┘ │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Google Sheets  │
                   │  (job listings) │
                   └─────────────────┘
```

**Key simplification:** No MCP layer. FastAPI reads/writes files directly.

### 6.2 Application Processing Flow (with n8n)

```
┌──────────────────┐
│  n8n: Cron or    │
│  User: "Start"   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ n8n: Fetch from  │────▶│ n8n: POST to     │
│ Google Sheets    │     │ FastAPI webhook  │
│ (status = new)   │     │ /jobs-sync       │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ FastAPI: Queue   │
                         │ jobs for process │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ FastAPI: Load    │
                         │ answers.json     │
                         │ (direct file I/O)│
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Playwright: Open │
                         │ job URL, detect  │
                         │ ATS, load adapter│
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Fill form fields │
                         │ Attach resume    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ FastAPI: Write   │
                         │ audit log, take  │
                         │ screenshot       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ WebSocket: Send  │
                         │ to Card Stack    │
                         └────────┬─────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ APPROVE (Enter)  │     │ SKIP (←)         │     │ PANIC (Esc)      │
│ Playwright submit│     │ n8n: Update      │     │ Stop everything  │
│ n8n: Update sheet│     │ sheet "skipped"  │     │ Save state       │
│ to "applied"     │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ n8n: Send Slack/ │     │ n8n: If 3+ fails │
│ Email on failure │     │ send alert       │
└──────────────────┘     └──────────────────┘
```

---

## 7. Google Sheets Structure

### 7.1 Columns (Simplified)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `id` | UUID | Auto | Unique identifier, generated by n8n on first sync |
| `job_url` | URL | Yes | Direct link to job application page |
| `company` | Text | Yes | Company name |
| `job_title` | Text | Yes | Position title |
| `location` | Text | No | Job location (city, state, or "Remote") |
| `portal_type` | Dropdown | No | `greenhouse` / `workday` / `direct` / `lever` (auto-detected from URL if blank) |
| `priority` | Dropdown | No | `high` / `medium` / `low` (default: medium) |
| `status` | Dropdown | Yes | `new` / `applied` / `failed` / `skipped` |
| `date_added` | Date | Yes | When row was added |
| `date_applied` | Date | Auto | When application submitted (tool fills) |
| `notes` | Text | No | Any specific notes |
| `error_log` | Text | Auto | If failed, reason why (tool fills) |

**Note:** The `id` column is the stable identifier used across the API (`/api/jobs/{id}/approve`). Generated as UUID by n8n when a row is first synced. The `portal_type` column is auto-detected from the job URL pattern if left blank.

### 7.2 Job Entry Method

**Manual copy-paste** for MVP:
1. Find job on career site
2. Copy URL to sheet
3. Fill company, title, location
4. Select portal_type from dropdown
5. Status defaults to "new"

### 7.3 Data Validation

```
portal_type: One of [greenhouse, workday, direct, lever, linkedin]
priority: One of [high, medium, low]
status: One of [new, applied, failed, skipped]
```

---

## 8. Answers Database Structure

### 8.1 Core Profile (answers.json)

```json
{
  "personal": {
    "first_name": "Alex",
    "last_name": "Johnson",
    "full_name": "Alex Johnson",
    "email": "alex.johnson@email.com",
    "phone": "+1-555-123-4567",
    "address": {
      "street": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94102",
      "country": "United States"
    }
  },

  "professional": {
    "linkedin_url": "https://linkedin.com/in/alexjohnson",
    "portfolio_url": "https://alexjohnson.dev",
    "github_url": "https://github.com/alexjohnson",
    "years_experience": "5",
    "current_title": "Senior Software Engineer",
    "current_company": "Previous Corp"
  },

  "work_authorization": {
    "authorized_us": "Yes",
    "sponsorship_required": "No",
    "visa_status": "US Citizen"
  },

  "preferences": {
    "salary_expectation": "Open to discuss based on total compensation",
    "available_start": "2 weeks notice",
    "willing_to_relocate": "Yes",
    "work_preference": "Remote or Hybrid"
  },

  "education": [
    {
      "degree": "Bachelor of Science",
      "major": "Computer Science",
      "university": "University of California, Berkeley",
      "graduation_year": "2019",
      "gpa": "3.7"
    }
  ],

  "work_history": [
    {
      "company": "Previous Corp",
      "title": "Senior Software Engineer",
      "start_date": "2021-06",
      "end_date": "present",
      "description": "Led development of microservices architecture..."
    }
  ],

  "demographics": {
    "gender": "Prefer not to say",
    "ethnicity": "Prefer not to say",
    "veteran_status": "No",
    "disability_status": "Prefer not to say"
  }
}
```

### 8.2 Field Matching Strategy

Each ATS adapter owns a **hardcoded label map** that maps form field labels/selectors to `answers.json` paths:

```python
# Example: backend/automation/adapters/greenhouse.py
FIELD_MAP = {
    "first_name": "personal.first_name",
    "last_name": "personal.last_name",
    "email": "personal.email",
    "phone": "personal.phone",
    "linkedin_url": "professional.linkedin_url",
    # ... adapter-specific mappings
}
```

**Matching priority:**
1. ATS-specific HTML selectors/field names (most reliable)
2. Hardcoded label map lookup
3. Pre-built answer bank for common custom questions
4. Gemini AI fallback for unmatched free-text questions (see 8.3)
5. Skip and flag ⚠ if all above fail

### 8.3 Custom Question Handling (Answer Bank + Gemini Fallback)

Greenhouse apps frequently include custom free-text questions ("Why do you want to work here?", "Describe a challenging project"). These are handled in two tiers:

**Tier 1: Pre-built Answer Bank**
Common Q&A pairs stored in `answers.json` under a `custom_answers` section:
```json
{
  "custom_answers": {
    "willing_to_relocate": "Yes, I am open to relocation",
    "why_interested": "I'm passionate about building impactful products...",
    "work_authorization": "Yes, I am authorized to work in the US"
  }
}
```

**Tier 2: Gemini AI Fallback**
When no answer bank match is found, call the Gemini API (free tier) to generate a contextual answer based on the question + user profile.

- **Why Gemini:** Free tier minimizes API costs for MVP
- **AI-generated answers are auto-filled** into the form but displayed as **directly editable fields** on the review card (no need to press 'E')
- Flagged with a 🤖 indicator so the user knows it was AI-generated
- User can edit inline before approving

### 8.4 Unknown Field Handling

When all matching strategies fail:
1. **Skip the field** - leave it blank
2. **Flag in preview** - show ⚠ indicator on card
3. **User decides** - approve anyway or skip for manual completion

---

## 9. Testing Strategy

### 9.1 Dry-Run Mode

The primary testing mechanism is **dry-run mode**:
- Fills all form fields
- Attaches resume
- Takes screenshot
- **Does NOT click submit button**
- Logs what would have been submitted

```bash
# CLI command
python -m backend.main apply --dry-run

# API endpoint
POST /api/automation/start?dry_run=true
```

### 9.2 Unit Tests (Key Critical Paths)

MVP includes unit tests for critical business logic:
- **Field matching:** Adapter label map lookups return correct answers.json paths
- **Adapter parsing:** Greenhouse adapter correctly identifies form fields from HTML
- **answers.json loading:** Profile loading handles missing fields, malformed JSON gracefully
- **ATS auto-detection:** URL pattern matching returns correct portal_type
- **Audit log writing:** Logs are written with correct structure and timing data

Framework: pytest (backend), Vitest (frontend — if needed)

### 9.3 Demo Mode

A `--demo` flag allows running the tool without n8n or Google Sheets:
```bash
python -m backend.main serve --demo
# or
POST /api/automation/start?demo=true
```
- Loads mock jobs from a local JSON fixture file
- Skips n8n webhook calls
- Great for portfolio showcase, quick demos, and development

### 9.4 Test Targets

- Use **public Greenhouse job postings** for testing
- Find active postings that won't affect real applications
- Test against known companies using Greenhouse (Stripe, Airbnb, Figma, etc.)

### 9.5 Testing Checklist

| Test Case | Method |
|-----------|--------|
| Form field detection | Dry-run, verify screenshot |
| Resume upload | Dry-run, check attachment appears |
| Multi-page forms | Dry-run through all pages |
| Dropdown selection | Dry-run, verify selections |
| Error handling | Intentionally break adapter |
| Session persistence | Run twice, verify no re-login |

---

## 10. Rollback & Audit System

### 10.1 Form Data Logging

Every application attempt is logged to JSON:

```json
// data/audit/2026-02-02_techcorp_12345.json
{
  "timestamp": "2026-02-02T14:30:00Z",
  "job_id": "a1b2c3d4-uuid",
  "job_url": "https://boards.greenhouse.io/techcorp/jobs/12345",
  "company": "TechCorp",
  "job_title": "Senior Engineer",
  "adapter": "greenhouse",
  "status": "submitted",
  "fields_filled": {
    "first_name": "Alex",
    "last_name": "Johnson",
    "email": "alex@email.com",
    "phone": "+1-555-123-4567",
    "linkedin": "linkedin.com/in/alex",
    "resume": "resume_2026.pdf"
  },
  "fields_skipped": ["salary_expectation"],
  "fields_ai_generated": ["custom_question_1"],
  "screenshot": "screenshots/2026-02-02_techcorp_12345.png",
  "timing": {
    "url_opened_at": "2026-02-02T14:28:00Z",
    "form_filled_at": "2026-02-02T14:28:45Z",
    "user_reviewed_at": "2026-02-02T14:29:30Z",
    "submitted_at": "2026-02-02T14:30:00Z"
  }
}
```

**Timing data** is recorded per application for analytics but not displayed in the UI sidebar for MVP.

### 10.2 What Can Be Recovered

| Scenario | Recovery Method |
|----------|-----------------|
| Wrong info submitted | Check audit log, contact company to correct |
| Duplicate application | Review audit log dates, explain to company |
| Missing field | Check `fields_skipped`, manually update if needed |
| Application error | Review screenshot, retry manually |

### 10.3 No True "Undo"

**Important:** Once an application is submitted, it cannot be automatically undone. The audit system provides:
- Evidence of what was submitted
- Contact information for corrections
- Learning for future improvements

---

## 11. Emergency Controls

### 11.1 Panic Button

A prominent, always-visible emergency stop:

```
┌─────────────────────────────────────┐
│  🛑 STOP ALL (Esc)                  │
│  Immediately halt all automation   │
└─────────────────────────────────────┘
```

**Behavior:**
1. Stop all browser automation immediately
2. Do not submit current form
3. Save current state to resume later
4. Close browser gracefully
5. Send email notification (if configured)

### 11.2 Keyboard Shortcut

`Escape` key triggers panic stop from anywhere in the UI.

### 11.3 Auto-Stop Conditions

Automatically stop processing when:
- 3 consecutive failures
- CAPTCHA detected
- Login wall encountered
- Rate limit response received
- Unknown critical error
- **Job queue is empty** — show "All caught up!" in UI and send notification via n8n

### 11.4 n8n Offline Resilience

When n8n is unreachable (e.g., Docker container stopped):
- **Queue failed n8n calls** in memory with the data that needs to be synced
- **Retry with exponential backoff** (1s, 2s, 4s, 8s... up to 5 min)
- **Auto-sync when n8n comes back online**
- Show "Sheets sync unavailable — queued" warning in the UI sidebar
- Automation can continue — submissions work, status updates are queued

---

## 12. Challenges & Mitigations

### 12.1 Technical Challenges

| Challenge | Impact | Mitigation Strategy |
|-----------|--------|---------------------|
| **Different form structures per ATS** | High | Start with Greenhouse only. Build modular adapters. |
| **CAPTCHA/bot detection** | High | Open browser window for user to solve, then continue. |
| **Authentication walls** | Medium | Manual login once, persist session cookies. |
| **Rate limiting by portals** | Medium | Random delays (150-750ms). Per-domain configurable rate limits (default 5/hour/domain). |
| **File upload variations** | Medium | Start with native file input only. |

### 12.2 Legal/TOS Risk (Top Concern)

| Platform | Risk Level | Recommendation |
|----------|------------|----------------|
| Direct company sites | Low | Safe to automate |
| Greenhouse | Low | No explicit prohibition |
| Workday | Medium | Gray area - user's choice |
| LinkedIn | **High** | Skip or use with explicit warning |
| Indeed | **High** | Skip entirely |

**User-Controlled Risk Levels:**
- Each platform has a configurable risk toggle
- High-risk platforms require explicit user acknowledgment
- Users can disable specific platforms entirely

---

## 13. Implementation Roadmap

### Phase 1: Prototype (2 Weeks)

**Goal:** Vertical slice - one complete flow working end-to-end with n8n

#### Week 1: Infrastructure + Backend
- [ ] **n8n Setup**
  - [ ] Docker install and run n8n
  - [ ] Configure Google Sheets OAuth in n8n
  - [ ] Create Workflow 1: Sync Jobs (Sheets → Webhook)
  - [ ] Create Workflow 2: Update Status (Webhook → Sheets)
  - [ ] Create Workflow 3: Error Notification (Webhook → Email)
- [ ] **FastAPI Backend**
  - [ ] Project setup with webhook endpoints
  - [ ] Simple file I/O for answers.json and audit logs
  - [ ] Playwright browser setup
  - [ ] Greenhouse adapter (basic)
  - [ ] Dry-run mode

#### Week 2: Frontend + Integration
- [ ] React project setup (Vite + TypeScript)
- [ ] Card stack component
- [ ] Form preview display
- [ ] Keyboard shortcuts (Enter/←/Esc)
- [ ] Panic button
- [ ] WebSocket integration
- [ ] Create Workflow 4: Daily Summary
- [ ] End-to-end testing

#### Deliverables
- Working prototype with n8n handling Sheets/notifications
- Simple file I/O for local data (no MCP complexity)
- Can process 1 Greenhouse application end-to-end
- Card stack review UI functional
- Dry-run and submit modes working

#### Success Criteria
- n8n workflows trigger correctly
- answers.json loads successfully
- Successfully dry-run 5 Greenhouse applications
- Successfully submit 1 real application (with approval)
- Keyboard navigation works smoothly
- Email notification sent on failure

---

### Phase 2: Polish & Expand (Weeks 3-4)

- [ ] **MCP Integration**
  - [ ] Add MCP Filesystem server for standardized file access
  - [ ] Prepare for Claude-assisted form matching
- [ ] Additional ATS adapters (Workday, Lever)
- [ ] Error handling improvements
- [ ] UI polish and animations
- [ ] Documentation

---

### Phase 3: Production Ready (Months 2-3)

- [ ] Cloud deployment (Railway/Render)
- [ ] User authentication
- [ ] Multiple user support
- [ ] Stripe billing integration
- [ ] Landing page

---

## 14. Existing Tools Analysis

### 14.1 Competitive Landscape

| Tool | Price | Approach | Our Advantage |
|------|-------|----------|---------------|
| **LazyApply** | $99/mo | Fully automated, cloud | Privacy (self-hosted), cheaper |
| **Sonara** | $19/mo | Easy Apply focus | Better review UX, more control |
| **AIHawk** | Free (OSS) | GPT-powered | Simpler setup, no API costs |
| **EasyApplyJobsBot** | Free (OSS) | Selenium-based | Playwright (more stable), better UX |

### 14.2 Our Differentiator

**Best Review UX** - Competitors either:
- Auto-submit without review (risky)
- Have clunky approval flows (slow)

We offer: Fast, keyboard-driven, Tinder-style review that maintains human oversight while enabling high volume.

---

## 15. Legal & Ethical Considerations

### 15.1 User-Controlled Risk Levels

```json
// config.json
{
  "platform_settings": {
    "greenhouse": {
      "enabled": true,
      "risk_level": "low",
      "requires_acknowledgment": false
    },
    "workday": {
      "enabled": true,
      "risk_level": "medium",
      "requires_acknowledgment": true
    },
    "linkedin": {
      "enabled": false,
      "risk_level": "high",
      "requires_acknowledgment": true,
      "warning": "LinkedIn explicitly prohibits automation. High ban risk."
    }
  }
}
```

### 15.2 Best Practices

1. **Human-in-the-loop:** Every application reviewed before submission
2. **Rate limiting:** Never exceed 10 applications per hour
3. **Respect robots.txt:** Check before automation
4. **No spam:** Only apply to genuinely interested positions
5. **Accurate information:** Never submit false data
6. **Session authenticity:** Use real browser, headed mode

### 15.3 Documentation Warnings

Prominent warnings in README and UI about:
- TOS risks per platform
- Potential account bans
- Responsibility lies with user

---

## 16. Success Metrics

### 16.1 Prototype Success Criteria

| Metric | Target |
|--------|--------|
| Greenhouse applications (dry-run) | 10 successful |
| Greenhouse applications (real) | 5 successful |
| Form field accuracy | 90%+ |
| Review speed (per card) | <30 seconds |
| Keyboard shortcut usage | 80%+ of actions |

### 16.2 Production Success Criteria

| Metric | Target |
|--------|--------|
| Daily throughput | 20-30 applications |
| Failure rate | <20% |
| Time per application | <5 minutes (including review) |
| User satisfaction | Would pay $10-20/mo |

---

## 17. Integration Details (n8n in MVP, MCP in Phase 2)

This section documents the n8n integration used in MVP and MCP planned for Phase 2.

### 17.1 n8n in MVP (100% Certain - Built-in Nodes)

n8n handles all Google Sheets operations and notifications using built-in, production-ready nodes.

#### n8n Nodes Used

| Node | Purpose | Certainty |
|------|---------|-----------|
| **Google Sheets** | Read job listings, write status updates | ✅ 100% - millions use this |
| **Gmail / SMTP Email** | Send failure alerts, daily summaries | ✅ 100% |
| **Slack** | Real-time error notifications | ✅ 100% |
| **Webhook** | Receive events from FastAPI | ✅ 100% |
| **HTTP Request** | Call FastAPI endpoints | ✅ 100% |
| **Schedule Trigger** | Daily summary at 6pm, job sync every 5min | ✅ 100% |
| **IF / Switch** | Conditional logic (3+ failures → alert) | ✅ 100% |

#### n8n Workflow Specifications

**Workflow 1: Sync Jobs from Sheets**
```
Trigger:    Schedule (every 5 minutes)
Action 1:   Google Sheets → Get rows where status = "new"
Action 2:   Code Node → Deduplicate by job_url (skip if URL already seen)
Action 3:   Code Node → Generate UUID for rows missing an id
Action 4:   Google Sheets → Write generated UUIDs back to id column
Action 5:   Code Node → Auto-detect portal_type from URL pattern if blank
Action 6:   HTTP Request → POST to FastAPI /api/webhooks/jobs-sync
Output:     Deduplicated jobs with stable IDs queued in FastAPI
```

**Workflow 2: Update Job Status**
```
Trigger:    Webhook /job-status-update
Input:      { row_id, status, date_applied, error_log }
Action:     Google Sheets → Update row by ID
Output:     Sheet updated with new status
```

**Workflow 3: Error Notification**
```
Trigger:    Webhook /job-failed
Input:      { job_url, company, error, failure_count }
Condition:  IF failure_count >= 3
Action A:   Email + Slack → "Automation paused - 3 consecutive failures"
Action B:   (else) Log only, continue processing
```

**Workflow 4: Daily Summary**
```
Trigger:    Schedule (6:00 PM daily)
Action 1:   Google Sheets → Get all rows from today
Action 2:   Code Node → Count by status (applied, failed, skipped)
Action 3:   Email → Send summary report
```

### 17.2 MCP (Deferred to Phase 2)

MCP is **not used in MVP** to reduce complexity. Simple Python file I/O handles local files instead.

#### MVP Approach (Simple File I/O)

```python
# backend/profile.py - What we use in MVP
import json
from pathlib import Path

DATA_DIR = Path("data")

def load_profile() -> dict:
    """Load user profile from answers.json"""
    with open(DATA_DIR / "answers.json") as f:
        return json.load(f)

def save_audit_log(job_id: str, data: dict):
    """Save audit log for an application"""
    audit_dir = DATA_DIR / "audit"
    audit_dir.mkdir(exist_ok=True)
    filename = f"{data['timestamp']}_{job_id}.json"
    with open(audit_dir / filename, "w") as f:
        json.dump(data, f, indent=2)
```

#### Why MCP is Deferred

| Concern | Decision |
|---------|----------|
| **Complexity** | MCP adds another integration layer to debug |
| **Learning curve** | Already learning Python + React + n8n |
| **Necessity** | FastAPI can read files directly - no abstraction needed |
| **Timeline** | 2 weeks is tight, fewer moving parts = higher success |

#### Phase 2: When to Add MCP

MCP becomes valuable when:
1. Claude needs to access files (AI-assisted form matching)
2. Multiple services need shared file access
3. Building custom MCP tools for ATS detection

```json
// Future: mcp/config.json (Phase 2)
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    }
  }
}
```

### 17.3 n8n Setup Instructions

```bash
# 1. Install Docker (if not already)
# Windows: Install Docker Desktop

# 2. Run n8n
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# 3. Access n8n UI
# Open http://localhost:5678

# 4. Configure Google Sheets OAuth
# - Create Google Cloud credentials
# - Add to n8n credentials store

# 5. Import workflows from n8n/workflows/*.json
```

### 17.4 What We DON'T Use in MVP (Avoided Complexity)

| Integration | Why Not in MVP |
|-------------|----------------|
| **MCP Filesystem** | Simple file I/O is sufficient, adds complexity |
| MCP Google Sheets server | n8n built-in node is more reliable |
| MCP Puppeteer server | We use Playwright, not Puppeteer |
| n8n for WebSocket | n8n can't handle real-time bidirectional comms |
| n8n full orchestration | Need tight Playwright control in FastAPI |
| MCP AI form matching | Zero error tolerance conflicts with AI uncertainty |

### 17.5 Future Enhancements (Phase 2+)

| Enhancement | When | Benefit |
|-------------|------|---------|
| **MCP Filesystem server** | Phase 2 | Standardized file access, Claude integration |
| MCP AI form matching | Phase 2 | Solve unknown field problem intelligently |
| n8n Google Drive node | Phase 2 | Pull resumes from Drive |
| MCP SQLite server | Phase 2 | Replace JSON audit logs with queryable DB |
| Custom MCP adapter server | Phase 3 | AI-powered ATS detection |

### 17.6 Troubleshooting

| Issue | Solution |
|-------|----------|
| n8n can't connect to Google Sheets | Re-authenticate OAuth in n8n credentials |
| Webhook not triggering | Verify n8n webhook URL matches FastAPI call |
| File permission error | Ensure data/ directory is writable |
| n8n container stops | Check Docker logs: `docker logs n8n` |
| answers.json not loading | Check file path, valid JSON format |

---

## 18. Appendix

### 18.1 Google API Setup

```bash
# 1. Create Google Cloud Project
# 2. Enable Google Sheets API
# 3. Create service account
# 4. Download credentials JSON
# 5. Share sheet with service account email

export GOOGLE_APPLICATION_CREDENTIALS="credentials/service_account.json"
export SHEET_ID="your-sheet-id"
```

### 18.2 Development Setup (WSL2 Linux)

**Primary dev environment:** WSL2 (Linux). Only n8n runs in Docker; FastAPI and React run natively for faster iteration.

```bash
# 1. n8n (Docker — only service in Docker)
docker run -d --name n8n --restart unless-stopped -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

# 2. Backend (native in WSL2)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 3. Frontend (native in WSL2)
cd frontend
npm install
npm run dev
```

### 18.3 Required Services

| Service | URL | Purpose |
|---------|-----|---------|
| n8n | http://localhost:5678 | Workflow automation |
| FastAPI | http://localhost:8000 | Backend API |
| React | http://localhost:5173 | Frontend UI |

### 18.4 Environment Variables

```bash
# n8n Configuration
N8N_URL=http://localhost:5678
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# FastAPI Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
API_KEY=your-secret-api-key  # Simple API key auth for all endpoints

# Google Sheets (configured in n8n, not here)
SHEET_ID=your-sheet-id  # For reference only

# Data Directory
DATA_DIR=./data
BROWSER_PROFILE_DIR=./data/browser-profile  # Persistent Playwright session

# Automation Settings
DELAY_MIN_MS=150
DELAY_MAX_MS=750
FILL_AHEAD_BUFFER=3           # Number of forms to pre-fill ahead of user
HEADLESS=false                # Always false for CAPTCHA handling

# Per-domain rate limits (JSON string)
RATE_LIMITS='{"greenhouse.io": 5, "myworkdayjobs.com": 3, "default": 5}'

# Gemini AI (for custom question fallback)
GEMINI_API_KEY=your-gemini-api-key  # Free tier

# Notifications (configured in n8n)
# SMTP, Slack tokens etc. are stored in n8n credentials
```

### 18.5 CLI Commands

```bash
# Start processing (batch mode with UI)
python -m backend.main serve

# Dry-run only (no submissions)
python -m backend.main apply --dry-run

# Process specific job
python -m backend.main apply --url "https://..."
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | - | Initial PRD |
| 1.1 | 2026-02-02 | - | Updated with interview findings: simplified architecture, 2-week timeline, card stack UX, testing/rollback sections |
| 1.2 | 2026-02-03 | - | Added Section 17: MCP & n8n integration opportunities, hybrid architecture, implementation priorities |
| 1.3 | 2026-02-03 | - | n8n + MCP in MVP. Updated architecture, data flow, implementation roadmap. |
| 1.4 | 2026-02-03 | - | **Simplified MVP:** MCP deferred to Phase 2. n8n stays for Sheets/notifications. Simple file I/O for local files. Higher confidence (75% for 2 weeks). |
| 1.5 | 2026-02-19 | - | **Deep-dive interview round 2:** 28 decisions added — pipeline fill-ahead, Gemini AI fallback, shadcn/ui, re-fill-on-approve, per-domain rate limits, demo mode, n8n dedup + UUID, persistent browser profile, API key auth, timing data, stats endpoint, empty queue handling, n8n offline resilience. |

---

## Interview Findings Summary

Key decisions from user interviews:

| Topic | Decision |
|-------|----------|
| Primary goal | Job search + portfolio + sellable product |
| Volume | 20-30 applications/day |
| Error tolerance | Zero (review every application) |
| Frontend | FastAPI + React (shadcn/ui + Tailwind) |
| Review UX | Tinder-style card stack with always-visible progress sidebar |
| Submit flow | Auto-submit after approval (re-fill for freshness) |
| Data source | Google Sheets (via n8n, with UUID + dedup) |
| Documents | Local files (simple file I/O) |
| First adapter | Greenhouse (hardcoded label map per adapter) |
| Unknown fields | Skip and flag → answer bank → Gemini AI fallback |
| Custom questions | Pre-built answer bank + Gemini free tier |
| AI answers UX | Auto-filled, directly editable on card (🤖 indicator) |
| CAPTCHA | Pop up browser window |
| Duplicates | Deduplicate in n8n sync workflow |
| ATS detection | Auto-detect from URL, manual override |
| TOS approach | User-controlled risk levels |
| Testing | Dry-run mode + key unit tests (pytest/Vitest) |
| Demo mode | `--demo` flag loads mock jobs, no n8n needed |
| Rollback | Full form data logging with timing phases |
| Panic button | Essential (Esc key) |
| Empty queue | Auto-stop + n8n notification |
| Batch flow | Pipeline: fill 2-3 ahead while user reviews |
| Form staleness | Re-fill on approve; retry once then pause on failure |
| Edit mode | Inline editable fields + bring browser to front |
| Form preview | Field list default, screenshot on Space key |
| Notifications | Toast popups + sidebar status updates |
| Session | Persistent Playwright `user_data_dir` (configurable path) |
| Resume | Single for MVP, data model supports multiple (Phase 2) |
| Cover letter | Deferred entirely from MVP |
| API auth | Simple API key via env var |
| Rate limiting | Per-domain configurable limits |
| n8n offline | Queue + retry with exponential backoff |
| Analytics | Basic `/api/stats` endpoint from audit logs |
| Docker | Only n8n in Docker; FastAPI + React native |
| Dev environment | WSL2 (Linux) |
| Timeline | 2 weeks prototype |
| UI polish | Clean minimal (shadcn/ui) |
| Pricing target | $10-20/month |
| Differentiator | Best review UX |
| **n8n** | **MVP - Sheets, notifications, scheduling, dedup** |
| **MCP** | **Phase 2 - Deferred for simplicity** |

---

*This PRD is a living document and will be updated as implementation progresses.*
