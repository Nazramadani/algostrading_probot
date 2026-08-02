# ==========================================================
# MULTI TIMEFRAME ENGINE v2.0
# NazRmd ProBot
# ==========================================================

from dataclasses import dataclass, field
from typing import Optional, List
import pandas as pd
from .market_structure import MarketStructureEngine

# ==========================================================
# TIMEFRAME STATE & ANALYSIS
# ==========================================================
@dataclass
class TimeframeAnalysis:
    timeframe: str
    trend: str = "NEUTRAL"
    structure: str = "NONE"
    confidence: float = 0.0
    bos: bool = False
    choch: bool = False
    structure_score: float = 0.0
    last_bos: bool = False
    last_choch: bool = False
    bullish_ob: bool = False
    bearish_ob: bool = False
    bullish_fvg: bool = False
    bearish_fvg: bool = False

    def to_dict(self):
        return {
            "timeframe": self.timeframe,
            "trend": self.trend,
            "structure": self.structure,
            "confidence": self.confidence,
            "bos": self.bos,
            "choch": self.choch,
            "structure_score": self.structure_score,
            "last_bos": self.last_bos,
            "last_choch": self.last_choch,
            "bullish_ob": self.bullish_ob,
            "bearish_ob": self.bearish_ob,
            "bullish_fvg": self.bullish_fvg,
            "bearish_fvg": self.bearish_fvg
        }

# Alias për përputhshmëri
TimeframeState = TimeframeAnalysis

# ==========================================================
# MULTI TIMEFRAME RESULT V2
# ==========================================================
@dataclass
class MultiTimeframeResult:
    tf4h: TimeframeAnalysis = field(default_factory=lambda: TimeframeAnalysis("4H"))
    tf1h: TimeframeAnalysis = field(default_factory=lambda: TimeframeAnalysis("1H"))
    tf15m: TimeframeAnalysis = field(default_factory=lambda: TimeframeAnalysis("15M"))
    tf5m: TimeframeAnalysis = field(default_factory=lambda: TimeframeAnalysis("5M"))
    aligned: bool = False
    alignment: bool = False
    overall_bias: str = "neutral"
    bias: str = "neutral"
    dominant_trend: str = "NEUTRAL"
    confidence: float = 0.0
    score: float = 0.0
    bullish_score: float = 0.0
    bearish_score: float = 0.0
    trade_allowed: bool = False
    entry_tf: str = "5M"
    execution_tf: str = "5M"
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "tf4h": self.tf4h.to_dict(),
            "tf1h": self.tf1h.to_dict(),
            "tf15m": self.tf15m.to_dict(),
            "tf5m": self.tf5m.to_dict(),
            "aligned": self.aligned,
            "overall_bias": self.overall_bias,
            "bias": self.bias,
            "confidence": self.confidence,
            "score": self.score,
            "trade_allowed": self.trade_allowed,
            "entry_tf": self.entry_tf,
            "execution_tf": self.execution_tf,
            "reasons": self.reasons
        }

# ==========================================================
# ENGINE
# ==========================================================
class MultiTimeframeEngine:
    def __init__(self):
        self.market = MarketStructureEngine()
        self.result = MultiTimeframeResult()
        self.weights = {
            "4H": 35,
            "1H": 30,
            "15M": 20,
            "5M": 15
        }
        self.minimum_score = 70
        self.minimum_confidence = 70

    # ======================================================
    # MAIN ANALYZE
    # ======================================================
    def analyze(self, df_4h: pd.DataFrame, df_1h: pd.DataFrame, df_15m: pd.DataFrame, df_5m: pd.DataFrame) -> MultiTimeframeResult:
        result = MultiTimeframeResult()
        self.result = result

        result.tf4h = self.analyze_timeframe(df_4h, "4H")
        result.tf1h = self.analyze_timeframe(df_1h, "1H")
        result.tf15m = self.analyze_timeframe(df_15m, "15M")
        result.tf5m = self.analyze_timeframe(df_5m, "5M")

        result.alignment = self.check_alignment(result)
        result.dominant_trend = self.calculate_trend(result)
        result.confidence = self.calculate_confidence(result)
        result.score = result.confidence
        result.bias = result.dominant_trend
        result.trade_allowed = self.trade_allowed(result)
        result.reasons = []

        # Ekzekutimi i vlerësimeve dhe analizave shtesë
        self._calculate_alignment()
        self._calculate_bias()
        self._calculate_score()
        self._validate_trade()

        return result

    # ======================================================
    # ANALYZE SINGLE TIMEFRAME
    # ======================================================
    def analyze_timeframe(self, df, timeframe):
        state = TimeframeAnalysis(timeframe=timeframe)

        if len(df) < 100:
            return state

        market = self.market.analyze(df)
        state.confidence = 50.0

        if len(market.breaks) > 0:
            last_break = market.breaks[-1]
            state.structure = last_break.kind

            if last_break.kind == "BOS":
                state.bos = True
                state.last_bos = True
            if last_break.kind == "CHOCH":
                state.choch = True
                state.last_choch = True

            state.trend = last_break.direction.upper()
        else:
            if len(market.swings) >= 2:
                last = market.swings[-1]
                prev = market.swings[-2]

                if last.kind == "HIGH" and last.price > prev.price:
                    state.trend = "BULLISH"
                elif last.kind == "LOW" and last.price < prev.price:
                    state.trend = "BEARISH"
                else:
                    state.trend = "NEUTRAL"

        # Confidence
        confidence = 0
        if state.trend != "NEUTRAL":
            confidence += 40
        if state.bos:
            confidence += 30
        if state.choch:
            confidence += 20
        if len(market.swings) >= 6:
            confidence += 10

        state.confidence = min(confidence, 100)
        return state

    # ======================================================
    # GET TREND
    # ======================================================
    def get_trend(self, state):
        return state.trend

    # ======================================================
    # IS BULLISH
    # ======================================================
    def bullish(self, state):
        return state.trend == "BULLISH"

    # ======================================================
    # IS BEARISH
    # ======================================================
    def bearish(self, state):
        return state.trend == "BEARISH"

    # ======================================================
    # CHECK ALIGNMENT
    # ======================================================
    def check_alignment(self, result):
        trends = [
            result.tf4h.trend,
            result.tf1h.trend,
            result.tf15m.trend,
            result.tf5m.trend
        ]

        bullish = trends.count("BULLISH")
        bearish = trends.count("BEARISH")

        if bullish >= 3 or bearish >= 3:
            return True

        return False

    # ======================================================
    # DOMINANT TREND
    # ======================================================
    def calculate_trend(self, result):
        trends = [
            result.tf4h.trend,
            result.tf1h.trend,
            result.tf15m.trend,
            result.tf5m.trend
        ]

        bullish = trends.count("BULLISH")
        bearish = trends.count("BEARISH")

        if bullish > bearish:
            return "BULLISH"
        if bearish > bullish:
            return "BEARISH"

        return "NEUTRAL"

    # ======================================================
    # CONFIDENCE SCORE
    # ======================================================
    def calculate_confidence(self, result):
        score = 0
        weights = {
            "4H": 35,
            "1H": 30,
            "15M": 20,
            "5M": 15
        }

        timeframes = [result.tf4h, result.tf1h, result.tf15m, result.tf5m]
        dominant = self.calculate_trend(result)

        for tf in timeframes:
            if tf.trend == dominant:
                score += weights[tf.timeframe]
            if tf.bos:
                score += 5
            if tf.choch:
                score += 3

        return min(score, 100)

    # ======================================================
    # TRADE ALLOWED
    # ======================================================
    def trade_allowed(self, result):
        if not result.alignment:
            return False
        if result.confidence < 70:
            return False
        if result.dominant_trend == "NEUTRAL":
            return False
        return True

    # ======================================================
    # SUMMARY
    # ======================================================
    def summary(self, result):
        return {
            "alignment": result.alignment,
            "trend": result.dominant_trend,
            "confidence": result.confidence,
            "trade_allowed": self.trade_allowed(result),
            "4H": {
                "trend": result.tf4h.trend,
                "bos": result.tf4h.bos,
                "choch": result.tf4h.choch,
                "confidence": result.tf4h.confidence
            },
            "1H": {
                "trend": result.tf1h.trend,
                "bos": result.tf1h.bos,
                "choch": result.tf1h.choch,
                "confidence": result.tf1h.confidence
            },
            "15M": {
                "trend": result.tf15m.trend,
                "bos": result.tf15m.bos,
                "choch": result.tf15m.choch,
                "confidence": result.tf15m.confidence
            },
            "5M": {
                "trend": result.tf5m.trend,
                "bos": result.tf5m.bos,
                "choch": result.tf5m.choch,
                "confidence": result.tf5m.confidence
            }
        }

    # ======================================================
    # PRINT
    # ======================================================
    def print_summary(self, result):
        data = self.summary(result)

        print("\n==========================================")
        print("MULTI TIMEFRAME ANALYSIS")
        print("==========================================")
        print(f"Dominant Trend : {data['trend']}")
        print(f"Alignment      : {data['alignment']}")
        print(f"Confidence     : {data['confidence']}%")
        print(f"Trade Allowed  : {data['trade_allowed']}")
        print("------------------------------------------")

        for tf in ["4H", "1H", "15M", "5M"]:
            info = data[tf]
            print(
                f"{tf} | "
                f"{info['trend']} | "
                f"BOS={info['bos']} | "
                f"CHOCH={info['choch']} | "
                f"{info['confidence']}%"
            )
        print("==========================================")

    # ==========================================================
    # ALIGNMENT INTERNAL
    # ==========================================================
    def _calculate_alignment(self):
        trends = [
            self.result.tf4h.trend.lower(),
            self.result.tf1h.trend.lower(),
            self.result.tf15m.trend.lower(),
            self.result.tf5m.trend.lower()
        ]

        bullish = trends.count("bullish")
        bearish = trends.count("bearish")
        neutral = trends.count("neutral")

        self.result.aligned = False

        # ------------------------------------------
        # Perfect Bullish Alignment
        # ------------------------------------------
        if bullish == 4:
            self.result.aligned = True
            self.result.reasons.append("Perfect Bullish Alignment")
            return

        # ------------------------------------------
        # Perfect Bearish Alignment
        # ------------------------------------------
        if bearish == 4:
            self.result.aligned = True
            self.result.reasons.append("Perfect Bearish Alignment")
            return

        # ------------------------------------------
        # Strong Bullish Alignment
        # ------------------------------------------
        if bullish >= 3 and bearish == 0:
            self.result.aligned = True
            self.result.reasons.append("Strong Bullish Alignment")
            return

        # ------------------------------------------
        # Strong Bearish Alignment
        # ------------------------------------------
        if bearish >= 3 and bullish == 0:
            self.result.aligned = True
            self.result.reasons.append("Strong Bearish Alignment")
            return

        # ------------------------------------------
        # Mixed Market
        # ------------------------------------------
        self.result.aligned = False
        self.result.reasons.append("Mixed Timeframe Structure")

    # ==========================================================
    # BIAS INTERNAL
    # ==========================================================
    def _calculate_bias(self):
        bullish_score = 0
        bearish_score = 0

        frames = {
            "4H": self.result.tf4h,
            "1H": self.result.tf1h,
            "15M": self.result.tf15m,
            "5M": self.result.tf5m
        }

        for tf_name, tf in frames.items():
            weight = self.weights[tf_name]

            if tf.trend.lower() == "bullish":
                bullish_score += weight
            elif tf.trend.lower() == "bearish":
                bearish_score += weight

        if bullish_score > bearish_score:
            self.result.bias = "bullish"
        elif bearish_score > bullish_score:
            self.result.bias = "bearish"
        else:
            self.result.bias = "neutral"

        self.result.overall_bias = self.result.bias
        self.result.bullish_score = bullish_score
        self.result.bearish_score = bearish_score

    # ==========================================================
    # SCORE ENGINE
    # ==========================================================
    def _calculate_score(self):
        score = 0

        frames = {
            "4H": self.result.tf4h,
            "1H": self.result.tf1h,
            "15M": self.result.tf15m,
            "5M": self.result.tf5m
        }

        # ------------------------------------------
        # Trend Score
        # ------------------------------------------
        for tf_name, tf in frames.items():
            weight = self.weights[tf_name]
            if tf.trend.lower() == self.result.bias.lower():
                score += weight

        # ------------------------------------------
        # Structure Score
        # ------------------------------------------
        for tf in frames.values():
            score += tf.structure_score * 0.20

        # ------------------------------------------
        # Alignment Bonus
        # ------------------------------------------
        if self.result.aligned:
            score += 20

        # ------------------------------------------
        # Clamp
        # ------------------------------------------
        score = min(score, 100)
        self.result.score = round(score, 2)

    # ==========================================================
    # VALIDATE TRADE
    # ==========================================================
    def _validate_trade(self):
        self.result.trade_allowed = False

        if not self.result.aligned:
            self.result.reasons.append("Timeframe Alignment Failed")
            return

        if self.result.score < self.minimum_score:
            self.result.reasons.append("Score Too Low")
            return

        if self.result.confidence < self.minimum_confidence:
            self.result.reasons.append("Confidence Too Low")
            return

        self.result.trade_allowed = True
        self.result.reasons.append("Trade Approved")

    # ==========================================================
    # STRUCTURE SCORE
    # ==========================================================
    def _score_market_structure(self):
        score = 0
        frames = [
            self.result.tf4h,
            self.result.tf1h,
            self.result.tf15m,
            self.result.tf5m
        ]

        for tf in frames:
            score += tf.structure_score * 0.15

        return min(score, 15)

    # ==========================================================
    # BOS SCORE
    # ==========================================================
    def _score_bos(self):
        score = 0
        frames = [
            self.result.tf4h,
            self.result.tf1h,
            self.result.tf15m,
            self.result.tf5m
        ]

        for tf in frames:
            if tf.last_bos:
                score += 2.5

        return min(score, 10)

    # ==========================================================
    # CHOCH SCORE
    # ==========================================================
    def _score_choch(self):
        score = 0
        frames = [
            self.result.tf4h,
            self.result.tf1h,
            self.result.tf15m,
            self.result.tf5m
        ]

        for tf in frames:
            if tf.last_choch:
                score += 2.5

        return min(score, 10)

    # ==========================================================
    # ORDER BLOCK SCORE
    # ==========================================================
    def _score_order_blocks(self):
        score = 0
        frames = [
            self.result.tf4h,
            self.result.tf1h,
            self.result.tf15m,
            self.result.tf5m
        ]

        for tf in frames:
            if self.result.bias == "bullish":
                if tf.bullish_ob:
                    score += 2.5
            elif self.result.bias == "bearish":
                if tf.bearish_ob:
                    score += 2.5

        return min(score, 10)

    # ==========================================================
    # FVG SCORE
    # ==========================================================
    def _score_fvg(self):
        score = 0
        frames = [
            self.result.tf4h,
            self.result.tf1h,
            self.result.tf15m,
            self.result.tf5m
        ]

        for tf in frames:
            if self.result.bias == "bullish":
                if tf.bullish_fvg:
                    score += 2.5
            elif self.result.bias == "bearish":
                if tf.bearish_fvg:
                    score += 2.5

        return min(score, 10)
