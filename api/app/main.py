import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app.database import engine, Base, _ensure_tables
from app.api import auth, play, drills, review, gamification

logger = logging.getLogger("uvicorn.error")

_ensure_tables()

app = FastAPI(title="LevelUp Poker Lab", version="1.0.0")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}: {exc}"},
    )

_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(play.router, prefix="/api/play", tags=["play"])
app.include_router(drills.router, prefix="/api/drills", tags=["drills"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["gamification"])


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "LevelUp Poker Lab"}


# Mangum handler for Vercel / AWS Lambda
handler = Mangum(app)
