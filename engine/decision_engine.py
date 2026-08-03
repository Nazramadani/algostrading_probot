# ==========================================================
# SMC DECISION ENGINE v2.0
# ==========================================================

from dataclasses import dataclass
from typing import List

from .market_structure_engine import MarketStructureEngine
from .liquidity_engine import LiquidityEngine
from .fvg_engine import FVGEngine
from .multi_timeframe_engine import MultiTimeframeEngine
from .risk_filter import RiskFilterEngine

from .models import (
    TradeSignal,
    DecisionResult,
    MarketStructureResult,
    LiquidityResult,
    FVGResult,
    MultiTimeframeResult
)

class DecisionEngine:
    def __init__(
        self,
        structure_engine=None,
        liquidity_engine=None,
        fvg_engine=None,
        mtf_engine=None,
        risk_filter=None
    ):
        # Inicializimi i motorëve
        self.structure_engine = structure_engine if structure_engine else MarketStructureEngine()
        self.liquidity_engine = liquidity_engine if liquidity_engine else LiquidityEngine()
        self.fvg_engine = fvg_engine if fvg_engine else FVGEngine()
        self.mtf_engine = mtf_engine if mtf_engine else MultiTimeframeEngine()
        self.risk_filter = risk_filter if risk_filter else RiskFilterEngine()

        # Peshat e vlerësimit
        self.structure_weight = 30
        self.liquidity_weight = 20
        self.fvg_weight = 15
        self.trend_weight = 15
        self.mtf_weight = 20

        # Pragjet minimale dhe parametrat e tjerë
        self.minimum_score = 70
        self.minimum_confidence = 75  # Rregulluar nga 70 në 75 sipas logjikës tënde më poshtë
        self.minimum_rr = 2.0
        self.buy_threshold = 75
        self.sell_threshold = 75

    # ==========================================================
    # TIME DECAY
    # ==========================================================
    def time_decay(self, level, current_index):
        age = current_index - level.index
        if age <= 30:
            return 1.0
        if age <= 80:
            return 0.75
        if age <= 150:
            return 0.50
        return 0.25

    # ==========================================================
    # TRADE SIDE
    # ==========================================================
    def _trade_side(self, trend):
        if trend == "bullish":
            return "BUY"
        if trend == "bearish":
            return "SELL"
        return ""

    # ==========================================================
    # MAIN ANALYZE METHOD
    # ==========================================================
    def analyze(
        self,
        structure: MarketStructureResult,
        liquidity: LiquidityResult,
        fvg: FVGResult,
        mtf: MultiTimeframeResult,
        trend_score: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ):
        result = DecisionResult()
        
        bull_score = 0.0
        bear_score = 0.0
        reasons = []

        # Pjesa e Structure Score
        bull_structure, bear_structure, structure_reasons = self.structure_score(structure)
        bull_score += bull_structure * (self.structure_weight / 100)
        bear_score += bear_structure * (self.structure_weight / 100)
        reasons.extend(structure_reasons)

        # Pjesa e Liquidity Score
        bull_liq, bear_liq, liq_reasons = self.liquidity_score(liquidity)
        bull_score += bull_liq * (self.liquidity_weight / 100)
        bear_score += bear_liq * (self.liquidity_weight / 100)
        reasons.extend(liq_reasons)

        # Pjesa e FVG Score
        bull_fvg, bear_fvg, fvg_reasons = self.fvg_score(fvg)
        bull_score += bull_fvg * (self.fvg_weight / 100)
        bear_score += bear_fvg * (self.fvg_weight / 100)
        reasons.extend(fvg_reasons)

        # Pjesa e Trend Score
        bull_trend, bear_trend, trend_reasons = self.trend_score(structure, mtf)
        bull_score += bull_trend * (self.trend_weight / 100)
        bear_score += bear_trend * (self.trend_weight / 100)
        reasons.extend(trend_reasons)

        # Bonuset dhe Penalitetet
        bonus = self.confluence_bonus(structure, liquidity, fvg, mtf)
        penalty = self.confidence_penalty(structure, mtf)

        bull_score += bonus
        bear_score += bonus

        bull_score -= penalty
        bear_score -= penalty

        bull_score = max(0, bull_score)
        bear_score = max(0, bear_score)

        # Kalkulimi Përfundimtar i Besimit (Confidence)
        conf_dict = self.confidence_score(bull_score, bear_score, reasons)

        if conf_dict["confidence"] >= self.minimum_confidence:
            result.allowed = True
        else:
            result.allowed = False

        result.confidence = conf_dict["confidence"]
        result.side = conf_dict["side"]
        result.reasons = conf_dict["reasons"]
        result.score = max(conf_dict["bull_score"], conf_dict["bear_score"])
        result.entry_price = entry_price
        result.stop_loss = stop_loss
        result.take_profit = take_profit

        return result

    # ==========================================================
    # STRUCTURE SCORE
    # ==========================================================
    def structure_score(self, structure: MarketStructureResult):
        bull = 0.0
        bear = 0.0
        reasons = []

        if structure.bias == "bullish":
            bull += 20
            reasons.append("Bullish Market Structure")
        elif structure.bias == "bearish":
            bear += 20
            reasons.append("Bearish Market Structure")

        bull += structure.bullish_score * 0.30
        bear += structure.bearish_score * 0.30

        if structure.breaks:
            last = structure.breaks[-1]
            if last.kind == "BOS":
                if last.direction == "bullish":
                    bull += 20
                    reasons.append("Bullish BOS")
                else:
                    bear += 20
                    reasons.append("Bearish BOS")
            elif last.kind == "CHOCH":
                if last.direction == "bullish":
                    bull += 25
                    reasons.append("Bullish CHOCH")
                else:
                    bear += 25
                    reasons.append("Bearish CHOCH")

        if structure.trend.direction == "bullish":
            bull += 10
        elif structure.trend.direction == "bearish":
            bear += 10

        bull = min(bull, 100)
        bear = min(bear, 100)

        return bull, bear, reasons

    # ==========================================================
    # LIQUIDITY SCORE
    # ==========================================================
    def liquidity_score(self, liquidity: LiquidityResult):
        bull = 0.0
        bear = 0.0
        reasons = []

        bull_void, bear_void, void_reasons = self.liquidity_void_score(liquidity)
        bull += bull_void
        bear += bear_void
        reasons.extend(void_reasons)

        bull_ie, bear_ie, _ = self.structure_liquidity_score(liquidity)
        bull += bull_ie
        bear += bear_ie

        buy_sweeps = [x for x in liquidity.sweeps if x.kind == "BUY_SIDE_SWEEP"]
        if buy_sweeps:
            bear += min(len(buy_sweeps) * 15, 30)
            reasons.append(f"Buy Side Swept ({len(buy_sweeps)})")

        sell_sweeps = [x for x in liquidity.sweeps if x.kind == "SELL_SIDE_SWEEP"]
        if sell_sweeps:
            bull += min(len(sell_sweeps) * 15, 30)
            reasons.append(f"Sell Side Swept ({len(sell_sweeps)})")

        active_buy = [x for x in liquidity.buy_side if x.active]
        if active_buy:
            bear += min(len(active_buy) * 3, 15)

        active_sell = [x for x in liquidity.sell_side if x.active]
        if active_sell:
            bull += min(len(active_sell) * 3, 15)

        if liquidity.equal_highs:
            bear += min(len(liquidity.equal_highs) * 2, 10)

        if liquidity.equal_lows:
            bull += min(len(liquidity.equal_lows) * 2, 10)

        strongest_buy = getattr(liquidity, "strongest_buy", None)
        if strongest_buy:
            score = strongest_buy.strength * 10
            bear += self.liquidity_time_decay(score, strongest_buy, liquidity.current_index)

        strongest_sell = getattr(liquidity, "strongest_sell", None)
        if strongest_sell:
            score = strongest_sell.strength * 10
            bull += self.liquidity_time_decay(score, strongest_sell, liquidity.current_index)

        bull = min(bull, 100)
        bear = min(bear, 100)

        return bull, bear, reasons

    # ==========================================================
    # FVG SCORE
    # ==========================================================
    def fvg_score(self, fvg: FVGResult):
        bull = 0.0
        bear = 0.0
        reasons = []

        active_bulls = [x for x in fvg.bullish if getattr(x, 'active', True)]
        if active_bulls:
            bull += min(len(active_bulls) * 8, 20)
            reasons.append(f"Active Bullish FVG ({len(active_bulls)})")

        active_bears = [x for x in fvg.bearish if getattr(x, 'active', True)]
        if active_bears:
            bear += min(len(active_bears) * 8, 20)
            reasons.append(f"Active Bearish FVG ({len(active_bears)})")

        if getattr(fvg, 'nearest', None):
            nearest = fvg.nearest
            if nearest.direction == "bullish":
                bull += 15
                reasons.append("Nearest Bullish FVG")
            else:
                bear += 15
                reasons.append("Nearest Bearish FVG")

        all_gaps = active_bulls + active_bears
        if all_gaps:
            strongest = max(all_gaps, key=lambda x: getattr(x, 'strength', 0))
            if strongest.direction == "bullish":
                bull += getattr(strongest, 'strength', 0) * 0.15
            else:
                bear += getattr(strongest, 'strength', 0) * 0.15

        current_index = getattr(fvg, "current_index", 0)

        for gap in all_gaps:
            weight = self.time_decay(gap, current_index)
            if gap.direction == "bullish":
                bull += 5 * weight
            else:
                bear += 5 * weight

        mitigated = [x for x in all_gaps if getattr(x, 'mitigated', False)]
        for gap in mitigated:
            if gap.direction == "bullish":
                bull -= 5
            else:
                bear -= 5

        if getattr(fvg, 'nearest', None):
            distance = getattr(fvg.nearest, 'distance', 1.0)
            if distance < 0.25:
                if fvg.nearest.direction == "bullish":
                    bull += 10
                else:
                    bear += 10
            elif distance < 0.50:
                if fvg.nearest.direction == "bullish":
                    bull += 5
                else:
                    bear += 5

        bull = min(bull, 100)
        bear = min(bear, 100)

        return bull, bear, reasons

    # ==========================================================
    # ALTERNATIVE FVG SCORE (I mbajtur nga kodi origjinal)
    # ==========================================================
    def fvg_score_alternate(self, fvg):
        score = 0
        score += min(len(fvg.bullish) * 5, 20)
        score += min(len(fvg.bearish) * 5, 20)
        score += min(getattr(fvg, 'active_count', 0) * 4, 20)
        score += min(getattr(fvg, 'mitigated_count', 0) * 3, 15)

        if getattr(fvg, 'nearest', None):
            score += 20
            score += min(getattr(fvg.nearest, 'strength', 0) / 5, 5)

        return round(min(score, 100), 2)

    # ==========================================================
    # TREND SCORE
    # ==========================================================
    def trend_score(self, structure: MarketStructureResult, mtf: MultiTimeframeResult):
        bull = 0.0
        bear = 0.0
        reasons = []

        trend = structure.trend.direction
        if trend == "bullish":
            bull += 20
            reasons.append("Bullish Structure Trend")
        elif trend == "bearish":
            bear += 20
            reasons.append("Bearish Structure Trend")

        if structure.bias == "bullish":
            bull += 15
        elif structure.bias == "bearish":
            bear += 15

        if getattr(structure.trend, 'internal_trend', '') == "bullish":
            bull += 8
        elif getattr(structure.trend, 'internal_trend', '') == "bearish":
            bear += 8

        if getattr(structure.trend, 'external_trend', '') == "bullish":
            bull += 12
        elif getattr(structure.trend, 'external_trend', '') == "bearish":
            bear += 12

        if mtf.aligned:
            if mtf.bias == "bullish":
                bull += 25
                reasons.append("MTF Bullish Alignment")
            elif mtf.bias == "bearish":
                bear += 25
                reasons.append("MTF Bearish Alignment")

        if mtf.confidence > 80:
            if mtf.bias == "bullish":
                bull += 10
            elif mtf.bias == "bearish":
                bear += 10

        return bull, bear, reasons

    # ==========================================================
    # MULTI TF SCORE
    # ==========================================================
    def mtf_score(self, mtf):
        score = 0
        if mtf.aligned:
            score += 35
        score += min(mtf.confidence * 0.35, 35)
        score += min(mtf.score * 0.30, 30)
        return round(min(score, 100), 2)

    # ==========================================================
    # LIQUIDITY VOID SCORE
    # ==========================================================
    def liquidity_void_score(self, liquidity):
        bull = 0.0
        bear = 0.0
        reasons = []

        if not hasattr(liquidity, "voids"):
            return bull, bear, reasons

        for void in liquidity.voids:
            if not getattr(void, "active", True):
                continue
            if void.direction == "bullish":
                bull += min(void.strength * 20, 20)
                reasons.append("Bullish Liquidity Void")
            elif void.direction == "bearish":
                bear += min(void.strength * 20, 20)
                reasons.append("Bearish Liquidity Void")

        return bull, bear, reasons

    # ==========================================================
    # INTERNAL / EXTERNAL LIQUIDITY
    # ==========================================================
    def structure_liquidity_score(self, liquidity):
        bull = 0.0
        bear = 0.0
        reasons = []

        for level in liquidity.buy_side:
            if getattr(level, "is_external", False):
                bear += 5
            elif getattr(level, "is_internal", False):
                bear += 2

        for level in liquidity.sell_side:
            if getattr(level, "is_external", False):
                bull += 5
            elif getattr(level, "is_internal", False):
                bull += 2

        return bull, bear, reasons

    # ==========================================================
    # LIQUIDITY TIME DECAY
    # ==========================================================
    def liquidity_time_decay(self, score, level, current_index):
        age = current_index - level.index
        if age <= 20:
            factor = 1.0
        elif age <= 50:
            factor = 0.80
        elif age <= 100:
            factor = 0.60
        else:
            factor = 0.40
        return score * factor

    # ==========================================================
    # CONFIDENCE ENGINE
    # ==========================================================
    def confidence_score(self, bull_score, bear_score, reasons):
        confidence = max(bull_score, bear_score)
        side = "NONE"

        if bull_score > bear_score:
            side = "BUY"
        elif bear_score > bull_score:
            side = "SELL"

        return {
            "side": side,
            "confidence": round(confidence, 2),
            "bull_score": round(bull_score, 2),
            "bear_score": round(bear_score, 2),
            "reasons": reasons
        }

    # ==========================================================
    # CONFLUENCE BONUS
    # ==========================================================
    def confluence_bonus(self, structure, liquidity, fvg, mtf):
        bonus = 0
        if getattr(structure, 'bias', None) == getattr(mtf, 'bias', None):
            bonus += 8
        if getattr(liquidity, 'sweeps', None) and getattr(fvg, 'nearest', None):
            bonus += 7
        if getattr(mtf, 'aligned', False):
            bonus += 10
        return min(bonus, 25)

    # ==========================================================
    # PENALTY
    # ==========================================================
    def confidence_penalty(self, structure, mtf):
        penalty = 0
        if getattr(structure, 'bias', None) == "neutral":
            penalty += 15
        if not getattr(mtf, 'aligned', False):
            penalty += 15
        return penalty
