# ==========================================================
# ORDER BLOCK ENGINE v2.0
# NazRmd ProBot
# ==========================================================

from dataclasses import dataclass, field
from typing import List
import pandas as pd
import numpy as np

# ==========================================================
# ORDER BLOCK
# ==========================================================
@dataclass
class OrderBlock:
    index: int
    timestamp: int
    direction: str
    high: float
    low: float
    open: float
    close: float
    volume: float
    strength: float = 0.0
    score: float = 0.0
    mitigated: bool = False
    invalidated: bool = False
    touched: bool = False
    confirmed: bool = False
    impulse_size: float = 0.0
    impulse_ratio: float = 0.0
    body_percent: float = 0.0
    wick_percent: float = 0.0

# ==========================================================
# RESULT
# ==========================================================
@dataclass
class OrderBlockResult:
    bullish: List[OrderBlock] = field(default_factory=list)
    bearish: List[OrderBlock] = field(default_factory=list)
    nearest_bullish: OrderBlock = None
    nearest_bearish: OrderBlock = None
    strongest_bullish: OrderBlock = None
    strongest_bearish: OrderBlock = None

# ==========================================================
# ENGINE
# ==========================================================
class OrderBlockEngine:
    def __init__(self, impulse_multiplier=2.0, volume_multiplier=1.50, max_blocks=40):
        self.impulse_multiplier = impulse_multiplier
        self.volume_multiplier = volume_multiplier
        self.max_blocks = max_blocks

    # ======================================================
    # PUBLIC
    # ======================================================
    def analyze(self, df):
        result = OrderBlockResult()

        if len(df) < 100:
            return result

        df = df.copy()

        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]
        df["body_percent"] = (df["body"] / df["range"].replace(0, np.nan)).fillna(0)
        df["vol_ma"] = df["volume"].rolling(20).mean()

        bullish = self.detect_bullish(df)
        bearish = self.detect_bearish(df)

        bullish = self.score_blocks(df, bullish)
        bearish = self.score_blocks(df, bearish)

        bullish = self.detect_mitigation(df, bullish)
        bearish = self.detect_mitigation(df, bearish)

        result.bullish = bullish
        result.bearish = bearish

        if bullish:
            result.nearest_bullish = bullish[-1]
            result.strongest_bullish = max(bullish, key=lambda x: x.score)

        if bearish:
            result.nearest_bearish = bearish[-1]
            result.strongest_bearish = max(bearish, key=lambda x: x.score)

        return result

    # ======================================================
    # BULLISH ORDER BLOCK DETECTOR
    # ======================================================
    def detect_bullish(self, df):
        blocks = []

        for i in range(2, len(df) - 2):
            current = df.iloc[i]
            next1 = df.iloc[i + 1]
            next2 = df.iloc[i + 2]

            # Bearish candle
            if current.close >= current.open:
                continue

            impulse = next2.close - current.close
            if impulse <= 0:
                continue

            avg_body = df["body"].iloc[max(0, i - 20):i].mean()
            if avg_body == 0:
                continue

            if impulse < avg_body * self.impulse_multiplier:
                continue

            volume_ok = current.volume >= current.vol_ma * self.volume_multiplier

            body = abs(current.close - current.open)
            rng = current.high - current.low

            if rng <= 0:
                continue

            body_percent = body / rng
            wick_percent = 1 - body_percent

            ob = OrderBlock(
                index=i,
                timestamp=int(current.timestamp),
                direction="bullish",
                high=float(current.high),
                low=float(current.low),
                open=float(current.open),
                close=float(current.close),
                volume=float(current.volume),
                body_percent=body_percent,
                wick_percent=wick_percent,
                impulse_size=float(impulse),
                impulse_ratio=float(impulse / avg_body),
                confirmed=volume_ok
            )
            blocks.append(ob)

        return blocks[:self.max_blocks]

    # ======================================================
    # BEARISH ORDER BLOCK DETECTOR
    # ======================================================
    def detect_bearish(self, df):
        blocks = []

        for i in range(2, len(df) - 2):
            current = df.iloc[i]
            next1 = df.iloc[i + 1]
            next2 = df.iloc[i + 2]

            if current.close <= current.open:
                continue

            impulse = current.close - next2.close
            if impulse <= 0:
                continue

            avg_body = df["body"].iloc[max(0, i - 20):i].mean()
            if avg_body == 0:
                continue

            if impulse < avg_body * self.impulse_multiplier:
                continue

            volume_ok = current.volume >= current.vol_ma * self.volume_multiplier

            body = abs(current.close - current.open)
            rng = current.high - current.low

            if rng <= 0:
                continue

            body_percent = body / rng
            wick_percent = 1 - body_percent

            ob = OrderBlock(
                index=i,
                timestamp=int(current.timestamp),
                direction="bearish",
                high=float(current.high),
                low=float(current.low),
                open=float(current.open),
                close=float(current.close),
                volume=float(current.volume),
                body_percent=body_percent,
                wick_percent=wick_percent,
                impulse_size=float(impulse),
                impulse_ratio=float(impulse / avg_body),
                confirmed=volume_ok
            )
            blocks.append(ob)

        return blocks[:self.max_blocks]

    # ======================================================
    # SCORE ENGINE
    # ======================================================
    def score_blocks(self, df, blocks):
        for ob in blocks:
            score = 0

            # Volume
            if ob.confirmed:
                score += 30

            # Body %
            score += ob.body_percent * 25

            # Impulse
            score += min(ob.impulse_ratio * 10, 25)

            # Wick
            if ob.wick_percent < 0.30:
                score += 10

            ob.score = round(score, 2)
            ob.strength = round(score / 100, 2)

        return blocks

    # ======================================================
    # MITIGATION DETECTOR
    # ======================================================
    def detect_mitigation(self, df, blocks):
        last_price = float(df["close"].iloc[-1])

        for ob in blocks:
            future = df.iloc[ob.index + 1:]

            for _, candle in future.iterrows():
                # Bullish Order Block
                if ob.direction == "bullish":
                    if candle["low"] <= ob.high:
                        ob.touched = True
                    if candle["close"] < ob.low:
                        ob.invalidated = True
                        break
                # Bearish Order Block
                else:
                    if candle["high"] >= ob.low:
                        ob.touched = True
                    if candle["close"] > ob.high:
                        ob.invalidated = True
                        break

            if ob.touched and not ob.invalidated:
                ob.mitigated = True

        return blocks

    # ======================================================
    # HELPER METHODS
    # ======================================================
    def get_active_blocks(self, blocks):
        return [x for x in blocks if not x.invalidated]

    def get_fresh_blocks(self, blocks):
        return [x for x in blocks if not x.touched and not x.invalidated]

    def get_strong_blocks(self, blocks, minimum_score=70):
        return [x for x in blocks if x.score >= minimum_score]

    def nearest_block(self, blocks, price):
        if len(blocks) == 0:
            return None
        return min(blocks, key=lambda x: abs(x.high - price))

    def strongest_block(self, blocks):
        if len(blocks) == 0:
            return None
        return max(blocks, key=lambda x: x.score)

    def breaker_blocks(self, blocks):
        return [x for x in blocks if x.invalidated]

    def retested_blocks(self, blocks):
        return [x for x in blocks if x.touched and not x.invalidated]

    # ======================================================
    # SUMMARY
    # ======================================================
    def summary(self, result):
        return {
            "bullish": len(result.bullish),
            "bearish": len(result.bearish),
            "strong_bullish": len(self.get_strong_blocks(result.bullish)),
            "strong_bearish": len(self.get_strong_blocks(result.bearish)),
            "fresh_bullish": len(self.get_fresh_blocks(result.bullish)),
            "fresh_bearish": len(self.get_fresh_blocks(result.bearish)),
            "mitigated_bullish": len(self.retested_blocks(result.bullish)),
            "mitigated_bearish": len(self.retested_blocks(result.bearish)),
            "breaker_blocks": len(self.breaker_blocks(result.bullish)) + len(self.breaker_blocks(result.bearish))
        }
