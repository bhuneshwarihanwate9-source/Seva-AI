"""
Seva-AI backend entry point.

Creates the FastAPI application, registers the API router, and
configures CORS for the Streamlit frontend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Backend.routes import router

app = FastAPI(
    title="Seva-AI Backend",
    description="AI Government Benefits Assistant — Eligibility Engine API",
    version="1.0.0",
)

# Allow the Streamlit frontend (default port 8501) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes.
app.include_router(router)


@app.get("/")
def home() -> dict:
    """Root health check."""
    return {"message": "Seva-AI Backend Running properly!"}