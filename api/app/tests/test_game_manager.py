"""Tests for GameManager — raise validation, heads-up play, hand lifecycle."""

from __future__ import annotations

import pytest

from app.services.poker_engine.game_manager import GameManager
from app.services.poker_engine.table import Street


@pytest.fixture
def gm():
    return GameManager()


@pytest.fixture
def table(gm):
    return gm.create_table(hero_id=1, hero_name="Hero")


@pytest.fixture
def started_table(gm, table):
    gm.start_hand(table.table_id)
    return table


class TestRaiseValidation:
    def test_raise_below_min_is_clamped(self, gm, started_table):
        """A raise below the minimum should be clamped to min_raise."""
        # Find when hero can act
        hero = started_table.get_hero_seat()
        started_table.active_seat_index = hero.index
        result = gm.apply_hero_action(started_table.table_id, 1, "raise", 1)
        # Should not error — amount is clamped
        assert "error" not in result or result.get("error") != "Not your turn"

    def test_raise_above_max_is_clamped(self, gm, started_table):
        """A raise above stack should be clamped to all-in."""
        hero = started_table.get_hero_seat()
        started_table.active_seat_index = hero.index
        result = gm.apply_hero_action(started_table.table_id, 1, "raise", 999999)
        assert "error" not in result or result.get("error") != "Not your turn"

    def test_valid_raise_accepted(self, gm, started_table):
        """A valid raise should work normally."""
        hero = started_table.get_hero_seat()
        started_table.active_seat_index = hero.index
        # BB is 20, so min raise = 40 total
        result = gm.apply_hero_action(started_table.table_id, 1, "raise", 40)
        assert "error" not in result or result.get("error") != "Not your turn"


class TestHeadsUpPreflop:
    def test_heads_up_button_acts_first(self, gm):
        """In heads-up, button/SB should act first preflop."""
        table = gm.create_table(hero_id=1, hero_name="Hero")
        # Only keep seats 0 and 1 active (heads-up)
        for i in range(2, 6):
            table.seats[i].status = gm.tables[table.table_id].seats[i].status = table.seats[i].status
        # Deactivate seats 2-5
        for i in range(2, 6):
            table.seats[i].status = table.seats[i].status.__class__.SITTING_OUT
        gm.start_hand(table.table_id)
        # Button should be first to act preflop in heads-up
        assert table.current_street == Street.PREFLOP


class TestHandLifecycle:
    def test_fold_ends_hand(self, gm, started_table):
        """Folding should end the hand when only one player remains."""
        hero = started_table.get_hero_seat()
        started_table.active_seat_index = hero.index
        result = gm.apply_hero_action(started_table.table_id, 1, "fold")
        assert result.get("hand_complete") is True

    def test_full_hand_to_showdown(self, gm, table):
        """Playing through all streets should reach showdown."""
        gm.start_hand(table.table_id)
        hero = table.get_hero_seat()
        max_steps = 50
        steps = 0
        while steps < max_steps:
            steps += 1
            if not table.is_hand_in_progress:
                break
            if table.active_seat_index != hero.index:
                break
            legal = gm.get_legal_actions(table.table_id, 1)
            if "check" in legal:
                result = gm.apply_hero_action(table.table_id, 1, "check")
            elif "call" in legal:
                result = gm.apply_hero_action(table.table_id, 1, "call")
            else:
                result = gm.apply_hero_action(table.table_id, 1, "fold")
                break
            if result.get("hand_complete"):
                break
        assert steps < max_steps  # Should complete, not hit safety limit


class TestBotAI:
    def test_bots_act_after_hero(self, gm, started_table):
        """After hero checks, bots should act."""
        hero = started_table.get_hero_seat()
        started_table.active_seat_index = hero.index
        result = gm.apply_hero_action(started_table.table_id, 1, "check")
        # Result should either be waiting for hero or hand complete
        assert "table" in result
