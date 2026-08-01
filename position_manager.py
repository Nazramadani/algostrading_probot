# ==========================================================
# POSITION MANAGER v2.0
# Position Monitoring Layer
# ==========================================================

import time
import logging

from typing import Dict, List, Optional

from .models import (
    PositionInfo,
    TradeResult
)

from .execution_engine import ExecutionEngine


class PositionManager:

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self, execution: ExecutionEngine):

        self.execution = execution

        self.positions: Dict[str, PositionInfo] = {}

        self.last_update = 0.0

        self.refresh_interval = 2.0

        self.logger = logging.getLogger("PositionManager")

        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:

            handler = logging.StreamHandler()

            formatter = logging.Formatter(

                "[%(asctime)s] %(levelname)s - %(message)s"

            )

            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

        self.sync()

    # ======================================================
    # LOG
    # ======================================================

    def log(
        self,
        message: str
    ):

        self.logger.info(message)

    # ======================================================
    # SYNC POSITIONS
    # ======================================================

    def sync(self):

        positions = self.execution.fetch_positions()

        self.positions.clear()

        for position in positions:

            self.positions[position.symbol] = position

        self.last_update = time.time()

        return list(self.positions.values())

    # ======================================================
    # AUTO REFRESH
    # ======================================================

    def refresh(self):

        now = time.time()

        if now - self.last_update >= self.refresh_interval:

            self.sync()

    # ======================================================
    # FORCE REFRESH
    # ======================================================

    def force_refresh(self):

        return self.sync()

    # ======================================================
    # CLEAR CACHE
    # ======================================================

    def clear(self):

        self.positions.clear()

    # ======================================================
    # POSITION COUNT
    # ======================================================

    def count(self):

        self.refresh()

        return len(self.positions)

    # ======================================================
    # HAS POSITIONS
    # ======================================================

    def has_positions(self):

        self.refresh()

        return len(self.positions) > 0

    # ======================================================
    # ALL POSITIONS
    # ======================================================

    def all_positions(self):

        self.refresh()

        return list(self.positions.values())

    # ======================================================
    # POSITION EXISTS
    # ======================================================

    def exists(
        self,
        symbol: str
    ):

        self.refresh()

        return symbol in self.positions

    # ======================================================
    # GET POSITION
    # ======================================================

    def get(
        self,
        symbol: str
    ) -> Optional[PositionInfo]:

        self.refresh()

        return self.positions.get(symbol)

    # ======================================================
    # REMOVE POSITION
    # ======================================================

    def remove(
        self,
        symbol: str
    ):

        if symbol in self.positions:

            del self.positions[symbol]

    # ======================================================
    # UPDATE CACHE
    # ======================================================

    def update_cache(
        self,
        position: PositionInfo
    ):

        self.positions[position.symbol] = position

    # ======================================================
    # LAST UPDATE
    # ======================================================

    def last_sync(self):

        return self.last_update

    # ======================================================
    # IS STALE
    # ======================================================

    def stale(self):

        return (

            time.time() - self.last_update

        ) > self.refresh_interval

    # ======================================================
    # EXPORT
    # ======================================================

    def to_dict(self):

        return {

            "positions": [

                vars(position)

                for position in self.positions.values()

            ],

            "count": len(self.positions),

            "last_update": self.last_update

        }

    # ======================================================
    # POSITION SIDE
    # ======================================================

    def position_side(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return ""

        return position.side.upper()

    # ======================================================
    # IS LONG
    # ======================================================

    def is_long(
        self,
        symbol: str
    ):

        return self.position_side(symbol) == "LONG"

    # ======================================================
    # IS SHORT
    # ======================================================

    def is_short(
        self,
        symbol: str
    ):

        return self.position_side(symbol) == "SHORT"

    # ======================================================
    # ENTRY PRICE
    # ======================================================

    def entry_price(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.entry)

    # ======================================================
    # MARK PRICE
    # ======================================================

    def mark_price(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.mark)

    # ======================================================
    # POSITION SIZE
    # ======================================================

    def position_size(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.quantity)

    # ======================================================
    # POSITION VALUE
    # ======================================================

    def position_value(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return round(

            position.quantity *

            position.mark,

            2

        )

    # ======================================================
    # LEVERAGE
    # ======================================================

    def leverage(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0

        return int(position.leverage)

    # ======================================================
    # MARGIN
    # ======================================================

    def margin(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.margin)

    # ======================================================
    # PNL
    # ======================================================

    def pnl(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.pnl)

    # ======================================================
    # ROE
    # ======================================================

    def roe(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.roe)

    # ======================================================
    # LIQUIDATION PRICE
    # ======================================================

    def liquidation_price(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return float(position.liquidation)

    # ======================================================
    # IS PROFITABLE
    # ======================================================

    def is_profitable(
        self,
        symbol: str
    ):

        return self.pnl(symbol) > 0

    # ======================================================
    # IS LOSING
    # ======================================================

    def is_losing(
        self,
        symbol: str
    ):

        return self.pnl(symbol) < 0

    # ======================================================
    # PROFIT PERCENT
    # ======================================================

    def profit_percent(
        self,
        symbol: str
    ):

        margin = self.margin(symbol)

        if margin <= 0:

            return 0.0

        pnl = self.pnl(symbol)

        return round(

            pnl /

            margin *

            100,

            2

        )

    # ======================================================
    # LOSS PERCENT
    # ======================================================

    def loss_percent(
        self,
        symbol: str
    ):

        value = self.profit_percent(symbol)

        if value >= 0:

            return 0.0

        return abs(value)

    # ======================================================
    # MOVE STOP LOSS
    # ======================================================

    def move_stop_loss(
        self,
        symbol: str,
        new_stop: float
    ):

        position = self.get(symbol)

        if position is None:

            return False

        return self.execution.modify_stop_loss(

            symbol,

            new_stop

        )

    # ======================================================
    # MOVE TAKE PROFIT
    # ======================================================

    def move_take_profit(
        self,
        symbol: str,
        new_tp: float
    ):

        position = self.get(symbol)

        if position is None:

            return False

        return self.execution.modify_take_profit(

            symbol,

            new_tp

        )

    # ======================================================
    # BREAK EVEN PRICE
    # ======================================================

    def break_even_price(
        self,
        symbol: str
    ):

        return self.entry_price(symbol)

    # ======================================================
    # MOVE TO BREAK EVEN
    # ======================================================

    def move_break_even(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return False

        return self.move_stop_loss(

            symbol,

            position.entry

        )

    # ======================================================
    # LOCK PROFIT
    # ======================================================

    def lock_profit(
        self,
        symbol: str,
        percent: float = 0.25
    ):

        position = self.get(symbol)

        if position is None:

            return False

        entry = position.entry

        mark = position.mark

        side = position.side.upper()

        move = abs(

            mark - entry

        ) * percent

        if side == "LONG":

            stop = entry + move

        else:

            stop = entry - move

        return self.move_stop_loss(

            symbol,

            stop

        )

    # ======================================================
    # STOP DISTANCE
    # ======================================================

    def stop_distance(
        self,
        symbol: str,
        stop_price: float
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return abs(

            position.mark -

            stop_price

        )

    # ======================================================
    # RISK DISTANCE
    # ======================================================

    def risk_distance(
        self,
        symbol: str,
        stop_price: float
    ):

        position = self.get(symbol)

        if position is None:

            return 0.0

        return abs(

            position.entry -

            stop_price

        )

    # ======================================================
    # TRAILING STOP
    # ======================================================

    def trailing_stop(
        self,
        symbol: str,
        trail_distance: float
    ):

        position = self.get(symbol)

        if position is None:

            return False

        side = position.side.upper()

        if side == "LONG":

            new_stop = position.mark - trail_distance

        else:

            new_stop = position.mark + trail_distance

        return self.move_stop_loss(

            symbol,

            new_stop

        )

    # ======================================================
    # ATR TRAILING STOP
    # ======================================================

    def atr_trailing_stop(
        self,
        symbol: str,
        atr: float,
        multiplier: float = 2.0
    ):

        distance = atr * multiplier

        return self.trailing_stop(

            symbol,

            distance

        )

    # ======================================================
    # CLOSE POSITION
    # ======================================================

    def close_position(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return False

        return self.execution.close_position(

            symbol

        )

    # ======================================================
    # PARTIAL CLOSE
    # ======================================================

    def partial_close(
        self,
        symbol: str,
        percent: float
    ):

        position = self.get(symbol)

        if position is None:

            return False

        percent = max(

            0,

            min(percent, 100)

        )

        amount = (

            position.quantity *

            percent /

            100

        )

        return self.execution.partial_close(

            symbol,

            amount

        )

    # ======================================================
    # CLOSE 25%
    # ======================================================

    def close_25(
        self,
        symbol: str
    ):

        return self.partial_close(

            symbol,

            25

        )

    # ======================================================
    # CLOSE 50%
    # ======================================================

    def close_half(
        self,
        symbol: str
    ):

        return self.partial_close(

            symbol,

            50

        )

    # ======================================================
    # CLOSE 75%
    # ======================================================

    def close_75(
        self,
        symbol: str
    ):

        return self.partial_close(

            symbol,

            75

        )

    # ======================================================
    # CLOSE ALL
    # ======================================================

    def close_all(
        self
    ):

        results = []

        for symbol in self.symbols():

            results.append(

                self.close_position(

                    symbol

                )

            )

        return results

    # ======================================================
    # EMERGENCY CLOSE
    # ======================================================

    def emergency_close(
        self
    ):

        self.execution.cancel_all_orders()

        return self.close_all()

    # ======================================================
    # REVERSE POSITION
    # ======================================================

    def reverse_position(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return False

        quantity = position.quantity

        if not self.close_position(symbol):

            return False

        if position.side.upper() == "LONG":

            side = "SELL"

        else:

            side = "BUY"

        return self.execution.market_order(

            symbol=symbol,

            side=side,

            amount=quantity

        )

    # ======================================================
    # HAS OPEN POSITIONS
    # ======================================================

    def has_positions(
        self
    ):

        return len(

            self.positions

        ) > 0

    # ======================================================
    # POSITION COUNT
    # ======================================================

    def position_count(
        self
    ):

        return len(

            self.positions

        )

    # ======================================================
    # SYMBOL LIST
    # ======================================================

    def symbols(
        self
    ):

        return list(

            self.positions.keys()

        )

    # ======================================================
    # CLEAR CACHE
    # ======================================================

    def clear(
        self
    ):

        self.positions.clear()

    # ======================================================
    # AUTO BREAK EVEN
    # ======================================================

    def auto_break_even(
        self,
        symbol: str,
        trigger_rr: float = 1.0
    ):

        position = self.get(symbol)

        if position is None:

            return False

        if position.stop_loss <= 0:

            return False

        risk = abs(

            position.entry -

            position.stop_loss

        )

        reward = abs(

            position.mark -

            position.entry

        )

        if risk <= 0:

            return False

        rr = reward / risk

        if rr >= trigger_rr:

            return self.move_break_even(

                symbol

            )

        return False

    # ======================================================
    # AUTO TRAILING STOP
    # ======================================================

    def auto_trailing_stop(
        self,
        symbol: str,
        atr: float,
        multiplier: float = 2.0
    ):

        position = self.get(symbol)

        if position is None:

            return False

        return self.atr_trailing_stop(

            symbol,

            atr,

            multiplier

        )

    # ======================================================
    # AUTO LOCK PROFIT
    # ======================================================

    def auto_lock_profit(
        self,
        symbol: str,
        trigger_rr: float = 2.0,
        percent: float = 0.30
    ):

        position = self.get(symbol)

        if position is None:

            return False

        risk = abs(

            position.entry -

            position.stop_loss

        )

        reward = abs(

            position.mark -

            position.entry

        )

        if risk <= 0:

            return False

        rr = reward / risk

        if rr >= trigger_rr:

            return self.lock_profit(

                symbol,

                percent

            )

        return False

    # ======================================================
    # AUTO PARTIAL TAKE PROFIT
    # ======================================================

    def auto_partial_tp(
        self,
        symbol: str,
        trigger_rr: float = 2.0,
        close_percent: float = 50
    ):

        position = self.get(symbol)

        if position is None:

            return False

        risk = abs(

            position.entry -

            position.stop_loss

        )

        reward = abs(

            position.mark -

            position.entry

        )

        if risk <= 0:

            return False

        rr = reward / risk

        if rr >= trigger_rr:

            return self.partial_close(

                symbol,

                close_percent

            )

        return False

    # ======================================================
    # POSITION HEALTH SCORE
    # ======================================================

    def health_score(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return 0

        score = 50

        if position.pnl > 0:

            score += 20

        if position.roe > 5:

            score += 10

        if position.roe > 10:

            score += 10

        if position.margin > 0:

            score += 10

        return min(

            score,

            100

        )

    # ======================================================
    # POSITION IS HEALTHY
    # ======================================================

    def is_healthy(
        self,
        symbol: str
    ):

        return self.health_score(

            symbol

        ) >= 70

    # ======================================================
    # POSITION RISK
    # ======================================================

    def risk_level(
        self,
        symbol: str
    ):

        position = self.get(symbol)

        if position is None:

            return "UNKNOWN"

        if position.roe <= -10:

            return "HIGH"

        if position.roe <= -5:

            return "MEDIUM"

        return "LOW"

    # ======================================================
    # MONITOR POSITION
    # ======================================================

    def monitor_position(
        self,
        symbol: str,
        atr: float
    ):

        self.auto_break_even(

            symbol

        )

        self.auto_lock_profit(

            symbol

        )

        self.auto_partial_tp(

            symbol

        )

        self.auto_trailing_stop(

            symbol,

            atr

        )

        return True

    # ======================================================
    # MONITOR ALL POSITIONS
    # ======================================================

    def monitor_all_positions(
        self,
        atr_map: dict
    ):

        for symbol in self.symbols():

            atr = atr_map.get(symbol)

            if atr is None:

                continue

            self.monitor_position(

                symbol,

                atr

            )

    # ======================================================
    # SYNC POSITIONS
    # ======================================================

    def sync_positions(self):

        positions = self.execution.fetch_positions()

        self.positions.clear()

        for position in positions:

            self.positions[

                position.symbol

            ] = position

        return len(

            self.positions

        )

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self):

        return self.sync_positions()

    # ======================================================
    # TOTAL OPEN RISK
    # ======================================================

    def total_open_risk(self):

        risk = 0.0

        for position in self.positions.values():

            if position.stop_loss <= 0:

                continue

            risk += abs(

                position.entry -

                position.stop_loss

            ) * position.quantity

        return round(

            risk,

            2

        )

    # ======================================================
    # TOTAL UNREALIZED PNL
    # ======================================================

    def total_pnl(self):

        pnl = 0.0

        for position in self.positions.values():

            pnl += position.pnl

        return round(

            pnl,

            2

        )

    # ======================================================
    # TOTAL MARGIN
    # ======================================================

    def total_margin(self):

        margin = 0.0

        for position in self.positions.values():

            margin += position.margin

        return round(

            margin,

            2

        )

    # ======================================================
    # PORTFOLIO EXPOSURE
    # ======================================================

    def portfolio_exposure(self):

        exposure = 0.0

        for position in self.positions.values():

            exposure += (

                position.mark *

                position.quantity

            )

        return round(

            exposure,

            2

        )

    # ======================================================
    # MAX POSITIONS CHECK
    # ======================================================

    def can_open_new_position(
        self,
        maximum: int = 5
    ):

        return self.position_count() < maximum

    # ======================================================
    # MAX DRAWDOWN CHECK
    # ======================================================

    def drawdown_alert(
        self,
        limit=-10
    ):

        total = 0

        for position in self.positions.values():

            total += position.roe

        return total <= limit

    # ======================================================
    # RISK ALERTS
    # ======================================================

    def risk_alerts(self):

        alerts = []

        if self.position_count() >= 5:

            alerts.append(

                "Maximum positions reached."

            )

        if self.total_open_risk() > 500:

            alerts.append(

                "Open risk is high."

            )

        if self.drawdown_alert():

            alerts.append(

                "Portfolio drawdown exceeded."

            )

        return alerts

    # ======================================================
    # PORTFOLIO SUMMARY
    # ======================================================

    def portfolio_summary(self):

        return {

            "positions":

                self.position_count(),

            "symbols":

                self.symbols(),

            "open_risk":

                self.total_open_risk(),

            "margin":

                self.total_margin(),

            "exposure":

                self.portfolio_exposure(),

            "pnl":

                self.total_pnl(),

            "alerts":

                self.risk_alerts()

        }