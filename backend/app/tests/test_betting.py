import pytest
from app.services.poker_engine.deck import Card, Deck, Rank, Suit
from app.services.poker_engine.table import Table, Seat, Street, SeatStatus
from app.services.poker_engine.betting import Action, ActionType, BettingRound


def make_cards(*strings):
    return [Card.from_str(s) for s in strings]


@pytest.fixture
def table():
    t = Table(table_id="test")
    for i in range(6):
        t.seats[i].player_id = i + 1
        t.seats[i].display_name = f"P{i + 1}"
        t.seats[i].stack = 1000
        t.seats[i].status = SeatStatus.ACTIVE
    return t


class TestBettingRound:
    def test_fold(self, table):
        seat = table.seats[0]
        BettingRound.apply_action(table, seat, Action(ActionType.FOLD, 0))
        assert seat.status == SeatStatus.FOLDED
        assert table.pot == 0

    def test_check(self, table):
        seat = table.seats[0]
        BettingRound.apply_action(table, seat, Action(ActionType.CHECK, 0))
        assert seat.stack == 1000
        assert table.pot == 0

    def test_call(self, table):
        table.seats[0].current_bet = 100  # Someone bet 100
        seat = table.seats[1]
        BettingRound.apply_action(table, seat, Action(ActionType.CALL, 1))
        assert seat.stack == 900
        assert seat.current_bet == 100

    def test_raise(self, table):
        seat = table.seats[0]
        BettingRound.apply_action(table, seat, Action(ActionType.RAISE, 0, 200))
        assert seat.stack == 800
        assert seat.current_bet == 200
        assert table.pot == 200

    def test_all_in(self, table):
        seat = table.seats[0]
        seat.stack = 500
        BettingRound.apply_action(table, seat, Action(ActionType.ALL_IN, 0))
        assert seat.stack == 0
        assert seat.status == SeatStatus.ALL_IN
        assert table.pot == 500

    def test_legal_actions_when_no_bet(self, table):
        seat = table.seats[0]
        actions = BettingRound.get_legal_actions(table, seat)
        assert ActionType.CHECK in actions
        assert ActionType.RAISE in actions
        assert ActionType.ALL_IN in actions
        assert ActionType.FOLD not in actions
        assert ActionType.CALL not in actions

    def test_legal_actions_when_bet_to_call(self, table):
        table.seats[1].current_bet = 100
        seat = table.seats[0]
        actions = BettingRound.get_legal_actions(table, seat)
        assert ActionType.FOLD in actions
        assert ActionType.CALL in actions
        assert ActionType.RAISE in actions
        assert ActionType.ALL_IN in actions
        assert ActionType.CHECK not in actions

    def test_round_complete_all_checked(self, table):
        # Only use first 3 seats: set others to sitting out
        for s in table.seats[3:]:
            s.status = SeatStatus.SITTING_OUT
        for s in table.seats[:3]:
            BettingRound.apply_action(table, s, Action(ActionType.CHECK, s.index))
        acting = table.get_acting_seats()
        assert len(acting) == 3

    def test_side_pot_calculation(self, table):
        # P1 all-in for 200, P2 all-in for 500, P3 calls 500
        for s in table.seats[3:]:
            s.status = SeatStatus.SITTING_OUT
        s0, s1, s2 = table.seats[0], table.seats[1], table.seats[2]
        s0.stack = 0
        s0.total_hand_bet = 200
        s0.status = SeatStatus.ALL_IN
        s1.stack = 0
        s1.total_hand_bet = 500
        s1.status = SeatStatus.ALL_IN
        s2.stack = 500
        s2.total_hand_bet = 500
        table.pot = 1200
        pots = BettingRound.calculate_side_pots(table)
        # Should create at least 2 pots: one for the 200 all-in, one for the 500 level
        assert len(pots) >= 2
        # Each pot should have eligible seats and a positive amount
        for pot in pots:
            assert pot["amount"] > 0
            assert len(pot["eligible_seats"]) > 0
        # Total should equal sum of all bets (200 + 500 + 500 = 1200)
        total = sum(p["amount"] for p in pots)
        assert total == 1200
