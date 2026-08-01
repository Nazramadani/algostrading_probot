# ==========================================================
# SMC CONFIDENCE ENGINE v2.0
# ==========================================================

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# WEIGHTED SCORE
# ==========================================================

@dataclass
class WeightedScore:

    structure: float = 0.0

    liquidity: float = 0.0

    fvg: float = 0.0

    trend: float = 0.0

    mtf: float = 0.0

    confluence: float = 0.0

    risk_penalty: float = 0.0

    def total(self):

        return (

            self.structure +

            self.liquidity +

            self.fvg +

            self.trend +

            self.mtf +

            self.confluence -

            self.risk_penalty

        )


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class ConfidenceResult:

    side: str = "NONE"

    confidence: float = 0.0

    bull_score: float = 0.0

    bear_score: float = 0.0

    normalized_bull: float = 0.0

    normalized_bear: float = 0.0

    reasons: List[str] = field(default_factory=list)


# ==========================================================
# ENGINE
# ==========================================================

class ConfidenceEngine:

    def __init__(

        self,

        maximum_score=100

    ):

        self.maximum_score = maximum_score

    # ======================================================
    # MAIN
    # ======================================================

    def analyze(

        self,

        bull: WeightedScore,

        bear: WeightedScore,

        reasons=None

    ):

        if reasons is None:

            reasons = []

        bull_total = bull.total()

        bear_total = bear.total()

        bull_total = max(0.0, bull_total)

        bear_total = max(0.0, bear_total)

        bull_norm = self.normalize(

            bull_total

        )

        bear_norm = self.normalize(

            bear_total

        )

        result = ConfidenceResult()

        result.bull_score = round(

            bull_total,

            2

        )

        result.bear_score = round(

            bear_total,

            2

        )

        result.normalized_bull = round(

            bull_norm,

            2

        )

        result.normalized_bear = round(

            bear_norm,

            2

        )

        if bull_norm > bear_norm:

            result.side = "BUY"

            result.confidence = bull_norm

        elif bear_norm > bull_norm:

            result.side = "SELL"

            result.confidence = bear_norm

        else:

            result.side = "NONE"

            result.confidence = bull_norm

        result.reasons = reasons

        return result

    # ======================================================
    # NORMALIZER
    # ======================================================

    def normalize(

        self,

        value

    ):

        value = max(

            0,

            min(

                value,

                self.maximum_score

            )

        )

        return round(

            value,

            2

        )

    # ======================================================
    # HELPERS
    # ======================================================

    def empty_score(self):

        return WeightedScore()

    def add_structure(

        self,

        score,

        value

    ):

        score.structure += value

    def add_liquidity(

        self,

        score,

        value

    ):

        score.liquidity += value

    def add_fvg(

        self,

        score,

        value

    ):

        score.fvg += value

    def add_trend(

        self,

        score,

        value

    ):

        score.trend += value

    def add_mtf(

        self,

        score,

        value

    ):

        score.mtf += value

    def add_confluence(

        self,

        score,

        value

    ):

        score.confluence += value

    def add_penalty(

        self,

        score,

        value

    ):

        score.risk_penalty += value