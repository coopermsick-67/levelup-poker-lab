"""Streak tracking service for LevelUp Poker Lab."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.user import User


def get_streak_info(user_id: int, db: Session) -> dict:
    """Return current streak and longest streak for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    return {
        "current_streak": user.streak,
        "longest_streak": user.longest_streak,
        "last_active": user.last_active.isoformat() if user.last_active else None,
    }


def update_streak(user_id: int, db: Session) -> dict:
    """Update the user's streak based on activity today.

    Rules:
    - If active today already: no change.
    - If active yesterday: increment streak.
    - If last active was 2+ days ago: reset streak to 1.

    Returns dict with:
      - previous_streak: streak before update
      - current_streak: streak after update
      - longest_streak: all-time best
      - changed: whether the streak value changed
      - message: encouraging message string
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    today = date.today()
    previous_streak = user.streak

    if user.last_active:
        last_active_date = user.last_active.date() if hasattr(user.last_active, "date") else user.last_active
        # Handle datetime vs date comparison
        if hasattr(last_active_date, "date"):
            last_active_date = last_active_date.date()
    else:
        last_active_date = None

    if last_active_date == today:
        # Already active today, no change
        return {
            "previous_streak": previous_streak,
            "current_streak": user.streak,
            "longest_streak": user.longest_streak,
            "changed": False,
            "message": "You're active today. Nice work!",
        }

    if last_active_date == today - timedelta(days=1):
        # Consecutive day: increment
        user.streak += 1
        message = "Keep it up!"
    else:
        # Missed one or more days: reset
        user.streak = 1
        message = "Fresh start! Let's build that streak back up."

    if user.streak > user.longest_streak:
        user.longest_streak = user.streak

    from datetime import datetime
    user.last_active = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "previous_streak": previous_streak,
        "current_streak": user.streak,
        "longest_streak": user.longest_streak,
        "changed": user.streak != previous_streak,
        "message": message,
    }
