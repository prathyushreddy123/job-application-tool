import argparse
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings

app = FastAPI(title="Job Application Tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


def main():
    parser = argparse.ArgumentParser(description="Job Application Tool")
    subparsers = parser.add_subparsers(dest="command")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--demo", action="store_true", help="Run in demo mode")

    # apply command
    apply_parser = subparsers.add_parser("apply", help="Process job applications")
    apply_parser.add_argument("--dry-run", action="store_true", help="Fill forms without submitting")
    apply_parser.add_argument("--url", type=str, help="Process a specific job URL")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    settings = get_settings()

    if args.command == "serve":
        if args.demo:
            settings.demo = True
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
