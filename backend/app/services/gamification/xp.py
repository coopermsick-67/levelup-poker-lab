"""XP and leveling system for LevelUp Poker Lab."""

from sqlalchemy.orm import Session

from app.models.user import User

# XP thresholds per level (index = level, value = XP required to reach that level)
XP_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 1000,
    6: 2000,
    7: 4000,
    8: 8000,
    9: 16000,
    10: 32000,
}

# XP award amounts for different activities
XP_AWARDS = {
    "play_hand": 10,
    "complete_drill": 20,
    "correct_drill_answer": 5,
    "complete_review": 15,
    "daily_login": 5,
}

MAX_LEVEL = max(XP_THRESHOLDS.keys())


def get_level(xp: int) -> int:
    """Compute the user's level from their total XP.

    Iterates thresholds from highest to lowest to find the level
    the user has reached.
    """
    level = 1
    for lvl in sorted(XP_THRESHOLDS.keys()):
        if xp >= XP_THRESHOLDS[lvl]:
            level = lvl
        else:
            break
    return level


def get_xp_for_next_level(xp: int) -> int | None:
    """Return the XP required to reach the next level, or None if at max level."""
    current_level = get_level(xp)
    next_level = current_level + 1
    if next_level > MAX_LEVEL:
        return None
    return XP_THRESHOLDS[next_level]


def get_level_progress(xp: int) -> dict:
    """Return progress info for the current level."""
    current_level = get_level(xp)
    current_threshold = XP_THRESHOLDS[current_level]
    next_threshold = get_xp_for_next_level(xp)

    if next_threshold is None:
        return {
            "current_level": current_level,
            "xp_in_level": 0,
            "xp_needed_for_next": 0,
            "progress_pct": 100,
            "is_max_level": True,
        }

    xp_in_level = xp - current_threshold
    xp_needed = next_threshold - current_threshold
    progress_pct = min(100, int((xp_in_level / xp_needed) * 100)) if xp_needed > 0 else 100

    return {
        "current_level": current_level,
        "xp_in_level": xp_in_level,
        "xp_needed_for_next": xp_needed,
        "progress_pct": progress_pct,
        "is_max_level": False,
    }


def award_xp(user_id: int, amount: int, reason: str, db: Session) -> dict:
    """Award XP to a user and handle level-ups.

    Returns a dict with keys:
      - xp_earned: amount awarded
      - old_level: level before award
      - new_level: level after award
      - leveled_up: whether a level-up occurred
      - new_total_xp: total XP after award
      - reason: the reason string
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    old_level = user.level
    user.xp += amount
    new_level = get_level(user.xp)
    user.level = new_level
    db.commit()
    db.refresh(user)

    return {
        "xp_earned": amount,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
        "new_total_xp": user.xp,
        "reason": reason,
    }
