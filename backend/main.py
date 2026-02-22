import argparse
import logging
import sys

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.automation.browser import BrowserManager
from backend.automation.form_filler import FormFillingPipeline
from backend.automation.rate_limiter import RateLimiter
from backend.config import Settings, get_settings
from backend.gemini_client import GeminiClient
from backend.job_store import JobStore
from backend.n8n_client import N8nClient
from backend.routes import automation, jobs, stats, webhooks
from backend.websocket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class AppState:
    """Holds shared application state accessible by route handlers."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.job_store = JobStore()
        self.ws_manager = ConnectionManager()
        self.n8n_client = N8nClient(settings)
        self.gemini_client = GeminiClient(settings.gemini_api_key)
        self.rate_limiter = RateLimiter(settings.get_rate_limits())
        self.browser = BrowserManager(settings)
        self.pipeline = FormFillingPipeline(
            self.browser, settings, self.rate_limiter,
            self.gemini_client, self.ws_manager
        )


# Global app state — initialized on startup
app_state: AppState = None  # type: ignore


app = FastAPI(title="Job Application Tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route modules
app.include_router(jobs.router)
app.include_router(jobs.public_router)
app.include_router(automation.router)
app.include_router(webhooks.router)
app.include_router(stats.router)


@app.on_event("startup")
async def startup():
    global app_state
    settings = get_settings()
    app_state = AppState(settings)

    # Start n8n client (health check + retry loop)
    await app_state.n8n_client.start()

    # Start browser only in non-demo mode (demo doesn't need Playwright)
    if not settings.demo:
        try:
            await app_state.browser.start()
        except Exception as e:
            logger.warning(
                f"Browser failed to start: {e}. "
                "Run 'playwright install chromium' if not installed."
            )

    logger.info(
        f"App started (demo={settings.demo}, dry_run={settings.dry_run})"
    )


@app.on_event("shutdown")
async def shutdown():
    if app_state is not None:
        await app_state.pipeline.stop()
        await app_state.browser.stop()
        await app_state.n8n_client.stop()
    logger.info("App shutdown complete")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await app_state.ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client sends pings
            data = await websocket.receive_text()
            # Echo back as acknowledgment
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        app_state.ws_manager.disconnect(websocket)


def main():
    parser = argparse.ArgumentParser(description="Job Application Tool")
    subparsers = parser.add_subparsers(dest="command")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--demo", action="store_true", help="Run in demo mode"
    )
    serve_parser.add_argument(
        "--dry-run", action="store_true", help="Fill forms without submitting"
    )

    # apply command
    apply_parser = subparsers.add_parser(
        "apply", help="Process job applications"
    )
    apply_parser.add_argument(
        "--dry-run", action="store_true", help="Fill forms without submitting"
    )
    apply_parser.add_argument(
        "--url", type=str, help="Process a specific job URL"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    settings = get_settings()

    if args.command == "serve":
        if args.demo:
            settings.demo = True
        if args.dry_run:
            settings.dry_run = True
        uvicorn.run(
            "backend.main:app",
            host=settings.fastapi_host,
            port=settings.fastapi_port,
            reload=True,
        )
    elif args.command == "apply":
        if args.dry_run:
            settings.dry_run = True
        if args.url:
            print(f"Processing: {args.url} (dry_run={settings.dry_run})")
        else:
            print(f"Processing batch (dry_run={settings.dry_run})")


if __name__ == "__main__":
    main()
