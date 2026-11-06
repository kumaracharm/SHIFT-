"""
DRIFTGUARD 2.0 — FastAPI Application Entry Point
High-performance REST API and real-time WebSocket server for the Financial Fraud Intelligence Platform.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import logging

from backend.routers import (
    overview,
    transactions,
    investigations,
    entities,
    experts,
    responses,
    models,
    drift,
    simulation,
    system,
    experiments,
)
from backend.websocket import ws_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("driftguard.backend")

app = FastAPI(
    title="DRIFTGUARD 2.0 Financial Fraud Intelligence API",
    description="Adaptive Streaming Fraud & Threat Detection Backend with 7 Specialist Experts and Real-Time WebSockets",
    version="2.0.0",
)

# Enable CORS for Next.js frontend (default Next.js runs on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned REST API routers
app.include_router(overview.router)
app.include_router(transactions.router)
app.include_router(investigations.router)
app.include_router(entities.router)
app.include_router(experts.router)
app.include_router(responses.router)
app.include_router(models.router)
app.include_router(drift.router)
app.include_router(simulation.router)
app.include_router(system.router)
app.include_router(experiments.router)


@app.get("/")
def read_root():
    """Root metadata endpoint."""
    return {
        "platform": "DRIFTGUARD 2.0",
        "name": "Financial Fraud Intelligence Platform",
        "status": "online",
        "api_version": "v1",
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.websocket("/ws/v1/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket endpoint streaming incoming transactions,
    anomaly scores, and risk classifications to dashboard clients.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and receive optional ping / client commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)

