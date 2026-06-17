import pytest
from app.services.poker_engine.deck import Card, Rank, Suit
from app.services.poker_engine.hand_evaluator import HandEvaluator, HandRank


def make_cards(*strings):
    return [Card.from_str(s) for s in strings]


class TestHandEvaluator:
    def test_royal_flush(self):
        cards = make_cards("AS", "KS", "QS", "JS", "TS")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.ROYAL_FLUSH

    def test_straight_flush(self):
        cards = make_cards("9S", "8S", "7S", "6S", "5S")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.STRAIGHT_FLUSH
        assert result.kickers == (9,)

    def test_four_of_a_kind(self):
        cards = make_cards("AS", "AH", "AD", "AC", "KS")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.FOUR_OF_A_KIND

    def test_full_house(self):
        cards = make_cards("AS", "AH", "AD", "KS", "KH")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.FULL_HOUSE

    def test_flush(self):
        cards = make_cards("AS", "KS", "9S", "7S", "3S")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.FLUSH

    def test_straight(self):
        cards = make_cards("9S", "8H", "7D", "6C", "5S")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.STRAIGHT
        assert result.kickers == (9,)

    def test_wheel_straight(self):
        cards = make_cards("AS", "2H", "3D", "4C", "5S")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.STRAIGHT
        assert result.kickers == (5,)

    def test_three_of_a_kind(self):
        cards = make_cards("AS", "AH", "AD", "KS", "QC")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.THREE_OF_A_KIND

    def test_two_pair(self):
        cards = make_cards("AS", "AH", "KS", "KH", "QC")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.TWO_PAIR

    def test_one_pair(self):
        cards = make_cards("AS", "AH", "KS", "QC", "JD")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.ONE_PAIR

    def test_high_card(self):
        cards = make_cards("AS", "KH", "QD", "JC", "9S")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.HIGH_CARD

    def test_seven_card_best_hand(self):
        cards = make_cards("AS", "KS", "QS", "JS", "TS", "2H", "3D")
        result = HandEvaluator.evaluate(cards)
        assert result.hand_rank == HandRank.ROYAL_FLUSH

    def test_compare_hands(self):
        hole1 = make_cards("AS", "KS")
        hole2 = make_cards("QD", "JC")
        community = make_cards("TS", "7H", "3D", "2S", "4C")
        result = HandEvaluator.compare_hands(hole1, hole2, community)
        assert result == 1  # AK wins with pair of Aces... wait, no pair. A high vs Q high.
        # Actually AK has A-K-T-7-4, QJ has Q-J-T-7-4. AK wins.

    def test_compare_tie(self):
        # Both players have the same straight on board — true tie
        hole1 = make_cards("AS", "KH")
        hole2 = make_cards("AD", "KC")
        community = make_cards("QS", "JS", "TS", "3D", "2C")
        result = HandEvaluator.compare_hands(hole1, hole2, community)
        assert result == 0  # Both have the same straight A-K-Q-J-T

    def test_flush_beats_straight(self):
        cards_flush = make_cards("2S", "4S", "6S", "8S", "TS")
        cards_straight = make_cards("9H", "8D", "7C", "6S", "5H")
        r1 = HandEvaluator.evaluate(cards_flush)
        r2 = HandEvaluator.evaluate(cards_straight)
        assert r1 > r2
