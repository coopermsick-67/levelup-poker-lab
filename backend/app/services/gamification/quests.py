"""Quest system for LevelUp Poker Lab.

Quests are generated per-user and tracked via simple in-memory state.
For a production system this would use a database table; for now we
use a module-level dict keyed by user_id.
"""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.game import Hand, HandDecision

# ---------------------------------------------------------------------------
# Quest templates
# ---------------------------------------------------------------------------

DAILY_QUEST_TEMPLATES = [
    {
        "id": "daily_drills",
        "title": "Drill Sergeant",
        "description": "Complete 2 Drill sessions",
        "target": 2,
        "reward_xp": 25,
        "event_type": "drill_complete",
    },
    {
        "id": "daily_hands",
        "title": "Hand Hunter",
        "description": "Play 50 hands",
        "target": 50,
        "reward_xp": 30,
        "event_type": "hand_played",
    },
    {
        "id": "daily_review",
        "title": "Review Cadet",
        "description": "Finish a Review Lab report",
        "target": 1,
        "reward_xp": 20,
        "event_type": "review_complete",
    },
]

WEEKLY_QUEST_TEMPLATES = [
    {
        "id": "weekly_hands",
        "title": "Volume Player",
        "description": "Play 300 hands",
        "target": 300,
        "reward_xp": 100,
        "event_type": "hand_played",
    },
    {
        "id": "weekly_accuracy",
        "title": "Precision Player",
        "description": "Achieve 80%+ accuracy in 3 drill sessions",
        "target": 3,
        "reward_xp": 75,
        "event_type": "drill_accurate",
    },
    {
        "id": "weekly_streak",
        "title": "Consistency King",
        "description": "Maintain a 3-day streak",
        "target": 3,
        "reward_xp": 50,
        "event_type": "streak_milestone",
    },
]

# ---------------------------------------------------------------------------
# In-memory quest progress store
# ---------------------------------------------------------------------------

# Structure: { user_id: { quest_id: { "progress": int, "completed": bool, "claimed": bool } } }
_quest_progress: dict[int, dict[str, dict]] = {}


def _ensure_user_loaded(user_id: int, db: Session) -> None:
    """Load quest progress for a user from the database into memory."""
    if user_id in _quest_progress:
        return

    # Build fresh quest state from DB data
    _quest_progress[user_id] = {}

    # Count hands played today for daily_hands
    today = datetime.utcnow().date()
    hands_today = (
        db.query(func.count(Hand.id))
        .filter(Hand.user_id == user_id)
        .filter(func.date(Hand.created_at) == today)
        .scalar()
        or 0
    )

    # Count correct drill sessions today (sessions with 80%+ accuracy)
    # We approximate by counting distinct hand_ids with was_correct decisions
    drill_sessions_today = (
        db.query(func.count(func.distinct(HandDecision.hand_id)))
        .filter(HandDecision.user_id == user_id)
        .filter(HandDecision.was_correct == 1)
        .filter(func.date(HandDecision.created_at) == today)
        .scalar()
        or 0
    )

    # Weekly hands count
    week_start = today - timedelta(days=today.weekday())
    hands_week = (
        db.query(func.count(Hand.id))
        .filter(Hand.user_id == user_id)
        .filter(func.date(Hand.created_at) >= week_start)
        .scalar()
        or 0
    )

    # Streak
    user = db.query(User).filter(User.id == user_id).first()
    current_streak = user.streak if user else 0

    for tmpl in DAILY_QUEST_TEMPLATES:
        progress = 0
        if tmpl["id"] == "daily_hands":
            progress = hands_today
        elif tmpl["id"] == "daily_drills":
            progress = min(drill_sessions_today, tmpl["target"])
        elif tmpl["id"] == "daily_review":
            progress = 0  # Review completion tracked via events

        _quest_progress[user_id][tmpl["id"]] = {
            "progress": progress,
            "completed": progress >= tmpl["target"],
            "claimed": False,
        }

    for tmpl in WEEKLY_QUEST_TEMPLATES:
        progress = 0
        if tmpl["id"] == "weekly_hands":
            progress = hands_week
        elif tmpl["id"] == "weekly_streak":
            progress = current_streak

        _quest_progress[user_id][tmpl["id"]] = {
            "progress": progress,
            "completed": progress >= tmpl["target"],
            "claimed": False,
        }


def get_active_quests(user_id: int, db: Session) -> list[dict]:
    """Return all active quests with progress for a user."""
    _ensure_user_loaded(user_id, db)

    quests = []
    for tmpl in DAILY_QUEST_TEMPLATES + WEEKLY_QUEST_TEMPLATES:
        state = _quest_progress.get(user_id, {}).get(tmpl["id"], {})
        progress = state.get("progress", 0)
        completed = state.get("completed", False) or progress >= tmpl["target"]
        claimed = state.get("claimed", False)

        quests.append({
            "id": tmpl["id"],
            "title": tmpl["title"],
            "description": tmpl["description"],
            "target": tmpl["target"],
            "progress": min(progress, tmpl["target"]),
            "reward_xp": tmpl["reward_xp"],
            "completed": completed,
            "claimed": claimed,
            "period": "daily" if tmpl in DAILY_QUEST_TEMPLATES else "weekly",
            "progress_pct": min(100, int((progress / tmpl["target"]) * 100)) if tmpl["target"] > 0 else 0,
        })

    return quests


def check_quest_progress(user_id: int, event_type: str, db: Session) -> list[dict]:
    """Update quest progress based on an event.

    Returns a list of quests that were completed by this event.
    """
    _ensure_user_loaded(user_id, db)

    completed_quests = []
    user_quests = _quest_progress.setdefault(user_id, {})

    for tmpl in DAILY_QUEST_TEMPLATES + WEEKLY_QUEST_TEMPLATES:
        if tmpl["event_type"] != event_type:
            continue

        state = user_quests.setdefault(tmpl["id"], {"progress": 0, "completed": False, "claimed": False})

        if state["completed"]:
            continue

        state["progress"] += 1
        if state["progress"] >= tmpl["target"]:
            state["completed"] = True
            completed_quests.append({
                "id": tmpl["id"],
                "title": tmpl["title"],
                "description": tmpl["description"],
                "reward_xp": tmpl["reward_xp"],
                "period": "daily" if tmpl in DAILY_QUEST_TEMPLATES else "weekly",
            })

    return completed_quests


def claim_quest_reward(user_id: int, quest_id: str, db: Session) -> dict:
    """Mark a quest reward as claimed and award XP."""
    from app.services.gamification.xp import award_xp

    user_quests = _quest_progress.get(user_id, {})
    state = user_quests.get(quest_id)
    if not state:
        raise ValueError(f"Quest {quest_id} not found for user {user_id}")
    if not state["completed"]:
        raise ValueError(f"Quest {quest_id} is not yet completed")
    if state["claimed"]:
        raise ValueError(f"Quest {quest_id} reward already claimed")

    # Find the template to get reward XP
    all_templates = {t["id"]: t for t in DAILY_QUEST_TEMPLATES + WEEKLY_QUEST_TEMPLATES}
    tmpl = all_templates.get(quest_id)
    if not tmpl:
        raise ValueError(f"Unknown quest {quest_id}")

    state["claimed"] = True
    result = award_xp(user_id, tmpl["reward_xp"], f"Quest reward: {tmpl['title']}", db)
    result["quest_title"] = tmpl["title"]
    return result
