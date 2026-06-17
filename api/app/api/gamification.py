"""Gamification API router for LevelUp Poker Lab."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_optional_user_id
from app.database import get_db
from app.models.user import User
from app.models.game import Hand
from app.services.gamification.xp import (
    award_xp,
    get_level,
    get_level_progress,
    get_xp_for_next_level,
    XP_AWARDS,
)
from app.services.gamification.streaks import get_streak_info, update_streak
from app.services.gamification.quests import get_active_quests, check_quest_progress

router = APIRouter()


@router.get("/profile")
def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return the user's gamification profile: XP, level, streak, badges."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    progress = get_level_progress(user.xp)
    next_level_xp = get_xp_for_next_level(user.xp)

    badges = _compute_badges(user_id, db)

    total_hands = db.query(func.count(Hand.id)).filter(Hand.user_id == user_id).scalar() or 0

    return {
        "user_id": user.id,
        "display_name": user.display_name,
        "username": user.username,
        "level": user.level,
        "xp": user.xp,
        "next_level_xp": next_level_xp,
        "progress": progress,
        "streak": user.streak,
        "longest_streak": user.longest_streak,
        "skill_rating": user.skill_rating,
        "badges": badges,
        "total_hands": total_hands,
    }


@router.get("/quests")
def get_quests(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return active quests with progress for the user."""
    quests = get_active_quests(user_id, db)
    return {"quests": quests}


@router.get("/leaderboard")
def get_leaderboard(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return top 20 users by skill_rating."""
    users = (
        db.query(User)
        .order_by(User.skill_rating.desc())
        .limit(20)
        .all()
    )

    entries = []
    for rank, u in enumerate(users, start=1):
        entries.append({
            "rank": rank,
            "user_id": u.id,
            "display_name": u.display_name,
            "username": u.username,
            "level": u.level,
            "xp": u.xp,
            "skill_rating": u.skill_rating,
            "streak": u.streak,
        })

    user = db.query(User).filter(User.id == user_id).first()
    user_rank = None
    if user:
        higher = db.query(func.count(User.id)).filter(User.skill_rating > user.skill_rating).scalar() or 0
        user_rank = higher + 1

    return {
        "leaderboard": entries,
        "user_rank": user_rank,
    }


@router.post("/claim-daily")
def claim_daily(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Claim the daily login bonus. Can only be claimed once per day."""
    from datetime import datetime, date

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    if user.last_active:
        last_date = user.last_active.date() if hasattr(user.last_active, "date") else user.last_active
        if hasattr(last_date, "date"):
            last_date = last_date.date()
        if last_date == today:
            raise HTTPException(status_code=400, detail="Daily bonus already claimed today")

    result = award_xp(user_id, XP_AWARDS["daily_login"], "Daily login bonus", db)
    streak_result = update_streak(user_id, db)

    return {
        "xp_earned": result["xp_earned"],
        "new_total_xp": result["new_total_xp"],
        "leveled_up": result["leveled_up"],
        "new_level": result["new_level"],
        "streak": streak_result["current_streak"],
        "streak_message": streak_result["message"],
    }


@router.post("/event")
def record_event(
    event_type: str = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Record a gamification event (hand played, drill completed, etc.)."""
    xp_amount = XP_AWARDS.get(event_type)
    result = {}

    if xp_amount:
        xp_result = award_xp(user_id, xp_amount, f"Event: {event_type}", db)
        result["xp"] = xp_result

    completed_quests = check_quest_progress(user_id, event_type, db)
    result["completed_quests"] = completed_quests

    return result


def _compute_badges(user_id: int, db: Session) -> list[dict]:
    """Compute which badges a user has earned."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    badges = []

    if user.level >= 5:
        badges.append({"id": "level_5", "name": "Rising Star", "icon": "star", "description": "Reach level 5"})
    if user.level >= 10:
        badges.append({"id": "level_10", "name": "Poker Pro", "icon": "crown", "description": "Reach level 10"})

    if user.longest_streak >= 3:
        badges.append({"id": "streak_3", "name": "On a Roll", "icon": "fire", "description": "Achieve a 3-day streak"})
    if user.longest_streak >= 7:
        badges.append({"id": "streak_7", "name": "Week Warrior", "icon": "fire", "description": "Achieve a 7-day streak"})
    if user.longest_streak >= 30:
        badges.append({"id": "streak_30", "name": "Monthly Master", "icon": "fire", "description": "Achieve a 30-day streak"})

    total_hands = db.query(func.count(Hand.id)).filter(Hand.user_id == user_id).scalar() or 0
    if total_hands >= 100:
        badges.append({"id": "hands_100", "name": "Century Club", "icon": "cards", "description": "Play 100 hands"})
    if total_hands >= 500:
        badges.append({"id": "hands_500", "name": "Grinder", "icon": "cards", "description": "Play 500 hands"})
    if total_hands >= 1000:
        badges.append({"id": "hands_1000", "name": "Iron Player", "icon": "cards", "description": "Play 1,000 hands"})

    if user.skill_rating >= 1200:
        badges.append({"id": "rating_1200", "name": "Sharp Mind", "icon": "brain", "description": "Reach 1200 skill rating"})
    if user.skill_rating >= 1500:
        badges.append({"id": "rating_1500", "name": "Strategist", "icon": "brain", "description": "Reach 1500 skill rating"})

    return badges
