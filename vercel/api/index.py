"""
Vercel serverless entrypoint.

Vercel's Python runtime serves any ASGI/WSGI object named `app` that a file
under `/api` exposes. So this file does exactly one thing: put the existing
`backend/` package on the import path and re-export the FastAPI `app`
untouched. All the real code still lives in `backend/` — this is just the
seam that lets the same app run as a Vercel function in production and under
`uvicorn app:app` locally, with zero divergence between the two.

`vercel/vercel.json` bundles `backend/**` alongside this function
(`includeFiles`) and rewrites every `/api/*` request here; FastAPI still sees
the original `/api/...` path, so its routes match unchanged.
"""

import os
import sys

# backend/ sits two levels up from vercel/api/; add it so `import app` and
# `import engine...` resolve to the real package.
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, _BACKEND)

from app import app  # noqa: E402  — the FastAPI ASGI app Vercel will serve

__all__ = ["app"]
