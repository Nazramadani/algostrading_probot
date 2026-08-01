# ==========================================================
# MARKET REGIME ENGINE v2.0
# Part 1
# ==========================================================

from .models import (
    MarketRegimeResult,
    MarketStructureResult
)


class MarketRegimeEngine:

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self):

        self.adx_trending = 25

        self.adx_strong = 35

        self.atr_expansion = 1.20

        self.atr_compression = 0.80

        self.volume_expansion = 1.30

        self.minimum_score = 60

    # ======================================================
    # ANALYZE
    # ======================================================

    def analyze(
        self,
        df,
        structure: MarketStructureResult
    ):

        result = MarketRegimeResult()

        # ------------------------------------------
        # Trend
        # ------------------------------------------

        self._detect_trend(
            df,
            structure,
            result
        )

        # ------------------------------------------
        # Volatility
        # ------------------------------------------

        self._detect_volatility(
            df,
            result
        )

        # ------------------------------------------
        # Expansion
        # ------------------------------------------

        self._detect_expansion(
            df,
            result
        )

        # ------------------------------------------
        # Compression
        # ------------------------------------------

        self._detect_compression(
            df,
            result
        )

        # ------------------------------------------
        # Range
        # ------------------------------------------

        self._detect_range(
            df,
            structure,
            result
        )

        # ------------------------------------------
        # Reversal
        # ------------------------------------------

        self._detect_reversal(
            structure,
            result
        )

        # ------------------------------------------
        # Trend Strength
        # ------------------------------------------

        self._trend_strength(
            df,
            structure,
            result
        )

        # ------------------------------------------
        # Score
        # ------------------------------------------

        self._score(
            result
        )

        # ------------------------------------------
        # Confidence
        # ------------------------------------------

        self._confidence(
            result
        )

        # ------------------------------------------
        # Tradable
        # ------------------------------------------

        self._tradable(
            result
        )

        return result