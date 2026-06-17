"""Drill session engine — creates sessions, grades answers, tracks state."""

import threading
from datetime import datetime, timezone, timedelta
from typing import Any

from app.services.drills.preflop import get_preflop_drills

# In-memory session storage with TTL-based expiry
_SESSIONS: dict[int, dict[str, Any]] = {}
_ATTEMPTS: dict[int, list[dict[str, Any]]] = {}
_NEXT_SESSION_ID = 1
_LOCK = threading.Lock()
_SESSION_TTL = timedelta(hours=1)  # Sessions expire after 1 hour


def _purge_expired() -> None:
    """Remove sessions older than _SESSION_TTL."""
    cutoff = datetime.now(timezone.utc) - _SESSION_TTL
    expired = [
        sid
        for sid, s in _SESSIONS.items()
        if datetime.fromisoformat(s["created_at"]) < cutoff
    ]
    for sid in expired:
        del _SESSIONS[sid]
        _ATTEMPTS.pop(sid, None)


def create_drill_session(user_id: int, drill_type: str, count: int) -> dict[str, Any]:
    """Create a drill session for the given user with N random drills."""
    global _NEXT_SESSION_ID

    with _LOCK:
        _purge_expired()
        session_id = _NEXT_SESSION_ID
        _NEXT_SESSION_ID += 1

    if drill_type == "preflop":
        drills = get_preflop_drills(count)
    else:
        from app.services.drills.postflop import get_postflop_drills
        drills = get_postflop_drills(count)

    session = {
        "id": session_id,
        "user_id": user_id,
        "drill_type": drill_type,
        "total_questions": len(drills),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "drills": drills,
    }
    _SESSIONS[session_id] = session
    _ATTEMPTS[session_id] = []

    return session


def get_session(session_id: int) -> dict[str, Any] | None:
    """Return the session dict if it exists."""
    return _SESSIONS.get(session_id)


def grade_answer(session_id: int, drill_id: int, answer: str) -> dict[str, Any]:
    """Grade a user's answer. Returns feedback + correctness."""
    session = _SESSIONS.get(session_id)
    if not session:
        raise ValueError("Session not found")

    drill = next((d for d in session["drills"] if d["id"] == drill_id), None)
    if not drill:
        raise ValueError("Drill not found in session")

    correct = answer == drill["correct_action"]
    options = drill.get("options", [])
    chosen_label = ""
    for opt in options:
        if opt["action"] == answer:
            chosen_label = opt.get("label", answer)
            break

    if correct:
        feedback = drill["feedback_good"]
    else:
        is_partial = any(opt["action"] == answer for opt in options)
        feedback = drill["feedback_ok"] if is_partial else drill["feedback_poor"]

    board_str = ""
    if "board" in drill and drill["board"]:
        board_str = " ".join(drill["board"])

    result = {
        "session_id": session_id,
        "drill_id": drill_id,
        "user_answer": answer,
        "user_answer_label": chosen_label,
        "correct_action": drill["correct_action"],
        "correct": correct,
        "feedback": feedback,
        "situation": drill.get("situation", drill.get("action_so_far", "")),
        "board": board_str,
    }

    _ATTEMPTS[session_id].append({
        "session_id": session_id,
        "user_id": session["user_id"],
        "drill_id": drill_id,
        "user_answer": answer,
        "correct": correct,
        "feedback": feedback,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return result


def session_results(session_id: int) -> dict[str, Any]:
    """Return aggregate results for a session."""
    session = _SESSIONS.get(session_id)
    if not session:
        raise ValueError("Session not found")

    attempts = _ATTEMPTS.get(session_id, [])
    correct_count = sum(1 for a in attempts if a["correct"])
    total = len(attempts)
    accuracy = (correct_count / total) if total else 0.0

    return {
        "session_id": session_id,
        "user_id": session["user_id"],
        "drill_type": session["drill_type"],
        "total_questions": session["total_questions"],
        "answered": total,
        "correct": correct_count,
        "accuracy": round(accuracy, 3),
        "created_at": session["created_at"],
        "attempts": attempts,
    }
