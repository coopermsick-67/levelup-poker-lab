"""
Template strings for the AI Coach report.

Each template is a callable that accepts keyword arguments and returns
a formatted string.  Keeping them in one place makes it easy to tweak
the coach's "voice" without touching the report logic.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Player-type summaries
# ---------------------------------------------------------------------------

def summary_nit(vpip: float, pfr: float, three_bet: float) -> str:
    return (
        f"You're a tight-passive player (VPIP {vpip:.0f}%, PFR {pfr:.0f}%). "
        f"You wait for strong hands but don't punish opponents enough with raises. "
        f"Your 3-bet frequency of {three_bet:.0f}% is well below optimal — "
        "you're giving opponents too much initiative preflop."
    )


def summary_tag(vpip: float, pfr: float, three_bet: float) -> str:
    return (
        f"You play a solid tight-aggressive style (VPIP {vpip:.0f}%, PFR {pfr:.0f}%). "
        f"You're selective with your hands and aggressive when you enter pots. "
        f"Your 3-bet frequency of {three_bet:.0f}% shows you're willing to "
        "fight for pots, though there's still room to fine-tune."
    )


def summary_lag(vpip: float, pfr: float, three_bet: float) -> str:
    return (
        f"You're a loose-aggressive player (VPIP {vpip:.0f}%, PFR {pfr:.0f}%). "
        f"You play a wide range of hands and put pressure on opponents. "
        f"Your 3-bet frequency of {three_bet:.0f}% is high — great for "
        "applying pressure, but make sure you're choosing spots wisely."
    )


def summary_maniac(vpip: float, pfr: float, three_bet: float) -> str:
    return (
        f"You're playing very aggressively (VPIP {vpip:.0f}%, PFR {pfr:.0f}%). "
        f"You're involved in too many pots and betting/raising with marginal hands. "
        f"Your 3-bet frequency of {three_bet:.0f}% is extremely high — "
        "tightening up your starting hand range will win you more money long-term."
    )


def summary_default(vpip: float, pfr: float, three_bet: float) -> str:
    return (
        f"Your current stats show VPIP {vpip:.0f}%, PFR {pfr:.0f}%, "
        f"and a 3-bet frequency of {three_bet:.0f}%. "
        "Keep playing hands to build your sample size — the coach will "
        "give you more personalised feedback with more data."
    )


# ---------------------------------------------------------------------------
# Leak explanations
# ---------------------------------------------------------------------------

def leak_tight_passive() -> str:
    return (
        "You fold too often to aggression. When you enter a pot, you should "
        "be prepared to defend it — especially in position. Practice calling "
        "3-bets with your stronger hands instead of automatically folding."
    )


def leak_loose_passive() -> str:
    return (
        "You're playing too many hands but not being aggressive enough with them. "
        "Try raising more of your strong hands preflop for value instead of "
        "just calling. This builds bigger pots when you have the best hand."
    )


def leak_too_tight() -> str:
    return (
        "You're playing too few hands. While discipline is good, you're "
        "missing profitable opportunities — especially from late position. "
        "Try opening a wider range from the Cutoff and Button."
    )


def leak_over_aggressive() -> str:
    return (
        "You're betting and raising too frequently with marginal hands. "
        "Not every spot requires aggression — sometimes the best play is "
        "to check back and see a free card. Focus on board texture."
    )


def leak_low_cbet() -> str:
    return (
        "You're not continuation-betting enough on the flop after raising "
        "preflop. When you raise pre-flop and get called, you should follow "
        "through with a c-bet on most dry boards to build your value pots."
    )


def leak_high_cbet() -> str:
    return (
        "You're continuation-betting too often, including on wet/coordinated "
        "boards where your opponent's calling range is strong. Check back "
        "more on boards that favour the caller."
    )


def leak_position_awareness() -> str:
    return (
        "Your play doesn't vary enough by position. Good players open wider "
        "from late position and tighten up from early position. Review "
        "position-specific ranges and practice opening more from the Button."
    )


# ---------------------------------------------------------------------------
# Strengths
# ---------------------------------------------------------------------------

def strength_hand_selection() -> str:
    return "Solid starting hand selection — you're not bleeding chips with weak hands."


def strength_aggression() -> str:
    return "Good aggression — you're not just calling, you're raising for value."


def strength_postflop() -> str:
    return "Solid postflop play — you're making good decisions after the flop."


def strength_positional() -> str:
    return "Good positional awareness — you play differently from early vs late position."


def strength_discipline() -> str:
    return "Strong discipline — you're not chasing draws or playing emotionally."


def strength_three_bet() -> str:
    return "Healthy 3-bet frequency — you're fighting for pots at a good rate."


# ---------------------------------------------------------------------------
# Training plan suggestions
# ---------------------------------------------------------------------------

DRILL_PREFLOP_RANGES = {
    "name": "Preflop Ranges",
    "description": "Master opening ranges from every position.",
    "url": "/drills/preflop-ranges",
}

DRILL_CBET_MASTER = {
    "name": "C-Bet Master",
    "description": "Learn when to continuation bet and when to check back.",
    "url": "/drills/cbet-master",
}

DRILL_THREE_BET = {
    "name": "3-Bet Pot Control",
    "description": "Practice 3-betting and defending against 3-bets.",
    "url": "/drills/three-bet",
}

DRILL_POSITIONAL = {
    "name": "Positional Play",
    "description": "Adjust your ranges and aggression by seat position.",
    "url": "/drills/positional",
}

DRILL_POSTFLOP = {
    "name": "Postflop Fundamentals",
    "description": "Improve your flop, turn, and river decisions.",
    "url": "/drills/postflop",
}

DRILL_HAND_READING = {
    "name": "Hand Reading",
    "description": "Narrow opponent ranges to make better calls and folds.",
    "url": "/drills/hand-reading",
}


def training_plan_nit() -> list[dict]:
    return [
        {**DRILL_PREFLOP_RANGES, "reason": "You need to open a wider range from late position."},
        {**DRILL_THREE_BET, "reason": "Your 3-bet frequency is too low — practice fighting back."},
        {**DRILL_CBET_MASTER, "reason": "Start building bigger pots with continuation bets."},
    ]


def training_plan_tag() -> list[dict]:
    return [
        {**DRILL_POSTFLOP, "reason": "Fine-tune your postflop aggression based on board texture."},
        {**DRILL_HAND_READING, "reason": "Sharpen your hand reading to make better river decisions."},
    ]


def training_plan_lag() -> list[dict]:
    return [
        {**DRILL_PREFLOP_RANGES, "reason": "Tighten your opening range to avoid marginal spots."},
        {**DRILL_CBET_MASTER, "reason": "Learn to check back on wet boards."},
    ]


def training_plan_maniac() -> list[dict]:
    return [
        {**DRILL_PREFLOP_RANGES, "reason": "Your range is too wide — focus on premium hands."},
        {**DRILL_POSTFLOP, "reason": "Practice checking back and playing more passively with medium-strength hands."},
        {**DRILL_HAND_READING, "reason": "Learn to fold more when you're behind."},
    ]


def training_plan_default() -> list[dict]:
    return [
        {**DRILL_PREFLOP_RANGES, "reason": "Build a solid preflop foundation first."},
        {**DRILL_POSTFLOP, "reason": "Practice postflop decision-making with real hand scenarios."},
    ]
