from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from app.services.poker_engine.table import Table, Seat, Street, SeatStatus


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"
    POST_BLIND = "post_blind"


@dataclass
class Action:
    action_type: ActionType
    seat_index: int
    amount: int = 0  # Total chips the player has put in after this action


class BettingRound:
    """Manages a single betting round within a hand."""

    @staticmethod
    def get_legal_actions(table: Table, seat: Seat) -> list[ActionType]:
        if not seat.can_act():
            return []
        highest_bet = max(s.current_bet for s in table.seats)
        to_call = highest_bet - seat.current_bet

        if to_call == 0:
            actions = [ActionType.CHECK, ActionType.RAISE]
        else:
            actions = [ActionType.FOLD, ActionType.CALL, ActionType.RAISE]

        # All-in is always an option if player can act
        actions.append(ActionType.ALL_IN)
        return actions

    @staticmethod
    def get_raise_bounds(table: Table, seat: Seat) -> tuple[int, int]:
        """Returns (min_raise_total, max_raise_total) — total chips after raise."""
        highest_bet = max(s.current_bet for s in table.seats)
        to_call = highest_bet - seat.current_bet
        min_raise = max(table.min_raise, table.big_blind)
        min_total = highest_bet + min_raise
        max_total = seat.stack + seat.current_bet
        if min_total > max_total:
            min_total = max_total  # All-in is the minimum
        return min_total, max_total

    @staticmethod
    def apply_action(table: Table, seat: Seat, action: Action) -> int:
        """
        Apply an action to the table. Returns the amount of chips added to the pot.
        """
        chips_added = 0
        highest_bet = max(s.current_bet for s in table.seats)
        to_call = highest_bet - seat.current_bet

        if action.action_type == ActionType.FOLD:
            seat.status = SeatStatus.FOLDED
            return 0

        elif action.action_type == ActionType.CHECK:
            return 0

        elif action.action_type == ActionType.CALL:
            call_amount = min(to_call, seat.stack)
            seat.stack -= call_amount
            seat.current_bet += call_amount
            seat.total_hand_bet += call_amount
            chips_added = call_amount
            if seat.stack == 0:
                seat.status = SeatStatus.ALL_IN

        elif action.action_type == ActionType.RAISE:
            raise_total = action.amount  # Total chips after raise
            chips_needed = raise_total - seat.current_bet
            actual_chips = min(chips_needed, seat.stack)
            seat.stack -= actual_chips
            seat.current_bet += actual_chips
            seat.total_hand_bet += actual_chips
            chips_added = actual_chips
            table.min_raise = max(table.min_raise, seat.current_bet - highest_bet)
            if seat.stack == 0:
                seat.status = SeatStatus.ALL_IN

        elif action.action_type == ActionType.ALL_IN:
            chips_added = seat.stack
            seat.current_bet += seat.stack
            seat.total_hand_bet += seat.stack
            seat.stack = 0
            seat.status = SeatStatus.ALL_IN

        elif action.action_type == ActionType.POST_BLIND:
            seat.stack -= action.amount
            seat.current_bet = action.amount
            seat.total_hand_bet = action.amount
            chips_added = action.amount
            if seat.stack == 0:
                seat.status = SeatStatus.ALL_IN

        table.pot += chips_added
        return chips_added

    @staticmethod
    def is_betting_round_complete(table: Table) -> bool:
        """Check if the current betting round is over."""
        acting = [s for s in table.seats if s.can_act()]
        if len(acting) <= 1:
            # Only one or zero players can act — check if they've matched
            if len(acting) == 0:
                return True
            highest = max(s.current_bet for s in table.seats)
            return acting[0].current_bet == highest

        # All acting players must have matched the highest bet
        highest = max(s.current_bet for s in table.seats)
        for s in acting:
            if s.current_bet != highest:
                return False
        return True

    @staticmethod
    def calculate_side_pots(table: Table) -> list[dict]:
        """Calculate side pots when players are all-in."""
        # Collect all-in amounts
        all_in_amounts: list[tuple[int, int]] = []  # (total_hand_bet, seat_index)
        for s in table.seats:
            if s.status == SeatStatus.ALL_IN and s.total_hand_bet > 0:
                all_in_amounts.append((s.total_hand_bet, s.index))

        if not all_in_amounts:
            return [{"amount": table.pot, "eligible_seats": [s.index for s in table.seats if s.status != SeatStatus.FOLDED]}]

        all_in_amounts.sort()
        side_pots = []
        prev_cap = 0
        for cap, _ in all_in_amounts:
            if cap > prev_cap:
                pot_amount = 0
                eligible = []
                for s in table.seats:
                    contribution = min(s.total_hand_bet, cap) - min(s.total_hand_bet, prev_cap)
                    if contribution > 0:
                        pot_amount += contribution
                    if s.total_hand_bet > prev_cap and s.status != SeatStatus.FOLDED:
                        eligible.append(s.index)
                if pot_amount > 0:
                    side_pots.append({"amount": pot_amount, "eligible_seats": eligible})
                prev_cap = cap

        # Main pot: any money from players who bet more than the highest all-in cap
        max_all_in = prev_cap
        remaining = sum(max(0, s.total_hand_bet - max_all_in) for s in table.seats)
        if remaining > 0:
            eligible = [s.index for s in table.seats if s.total_hand_bet > max_all_in and s.status != SeatStatus.FOLDED]
            side_pots.append({"amount": remaining, "eligible_seats": eligible})

        return side_pots if side_pots else [{"amount": table.pot, "eligible_seats": [s.index for s in table.seats if s.status != SeatStatus.FOLDED]}]
