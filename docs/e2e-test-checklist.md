# End-to-End Test Checklist

Run this after every phase to verify the full system works.

---

## 1. Backend Unit Tests

```bash
cd /home/prat/ai/job-application-tool
source venv/bin/activate
python -m pytest backend/tests/ -v
```

**Expected:** All tests pass (currently 75).

---

## 2. Frontend Build

```bash
cd frontend
npm run build
```

**Expected:** TypeScript compiles and Vite bundles with no errors.

---

## 3. Backend Server & API Endpoints

```bash
# Start backend
cd /home/prat/ai/job-application-tool
source venv/bin/activate
python -m backend.main serve
```

Then test each endpoint:

| # | Test | Command | Expected |
|---|------|---------|----------|
| 1 | Health | `curl -s localhost:8000/health` | `{"status":"ok"}` |
| 2 | Auth rejection (no key) | `curl -s -o /dev/null -w "%{http_code}" localhost:8000/api/jobs` | `422` |
| 3 | Auth rejection (bad key) | `curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: bad" localhost:8000/api/jobs` | `401` |
| 4 | Jobs (empty) | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/jobs` | `[]` |
| 5 | Status (stopped) | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/automation/status` | `running: false` |
| 6 | Start demo | `curl -s -X POST -H "X-API-Key: dev-key" "localhost:8000/api/automation/start?demo=true"` | `job_count: 5` |
| 7 | Jobs (5 loaded) | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/jobs` | 5 jobs with status=ready |
| 8 | Approve | `curl -s -X POST -H "X-API-Key: dev-key" localhost:8000/api/jobs/{id}/approve` | `status: submitted` |
| 9 | Skip | `curl -s -X POST -H "X-API-Key: dev-key" localhost:8000/api/jobs/{id}/skip` | `status: skipped` |
| 10 | Status (running) | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/automation/status` | `running: true, mode: demo` |
| 11 | Stats | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/stats` | counts > 0 |
| 12 | Stop | `curl -s -X POST -H "X-API-Key: dev-key" localhost:8000/api/automation/stop` | `status: stopped` |
| 13 | Status (after stop) | `curl -s -H "X-API-Key: dev-key" localhost:8000/api/automation/status` | `running: false` |
| 14 | Webhook sync | `curl -s -X POST -H "Content-Type: application/json" -d '{"jobs":[...]}' localhost:8000/api/webhooks/jobs-sync` | `synced: 1` |
| 15 | Screenshot (404) | `curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: dev-key" localhost:8000/api/jobs/{id}/screenshot` | `404` |
| 16 | Approve non-existent | `curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-API-Key: dev-key" localhost:8000/api/jobs/nonexistent/approve` | `404` |

---

## 4. WebSocket

```python
import asyncio, json, websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws/updates') as ws:
        print('Connected')
        # Trigger a broadcast (start demo via curl), then:
        msg = await asyncio.wait_for(ws.recv(), timeout=3)
        print(json.loads(msg))

asyncio.run(test())
```

**Expected:** Connects, receives broadcast messages.

---

## 5. Frontend Dev Server + Proxy

```bash
cd frontend
npm run dev
```

Then:

| # | Test | Expected |
|---|------|----------|
| 1 | `curl -s localhost:5173` | Returns HTML with `<div id="root">` |
| 2 | `curl -s -H "X-API-Key: dev-key" localhost:5173/api/jobs` | Proxies to backend, returns jobs |
| 3 | `curl -s -H "X-API-Key: dev-key" localhost:5173/api/automation/status` | Proxies to backend, returns status |

---

## 6. n8n Connectivity

```bash
curl -s http://localhost:5678/healthz
```

**Expected:** `{"status":"ok"}` (requires n8n Docker container running).

---

## Quick Automated Run

```bash
# All-in-one test script (backend must be running on :8000)
cd /home/prat/ai/job-application-tool

# Unit tests
source venv/bin/activate && python -m pytest backend/tests/ -q

# Frontend build
cd frontend && npm run build && cd ..

# API smoke test
curl -sf localhost:8000/health > /dev/null && echo "API: OK" || echo "API: FAIL"
```
