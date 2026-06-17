"""
Vercel entry point for LevelUp Poker Lab.
Builds frontend at deploy time, serves it via FastAPI static files.
"""
import os
import subprocess
import sys
from pathlib import Path

# --- Build frontend at deploy time ---
_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND_DIR = _ROOT / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"

if not _DIST_DIR.exists():
    # Install dependencies and build
    subprocess.run(["npm", "install"], cwd=str(_FRONTEND_DIR), check=True)
    subprocess.run(["npm", "run", "build"], cwd=str(_FRONTEND_DIR), check=True)

# --- Import FastAPI app ---
_BACKEND_DIR = str(_ROOT / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.main import app

# Mount static assets
_assets = _DIST_DIR / "assets"
if _assets.exists():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

# SPA fallback
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    idx = _DIST_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"detail": "Frontend not built"}

# Mangum handler
from mangum import Mangum
handler = Mangum(app)
