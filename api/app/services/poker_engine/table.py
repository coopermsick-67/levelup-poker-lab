from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from app.services.poker_engine.deck import Card, Deck


class Street(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


class SeatStatus(Enum):
    EMPTY = "empty"
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    SITTING_OUT = "sitting_out"


@dataclass
class Seat:
    index: int
    player_id: int | None = None
    display_name: str = ""
    stack: int = 1000
    hole_cards: list[Card] = field(default_factory=list)
    status: SeatStatus = SeatStatus.EMPTY
    current_bet: int = 0  # Amount bet this street
    total_hand_bet: int = 0  # Total bet this hand
    is_hero: bool = False
    is_bot: bool = False
    bot_style: str | None = None

    def reset_for_hand(self) -> None:
        self.hole_cards = []
        self.current_bet = 0
        self.total_hand_bet = 0
        if self.status not in (SeatStatus.EMPTY, SeatStatus.SITTING_OUT):
            if self.stack > 0:
                self.status = SeatStatus.ACTIVE
            else:
                self.status = SeatStatus.SITTING_OUT

    def can_act(self) -> bool:
        return self.status == SeatStatus.ACTIVE and self.stack > 0

    def to_public_dict(self, reveal_cards: bool = False) -> dict:
        cards = [str(c) for c in self.hole_cards] if (reveal_cards or self.is_hero) else []
        return {
            "index": self.index,
            "display_name": self.display_name,
            "stack": self.stack,
            "status": self.status.value,
            "current_bet": self.current_bet,
            "total_hand_bet": self.total_hand_bet,
            "is_hero": self.is_hero,
            "is_bot": self.is_bot,
            "hole_cards": cards,
        }


@dataclass
class Table:
    table_id: str = ""
    seats: list[Seat] = field(default_factory=list)
    community_cards: list[Card] = field(default_factory=list)
    pot: int = 0
    side_pots: list[dict] = field(default_factory=list)
    button_index: int = 0
    small_blind: int = 5
    big_blind: int = 10
    current_street: Street = Street.PREFLOP
    active_seat_index: int = -1  # Whose turn it is
    hand_number: int = 0
    is_hand_in_progress: bool = False
    min_raise: int = 10
    _deck: Deck | None = field(default=None, repr=False)

    def __post_init__(self):
        if not self.seats:
            self.seats = [Seat(index=i) for i in range(6)]

    def get_active_seats(self) -> list[Seat]:
        return [s for s in self.seats if s.status in (SeatStatus.ACTIVE, SeatStatus.ALL_IN)]

    def get_acting_seats(self) -> list[Seat]:
        """Seats that can still make decisions this street."""
        return [s for s in self.seats if s.can_act()]

    def get_hero_seat(self) -> Seat | None:
        for s in self.seats:
            if s.is_hero:
                return s
        return None

    def to_dict(self, hero_id: int | None = None) -> dict:
        hero_seat = self.get_hero_seat()
        reveal = self.current_street == Street.SHOWDOWN
        return {
            "table_id": self.table_id,
            "seats": [s.to_public_dict(reveal_cards=reveal) for s in self.seats],
            "community_cards": [str(c) for c in self.community_cards],
            "pot": self.pot,
            "side_pots": self.side_pots,
            "button_index": self.button_index,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "current_street": self.current_street.value,
            "active_seat_index": self.active_seat_index,
            "hand_number": self.hand_number,
            "is_hand_in_progress": self.is_hand_in_progress,
            "min_raise": self.min_raise,
            "hero_seat_index": hero_seat.index if hero_seat else -1,
        }
