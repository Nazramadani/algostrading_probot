# ==========================================================
# EXECUTION ENGINE v2.0
# Binance Futures Execution Layer
# ==========================================================

import time
import math
import logging
from typing import Optional, Dict, List

import ccxt

from .models import (
    TradeSignal,
    TradeResult,
    PositionInfo
)


class ExecutionEngine:

    # ======================================================
    # INIT
    # ======================================================

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):

        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        self.exchange = None

        self.positions: Dict[str, PositionInfo] = {}

        self.orders = {}

        self.logger = logging.getLogger("ExecutionEngine")

        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:

            handler = logging.StreamHandler()

            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(message)s"
            )

            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

        self._connect()

    # ======================================================
    # CONNECT
    # ======================================================

    def _connect(self):

        self.exchange = ccxt.binanceusdm({

            "apiKey": self.api_key,

            "secret": self.api_secret,

            "enableRateLimit": True,

            "options": {

                "defaultType": "future"

            }

        })

        if self.testnet:

            self.exchange.set_sandbox_mode(True)

        self.exchange.load_markets()

        self.logger.info("Connected to Binance Futures")

    # ======================================================
    # PING
    # ======================================================

    def ping(self):

        try:

            self.exchange.fetch_time()

            return True

        except Exception as e:

            self.logger.error(str(e))

            return False

    # ======================================================
    # SERVER TIME
    # ======================================================

    def server_time(self):

        try:

            return self.exchange.fetch_time()

        except:

            return 0

    # ======================================================
    # LOAD MARKETS
    # ======================================================

    def reload_markets(self):

        self.exchange.load_markets(True)

    # ======================================================
    # SYMBOL EXISTS
    # ======================================================

    def symbol_exists(
        self,
        symbol
    ):

        return symbol in self.exchange.markets

    # ======================================================
    # MARKET INFO
    # ======================================================

    def market(
        self,
        symbol
    ):

        return self.exchange.market(symbol)

    # ======================================================
    # PRICE PRECISION
    # ======================================================

    def price_precision(
        self,
        symbol
    ):

        market = self.market(symbol)

        return market["precision"]["price"]

    # ======================================================
    # AMOUNT PRECISION
    # ======================================================

    def amount_precision(
        self,
        symbol
    ):

        market = self.market(symbol)

        return market["precision"]["amount"]

    # ======================================================
    # ROUND PRICE
    # ======================================================

    def round_price(
        self,
        symbol,
        price
    ):

        return float(

            self.exchange.price_to_precision(

                symbol,

                price

            )

        )

    # ======================================================
    # ROUND AMOUNT
    # ======================================================

    def round_amount(
        self,
        symbol,
        amount
    ):

        return float(

            self.exchange.amount_to_precision(

                symbol,

                amount

            )

        )

    # ======================================================
    # MINIMUM AMOUNT
    # ======================================================

    def minimum_amount(
        self,
        symbol
    ):

        market = self.market(symbol)

        return market["limits"]["amount"]["min"]

    # ======================================================
    # MINIMUM COST
    # ======================================================

    def minimum_cost(
        self,
        symbol
    ):

        market = self.market(symbol)

        value = market["limits"]["cost"]

        if value is None:

            return 0

        return value["min"]

    # ======================================================
    # CURRENT PRICE
    # ======================================================

    def current_price(
        self,
        symbol
    ):

        ticker = self.exchange.fetch_ticker(symbol)

        return float(ticker["last"])

    # ======================================================
    # MARK PRICE
    # ======================================================

    def mark_price(
        self,
        symbol
    ):

        ticker = self.exchange.fetch_ticker(symbol)

        if "markPrice" in ticker["info"]:

            return float(

                ticker["info"]["markPrice"]

            )

        return float(

            ticker["last"]

        )

    # ======================================================
    # ACCOUNT INFO
    # ======================================================

    def account(self):

        return self.exchange.fetch_balance()

    # ======================================================
    # FUTURES BALANCE
    # ======================================================

    def futures_balance(self):

        balance = self.exchange.fetch_balance()

        if "USDT" not in balance:

            return {}

        return balance["USDT"]

    # ======================================================
    # TOTAL BALANCE
    # ======================================================

    def total_balance(self):

        wallet = self.futures_balance()

        return float(

            wallet.get(

                "total",

                0

            )

        )

    # ======================================================
    # FREE BALANCE
    # ======================================================

    def free_balance(self):

        wallet = self.futures_balance()

        return float(

            wallet.get(

                "free",

                0

            )

        )

    # ======================================================
    # USED BALANCE
    # ======================================================

    def used_balance(self):

        wallet = self.futures_balance()

        return float(

            wallet.get(

                "used",

                0

            )

        )

    # ======================================================
    # CHECK BALANCE
    # ======================================================

    def has_balance(
        self,
        amount
    ):

        return self.free_balance() >= amount

    # ======================================================
    # LEVERAGE
    # ======================================================

    def set_leverage(
        self,
        symbol,
        leverage
    ):

        leverage = int(leverage)

        self.exchange.set_leverage(

            leverage,

            symbol

        )

        self.logger.info(

            f"{symbol} leverage -> {leverage}x"

        )

    # ======================================================
    # MARGIN MODE
    # ======================================================

    def set_margin_mode(
        self,
        symbol,
        mode="ISOLATED"
    ):

        try:

            self.exchange.set_margin_mode(

                mode,

                symbol

            )

        except Exception:

            pass

    # ======================================================
    # POSITION MODE
    # ======================================================

    def set_oneway_mode(self):

        try:

            self.exchange.set_position_mode(

                False

            )

        except Exception:

            pass

    # ======================================================
    # HEDGE MODE
    # ======================================================

    def set_hedge_mode(self):

        try:

            self.exchange.set_position_mode(

                True

            )

        except Exception:

            pass

    # ======================================================
    # CURRENT LEVERAGE
    # ======================================================

    def current_leverage(
        self,
        symbol
    ):

        positions = self.exchange.fetch_positions(

            [symbol]

        )

        if not positions:

            return 0

        return int(

            positions[0].get(

                "leverage",

                0

            )

        )

    # ======================================================
    # MARKET PRICE
    # ======================================================

    def bid_ask(
        self,
        symbol
    ):

        ticker = self.exchange.fetch_ticker(

            symbol

        )

        return (

            float(ticker["bid"]),

            float(ticker["ask"])

        )

    # ======================================================
    # VALIDATE SYMBOL
    # ======================================================

    def validate_symbol(
        self,
        symbol
    ):

        if not self.symbol_exists(symbol):

            raise Exception(

                f"Unknown symbol {symbol}"

            )

    # ======================================================
    # VALIDATE AMOUNT
    # ======================================================

    def validate_amount(
        self,
        symbol,
        amount
    ):

        minimum = self.minimum_amount(

            symbol

        )

        if amount < minimum:

            raise Exception(

                f"Minimum amount is {minimum}"

            )

    # ======================================================
    # VALIDATE PRICE
    # ======================================================

    def validate_price(
        self,
        price
    ):

        if price <= 0:

            raise Exception(

                "Invalid price"

            )

    # ======================================================
    # EXCHANGE INFO
    # ======================================================

    def exchange_info(self):

        return {

            "exchange": "Binance Futures",

            "sandbox": self.testnet,

            "connected": self.ping(),

            "markets": len(

                self.exchange.markets

            )

        }

    # ======================================================
    # LOG
    # ======================================================

    def log(
        self,
        message
    ):

        self.logger.info(message)

    # ======================================================
    # FETCH POSITIONS
    # ======================================================

    def fetch_positions(
        self,
        symbols=None
    ):

        try:

            positions = self.exchange.fetch_positions(

                symbols

            )

            self.positions.clear()

            for p in positions:

                contracts = float(

                    p.get(

                        "contracts",

                        0

                    )

                )

                if contracts <= 0:

                    continue

                info = PositionInfo(

                    symbol=p["symbol"],

                    side=p["side"],

                    entry=float(

                        p.get(

                            "entryPrice",

                            0

                        )

                    ),

                    mark=float(

                        p.get(

                            "markPrice",

                            0

                        )

                    ),

                    quantity=contracts,

                    leverage=int(

                        p.get(

                            "leverage",

                            0

                        )

                    ),

                    pnl=float(

                        p.get(

                            "unrealizedPnl",

                            0

                        )

                    ),

                    liquidation=float(

                        p.get(

                            "liquidationPrice",

                            0

                        )

                    ),

                    margin=float(

                        p.get(

                            "initialMargin",

                            0

                        )

                    )

                )

                self.positions[

                    info.symbol

                ] = info

            return list(

                self.positions.values()

            )

        except Exception as e:

            self.logger.error(str(e))

            return []

    # ======================================================
    # POSITION
    # ======================================================

    def position(
        self,
        symbol
    ):

        if symbol not in self.positions:

            self.fetch_positions([symbol])

        return self.positions.get(symbol)

    # ======================================================
    # HAS POSITION
    # ======================================================

    def has_position(
        self,
        symbol
    ):

        return self.position(symbol) is not None

    # ======================================================
    # POSITION SIDE
    # ======================================================

    def position_side(
        self,
        symbol
    ):

        pos = self.position(symbol)

        if pos is None:

            return ""

        return pos.side.upper()

    # ======================================================
    # POSITION SIZE
    # ======================================================

    def position_size(
        self,
        symbol
    ):

        pos = self.position(symbol)

        if pos is None:

            return 0.0

        return pos.quantity

    # ======================================================
    # OPEN ORDERS
    # ======================================================

    def open_orders(
        self,
        symbol=None
    ):

        return self.exchange.fetch_open_orders(

            symbol

        )

    # ======================================================
    # OPEN ORDER COUNT
    # ======================================================

    def open_order_count(
        self,
        symbol=None
    ):

        return len(

            self.open_orders(symbol)

        )

    # ======================================================
    # CANCEL ORDER
    # ======================================================

    def cancel_order(
        self,
        order_id,
        symbol
    ):

        return self.exchange.cancel_order(

            order_id,

            symbol

        )

    # ======================================================
    # CANCEL ALL
    # ======================================================

    def cancel_all(
        self,
        symbol
    ):

        orders = self.open_orders(

            symbol

        )

        for order in orders:

            try:

                self.cancel_order(

                    order["id"],

                    symbol

                )

            except Exception:

                pass

    # ======================================================
    # CLOSE ALL ORDERS
    # ======================================================

    def clear_orders(
        self,
        symbol
    ):

        self.cancel_all(symbol)

        self.logger.info(

            f"Orders cleared -> {symbol}"

        )

    # ======================================================
    # ORDER EXISTS
    # ======================================================

    def order_exists(
        self,
        order_id,
        symbol
    ):

        orders = self.open_orders(symbol)

        for order in orders:

            if order["id"] == order_id:

                return True

        return False

    # ======================================================
    # EXCHANGE STATUS
    # ======================================================

    def status(self):

        return {

            "connected": self.ping(),

            "balance": self.free_balance(),

            "positions": len(

                self.positions

            ),

            "orders": len(

                self.open_orders()

            )

        }

    # ======================================================
    # CREATE MARKET ORDER
    # ======================================================

    def create_market_order(
        self,
        symbol,
        side,
        amount,
        reduce_only=False
    ):

        self.validate_symbol(symbol)

        self.validate_amount(

            symbol,

            amount

        )

        amount = self.round_amount(

            symbol,

            amount

        )

        order = self.exchange.create_order(

            symbol=symbol,

            type="market",

            side=side.lower(),

            amount=amount,

            params={

                "reduceOnly": reduce_only

            }

        )

        self.logger.info(

            f"MARKET {side.upper()} {symbol} {amount}"

        )

        return order

    # ======================================================
    # CREATE LIMIT ORDER
    # ======================================================

    def create_limit_order(
        self,
        symbol,
        side,
        amount,
        price,
        reduce_only=False
    ):

        self.validate_symbol(symbol)

        self.validate_amount(

            symbol,

            amount

        )

        self.validate_price(price)

        amount = self.round_amount(

            symbol,

            amount

        )

        price = self.round_price(

            symbol,

            price

        )

        order = self.exchange.create_order(

            symbol=symbol,

            type="limit",

            side=side.lower(),

            amount=amount,

            price=price,

            params={

                "reduceOnly": reduce_only,

                "timeInForce": "GTC"

            }

        )

        self.logger.info(

            f"LIMIT {side.upper()} {symbol} {amount} @ {price}"

        )

        return order

    # ======================================================
    # CREATE STOP MARKET
    # ======================================================

    def create_stop_market(
        self,
        symbol,
        side,
        amount,
        stop_price
    ):

        amount = self.round_amount(

            symbol,

            amount

        )

        stop_price = self.round_price(

            symbol,

            stop_price

        )

        return self.exchange.create_order(

            symbol=symbol,

            type="STOP_MARKET",

            side=side.lower(),

            amount=amount,

            price=None,

            params={

                "stopPrice": stop_price,

                "reduceOnly": True

            }

        )

    # ======================================================
    # CREATE TAKE PROFIT MARKET
    # ======================================================

    def create_take_profit_market(
        self,
        symbol,
        side,
        amount,
        stop_price
    ):

        amount = self.round_amount(

            symbol,

            amount

        )

        stop_price = self.round_price(

            symbol,

            stop_price

        )

        return self.exchange.create_order(

            symbol=symbol,

            type="TAKE_PROFIT_MARKET",

            side=side.lower(),

            amount=amount,

            price=None,

            params={

                "stopPrice": stop_price,

                "reduceOnly": True

            }

        )

    # ======================================================
    # WAIT UNTIL FILLED
    # ======================================================

    def wait_until_filled(
        self,
        symbol,
        order_id,
        timeout=20
    ):

        start = time.time()

        while time.time() - start < timeout:

            try:

                order = self.exchange.fetch_order(

                    order_id,

                    symbol

                )

                status = order.get(

                    "status",

                    ""

                ).lower()

                if status == "closed":

                    return order

                if status == "canceled":

                    return order

            except Exception as e:

                self.logger.error(str(e))

            time.sleep(1)

        return None

    # ======================================================
    # AVERAGE FILL PRICE
    # ======================================================

    def average_fill_price(
        self,
        order,
        fallback_price
    ):

        if order is None:

            return fallback_price

        average = order.get("average")

        if average is not None:

            try:

                return float(average)

            except Exception:

                pass

        price = order.get("price")

        if price is not None:

            try:

                return float(price)

            except Exception:

                pass

        return fallback_price

    # ======================================================
    # EXECUTE TRADE
    # ======================================================

    def execute_trade(
        self,
        trade
    ):

        result = TradeResult()

        try:

            self.validate_symbol(

                trade.symbol

            )

            self.validate_amount(

                trade.symbol,

                trade.amount

            )

            self.set_margin_mode(

                trade.symbol,

                "ISOLATED"

            )

            self.set_oneway_mode()

            self.set_leverage(

                trade.symbol,

                trade.leverage

            )

            order = self.create_market_order(

                symbol=trade.symbol,

                side=trade.side,

                amount=trade.amount

            )

            order = self.wait_until_filled(

                trade.symbol,

                order["id"]

            )

            entry = self.average_fill_price(

                order,

                trade.entry_price

            )

            trade.entry_price = entry

            close_side = (

                "SELL"

                if trade.side == "BUY"

                else "BUY"

            )

            sl = self.create_stop_market(

                symbol=trade.symbol,

                side=close_side,

                amount=trade.amount,

                stop_price=trade.stop_loss

            )

            tp = self.create_take_profit_market(

                symbol=trade.symbol,

                side=close_side,

                amount=trade.amount,

                stop_price=trade.take_profit

            )

            result.success = True

            result.message = "Trade executed"

            result.order_id = order["id"]

            result.symbol = trade.symbol

            result.side = trade.side

            result.amount = trade.amount

            result.entry_price = entry

            result.stop_loss = trade.stop_loss

            result.take_profit = trade.take_profit

            result.leverage = trade.leverage

            self.orders[

                order["id"]

            ] = {

                "entry": order,

                "sl": sl,

                "tp": tp

            }

            self.logger.info(

                f"{trade.side} {trade.symbol} OPENED"

            )

            return result

        except Exception as e:

            result.success = False

            result.message = str(e)

            self.logger.error(str(e))

            return result

    # ======================================================
    # CLOSE POSITION
    # ======================================================

    def close_position(
        self,
        symbol
    ):

        position = self.position(symbol)

        if position is None:

            return False

        side = (

            "SELL"

            if position.side.upper() == "LONG"

            else "BUY"

        )

        order = self.create_market_order(

            symbol=symbol,

            side=side,

            amount=position.quantity,

            reduce_only=True

        )

        self.cancel_all(symbol)

        self.logger.info(

            f"Position closed -> {symbol}"

        )

        return order

    # ======================================================
    # CLOSE ALL POSITIONS
    # ======================================================

    def close_all_positions(self):

        closed = []

        positions = self.fetch_positions()

        for position in positions:

            try:

                result = self.close_position(

                    position.symbol

                )

                closed.append(result)

            except Exception as e:

                self.logger.error(

                    str(e)

                )

        return closed

    # ======================================================
    # PARTIAL CLOSE
    # ======================================================

    def partial_close(
        self,
        symbol,
        percent
    ):

        position = self.position(symbol)

        if position is None:

            return None

        percent = max(

            1,

            min(

                percent,

                100

            )

        )

        amount = (

            position.quantity *

            percent /

            100

        )

        amount = self.round_amount(

            symbol,

            amount

        )

        side = (

            "SELL"

            if position.side.upper() == "LONG"

            else "BUY"

        )

        order = self.create_market_order(

            symbol=symbol,

            side=side,

            amount=amount,

            reduce_only=True

        )

        self.logger.info(

            f"Partial Close {percent}% -> {symbol}"

        )

        return order

    # ======================================================
    # EMERGENCY CLOSE
    # ======================================================

    def emergency_close(
        self,
        symbol
    ):

        try:

            self.cancel_all(

                symbol

            )

        except Exception:

            pass

        try:

            return self.close_position(

                symbol

            )

        except Exception as e:

            self.logger.error(

                str(e)

            )

            return None

    # ======================================================
    # HAS OPEN POSITION
    # ======================================================

    def has_open_position(
        self,
        symbol
    ):

        position = self.position(

            symbol

        )

        if position is None:

            return False

        return position.quantity > 0

    # ======================================================
    # POSITION PNL
    # ======================================================

    def position_pnl(
        self,
        symbol
    ):

        position = self.position(

            symbol

        )

        if position is None:

            return 0.0

        return float(

            position.pnl

        )

    # ======================================================
    # POSITION ROI
    # ======================================================

    def position_roi(
        self,
        symbol
    ):

        position = self.position(

            symbol

        )

        if position is None:

            return 0.0

        if position.margin <= 0:

            return 0.0

        return round(

            (

                position.pnl /

                position.margin

            ) * 100,

            2

        )

    # ======================================================
    # UPDATE STOP LOSS
    # ======================================================

    def update_stop_loss(
        self,
        symbol,
        new_stop
    ):

        position = self.position(symbol)

        if position is None:

            return False

        self.cancel_all(symbol)

        side = (

            "SELL"

            if position.side.upper() == "LONG"

            else "BUY"

        )

        self.create_stop_market(

            symbol=symbol,

            side=side,

            amount=position.quantity,

            stop_price=new_stop

        )

        self.logger.info(

            f"Stop Loss updated -> {symbol} : {new_stop}"

        )

        return True

    # ======================================================
    # UPDATE TAKE PROFIT
    # ======================================================

    def update_take_profit(
        self,
        symbol,
        new_tp
    ):

        position = self.position(symbol)

        if position is None:

            return False

        orders = self.open_orders(symbol)

        for order in orders:

            try:

                if order["type"] == "take_profit_market":

                    self.cancel_order(

                        order["id"],

                        symbol

                    )

            except Exception:

                pass

        side = (

            "SELL"

            if position.side.upper() == "LONG"

            else "BUY"

        )

        self.create_take_profit_market(

            symbol=symbol,

            side=side,

            amount=position.quantity,

            stop_price=new_tp

        )

        self.logger.info(

            f"Take Profit updated -> {symbol} : {new_tp}"

        )

        return True

    # ======================================================
    # MOVE STOP TO BREAK EVEN
    # ======================================================

    def move_stop_to_break_even(
        self,
        symbol,
        offset=0
    ):

        position = self.position(symbol)

        if position is None:

            return False

        entry = position.entry

        if position.side.upper() == "LONG":

            new_stop = entry + offset

        else:

            new_stop = entry - offset

        return self.update_stop_loss(

            symbol,

            new_stop

        )

    # ======================================================
    # TRAILING STOP
    # ======================================================

    def trailing_stop(
        self,
        symbol,
        distance
    ):

        position = self.position(symbol)

        if position is None:

            return False

        mark = self.mark_price(symbol)

        if position.side.upper() == "LONG":

            stop = mark - distance

            if stop > position.stop_loss:

                return self.update_stop_loss(

                    symbol,

                    stop

                )

        else:

            stop = mark + distance

            if position.stop_loss == 0:

                return self.update_stop_loss(

                    symbol,

                    stop

                )

            if stop < position.stop_loss:

                return self.update_stop_loss(

                    symbol,

                    stop

                )

        return False

    # ======================================================
    # SCALE IN
    # ======================================================

    def scale_in(
        self,
        symbol,
        side,
        amount
    ):

        return self.create_market_order(

            symbol=symbol,

            side=side,

            amount=amount,

            reduce_only=False

        )

    # ======================================================
    # SCALE OUT
    # ======================================================

    def scale_out(
        self,
        symbol,
        percent
    ):

        return self.partial_close(

            symbol,

            percent

        )

    # ======================================================
    # SYNC OPEN ORDERS
    # ======================================================

    def sync_orders(
        self,
        symbol=None
    ):

        try:

            orders = self.exchange.fetch_open_orders(

                symbol

            )

            self.orders.clear()

            for order in orders:

                self.orders[

                    order["id"]

                ] = order

            self.logger.info(

                f"Orders synchronized ({len(self.orders)})"

            )

            return self.orders

        except Exception as e:

            self.logger.error(str(e))

            return {}

    # ======================================================
    # SYNC POSITIONS
    # ======================================================

    def sync_positions(
        self,
        symbols=None
    ):

        self.fetch_positions(

            symbols

        )

        self.sync_orders()

        self.logger.info(

            "Positions synchronized"

        )

        return self.positions

    # ======================================================
    # WAIT UNTIL CLOSED
    # ======================================================

    def wait_until_closed(
        self,
        symbol,
        timeout=60
    ):

        start = time.time()

        while time.time() - start < timeout:

            self.fetch_positions(

                [symbol]

            )

            if not self.has_open_position(

                symbol

            ):

                return True

            time.sleep(1)

        return False

    # ======================================================
    # RETRY ORDER
    # ======================================================

    def retry_order(
        self,
        callback,
        retries=3,
        delay=2
    ):

        last_error = None

        for _ in range(retries):

            try:

                return callback()

            except Exception as e:

                last_error = e

                self.logger.error(

                    str(e)

                )

                time.sleep(delay)

        raise last_error

    # ======================================================
    # RECOVER AFTER RESTART
    # ======================================================

    def recover_after_restart(
        self
    ):

        self.logger.info(

            "Recovering state..."

        )

        self.sync_positions()

        self.sync_orders()

        self.logger.info(

            f"Recovered {len(self.positions)} positions"

        )

        self.logger.info(

            f"Recovered {len(self.orders)} orders"

        )

        return {

            "positions": len(

                self.positions

            ),

            "orders": len(

                self.orders

            )

        }

    # ======================================================
    # REFRESH
    # ======================================================

    def refresh(
        self
    ):

        self.fetch_positions()

        self.sync_orders()

        return {

            "positions": len(

                self.positions

            ),

            "orders": len(

                self.orders

            ),

            "balance": self.free_balance()

        }

    # ======================================================
    # IS CONNECTED
    # ======================================================

    def is_connected(
        self
    ):

        return self.ping()

    # ======================================================
    # RECONNECT
    # ======================================================

    def reconnect(
        self
    ):

        try:

            self._connect()

            return True

        except Exception as e:

            self.logger.error(

                str(e)

            )

            return False

    # ======================================================
    # TRADE HISTORY
    # ======================================================

    def trade_history(
        self,
        symbol=None,
        limit=100
    ):

        try:

            return self.exchange.fetch_my_trades(

                symbol,

                limit=limit

            )

        except Exception as e:

            self.logger.error(str(e))

            return []

    # ======================================================
    # CLOSED PNL
    # ======================================================

    def closed_pnl(
        self,
        symbol=None,
        limit=100
    ):

        pnl = 0.0

        trades = self.trade_history(

            symbol,

            limit

        )

        for trade in trades:

            try:

                pnl += float(

                    trade.get(

                        "info",

                        {}

                    ).get(

                        "realizedPnl",

                        0

                    )

                )

            except Exception:

                pass

        return round(

            pnl,

            2

        )

    # ======================================================
    # TOTAL FEES
    # ======================================================

    def total_fees(
        self,
        symbol=None,
        limit=100
    ):

        fee = 0.0

        trades = self.trade_history(

            symbol,

            limit

        )

        for trade in trades:

            try:

                if trade.get("fee"):

                    fee += float(

                        trade["fee"]["cost"]

                    )

            except Exception:

                pass

        return round(

            fee,

            4

        )

    # ======================================================
    # WIN RATE
    # ======================================================

    def win_rate(
        self,
        symbol=None,
        limit=100
    ):

        wins = 0

        losses = 0

        trades = self.trade_history(

            symbol,

            limit

        )

        for trade in trades:

            try:

                pnl = float(

                    trade.get(

                        "info",

                        {}

                    ).get(

                        "realizedPnl",

                        0

                    )

                )

                if pnl > 0:

                    wins += 1

                elif pnl < 0:

                    losses += 1

            except Exception:

                pass

        total = wins + losses

        if total == 0:

            return 0.0

        return round(

            wins /

            total *

            100,

            2

        )

    # ======================================================
    # CURRENT EXPOSURE
    # ======================================================

    def current_exposure(
        self
    ):

        exposure = 0.0

        positions = self.fetch_positions()

        for position in positions:

            exposure += (

                position.mark *

                position.quantity

            )

        return round(

            exposure,

            2

        )

    # ======================================================
    # ACCOUNT SUMMARY
    # ======================================================

    def account_summary(
        self
    ):

        return {

            "wallet_balance": self.total_balance(),

            "free_balance": self.free_balance(),

            "used_balance": self.used_balance(),

            "positions": len(

                self.fetch_positions()

            ),

            "open_orders": self.open_order_count(),

            "exposure": self.current_exposure(),

            "closed_pnl": self.closed_pnl(),

            "fees": self.total_fees(),

            "win_rate": self.win_rate()

        }

    # ======================================================
    # PRINT SUMMARY
    # ======================================================

    def print_summary(
        self
    ):

        summary = self.account_summary()

        self.logger.info(

            "=" * 50

        )

        for key, value in summary.items():

            self.logger.info(

                f"{key}: {value}"

            )

        self.logger.info(

            "=" * 50

        )

    # ======================================================
    # RESET CACHE
    # ======================================================

    def reset_cache(
        self
    ):

        self.positions.clear()

        self.orders.clear()

        self.logger.info(

            "Cache cleared"

        )

    # ======================================================
    # SHUTDOWN
    # ======================================================

    def shutdown(
        self
    ):

        self.logger.info(

            "Execution Engine stopped."

        )

        self.reset_cache()
