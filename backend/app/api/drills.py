"""Drill Lab API — session creation, answer grading, results."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database import get_db
from app.models.game import DrillAttempt, DrillSession
from app.services.drills.engine import (
    create_drill_session,
    grade_answer,
    session_results,
)

router = APIRouter()




class CreateSessionRequest(BaseModel):
    drill_type: str = "preflop"  # preflop | postflop
    count: int = 10


class AnswerRequest(BaseModel):
    session_id: int
    drill_id: str
    answer: str


@router.post("/session")
def create_session(
    req: CreateSessionRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new drill session and return the drills."""
    if req.drill_type not in ("preflop", "postflop"):
        raise HTTPException(status_code=400, detail="drill_type must be 'preflop' or 'postflop'")
    if req.count < 1 or req.count > 50:
        raise HTTPException(status_code=400, detail="count must be between 1 and 50")

    engine_session = create_drill_session(user_id, req.drill_type, req.count)

    # Persist to DB
    db_session = DrillSession(
        id=engine_session["id"],
        user_id=user_id,
        drill_type=req.drill_type,
        total_questions=engine_session["total_questions"],
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return {
        "session": {
            "id": db_session.id,
            "user_id": db_session.user_id,
            "drill_type": db_session.drill_type,
            "total_questions": db_session.total_questions,
            "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
        },
        "drills": engine_session["drills"],
    }


@router.post("/answer")
def submit_answer(
    req: AnswerRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Grade an answer and return feedback."""
    try:
        result = grade_answer(req.session_id, req.drill_id, req.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Persist attempt to DB
    attempt = DrillAttempt(
        session_id=req.session_id,
        user_id=user_id,
        drill_id=str(req.drill_id),
        user_answer=req.answer,
        correct=1 if result["correct"] else 0,
        feedback=result["feedback"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    result["attempt_id"] = attempt.id
    return result


@router.get("/session/{session_id}/results")
def get_results(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return session results (score, accuracy)."""
    # Verify session exists in DB
    db_session = db.query(DrillSession).filter(DrillSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    try:
        results = session_results(session_id)
    except ValueError:
        # Fall back to DB query if not in memory
        attempts = (
            db.query(DrillAttempt)
            .filter(DrillAttempt.session_id == session_id)
            .all()
        )
        correct = sum(1 for a in attempts if a.correct)
        total = len(attempts)
        results = {
            "session_id": session_id,
            "user_id": user_id,
            "drill_type": db_session.drill_type,
            "total_questions": db_session.total_questions,
            "answered": total,
            "correct": correct,
            "accuracy": round(correct / total, 3) if total else 0.0,
            "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
            "attempts": [
                {
                    "session_id": a.session_id,
                    "user_id": a.user_id,
                    "drill_id": a.drill_id,
                    "user_answer": a.user_answer,
                    "correct": bool(a.correct),
                    "feedback": a.feedback,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in attempts
            ],
        }

    return results
