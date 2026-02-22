# Missing Features & Roadmap

Audit of all missing, incomplete, and planned features as of 2026-02-22.

---

## Critical Gaps (Must-Fix for MVP)

### 1. Screenshot Capture — BROKEN
- **Problem:** `fill_single()` in `form_filler.py` calls `self._browser.screenshot()` and sets `job.screenshot_path`, but screenshots directory is never created. Frontend Space key modal will 404.
- **Files:** `backend/automation/form_filler.py`, `backend/automation/browser.py`
- **Fix:** Ensure `data/screenshots/` directory is created on startup. Verify screenshot path flows to frontend correctly.
- **Status:** [x] Fixed — screenshot endpoint moved to public (no-auth) router, file existence check added

### 2. Gemini AI Fallback — NOT WIRED
- **Problem:** `gemini_client.py` is fully implemented (Gemini 2.0 Flash, 10s timeout, contextual prompts) but never called from the form filling pipeline. Custom questions that don't match the answer bank are left blank instead of AI-answered.
- **Files:** `backend/automation/form_filler.py`, `backend/gemini_client.py`
- **Fix:** In `fill_single()`, after `search_answer_bank()` returns None for a custom question, call `gemini_client.generate_answer()`. Flag the field with `source="gemini"` so the frontend can show a robot indicator.
- **Status:** [x] Fixed — Gemini integrated into form_filler pipeline, fields flagged as `ai_generated` with `source="gemini"`

### 3. Edit Mode Browser Focus — HALF DONE
- **Problem:** Pressing E toggles inline editing on the card (works), but doesn't call `bring_to_front()` to show the Playwright browser window for complex edits. Users cannot interactively edit forms in the browser.
- **Files:** `frontend/src/components/CardStack.tsx`, `backend/routes/jobs.py`
- **Fix:** Add a `POST /api/jobs/{id}/edit` endpoint that brings the browser to front. Frontend E key should call this endpoint in addition to toggling inline edit mode.
- **Status:** [x] Fixed — `POST /api/jobs/{id}/edit` endpoint added, E key brings browser to front via `editJob()` API call

### 4. CAPTCHA Handling — MISSING
- **Problem:** No CAPTCHA detection. If a job URL has a CAPTCHA, the form filler hangs or fails silently. PRD requires pausing and popping up the browser for user to solve.
- **Files:** `backend/automation/form_filler.py`, `backend/automation/browser.py`
- **Fix:** After page load, scan for common CAPTCHA markers (`iframe[src*="recaptcha"]`, `iframe[src*="hcaptcha"]`, `.g-recaptcha`, `#captcha`). If found, bring browser to front, pause pipeline, notify frontend via WebSocket, wait for user signal to continue.
- **Status:** [x] Fixed — `detect_captcha()` added to BrowserManager, integrated into `fill_single()`, broadcasts WebSocket `captcha_detected` event

### 5. Re-fill Retry Logic — INCOMPLETE
- **Problem:** `refill_and_submit()` has a retry loop but the pause + show-browser-for-manual-intervention path has edge cases. The `finally` block's page cleanup logic is fragile.
- **Files:** `backend/automation/form_filler.py`
- **Fix:** Clean up retry logic. On second failure: set job status to NEEDS_INTERVENTION, bring browser to front, broadcast WebSocket event, don't close the page.
- **Status:** [ ] Not started

---

## Should-Fix for Polish

### 6. Edit Field Persistence — MISSING ENDPOINT
- **Problem:** No `POST /api/jobs/{id}/edit` endpoint to persist inline field edits from the card back to the backend. Edits made in the frontend are lost on refresh.
- **Files:** `backend/routes/jobs.py`, `backend/job_store.py`
- **Fix:** Add endpoint that accepts updated field values and stores them in the job store. On approve, use the edited values during re-fill.
- **Status:** [ ] Not started

### 7. Rate Limit Enforcement — NOT ENFORCED
- **Problem:** `RateLimiter` computes whether a domain is rate-limited but `fill_single()` proceeds regardless. `wait_if_needed()` waits but `record()` is only called in `refill_and_submit()`, not in `fill_single()`.
- **Files:** `backend/automation/form_filler.py`, `backend/automation/rate_limiter.py`
- **Fix:** Call `self._rate_limiter.record(job.job_url)` in `fill_single()` after successful form fill. Ensure `wait_if_needed()` actually blocks when limit is exceeded.
- **Status:** [ ] Not started

### 8. Stats in Frontend Sidebar — NOT WIRED
- **Problem:** `/api/stats` endpoint returns aggregated stats (total applied, success rate, top skipped fields) but `ProgressSidebar` only shows local React state counts.
- **Files:** `frontend/src/components/ProgressSidebar.tsx`, `frontend/src/lib/api.ts`
- **Fix:** Fetch `/api/stats` periodically and display success rate, total applied, and top skipped fields in the sidebar.
- **Status:** [x] Fixed — `ProgressSidebar` now fetches `/api/stats` every 15s, displays success rate, total applied, AI answer count, and top skipped fields

### 9. Resume Upload Verification — UNTESTED
- **Problem:** All 4 adapters have `upload_resume()` methods but none are tested against real forms. No unit tests for file upload behavior.
- **Files:** `backend/automation/adapters/*.py`, `backend/tests/`
- **Fix:** Add unit tests with mocked Playwright page objects. Test each adapter's resume selector chain.
- **Status:** [ ] Not started

### 10. Empty Queue n8n Notification — MISSING
- **Problem:** Frontend shows "All caught up!" toast when queue is empty, but no webhook fires to notify n8n. n8n daily summary won't know the batch finished.
- **Files:** `backend/automation/form_filler.py`, `backend/n8n_client.py`
- **Fix:** When pipeline detects empty queue + auto-stops, call n8n webhook with batch summary (count submitted, failed, skipped).
- **Status:** [ ] Not started

### 11. Multi-Page Form Custom Questions — INCOMPLETE
- **Problem:** After navigating pages, fields on new pages are filled via `adapter.fill_form()` but `detect_custom_questions()` is only called once (on the first page). Custom questions on later pages are missed.
- **Files:** `backend/automation/form_filler.py`
- **Fix:** Call `detect_custom_questions()` + answer bank/Gemini on each page after navigation.
- **Status:** [ ] Not started

---

## Not Started (Planned in PRD)

### 12. Cover Letter Handling — DEFERRED
- **PRD:** Deferred from MVP entirely. Should at minimum detect cover letter fields and flag them with warning.
- **Status:** [ ] Phase 2

### 13. Multiple Resumes — DEFERRED
- **PRD:** Data model designed for multiple role-specific resumes. No UI or selection logic.
- **Status:** [ ] Phase 2

### 14. MCP Integration — DEFERRED
- **PRD:** MCP Filesystem server for standardized file access + AI-assisted form matching. Currently uses direct file I/O.
- **Status:** [ ] Phase 2

### 15. LinkedIn Adapter — DEFERRED
- **PRD:** High TOS risk, intentionally deferred indefinitely.
- **Status:** [ ] Future (if ever)

### 16. Cloud Deployment — DEFERRED
- **PRD:** Multi-user auth, Stripe billing, cloud hosting.
- **Status:** [ ] Phase 3

---

## Nice-to-Have Improvements

### 17. Login Wall Detection
- Detect when a URL requires login (redirect to SSO, login form on page) and pause instead of failing.

### 18. Duplicate Application Detection
- ~~Check audit logs before filling — skip if already applied to same company/role URL.~~
- **Status:** [x] Fixed — `_is_duplicate()` checks audit logs for matching submitted URLs before filling

### 19. Field Confidence Scoring
- Show confidence % on each filled field (exact match=100%, substring=70%, AI-generated=50%).

### 20. Batch Analytics Dashboard
- Visual charts for application trends, success rate over time, ATS type breakdown.

### 21. Answer Bank Learning
- After user edits an AI-generated field, save the correction back to `answers.json` `custom_answers` for next time.

### 22. Form Validation Detection
- After filling, check for red validation error indicators on the page and flag them on the card before submission.

### 23. Proxy/VPN Rotation
- For high-volume use to avoid IP-based rate limiting.

### 24. Job Description Parsing
- Extract salary range, requirements, remote status from the job page and display on the review card.

### 25. Undo/Rollback
- Undo an accidental approve/skip within a short time window (e.g., 5 seconds).

---

## Implementation Priority Order

**Recommended order for making the tool usable end-to-end:**

1. Screenshot capture fix (small, high impact)
2. Gemini integration into pipeline (custom questions auto-fill)
3. Edit endpoint + browser focus (complete E key flow)
4. CAPTCHA detection + pause (prevents silent failures)
5. Duplicate application check (prevents double-applies)
6. Stats in sidebar UI (backend already built)
