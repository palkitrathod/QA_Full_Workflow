import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure project root is in path so tools import correctly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .routes.pipeline import router as pipeline_router

app = FastAPI(
    title="QA Workflow AI Agent",
    description="Automated QA pipeline — generate tests, run scripts, file bugs, generate reports.",
    version="1.0.0",
)

app.include_router(pipeline_router)

# Serve built frontend (Vite build output)
frontend_dir = Path(__file__).parent / "static"
if frontend_dir.exists() and (frontend_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.get("/")
async def root():
    # Try frontend first, then show API docs
    index = frontend_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "QA Workflow AI Agent API", "docs": "/docs"}
