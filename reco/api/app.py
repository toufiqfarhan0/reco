"""FastAPI Backend Application with SPA Static Files Mount (Track 1).

Serves:
- Core API health endpoints (/health, /api/health)
- Monetization endpoints (/billing/checkout, /billing/portal, /billing/webhook)
- Static files for Vite + React SPA (/ -> frontend/dist)
- Fallback SPA catch-all routing to frontend/dist/index.html
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from reco.billing.service import BillingService

logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="Reco — Autonomous Agent Engineering System",
    description="Backend API and Vite + React SPA Serving for Track 1",
    version="0.1.0",
)

# Enable CORS for local Vite dev server and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton Billing Service instance
_billing_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """Retrieve or initialize the BillingService singleton."""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service


def set_billing_service(service: BillingService) -> None:
    """Override BillingService (useful for unit tests)."""
    global _billing_service
    _billing_service = service


# ==============================================================================
# 1. Core API & Health Endpoints
# ==============================================================================

@app.get("/api/health")
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Render Web Service probes."""
    return {
        "status": "ok",
        "service": "reco",
        "track": "Track 1: Automated Agent Engineering",
        "version": "0.1.0",
    }


@app.get("/api/config")
async def get_public_config() -> Dict[str, Any]:
    """Public runtime configuration for frontend client bootstrapping."""
    return {
        "dodo_product_id": os.getenv("DODO_PAYMENTS_PRODUCT_ID") or os.getenv("DODO_PRO_PRODUCT_ID") or "pdt_0Nmvzbo4wJETkRyCMAEPt",
        "supabase_url": os.getenv("SUPABASE_URL", ""),
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
        "tensormux_model": os.getenv("TENSORMUX_MODEL", "glm-4-7-flash"),
        "neatlogs_available": bool(os.getenv("NEATLOGS_API_KEY")),
    }


# ==============================================================================
# 2. Billing & Monetization Endpoints (POST /billing/*)
# ==============================================================================

@app.post("/billing/checkout")
async def billing_checkout(request: Request) -> JSONResponse:
    """Generate Dodo Payments hosted Checkout Session URL."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    service = get_billing_service()
    status_code, data = service.handle_http_request(
        method="POST",
        path="/billing/checkout",
        headers=headers,
        body=body,
    )
    return JSONResponse(status_code=status_code, content=data)


@app.post("/billing/portal")
async def billing_portal(request: Request) -> JSONResponse:
    """Generate Dodo Payments customer portal session URL."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    service = get_billing_service()
    status_code, data = service.handle_http_request(
        method="POST",
        path="/billing/portal",
        headers=headers,
        body=body,
    )
    return JSONResponse(status_code=status_code, content=data)


@app.post("/billing/webhook")
async def billing_webhook(request: Request) -> JSONResponse:
    """Ingest and verify HMAC webhook events from Dodo Payments."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    service = get_billing_service()
    status_code, data = service.handle_http_request(
        method="POST",
        path="/billing/webhook",
        headers=headers,
        body=body,
    )
    return JSONResponse(status_code=status_code, content=data)


# ==============================================================================
# 3. Static SPA Serving & Fallback Routing (AFTER all API and /billing/*)
# ==============================================================================

def get_frontend_dist_path() -> Optional[Path]:
    """Locate the frontend/dist directory relative to repo root or CWD."""
    # Try relative to this file: reco/api/app.py -> repo_root / frontend / dist
    repo_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if repo_dist.is_dir():
        return repo_dist

    # Try relative to current working directory
    cwd_dist = Path.cwd() / "frontend" / "dist"
    if cwd_dist.is_dir():
        return cwd_dist

    # Try environment variable override
    env_dist = os.getenv("FRONTEND_DIST_DIR")
    if env_dist and Path(env_dist).is_dir():
        return Path(env_dist)

    return None


def configure_spa_mount(fastapi_app: FastAPI, dist_dir: Optional[Union[str, Path]] = None) -> bool:
    """Mount frontend/dist as StaticFiles and configure SPA catch-all route.

    Returns True if dist directory exists and was successfully mounted, False otherwise.
    """
    resolved_dist = Path(dist_dir) if dist_dir else get_frontend_dist_path()
    if resolved_dist is None or not resolved_dist.is_dir():
        logger.info("Frontend dist directory not found. Static SPA serving skipped.")
        return False

    index_html = resolved_dist / "index.html"
    if not index_html.is_file():
        logger.warning("frontend/dist found but index.html is missing: %s", index_html)
        return False

    # Check if static mount is already present
    for route in fastapi_app.routes:
        if getattr(route, "name", None) == "static":
            return True

    # Mount StaticFiles at root / (AFTER all API and /billing/* endpoints)
    fastapi_app.mount(
        "/",
        StaticFiles(directory=str(resolved_dist), html=True),
        name="static",
    )

    # Add catch-all SPA exception handler to serve index.html for client-side routes
    @fastapi_app.exception_handler(404)
    @fastapi_app.exception_handler(StarletteHTTPException)
    async def spa_fallback_handler(request: Request, exc: Exception) -> Any:
        status_code = getattr(exc, "status_code", 404)
        path = request.url.path
        # Never rewrite API, billing, or openapi docs to index.html
        if (
            status_code == 404
            and not path.startswith(("/api", "/billing", "/docs", "/redoc", "/openapi.json"))
        ):
            if index_html.is_file():
                return FileResponse(str(index_html))

        detail = getattr(exc, "detail", "Not Found")
        return JSONResponse(status_code=status_code, content={"detail": detail})

    logger.info("Static SPA serving mounted from: %s", resolved_dist)
    return True


# Configure SPA mount on startup if dist directory is present
configure_spa_mount(app)
