"""Leak detection for poker analytics."""

from __future__ import annotations

from typing import Any


def find_leaks(stats: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze computed stats and return a list of detected leaks.

    Each leak is a dict with:
      - description: str  (plain English)
      - severity: str     ("minor", "moderate", "major")
      - category: str     ("preflop", "postflop", "positional")
    """
    leaks: list[dict[str, Any]] = []

    if not stats or stats.get("total_hands", 0) == 0:
        return [{
            "description": "Not enough data to analyze. Play more hands to detect leaks.",
            "severity": "minor",
            "category": "preflop",
        }]

    vpip = stats.get("vpip", 0.0)
    pfr = stats.get("pfr", 0.0)
    three_bet = stats.get("three_bet_pct", 0.0)
    fold_to_3bet = stats.get("fold_to_3bet_pct", 0.0)
    cbet = stats.get("cbet_pct", 0.0)
    fold_to_cbet = stats.get("fold_to_cbet_pct", 0.0)
    af = stats.get("aggression_factor", 0.0)
    wwsf = stats.get("wwsf_pct", 0.0)
    pos_stats = stats.get("position_stats", {})

    # --- Preflop leaks ---

    # VPIP too low (tight-passive)
    if vpip < 15:
        leaks.append({
            "description": (
                f"Your VPIP of {vpip}% is very tight. You're folding too many hands "
                "preflop and missing profitable opportunities. Consider widening your "
                "range, especially in late position."
            ),
            "severity": "moderate",
            "category": "preflop",
        })
    elif vpip < 18:
        leaks.append({
            "description": (
                f"Your VPIP of {vpip}% is on the tighter side. While discipline is good, "
                "you may be leaving money on the table. Try adding more suited connectors "
                "and broadway hands from late position."
            ),
            "severity": "minor",
            "category": "preflop",
        })

    # VPIP too high (loose)
    if vpip > 35:
        leaks.append({
            "description": (
                f"Your VPIP of {vpip}% is very loose. You're playing too many hands, "
                "which leads to difficult postflop situations. Tighten up, especially "
                "from early position."
            ),
            "severity": "major",
            "category": "preflop",
        })
    elif vpip > 28:
        leaks.append({
            "description": (
                f"Your VPIP of {vpip}% is on the loose side. Consider folding more "
                "marginal hands, particularly weak aces and suited kings from early position."
            ),
            "severity": "moderate",
            "category": "preflop",
        })

    # PFR much lower than VPIP (passive preflop)
    vpip_pfr_gap = vpip - pfr
    if vpip_pfr_gap > 15:
        leaks.append({
            "description": (
                f"Your PFR ({pfr}%) is much lower than your VPIP ({vpip}%). You're "
                "calling too much instead of raising preflop. Raising gives you initiative "
                "and allows you to win pots without the best hand."
            ),
            "severity": "major",
            "category": "preflop",
        })
    elif vpip_pfr_gap > 10:
        leaks.append({
            "description": (
                f"Your PFR ({pfr}%) is significantly lower than your VPIP ({vpip}%). "
                "Try raising more of your strong hands preflop instead of limping along."
            ),
            "severity": "moderate",
            "category": "preflop",
        })

    # PFR higher than VPIP (unusual, might indicate data issue)
    if pfr > vpip and vpip > 0:
        leaks.append({
            "description": (
                "Your PFR is higher than your VPIP, which is unusual. This may indicate "
                "a data tracking issue, or you may be raising almost every hand you play."
            ),
            "severity": "minor",
            "category": "preflop",
        })

    # 3-bet too low
    if three_bet < 3 and stats.get("total_hands", 0) >= 20:
        leaks.append({
            "description": (
                f"Your 3-bet percentage of {three_bet}% is very low. You're missing "
                "opponents' opens to re-steal. Consider 3-betting more with both value "
                "hands and bluffs, especially from the blinds."
            ),
            "severity": "moderate",
            "category": "preflop",
        })

    # 3-bet too high
    if three_bet > 12:
        leaks.append({
            "description": (
                f"Your 3-bet percentage of {three_bet}% is very high. You may be "
                "3-betting too wide, which can lead to playing large pots with marginal "
                "hands. Consider narrowing your 3-betting range."
            ),
            "severity": "moderate",
            "category": "preflop",
        })

    # Fold to 3-bet too high
    if fold_to_3bet > 70:
        leaks.append({
            "description": (
                f"You fold to 3-bets {fold_to_3bet}% of the time. This is too high — "
                "opponents can exploit you by 3-betting wide. Consider calling or 4-betting "
                "more often."
            ),
            "severity": "moderate",
            "category": "preflop",
        })

    # Fold to 3-bet too low
    if fold_to_3bet < 40 and stats.get("total_hands", 0) >= 20:
        leaks.append({
            "description": (
                f"You only fold to 3-bets {fold_to_3bet}% of the time. You may be "
                "calling too wide out of position, leading to tough postflop spots."
            ),
            "severity": "minor",
            "category": "preflop",
        })

    # --- Postflop leaks ---

    # c-bet too low
    if cbet < 40 and stats.get("total_hands", 0) >= 20:
        leaks.append({
            "description": (
                f"Your c-bet percentage of {cbet}% is low. As the preflop aggressor, "
                "you should be c-betting more often to capitalize on your range advantage."
            ),
            "severity": "moderate",
            "category": "postflop",
        })

    # c-bet too high
    if cbet > 80:
        leaks.append({
            "description": (
                f"Your c-bet percentage of {cbet}% is very high. You may be auto-c-betting "
                "too often. Consider checking back on dry boards or when you have a weak "
                "range."
            ),
            "severity": "moderate",
            "category": "postflop",
        })

    # Fold to c-bet too high
    if fold_to_cbet > 65:
        leaks.append({
            "description": (
                f"You fold to c-bets {fold_to_cbet}% of the time. Opponents can exploit "
                "this by c-betting too frequently against you. Consider check-raising or "
                "calling wider on favorable boards."
            ),
            "severity": "moderate",
            "category": "postflop",
        })

    # Aggression Factor too low
    if af < 1.0 and stats.get("total_decisions", 0) >= 10:
        leaks.append({
            "description": (
                f"Your aggression factor of {af} is low. You're playing too passively — "
                "calling instead of betting/raises. Try being more aggressive, especially "
                "when you have strong hands or good draws."
            ),
            "severity": "moderate",
            "category": "postflop",
        })

    # Aggression Factor too high
    if af > 5.0:
        leaks.append({
            "description": (
                f"Your aggression factor of {af} is very high. While aggression is good, "
                "you may be betting and raising too much. Consider pot-controlling with "
                "medium-strength hands."
            ),
            "severity": "minor",
            "category": "postflop",
        })

    # WWSF too low
    if wwsf < 35 and stats.get("total_hands", 0) >= 20:
        leaks.append({
            "description": (
                f"Your WWSF of {wwsf}% is low. When you see a flop, you're not winning "
                "enough. This could mean you're seeing too many flops with weak hands, "
                "or not playing aggressively enough postflop."
            ),
            "severity": "moderate",
            "category": "postflop",
        })

    # WWSF too high
    if wwsf > 55:
        leaks.append({
            "description": (
                f"Your WWSF of {wwsf}% is very high. While this looks good, it might "
                "mean you're only seeing flops with very strong hands. Make sure you're "
                "not being too predictable."
            ),
            "severity": "minor",
            "category": "postflop",
        })

    # --- Positional leaks ---
    for pos, pdata in pos_stats.items():
        pos_vpip = pdata.get("vpip", 0.0)
        pos_pfr = pdata.get("pfr", 0.0)
        pos_hands = pdata.get("hands", 0)

        if pos_hands < 5:
            continue  # Not enough data

        # Position-specific VPIP checks
        if pos in ("UTG",) and pos_vpip > 20:
            leaks.append({
                "description": (
                    f"Your VPIP from {pos} is {pos_vpip}%, which is too high for early "
                    "position. Stick to premium hands like AA-QQ, AKs, and AKo."
                ),
                "severity": "moderate",
                "category": "positional",
            })

        if pos == "BTN" and pos_vpip < 30:
            leaks.append({
                "description": (
                    f"Your VPIP from the button is only {pos_vpip}%. The button is the "
                    "most profitable position — you should be opening a wide range here "
                    "(40%+ VPIP)."
                ),
                "severity": "moderate",
                "category": "positional",
            })

        if pos == "CO" and pos_vpip < 25:
            leaks.append({
                "description": (
                    f"Your VPIP from the cutoff is only {pos_vpip}%. The cutoff is the "
                    "second-best position. Try opening 30%+ of hands here."
                ),
                "severity": "minor",
                "category": "positional",
            })

        if pos == "SB" and pos_vpip > 35:
            leaks.append({
                "description": (
                    f"Your VPIP from the small blind is {pos_vpip}%, which is too high. "
                    "You'll be out of position for the rest of the hand, so be selective."
                ),
                "severity": "moderate",
                "category": "positional",
            })

        # Positional PFR vs VPIP gap
        pos_gap = pos_vpip - pos_pfr
        if pos_gap > 20 and pos_hands >= 10:
            leaks.append({
                "description": (
                    f"From {pos}, your VPIP ({pos_vpip}%) is much higher than your PFR "
                    f"({pos_pfr}%). You're limping too much — raise or fold instead."
                ),
                "severity": "moderate",
                "category": "positional",
            })

    # If no leaks detected, give positive feedback
    if not leaks:
        leaks.append({
            "description": (
                "No major leaks detected! Your stats look solid. Keep playing and "
                "review again after more hands to get a complete picture."
            ),
            "severity": "minor",
            "category": "preflop",
        })

    return leaks
