"""
AI Coach Report Generator.

Produces a personalised coaching report based on the player's stats and
detected leaks.  Uses LLM when available (via OPENROUTER_API_KEY),
otherwise falls back to deterministic rules-based generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.analytics.stats import compute_stats
from app.services.analytics.leaks import find_leaks
from app.services.ai_coach import templates
from app.services.ai_coach.llm_adapter import LLMAdapter
from app.services.poker_engine.game_manager import game_manager

DECISIONS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "user_decisions.json"


class _DecisionProxy:
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


def _load_decisions(user_id: int) -> list[_DecisionProxy]:
    if DECISIONS_PATH.exists():
        try:
            data = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
            raw = data.get(str(user_id), [])
            return [_DecisionProxy(d) for d in raw]
        except (json.JSONDecodeError, OSError):
            pass

    decisions: list[dict[str, Any]] = []
    for table in game_manager.tables.values():
        for hand_data in getattr(table, "decision_log", []):
            if hand_data.get("user_id") == user_id:
                decisions.append(hand_data)
    return [_DecisionProxy(d) for d in decisions]


def _classify_player(stats: dict) -> str:
    vpip = stats.get("vpip", 0.0)
    pfr = stats.get("pfr", 0.0)
    af = stats.get("aggression_factor", 0.0)
    total_hands = stats.get("total_hands", 0)

    if total_hands < 5:
        return "default"
    if vpip > 35 and af > 4:
        return "maniac"
    if vpip > 25 and pfr > 18 and af > 2:
        return "lag"
    if 18 <= vpip <= 28 and pfr >= 12 and af >= 1.5:
        return "tag"
    if vpip < 18 and af < 1.5:
        return "nit"
    if vpip < 20:
        return "nit"
    if vpip > 30:
        return "lag"
    return "tag"


def _find_strengths(stats: dict) -> list[str]:
    strengths: list[str] = []
    vpip = stats.get("vpip", 0.0)
    pfr = stats.get("pfr", 0.0)
    three_bet = stats.get("three_bet_pct", 0.0)
    af = stats.get("aggression_factor", 0.0)
    wwsf = stats.get("wwsf_pct", 0.0)
    pos_stats = stats.get("position_stats", {})

    if 18 <= vpip <= 28:
        strengths.append(templates.strength_hand_selection())
    if af >= 1.5 and af <= 4.0:
        strengths.append(templates.strength_aggression())
    if wwsf >= 40:
        strengths.append(templates.strength_postflop())
    btn_vpip = pos_stats.get("BTN", {}).get("vpip", 0.0)
    utg_vpip = pos_stats.get("UTG", {}).get("vpip", 0.0)
    if btn_vpip > utg_vpip + 10 and btn_vpip > 0:
        strengths.append(templates.strength_positional())
    if vpip < 20 and pfr < 12:
        strengths.append(templates.strength_discipline())
    if 4 <= three_bet <= 10:
        strengths.append(templates.strength_three_bet())

    seen: set[str] = set()
    unique: list[str] = []
    for s in strengths:
        if s not in seen:
            seen.add(s)
            unique.append(s)
        if len(unique) >= 3:
            break

    if not unique:
        unique.append("You're putting in the work by reviewing your play — that's the first step to improvement.")

    return unique


def _build_training_plan(archetype: str, stats: dict, leaks: list[dict]) -> list[dict]:
    total_hands = stats.get("total_hands", 0)

    if total_hands < 5:
        return [templates.training_plan_default()[0]]

    plan_map = {
        "nit": templates.training_plan_nit,
        "tag": templates.training_plan_tag,
        "lag": templates.training_plan_lag,
        "maniac": templates.training_plan_maniac,
        "default": templates.training_plan_default,
    }
    plan = plan_map.get(archetype, templates.training_plan_default)()

    major_leaks = [l for l in leaks if l.get("severity") == "major"]
    if major_leaks and archetype != "default":
        first_major = major_leaks[0]
        category = first_major.get("category", "preflop")
        if category == "postflop":
            plan.insert(0, {
                **templates.DRILL_POSTFLOP,
                "reason": first_major["description"][:100],
            })
        elif category == "positional":
            plan.insert(0, {
                **templates.DRILL_POSITIONAL,
                "reason": first_major["description"][:100],
            })

    return plan[:3]


class CoachReport:
    """Generates a personalised coaching report for a user."""

    def __init__(self):
        self._llm = LLMAdapter()

    def generate(self, user_id: int, db: Session) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return self._empty_report("User not found.")

        decisions = _load_decisions(user_id)
        stats = compute_stats(decisions)
        leaks = find_leaks(stats)
        archetype = _classify_player(stats)

        # Try LLM for summary, fall back to rules-based
        if self._llm.is_available():
            try:
                llm_summary = self._llm.generate_report(
                    stats={k: stats.get(k, 0.0) for k in [
                        "total_hands", "vpip", "pfr", "three_bet_pct",
                        "cbet_pct", "aggression_factor", "wwsf_pct",
                    ]},
                    leaks=[l.get("description", "") for l in leaks[:5]],
                )
                if llm_summary and "coming soon" not in llm_summary.lower():
                    summary = llm_summary
                else:
                    summary = self._rules_summary(archetype, stats)
            except Exception:
                summary = self._rules_summary(archetype, stats)
        else:
            summary = self._rules_summary(archetype, stats)

        strengths = _find_strengths(stats)
        training_plan = _build_training_plan(archetype, stats, leaks)

        stats_snapshot = {
            "total_hands": stats.get("total_hands", 0),
            "vpip": stats.get("vpip", 0.0),
            "pfr": stats.get("pfr", 0.0),
            "three_bet_pct": stats.get("three_bet_pct", 0.0),
            "cbet_pct": stats.get("cbet_pct", 0.0),
            "aggression_factor": stats.get("aggression_factor", 0.0),
            "wwsf_pct": stats.get("wwsf_pct", 0.0),
        }

        return {
            "summary": summary,
            "archetype": archetype,
            "leaks": leaks[:5],
            "strengths": strengths,
            "training_plan": training_plan,
            "stats_snapshot": stats_snapshot,
        }

    @staticmethod
    def _rules_summary(archetype: str, stats: dict) -> str:
        summary_map = {
            "nit": templates.summary_nit,
            "tag": templates.summary_tag,
            "lag": templates.summary_lag,
            "maniac": templates.summary_maniac,
            "default": templates.summary_default,
        }
        return summary_map.get(archetype, templates.summary_default)(
            vpip=stats.get("vpip", 0.0),
            pfr=stats.get("pfr", 0.0),
            three_bet=stats.get("three_bet_pct", 0.0),
        )

    @staticmethod
    def _empty_report(reason: str) -> dict:
        return {
            "summary": reason,
            "archetype": "unknown",
            "leaks": [],
            "strengths": [],
            "training_plan": [templates.training_plan_default()[0]],
            "stats_snapshot": {
                "total_hands": 0,
                "vpip": 0.0,
                "pfr": 0.0,
                "three_bet_pct": 0.0,
                "cbet_pct": 0.0,
                "aggression_factor": 0.0,
                "wwsf_pct": 0.0,
            },
        }
