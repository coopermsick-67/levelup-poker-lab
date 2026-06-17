"""
Vercel entry point for LevelUp Poker Lab.
"""
import os
import subprocess
import sys
from pathlib import Path

# Build frontend at deploy time
_ROOT = Path(__file__).resolve().parent.parent
_DIST = _ROOT / "frontend" / "dist"
if not _DIST.exists():
    subprocess.run(["npm", "install"], cwd=str(_ROOT / "frontend"), check=True)
    subprocess.run(["npm", "run", "build"], cwd=str(_ROOT / "frontend"), check=True)

# Import FastAPI app (app/ is in the same directory as this file)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.main import app

# Mount static assets
if (_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

# SPA fallback
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    idx = _DIST / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"detail": "Not found"}

from mangum import Mangum
handler = Mangum(app)
