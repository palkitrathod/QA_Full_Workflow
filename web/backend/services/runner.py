import os
import sys
import uuid
import datetime
import json
import threading
import io
import time
from pathlib import Path

from .storage import save_run_meta, save_run_log, save_report, save_artifact, get_artifact_path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Active runs: run_id -> dict with status, log_lines, event
_active_runs: dict = {}
_lock = threading.Lock()


def _capture_output(run_id: str):
    """Redirect stdout to capture logs for a specific run."""
    old_stdout = sys.stdout

    class StreamCapture(io.StringIO):
        def write(self, s):
            old_stdout.write(s)
            with _lock:
                if run_id in _active_runs:
                    _active_runs[run_id]["log_lines"].append(s.rstrip())
                    if len(_active_runs[run_id]["log_lines"]) > 500:
                        _active_runs[run_id]["log_lines"] = _active_runs[run_id]["log_lines"][-500:]

        def flush(self):
            old_stdout.flush()

    sys.stdout = StreamCapture()
    return old_stdout


def _restore_output(old):
    sys.stdout = old


def start_run(config: dict) -> str:
    run_id = str(uuid.uuid4())[:8]
    meta = {
        "run_id": run_id,
        "status": "running",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": config.get("document_path") or config.get("jira_ticket_id") or "manual",
        "config": config,
    }
    save_run_meta(run_id, meta)

    with _lock:
        _active_runs[run_id] = {
            "status": "running",
            "log_lines": [],
            "meta": meta,
            "overall_accuracy": None,
        }

    thread = threading.Thread(target=_run_pipeline, args=(run_id, config), daemon=True)
    thread.start()
    return run_id


def _run_pipeline(run_id: str, config: dict):
    old_out = _capture_output(run_id)
    try:
        from tools.orchestrator import PipelineController

        input_mode = config.get("mode", "document")
        source_id = config.get("jira_ticket_id") or config.get("document_path") or ""
        document_path = config.get("document_path")

        # Override env for this run
        if config.get("target_url"):
            os.environ["TARGET_APP_URL"] = config["target_url"]
        if config.get("username"):
            os.environ["USERNAME"] = config["username"]
        if config.get("password"):
            os.environ["PASSWORD"] = config["password"]

        print(f"[RUN {run_id}] Starting pipeline (mode={input_mode})...")

        controller = PipelineController(
            input_mode=input_mode,
            run_type=config.get("run_type", "verification"),
            source_id=source_id,
            document_path=document_path,
        )

        try:
            controller.run_pipeline(dry_run=config.get("dry_run", False))
            with _lock:
                _active_runs[run_id]["status"] = "completed"
                meta = _active_runs[run_id]["meta"]
                meta["status"] = "completed"
                save_run_meta(run_id, meta)
        except SystemExit:
            with _lock:
                _active_runs[run_id]["status"] = "aborted"
                meta = _active_runs[run_id]["meta"]
                meta["status"] = "aborted"
                save_run_meta(run_id, meta)
        except Exception as e:
            print(f"[RUN {run_id}] Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            with _lock:
                _active_runs[run_id]["status"] = "failed"
                meta = _active_runs[run_id]["meta"]
                meta["status"] = "failed"
                save_run_meta(run_id, meta)

        # Save artifacts
        ctx_path = Path(".tmp") / "context.json"
        if ctx_path.exists():
            ctx = json.loads(ctx_path.read_text())
            eval_data = ctx.get("evaluation", {})
            with _lock:
                _active_runs[run_id]["overall_accuracy"] = eval_data.get("overall_accuracy")
                _active_runs[run_id]["meta"]["overall_accuracy"] = eval_data.get("overall_accuracy")

            # Copy report if generated
            for report_name in ["report.html", "deep_evaluation_report.html",
                                "generated_test_cases.md", "bugs.md", "playwright-results.json"]:
                src = Path(report_name)
                if src.exists():
                    save_artifact(run_id, report_name, src.read_text(encoding="utf-8", errors="replace"))

            # Copy context
            save_artifact(run_id, "context.json", json.dumps(ctx, indent=2))

    except Exception as e:
        print(f"[RUN {run_id}] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        with _lock:
            _active_runs[run_id]["status"] = "failed"
    finally:
        save_run_log(run_id, _active_runs.get(run_id, {}).get("log_lines", []))
        _restore_output(old_out)


def get_run_status(run_id: str) -> dict:
    with _lock:
        run = _active_runs.get(run_id)
        if run:
            return {
                "run_id": run_id,
                "status": run["status"],
                "progress": run["log_lines"][-1] if run["log_lines"] else "",
                "overall_accuracy": run.get("overall_accuracy"),
            }
    from .storage import get_run_meta as _get_meta
    meta = _get_meta(run_id)
    if meta:
        return {
            "run_id": run_id,
            "status": meta.get("status", "unknown"),
            "progress": "",
            "overall_accuracy": meta.get("overall_accuracy"),
        }
    return {"run_id": run_id, "status": "not_found", "progress": "", "overall_accuracy": None}


def get_run_logs(run_id: str) -> list:
    with _lock:
        run = _active_runs.get(run_id)
        if run:
            return list(run["log_lines"])
    from .storage import get_run_log as _get_log
    return _get_log(run_id)
