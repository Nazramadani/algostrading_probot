# ==========================================================
# SMC ENTRY VALIDATOR v2.0
# ==========================================================

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class EntryValidationResult:

    allowed: bool = False

    score: float = 0.0

    reasons: List[str] = field(default_factory=list)


# ==========================================================
# ENGINE
# ==========================================================

class EntryValidator:

    def __init__(

        self,

        max_fvg_distance=0.30,

        max_ob_distance=0.30,

        minimum_score=70

    ):

        self.max_fvg_distance = max_fvg_distance

        self.max_ob_distance = max_ob_distance

        self.minimum_score = minimum_score

    # ======================================================
    # MAIN
    # ======================================================

    def validate(

        self,

        side,

        current_price,

        structure,

        liquidity,

        fvg,

        order_blocks

    ):

        result = EntryValidationResult()

        score = 0

        # ==========================================
        # Structure
        # ==========================================

        if structure.breaks:

            last = structure.breaks[-1]

            if side == "BUY":

                if last.direction == "bullish":

                    score += 20

                    result.reasons.append(

                        "Bullish BOS"

                    )

            else:

                if last.direction == "bearish":

                    score += 20

                    result.reasons.append(

                        "Bearish BOS"

                    )

        # ==========================================
        # FVG
        # ==========================================

        nearest = getattr(

            fvg,

            "nearest",

            None

        )

        if nearest:

            if nearest.direction.lower() == side.lower():

                if nearest.distance <= self.max_fvg_distance:

                    score += 25

                    result.reasons.append(

                        "Near FVG"

                    )

                else:

                    result.reasons.append(

                        "Far from FVG"

                    )

        # ==========================================
        # ORDER BLOCK
        # ==========================================

        nearest_ob = None

        if side == "BUY":

            nearest_ob = getattr(

                order_blocks,

                "nearest_bullish",

                None

            )

        else:

            nearest_ob = getattr(

                order_blocks,

                "nearest_bearish",

                None

            )

        if nearest_ob:

            distance = abs(

                current_price -

                nearest_ob.high

            )

            if distance <= self.max_ob_distance:

                score += 25

                result.reasons.append(

                    "Near Order Block"

                )

        # ==========================================
        # Liquidity
        # ==========================================

        if side == "BUY":

            if liquidity.sell_side:

                score += 15

                result.reasons.append(

                    "Sell Liquidity Available"

                )

        else:

            if liquidity.buy_side:

                score += 15

                result.reasons.append(

                    "Buy Liquidity Available"

                )

        # ==========================================
        # Premium Discount
        # ==========================================

        if side == "BUY":

            if structure.in_discount:

                score += 15

                result.reasons.append(

                    "Discount Zone"

                )

        else:

            if structure.in_premium:

                score += 15

                result.reasons.append(

                    "Premium Zone"

                )

        result.score = score

        result.allowed = (

            score >= self.minimum_score

        )

        return result