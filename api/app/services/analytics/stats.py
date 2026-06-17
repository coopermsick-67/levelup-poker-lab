"""Analytics stats computation for poker hand decisions."""

from __future__ import annotations

from typing import Any


def get_position_name(seat_index: int, button_index: int, total_players: int) -> str:
    """Map a seat index to a position name relative to the button.

    Positions for a 6-max table (in order after button):
      BTN, SB, BB, UTG, MP, CO
    For other sizes the same relative ordering is used, collapsing
    early positions into UTG as needed.
    """
    if total_players < 2:
        return "BTN"

    # Distance from the button, clockwise
    rel = (seat_index - button_index) % total_players

    # rel == 0 is always the button
    if rel == 0:
        return "BTN"

    # Standard 6-max mapping
    if total_players == 6:
        _map = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "MP", 5: "CO"}
        return _map[rel]

    # Full ring (9-max): BTN, SB,BB,UTG,UTG+1,MP,MP+1,CO,HJ
    if total_players >= 8:
        _map = {
            0: "BTN",
            1: "SB",
            2: "BB",
            3: "UTG",
            4: "UTG+1",
            5: "MP",
            6: "MP+1",
            7: "HJ",
            8: "CO",
        }
        if rel in _map:
            return _map[rel]
        return f"POS{rel}"

    # Heads-up
    if total_players == 2:
        return "BB"

    # 3-5 players: BTN, SB, BB, UTG, CO (collapse as needed)
    if total_players == 3:
        _map3 = {0: "BTN", 1: "SB", 2: "BB"}
        return _map3.get(rel, "UTG")
    if total_players == 4:
        _map4 = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG"}
        return _map4.get(rel, "UTG")
    if total_players == 5:
        _map5 = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "CO"}
        return _map5.get(rel, "UTG")

    # 7-player table (fallback)
    _map7 = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "MP", 5: "CO", 6: "HJ"}
    return _map7.get(rel, f"POS{rel}")


def compute_stats(decisions: list[Any]) -> dict[str, Any]:
    """Compute poker statistics from a list of HandDecision-like objects.

    Each decision object is expected to have at minimum:
      - street: str   (preflop, flop, turn, river)
      - position: str (UTG, MP, CO, BTN, SB, BB)
      - action_taken: str (fold, check, call, raise, all_in)
      - amount: int
      - pot_size: int
      - stack_size: int
      - hole_cards: str
      - community_cards: str
    """
    if not decisions:
        return _empty_stats()

    # --- Preflop stats ---
    preflop_decisions = [d for d in decisions if d.street == "preflop"]

    # VPIP: voluntarily put $ in pot (call or raise preflop, not counting blind posts)
    vpip_opportunities = 0
    vpip_actions = 0
    for d in preflop_decisions:
        # Count each street-level decision once per street per hand
        # We count a decision as VPIP if the player called or raised
        if d.action_taken in ("call", "raise", "all_in"):
            vpip_actions += 1
        # Every preflop decision is a VPIP opportunity
        vpip_opportunities += 1

    # Deduplicate: count one VPIP opportunity per hand (group by hand_id if available)
    vpip_hand_ids: set[int] = set()
    vpip_hands_voluntary: set[int] = set()
    for d in preflop_decisions:
        hand_id = getattr(d, "hand_id", id(d))
        vpip_hand_ids.add(hand_id)
        if d.action_taken in ("call", "raise", "all_in"):
            vpip_hands_voluntary.add(hand_id)

    total_hands = len(vpip_hand_ids) if vpip_hand_ids else 0
    vpip_count = len(vpip_hands_voluntary)
    vpip_pct = round(vpip_count / total_hands * 100, 1) if total_hands > 0 else 0.0

    # PFR: preflop raise
    pfr_hand_ids: set[int] = set()
    for d in preflop_decisions:
        hand_id = getattr(d, "hand_id", id(d))
        if d.action_taken in ("raise", "all_in"):
            pfr_hand_ids.add(hand_id)

    pfr_count = len(pfr_hand_ids)
    pfr_pct = round(pfr_count / total_hands * 100, 1) if total_hands > 0 else 0.0

    # --- 3-bet stats ---
    # A 3-bet is a raise preflop when there was already a raise
    # We detect this by looking for raises on streets after preflop raises
    # For simplicity, we count "all_in" for 3+ bets, and also track
    # raises that happen after an opponent raise (approximated by pot_size > 2*BB)
    three_bet_opportunities = 0
    three_bet_actions = 0
    for d in preflop_decisions:
        # If pot_size > 30 (assuming 5/10 blinds, a raise makes pot ~25-30),
        # there was likely a prior raise
        if d.pot_size > 30 and d.action_taken in ("raise", "all_in"):
            three_bet_actions += 1
        if d.pot_size > 30:
            three_bet_opportunities += 1

    three_bet_pct = (
        round(three_bet_actions / three_bet_opportunities * 100, 1)
        if three_bet_opportunities > 0
        else 0.0
    )

    # Fold-to-3-bet: when facing a 3-bet (pot already large), did we fold?
    fold_to_3bet_opportunities = 0
    fold_to_3bet_actions = 0
    for d in preflop_decisions:
        if d.pot_size > 60:  # facing a re-raise
            fold_to_3bet_opportunities += 1
            if d.action_taken == "fold":
                fold_to_3bet_actions += 1

    fold_to_3bet_pct = (
        round(fold_to_3bet_actions / fold_to_3bet_opportunities * 100, 1)
        if fold_to_3bet_opportunities > 0
        else 0.0
    )

    # --- Postflop stats ---
    postflop_decisions = [d for d in decisions if d.street in ("flop", "turn", "river")]

    # c-bet: bet on flop after raising preflop
    # Approximation: raise preflop + bet on flop
    # We use a simpler heuristic: on flop, if player bets/raises and was PFR
    cbet_opportunities = 0
    cbet_actions = 0
    flop_decisions = [d for d in decisions if d.street == "flop"]
    for d in flop_decisions:
        # c-bet opportunity: player was the PFR (approximated by having raised preflop)
        # For now, count all flop betting opportunities as c-bet opportunities
        # when the player has position (acting last)
        if d.action_taken in ("raise", "all_in"):
            cbet_actions += 1
        # Every flop decision where player could bet is an opportunity
        cbet_opportunities += 1

    cbet_pct = (
        round(cbet_actions / cbet_opportunities * 100, 1)
        if cbet_opportunities > 0
        else 0.0
    )

    # Fold-to-c-bet
    fold_to_cbet_opportunities = 0
    fold_to_cbet_actions = 0
    for d in flop_decisions:
        # Facing a c-bet means pot was bet into on flop
        if d.pot_size > 20 and d.action_taken in ("fold", "call", "raise"):
            fold_to_cbet_opportunities += 1
            if d.action_taken == "fold":
                fold_to_cbet_actions += 1

    fold_to_cbet_pct = (
        round(fold_to_cbet_actions / fold_to_cbet_opportunities * 100, 1)
        if fold_to_cbet_opportunities > 0
        else 0.0
    )

    # --- Aggression Factor ---
    # AF = (bets + raises) / calls across all streets
    bets_raises = sum(
        1 for d in decisions if d.action_taken in ("raise", "all_in")
    )
    calls = sum(1 for d in decisions if d.action_taken == "call")
    aggression_factor = round(bets_raises / calls, 2) if calls > 0 else float(bets_raises)

    # --- WWSF: Won When Saw Flop ---
    # Approximation: count hands where player saw flop and had positive result
    # We use hand_id grouping
    hands_saw_flop: set[int] = set()
    hands_won_saw_flop: set[int] = set()
    for d in decisions:
        hand_id = getattr(d, "hand_id", id(d))
        if d.street in ("flop", "turn", "river"):
            hands_saw_flop.add(hand_id)
            # If amount > 0 on later streets, likely won
            # Better: check if action_taken is not fold on flop
        if d.street == "flop" and d.action_taken != "fold":
            hands_saw_flop.add(hand_id)

    # For WWSF we need win data; use ev_diff or was_correct as proxy
    for d in decisions:
        hand_id = getattr(d, "hand_id", id(d))
        if hand_id in hands_saw_flop:
            ev = getattr(d, "ev_diff", None)
            if ev is not None and ev > 0:
                hands_won_saw_flop.add(hand_id)
            elif getattr(d, "was_correct", None) == 1:
                hands_won_saw_flop.add(hand_id)

    wwsf_pct = (
        round(len(hands_won_saw_flop) / len(hands_saw_flop) * 100, 1)
        if hands_saw_flop
        else 0.0
    )

    # --- Position-specific stats ---
    positions = ("UTG", "MP", "CO", "BTN", "SB", "BB")
    position_stats: dict[str, dict[str, float]] = {}
    for pos in positions:
        pos_decisions = [d for d in preflop_decisions if d.position == pos]
        pos_hand_ids: set[int] = set()
        pos_vpip_hands: set[int] = set()
        pos_pfr_hands: set[int] = set()
        for d in pos_decisions:
            hand_id = getattr(d, "hand_id", id(d))
            pos_hand_ids.add(hand_id)
            if d.action_taken in ("call", "raise", "all_in"):
                pos_vpip_hands.add(hand_id)
            if d.action_taken in ("raise", "all_in"):
                pos_pfr_hands.add(hand_id)

        pos_total = len(pos_hand_ids)
        position_stats[pos] = {
            "hands": pos_total,
            "vpip": round(len(pos_vpip_hands) / pos_total * 100, 1) if pos_total > 0 else 0.0,
            "pfr": round(len(pos_pfr_hands) / pos_total * 100, 1) if pos_total > 0 else 0.0,
        }

    return {
        "total_hands": total_hands,
        "total_decisions": len(decisions),
        "vpip": vpip_pct,
        "pfr": pfr_pct,
        "three_bet_pct": three_bet_pct,
        "fold_to_3bet_pct": fold_to_3bet_pct,
        "cbet_pct": cbet_pct,
        "fold_to_cbet_pct": fold_to_cbet_pct,
        "aggression_factor": aggression_factor,
        "wwsf_pct": wwsf_pct,
        "position_stats": position_stats,
    }


def _empty_stats() -> dict[str, Any]:
    """Return a zeroed-out stats dict."""
    positions = ("UTG", "MP", "CO", "BTN", "SB", "BB")
    return {
        "total_hands": 0,
        "total_decisions": 0,
        "vpip": 0.0,
        "pfr": 0.0,
        "three_bet_pct": 0.0,
        "fold_to_3bet_pct": 0.0,
        "cbet_pct": 0.0,
        "fold_to_cbet_pct": 0.0,
        "aggression_factor": 0.0,
        "wwsf_pct": 0.0,
        "position_stats": {
            pos: {"hands": 0, "vpip": 0.0, "pfr": 0.0} for pos in positions
        },
    }
