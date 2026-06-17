from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from app.services.poker_engine.deck import Card, Rank, Suit


class HandRank(IntEnum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

    def __str__(self) -> str:
        names = {
            0: "High Card", 1: "One Pair", 2: "Two Pair", 3: "Three of a Kind",
            4: "Straight", 5: "Flush", 6: "Full House", 7: "Four of a Kind",
            8: "Straight Flush", 9: "Royal Flush",
        }
        return names[self.value]


@dataclass(frozen=True, slots=True)
class HandResult:
    """Comparable hand evaluation result. Higher is better."""
    hand_rank: HandRank
    kickers: tuple[int, ...]  # Rank values for tiebreaking, sorted by importance

    def __gt__(self, other: HandResult) -> bool:
        if self.hand_rank != other.hand_rank:
            return self.hand_rank > other.hand_rank
        return self.kickers > other.kickers

    def __ge__(self, other: HandResult) -> bool:
        return self == other or self > other

    def __lt__(self, other: HandResult) -> bool:
        return other > self

    def __le__(self, other: HandResult) -> bool:
        return other >= self


class HandEvaluator:
    """Evaluates 5-7 card poker hands. Returns comparable HandResult."""

    @staticmethod
    def evaluate(cards: list[Card]) -> HandResult:
        """Best 5-card hand from 5-7 cards."""
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")
        if len(cards) == 5:
            return HandEvaluator._eval_five(cards)
        # For 6 or 7 cards, find the best 5-card combination
        from itertools import combinations
        best: HandResult | None = None
        for combo in combinations(cards, 5):
            result = HandEvaluator._eval_five(list(combo))
            if best is None or result > best:
                best = result
        return best

    @staticmethod
    def _eval_five(cards: list[Card]) -> HandResult:
        assert len(cards) == 5
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        is_flush = len(set(suits)) == 1

        # Check for straight (including wheel: A-2-3-4-5)
        unique_ranks = sorted(set(ranks), reverse=True)
        is_straight = False
        straight_high = 0
        if len(unique_ranks) == 5:
            if unique_ranks[0] - unique_ranks[4] == 4:
                is_straight = True
                straight_high = unique_ranks[0]
            # Wheel: A-2-3-4-5 → ranks are [14, 5, 4, 3, 2]
            elif unique_ranks == [14, 5, 4, 3, 2]:
                is_straight = True
                straight_high = 5  # 5-high straight

        # Count rank frequencies
        from collections import Counter
        rank_counts = Counter(ranks)
        # Sort by count desc, then rank desc
        count_rank = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

        # Royal flush
        if is_straight and is_flush and straight_high == 14:
            return HandResult(HandRank.ROYAL_FLUSH, (14,))
        # Straight flush
        if is_straight and is_flush:
            return HandResult(HandRank.STRAIGHT_FLUSH, (straight_high,))
        # Four of a kind
        if count_rank[0][1] == 4:
            return HandResult(HandRank.FOUR_OF_A_KIND, (count_rank[0][0], count_rank[1][0]))
        # Full house
        if count_rank[0][1] == 3 and count_rank[1][1] == 2:
            return HandResult(HandRank.FULL_HOUSE, (count_rank[0][0], count_rank[1][0]))
        # Flush
        if is_flush:
            return HandResult(HandRank.FLUSH, tuple(ranks))
        # Straight
        if is_straight:
            return HandResult(HandRank.STRAIGHT, (straight_high,))
        # Three of a kind
        if count_rank[0][1] == 3:
            kickers = tuple(r for r in ranks if r != count_rank[0][0])
            return HandResult(HandRank.THREE_OF_A_KIND, (count_rank[0][0],) + kickers[:2])
        # Two pair
        if count_rank[0][1] == 2 and count_rank[1][1] == 2:
            pairs = sorted([count_rank[0][0], count_rank[1][0]], reverse=True)
            kicker = count_rank[2][0]
            return HandResult(HandRank.TWO_PAIR, tuple(pairs) + (kicker,))
        # One pair
        if count_rank[0][1] == 2:
            pair_rank = count_rank[0][0]
            kickers = tuple(r for r in ranks if r != pair_rank)
            return HandResult(HandRank.ONE_PAIR, (pair_rank,) + kickers)
        # High card
        return HandResult(HandRank.HIGH_CARD, tuple(ranks))

    @staticmethod
    def compare_hands(hole1: list[Card], hole2: list[Card], community: list[Card]) -> int:
        """Returns 1 if hole1 wins, -1 if hole2 wins, 0 for tie."""
        result1 = HandEvaluator.evaluate(hole1 + community)
        result2 = HandEvaluator.evaluate(hole2 + community)
        if result1 > result2:
            return 1
        elif result2 > result1:
            return -1
        return 0
