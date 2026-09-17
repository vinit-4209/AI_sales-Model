import asyncio
import json
import os
import threading
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from crm_functions import _load_crm_data, get_client_data_from_csv, summarize_client_data
from main import LIVE_FILE, POST_SUMMARY_FILE, STATUS_FILE, SalesCallPipeline

# Global event loop reference for thread-safe websocket broadcasts
main_loop: Optional[asyncio.AbstractEventLoop] = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        text_data = json.dumps(message)
        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(text_data)
            except Exception:
                async with self._lock:
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)


manager = ConnectionManager()


def broadcast_sync(message: dict):
    """Thread-safe bridge to broadcast from background threads to WebSockets."""
    global main_loop
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), main_loop)


def on_utterance_callback(data: dict):
    broadcast_sync({
        "type": "utterance",
        "data": data,
    })


def on_finalized_callback(data: dict):
    broadcast_sync({
        "type": "call_ended",
        "data": data,
    })


# Pipeline singleton
pipeline = SalesCallPipeline(
    on_utterance=on_utterance_callback,
    on_finalized=on_finalized_callback,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    print("[Server] Started FastAPI backend for AI Sales Call Assistant")
    yield
    if pipeline.is_running():
        pipeline.stop(wait_for_finalize=False)
    print("[Server] Shutting down FastAPI backend")


app = FastAPI(title="AI Sales Call Assistant API", lifespan=lifespan)

# Allow CORS for React dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "is_running": pipeline.is_running(),
    }


@app.post("/api/call/start")
def start_call():
    if pipeline.is_running():
        return {"status": "already_running", "is_running": True}

    pipeline.start()
    broadcast_sync({"type": "status", "data": {"is_running": True}})
    return {"status": "started", "is_running": True}


@app.post("/api/call/stop")
def stop_call():
    if not pipeline.is_running():
        summary_data = None
        if os.path.exists(POST_SUMMARY_FILE):
            try:
                with open(POST_SUMMARY_FILE, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
            except Exception:
                pass
        return {"status": "already_stopped", "is_running": False, "summary": summary_data}

    # Stop and wait for final Whisper transcription and Groq post-call summary
    pipeline.stop(wait_for_finalize=True, timeout=30)
    broadcast_sync({"type": "status", "data": {"is_running": False}})

    summary_data = None
    if os.path.exists(POST_SUMMARY_FILE):
        try:
            with open(POST_SUMMARY_FILE, "r", encoding="utf-8") as f:
                summary_data = json.load(f)
        except Exception:
            pass

    return {
        "status": "stopped",
        "is_running": False,
        "summary": summary_data,
    }


@app.get("/api/call/status")
def get_call_status():
    status = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status = json.load(f)
        except Exception:
            status = {}

    return {
        "is_running": pipeline.is_running(),
        "sentiment": status.get("sentiment", "Neutral"),
        "summary": status.get("summary", ""),
        "suggestion": status.get("suggestion", "Waiting for customer input..."),
    }


@app.get("/api/call/transcript")
def get_transcript():
    if os.path.exists(LIVE_FILE):
        try:
            with open(LIVE_FILE, "r", encoding="utf-8") as f:
                return {"transcript": f.read()}
        except Exception as e:
            return {"transcript": "", "error": str(e)}
    return {"transcript": ""}


@app.get("/api/call/summary")
def get_summary():
    if os.path.exists(POST_SUMMARY_FILE):
        try:
            with open(POST_SUMMARY_FILE, "r", encoding="utf-8") as f:
                return {"summary": json.load(f)}
        except Exception as e:
            return {"summary": None, "error": str(e)}
    return {"summary": None}


@app.get("/api/crm/leads")
def get_crm_leads():
    """Returns sample leads from CRM_data.csv for quick selection."""
    try:
        df = _load_crm_data()
        if df.empty:
            return {"leads": []}

        records = []
        for _, row in df.iterrows():
            records.append({
                "lead_id": str(row.get("Lead ID", "")),
                "name": str(row.get("Name", "")),
                "phone": str(row.get("Phone", "")),
                "email": str(row.get("Email Id", "")),
                "product": str(row.get("Product Name", "")),
                "category": str(row.get("Category", "")),
                "price": str(row.get("Price (INR)", "")),
                "purchase_date": str(row.get("Purchase Date", "")),
            })
        return {"leads": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crm/customer")
def get_customer(phone: str = Query(..., description="Customer phone number")):
    customer_data = get_client_data_from_csv(phone)
    if not customer_data:
        raise HTTPException(status_code=404, detail="Customer not found with this phone number")

    recommendations = summarize_client_data(customer_data)
    return {
        "customer": customer_data,
        "recommendations": recommendations,
    }


@app.websocket("/ws/call")
async def websocket_call_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial state
    await websocket.send_text(json.dumps({
        "type": "status",
        "data": {"is_running": pipeline.is_running()}
    }))

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                # Binary audio frame: 16kHz float32 PCM samples from browser
                raw_bytes = message["bytes"]
                try:
                    audio_block = np.frombuffer(raw_bytes, dtype=np.float32)
                    if pipeline.is_running() and len(audio_block) > 0:
                        pipeline.enqueue_audio(audio_block)
                except Exception as e:
                    print(f"[WebSocket] Error processing audio frame: {e}")

            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    action = payload.get("action")
                    if action == "start":
                        if not pipeline.is_running():
                            pipeline.start()
                            await manager.broadcast({"type": "status", "data": {"is_running": True}})
                    elif action == "stop":
                        if pipeline.is_running():
                            pipeline.stop(wait_for_finalize=True, timeout=30)
                            await manager.broadcast({"type": "status", "data": {"is_running": False}})
                    elif action == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] Disconnected with error: {e}")
        await manager.disconnect(websocket)


# Mount production React frontend if built
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
