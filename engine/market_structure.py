# ============================================================
# SMC MARKET STRUCTURE ENGINE v2.0
# ============================================================

import pandas as pd
import pandas_ta as ta

from .models import (
    SwingPoint,
    MarketStructureResult,
    StructureBreak,
)


class MarketStructureEngine:

    def __init__(
        self,
        pivot_length=5,
        atr_length=14,
        atr_multiplier=0.30,
        volume_weight=0.25,
        body_weight=0.20,
        distance_weight=0.55,
    ):

        self.default_pivot = pivot_length
        self.atr_length = atr_length
        self.atr_multiplier = atr_multiplier

        self.volume_weight = volume_weight
        self.body_weight = body_weight
        self.distance_weight = distance_weight

    # ==========================================================
    # MAIN
    # ==========================================================

    def analyze(self, df):

        result = MarketStructureResult()

        if df is None or len(df) < 100:
            return result

        df = df.copy()

        df = self._calculate_atr(df)

        pivot = self._dynamic_pivot(df)

        # --------------------------------------------------
        # Swings
        # --------------------------------------------------

        swings = self._detect_swings(df, pivot)

        swings = self._classify_swings(swings)

        swings = self._rank_swings(swings)

        swings = self._calculate_strength(swings, df)

        swings = self._detect_internal_structure(swings)

        swings = self._detect_external_structure(swings)

        # --------------------------------------------------
        # Trend
        # --------------------------------------------------

        trend = self._detect_trend(swings)

        # --------------------------------------------------
        # BOS / CHOCH
        # --------------------------------------------------

        breaks = self._detect_bos(df, swings)

        breaks = self._score_breaks(breaks)

        breaks = self._detect_choch(trend, breaks)

        # --------------------------------------------------
        # Final Trend
        # --------------------------------------------------

        trend = self._trend_from_breaks(breaks)

        structure_score = self._calculate_structure_score(
            swings,
            breaks,
            trend,
        )

        bull_score, bear_score = self._direction_score(breaks)

        # --------------------------------------------------
        # Result
        # --------------------------------------------------

        result.swings = swings
        result.breaks = breaks

        result.trend.direction = trend

        result.bias = trend

        result.structure_score = structure_score

        result.confidence = structure_score

        result.bullish_score = bull_score

        result.bearish_score = bear_score

        result.trade_allowed = self._trade_allowed(
            structure_score,
            trend,
        )

        result.trade_side = self._trade_side(trend)

        return result

# ==========================================================
# STRUCTURE SCORE
# ==========================================================

    def _calculate_structure_score(
        self,
        swings,
        breaks,
        trend,
    ):

        score = 0.0

        # Trend
        if trend != "neutral":
            score += 20

        # Average swing strength
        if swings:
            avg_strength = (
                sum(s.strength for s in swings[-5:])
                / min(5, len(swings))
            )
            score += avg_strength * 0.25

        # BOS
        bos = [b for b in breaks if b.kind == "BOS"]
        score += min(len(bos) * 5, 20)

        # External BOS
        ext = [b for b in bos if b.external]
        score += min(len(ext) * 10, 20)

        # CHOCH penalty
        choch = [b for b in breaks if b.kind == "CHOCH"]
        score -= min(len(choch) * 6, 18)

        return round(max(0, min(score, 100)), 2)

# ==========================================================
# BULL / BEAR SCORE
# ==========================================================

    def _direction_score(self, breaks):

        bull = 0
        bear = 0

        for b in breaks:

            value = 10

            if b.external:
                value += 10

            if b.kind == "CHOCH":
                value += 5

            if b.direction == "bullish":
                bull += value
            else:
                bear += value

        return bull, bear

# ==========================================================
# ATR
# ==========================================================

    def _calculate_atr(self, df):

        df["atr"] = ta.atr(
            df["high"],
            df["low"],
            df["close"],
            length=self.atr_length,
        )

        df["atr"] = df["atr"].bfill()

        df["body"] = (
            df["close"] - df["open"]
        ).abs()

        df["range"] = (
            df["high"] - df["low"]
        )

        df["body_percent"] = (
            df["body"] /
            df["range"].replace(0, 1)
        )

        if "volume" in df.columns:

            df["volume_ma"] = (
                df["volume"]
                .rolling(20)
                .mean()
                .bfill()
            )

        else:

            df["volume"] = 1
            df["volume_ma"] = 1

        return df

# ==========================================================
# DYNAMIC PIVOT
# ==========================================================

    def _dynamic_pivot(self, df):

        atr = float(df["atr"].iloc[-1])
        close = float(df["close"].iloc[-1])

        volatility = atr / close

        if volatility < 0.003:
            return 3

        if volatility < 0.008:
            return 5

        return 7

# ==========================================================
# DETECT SWINGS
# ==========================================================

    def _detect_swings(self, df, pivot):

        swings = []

        highs = df["high"].values
        lows = df["low"].values
        atr = df["atr"].values

        last = None

        for i in range(pivot, len(df) - pivot):

            if highs[i] == max(highs[i-pivot:i+pivot+1]):

                if self._is_valid_swing(highs[i], last, atr[i]):

                    swings.append(
                        SwingPoint(
                            index=i,
                            timestamp=int(df.iloc[i]["timestamp"]),
                            price=float(highs[i]),
                            kind="HIGH",
                        )
                    )

                    last = highs[i]

            if lows[i] == min(lows[i-pivot:i+pivot+1]):

                if self._is_valid_swing(lows[i], last, atr[i]):

                    swings.append(
                        SwingPoint(
                            index=i,
                            timestamp=int(df.iloc[i]["timestamp"]),
                            price=float(lows[i]),
                            kind="LOW",
                        )
                    )

                    last = lows[i]

        swings.sort(key=lambda s: s.index)

        return swings

# ==========================================================
# VALID SWING
# ==========================================================

    def _is_valid_swing(
        self,
        price,
        previous_price,
        atr,
    ):

        if previous_price is None:
            return True

        return abs(price - previous_price) >= (
            atr * self.atr_multiplier
        )

# ==========================================================
# CLASSIFY SWINGS
# ==========================================================

    def _classify_swings(self, swings):

        last_high = None
        last_low = None

        for swing in swings:

            if swing.kind == "HIGH":

                if last_high is None:
                    swing.label = "HH"
                else:
                    swing.label = (
                        "HH"
                        if swing.price > last_high
                        else "LH"
                    )

                last_high = swing.price

            else:

                if last_low is None:
                    swing.label = "LL"
                else:
                    swing.label = (
                        "HL"
                        if swing.price > last_low
                        else "LL"
                    )

                last_low = swing.price

        return swings

# ==========================================================
# SWING RANKING
# ==========================================================

    def _rank_swings(self, swings):

        if len(swings) < 2:
            return swings

        for i, swing in enumerate(swings):

            swing.rank = i + 1

            if i == 0:
                swing.distance = 0
                continue

            swing.distance = abs(
                swing.price -
                swings[i - 1].price
            )

        return swings

# ==========================================================
# TREND
# ==========================================================

    def _detect_trend(self, swings):

        if len(swings) < 4:
            return "neutral"

        labels = [x.label for x in swings[-4:]]

        if labels == ["HL", "HH", "HL", "HH"] or labels[-2:] == ["HL", "HH"]:
            return "bullish"

        if labels == ["LH", "LL", "LH", "LL"] or labels[-2:] == ["LH", "LL"]:
            return "bearish"

        return "neutral"

# ==========================================================
# INTERNAL STRUCTURE
# ==========================================================

    def _detect_internal_structure(self, swings):

        if len(swings) < 3:
            return swings

        distances = [
            abs(swings[i].price - swings[i-1].price)
            for i in range(1, len(swings))
        ]

        average = sum(distances) / len(distances)

        for i in range(1, len(swings)):

            distance = abs(
                swings[i].price -
                swings[i-1].price
            )

            swings[i].is_internal = (
                distance < average * 0.60
            )

            swings[i].is_external = (
                not swings[i].is_internal
            )

        return swings

# ==========================================================
# EXTERNAL STRUCTURE
# ==========================================================

    def _detect_external_structure(self, swings):

        if len(swings) < 4:
            return swings

        highs = [x for x in swings if x.kind == "HIGH"]
        lows = [x for x in swings if x.kind == "LOW"]

        if highs:

            strongest = max(
                highs,
                key=lambda x: x.strength,
            )

            strongest.is_external = True
            strongest.is_internal = False

        if lows:

            strongest = max(
                lows,
                key=lambda x: x.strength,
            )

            strongest.is_external = True
            strongest.is_internal = False

        return swings

# ==========================================================
# BOS DETECTION V2
# ==========================================================

    def _detect_bos(self, df, swings):

        breaks = []

        closes = df["close"].values
        atrs = df["atr"].values

        for swing in swings:

            for i in range(swing.index + 1, len(df)):

                atr = atrs[i]

                # ----------------------------------
                # Bullish BOS
                # ----------------------------------

                if swing.kind == "HIGH":

                    if closes[i] <= swing.price:
                        continue

                    displacement = closes[i] - swing.price

                    if displacement < atr * 0.20:
                        continue

                    breaks.append(

                        StructureBreak(
                            kind="BOS",
                            direction="bullish",
                            index=i,
                            timestamp=int(df.iloc[i]["timestamp"]),
                            price=float(closes[i]),
                            swing_index=swing.index,
                            strength=round(displacement / atr, 2),
                            confirmed=True,
                            internal=swing.is_internal,
                            external=swing.is_external,
                        )

                    )

                    break

                # ----------------------------------
                # Bearish BOS
                # ----------------------------------

                else:

                    if closes[i] >= swing.price:
                        continue

                    displacement = swing.price - closes[i]

                    if displacement < atr * 0.20:
                        continue

                    breaks.append(

                        StructureBreak(
                            kind="BOS",
                            direction="bearish",
                            index=i,
                            timestamp=int(df.iloc[i]["timestamp"]),
                            price=float(closes[i]),
                            swing_index=swing.index,
                            strength=round(displacement / atr, 2),
                            confirmed=True,
                            internal=swing.is_internal,
                            external=swing.is_external,
                        )

                    )

                    break

        return breaks


# ==========================================================
# BOS SCORE
# ==========================================================

    def _score_breaks(self, breaks):

        for b in breaks:

            score = 50

            score += min(b.strength * 10, 30)

            if b.external:
                score += 20

            elif b.internal:
                score += 10

            b.score = round(min(score, 100), 2)

        return breaks


# ==========================================================
# CHOCH DETECTION
# ==========================================================

    def _detect_choch(self, trend, breaks):

        if len(breaks) < 2:
            return breaks

        previous = None

        for current in breaks:

            if previous is None:
                previous = current
                continue

            if previous.direction != current.direction:
                current.kind = "CHOCH"

            previous = current

        return breaks


# ==========================================================
# SWING STRENGTH
# ==========================================================

    def _calculate_strength(self, swings, df):

        for swing in swings:

            atr = df["atr"].iloc[swing.index]

            body = df["body_percent"].iloc[swing.index]

            volume = (
                df["volume"].iloc[swing.index]
                / max(df["volume_ma"].iloc[swing.index], 1)
            )

            distance = (
                df["high"].iloc[swing.index]
                - df["low"].iloc[swing.index]
            ) / atr

            distance_score = min(distance * 35, 35)

            volume_score = min(volume * 25, 25)

            body_score = body * 20

            swing.strength = round(
                min(
                    distance_score +
                    volume_score +
                    body_score,
                    100,
                ),
                2,
            )

        return swings


# ==========================================================
# LAST EXTERNAL BOS
# ==========================================================

    def _last_external_break(self, breaks):

        ext = [
            b for b in breaks
            if b.external
        ]

        if not ext:
            return None

        return ext[-1]


# ==========================================================
# TREND FROM BOS
# ==========================================================

    def _trend_from_breaks(self, breaks):

        last = self._last_external_break(breaks)

        if last is None:
            return "neutral"

        return last.direction


# ==========================================================
# TRADE FILTER
# ==========================================================

    def _trade_allowed(
        self,
        score,
        trend,
    ):

        if score < 60:
            return False

        if trend == "neutral":
            return False

        return True


# ==========================================================
# TRADE SIDE
# ==========================================================

    def _trade_side(
        self,
        trend,
    ):

        if trend == "bullish":
            return "BUY"

        if trend == "bearish":
            return "SELL"

        return ""
