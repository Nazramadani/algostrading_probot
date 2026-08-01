# ==========================================================
# SMC FAIR VALUE GAP ENGINE v3.0
# NazRmd ProBot
# ==========================================================

from typing import List
import numpy as np
import pandas as pd

from .models import (
    FairValueGap,
    FVGResult
)

class FVGEngine:

    def __init__(
        self,
        min_gap_percent=0.0005,
        mitigation_percent=0.50,
        atr_multiplier=0.20,
        max_age=250
    ):
        self.min_gap = min_gap_percent
        self.mitigation = mitigation_percent
        self.atr_multiplier = atr_multiplier
        self.max_age = max_age

    # ==========================================================
    # MAIN ANALYSIS
    # ==========================================================
    def analyze(self, df):
        result = FVGResult()

        if len(df) < 20:
            return result

        bullish = []
        bearish = []

        for i in range(2, len(df)):
            bull = self.detect_bullish(df, i)
            if bull:
                bullish.append(bull)

            bear = self.detect_bearish(df, i)
            if bear:
                bearish.append(bear)

        current_price = float(df.close.iloc[-1])

        bullish = self.update_status(bullish, df, current_price)
        bearish = self.update_status(bearish, df, current_price)

        bullish = self.update_scores(bullish, df)
        bearish = self.update_scores(bearish, df)

        bullish = self.merge_gaps(bullish)
        bearish = self.merge_gaps(bearish)

        result.bullish = bullish
        result.bearish = bearish
        result.gaps = bullish + bearish

        result.active = [
            x for x in result.gaps
            if x.active
        ]

        result.mitigated = [
            x for x in result.gaps
            if x.mitigated
        ]

        result.filled = [
            x for x in result.gaps
            if x.filled
        ]

        result.nearest = self.find_nearest(
            result.gaps,
            current_price
        )

        result.strongest = self.find_strongest(
            result.gaps
        )

        result.active_count = len(result.active)
        result.mitigated_count = len(result.mitigated)
        result.filled_count = len(result.filled)
        result.current_index = len(df) - 1

        return result

    # ==========================================================
    # BULLISH FVG
    # ==========================================================
    def detect_bullish(self, df, i):
        high1 = float(df.high.iloc[i - 2])
        low3 = float(df.low.iloc[i])

        if low3 <= high1:
            return None

        gap = low3 - high1
        percent = gap / float(df.close.iloc[i])

        if percent < self.min_gap:
            return None

        if not self.atr_filter(df, i, gap):
            return None

        return FairValueGap(
            direction="bullish",
            top=low3,
            bottom=high1,
            index=i,
            timestamp=int(df.iloc[i]["timestamp"]),
            mitigated=False,
            filled=False,
            active=True,
            strength=0.0,
            score=0.0,
            distance=0.0,
            fill_percent=0.0,
            age=0,
            ce=(low3 + high1) / 2
        )

    # ==========================================================
    # BEARISH FVG
    # ==========================================================
    def detect_bearish(self, df, i):
        low1 = float(df.low.iloc[i - 2])
        high3 = float(df.high.iloc[i])

        if high3 >= low1:
            return None

        gap = low1 - high3
        percent = gap / float(df.close.iloc[i])

        if percent < self.min_gap:
            return None

        return FairValueGap(
            direction="bearish",
            top=low1,
            bottom=high3,
            index=i,
            timestamp=int(df.iloc[i]["timestamp"]),
            mitigated=False,
            filled=False,
            active=True,
            strength=0.0,
            score=0.0,
            distance=0.0,
            fill_percent=0.0,
            age=0,
            ce=(low1 + high3) / 2
        )

    # ==========================================================
    # ATR FILTER
    # ==========================================================
    def atr_filter(self, df, index, gap_size):
        if "atr" not in df.columns:
            return True

        atr = float(df.atr.iloc[index])

        if atr <= 0:
            return True

        return gap_size >= atr * self.atr_multiplier

    # ==========================================================
    # FILL %
    # ==========================================================
    def calculate_fill(self, gap, df):
        gap_size = abs(gap.top - gap.bottom)

        if gap_size == 0:
            return 100

        fill = 0.0

        for i in range(gap.index + 1, len(df)):
            high = float(df.high.iloc[i])
            low = float(df.low.iloc[i])

            if gap.direction == "bullish":
                penetration = gap.top - low
            else:
                penetration = high - gap.bottom

            if penetration > fill:
                fill = penetration

        fill_percent = (fill / gap_size) * 100

        return max(0, min(fill_percent, 100))

    # ==========================================================
    # UPDATE STATUS
    # ==========================================================
    def update_status(self, gaps, df, current_price):
        for gap in gaps:
            gap.age = len(df) - gap.index

            gap.distance = abs(
                current_price -
                ((gap.top + gap.bottom) / 2)
            )

            gap.fill_percent = self.calculate_fill(gap, df)

            gap.mitigated = (
                gap.fill_percent >=
                self.mitigation * 100
            )

            gap.filled = (
                gap.fill_percent >= 100
            )

            gap.invalid = self.is_invalid(gap, df)

            gap.active = (
                not gap.filled
                and
                not gap.invalid
            )

        return gaps

    # ==========================================================
    # INVALIDATION
    # ==========================================================
    def is_invalid(self, gap, df):
        if gap.age > self.max_age:
            return True

        if gap.direction == "bullish":
            if float(df.close.iloc[-1]) < gap.bottom:
                return True
        else:
            if float(df.close.iloc[-1]) > gap.top:
                return True

        return False

    # ==========================================================
    # FVG SCORE ENGINE
    # ==========================================================
    def calculate_score(self, gap, df):
        score = 0.0

        # GAP SIZE
        gap_size = abs(gap.top - gap.bottom)
        score += min(gap_size * 10000, 25)

        # FILL %
        score += (100 - gap.fill_percent) * 0.15

        # AGE
        age_score = max(0, 20 - gap.age * 0.10)
        score += age_score

        # DISTANCE
        if gap.distance == 0:
            score += 15
        else:
            score += max(0, 15 - gap.distance * 0.5)

        # MITIGATION
        if gap.mitigated:
            score -= 10

        # FILLED
        if gap.filled:
            score -= 40

        score = max(0, min(score, 100))
        return round(score, 2)

    # ==========================================================
    # STRENGTH
    # ==========================================================
    def calculate_strength(self, gap):
        return round(gap.score / 100, 2)

    # ==========================================================
    # NEAREST (Split Method - Optional Fallback)
    # ==========================================================
    def _find_nearest_split(self, bulls, bears, price):
        all_gaps = bulls + bears
        if not all_gaps:
            return None
        return min(all_gaps, key=lambda x: x.distance)

    # ==========================================================
    # UPDATE SCORE
    # ==========================================================
    def update_scores(self, gaps, df):
        for gap in gaps:
            gap.score = self.calculate_score(gap, df)
            gap.strength = self.calculate_strength(gap)
        return gaps

    # ==========================================================
    # STRONGEST
    # ==========================================================
    def find_strongest(self, gaps):
        if len(gaps) == 0:
            return None
        return max(gaps, key=lambda x: x.score)

    # ==========================================================
    # NEAREST (Main List Method)
    # ==========================================================
    def find_nearest(self, gaps, price):
        if len(gaps) == 0:
            return None
        return min(
            gaps,
            key=lambda x: abs(((x.top + x.bottom) / 2) - price)
        )

    # ==========================================================
    # ACTIVE
    # ==========================================================
    def active_gaps(self, gaps):
        return [x for x in gaps if x.active]

    # ==========================================================
    # FILLED
    # ==========================================================
    def filled_gaps(self, gaps):
        return [x for x in gaps if x.filled]

    # ==========================================================
    # MERGE OVERLAPPING FVG
    # ==========================================================
    def merge_gaps(self, gaps):
        if len(gaps) <= 1:
            return gaps

        gaps = sorted(
            gaps,
            key=lambda x: x.bottom
        )

        merged = []
        current = gaps[0]

        for nxt in gaps[1:]:
            if nxt.bottom <= current.top:
                current.top = max(current.top, nxt.top)
                current.bottom = min(current.bottom, nxt.bottom)
                current.score = max(current.score, nxt.score)
            else:
                merged.append(current)
                current = nxt

        merged.append(current)
        return merged

    # ==========================================================
    # PREMIUM DISCOUNT BONUS
    # ==========================================================
    def premium_discount_bonus(self, gap, structure):
        if structure is None:
            return 0

        bonus = 0

        if gap.direction == "bullish":
            if structure.in_discount:
                bonus += 10
        else:
            if structure.in_premium:
                bonus += 10

        return bonus

    # ==========================================================
    # HTF BONUS
    # ==========================================================
    def htf_bonus(self, gap, mtf):
        if mtf is None:
            return 0

        if gap.direction == "bullish":
            if mtf.bias == "bullish":
                return 10

        if gap.direction == "bearish":
            if mtf.bias == "bearish":
                return 10

        return 0

    # ==========================================================
    # SUMMARY
    # ==========================================================
    def summary(self, result):
        return {
            "bullish": len(result.bullish),
            "bearish": len(result.bearish),
            "active": len(result.active),
            "filled": len(result.filled),
            "mitigated": len(result.mitigated),
            "nearest": result.nearest,
            "strongest": result.strongest
        }

    # ==========================================================
    # ACTIVE BULLISH
    # ==========================================================
    def active_bullish(self, result):
        return [x for x in result.bullish if x.active]

    # ==========================================================
    # ACTIVE BEARISH
    # ==========================================================
    def active_bearish(self, result):
        return [x for x in result.bearish if x.active]

    # ==========================================================
    # NEAREST BULLISH
    # ==========================================================
    def nearest_bullish(self, result, price):
        active = self.active_bullish(result)

        if not active:
            return None

        return min(
            active,
            key=lambda x: abs(x.ce - price)
        )

    # ==========================================================
    # NEAREST BEARISH
    # ==========================================================
    def nearest_bearish(self, result, price):
        active = self.active_bearish(result)

        if not active:
            return None

        return min(
            active,
            key=lambda x: abs(x.ce - price)
        )