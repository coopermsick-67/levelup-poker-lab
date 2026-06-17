"""
Vercel entry point for LevelUp Poker Lab.
Frontend static files are in api/_static/ (built at deploy time).
"""
import sys
from pathlib import Path

# Add api/ to sys.path so `import app` works
sys.path.insert(0, str(Path(__file__).parent))

_STATIC_DIR = Path(__file__).parent / "_static"

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.main import app

# Mount static assets
_assets = _STATIC_DIR / "assets"
if _assets.exists():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

# SPA fallback for non-API routes
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    idx = _STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"detail": "Frontend not built"}

from mangum import Mangum
handler = Mangum(app)
