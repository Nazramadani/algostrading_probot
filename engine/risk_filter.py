# ==========================================================
# SMC RISK FILTER ENGINE v1.0
# ==========================================================

from dataclasses import dataclass
from typing import List

import numpy as np


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class RiskFilterResult:

    passed: bool = False

    score: float = 100.0

    penalty: float = 0.0

    rr: float = 0.0

    atr: float = 0.0

    volatility: float = 0.0

    reasons: List[str] = None

    def __post_init__(self):

        if self.reasons is None:
            self.reasons = []


# ==========================================================
# ENGINE
# ==========================================================

class RiskFilterEngine:

    def __init__(

        self,

        minimum_rr=2.0,

        minimum_atr_ratio=0.60,

        maximum_atr_ratio=2.00,

        max_body_percent=0.90,

        max_range_atr=3.00

    ):

        self.minimum_rr = minimum_rr

        self.minimum_atr_ratio = minimum_atr_ratio

        self.maximum_atr_ratio = maximum_atr_ratio

        self.max_body_percent = max_body_percent

        self.max_range_atr = max_range_atr

    # ======================================================
    # MAIN
    # ======================================================

    def analyze(

        self,

        df,

        entry,

        stop,

        take_profit

    ):

        result = RiskFilterResult()

        result.rr = self.calculate_rr(

            entry,

            stop,

            take_profit

        )

        rr_ok = self.check_rr(

            result,

            result.rr

        )

        atr_ok = self.check_atr(

            result,

            df

        )

        vol_ok = self.check_volatility(

            result,

            df

        )

        result.passed = (

            rr_ok and

            atr_ok and

            vol_ok

        )

        result.score = max(

            0,

            100 - result.penalty

        )

        return result

    # ======================================================
    # RR
    # ======================================================

    def calculate_rr(

        self,

        entry,

        stop,

        tp

    ):

        risk = abs(entry - stop)

        reward = abs(tp - entry)

        if risk == 0:

            return 0

        return reward / risk

    def check_rr(

        self,

        result,

        rr

    ):

        if rr < self.minimum_rr:

            result.penalty += 35

            result.reasons.append(

                f"Low RR ({rr:.2f})"

            )

            return False

        return True

    # ======================================================
    # ATR
    # ======================================================

    def check_atr(

        self,

        result,

        df

    ):

        if "atr" not in df.columns:

            return True

        atr = float(

            df["atr"].iloc[-1]

        )

        atr_avg = float(

            df["atr"]

            .rolling(20)

            .mean()

            .iloc[-1]

        )

        result.atr = atr

        if atr_avg == 0:

            return True

        ratio = atr / atr_avg

        if ratio < self.minimum_atr_ratio:

            result.penalty += 20

            result.reasons.append(

                "ATR too low"

            )

            return False

        if ratio > self.maximum_atr_ratio:

            result.penalty += 15

            result.reasons.append(

                "ATR extremely high"

            )

        return True

    # ======================================================
    # VOLATILITY
    # ======================================================

    def check_volatility(

        self,

        result,

        df

    ):

        last = df.iloc[-1]

        body = abs(

            last["close"] -

            last["open"]

        )

        candle_range = (

            last["high"] -

            last["low"]

        )

        if candle_range == 0:

            return True

        body_percent = body / candle_range

        result.volatility = body_percent

        if body_percent > self.max_body_percent:

            result.penalty += 15

            result.reasons.append(

                "Momentum candle"

            )

        if "atr" in df.columns:

            if candle_range > (

                last["atr"] *

                self.max_range_atr

            ):

                result.penalty += 20

                result.reasons.append(

                    "Huge volatility"

                )

        return True
