from __future__ import annotations
import random
from enum import Enum
from app.services.poker_engine.deck import Card, Rank
from app.services.poker_engine.table import Table, Seat, Street
from app.services.poker_engine.betting import Action, ActionType, BettingRound


class BotStyle(str, Enum):
    NIT = "nit"           # Tight-passive
    REG = "reg"           # TAG (tight-aggressive)
    MANIAC = "maniac"     # Loose-aggressive


# Preflop hand strength tiers (simplified)
PREMIUM_HANDS = {"AA", "KK", "QQ", "JJ", "AKs", "AKo"}
STRONG_HANDS = {"TT", "99", "AQs", "AQo", "AJs", "KQs", "KJs", "ATs"}
PLAYABLE_HANDS = {"88", "77", "66", "AJo", "ATo", "KQo", "KJo", "QJs", "JTs", "T9s", "98s", "A9s", "A8s"}
SPECULATIVE = {"55", "44", "33", "22", "KTo", "QTo", "JTo", "QTs", "J9s", "T8s", "97s", "87s", "76s", "65s", "54s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KTs", "Q9s"}


def _hand_key(cards: list[Card]) -> str:
    """Convert two hole cards to a key like 'AKs' or 'AKo'."""
    if len(cards) != 2:
        return ""
    r1, r2 = sorted([cards[0].rank, cards[1].rank], reverse=True)
    rank_chars = {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T"}
    rc1 = rank_chars.get(r1, str(r1))
    rc2 = rank_chars.get(r2, str(r2))
    if r1 == r2:
        return rc1 + rc2  # e.g. "AA"
    suited = "s" if cards[0].suit == cards[1].suit else "o"
    return rc1 + rc2 + suited


def _hand_strength(cards: list[Card]) -> float:
    """Rough preflop hand strength 0.0-1.0."""
    key = _hand_key(cards)
    if key in PREMIUM_HANDS:
        return 0.9 + random.uniform(0, 0.1)
    if key in STRONG_HANDS:
        return 0.7 + random.uniform(0, 0.15)
    if key in PLAYABLE_HANDS:
        return 0.5 + random.uniform(0, 0.15)
    if key in SPECULATIVE:
        return 0.3 + random.uniform(0, 0.15)
    # High card value fallback
    high = max(c.rank for c in cards)
    return min(0.3, high / 14.0 * 0.3)


def _board_texture(community: list[Card]) -> dict:
    """Simple board texture analysis."""
    if not community:
        return {"paired": False, "suited": False, "connected": False, "high_cards": 0}
    ranks = [c.rank for c in community]
    suits = [c.suit for c in community]
    paired = len(ranks) != len(set(ranks))
    suited = len(set(suits)) == 1 if len(suits) >= 2 else False
    sorted_r = sorted(set(ranks))
    connected = any(sorted_r[i + 1] - sorted_r[i] == 1 for i in range(len(sorted_r) - 1)) if len(sorted_r) >= 2 else False
    high = sum(1 for r in ranks if r >= 10)
    return {"paired": paired, "suited": suited, "connected": connected, "high_cards": high}


class BotAI:
    """Heuristic bot decision-making."""

    @staticmethod
    def decide(table: Table, seat: Seat) -> Action:
        style = BotStyle(seat.bot_style) if seat.bot_style else BotStyle.REG
        legal = BettingRound.get_legal_actions(table, seat)
        if not legal:
            return Action(ActionType.FOLD, seat.index)

        hole = seat.hole_cards
        community = table.community_cards
        street = table.current_street
        hand_str = _hand_strength(hole) if street == Street.PREFLOP else BotAI._postflop_strength(hole, community)
        board = _board_texture(community)
        pot_odds = BotAI._pot_odds(table, seat)
        rng = random.random()

        if style == BotStyle.NIT:
            return BotAI._nit_decision(table, seat, legal, hand_str, pot_odds, rng, board)
        elif style == BotStyle.MANIAC:
            return BotAI._maniac_decision(table, seat, legal, hand_str, pot_odds, rng, board)
        else:
            return BotAI._reg_decision(table, seat, legal, hand_str, pot_odds, rng, board)

    @staticmethod
    def _postflop_strength(hole: list[Card], community: list[Card]) -> float:
        """Very rough postflop hand strength."""
        from app.services.poker_engine.hand_evaluator import HandEvaluator, HandRank
        all_cards = hole + community
        if len(all_cards) < 5:
            # Flop: use preflop strength as base
            return _hand_strength(hole) * 0.7
        result = HandEvaluator.evaluate(all_cards)
        base = result.hand_rank.value / 9.0
        # Adjust for kicker strength
        kicker_bonus = sum(result.kickers[:3]) / (14 * 3) * 0.2
        return min(1.0, base + kicker_bonus)

    @staticmethod
    def _pot_odds(table: Table, seat: Seat) -> float:
        highest = max(s.current_bet for s in table.seats)
        to_call = highest - seat.current_bet
        if to_call == 0:
            return 0
        return to_call / (table.pot + to_call)

    @staticmethod
    def _nit_decision(table, seat, legal, hand_str, pot_odds, rng, board):
        highest = max(s.current_bet for s in table.seats)
        to_call = highest - seat.current_bet

        # Very tight: only play premium+ hands
        if hand_str >= 0.85:
            # Bet/raise with premium
            if ActionType.RAISE in legal:
                min_r, max_r = BettingRound.get_raise_bounds(table, seat)
                raise_to = min(min_r + (max_r - min_r) // 3, max_r)
                return Action(ActionType.RAISE, seat.index, raise_to)
            if ActionType.CALL in legal:
                return Action(ActionType.CALL, seat.index)
            return Action(ActionType.CHECK, seat.index)

        if hand_str >= 0.6:
            # Call with strong hands, rarely raise
            if to_call == 0:
                return Action(ActionType.CHECK, seat.index)
            if to_call <= table.big_blind * 2 and ActionType.CALL in legal:
                return Action(ActionType.CALL, seat.index)
            if ActionType.FOLD in legal:
                return Action(ActionType.FOLD, seat.index)
            return Action(ActionType.CHECK, seat.index)

        # Weak hand: usually fold
        if to_call == 0:
            return Action(ActionType.CHECK, seat.index)
        if ActionType.FOLD in legal:
            return Action(ActionType.FOLD, seat.index)
        return Action(ActionType.CHECK, seat.index)

    @staticmethod
    def _reg_decision(table, seat, legal, hand_str, pot_odds, rng, board):
        highest = max(s.current_bet for s in table.seats)
        to_call = highest - seat.current_bet

        if hand_str >= 0.7:
            if ActionType.RAISE in legal:
                min_r, max_r = BettingRound.get_raise_bounds(table, seat)
                if rng < 0.7:
                    raise_to = min(min_r + (max_r - min_r) // 2, max_r)
                else:
                    raise_to = min_r
                return Action(ActionType.RAISE, seat.index, raise_to)
            if ActionType.CALL in legal:
                return Action(ActionType.CALL, seat.index)
            return Action(ActionType.CHECK, seat.index)

        if hand_str >= 0.45:
            if to_call == 0:
                if rng < 0.3 and ActionType.RAISE in legal:
                    min_r, max_r = BettingRound.get_raise_bounds(table, seat)
                    return Action(ActionType.RAISE, seat.index, min_r)
                return Action(ActionType.CHECK, seat.index)
            if pot_odds < 0.3 and ActionType.CALL in legal:
                return Action(ActionType.CALL, seat.index)
            if ActionType.FOLD in legal:
                return Action(ActionType.FOLD, seat.index)
            return Action(ActionType.CHECK, seat.index)

        # Weak: occasional bluff
        if to_call == 0:
            if rng < 0.15 and ActionType.RAISE in legal:
                min_r, max_r = BettingRound.get_raise_bounds(table, seat)
                return Action(ActionType.RAISE, seat.index, min_r)
            return Action(ActionType.CHECK, seat.index)
        if pot_odds < 0.15 and ActionType.CALL in legal:
            return Action(ActionType.CALL, seat.index)
        if ActionType.FOLD in legal:
            return Action(ActionType.FOLD, seat.index)
        return Action(ActionType.CHECK, seat.index)

    @staticmethod
    def _maniac_decision(table, seat, legal, hand_str, pot_odds, rng, board):
        highest = max(s.current_bet for s in table.seats)
        to_call = highest - seat.current_bet

        # Maniac raises a lot
        if ActionType.RAISE in legal:
            min_r, max_r = BettingRound.get_raise_bounds(table, seat)
            if hand_str >= 0.5 or rng < 0.4:
                raise_to = min(min_r + int((max_r - min_r) * rng), max_r)
                return Action(ActionType.RAISE, seat.index, raise_to)

        if ActionType.CALL in legal:
            if hand_str >= 0.25 or rng < 0.5:
                return Action(ActionType.CALL, seat.index)

        if ActionType.CHECK in legal:
            return Action(ActionType.CHECK, seat.index)
        if ActionType.FOLD in legal:
            return Action(ActionType.FOLD, seat.index)
        return Action(ActionType.CHECK, seat.index)
