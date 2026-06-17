from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import IntEnum


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    def __str__(self) -> str:
        return ["♣", "♦", "♥", "♠"][self.value]

    @staticmethod
    def from_str(s: str) -> Suit:
        return {"C": Suit.CLUBS, "D": Suit.DIAMONDS, "H": Suit.HEARTS, "S": Suit.SPADES}[s.upper()]


class Rank(IntEnum):
    TWO = 2; THREE = 3; FOUR = 4; FIVE = 5; SIX = 6; SEVEN = 7; EIGHT = 8
    NINE = 9; TEN = 10; JACK = 11; QUEEN = 12; KING = 13; ACE = 14

    def __str__(self) -> str:
        if self.value <= 10:
            return str(self.value)
        return {11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]

    @staticmethod
    def from_str(s: str) -> Rank:
        return {
            "2": Rank.TWO, "3": Rank.THREE, "4": Rank.FOUR, "5": Rank.FIVE,
            "6": Rank.SIX, "7": Rank.SEVEN, "8": Rank.EIGHT, "9": Rank.NINE,
            "10": Rank.TEN, "T": Rank.TEN, "J": Rank.JACK, "Q": Rank.QUEEN,
            "K": Rank.KING, "A": Rank.ACE,
        }[s.upper()]


@dataclass(frozen=True, slots=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def from_str(s: str) -> Card:
        """Parse 'Ah' or 'AS' format."""
        rank_part = s[:-1]
        suit_part = s[-1]
        suit_map = {"♣": "C", "♦": "D", "♥": "H", "♠": "S", "C": "C", "D": "D", "H": "H", "S": "S"}
        return Card(Rank.from_str(rank_part), Suit.from_str(suit_map[suit_part.upper()]))

    @property
    def value(self) -> int:
        """Unique integer 0-51 for hashing/comparison."""
        return self.suit * 13 + (self.rank - 2)


class Deck:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self._cards: list[Card] = []
        self.reset()

    def reset(self) -> None:
        self._cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self) -> None:
        self._rng.shuffle(self._cards)

    def deal(self, n: int = 1) -> list[Card]:
        if n > len(self._cards):
            raise ValueError(f"Cannot deal {n} cards from {len(self._cards)} remaining")
        dealt = self._cards[:n]
        self._cards = self._cards[n:]
        return dealt

    @property
    def remaining(self) -> int:
        return len(self._cards)
