from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="QuantFin Structured Products API",
    version="1.0.0",
    description="Quantitative analytics API for derivatives pricing, market risk, volatility, and structured-product analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "QuantFin Structured Products API",
        "docs": "/docs",
        "health": "/health",
        "usage": "Research and portfolio implementation; not approved for live trading or client valuation.",
    }
