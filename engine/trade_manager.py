# ============================================================
# TRADE MANAGER V2.0
# ============================================================

from .models import (
    DecisionResult,
    TradeResult
)


class TradeManager:

    def __init__(
        self,
        execution_engine,
        risk_filter
    ):
        self.execution = execution_engine
        self.risk = risk_filter

    # ======================================================
    # POSITION SIZE
    # ======================================================

    def calculate_position_size(
        self,
        entry,
        risk_usdt,
        leverage
    ):
        if entry <= 0:
            return 0

        qty = (
            risk_usdt *
            leverage
        ) / entry

        return round(qty, 6)

    # ======================================================
    # STOP LOSS
    # ======================================================

    def calculate_stop_loss(
        self,
        side,
        entry,
        atr,
        multiplier
    ):
        if side == "BUY":
            return round(
                entry -
                atr * multiplier,
                6
            )

        return round(
            entry +
            atr * multiplier,
            6
        )

    # ======================================================
    # TAKE PROFIT
    # ======================================================

    def calculate_take_profit(
        self,
        side,
        entry,
        stop,
        rr
    ):
        risk = abs(
            entry -
            stop
        )

        if side == "BUY":
            return round(
                entry +
                risk * rr,
                6
            )

        return round(
            entry -
            risk * rr,
            6
        )

    # ======================================================
    # BUILD SIGNAL
    # ======================================================

    def build_trade(
        self,
        symbol,
        decision,
        current_price,
        atr,
        config
    ):
        trade = TradeResult()

        trade.symbol = symbol
        trade.side = decision.side
        trade.entry_price = current_price
        trade.leverage = config["leverage"]

        trade.amount = self.calculate_position_size(
            current_price,
            config["risk_usdt"],
            config["leverage"]
        )

        trade.stop_loss = self.calculate_stop_loss(
            decision.side,
            current_price,
            atr,
            config["atr_multiplier"]
        )

        trade.take_profit = self.calculate_take_profit(
            decision.side,
            current_price,
            trade.stop_loss,
            config["reward_ratio"]
        )

        return trade

    # ======================================================
    # VALIDATE TRADE
    # ======================================================

    def validate_trade(
        self,
        trade
    ):
        if trade.symbol == "":
            return False, "Missing symbol"

        if trade.side not in [
            "BUY",
            "SELL"
        ]:
            return False, "Invalid side"

        if trade.amount <= 0:
            return False, "Invalid position size"

        if trade.entry_price <= 0:
            return False, "Invalid entry"

        if trade.stop_loss <= 0:
            return False, "Invalid stop loss"

        if trade.take_profit <= 0:
            return False, "Invalid take profit"

        return True, ""

    # ======================================================
    # RISK CHECK
    # ======================================================

    def check_risk(
        self,
        trade
    ):
        result = self.risk.validate(trade)

        if not result.allowed:
            return False, result.message

        return True, ""

    # ======================================================
    # EXECUTE
    # ======================================================

    def execute(
        self,
        trade
    ):
        valid, message = self.validate_trade(
            trade
        )

        if not valid:
            trade.success = False
            trade.message = message
            return trade

        valid, message = self.check_risk(
            trade
        )

        if not valid:
            trade.success = False
            trade.message = message
            return trade

        execution = self.execution.execute_trade(
            trade
        )

        return execution

    # ======================================================
    # PROCESS DECISION
    # ======================================================

    def process(
        self,
        symbol,
        decision,
        current_price,
        atr,
        config
    ):
        if not decision.allowed:
            result = TradeResult()
            result.success = False
            result.message = "Decision Engine rejected trade."
            return result

        trade = self.build_trade(
            symbol,
            decision,
            current_price,
            atr,
            config
        )

        return self.execute(
            trade
        )
