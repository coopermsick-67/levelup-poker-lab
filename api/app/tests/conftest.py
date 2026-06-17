import pytest
from app.services.poker_engine.deck import Card, Deck, Rank, Suit


@pytest.fixture
def deck():
    return Deck(seed=42)


@pytest.fixture
def sample_cards():
    return [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.JACK, Suit.SPADES),
        Card(Rank.TEN, Suit.SPADES),
    ]
