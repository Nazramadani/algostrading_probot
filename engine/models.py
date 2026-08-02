from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class SwingPoint:

    index: int
    timestamp: int
    price: float
    kind: str

    label: str = ""

    strength: float = 0.0
    score: float = 0.0

    rank: int = 0
    distance: float = 0.0

    is_internal: bool = False
    is_external: bool = True

    is_liquidity: bool = False

    broken: bool = False
    confirmed: bool = False

    volume: float = 0.0
    atr: float = 0.0

    timeframe: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class StructureBreak:

    kind: str
    direction: str

    index: int
    timestamp: int

    price: float

    swing_index: int = -1

    strength: float = 0.0
    score: float = 0.0

    confirmed: bool = False

    internal: bool = False
    external: bool = True

    displacement: float = 0.0

    timeframe: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class TrendState:

    direction: str = "neutral"

    bias: str = "neutral"

    confidence: float = 0.0

    strength: float = 0.0

    structure_score: float = 0.0

    bullish_breaks: int = 0
    bearish_breaks: int = 0

    internal_trend: str = "neutral"
    external_trend: str = "neutral"

    last_bos: float = 0.0
    last_choch: float = 0.0

    def to_dict(self):
        return asdict(self)

from dataclasses import dataclass, field, asdict
from typing import List, Optional

# ==========================================================
# RISK FILTER RESULT
# ==========================================================

@dataclass
class RiskFilterResult:
    allowed: bool = False
    score: float = 0.0
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    risk_reward: float = 0.0
    stop_distance: float = 0.0
    atr_distance: float = 0.0
    penalty: float = 0.0

    def to_dict(self):
        return asdict(self)


# ==========================================================
# ORDER BLOCK RESULT
# ==========================================================

@dataclass
class OrderBlockResult:
    bullish: List['OrderBlock'] = field(default_factory=list)
    bearish: List['OrderBlock'] = field(default_factory=list)
    all_blocks: List['OrderBlock'] = field(default_factory=list)
    nearest_bullish: Optional['OrderBlock'] = None
    nearest_bearish: Optional['OrderBlock'] = None

    def to_dict(self):
        return {
            "bullish": [x.to_dict() for x in self.bullish],
            "bearish": [x.to_dict() for x in self.bearish]
        }


# ==========================================================
# LIQUIDITY RESULT
# ==========================================================

@dataclass
class LiquidityResult:
    sweeps: List['LiquidityLevel'] = field(default_factory=list)
    equal_highs: List['EqualLevel'] = field(default_factory=list)
    equal_lows: List['EqualLevel'] = field(default_factory=list)
    buy_side: List['LiquidityLevel'] = field(default_factory=list)
    sell_side: List['LiquidityLevel'] = field(default_factory=list)
    strongest_buy: Optional['LiquidityLevel'] = None
    strongest_sell: Optional['LiquidityLevel'] = None
    current_index: int = 0

    def to_dict(self):
        return {
            "sweeps": [x.to_dict() for x in self.sweeps],
            "equal_highs": [x.to_dict() for x in self.equal_highs],
            "equal_lows": [x.to_dict() for x in self.equal_lows]
        }


# ==========================================================
# MULTI TIMEFRAME RESULT
# ==========================================================

@dataclass
class MultiTimeframeResult:
    trend_4h: str = "neutral"
    trend_1h: str = "neutral"
    trend_15m: str = "neutral"
    trend_5m: str = "neutral"
    aligned: bool = False
    confidence: float = 0.0
    score: float = 0.0
    bias: str = "neutral"
    trade_allowed: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ==========================================================
# TRADE SIGNAL
# ==========================================================

@dataclass
class TradeSignal:
    symbol: str = ""
    side: str = ""
    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    confidence: float = 0.0
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ==========================================================
# TRADE RESULT
# ==========================================================

@dataclass
class TradeResult:
    success: bool = False
    message: str = ""
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    leverage: int = 0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    pnl: float = 0.0
    fee: float = 0.0
    roi: float = 0.0

    def to_dict(self):
        return asdict(self)


# ==========================================================
# POSITION INFO
# ==========================================================

@dataclass
class PositionInfo:
    symbol: str = ""
    side: str = ""
    entry: float = 0.0
    mark: float = 0.0
    quantity: float = 0.0
    leverage: int = 0
    pnl: float = 0.0
    roe: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    liquidation: float = 0.0
    margin: float = 0.0
    status: str = "OPEN"

    def to_dict(self):
        return asdict(self)

# ==========================================================
# DECISION RESULT
# ==========================================================

@dataclass
class DecisionResult:
    allowed: bool = False
    side: str = ""
    confidence: float = 0.0
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_reward: float = 0.0

    def to_dict(self):
        return asdict(self)


# ==========================================================
# MARKET STRUCTURE RESULT
# ==========================================================

@dataclass
class MarketStructureResult:

    # -----------------------------------------
    # Swings
    # -----------------------------------------
    swings: List['SwingPoint'] = field(default_factory=list)
    internal_swings: List['SwingPoint'] = field(default_factory=list)
    external_swings: List['SwingPoint'] = field(default_factory=list)

    # -----------------------------------------
    # BOS / CHOCH
    # -----------------------------------------
    breaks: List['StructureBreak'] = field(default_factory=list)
    internal_breaks: List['StructureBreak'] = field(default_factory=list)
    external_breaks: List['StructureBreak'] = field(default_factory=list)

    # -----------------------------------------
    # Trend
    # -----------------------------------------
    trend: 'TrendState' = field(default_factory=lambda: TrendState())

    # -----------------------------------------
    # Liquidity
    # -----------------------------------------
    liquidity: List['LiquidityLevel'] = field(default_factory=list)
    equal_highs: List['EqualLevel'] = field(default_factory=list)
    equal_lows: List['EqualLevel'] = field(default_factory=list)

    # -----------------------------------------
    # FVG
    # -----------------------------------------
    fvgs: List['FairValueGap'] = field(default_factory=list)
    score: float = 0.0
    fill_percent: float = 0.0
    ce: float = 0.0
    age: int = 0
    invalid: bool = False

    # -----------------------------------------
    # Order Blocks
    # -----------------------------------------
    order_blocks: List['OrderBlock'] = field(default_factory=list)
    bullish_order_blocks: List['OrderBlock'] = field(default_factory=list)
    bearish_order_blocks: List['OrderBlock'] = field(default_factory=list)

    # -----------------------------------------
    # Statistics
    # -----------------------------------------
    structure_score: float = 0.0
    confidence: float = 0.0
    bullish_score: float = 0.0
    bearish_score: float = 0.0

    # -----------------------------------------
    # Market Bias
    # -----------------------------------------
    bias: str = "neutral"
    trade_side: str = ""
    trade_allowed: bool = False

    # -----------------------------------------
    # Helpers
    # -----------------------------------------
    @property
    def last_swing(self):
        if self.swings:
            return self.swings[-1]
        return None

    @property
    def last_break(self):
        if self.breaks:
            return self.breaks[-1]
        return None

    # -----------------------------------------
    # Export
    # -----------------------------------------
    def to_dict(self):
        return {
            "trend": self.trend.to_dict() if hasattr(self.trend, 'to_dict') else self.trend,
            "structure_score": self.structure_score,
            "confidence": self.confidence,
            "bias": self.bias,
            "trade_allowed": self.trade_allowed,
            "in_premium": self.in_premium,
            "in_discount": self.in_discount,
            "swings": [s.to_dict() for s in self.swings],
            "breaks": [b.to_dict() for b in self.breaks],
            "liquidity": [l.to_dict() for l in self.liquidity],
            "equal_highs": [e.to_dict() for e in self.equal_highs],
            "equal_lows": [e.to_dict() for e in self.equal_lows],
            "fvgs": [f.to_dict() for f in self.fvgs],
            "order_blocks": [o.to_dict() for o in self.order_blocks]
        }

# ==========================================================
# FAIR VALUE GAP (Përditësuar për v3.0)
# ==========================================================
@dataclass
class FairValueGap:
    direction: str
    top: float
    bottom: float
    index: int
    timestamp: int = 0
    mitigated: bool = False
    filled: bool = False
    active: bool = True
    invalid: bool = False
    strength: float = 0.0
    score: float = 0.0
    distance: float = 0.0
    fill_percent: float = 0.0
    age: int = 0
    ce: float = 0.0

    @property
    def size(self):
        return abs(self.top - self.bottom)

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)

@dataclass
class FVGResult:
    bullish: list = field(default_factory=list)
    bearish: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    active: list = field(default_factory=list)
    mitigated: list = field(default_factory=list)
    filled: list = field(default_factory=list)
    nearest: any = None
    strongest: any = None
    active_count: int = 0
    mitigated_count: int = 0
    filled_count: int = 0
    current_index: int = 0

@dataclass
class MarketRegimeResult:

    regime: str = "UNKNOWN"

    trend_direction: str = "neutral"

    trend_strength: float = 0.0

    volatility: str = "NORMAL"

    volatility_score: float = 0.0

    expansion: bool = False

    compression: bool = False

    ranging: bool = False

    trending: bool = False

    reversal: bool = False

    tradable: bool = False

    confidence: float = 0.0

    score: float = 0.0

    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
