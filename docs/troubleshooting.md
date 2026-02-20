# Troubleshooting

Log of issues encountered during development and their solutions.

---

## 2026-02-19: Demo mode stop doesn't reset running status

**Problem:** After calling `POST /api/automation/stop`, the `GET /api/automation/status` endpoint still returned `running: true`.

**Root cause:** In demo mode, the `/stop` endpoint didn't reset `settings.demo` to `False`. The `/status` endpoint always returned `running: True` when `settings.demo` was set.

**Fix:** Added `app_state.settings.demo = False` and `app_state.settings.dry_run = False` in the `/stop` handler (`backend/routes/automation.py`).

---

## 2026-02-19: useRef() strict TypeScript error

**Problem:** `useRef<ReturnType<typeof setInterval>>()` caused TS error: "Expected 1 arguments, but got 0."

**Root cause:** With `strict: true` in tsconfig, React 19 types require an explicit initial value.

**Fix:** Pass `undefined` explicitly: `useRef<ReturnType<typeof setInterval>>(undefined)`.

---

## 2026-02-19: RateLimiter returns empty domain for malformed URLs

**Problem:** `_get_domain("not-a-url")` returned `""` instead of `"unknown"`.

**Root cause:** `urlparse` returns empty hostname for strings without `://`.

**Fix:** Added `if not hostname: return "unknown"` check in `_get_domain()`.

---

## 2026-02-19: Port 8000 already in use

**Problem:** Backend server failed to start because port was occupied.

**Fix:** `lsof -ti:8000 | xargs kill -9` before starting.

---

## 2026-02-19: Playwright chromium not installed

**Problem:** Browser startup warning: "Executable doesn't exist at .../chrome-linux64/chrome"

**Fix:** Run `playwright install chromium` in the venv. Not critical for demo mode/API testing.
