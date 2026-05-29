import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ..schemas import RunRequest, RunStatus, RunSummary
from ..services.runner import start_run, get_run_status, get_run_logs
from ..services.storage import list_runs, get_report_path, get_artifact_path, save_artifact, get_run_meta

router = APIRouter(prefix="/api")


@router.post("/pipeline/run")
async def create_run(req: RunRequest):
    run_id = start_run(req.model_dump())
    return {"run_id": run_id, "status": "started"}


@router.post("/pipeline/run/upload")
async def create_run_with_upload(
    file: UploadFile = File(...),
    target_url: str = Form(""),
    username: str = Form(""),
    password: str = Form(""),
):
    # Save uploaded file
    docs_dir = Path("web/uploads")
    docs_dir.mkdir(parents=True, exist_ok=True)
    file_path = docs_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    config = {
        "mode": "document",
        "document_path": str(file_path),
        "target_url": target_url or None,
        "username": username or None,
        "password": password or None,
        "run_type": "verification",
    }
    run_id = start_run(config)
    return {"run_id": run_id, "status": "started"}


@router.get("/pipeline/{run_id}/status")
async def get_status(run_id: str):
    status = get_run_status(run_id)
    if status.get("status") == "not_found":
        raise HTTPException(404, f"Run {run_id} not found")
    return status


@router.websocket("/pipeline/{run_id}/logs")
async def stream_logs(websocket: WebSocket, run_id: str):
    await websocket.accept()
    sent_lines = set()
    try:
        while True:
            logs = get_run_logs(run_id)
            for line in logs:
                key = hash(line)
                if key not in sent_lines:
                    await websocket.send_text(line)
                    sent_lines.add(key)
            status = get_run_status(run_id)
            if status.get("status") in ("completed", "failed", "aborted"):
                await websocket.send_text(f"[RUN] Pipeline {status['status']}")
                break
            import asyncio
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass


@router.get("/pipeline/{run_id}/report")
async def get_report(run_id: str):
    path = get_report_path(run_id)
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    raise HTTPException(404, "Report not yet generated")


@router.get("/pipeline/{run_id}/artifact/{name}")
async def get_artifact(run_id: str, name: str):
    path = get_artifact_path(run_id, name)
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    raise HTTPException(404, f"Artifact '{name}' not found")


@router.get("/pipeline/{run_id}/artifact-raw/{name}")
async def get_artifact_raw(run_id: str, name: str):
    path = get_artifact_path(run_id, name)
    if path.exists():
        return path.read_text(encoding="utf-8")
    raise HTTPException(404, f"Artifact '{name}' not found")


@router.get("/runs")
async def list_all_runs():
    return list_runs()


@router.get("/runs/{run_id}")
async def get_run_detail(run_id: str):
    meta = get_run_meta(run_id)
    if not meta:
        raise HTTPException(404, f"Run {run_id} not found")
    status = get_run_status(run_id)
    meta.update(status)
    return meta
