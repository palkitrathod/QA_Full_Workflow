import json
import datetime
import shutil
from pathlib import Path

RUNS_DIR = Path("web/runs")


def ensure_dirs():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def save_run_meta(run_id: str, meta: dict):
    ensure_dirs()
    path = RUNS_DIR / run_id / "meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2))


def get_run_meta(run_id: str) -> dict:
    path = RUNS_DIR / run_id / "meta.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_run_log(run_id: str, lines: list):
    ensure_dirs()
    path = RUNS_DIR / run_id / "log.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def get_run_log(run_id: str) -> list:
    path = RUNS_DIR / run_id / "log.txt"
    if path.exists():
        return path.read_text(encoding="utf-8").splitlines()
    return []


def save_report(run_id: str, html: str):
    ensure_dirs()
    path = RUNS_DIR / run_id / "report.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def get_report_path(run_id: str) -> Path:
    return RUNS_DIR / run_id / "report.html"


def list_runs() -> list:
    ensure_dirs()
    runs = []
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        if d.is_dir():
            meta = get_run_meta(d.name)
            runs.append({
                "run_id": d.name,
                "status": meta.get("status", "unknown"),
                "created_at": meta.get("created_at", ""),
                "overall_accuracy": meta.get("overall_accuracy"),
                "source": meta.get("source", ""),
            })
    return runs


def save_artifact(run_id: str, name: str, content: str):
    ensure_dirs()
    path = RUNS_DIR / run_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def get_artifact_path(run_id: str, name: str) -> Path:
    return RUNS_DIR / run_id / name
