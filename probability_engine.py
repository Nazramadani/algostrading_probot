# ==========================================================
# SMC PROBABILITY ENGINE v2.0
# ==========================================================

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class ProbabilityResult:

    probability: float = 0.0

    confidence: float = 0.0

    score: float = 0.0

    trade_quality: str = "LOW"

    reasons: List[str] = field(default_factory=list)


# ==========================================================
# ENGINE
# ==========================================================

class ProbabilityEngine:

    def __init__(self):

        self.structure_weight = 0.25

        self.liquidity_weight = 0.20

        self.fvg_weight = 0.15

        self.trend_weight = 0.15

        self.mtf_weight = 0.15

        self.entry_weight = 0.10

    # ======================================================
    # MAIN
    # ======================================================

    def analyze(

        self,

        structure_score,

        liquidity_score,

        fvg_score,

        trend_score,

        mtf_score,

        entry_score,

        confidence

    ):

        result = ProbabilityResult()

        score = (

            structure_score * self.structure_weight +

            liquidity_score * self.liquidity_weight +

            fvg_score * self.fvg_weight +

            trend_score * self.trend_weight +

            mtf_score * self.mtf_weight +

            entry_score * self.entry_weight

        )

        probability = (

            score * 0.70 +

            confidence * 0.30

        )

        probability = max(

            0,

            min(

                probability,

                100

            )

        )

        result.score = round(score,2)

        result.confidence = round(confidence,2)

        result.probability = round(probability,2)

        result.trade_quality = self.trade_quality(

            probability

        )

        result.reasons = self.generate_reason(

            probability

        )

        return result

    # ======================================================
    # QUALITY
    # ======================================================

    def trade_quality(

        self,

        probability

    ):

        if probability >= 90:

            return "A+"

        if probability >= 85:

            return "A"

        if probability >= 80:

            return "B+"

        if probability >= 75:

            return "B"

        if probability >= 70:

            return "C"

        return "NO TRADE"

    # ======================================================
    # REASONS
    # ======================================================

    def generate_reason(

        self,

        probability

    ):

        reasons = []

        if probability >= 90:

            reasons.append(

                "Institutional Grade Setup"

            )

        elif probability >= 85:

            reasons.append(

                "Excellent Confluence"

            )

        elif probability >= 80:

            reasons.append(

                "High Probability Setup"

            )

        elif probability >= 75:

            reasons.append(

                "Good Setup"

            )

        elif probability >= 70:

            reasons.append(

                "Acceptable Setup"

            )

        else:

            reasons.append(

                "Weak Setup"

            )

        return reasons