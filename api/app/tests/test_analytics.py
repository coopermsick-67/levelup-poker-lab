"""Tests for poker analytics (stats computation + leak detection)."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

import pytest

from app.services.analytics.stats import compute_stats, get_position_name
from app.services.analytics.leaks import find_leaks


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

@dataclass
class FakeDecision:
    """Lightweight stand-in for HandDecision for testing."""
    hand_id: int = 0
    street: str = "preflop"
    position: str = "BTN"
    action_taken: str = "fold"
    amount: int = 0
    pot_size: int = 0
    stack_size: int = 2000
    hole_cards: str = ""
    community_cards: str = ""
    was_correct: int | None = None
    ev_diff: int | None = None


def make_decisions(*specs: dict[str, Any]) -> list[FakeDecision]:
    """Convenience builder: pass dicts of overrides."""
    base: dict[str, Any] = dict(
        hand_id=0, street="preflop", position="BTN",
        action_taken="fold", amount=0, pot_size=0,
        stack_size=2000, hole_cards="", community_cards="",
        was_correct=None, ev_diff=None,
    )
    out: list[FakeDecision] = []
    next_hand = 1
    for spec in specs:
        d = dict(base)
        if "hand_id" not in spec:
            d["hand_id"] = next_hand
            next_hand += 1
        d.update(spec)
        out.append(FakeDecision(**d))
    return out


def tight_passive_player_hands(n_hands: int = 40) -> list[FakeDecision]:
    """Generate decisions simulating a tight-passive player (VPIP ~15%)."""
    decisions: list[FakeDecision] = []
    for h in range(1, n_hands + 1):
        # Only raise with ~10% of hands, call ~5%, rest fold => VPIP ~15%
        if h % 10 == 0:
            decisions.append(FakeDecision(
                hand_id=h, street="preflop", position="BTN",
                action_taken="raise", amount=30, pot_size=15,
            ))
        elif h % 20 == 0:
            decisions.append(FakeDecision(
                hand_id=h, street="preflop", position="CO",
                action_taken="call", amount=10, pot_size=15,
            ))
        else:
            decisions.append(FakeDecision(
                hand_id=h, street="preflop", position="UTG",
                action_taken="fold", amount=0, pot_size=15,
            ))
        # Sometimes see flop when called/raised
        if decisions[-1].action_taken in ("call", "raise"):
            decisions.append(FakeDecision(
                hand_id=h, street="flop", position=decisions[-1].position,
                action_taken="check", amount=0, pot_size=30,
                ev_diff=-5,
            ))
    return decisions


def loose_aggressive_player_hands(n_hands: int = 40) -> list[FakeDecision]:
    """Generate decisions simulating a loose-aggressive player."""
    decisions: list[FakeDecision] = []
    positions_cycle = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
    for h in range(1, n_hands + 1):
        pos = positions_cycle[h % 6]
        # VPIP ~40%
        if h % 5 != 0:
            if h % 3 == 0:
                decisions.append(FakeDecision(
                    hand_id=h, street="preflop", position=pos,
                    action_taken="raise", amount=30, pot_size=15,
                ))
            else:
                decisions.append(FakeDecision(
                    hand_id=h, street="preflop", position=pos,
                    action_taken="call", amount=10, pot_size=15,
                ))
            # c-bet often
            decisions.append(FakeDecision(
                hand_id=h, street="flop", position=pos,
                action_taken="raise", amount=40, pot_size=60,
                ev_diff=10 if h % 4 == 0 else -5,
            ))
        else:
            decisions.append(FakeDecision(
                hand_id=h, street="preflop", position=pos,
                action_taken="fold", amount=0, pot_size=15,
            ))
    return decisions


# ---------------------------------------------------------------------------
# get_position_name tests
# ---------------------------------------------------------------------------

class TestGetPositionName:
    def test_button(self):
        assert get_position_name(0, 0, 6) == "BTN"

    def test_sb_from_button(self):
        assert get_position_name(1, 0, 6) == "SB"

    def test_bb_from_button(self):
        assert get_position_name(2, 0, 6) == "BB"

    def test_utg_from_button(self):
        assert get_position_name(3, 0, 6) == "UTG"

    def test_mp_from_button(self):
        assert get_position_name(4, 0, 6) == "MP"

    def test_co_from_button(self):
        assert get_position_name(5, 0, 6) == "CO"

    def test_wraps_around_table(self):
        # Seat 0 when button is at seat 4 => rel = (0-4)%6 = 2 => BB
        assert get_position_name(0, 4, 6) == "BB"

    def test_heads_up(self):
        assert get_position_name(0, 0, 2) == "BTN"
        assert get_position_name(1, 0, 2) == "BB"

    def test_9_max_positions(self):
        assert get_position_name(3, 0, 9) == "UTG"
        assert get_position_name(4, 0, 9) == "UTG+1"
        assert get_position_name(7, 0, 9) == "HJ"
        assert get_position_name(8, 0, 9) == "CO"

    def test_3_player(self):
        assert get_position_name(0, 0, 3) == "BTN"
        assert get_position_name(1, 0, 3) == "SB"
        assert get_position_name(2, 0, 3) == "BB"

    def test_seat_equals_button_is_btn(self):
        for total in range(2, 10):
            assert get_position_name(5, 5, total) == "BTN"


# ---------------------------------------------------------------------------
# compute_stats — empty / edge cases
# ---------------------------------------------------------------------------

class TestComputeStatsEmpty:
    def test_no_decisions(self):
        stats = compute_stats([])
        assert stats["total_hands"] == 0
        assert stats["total_decisions"] == 0
        assert stats["vpip"] == 0.0
        assert stats["pfr"] == 0.0
        assert stats["aggression_factor"] == 0.0

    def test_position_stats_present(self):
        stats = compute_stats([])
        for pos in ("UTG", "MP", "CO", "BTN", "SB", "BB"):
            assert pos in stats["position_stats"]


# ---------------------------------------------------------------------------
# compute_stats — VPIP / PFR
# ---------------------------------------------------------------------------

class TestComputeStatsVpipPfr:
    def test_all_folds(self):
        decisions = [
            FakeDecision(hand_id=i, street="preflop", position="BTN", action_taken="fold")
            for i in range(1, 11)
        ]
        stats = compute_stats(decisions)
        assert stats["vpip"] == 0.0
        assert stats["pfr"] == 0.0

    def test_all_raises(self):
        decisions = [
            FakeDecision(hand_id=i, street="preflop", position="BTN", action_taken="raise", amount=30)
            for i in range(1, 11)
        ]
        stats = compute_stats(decisions)
        assert stats["vpip"] == 100.0
        assert stats["pfr"] == 100.0

    def test_half_call_half_raise(self):
        decisions = []
        for i in range(1, 11):
            if i % 2 == 0:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", action_taken="call", amount=10, position="BTN",
                ))
            else:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", action_taken="raise", amount=30, position="BTN",
                ))
        stats = compute_stats(decisions)
        assert stats["vpip"] == 100.0  # all hands either called or raised
        assert stats["pfr"] == 50.0    # half raised

    def test_vpip_pfr_gap(self):
        """4 calls, 1 raise, 5 folds => VPIP=50%, PFR=10%."""
        decisions = []
        for i in range(1, 11):
            if i <= 5:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", action_taken="fold", position="UTG",
                ))
            elif i <= 9:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", action_taken="call", amount=10, position="BTN",
                ))
            else:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", action_taken="raise", amount=30, position="BTN",
                ))
        stats = compute_stats(decisions)
        assert stats["vpip"] == 50.0
        assert stats["pfr"] == 10.0


# ---------------------------------------------------------------------------
# compute_stats — Aggression Factor
# ---------------------------------------------------------------------------

class TestComputeStatsAggression:
    def test_af_basic(self):
        """2 raises, 1 call => AF = 2.0."""
        decisions = [
            FakeDecision(hand_id=1, street="preflop", action_taken="raise", amount=30),
            FakeDecision(hand_id=2, street="flop", action_taken="raise", amount=40),
            FakeDecision(hand_id=3, street="flop", action_taken="call", amount=20),
        ]
        stats = compute_stats(decisions)
        assert stats["aggression_factor"] == 2.0

    def test_af_no_calls(self):
        raises_only = [
            FakeDecision(hand_id=1, street="preflop", action_taken="raise", amount=30),
            FakeDecision(hand_id=2, street="flop", action_taken="raise", amount=40),
        ]
        stats = compute_stats(raises_only)
        assert stats["aggression_factor"] == 2.0  # bets_raises / 1 (default)

    def test_af_all_calls(self):
        calls_only = [
            FakeDecision(hand_id=1, street="preflop", action_taken="call", amount=10),
            FakeDecision(hand_id=2, street="flop", action_taken="call", amount=20),
        ]
        stats = compute_stats(calls_only)
        assert stats["aggression_factor"] == 0.0


# ---------------------------------------------------------------------------
# compute_stats — Position-specific
# ---------------------------------------------------------------------------

class TestComputeStatsPosition:
    def test_position_vpip(self):
        """Player raises from BTN, folds from UTG."""
        decisions = []
        for i in range(1, 11):
            if i % 2 == 0:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", position="BTN",
                    action_taken="raise", amount=30,
                ))
            else:
                decisions.append(FakeDecision(
                    hand_id=i, street="preflop", position="UTG",
                    action_taken="fold", amount=0,
                ))
        stats = compute_stats(decisions)
        assert stats["position_stats"]["BTN"]["vpip"] == 100.0
        assert stats["position_stats"]["BTN"]["pfr"] == 100.0
        assert stats["position_stats"]["UTG"]["vpip"] == 0.0
        assert stats["position_stats"]["UTG"]["pfr"] == 0.0


# ---------------------------------------------------------------------------
# compute_stats — WWSF
# ---------------------------------------------------------------------------

class TestComputeStatsWwsf:
    def test_wwsf_with_positive_ev(self):
        decisions = [
            FakeDecision(
                hand_id=1, street="flop", action_taken="call", amount=10,
                pot_size=30, ev_diff=20,
            ),
            FakeDecision(
                hand_id=2, street="fold", action_taken="fold", amount=0,
                pot_size=15, ev_diff=-5,
            ),
        ]
        stats = compute_stats(decisions)
        # Only hand 1 saw flop, and it had positive ev_diff
        assert stats["wwsf_pct"] == 100.0

    def test_wwsf_no_flop_seen(self):
        decisions = [
            FakeDecision(hand_id=1, street="preflop", action_taken="fold"),
        ]
        stats = compute_stats(decisions)
        assert stats["wwsf_pct"] == 0.0


# ---------------------------------------------------------------------------
# compute_stats — 3-bet detection
# ---------------------------------------------------------------------------

class TestComputeStatsThreeBet:
    def test_three_bet_detected(self):
        """Raise when pot is already >30 (opponent raised)."""
        decisions = [
            FakeDecision(
                hand_id=1, street="preflop", action_taken="raise", amount=60,
                pot_size=45, position="BTN",
            ),
        ]
        stats = compute_stats(decisions)
        assert stats["three_bet_pct"] == 100.0

    def test_no_three_bet_when_small_pot(self):
        decisions = [
            FakeDecision(
                hand_id=1, street="preflop", action_taken="raise", amount=30,
                pot_size=15, position="BTN",
            ),
        ]
        stats = compute_stats(decisions)
        assert stats["three_bet_pct"] == 0.0


# ---------------------------------------------------------------------------
# find_leaks — empty / edge cases
# ---------------------------------------------------------------------------

class TestFindLeaksEmpty:
    def test_empty_stats(self):
        leaks = find_leaks({})
        assert len(leaks) == 1
        assert "Not enough data" in leaks[0]["description"]

    def test_zero_hands(self):
        leaks = find_leaks({"total_hands": 0})
        assert len(leaks) == 1
        assert "Not enough data" in leaks[0]["description"]


# ---------------------------------------------------------------------------
# find_leaks — preflop leaks
# ---------------------------------------------------------------------------

class TestFindLeaksPreflop:
    def test_too_tight(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 100,
            "vpip": 10.0, "pfr": 8.0,
            "three_bet_pct": 2.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "tight" in descs.lower() or "VPIP" in descs

    def test_too_loose(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 100,
            "vpip": 40.0, "pfr": 15.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "loose" in descs.lower() or "VPIP" in descs

    def test_too_passive_preflop(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 100,
            "vpip": 30.0, "pfr": 5.0,
            "three_bet_pct": 2.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "PFR" in descs or "passive" in descs.lower()

    def test_low_three_bet(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 100,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 1.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "3-bet" in descs or "3-bet" in descs.lower()


# ---------------------------------------------------------------------------
# find_leaks — postflop leaks
# ---------------------------------------------------------------------------

class TestFindLeaksPostflop:
    def test_low_cbet(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 25.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "c-bet" in descs.lower() or "c-bet" in descs

    def test_high_cbet(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 90.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "c-bet" in descs.lower() or "auto-c-bet" in descs.lower()

    def test_low_aggression(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 0.5, "wwsf_pct": 40.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "aggression" in descs.lower() or "passive" in descs.lower()

    def test_low_wwsf(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 25.0,
            "position_stats": {},
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "WWSF" in descs or "wwsf" in descs.lower()


# ---------------------------------------------------------------------------
# find_leaks — positional leaks
# ---------------------------------------------------------------------------

class TestFindLeaksPositional:
    def test_utg_too_loose(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {
                "UTG": {"hands": 20, "vpip": 30.0, "pfr": 15.0},
                "MP": {"hands": 15, "vpip": 20.0, "pfr": 12.0},
                "CO": {"hands": 15, "vpip": 25.0, "pfr": 18.0},
                "BTN": {"hands": 15, "vpip": 40.0, "pfr": 30.0},
                "SB": {"hands": 10, "vpip": 20.0, "pfr": 10.0},
                "BB": {"hands": 10, "vpip": 15.0, "pfr": 8.0},
            },
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "UTG" in descs

    def test_btn_too_tight(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {
                "UTG": {"hands": 10, "vpip": 12.0, "pfr": 8.0},
                "MP": {"hands": 10, "vpip": 18.0, "pfr": 12.0},
                "CO": {"hands": 10, "vpip": 22.0, "pfr": 16.0},
                "BTN": {"hands": 20, "vpip": 20.0, "pfr": 15.0},
                "SB": {"hands": 10, "vpip": 20.0, "pfr": 10.0},
                "BB": {"hands": 10, "vpip": 15.0, "pfr": 8.0},
            },
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "button" in descs.lower() or "BTN" in descs

    def test_sb_too_loose(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 16.0,
            "three_bet_pct": 5.0, "fold_to_3bet_pct": 50.0,
            "cbet_pct": 50.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.0, "wwsf_pct": 40.0,
            "position_stats": {
                "UTG": {"hands": 10, "vpip": 12.0, "pfr": 8.0},
                "MP": {"hands": 10, "vpip": 18.0, "pfr": 12.0},
                "CO": {"hands": 10, "vpip": 25.0, "pfr": 18.0},
                "BTN": {"hands": 15, "vpip": 45.0, "pfr": 35.0},
                "SB": {"hands": 15, "vpip": 45.0, "pfr": 15.0},
                "BB": {"hands": 10, "vpip": 15.0, "pfr": 8.0},
            },
        }
        leaks = find_leaks(stats)
        descs = " ".join(l["description"] for l in leaks)
        assert "small blind" in descs.lower() or "SB" in descs


# ---------------------------------------------------------------------------
# find_leaks — no leaks (healthy stats)
# ---------------------------------------------------------------------------

class TestFindLeaksHealthy:
    def test_healthy_player(self):
        stats = {
            "total_hands": 50,
            "total_decisions": 200,
            "vpip": 22.0, "pfr": 18.0,
            "three_bet_pct": 6.0, "fold_to_3bet_pct": 55.0,
            "cbet_pct": 55.0, "fold_to_cbet_pct": 50.0,
            "aggression_factor": 2.5, "wwsf_pct": 42.0,
            "position_stats": {
                "UTG": {"hands": 15, "vpip": 14.0, "pfr": 10.0},
                "MP": {"hands": 15, "vpip": 18.0, "pfr": 14.0},
                "CO": {"hands": 15, "vpip": 28.0, "pfr": 22.0},
                "BTN": {"hands": 20, "vpip": 42.0, "pfr": 32.0},
                "SB": {"hands": 10, "vpip": 25.0, "pfr": 12.0},
                "BB": {"hands": 10, "vpip": 18.0, "pfr": 10.0},
            },
        }
        leaks = find_leaks(stats)
        # Should return the "no leaks" positive feedback
        assert len(leaks) == 1
        assert "No major leaks" in leaks[0]["description"]


# ---------------------------------------------------------------------------
# Integration: full pipeline with simulated player profiles
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_tight_passive_profile(self):
        decisions = tight_passive_player_hands(40)
        stats = compute_stats(decisions)
        leaks = find_leaks(stats)

        # Should detect tightness
        descs = " ".join(l["description"] for l in leaks)
        assert "tight" in descs.lower() or "VPIP" in descs

    def test_loose_aggressive_profile(self):
        decisions = loose_aggressive_player_hands(40)
        stats = compute_stats(decisions)
        leaks = find_leaks(stats)

        # Should detect looseness
        descs = " ".join(l["description"] for l in leaks)
        assert "loose" in descs.lower() or "VPIP" in descs

    def test_stats_keys_present(self):
        decisions = tight_passive_player_hands(20)
        stats = compute_stats(decisions)
        expected_keys = {
            "total_hands", "total_decisions", "vpip", "pfr",
            "three_bet_pct", "fold_to_3bet_pct",
            "cbet_pct", "fold_to_cbet_pct",
            "aggression_factor", "wwsf_pct", "position_stats",
        }
        assert expected_keys.issubset(stats.keys())

    def test_leak_structure(self):
        decisions = tight_passive_player_hands(20)
        stats = compute_stats(decisions)
        leaks = find_leaks(stats)
        for leak in leaks:
            assert "description" in leak
            assert "severity" in leak
            assert "category" in leak
            assert leak["severity"] in ("minor", "moderate", "major")
            assert leak["category"] in ("preflop", "postflop", "positional")
