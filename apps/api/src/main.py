"""FastAPI Entry Point for QUANTKUPON REST API Service."""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="QUANTKUPON API",
    version="1.0.0",
    description="Mathematical Analysis and Combinatorial Slip Optimization Service",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
)

# CORS setup for Cloudflare Pages and local development
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://quantkupon.pages.dev")
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint used by Render Free keep-alive and monitoring."""
    return {"status": "ok", "service": "quantkupon-api", "version": "1.0.0"}


@app.get("/api/v1/health", tags=["System"])
async def api_health_check():
    """Versioned health check endpoint."""
    return {"status": "ok", "service": "quantkupon-api", "version": "1.0.0"}
