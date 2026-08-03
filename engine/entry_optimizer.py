# ==========================================================
# SMC ENTRY OPTIMIZER v2.0
# ==========================================================

from dataclasses import dataclass


# ==========================================================
# RESULT
# ==========================================================

@dataclass
class EntryResult:

    valid: bool = False

    side: str = ""

    entry: float = 0.0

    stop_loss: float = 0.0

    take_profit: float = 0.0

    risk: float = 0.0

    reward: float = 0.0

    rr: float = 0.0

    score: float = 0.0

    reason: str = ""


# ==========================================================
# ENGINE
# ==========================================================

class EntryOptimizer:

    def __init__(self):

        self.minimum_rr = 2.0

        self.maximum_sl_atr = 2.5

        self.minimum_tp_atr = 3.0

    # ======================================================
    # MAIN
    # ======================================================

    def analyze(

        self,

        side,

        entry,

        atr,

        nearest_fvg,

        nearest_ob,

        liquidity_level

    ):

        result = EntryResult()

        result.side = side

        result.entry = entry

        if side == "BUY":

            stop = self.buy_stop(

                entry,

                atr,

                nearest_ob,

                liquidity_level

            )

            tp = self.buy_tp(

                entry,

                atr,

                nearest_fvg

            )

        else:

            stop = self.sell_stop(

                entry,

                atr,

                nearest_ob,

                liquidity_level

            )

            tp = self.sell_tp(

                entry,

                atr,

                nearest_fvg

            )

        result.stop_loss = stop

        result.take_profit = tp

        result.risk = abs(

            entry -

            stop

        )

        result.reward = abs(

            tp -

            entry

        )

        if result.risk == 0:

            return result

        result.rr = round(

            result.reward /

            result.risk,

            2

        )

        result.valid = (

            result.rr >=

            self.minimum_rr

        )

        result.score = self.score(

            result.rr

        )

        result.reason = self.reason(

            result

        )

        return result

    # ======================================================
    # BUY STOP
    # ======================================================

    def buy_stop(

        self,

        entry,

        atr,

        ob,

        liquidity

    ):

        stop = entry - atr * 1.2

        if ob:

            stop = min(

                stop,

                ob.low

            )

        if liquidity:

            stop = min(

                stop,

                liquidity.price

            )

        return stop

    # ======================================================
    # SELL STOP
    # ======================================================

    def sell_stop(

        self,

        entry,

        atr,

        ob,

        liquidity

    ):

        stop = entry + atr * 1.2

        if ob:

            stop = max(

                stop,

                ob.high

            )

        if liquidity:

            stop = max(

                stop,

                liquidity.price

            )

        return stop

    # ======================================================
    # BUY TP
    # ======================================================

    def buy_tp(

        self,

        entry,

        atr,

        fvg

    ):

        if fvg:

            return fvg.top

        return entry + atr * 4

    # ======================================================
    # SELL TP
    # ======================================================

    def sell_tp(

        self,

        entry,

        atr,

        fvg

    ):

        if fvg:

            return fvg.bottom

        return entry - atr * 4

    # ======================================================
    # SCORE
    # ======================================================

    def score(

        self,

        rr

    ):

        if rr >= 5:

            return 100

        if rr >= 4:

            return 95

        if rr >= 3:

            return 90

        if rr >= 2.5:

            return 85

        if rr >= 2:

            return 75

        return 50

    # ======================================================
    # REASON
    # ======================================================

    def reason(

        self,

        result

    ):

        if not result.valid:

            return "Risk Reward too low"

        return f"RR {result.rr}"
