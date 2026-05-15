"""
EduFlow — FastAPI main entry point.
Registers all routers, WebSocket broadcaster, startup events (DB init, FAISS, cron).
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
import orchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# ── WebSocket connection manager ───────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self._subs: dict[str, list[WebSocket]] = {}

    async def connect(self, submission_id: str, ws: WebSocket):
        await ws.accept()
        self._subs.setdefault(submission_id, []).append(ws)

    def disconnect(self, submission_id: str, ws: WebSocket):
        if submission_id in self._subs:
            self._subs[submission_id].discard(ws) if hasattr(self._subs[submission_id], 'discard') else None
            try:
                self._subs[submission_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, submission_id: str, message: dict):
        dead = []
        for ws in self._subs.get(submission_id, []):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(submission_id, ws)


manager = ConnectionManager()

async def ws_broadcast(submission_id: str, event: dict):
    await manager.broadcast(submission_id, event)

orchestrator.set_broadcast(ws_broadcast)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EduFlow starting up...")
    await init_db()
    logger.info("Database initialised.")

    # Start daily cron
    from tasks.cron import start_scheduler
    scheduler = start_scheduler()

    yield

    scheduler.shutdown()
    logger.info("EduFlow shut down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EduFlow Pakistan API",
    description="AI-powered multi-agent education platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import submissions, review, analytics_router, schools, auth

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(analytics_router.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(schools.router, prefix="/api/schools", tags=["schools"])


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/pipeline/{submission_id}")
async def pipeline_ws(websocket: WebSocket, submission_id: str):
    """
    Real-time pipeline progress stream.
    Frontend connects to this to watch agent steps fire live.
    """
    await manager.connect(submission_id, websocket)
    try:
        while True:
            await websocket.receive_text()   # keep alive
    except WebSocketDisconnect:
        manager.disconnect(submission_id, websocket)


@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": settings.DEMO_MODE}
