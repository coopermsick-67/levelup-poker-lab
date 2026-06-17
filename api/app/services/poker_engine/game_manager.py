from __future__ import annotations
import uuid
from app.services.poker_engine.deck import Deck, Card
from app.services.poker_engine.table import Table, Seat, Street, SeatStatus
from app.services.poker_engine.betting import Action, ActionType, BettingRound
from app.services.poker_engine.hand_evaluator import HandEvaluator
from app.services.poker_engine.bot_ai import BotAI, BotStyle


class GameManager:
    """Manages the full lifecycle of a poker hand."""

    def __init__(self):
        self.tables: dict[str, Table] = {}

    def create_table(self, hero_id: int, hero_name: str, bot_styles: list[str] | None = None) -> Table:
        table_id = str(uuid.uuid4())[:8]
        table = Table(table_id=table_id)

        if bot_styles is None:
            bot_styles = ["nit", "reg", "maniac", "reg", "nit"]

        # Seat 0 = Hero
        table.seats[0].player_id = hero_id
        table.seats[0].display_name = hero_name
        table.seats[0].is_hero = True
        table.seats[0].stack = 1000
        table.seats[0].status = SeatStatus.ACTIVE

        bot_names = ["NitBot", "RegBot", "ManiacBot", "TAGBot", "FishBot"]
        for i in range(1, 6):
            style = bot_styles[i - 1] if i - 1 < len(bot_styles) else "reg"
            table.seats[i].player_id = -(i + 1)  # Negative IDs for bots
            table.seats[i].display_name = bot_names[i - 1] if i - 1 < len(bot_names) else f"Bot{i}"
            table.seats[i].is_bot = True
            table.seats[i].bot_style = style
            table.seats[i].stack = 1000
            table.seats[i].status = SeatStatus.ACTIVE

        self.tables[table_id] = table
        return table

    def start_hand(self, table_id: str) -> Table:
        table = self.tables[table_id]
        deck = Deck()

        # Reset table state
        table.community_cards = []
        table.pot = 0
        table.side_pots = []
        table.current_street = Street.PREFLOP
        table.hand_number += 1
        table.is_hand_in_progress = True
        table.min_raise = table.big_blind

        # Reset seats
        for s in table.seats:
            s.reset_for_hand()

        # Move button
        active_indices = [i for i, s in enumerate(table.seats) if s.status == SeatStatus.ACTIVE]
        if table.hand_number == 1:
            table.button_index = active_indices[0]
        else:
            current_idx = active_indices.index(table.button_index) if table.button_index in active_indices else -1
            next_idx = (current_idx + 1) % len(active_indices)
            table.button_index = active_indices[next_idx]

        # Deal cards
        deck.shuffle()
        table._deck = deck
        for s in table.seats:
            if s.status == SeatStatus.ACTIVE:
                s.hole_cards = deck.deal(2)

        # Post blinds
        self._post_blinds(table, deck)

        # Set first to act
        self._set_next_actor(table)
        return table

    def _post_blinds(self, table: Table, deck: Deck | None = None) -> None:
        active = [i for i, s in enumerate(table.seats) if s.status == SeatStatus.ACTIVE]
        n = len(active)
        if n < 2:
            return

        btn_pos = active.index(table.button_index) if table.button_index in active else 0
        sb_idx = active[(btn_pos + 1) % n]
        bb_idx = active[(btn_pos + 2) % n]

        sb_seat = table.seats[sb_idx]
        bb_seat = table.seats[bb_idx]

        sb_amount = min(table.small_blind, sb_seat.stack)
        BettingRound.apply_action(table, sb_seat, Action(ActionType.POST_BLIND, sb_idx, sb_amount))

        bb_amount = min(table.big_blind, bb_seat.stack)
        BettingRound.apply_action(table, bb_seat, Action(ActionType.POST_BLIND, bb_idx, bb_amount))

    def _set_next_actor(self, table: Table) -> None:
        acting = table.get_acting_seats()
        if len(acting) <= 1:
            table.active_seat_index = -1
            return

        # Find next actor after current
        active_indices = sorted([s.index for s in acting])
        if table.active_seat_index < 0:
            # First to act this street
            if table.current_street == Street.PREFLOP:
                n = len(active_indices)
                if n == 2:
                    # Heads-up: button is SB, acts first preflop
                    first = table.button_index
                else:
                    # UTG = n-2 seats after button (0-indexed from button)
                    btn_idx = table.button_index
                    ordered = sorted([(i - btn_idx) % 6 for i in active_indices])
                    utg_offset = ordered[2] if len(ordered) > 2 else ordered[0]
                    first = (btn_idx + utg_offset) % 6
                table.active_seat_index = first
            else:
                # First active seat after button
                after_btn = [i for i in active_indices if i > table.button_index]
                table.active_seat_index = after_btn[0] if after_btn else active_indices[0]
        else:
            # Find next after current
            after_current = [i for i in active_indices if i > table.active_seat_index]
            if after_current:
                table.active_seat_index = after_current[0]
            else:
                table.active_seat_index = -1  # Round complete

    def apply_hero_action(self, table_id: str, hero_id: int, action_type: str, amount: int | None = None) -> dict:
        """Apply hero action, then run bot actions until hero's turn or hand ends."""
        table = self.tables[table_id]
        hero = table.get_hero_seat()
        if not hero or hero.player_id != hero_id:
            return {"error": "Not your table", "table": table.to_dict(hero_id)}

        if table.active_seat_index != hero.index:
            return {"error": "Not your turn", "table": table.to_dict(hero_id)}

        # Build action
        at = ActionType(action_type)
        if at == ActionType.RAISE and amount is not None:
            min_total, max_total = BettingRound.get_raise_bounds(table, hero)
            clamped = max(min_total, min(amount, max_total))
            action = Action(at, hero.index, clamped)
        else:
            action = Action(at, hero.index)

        BettingRound.apply_action(table, hero, action)

        # Check if hand is over
        result = self._check_hand_end(table, hero_id)
        if result:
            return result

        # Advance to next actor or run bots
        self._set_next_actor(table)
        return self._run_bots(table, hero_id)

    def _run_bots(self, table: Table, hero_id: int) -> dict:
        """Run bot actions until it's hero's turn or hand ends."""
        max_iterations = 20  # Safety limit
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            seat = table.seats[table.active_seat_index] if 0 <= table.active_seat_index < 6 else None

            if seat is None or not seat.can_act():
                # Betting round complete
                if not self._advance_street(table):
                    return self._finalize_hand(table, hero_id)
                self._set_next_actor(table)
                continue

            if seat.is_hero:
                return {"table": table.to_dict(hero_id), "waiting_for_hero": True}

            if seat.is_bot:
                action = BotAI.decide(table, seat)
                BettingRound.apply_action(table, seat, action)
                result = self._check_hand_end(table, hero_id)
                if result:
                    return result
                self._set_next_actor(table)
                continue

            break

        return {"table": table.to_dict(hero_id), "waiting_for_hero": table.seats[table.active_seat_index].is_hero if 0 <= table.active_seat_index < 6 else False}

    def _check_hand_end(self, table: Table, hero_id: int) -> dict | None:
        """Check if only one player remains (everyone else folded)."""
        non_folded = [s for s in table.seats if s.status != SeatStatus.FOLDED and s.status != SeatStatus.EMPTY and s.status != SeatStatus.SITTING_OUT]
        if len(non_folded) == 1:
            # Single player wins the pot
            winner = non_folded[0]
            winner.stack += table.pot
            table.pot = 0
            table.is_hand_in_progress = False
            return {
                "table": table.to_dict(hero_id),
                "hand_complete": True,
                "winner": {"seat_index": winner.index, "display_name": winner.display_name, "reason": "all_others_folded"},
            }
        return None

    def _advance_street(self, table: Table) -> bool:
        """Advance to next street. Returns False if hand is over."""
        # Reset current bets for new street
        for s in table.seats:
            s.current_bet = 0
        table.min_raise = table.big_blind

        deck = table._deck
        if deck is None:
            return False

        if table.current_street == Street.PREFLOP:
            # Burn + flop (3 cards)
            deck.deal(1)  # burn
            table.community_cards.extend(deck.deal(3))
            table.current_street = Street.FLOP
            return True
        elif table.current_street == Street.FLOP:
            deck.deal(1)  # burn
            table.community_cards.extend(deck.deal(1))
            table.current_street = Street.TURN
            return True
        elif table.current_street == Street.TURN:
            deck.deal(1)  # burn
            table.community_cards.extend(deck.deal(1))
            table.current_street = Street.RIVER
            return True
        elif table.current_street == Street.RIVER:
            table.current_street = Street.SHOWDOWN
            return False
        return False

    def _finalize_hand(self, table: Table, hero_id: int) -> dict:
        """Showdown: evaluate hands and award pots."""
        table.current_street = Street.SHOWDOWN
        table.is_hand_in_progress = False

        active = [s for s in table.seats if s.status != SeatStatus.FOLDED and s.status != SeatStatus.EMPTY and s.status != SeatStatus.SITTING_OUT]
        side_pots = BettingRound.calculate_side_pots(table)
        table.side_pots = side_pots

        winners_info = []
        for pot in side_pots:
            pot_amount = pot["amount"]
            eligible = [table.seats[i] for i in pot["eligible_seats"] if table.seats[i].status != SeatStatus.FOLDED]
            if not eligible:
                continue

            # Find winner(s) of this pot
            best_seat = eligible[0]
            best_result = HandEvaluator.evaluate(best_seat.hole_cards + table.community_cards) if len(table.community_cards) >= 3 else None
            pot_winners = [best_seat]

            for s in eligible[1:]:
                if len(table.community_cards) < 3:
                    continue
                result = HandEvaluator.evaluate(s.hole_cards + table.community_cards)
                if best_result is None or result > best_result:
                    best_result = result
                    best_seat = s
                    pot_winners = [s]
                elif result == best_result:
                    pot_winners.append(s)

            # Split pot among winners
            share = pot_amount // len(pot_winners)
            remainder = pot_amount % len(pot_winners)
            for i, w in enumerate(pot_winners):
                w.stack += share + (1 if i < remainder else 0)

            table.pot -= pot_amount

            winners_info.append({
                "pot_amount": pot_amount,
                "winners": [{"seat_index": w.index, "display_name": w.display_name} for w in pot_winners],
                "winning_hand": str(best_result) if best_result else "N/A",
            })

        # Distribute any remaining pot (shouldn't happen, but safety)
        if table.pot > 0:
            if active:
                share = table.pot // len(active)
                for s in active:
                    s.stack += share
            table.pot = 0

        return {
            "table": table.to_dict(hero_id),
            "hand_complete": True,
            "showdown": True,
            "pot_results": winners_info,
        }

    def get_legal_actions(self, table_id: str, hero_id: int) -> list[str]:
        table = self.tables[table_id]
        hero = table.get_hero_seat()
        if not hero:
            return []
        return [a.value for a in BettingRound.get_legal_actions(table, hero)]


# Shared singleton instance used across the app
game_manager = GameManager()
