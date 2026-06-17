"""Review & Analytics API router."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database import get_db
from app.services.analytics.stats import compute_stats
from app.services.analytics.leaks import find_leaks
from app.services.poker_engine.game_manager import game_manager

router = APIRouter()

# Path to the persisted decisions file
DECISIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "user_decisions.json"


def _load_decisions(user_id: int) -> list[dict[str, Any]]:
    """Load persisted decisions for a user from the JSON file."""
    try:
        if DECISIONS_PATH.exists():
            data = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
            return data.get(str(user_id), [])
    except (json.JSONDecodeError, OSError):
        pass
    return _load_from_game_manager(user_id)


def _load_from_game_manager(user_id: int) -> list[dict[str, Any]]:
    """Extract decisions from the in-memory game manager tables."""
    decisions: list[dict[str, Any]] = []
    for table in game_manager.tables.values():
        for hand_data in getattr(table, "decision_log", []):
            if hand_data.get("user_id") == user_id:
                decisions.append(hand_data)
    return decisions


def _decisions_to_objects(decisions: list[dict[str, Any]]) -> list[Any]:
    """Convert dict decisions to simple namespace objects for stats computation."""

    class DecisionProxy:
        __slots__ = (
            "hand_id", "street", "position", "action_taken", "amount",
            "pot_size", "stack_size", "hole_cards", "community_cards",
            "was_correct", "ev_diff",
        )

        def __init__(self, d: dict[str, Any]):
            self.hand_id = d.get("hand_id", 0)
            self.street = d.get("street", "")
            self.position = d.get("position", "")
            self.action_taken = d.get("action_taken", "")
            self.amount = d.get("amount", 0)
            self.pot_size = d.get("pot_size", 0)
            self.stack_size = d.get("stack_size", 0)
            self.hole_cards = d.get("hole_cards", "")
            self.community_cards = d.get("community_cards", "")
            self.was_correct = d.get("was_correct", None)
            self.ev_diff = d.get("ev_diff", None)

    return [DecisionProxy(d) for d in decisions]


@router.get("/stats")
def get_stats(
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return computed poker statistics for the authenticated user."""
    raw = _load_decisions(user_id)
    decisions = _decisions_to_objects(raw)
    return compute_stats(decisions)


@router.get("/leaks")
def get_leaks(
    user_id: int = Depends(get_current_user_id),
) -> list[dict[str, Any]]:
    """Return detected leaks for the authenticated user."""
    raw = _load_decisions(user_id)
    decisions = _decisions_to_objects(raw)
    stats = compute_stats(decisions)
    return find_leaks(stats)


@router.get("/summary")
def get_summary(
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return combined stats + leaks summary for the authenticated user."""
    raw = _load_decisions(user_id)
    decisions = _decisions_to_objects(raw)
    stats = compute_stats(decisions)
    leaks = find_leaks(stats)
    return {"stats": stats, "leaks": leaks}


@router.get("/coach-report")
def get_coach_report(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a full AI coaching report for the authenticated user."""
    from app.services.ai_coach.report import CoachReport

    report = CoachReport()
    return report.generate(user_id=user_id, db=db)
