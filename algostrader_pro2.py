#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ALGOSTRADER PRO - SMC TRADING BOT
VERSIONI LIVE ME UI TE PERMIRESUAR (CHECKBOXES + MANUAL INPUTS)
"""

import os
import sys
import threading
import time
from datetime import datetime
import webbrowser
from collections import deque
from shared_state import bot_data
from datetime import datetime



from engine.market_structure import MarketStructureEngine
from engine.trade_manager import TradeManager
from engine.fvg_engine import FVGEngine
from engine.market_structure import MarketStructureEngine
from engine.order_block_engine import OrderBlockEngine
from engine.liquidity_engine import LiquidityEngine
from engine.fvg_engine import FVGEngine
from engine.multi_timeframe_engine import MultiTimeframeEngine
from engine.trade_manager import TradeManager
from keep_alive import keep_alive
keep_alive()
from functools import wraps
from flask import request, Response

# =====================================================================
# SISTEMI I SIGURISË (LOGIN)
# =====================================================================
def check_auth(username, password):
    # Këtu vendos Emrin dhe Fjalëkalimin që dëshiron të përdorësh
    return username == '123123' and password == '123123'

def authenticate():
    return Response(
    'Qasje e ndaluar! Ju lutem fusni kredencialet e sakta.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Këtu vazhdon kodi yt i zakonshëm i botit...

fvg_engine = FVGEngine()

import os

print(os.path.abspath(__file__))
print(os.path.exists(__file__))

try:
    from flask import Flask, jsonify, request, render_template_string
    import ccxt
    import pandas as pd
    import pandas_ta as ta
except ImportError:
    print("⚠️ Mungojnë libraritë. Instalo: pip install flask ccxt pandas pandas_ta")
    sys.exit(1)


# =====================================================================
# KONFIGURIMI I BOTIT (STATE)
# =====================================================================
# =====================================================================
# KONFIGURIMI I BOTIT (STATE)
# =====================================================================

bot_config = {
    # ---------------------------------------------------
    # Binance
    # ---------------------------------------------------
    "api_key": "",
    "api_secret": "",

    # ---------------------------------------------------
    # Risk Management
    # ---------------------------------------------------
    "risk_usdt": 10.0,
    "risk_percent": 1.0,
    "risk_mode": "fixed",          # fixed | percent
    "leverage": 3,

    # ---------------------------------------------------
    # Take Profit / Stop Loss
    # ---------------------------------------------------
    "tp_ratio": 2.0,
    "sl_buffer": 0.30,
    "reward_ratio": 2.0,
    "sl_method": "swing",          # swing | atr | candle | fixed
    "tp_method": "rr",             # rr | liquidity | swing | fixed
    "atr_multiplier": 1.50,
    "auto_sl": True,
    "auto_tp": True,

    # ---------------------------------------------------
    # Position Management
    # ---------------------------------------------------
    "max_positions": 1,
    "cooldown_seconds": 60,

    # ---------------------------------------------------
    # Scanner
    # ---------------------------------------------------
    "watchlist": [
        "BTC/USDT",
        "SOL/USDT",
        "ETH/USDT",
        "PAXG/USDT"
    ],
    "timeframe": "5m",

    # ---------------------------------------------------
    # Indicators
    # ---------------------------------------------------
    "indicators": {
        "ema": {
            "active": True,
            "fast": 50,
            "slow": 200
        },
        "atr": {
            "active": True,
            "length": 14
        },
        "rsi": {
            "active": True,
            "length": 14,
            "buy": 35,
            "sell": 65
        },
        "volume": {
            "active": True,
            "length": 20
        },
        "fvg": {
            "active": True
        }
    },

    # ---------------------------------------------------
    # Bot Status
    # ---------------------------------------------------
    "is_running": False
}

bot_logs = deque(maxlen=50)
trade_history = deque(maxlen=100)
market_engine = MarketStructureEngine()

# ==========================================================
# SMART MONEY ENGINES
# ==========================================================

market_engine = MarketStructureEngine()
order_block_engine = OrderBlockEngine()
liquidity_engine = LiquidityEngine()
fvg_engine = FVGEngine()
mtf_engine = MultiTimeframeEngine()
trade_manager = TradeManager(None, None)

account_overview = {
    "balance": 0.0,
    "equity": 0.0,
    "wallet_balance": 0.0,
    "available_balance": 0.0,
    "used_margin": 0.0,
    "margin_balance": 0.0,
    "margin_ratio": 0.0,
    "realized_pnl": 0.0,
    "unrealized": 0.0,
    "unrealized_pnl": 0.0,
    "funding_fee": 0.0,
    "daily_pnl": 0.0,
    "roi": 0.0,
    "open_positions": 0
}

setup_stats = {
    "total_trades": 0,
    "wins": 0,
    "losses": 0,
    "win_rate": 0,
    "net_profit": 0,
    "max_drawdown": 0
}

system_status = {
    "connected": False,
    "scanner": False,
    "position_monitor": False,
    "binance_connected": False,
    "api_connected": False,
    "latency": 0,
    "server_time": "",
    "last_update": ""
}

position_details = {
    "symbol": "",
    "side": "",
    "entry_price": 0.0,
    "mark_price": 0.0,
    "contracts": 0.0,
    "leverage": 0,
    "margin": 0.0,
    "liquidation": 0.0,
    "roe": 0.0,
    "unrealized": 0.0
}

# =====================================================================
# LIVE POSITION DATA
# =====================================================================

active_positions = []
closed_trades = []
last_position_snapshot = {}
sync_lock = threading.Lock()

bot_thread = None
position_monitor_thread = None
stop_event = threading.Event()
active_exchange = None
trade_manager = TradeManager(None, None)

# =====================================================================
# LIVE BINANCE SYNCHRONIZATION
# =====================================================================

active_positions = []
closed_trades = trade_history
last_position_snapshot = {}
last_closed_trade_ids = set()
sync_lock = threading.Lock()
position_monitor_thread = None

# =====================================================================
# LOGJIKA E LOGS & TRANSAKSIONEVE
# =====================================================================
def shto_log(mesazhi, lloji="INFO"):
    koha = time.strftime('%H:%M:%S')
    bot_logs.appendleft({"koha": koha, "mesazhi": mesazhi, "lloji": lloji})
    print(f"[{lloji}] {koha} - {mesazhi}")

def shto_transaksion(symbol, side, mesazhi, statusi, profit=0):
    trade_history.appendleft({
        "koha": time.strftime('%I:%M:%S %p'),
        "symbol": symbol,
        "lloji": side.upper(),
        "mesazhi": mesazhi,
        "statusi": statusi,
        "profit": round(profit, 2)
    })

def update_statistics(profit):
    global setup_stats
    setup_stats["total_trades"] += 1

    if profit > 0:
        setup_stats["wins"] += 1
    elif profit < 0:
        setup_stats["losses"] += 1

    setup_stats["net_profit"] += profit
    total = setup_stats["total_trades"]

    if total > 0:
        setup_stats["win_rate"] = round(
            setup_stats["wins"] * 100 / total,
            2
        )

def calculate_roe(entry_price, mark_price, side, leverage):
    try:
        if entry_price <= 0:
            return 0

        if side.upper() == "LONG":
            pnl_percent = (
                (mark_price - entry_price)
                / entry_price
            ) * 100
        else:
            pnl_percent = (
                (entry_price - mark_price)
                / entry_price
            ) * 100

        return round(
            pnl_percent * leverage,
            2
        )
    except:
        return 0

def clear_active_positions():
    global active_positions
    with sync_lock:
        active_positions.clear()

def add_active_position(position):
    global active_positions
    with sync_lock:
        active_positions.append(position)

def update_position_snapshot(position):
    global last_position_snapshot
    symbol = position["symbol"]
    last_position_snapshot[symbol] = position.copy()

def get_position_snapshot(symbol):
    return last_position_snapshot.get(symbol)

def sync_binance_data():
    global active_exchange
    global position_details

    if active_exchange is None:
        return

    try:
        if active_positions:
            position_details.update(active_positions[0])
    except Exception as e:
        shto_log(
            f"SYNC ERROR: {e}",
            "GABIM"
        )

def is_position_open(symbol):
    global active_positions
    with sync_lock:
        for pos in active_positions:
            if pos["symbol"] == symbol:
                return True
    return False

def monitor_positions():
    global active_exchange

    shto_log(
        "Position Monitor u aktivizua.",
        "SISTEMI"
    )

    last_balance_sync = 0

    while not stop_event.is_set():
        try:
            if not bot_config["is_running"]:
                time.sleep(1)
                continue

            if active_exchange is None:
                time.sleep(1)
                continue

            # Pozicionet rifreskohen çdo sekondë
            sync_binance_data()

            # Balance / Equity rifreskohet çdo 5 sekonda
            now = time.time()
            if now - last_balance_sync >= 5:
                rifresko_balancin(active_exchange)
                last_balance_sync = now

        except Exception as e:
            shto_log(
                f"Monitor Error: {e}",
                "GABIM"
            )
        time.sleep(1)

# =====================================================================
# LOGJIKA E TREGTIMIT
# =====================================================================
def rifresko_balancin(exchange):
    global account_overview
    global active_positions

    try:
        balance = exchange.fetch_balance(params={"type": "future"})
        total_balance = float(balance["total"].get("USDT", 0))
        free_balance = float(balance["free"].get("USDT", 0))
        used_balance = float(balance["used"].get("USDT", 0))
        margin_balance = total_balance
        
        account_overview["balance"] = round(total_balance, 2)

        positions = []
        if "info" in balance and "positions" in balance["info"]:
            positions = balance["info"]["positions"]

        if not positions:
            try:
                positions = exchange.fetch_positions()
            except:
                positions = []

        clear_active_positions()

        unrealized = 0.0
        open_positions = 0

        for pos in positions:
            try:
                info = pos["info"] if "info" in pos else pos
                symbol = info.get("symbol") or pos.get("symbol") or ""

                if "/" not in symbol:
                    symbol = symbol.replace("USDT", "/USDT")

                qty = float(info.get("positionAmt", pos.get("contracts", 0)))

                if abs(qty) <= 0:
                    continue

                open_positions += 1

                entry_price = float(info.get("entryPrice", pos.get("entryPrice", 0)))
                mark_price = float(info.get("markPrice", pos.get("markPrice", 0)))
                leverage = int(float(info.get("leverage", pos.get("leverage", 1))))
                liquidation = float(info.get("liquidationPrice", 0))
                margin = float(info.get("isolatedWallet", 0))
                pnl = float(info.get("unrealizedProfit", pos.get("unrealizedPnl", 0)))

                unrealized += pnl
                side = "SHORT" if qty < 0 else "LONG"

                roe = calculate_roe(
                    entry_price,
                    mark_price,
                    side,
                    leverage
                )

                position = {
                    "symbol": symbol,
                    "side": side,
                    "contracts": abs(qty),
                    "entry_price": round(entry_price, 6),
                    "mark_price": round(mark_price, 6),
                    "leverage": leverage,
                    "margin": round(margin, 2),
                    "liquidation": round(liquidation, 6),
                    "unrealized": round(pnl, 2),
                    "roe": roe
                }

                add_active_position(position)
                update_position_snapshot(position)

            except Exception as err:
                shto_log(f"Position Parse Error: {err}", "GABIM")

        equity = total_balance + unrealized

        account_overview["equity"] = round(equity, 2)
        account_overview["wallet_balance"] = round(total_balance, 2)
        account_overview["available_balance"] = round(free_balance, 2)
        account_overview["used_margin"] = round(used_balance, 2)
        account_overview["margin_balance"] = round(margin_balance, 2)
        account_overview["unrealized"] = round(unrealized, 2)        
        account_overview["unrealized_pnl"] = round(unrealized, 2)
        account_overview["unrealizedPnL"] = round(unrealized, 2)
        account_overview["open_positions"] = open_positions
        account_overview["positions"] = open_positions
        account_overview["active_positions"] = open_positions
        account_overview["realized_pnl"] = round(setup_stats["net_profit"], 2)
        account_overview["daily_pnl"] = round(setup_stats["net_profit"], 2)
        account_overview["roi"] = calculate_roi()
        account_overview["funding_fee"] = 0.0

    except Exception as e:
        shto_log(f"Balance Sync Error: {e}", "GABIM")

def calculate_roi():
    try:
        if account_overview["balance"] <= 0:
            return 0
        return round(
            (setup_stats["net_profit"] /
             account_overview["balance"]) * 100,
            2
        )
    except:
        return 0


def analizo_dhe_tregto():
    global active_exchange

    shto_log(
        f"Skaneri SMC u aktivizua (Timeframe: {bot_config['timeframe']})",
        "SISTEMI"
    )

    while not stop_event.is_set():

        if not bot_config["is_running"] or active_exchange is None:
            time.sleep(2)
            continue

        rifresko_balancin(active_exchange)

        for symbol in bot_config["watchlist"]:

            if is_position_open(symbol):
                continue

            try:
                bars = active_exchange.fetch_ohlcv(
                    symbol,
                    timeframe=bot_config["timeframe"],
                    limit=300
                )

                # Krijo tabelen (DataFrame) qe i duhet bllokut me poshte
                df = pd.DataFrame(
                    bars,
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )

                # =====================================================
                # MULTI TIMEFRAME
                # =====================================================
                frames = {}

                for tf in ["4h", "1h", "15m", "5m"]:
                    bars_tf = active_exchange.fetch_ohlcv(
                        symbol,
                        timeframe=tf,
                        limit=300
                    )
                    frames[tf] = pd.DataFrame(
                        bars_tf,
                        columns=[
                            "timestamp",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume"
                        ]
                    )

                df4h = frames["4h"]
                df1h = frames["1h"]
                df15m = frames["15m"]
                df5m = frames["5m"]

                mtf = mtf_engine.analyze(
                    df4h,
                    df1h,
                    df15m,
                    df5m
                )

                # =====================================================
                # MARKET STRUCTURE
                # =====================================================
                market = market_engine.analyze(df)

                print("\n==============================")
                print(f"{symbol} MARKET STRUCTURE")
                print("==============================")

                print(f"Trend : {market.trend.direction}")
                print(f"Structure Score : {market.structure_score}")
                print(f"Swing Count : {len(market.swings)}")

                for swing in market.swings[-5:]:
                    print(
                        swing.kind,
                        round(swing.price, 2),
                        swing.index
                    )

                # =====================================================
                # ORDER BLOCK ENGINE
                # =====================================================
                order_blocks = order_block_engine.analyze(df)

                print(f"Bullish OB : {len(order_blocks.bullish)}")
                print(f"Bearish OB : {len(order_blocks.bearish)}")

                # =====================================================
                # LIQUIDITY ENGINE
                # =====================================================
                liquidity = liquidity_engine.analyze(df)

                print(f"Liquidity Sweeps : {len(liquidity.sweeps)}")
                print(f"Equal Highs : {len(liquidity.equal_highs)}")
                print(f"Equal Lows : {len(liquidity.equal_lows)}")

                # =====================================================
                # FVG ENGINE
                # =====================================================
                fvg = fvg_engine.analyze(df)

                has_fvg = False
                if len(fvg.gaps) > 0:
                    has_fvg = True

                print(f"FVG Count : {len(fvg.gaps)}")

                # =====================================================
                # SMART MONEY FILTER
                # =====================================================
                if not mtf.trade_allowed:
                    print(f"{symbol} -> Multi Timeframe nuk lejon hyrje.")
                    continue

                if market.trend.direction == "bullish":
                    side = "buy"
                elif market.trend.direction == "bearish":
                    side = "sell"
                else:
                    continue

                # =====================================================
                # STRUCTURE SCORE FILTER
                # =====================================================
                if market.structure_score < 60:
                    print(f"{symbol} -> Structure Score shumë i ulët.")
                    continue

                # =====================================================
                # ORDER BLOCK FILTER
                # =====================================================
                if side == "buy":
                    if len(order_blocks.bullish) == 0:
                        continue

                if side == "sell":
                    if len(order_blocks.bearish) == 0:
                        continue

                # =====================================================
                # LIQUIDITY FILTER
                # =====================================================
                if len(liquidity.sweeps) == 0:
                    continue

                # =====================================================
                # FVG FILTER
                # =====================================================
                if not has_fvg:
                    continue

                # Variabli i indikatoreve per te bere lidhjen e duhur
                ind = bot_config["indicators"]

                # =====================================================
                # EMA
                # =====================================================
                if ind["ema"]["active"] and len(df) > ind["ema"]["slow"]:
                    df["ema_fast"] = ta.ema(
                        df["close"],
                        length=ind["ema"]["fast"]
                    )
                    df["ema_slow"] = ta.ema(
                        df["close"],
                        length=ind["ema"]["slow"]
                    )

                # =====================================================
                # RSI
                # =====================================================
                if ind["rsi"]["active"]:
                    df["rsi"] = ta.rsi(
                        df["close"],
                        length=ind["rsi"]["length"]
                    )

                # =====================================================
                # ATR
                # =====================================================
                if ind["atr"]["active"]:
                    df["atr"] = ta.atr(
                        df["high"],
                        df["low"],
                        df["close"],
                        length=ind["atr"]["length"]
                    )

                # =====================================================
                # VOLUME
                # =====================================================
                if ind["volume"]["active"]:
                    df["vol_ma"] = ta.sma(
                        df["volume"],
                        length=ind["volume"]["length"]
                    )

                # =====================================================
                # FVG
                # =====================================================
                if ind["fvg"]["active"]:
                    df["fvg_bull"] = df["low"] > df["high"].shift(2)
                    df["fvg_bear"] = df["high"] < df["low"].shift(2)
                    df["has_fvg"] = df["fvg_bull"] | df["fvg_bear"]

                # =====================================================
                # CURRENT VALUES
                # =====================================================
                current_price = df["close"].iloc[-1]
                current_volume = df["volume"].iloc[-1]

                current_ema_fast = (
                    df["ema_fast"].iloc[-1]
                    if "ema_fast" in df.columns
                    else current_price
                )

                current_ema_slow = (
                    df["ema_slow"].iloc[-1]
                    if "ema_slow" in df.columns
                    else current_price
                )

                current_rsi = (
                    df["rsi"].iloc[-1]
                    if "rsi" in df.columns
                    else 50
                )

                current_atr = (
                    df["atr"].iloc[-1]
                    if "atr" in df.columns
                    else 0
                )

                has_fvg = (
                    df["has_fvg"].iloc[-1]
                    if "has_fvg" in df.columns
                    else False
                )

                status_ema = (
                    "BULL"
                    if current_price > current_ema_fast
                    else "BEAR"
                )

                status_fvg = (
                    "PO"
                    if has_fvg
                    else "JO"
                )

                print(
                    f"--> [MONITORIMI] {symbol} | "
                    f"Çmimi: {current_price:.4f} | "
                    f"RSI: {round(current_rsi,2)} | "
                    f"EMA: {status_ema} | "
                    f"ATR: {round(current_atr,4)} | "
                    f"Vol: {current_volume:.0f} | "
                    f"FVG: {status_fvg}"
                )

                # =====================================================
                # SIGNAL
                # =====================================================
                signal_msg = []
                is_valid = True
                side = "buy"

                if ind["ema"]["active"]:
                    if current_ema_fast > current_ema_slow:
                        signal_msg.append("Trend Bullish")
                        side = "buy"
                    else:
                        signal_msg.append("Trend Bearish")
                        side = "sell"

                if ind["rsi"]["active"]:
                    if current_rsi < ind["rsi"]["buy"]:
                        signal_msg.append(f"RSI OS ({round(current_rsi,1)})")
                        side = "buy"
                    elif current_rsi > ind["rsi"]["sell"]:
                        signal_msg.append(f"RSI OB ({round(current_rsi,1)})")
                        side = "sell"
                    else:
                        is_valid = False

                # =====================================================
                # EXECUTE TRADE
                # =====================================================
                if is_valid and len(signal_msg) > 0:
                    shto_log(
                        f"{symbol} Plotëson kushtet: {', '.join(signal_msg)}",
                        "SIGNAL"
                    )

                    trade = trade_manager.execute_trade(
                        exchange=active_exchange,
                        symbol=symbol,
                        side=side,
                        current_price=current_price,
                        current_atr=current_atr,
                        config=bot_config
                    )

                    if trade.success:
                        shto_log(f"{trade.symbol} u hap me sukses.", "SUKSES")
                        shto_log(f"Entry : {trade.entry_price}", "TRADE")
                        shto_log(f"SL : {trade.stop_loss}", "TRADE")
                        shto_log(f"TP : {trade.take_profit}", "TRADE")

                        sync_binance_data()

                        shto_transaksion(
                            trade.symbol,
                            trade.side,
                            "Pozicioni u hap.",
                            "LIVE",
                            0
                        )

                        time.sleep(bot_config["cooldown_seconds"])
                    else:
                        shto_log(trade.message, "GABIM")

            except Exception as e:
                shto_log(f"Gabim gjatë ekzekutimit te {symbol}: {e}", "GABIM")

        time.sleep(60)


# =====================================================================
# SERVERI FLASK & GUI HTML
# =====================================================================
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="sq">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <title>NazRmd ProBot - LIVE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b1120; color: #f8fafc; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        .live-border { border: 1px solid #ef4444; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
        
        /* Stilizimi per checkbox */
        .custom-checkbox {
            appearance: none;
            width: 1.25rem;
            height: 1.25rem;
            border: 2px solid #334155;
            border-radius: 0.25rem;
            background-color: #0f172a;
            cursor: pointer;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .custom-checkbox:checked {
            background-color: #10b981;
            border-color: #10b981;
        }
        .custom-checkbox:checked::after {
            content: '';
            width: 0.35rem;
            height: 0.65rem;
            border: solid white;
            border-width: 0 2px 2px 0;
            transform: rotate(45deg);
            position: absolute;
            top: 0.15rem;
        }
        
        .pair-btn {
            cursor: pointer;
            transition: all 0.2s;
        }
        .pair-btn.active {
            background-color: #10b98120;
            border-color: #10b981;
            color: #10b981;
        }
        .pair-btn.inactive {
            background-color: #0f172a;
            border-color: #334155;
            color: #94a3b8;
        }
        
        .indicator-settings {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .indicator-settings.open {
            max-height: 100px;
        }
    </style>
</head>
<!-- Ndryshimi 1: 'flex-col md:flex-row' bën që sidebar-i të rrijë lart në telefon dhe majtas në desktop -->
<body class="min-h-screen flex flex-col md:flex-row bg-[#0b1120] overflow-x-hidden md:overflow-hidden">

    <!-- SIDEBAR (Majtas në PC / Lart në Telefon) -->
    <!-- Ndryshimi 2: 'w-full md:w-80' dhe heqja e lartësisë fikse për telefonat -->
    <div class="w-full md:w-80 bg-slate-900 border-b md:border-b-0 md:border-r border-slate-800 flex flex-col live-border z-10 relative">
        <div class="p-4 border-b border-slate-800">
            <h1 class="text-xl font-bold flex items-center gap-2 text-white">
                <i data-lucide="activity" class="text-rose-500"></i> NazRmd ProBot <span class="text-xs font-normal">GUI</span>
            </h1>
            <p class="text-[10px] text-rose-400 mt-1 uppercase tracking-wider font-bold">Llogaria Reale</p>
        </div>
        
        <div class="flex-1 md:overflow-y-auto p-4 space-y-5">
            
            <!-- API Keys -->
            <details class="group bg-slate-950/50 rounded-xl border border-slate-800">
                <summary class="flex justify-between items-center font-medium cursor-pointer list-none p-3 text-sm text-slate-300">
                    <span class="flex items-center gap-2"><i data-lucide="key" class="w-4 h-4"></i> Lidhja me API</span>
                    <span class="transition group-open:rotate-180"><i data-lucide="chevron-down" class="w-4 h-4"></i></span>
                </summary>
                <div class="text-slate-500 group-open:animate-fadeIn p-3 pt-0 space-y-3">
                    <div>
                        <input type="text" id="api-key" placeholder="LIVE API Key" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-rose-500">
                    </div>
                    <div>
                        <input type="password" id="api-secret" placeholder="LIVE Secret Key" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-rose-500">
                    </div>
                </div>
            </details>

            <!-- Indikatorët Aktivë -->
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <h2 class="text-sm font-semibold text-white flex items-center gap-2 bg-blue-600/20 px-2 py-1 rounded">
                        <i data-lucide="trending-up" class="w-4 h-4 text-blue-400"></i> Indikatorët Aktivë
                    </h2>
                    <select id="timeframe" class="bg-slate-950 border border-slate-700 rounded text-xs px-2 py-1 text-slate-300 focus:outline-none focus:border-blue-500">
                        <option value="1m">1m</option>
                        <option value="5m" selected>5m</option>
                        <option value="15m">15m</option>
                        <option value="1h">1h</option>
                        <option value="4h">4h</option>
                    </select>
                </div>
                
                <div class="space-y-1">
                    <!-- EMA -->
                    <div class="bg-slate-950 border border-slate-800/50 rounded-lg p-2 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <input type="checkbox" id="check-ema" checked class="custom-checkbox" onchange="toggleSettings('settings-ema')">
                                <div>
                                    <div class="text-sm font-medium text-slate-200">EMA (<span id="ema-label">50/200</span>)</div>
                                    <div class="text-[10px] text-slate-400">Drejtimi i Trendit</div>
                                </div>
                            </div>
                            <button onclick="toggleSettings('settings-ema')" class="text-slate-500 hover:text-slate-300"><i data-lucide="settings" class="w-4 h-4"></i></button>
                        </div>
                        <div id="settings-ema" class="indicator-settings mt-2 border-t border-slate-800 pt-2 grid grid-cols-2 gap-2 px-4 md:px-8">
                            <div>
                                <label class="text-[9px] text-slate-500">E Shpejtë</label>
                                <input type="number" id="val-ema-fast" value="50" onchange="updateLabel('ema')" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 text-center">
                            </div>
                            <div>
                                <label class="text-[9px] text-slate-500">E Ngadaltë</label>
                                <input type="number" id="val-ema-slow" value="200" onchange="updateLabel('ema')" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 text-center">
                            </div>
                        </div>
                    </div>

                    <!-- ATR -->
                    <div class="bg-slate-950 border border-slate-800/50 rounded-lg p-2 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <input type="checkbox" id="check-atr" checked class="custom-checkbox" onchange="toggleSettings('settings-atr')">
                                <div>
                                    <div class="text-sm font-medium text-slate-200">ATR (<span id="atr-label">14</span>)</div>
                                    <div class="text-[10px] text-slate-400">Stop Loss Dinamik</div>
                                </div>
                            </div>
                            <button onclick="toggleSettings('settings-atr')" class="text-slate-500 hover:text-slate-300"><i data-lucide="settings" class="w-4 h-4"></i></button>
                        </div>
                        <div id="settings-atr" class="indicator-settings mt-2 border-t border-slate-800 pt-2 px-4 md:px-8">
                            <label class="text-[9px] text-slate-500">Gjatësia</label>
                            <input type="number" id="val-atr-len" value="14" onchange="updateLabel('atr')" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 text-center">
                        </div>
                    </div>

                    <!-- RSI -->
                    <div class="bg-slate-950 border border-slate-800/50 rounded-lg p-2 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <input type="checkbox" id="check-rsi" checked class="custom-checkbox" onchange="toggleSettings('settings-rsi')">
                                <div>
                                    <div class="text-sm font-medium text-slate-200">RSI (<span id="rsi-label">14</span>)</div>
                                    <div class="text-[10px] text-slate-400">Momentum Hyrjeje</div>
                                </div>
                            </div>
                            <button onclick="toggleSettings('settings-rsi')" class="text-slate-500 hover:text-slate-300"><i data-lucide="settings" class="w-4 h-4"></i></button>
                        </div>
                        <div id="settings-rsi" class="indicator-settings mt-2 border-t border-slate-800 pt-2 grid grid-cols-3 gap-2 px-4 md:px-8">
                            <div>
                                <label class="text-[9px] text-slate-500">Gjatësia</label>
                                <input type="number" id="val-rsi-len" value="14" onchange="updateLabel('rsi')" class="w-full bg-slate-900 border border-slate-700 rounded px-1 py-1 text-xs text-slate-300 text-center">
                            </div>
                            <div>
                                <label class="text-[9px] text-slate-500">Buy (OS)</label>
                                <input type="number" id="val-rsi-buy" value="35" class="w-full bg-slate-900 border border-slate-700 rounded px-1 py-1 text-xs text-slate-300 text-center">
                            </div>
                            <div>
                                <label class="text-[9px] text-slate-500">Sell (OB)</label>
                                <input type="number" id="val-rsi-sell" value="65" class="w-full bg-slate-900 border border-slate-700 rounded px-1 py-1 text-xs text-slate-300 text-center">
                            </div>
                        </div>
                    </div>

                    <!-- Volume -->
                    <div class="bg-slate-950 border border-slate-800/50 rounded-lg p-2 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <input type="checkbox" id="check-vol" checked class="custom-checkbox" onchange="toggleSettings('settings-vol')">
                                <div>
                                    <div class="text-sm font-medium text-slate-200">Volume (<span id="vol-label">20 Avg</span>)</div>
                                    <div class="text-[10px] text-slate-400">Konfirmim Fuqie</div>
                                </div>
                            </div>
                            <button onclick="toggleSettings('settings-vol')" class="text-slate-500 hover:text-slate-300"><i data-lucide="settings" class="w-4 h-4"></i></button>
                        </div>
                        <div id="settings-vol" class="indicator-settings mt-2 border-t border-slate-800 pt-2 px-4 md:px-8">
                            <label class="text-[9px] text-slate-500">Gjatësia Mesatare</label>
                            <input type="number" id="val-vol-len" value="20" onchange="updateLabel('vol')" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 text-center">
                        </div>
                    </div>

                    <!-- FVG -->
                    <div class="bg-slate-950 border border-slate-800/50 rounded-lg p-2 transition-colors">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" id="check-fvg" checked class="custom-checkbox">
                            <div>
                                <div class="text-sm font-medium text-slate-200">FVG Detector</div>
                                <div class="text-[10px] text-slate-400">Smart Money Gap</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tregtimi (Pairs) -->
            <div class="space-y-3 pt-2">
                <h2 class="text-sm font-semibold text-slate-300 flex items-center gap-2">
                    <i data-lucide="list" class="w-4 h-4 text-slate-400"></i> Tregtimi (Pairs)
                </h2>
                <div class="grid grid-cols-2 gap-2" id="pair-grid">
                    <!-- Javascript mbushe kete pjese -->
                </div>
            </div>

            <!-- Risk Management Box -->
            <div class="space-y-3 pt-4 border-t border-slate-800 mb-6 md:mb-0">
                <h2 class="text-sm font-semibold text-slate-300 flex items-center gap-2">
                    <i data-lucide="pie-chart" class="w-4 h-4 text-slate-400"></i> Risku & Kapitali
                </h2>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-[10px] text-slate-500 mb-1 block">Kapitali (USDT)</label>
                        <input type="number" id="risk-usdt" value="10" class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-300 text-center focus:border-rose-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 mb-1 block">Leva (x)</label>
                        <input type="number" id="leverage" value="3" class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-300 text-center focus:border-rose-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 mb-1 block">Take Profit (%)</label>
                        <input type="number" id="tp-ratio" value="2.0" step="0.1" class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-300 text-center focus:border-rose-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] text-slate-500 mb-1 block">Stop Loss (%)</label>
                        <input type="number" id="sl-buffer" value="0.3" step="0.05" class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-300 text-center focus:border-rose-500 outline-none">
                    </div>
                </div>
            </div>
        </div>

        <div class="p-4 border-t border-slate-800 bg-slate-900 mt-auto md:mt-0">
            <button id="btn-toggle" onclick="toggleBot()" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-rose-900/20">
                <i data-lucide="play" class="w-4 h-4"></i> Nis Skanimin
            </button>
        </div>
    </div>

    <!-- MAIN CONTENT (Djathtas në PC / Poshtë në Telefon) -->
    <!-- Ndryshimi 3: Shtimi i 'md:h-screen' për ta lënë të rrëshqasë natyrshëm në telefon -->
    <div class="flex-1 flex flex-col md:h-screen md:overflow-y-auto bg-[#0b1120] p-4 md:p-6 space-y-6 relative">
        
        <div class="flex justify-between items-center mt-4 md:mt-0">
            <div>
                <h2 class="text-xl md:text-2xl font-bold text-white tracking-tight">Paneli i Kontrollit LIVE</h2>
                <div id="status-badge" class="mt-1 text-xs font-medium text-slate-400 flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-slate-500"></span> Boti Joaktiv
                </div>
            </div>
        </div>

        <!-- TOP ACCOUNT STATS -->
        <!-- Ndryshimi 4: 'grid-cols-2 lg:grid-cols-4' - 2 kolona në tel, 4 në PC -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Balanca e Llogarisë</span>
                <span id="stat-balance" class="text-xl md:text-3xl font-bold text-white">$0.00</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Ekuiteti (Equity)</span>
                <span id="stat-equity" class="text-xl md:text-3xl font-bold text-amber-400">$0.00</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Unrealized PnL</span>
                <span id="stat-pnl" class="text-xl md:text-3xl font-bold text-emerald-400">$0.00</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Pozicione Aktive</span>
                <span id="stat-positions" class="text-xl md:text-3xl font-bold text-cyan-400">0</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Margin Ratio</span>
                <span id="margin-ratio" class="text-xl md:text-3xl font-bold text-orange-400">0%</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Funding Fee</span>
                <span id="funding-fee" class="text-xl md:text-3xl font-bold text-cyan-400">$0.00</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Daily PnL</span>
                <span id="daily-pnl" class="text-xl md:text-3xl font-bold text-emerald-400">$0.00</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 md:p-5 rounded-2xl flex flex-col justify-center">
                <span class="text-[10px] md:text-xs text-slate-400 font-medium mb-1">Realized PnL</span>
                <span id="realized-pnl" class="text-xl md:text-3xl font-bold text-blue-400">$0.00</span>
            </div>
        </div>

        <!-- LIVE POSITION CARDS -->
        <!-- Ndryshimi 5: 1 kolonë në telefon, 3 në kompjuter -->
        <div id="position-cards" class="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-4 mb-2 md:mb-5"></div>

        <!-- LIVE OPEN POSITIONS (Tabela) -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 overflow-hidden w-full">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-sm font-bold text-slate-300 flex items-center gap-2">
                    <i data-lucide="briefcase" class="w-4 h-4 text-cyan-400"></i>
                    Pozicionet LIVE
                </h3>
                <span class="text-[10px] md:text-xs text-slate-500">
                    Refresh 1s <span id="last-refresh" class="text-emerald-400 font-semibold ml-1">--</span>
                </span>
            </div>
            <div class="overflow-x-auto w-full">
                <!-- Klasa w-[600px] md:w-full detyron tabelën të bëhet e lëvizshme majtas-djathtas pa prishur ekranin -->
                <table class="w-[700px] md:w-full text-xs text-left">
                    <thead class="text-slate-500 border-b border-slate-800">
                        <tr>
                            <th class="py-2">Pair</th>
                            <th class="py-2">Side</th>
                            <th class="py-2 text-right">Entry</th>
                            <th class="py-2 text-right">Mark</th>
                            <th class="py-2 text-right">Qty</th>
                            <th class="py-2 text-right">Lev</th>
                            <th class="py-2 text-right">Margin</th>
                            <th class="py-2 text-right">PnL</th>
                            <th class="py-2 text-right">ROE%</th>
                            <th class="py-2 text-right">Liq.</th>
                        </tr>
                    </thead>
                    <tbody id="positions-table" class="divide-y divide-slate-800 text-slate-300">
                        <tr>
                            <td colspan="10" class="text-center text-slate-500 py-8">Nuk ka pozicione aktive</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- TRADINGVIEW -->
        <!-- Ndryshimi 6: Lartësia e TradingView u bë h-[400px] për telefonat dhe h-[65vh] për PC -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-1 overflow-hidden relative w-full h-[400px] lg:h-[65vh]">
            <iframe
                id="tv-chart"
                src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:BTCUSDT.P&interval=5&theme=dark&style=1&hide_top_toolbar=1"
                class="w-full h-full rounded-xl"
                frameborder="0">
            </iframe>
        </div>

        <!-- Bottom Row (Logs & Stats) -->
        <!-- Ndryshimi 7: 1 kolonë në tel, 3 kolona në PC -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6 pb-10 md:pb-0">
            <!-- Trade History -->
            <div class="col-span-1 lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col h-64 w-full overflow-hidden">
                <h3 class="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                    <i data-lucide="list" class="w-4 h-4 text-emerald-400"></i> Historiku & Sinjalet e Skanerit
                </h3>
                <div class="flex-1 overflow-x-auto overflow-y-auto pr-2">
                    <table class="w-[500px] md:w-full text-left text-[10px] md:text-xs">
                        <thead class="sticky top-0 bg-slate-900 text-slate-500">
                            <tr><th class="pb-2 font-medium">Koha</th><th class="pb-2 font-medium">Lloji</th><th class="pb-2 font-medium">Mesazhi / Kushtet</th></tr>
                        </thead>
                        <tbody id="trade-history" class="divide-y divide-slate-800/50 text-slate-300 font-mono">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Setup Stats -->
            <div class="col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col h-64 w-full">
                <h3 class="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                    <i data-lucide="bar-chart-2" class="w-4 h-4 text-amber-400"></i> Performanca (W/L)
                </h3>
                <div class="space-y-4 text-sm flex-1 font-medium">
                    <div class="flex justify-between items-center border-b border-slate-800/60 pb-3">
                        <span class="text-slate-400">Total Tregti:</span>
                        <span id="stat-total" class="text-white">0</span>
                    </div>
                    <div class="flex justify-between items-center border-b border-slate-800/60 pb-3">
                        <span class="text-slate-400">Fitore:</span>
                        <span id="stat-wins" class="text-emerald-400">0</span>
                    </div>
                    <div class="flex justify-between items-center border-b border-slate-800/60 pb-3">
                        <span class="text-slate-400">Humbje:</span>
                        <span id="stat-losses" class="text-rose-400">0</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal per Error -->
    <div id="error-modal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-rose-500/30 p-6 rounded-2xl max-w-sm w-full text-center shadow-2xl shadow-rose-900/20">
            <i data-lucide="alert-circle" class="w-12 h-12 text-rose-500 mx-auto mb-3"></i>
            <h3 class="text-lg font-bold text-white mb-2">Gabim Lidhjeje</h3>
            <p id="error-message" class="text-sm text-slate-400 mb-5">Mesazhi i gabimit...</p>
            <button onclick="document.getElementById('error-modal').classList.add('hidden')" class="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-2 rounded-lg transition-colors">Kuptova</button>
        </div>
    </div>
    
    <!-- Scripts per konfigurimin e Ikonave lucide -->
    <script>
        lucide.createIcons();
        // Kodi yt javascript vazhdon këtu poshtë...
    </script>
</body>
</html>
"""

    <script>
        lucide.createIcons();

        // Menaxhimi i Liste se Cifteve (Pairs) UI
        const availablePairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XAU/USDT', 'XRP/USDT', 'DOGE/USDT', 'ORCA/USDT', 'AVAX/USDT', 'LINK/USDT', 'AIOT/USDT', 'PEPE/USDT', 'FLOKI/USDT'];
        let selectedPairs = new Set(['BTC/USDT']);

        function renderPairs() {
            const grid = document.getElementById('pair-grid');
            grid.innerHTML = '';
            availablePairs.forEach(pair => {
                const isActive = selectedPairs.has(pair);
                const btnClass = isActive ? 'pair-btn active' : 'pair-btn inactive';
                const icon = isActive ? '<i data-lucide="check-circle-2" class="w-3 h-3"></i>' : '<i data-lucide="circle" class="w-3 h-3"></i>';
                
                grid.innerHTML += `
                    <div onclick="togglePair('${pair}')" class="${btnClass} border rounded-lg px-2 py-1.5 text-[10px] font-bold flex items-center gap-1.5 uppercase">
                        ${icon} ${pair.split('/')[0]}
                    </div>
                `;
            });
            lucide.createIcons();
        }

        function togglePair(pair) {
            if(selectedPairs.has(pair)) {
                if(selectedPairs.size > 1) selectedPairs.delete(pair); // Must keep at least 1
            } else {
                selectedPairs.add(pair);
                // Ndrysho chartin te monedha e fundit e klikuar
                document.getElementById('tv-chart').src = `https://s.tradingview.com/widgetembed/?symbol=BINANCE:${pair.replace('/','')}.P&interval=5&theme=dark&style=1&hide_top_toolbar=1`;
            }
            renderPairs();
        }

        renderPairs();

        // UI Helpers
        function toggleSettings(id) {
            const el = document.getElementById(id);
            el.classList.toggle('open');
        }

        function updateLabel(type) {
            if(type === 'ema') {
                document.getElementById('ema-label').innerText = `${document.getElementById('val-ema-fast').value}/${document.getElementById('val-ema-slow').value}`;
            } else if(type === 'atr') {
                document.getElementById('atr-label').innerText = document.getElementById('val-atr-len').value;
            } else if(type === 'rsi') {
                document.getElementById('rsi-label').innerText = document.getElementById('val-rsi-len').value;
            } else if(type === 'vol') {
                document.getElementById('vol-label').innerText = `${document.getElementById('val-vol-len').value} Avg`;
            }
        }

        function toggleBot() {
            const btn = document.getElementById('btn-toggle');
            
            if (btn.innerText.includes('Nis Skanimin')) {
                // Mbledhim parametrat
                const config = {
                    api_key: document.getElementById('api-key').value,
                    api_secret: document.getElementById('api-secret').value,
                    risk_usdt: parseFloat(document.getElementById('risk-usdt').value),
                    leverage: parseInt(document.getElementById('leverage').value),
                    tp_ratio: parseFloat(document.getElementById('tp-ratio').value),
                    sl_buffer: parseFloat(document.getElementById('sl-buffer').value),
                    watchlist: Array.from(selectedPairs),
                    timeframe: document.getElementById('timeframe').value,
                    indicators: {
                        ema: {
                            active: document.getElementById('check-ema').checked,
                            fast: parseInt(document.getElementById('val-ema-fast').value),
                            slow: parseInt(document.getElementById('val-ema-slow').value)
                        },
                        atr: {
                            active: document.getElementById('check-atr').checked,
                            length: parseInt(document.getElementById('val-atr-len').value)
                        },
                        rsi: {
                            active: document.getElementById('check-rsi').checked,
                            length: parseInt(document.getElementById('val-rsi-len').value),
                            buy: parseInt(document.getElementById('val-rsi-buy').value),
                            sell: parseInt(document.getElementById('val-rsi-sell').value)
                        },
                        volume: {
                            active: document.getElementById('check-vol').checked,
                            length: parseInt(document.getElementById('val-vol-len').value)
                        },
                        fvg: {
                            active: document.getElementById('check-fvg').checked
                        }
                    }
                };

                btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Duke u lidhur...';
                
                fetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        btn.innerHTML = '<i data-lucide="square" class="w-4 h-4"></i> Ndalo Skanimin';
                        btn.className = "w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-rose-500 font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg";
                    } else {
                        btn.innerHTML = '<i data-lucide="play" class="w-4 h-4"></i> Nis Skanimin';
                        document.getElementById('error-message').innerText = data.error;
                        document.getElementById('error-modal').classList.remove('hidden');
                    }
                    lucide.createIcons();
                });
            } else {
                fetch('/api/stop', { method: 'POST' }).then(() => {
                    btn.innerHTML = '<i data-lucide="play" class="w-4 h-4"></i> Nis Skanimin';
                    btn.className = "w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-rose-900/20";
                    lucide.createIcons();
                });
            }
        }

        function refreshData() {
            fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                const badge = document.getElementById('status-badge');
                if (data.system.scanner) {
                    badge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Skaneri Aktiv (Duke kërkuar sinjale)';
                    badge.className = "mt-1 text-xs font-medium text-emerald-400 flex items-center gap-1.5";
                } else {
                    badge.innerHTML = '<span class="w-2 h-2 rounded-full bg-slate-500"></span> Boti Joaktiv';
                    badge.className = "mt-1 text-xs font-medium text-slate-400 flex items-center gap-1.5";
                }

                document.getElementById('stat-balance').innerText = '$' + data.account.balance.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('stat-equity').innerText = '$' + data.account.equity.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById("last-refresh").innerText = data.time;
                
                const pnlEl = document.getElementById('stat-pnl');
                pnlEl.innerText = (data.account.unrealized >= 0 ? '+$' : '-$') + Math.abs(data.account.unrealized).toLocaleString('en-US', {minimumFractionDigits: 2});
                pnlEl.className = data.account.unrealized >= 0 ? "text-3xl font-bold text-emerald-400" : "text-3xl font-bold text-rose-400";
                
                document.getElementById('stat-positions').innerText = data.account.open_positions;

                // Renditja e Logeve te sistemit dhe skanerit
                const hist = document.getElementById('trade-history');
                hist.innerHTML = data.logs.map(t => {
                    let sideColor = 'text-slate-400 bg-slate-400/10';
                    if (t.lloji === 'SIGNAL') sideColor = 'text-blue-400 bg-blue-400/10';
                    if (t.lloji === 'GABIM') sideColor = 'text-rose-400 bg-rose-400/10';
                    if (t.lloji === 'SISTEMI') sideColor = 'text-emerald-400 bg-emerald-400/10';
                    if (t.lloji === 'SUKSES' || t.lloji === 'TRADE') sideColor = 'text-green-400 bg-green-400/10';
                    
                    return `
                        <tr class="hover:bg-slate-800/30 transition-colors">
                            <td class="py-2.5 whitespace-nowrap">${t.koha}</td>
                            <td class="py-2.5"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${sideColor}">${t.lloji}</span></td>
                            <td class="py-2.5 text-slate-300">${t.mesazhi}</td>
                        </tr>
                    `;
                }).join('');

                document.getElementById('stat-total').innerText = data.stats.total_trades;
                document.getElementById('stat-wins').innerText = data.stats.wins;
                document.getElementById('stat-losses').innerText = data.stats.losses;

                const table = document.getElementById("positions-table");
                if (data.positions.length === 0) {
                    table.innerHTML = `
                        <tr>
                            <td colspan="10" class="text-center text-slate-500 py-8">
                                Nuk ka pozicione aktive
                            </td>
                        </tr>
                    `;
                } else {
                    table.innerHTML = data.positions.map(p => `
                        <tr class="hover:bg-slate-800/30 border-b border-slate-800">
                            <td class="py-2 font-bold text-white">${p.symbol}</td>
                            <td class="py-2">
                                <span class="${p.side === "LONG" ? "text-emerald-400" : "text-rose-400"} font-bold">
                                    ${p.side}
                                </span>
                            </td>
                            <td class="py-2 text-right">${p.entry_price}</td>
                            <td class="py-2 text-right">${p.mark_price}</td>
                            <td class="py-2 text-right">${p.contracts}</td>
                            <td class="py-2 text-right">${p.leverage}x</td>
                            <td class="py-2 text-right">$${p.margin}</td>
                            <td class="py-2 text-right ${p.unrealized >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                                ${p.unrealized >= 0 ? "+" : ""}$${p.unrealized}
                            </td>
                            <td class="py-2 text-right ${p.roe >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                                ${p.roe >= 0 ? "+" : ""}${p.roe}%
                            </td>
                            <td class="py-2 text-right text-slate-300">${p.liquidation}</td>
                        </tr>
                    `).join("");
                }
            });
        }

        setInterval(refreshData, 2000);
    </script>
</body>
</html>
"""

# =====================================================================
# API ROUTES
# =====================================================================
@app.route('/')
@requires_auth
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
@requires_auth
def get_status():
    return jsonify({
        "account": account_overview,
        "stats": setup_stats,
        "positions": list(active_positions),
        "position_details": position_details,
        "closed_trades": list(trade_history),
        "system": system_status,
        "logs": list(bot_logs),
        "time": time.strftime("%H:%M:%S")
    })

@app.route('/api/config', methods=['POST'])
@app.route('/api/start', methods=['POST'])
@requires_auth
def start_bot():
    global bot_thread
    global position_monitor_thread
    global stop_event
    global active_exchange

    data = request.json

    api_key = data.get("api_key", "").strip()
    api_secret = data.get("api_secret", "").strip()

    # Marrim te gjitha parametrat e rinj
    bot_config["risk_usdt"] = float(data.get("risk_usdt", 10))
    bot_config["leverage"] = int(data.get("leverage", 3))
    bot_config["tp_ratio"] = float(data.get("tp_ratio", 2.0))
    bot_config["sl_buffer"] = float(data.get("sl_buffer", 0.3))
    bot_config["watchlist"] = data.get("watchlist", ['BTC/USDT'])
    bot_config["timeframe"] = data.get("timeframe", "5m")
    bot_config["indicators"] = data.get("indicators", bot_config["indicators"])

    if not api_key or not api_secret:
        return jsonify({
            "success": False,
            "error": "API Key dhe Secret janë të detyrueshme për llogarinë REALE!"
        })

    if not bot_config["is_running"]:
        try:
            active_exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                }
            })

            # Asnje sandbox / testnet
            active_exchange.fetch_balance(params={"type": "future"})

            bot_config["is_running"] = True
            system_status["connected"] = True
            system_status["scanner"] = True
            system_status["position_monitor"] = True
            system_status["api_connected"] = True
            system_status["binance_connected"] = True

            stop_event.clear()

            bot_thread = threading.Thread(
                target=analizo_dhe_tregto,
                daemon=True
            )
            bot_thread.start()

            position_monitor_thread = threading.Thread(
                target=monitor_positions,
                daemon=True
            )
            position_monitor_thread.start()

            shto_log("Boti u nis me sukses.", "SISTEMI")
            return jsonify({"success": True})

        except ccxt.AuthenticationError:
            return jsonify({
                "success": False,
                "error": "API Keys të pasakta ose nuk keni aktivizuar Enable Futures në Binance."
            })
        except Exception as e:
            system_status["scanner"] = False
            system_status["position_monitor"] = False
            system_status["api_connected"] = False
            system_status["binance_connected"] = False
            return jsonify({
                "success": False,
                "error": f"Gabim në Binance: {str(e)}"
            })

    return jsonify({"success": True})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global stop_event

    if bot_config["is_running"]:
        bot_config["is_running"] = False
        system_status["connected"] = False
        system_status["scanner"] = False
        system_status["position_monitor"] = False

        stop_event.set()
        clear_active_positions()
        shto_log("Skaneri u ndal nga përdoruesi.", "SISTEMI")

    return jsonify({"success": True})

@app.route("/api/history")
def api_history():
    return jsonify(list(trade_history))

import os

# =====================================================================
# START
# =====================================================================
if __name__ == '__main__':
    print('=' * 70)
    print('NazRmd ProBot GUI - STARTING LIVE SERVER ON RENDER...')
    print('=' * 70)

    # Render ka nevojë për portin e tij dhe adresën 0.0.0.0 për të dalë online
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
