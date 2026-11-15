"""
FastAPI simulation-control service for Superviser le trafic dans une intersection.

Endpoints
---------
POST /start          – start the SUMO simulation (optional JSON body for parameters)
POST /stop           – stop a running simulation
GET  /status         – current state: idle | running | finished | error
WS   /ws/metrics     – real-time metrics stream (one JSON message per simulated second)

The SUMO simulation runs in a background daemon thread so it never blocks the
HTTP layer. Each connected WebSocket client receives every metrics frame produced
by the simulation.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Make sure the simulation package is importable from wherever this file lives
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
SIM_DIR = (HERE.parent / "simulation").resolve()
sys.path.insert(0, str(SIM_DIR))

# runner imports SUMO libs; it handles SUMO_HOME resolution itself.
import runner  # noqa: E402  (imported after sys.path tweak)


# ---------------------------------------------------------------------------
# Shared simulation state  (accessed from both the HTTP thread and the
# background simulation thread – protected by _lock)
# ---------------------------------------------------------------------------
_lock = threading.Lock()

_state: dict[str, Any] = {
    "status": "idle",          # idle | running | finished | error
    "controller": "fixed",
    "seed": 1,
    "duration": 1800,
    "current_time": 0,
    "last_metrics": None,
    "error": None,
}

# asyncio event loop running in the main uvicorn thread – set at startup
_loop: asyncio.AbstractEventLoop | None = None

# live WebSocket clients: set of asyncio.Queue objects, one per connection
_ws_queues: set[asyncio.Queue] = set()

# token that the running background thread checks every step
_stop_event = threading.Event()


# ---------------------------------------------------------------------------
# Background simulation thread
# ---------------------------------------------------------------------------
def _simulation_thread(controller: str, seed: int, duration: int,
                        net: str, routes: str, tls: str,
                        green_a: int, green_b: int,
                        step_delay: float = 1.0) -> None:
    """Runs the SUMO simulation and broadcasts metrics to all WebSocket clients."""
    global _loop, _ws_queues

    with _lock:
        _state["status"] = "running"
        _state["current_time"] = 0
        _state["last_metrics"] = None
        _state["error"] = None

    try:
        gen = runner.run(
            controller=controller, seed=seed, duration=duration,
            gui=False, net=net, routes=routes, tls=tls,
            green_a=green_a, green_b=green_b,
        )
        for metrics in gen:
            if _stop_event.is_set():
                break

            with _lock:
                _state["current_time"] = metrics["time"]
                _state["last_metrics"] = metrics

            # Broadcast to all WebSocket clients
            payload = json.dumps(metrics)
            _broadcast_to_queues(payload)

            if step_delay > 0:
                time.sleep(step_delay)

        with _lock:
            _state["status"] = "finished"

    except Exception as exc:
        with _lock:
            _state["status"] = "error"
            _state["error"] = str(exc)
        # broadcast the error so dashboards know
        _broadcast_to_queues(json.dumps({"error": str(exc)}))


def _broadcast_to_queues(payload: str) -> None:
    """Safely put payload into every connected WebSocket queue from the background thread."""
    global _loop, _ws_queues
    if _loop is None or not _ws_queues:
        return
    for q in list(_ws_queues):
        try:
            _loop.call_soon_threadsafe(q.put_nowait, payload)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _loop
    _loop = asyncio.get_running_loop()
    yield
    # On shutdown: stop any running simulation
    _stop_event.set()


app = FastAPI(
    title="Traffic Supervision – Simulation Control API",
    description="Control the SUMO simulation and stream live metrics over WebSocket.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten when React origin is known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class StartRequest(BaseModel):
    controller: str = "smart"   # "fixed" or "smart"
    seed: int = 1
    duration: int = 1800        # simulated seconds (30 min)
    net: str = str(SIM_DIR / "network" / "casa.net.xml")
    routes: str = str(SIM_DIR / "network" / "routes_casa2.rou.xml")
    tls: str = "cluster_12698757853_12698757855_2138359128"
    green_a: int = 35
    green_b: int = 35
    step_delay: float = 1.0     # real seconds per simulation step (for live streaming)


class StatusResponse(BaseModel):
    status: str
    controller: str
    seed: int
    duration: int
    current_time: int
    error: str | None


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------
@app.post("/start", summary="Start the simulation")
def post_start(req: StartRequest = StartRequest()):
    """
    Launch a new simulation run. Returns 409 if one is already running.

    Body (all fields optional, shown with defaults):
    ```json
    {
        "controller": "fixed",
        "seed": 1,
        "duration": 1800,
        "tls": "C",
        "green_a": 35,
        "green_b": 35
    }
    ```
    """
    with _lock:
        if _state["status"] == "running":
            from fastapi import HTTPException
            raise HTTPException(409, "Simulation already running. POST /stop first.")
        _state.update(
            status="running",
            controller=req.controller,
            seed=req.seed,
            duration=req.duration,
            current_time=0,
            error=None
        )

    _stop_event.clear()
    t = threading.Thread(
        target=_simulation_thread,
        kwargs=dict(
            controller=req.controller, seed=req.seed, duration=req.duration,
            net=req.net, routes=req.routes, tls=req.tls,
            green_a=req.green_a, green_b=req.green_b,
            step_delay=req.step_delay,
        ),
        daemon=True,
    )
    t.start()
    return {"message": "Simulation started", "controller": req.controller, "seed": req.seed}


@app.post("/stop", summary="Stop the simulation")
def post_stop():
    """
    Signal the running simulation to stop after the current step.
    Safe to call even if no simulation is running.
    """
    _stop_event.set()
    with _lock:
        status = _state["status"]
    return {"message": "Stop signal sent", "was_status": status}


@app.get("/status", response_model=StatusResponse, summary="Current simulation state")
def get_status():
    """
    Returns the current simulation state.

    - **idle** – no simulation has been started yet (or previous one was stopped)
    - **running** – simulation is active
    - **finished** – simulation reached its end duration naturally
    - **error** – simulation crashed; see the `error` field for details
    """
    with _lock:
        return StatusResponse(
            status=_state["status"],
            controller=_state["controller"],
            seed=_state["seed"],
            duration=_state["duration"],
            current_time=_state["current_time"],
            error=_state["error"],
        )


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws/metrics")
async def websocket_metrics(ws: WebSocket):
    """
    Real-time metrics stream. Sends one JSON frame per simulated second.

    Example frame:
    ```json
    {
      "time": 42,
      "roads": [
        {"road": "N_in (from N)", "queue": 3, "avg_speed": 2.1,
         "avg_wait": 12.0, "max_wait": 28.0, "crossed": 7, ...}
      ],
      "light": {"controller": "fixed", "axis": "A", "stage": "green", "stage_time": 7}
    }
    ```

    If you connect while a simulation is already running, you will receive
    the latest snapshot immediately, then live frames as they arrive.
    """
    global _loop
    _loop = asyncio.get_running_loop()
    await ws.accept()

    q: asyncio.Queue = asyncio.Queue(maxsize=120)
    _ws_queues.add(q)

    # Send the last known snapshot immediately so the client is not blank
    with _lock:
        snap = _state["last_metrics"]
    if snap is not None:
        await ws.send_text(json.dumps(snap))

    try:
        while True:
            try:
                # Wait up to 5 s for new data; send a heartbeat if nothing arrives
                payload = await asyncio.wait_for(q.get(), timeout=5.0)
                await ws.send_text(payload)
            except asyncio.TimeoutError:
                # Heartbeat – keeps the connection alive and lets the client
                # detect disconnection from the server side
                await ws.send_text(json.dumps({"heartbeat": True, "status": _state["status"]}))
    except WebSocketDisconnect:
        pass
    finally:
        _ws_queues.discard(q)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,       # reload=True breaks background threads
    )
