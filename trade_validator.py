# ==========================================================
# SMC TRADE VALIDATOR v2.0
# ==========================================================

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class TradeValidationResult:

    allowed: bool = False

    side: str = ""

    confidence: float = 0.0

    reasons: List[str] = field(default_factory=list)


# ==========================================================
# ENGINE
# ==========================================================

class TradeValidator:

    def __init__(

        self,

        minimum_confidence=80,

        minimum_rr=2.0

    ):

        self.minimum_confidence = minimum_confidence

        self.minimum_rr = minimum_rr

    # ======================================================
    # MAIN
    # ======================================================

    def validate(

        self,

        confidence,

        risk,

        structure,

        liquidity,

        fvg,

        mtf

    ):

        result = TradeValidationResult()

        result.side = confidence.side

        result.confidence = confidence.confidence

        # ---------------------------------------------
        # Confidence
        # ---------------------------------------------

        if confidence.confidence < self.minimum_confidence:

            result.reasons.append(

                "Low confidence"

            )

            return result

        # ---------------------------------------------
        # Risk Filter
        # ---------------------------------------------

        if not risk.passed:

            result.reasons.extend(

                risk.reasons

            )

            return result

        # ---------------------------------------------
        # RR
        # ---------------------------------------------

        if risk.rr < self.minimum_rr:

            result.reasons.append(

                "Low Risk Reward"

            )

            return result

        # ---------------------------------------------
        # Trend
        # ---------------------------------------------

        if structure.bias == "neutral":

            result.reasons.append(

                "Neutral Trend"

            )

            return result

        # ---------------------------------------------
        # MTF
        # ---------------------------------------------

        if not mtf.aligned:

            result.reasons.append(

                "MTF Conflict"

            )

            return result

        # ---------------------------------------------
        # Liquidity
        # ---------------------------------------------

        if result.side == "BUY":

            if len(liquidity.sell_side) == 0:

                result.reasons.append(

                    "No Sell Liquidity"

                )

                return result

        if result.side == "SELL":

            if len(liquidity.buy_side) == 0:

                result.reasons.append(

                    "No Buy Liquidity"

                )

                return result

        # ---------------------------------------------
        # FVG
        # ---------------------------------------------

        if result.side == "BUY":

            if len(fvg.bullish) == 0:

                result.reasons.append(

                    "No Bullish FVG"

                )

                return result

        if result.side == "SELL":

            if len(fvg.bearish) == 0:

                result.reasons.append(

                    "No Bearish FVG"

                )

                return result

        result.allowed = True

        result.reasons.append(

            "Trade Validated"

        )

        return result