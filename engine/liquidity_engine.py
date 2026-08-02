# ==========================================================
# LIQUIDITY ENGINE v2.0
# NazRmd ProBot
# PART 1 - IMPORTS & MODELS
# ==========================================================

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
import pandas as pd


# ==========================================================
# LIQUIDITY LEVEL
# ==========================================================
@dataclass
class LiquidityLevel:
    index: int
    timestamp: int
    price: float
    kind: str
    strength: float = 0.0
    score: float = 0.0
    touches: int = 1
    swept: bool = False
    active: bool = True
    sweep_index: int = -1
    volume: float = 0.0
    timeframe: str = ""
    internal: bool = False
    external: bool = False

    def distance(self, price):
        return abs(self.price - price)


# ==========================================================
# LIQUIDITY VOID
# ==========================================================
@dataclass
class LiquidityVoid:
    start_index: int
    end_index: int
    high: float
    low: float
    direction: str
    size: float
    filled: bool = False
    strength: float = 0.0


# ==========================================================
# RESULT
# ==========================================================
@dataclass
class LiquidityResult:
    equal_highs: List[LiquidityLevel] = field(default_factory=list)
    equal_lows: List[LiquidityLevel] = field(default_factory=list)
    buy_side: List[LiquidityLevel] = field(default_factory=list)
    sell_side: List[LiquidityLevel] = field(default_factory=list)
    sweeps: List[LiquidityLevel] = field(default_factory=list)
    voids: List[LiquidityVoid] = field(default_factory=list)
    strongest_buy: Optional[LiquidityLevel] = None
    strongest_sell: Optional[LiquidityLevel] = None
    nearest_buy: Optional[LiquidityLevel] = None
    nearest_sell: Optional[LiquidityLevel] = None
    current_index: int = 0


# ==========================================================
# ENGINE
# ==========================================================
class LiquidityEngine:

    def __init__(
        self,
        tolerance=0.0015,
        lookback=150,
        sweep_buffer=0.0005,
        void_factor=2.0
    ):
        self.tolerance = tolerance
        self.lookback = lookback
        self.sweep_buffer = sweep_buffer
        self.void_factor = void_factor

    # ==========================================================
    # MAIN ANALYZE
    # ==========================================================
    def analyze(self, df):
        result = LiquidityResult()

        if len(df) < 50:
            return result

        # --------------------------------------------------
        # Equal Highs / Lows
        # --------------------------------------------------
        result.equal_highs = self.equal_highs(df)
        result.equal_lows = self.equal_lows(df)

        # --------------------------------------------------
        # Buy Side / Sell Side
        # --------------------------------------------------
        result.buy_side = self.buy_side_liquidity(result.equal_highs)
        result.sell_side = self.sell_side_liquidity(result.equal_lows)

        # --------------------------------------------------
        # Sweeps
        # --------------------------------------------------
        result.sweeps = self.detect_sweeps(
            df,
            result.buy_side,
            result.sell_side
        )

        # --------------------------------------------------
        # Liquidity Voids
        # (Shenim: Funksioni detect_liquidity_voids duhet te jete pjese e klases)
        # --------------------------------------------------
        if hasattr(self, 'detect_liquidity_voids'):
            result.voids = self.detect_liquidity_voids(df)

        # --------------------------------------------------
        # Nearest Levels
        # --------------------------------------------------
        price = float(df.close.iloc[-1])
        result.nearest_buy = self.nearest_liquidity(result.buy_side, price)
        result.nearest_sell = self.nearest_liquidity(result.sell_side, price)

        # --------------------------------------------------
        # Strongest Levels
        # --------------------------------------------------
        result.strongest_buy = self.strongest_liquidity(result.buy_side)
        result.strongest_sell = self.strongest_liquidity(result.sell_side)

        result.current_index = len(df) - 1

        return result

    # ==========================================================
    # EQUAL HIGHS
    # ==========================================================
    def equal_highs(self, df):
        levels = []
        highs = df.high.values
        atr = None

        if "atr" in df.columns:
            atr = df.atr.values

        for i in range(3, len(df) - 3):
            h = highs[i]
            touches = 1
            volume = 0.0
            tolerance = h * self.tolerance

            if atr is not None:
                tolerance = max(tolerance, atr[i] * 0.15)

            for j in range(i + 1, min(i + 35, len(df))):
                if abs(highs[j] - h) <= tolerance:
                    touches += 1
                    volume += float(df.volume.iloc[j])

            if touches >= 2:
                strength = min(1.0, touches / 5)
                score = min(100, 25 * touches)
                levels.append(
                    LiquidityLevel(
                        index=i,
                        timestamp=int(df.timestamp.iloc[i]),
                        price=float(h),
                        kind="EQH",
                        touches=touches,
                        strength=strength,
                        score=score,
                        volume=volume,
                        active=True
                    )
                )

        return levels

    # ==========================================================
    # EQUAL LOWS
    # ==========================================================
    def equal_lows(self, df):
        levels = []
        lows = df.low.values
        atr = None

        if "atr" in df.columns:
            atr = df.atr.values

        for i in range(3, len(df) - 3):
            l = lows[i]
            touches = 1
            volume = 0.0
            tolerance = l * self.tolerance

            if atr is not None:
                tolerance = max(tolerance, atr[i] * 0.15)

            for j in range(i + 1, min(i + 35, len(df))):
                if abs(lows[j] - l) <= tolerance:
                    touches += 1
                    volume += float(df.volume.iloc[j])

            if touches >= 2:
                strength = min(1.0, touches / 5)
                score = min(100, 25 * touches)
                levels.append(
                    LiquidityLevel(
                        index=i,
                        timestamp=int(df.timestamp.iloc[i]),
                        price=float(l),
                        kind="EQL",
                        touches=touches,
                        strength=strength,
                        score=score,
                        volume=volume,
                        active=True
                    )
                )

        return levels

    # ==========================================================
    # BUY SIDE LIQUIDITY
    # ==========================================================
    def buy_side_liquidity(self, equal_highs):
        result = []
        for level in equal_highs:
            level.kind = "BUY_SIDE"
            level.external = True
            level.internal = False
            result.append(level)
            
        return sorted(
            result,
            key=lambda x: x.score,
            reverse=True
        )

    # ==========================================================
    # SELL SIDE LIQUIDITY
    # ==========================================================
    def sell_side_liquidity(self, equal_lows):
        result = []
        for level in equal_lows:
            level.kind = "SELL_SIDE"
            level.external = True
            level.internal = False
            result.append(level)
            
        return sorted(
            result,
            key=lambda x: x.score,
            reverse=True
        )

    # ==========================================================
    # LIQUIDITY SWEEPS
    # ==========================================================
    def detect_sweeps(
        self,
        df,
        buy_side,
        sell_side
    ):
        sweeps = []
        highs = df.high.values
        lows = df.low.values
        closes = df.close.values

        # -----------------------------
        # BUY SIDE SWEEP
        # -----------------------------
        for level in buy_side:
            for i in range(level.index + 1, len(df)):
                if highs[i] > level.price:
                    if closes[i] < level.price:
                        level.swept = True
                        level.active = False
                        level.sweep_index = i

                        sweep = LiquidityLevel(
                            index=i,
                            timestamp=int(df.timestamp.iloc[i]),
                            price=level.price,
                            kind="BUY_SIDE_SWEEP",
                            touches=level.touches,
                            score=level.score,
                            strength=level.strength,
                            swept=True,
                            active=False,
                            volume=float(df.volume.iloc[i])
                        )
                        sweeps.append(sweep)
                    break

        # -----------------------------
        # SELL SIDE SWEEP
        # -----------------------------
        for level in sell_side:
            for i in range(level.index + 1, len(df)):
                if lows[i] < level.price:
                    if closes[i] > level.price:
                        level.swept = True
                        level.active = False
                        level.sweep_index = i

                        sweep = LiquidityLevel(
                            index=i,
                            timestamp=int(df.timestamp.iloc[i]),
                            price=level.price,
                            kind="SELL_SIDE_SWEEP",
                            touches=level.touches,
                            score=level.score,
                            strength=level.strength,
                            swept=True,
                            active=False,
                            volume=float(df.volume.iloc[i])
                        )
                        sweeps.append(sweep)
                    break

        return sweeps

    # ==========================================================
    # GRAB / SWEEP CLASSIFIER
    # ==========================================================
    def classify_sweep(
        self,
        candle,
        level,
        bullish=True
    ):
        if bullish:
            if candle["high"] > level.price:
                if candle["close"] < level.price:
                    return "SWEEP"
                return "BREAK"
        else:
            if candle["low"] < level.price:
                if candle["close"] > level.price:
                    return "SWEEP"
                return "BREAK"
                
        return "NONE"

    # ==========================================================
    # INTERNAL LIQUIDITY
    # ==========================================================
    def internal_liquidity(
        self,
        levels,
        swing_high,
        swing_low
    ):
        result = []
        for level in levels:
            if swing_low <= level.price <= swing_high:
                level.internal = True
                level.external = False
                result.append(level)
        return result

    # ==========================================================
    # EXTERNAL LIQUIDITY
    # ==========================================================
    def external_liquidity(
        self,
        levels,
        swing_high,
        swing_low
    ):
        result = []
        for level in levels:
            if level.price > swing_high or level.price < swing_low:
                level.external = True
                level.internal = False
                result.append(level)
        return result

    # ==========================================================
    # ACTIVE LIQUIDITY
    # ==========================================================
    def active_liquidity(self, levels):
        return [
            x
            for x in levels
            if getattr(x, "active", False)
        ]

    # ==========================================================
    # SWEPT LIQUIDITY
    # ==========================================================
    def swept_liquidity(self, levels):
        return [
            x
            for x in levels
            if getattr(x, "swept", False)
        ]

    # ==========================================================
    # STRONGEST
    # ==========================================================
    def strongest_liquidity(self, levels):
        if not levels:
            return None
            
        return max(
            levels,
            key=lambda x: (
                x.score,
                x.strength,
                x.touches,
                x.volume
            )
        )

    # ==========================================================
    # NEAREST
    # ==========================================================
    def nearest_liquidity(
        self,
        levels,
        current_price
    ):
        if not levels:
            return None
            
        return min(
            levels,
            key=lambda x: abs(x.price - current_price)
        )

    # ==========================================================
    # MARKET SCORE
    # ==========================================================
    def liquidity_score(self, result):
        score = 0

        if result.strongest_buy:
            score += result.strongest_buy.score * 0.15

        if result.strongest_sell:
            score += result.strongest_sell.score * 0.15

        score += len(result.sweeps) * 6
        score += len(result.voids) * 4
        score += len(result.equal_highs)
        score += len(result.equal_lows)

        return min(100, round(score, 2))

    # ==========================================================
    # SUMMARY
    # ==========================================================
    def summary(self, result):
        return {
            "equal_highs": len(result.equal_highs),
            "equal_lows": len(result.equal_lows),
            "buy_side": len(result.buy_side),
            "sell_side": len(result.sell_side),
            "active_buy": len(self.active_liquidity(result.buy_side)),
            "active_sell": len(self.active_liquidity(result.sell_side)),
            "sweeps": len(result.sweeps),
            "voids": len(result.voids),
            "strongest_buy": result.strongest_buy,
            "strongest_sell": result.strongest_sell,
            "nearest_buy": result.nearest_buy,
            "nearest_sell": result.nearest_sell,
            "score": self.liquidity_score(result)
        }
