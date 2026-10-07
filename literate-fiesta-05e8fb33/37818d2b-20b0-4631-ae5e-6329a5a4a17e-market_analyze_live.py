#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Indian Market Analyzer
---------------------------
- Fetches recent intraday NSE data using yfinance
- Supports Nifty 50 and NSE stocks (.NS)
- Calculates EMA20, EMA50, SMA200, RSI(14), MACD, VWAP, ATR
- Detects volume spikes and basic support/resistance
- Produces a rule-based BUY / SELL / HOLD / WATCH signal
- Refreshes automatically during market hours
- Cross-checks price with NSE India and Moneycontrol, reads the NSE option
  chain (PCR, OI walls, max pain, IV) and India VIX, and prints one
  consensus, defined-risk option idea

IMPORTANT:
Yahoo Finance data should be treated as delayed/near-real-time depending on
the instrument/account/data source. This is NOT a guaranteed exchange-grade
real-time trading feed.
"""

import sys
import io
import time
import warnings
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IST = ZoneInfo("Asia/Kolkata")

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

SYMBOLS = {
    "^NSEI": "Nifty 50",
    #"RELIANCE.NS": "Reliance Industries",
   # "TCS.NS": "TCS",
}

# For intraday yfinance data, 5m is a practical default.
INTERVAL = "5m"
PERIOD = "5d"

# Refresh interval in seconds.
REFRESH_SECONDS = 60

# Number of candles used for support/resistance.
SR_LOOKBACK = 20

# Volume spike threshold: current volume / average volume.
VOLUME_SPIKE_MULTIPLIER = 1.5

# Set to False if you only want one scan.
CONTINUOUS_MODE = True

# Cross-source correlation (NSE India + Moneycontrol + Yahoo) and option idea.
# Keys are Yahoo symbols. nse_index = name in NSE allIndices, nse_oc = NSE
# option-chain symbol, mc_id = Moneycontrol price-feed index id.
MULTI_SOURCE = {
    "^NSEI": {"nse_index": "NIFTY 50", "nse_oc": "NIFTY", "mc_id": "in%3BNSX"},
}
ENABLE_MULTI_SOURCE = True

# Fallback lot size if Moneycontrol does not provide one. Verify with NSE.
DEFAULT_LOT_SIZE = {"NIFTY": 65}

# India VIX at/above this is treated as "premium rich" (favour selling spreads).
HIGH_VIX = 16.0

# Max acceptable price difference between sources before confidence drops.
PRICE_DEVIATION_WARN_PCT = 0.25

HTTP_TIMEOUT = 15
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# MARKET HOURS
# ---------------------------------------------------------------------------

def is_market_open(now=None):
    """Return True during normal NSE equity market hours, Mon-Fri."""
    now = now or datetime.now(IST)

    if now.weekday() >= 5:
        return False

    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)

    return market_open <= now.time() <= market_close


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

def get_intraday_data(symbol):
    """Download recent intraday OHLCV data."""
    try:
        df = yf.download(
            symbol,
            period=PERIOD,
            interval=INTERVAL,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return None

        # Handle yfinance MultiIndex columns.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close", "Volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"[!] {symbol}: missing columns: {missing}")
            return None

        df = df[required].copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            print(f"[!] {symbol}: data has no timestamp index")
            return None

        if df.index.tz is None:
            df.index = df.index.tz_localize(IST)
        else:
            df.index = df.index.tz_convert(IST)

        for col in required:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        df = df[~df.index.duplicated(keep="last")].sort_index()

        # Yahoo timestamps intraday candles by their start time. Exclude the
        # currently forming candle so indicators use only completed bars.
        try:
            candle_duration = pd.Timedelta(INTERVAL)
        except ValueError:
            candle_duration = None

        if candle_duration is not None:
            now = pd.Timestamp.now(tz=IST)
            df = df[df.index + candle_duration <= now]

        df = df[df["Close"] > 0]

        if len(df) < 60:
            print(f"[!] {symbol}: insufficient intraday data ({len(df)} candles)")
            return None

        return df

    except Exception as exc:
        print(f"[!] {symbol}: data error: {exc}")
        return None


# ---------------------------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------------------------

def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss > 0), 0)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss == 0), 50)
    return rsi


def calculate_vwap(df):
    """
    Session VWAP approximation.
    Resets at each trading date.
    """
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    session_date = pd.Series(df.index.date, index=df.index)

    cumulative_pv = (typical_price * df["Volume"]).groupby(session_date).cumsum()
    cumulative_volume = df["Volume"].groupby(session_date).cumsum()

    return cumulative_pv / cumulative_volume.replace(0, np.nan)


def calculate_atr(df, period=14):
    previous_close = df["Close"].shift(1)

    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    df["RSI14"] = calculate_rsi(df["Close"], 14)

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    df["VWAP"] = calculate_vwap(df)
    df["ATR14"] = calculate_atr(df, 14)

    # Compare with earlier bars, not an average that includes the current bar.
    df["VOL_AVG20"] = df["Volume"].shift(1).rolling(20).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_AVG20"].replace(0, np.nan)

    return df


# ---------------------------------------------------------------------------
# SUPPORT / RESISTANCE
# ---------------------------------------------------------------------------

def support_resistance(df, lookback=SR_LOOKBACK):
    recent = df.tail(lookback)

    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())

    return support, resistance


# ---------------------------------------------------------------------------
# SIGNAL ENGINE
# ---------------------------------------------------------------------------

def generate_signal(df):
    """
    Rule-based signal.

    Scores compare available indicators only. VWAP and volume are omitted when
    the instrument does not provide usable volume data (common for indices).

    SELL points:
      +1 price below EMA20
      +1 EMA20 below EMA50
      +1 price below VWAP
      +1 MACD below signal
      +1 RSI between 30 and 50
      +1 volume spike

    This is an analytical rule set, NOT financial advice.
    """
    row = df.iloc[-1]

    buy_score = 0
    sell_score = 0
    core_factors = 0
    reasons = []

    price = float(row["Close"])
    ema20 = float(row["EMA20"])
    ema50 = float(row["EMA50"])
    vwap = float(row["VWAP"]) if pd.notna(row["VWAP"]) else None
    rsi = float(row["RSI14"])
    macd = float(row["MACD"])
    macd_signal = float(row["MACD_SIGNAL"])
    vol_ratio = float(row["VOL_RATIO"]) if pd.notna(row["VOL_RATIO"]) else None

    # Trend
    core_factors += 1
    if price > ema20:
        buy_score += 1
        reasons.append("Price > EMA20")
    elif price < ema20:
        sell_score += 1
        reasons.append("Price < EMA20")

    core_factors += 1
    if ema20 > ema50:
        buy_score += 1
        reasons.append("EMA20 > EMA50")
    elif ema20 < ema50:
        sell_score += 1
        reasons.append("EMA20 < EMA50")

    # VWAP
    if vwap is not None:
        core_factors += 1
        if price > vwap:
            buy_score += 1
            reasons.append("Price > VWAP")
        elif price < vwap:
            sell_score += 1
            reasons.append("Price < VWAP")
    else:
        reasons.append("VWAP unavailable (no usable volume)")

    # MACD
    core_factors += 1
    if macd > macd_signal:
        buy_score += 1
        reasons.append("MACD bullish")
    elif macd < macd_signal:
        sell_score += 1
        reasons.append("MACD bearish")

    # RSI
    if pd.notna(rsi):
        core_factors += 1
    if 50 <= rsi < 70:
        buy_score += 1
        reasons.append("RSI bullish zone")
    elif 30 < rsi < 50:
        sell_score += 1
        reasons.append("RSI bearish zone")
    elif rsi >= 70:
        reasons.append("RSI overbought")
    elif rsi <= 30:
        reasons.append("RSI oversold")

    # Volume
    volume_available = (
        vol_ratio is not None
        and vol_ratio > 0
        and float(row["Volume"]) > 0
    )
    volume_point_added = False
    if volume_available and vol_ratio >= VOLUME_SPIKE_MULTIPLIER:
        if buy_score > sell_score:
            buy_score += 1
            volume_point_added = True
            reasons.append("Bullish volume spike")
        elif sell_score > buy_score:
            sell_score += 1
            volume_point_added = True
            reasons.append("Bearish volume spike")
        else:
            reasons.append("Volume spike")

    max_score = core_factors + int(volume_point_added)
    threshold = int(np.ceil(max_score * 0.75))

    if buy_score >= threshold and buy_score >= sell_score + 2:
        signal = "BUY"
    elif sell_score >= threshold and sell_score >= buy_score + 2:
        signal = "SELL"
    elif buy_score > sell_score:
        signal = "BULLISH / WATCH"
    elif sell_score > buy_score:
        signal = "BEARISH / WATCH"
    else:
        signal = "HOLD / MIXED"

    return {
        "signal": signal,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "max_score": max_score,
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------------------------

def format_timestamp(index_value):
    try:
        ts = pd.Timestamp(index_value)
        if ts.tzinfo is None:
            ts = ts.tz_localize(IST)
        else:
            ts = ts.tz_convert(IST)
        return ts.strftime("%Y-%m-%d %H:%M:%S IST")
    except Exception:
        return str(index_value)


def analyze_symbol(symbol, name):
    df = get_intraday_data(symbol)

    if df is None:
        return None

    df = add_indicators(df)

    row = df.iloc[-1]
    signal = generate_signal(df)
    support, resistance = support_resistance(df)

    price = float(row["Close"])
    previous = float(df.iloc[-2]["Close"])
    bar_change_pct = ((price - previous) / previous) * 100

    session_dates = pd.Index(df.index.date).unique()
    session_change_pct = None
    if len(session_dates) >= 2:
        prior_session = df.loc[df.index.date == session_dates[-2], "Close"]
        if not prior_session.empty and float(prior_session.iloc[-1]) > 0:
            session_change_pct = (
                (price - float(prior_session.iloc[-1]))
                / float(prior_session.iloc[-1])
                * 100
            )

    candle_duration = pd.Timedelta(INTERVAL)
    candle_close_time = pd.Timestamp(df.index[-1]) + candle_duration
    now = pd.Timestamp.now(tz=IST)
    quote_age_minutes = max(
        0.0, (now - candle_close_time).total_seconds() / 60
    )
    stale_limit_minutes = max(15.0, candle_duration.total_seconds() / 60 * 3)
    stale_during_market = is_market_open(now.to_pydatetime()) and (
        quote_age_minutes > stale_limit_minutes
    )
    if stale_during_market:
        signal["signal"] = "STALE DATA / NO SIGNAL"

    print("\n" + "=" * 78)
    print(f"{name} ({symbol})")
    print("=" * 78)

    print(f"Last completed candle: {format_timestamp(candle_close_time)}")
    print(f"Quote age:     {quote_age_minutes:.1f} minutes")
    print(f"Price:         ₹{price:,.2f} (last completed candle close)")
    if session_change_pct is not None:
        print(f"Session change:{session_change_pct:+.2f}% (vs prior session close)")
    else:
        print("Session change: N/A (prior session data unavailable)")
    print(f"Bar change:    {bar_change_pct:+.2f}% (vs previous {INTERVAL} candle)")
    print(f"High / Low:    ₹{float(row['High']):,.2f} / ₹{float(row['Low']):,.2f}")
    print(f"Volume:        {int(float(row['Volume'])):,}")

    print("\nIndicators")
    print(f"  EMA20:       ₹{float(row['EMA20']):,.2f}")
    print(f"  EMA50:       ₹{float(row['EMA50']):,.2f}")
    print(f"  SMA200:      ₹{float(row['SMA200']):,.2f}" if pd.notna(row["SMA200"]) else "  SMA200:      N/A")
    print(f"  RSI14:       {float(row['RSI14']):.2f}")
    print(f"  MACD:        {float(row['MACD']):.4f}")
    print(f"  MACD Signal: {float(row['MACD_SIGNAL']):.4f}")
    print(
        f"  VWAP:        ₹{float(row['VWAP']):,.2f}"
        if pd.notna(row["VWAP"])
        else "  VWAP:        N/A (no usable volume data)"
    )
    print(f"  ATR14:       ₹{float(row['ATR14']):,.2f}")
    print(
        f"  Volume vs prior 20 bars: {float(row['VOL_RATIO']):.2f}x"
        if pd.notna(row["VOL_RATIO"]) and float(row["Volume"]) > 0
        else "  Volume vs prior 20 bars: N/A (unavailable or zero volume)"
    )

    print("\nSupport / Resistance")
    print(f"  Support:     ₹{support:,.2f}")
    print(f"  Resistance:  ₹{resistance:,.2f}")

    print("\nSignal")
    print(f"  {signal['signal']}")
    print(f"  Buy score:   {signal['buy_score']}/{signal['max_score']}")
    print(f"  Sell score:  {signal['sell_score']}/{signal['max_score']}")
    print("  Reasons:     " + ", ".join(signal["reasons"]))
    print("  Meaning:     SELL = bearish indicator setup only; no order is placed.")
    print("               It does not by itself mean short the market or sell holdings.")
    if stale_during_market:
        print("  Warning:     Latest completed candle is stale during market hours.")

    print("=" * 78)

    return {
        "symbol": symbol,
        "name": name,
        "price": price,
        "change_pct": session_change_pct,
        "bar_change_pct": bar_change_pct,
        "rsi": float(row["RSI14"]),
        "vwap": float(row["VWAP"]),
        "signal": signal["signal"],
        "buy_score": signal["buy_score"],
        "sell_score": signal["sell_score"],
        "max_score": signal["max_score"],
        "atr": float(row["ATR14"]),
        "ema20": float(row["EMA20"]),
        "ema50": float(row["EMA50"]),
        "stale": stale_during_market,
        "timestamp": format_timestamp(candle_close_time),
        "quote_age_minutes": quote_age_minutes,
    }


# ---------------------------------------------------------------------------
# NSE INDIA + MONEYCONTROL
# ---------------------------------------------------------------------------
# These are the public JSON endpoints used by the nseindia.com and
# moneycontrol.com websites. They are unofficial, may change or rate-limit
# without notice, and are intended for personal use only.

_nse_session = None


def _get_nse_session(force_new=False):
    """NSE requires browser-like headers and cookies from the website first."""
    global _nse_session
    if _nse_session is None or force_new:
        s = requests.Session()
        s.headers.update({
            "User-Agent": BROWSER_UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/option-chain",
        })
        s.get("https://www.nseindia.com/option-chain", timeout=HTTP_TIMEOUT)
        _nse_session = s
    return _nse_session


def nse_get_json(path):
    url = "https://www.nseindia.com" + path
    for attempt in range(2):
        try:
            r = _get_nse_session(force_new=attempt > 0).get(url, timeout=HTTP_TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except (requests.RequestException, ValueError):
            pass
    return None


def _num(value):
    try:
        v = float(str(value).replace(",", ""))
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def fetch_nse_index(index_name):
    """Index quote, India VIX and breadth from NSE allIndices."""
    data = nse_get_json("/api/allIndices")
    if not data:
        return None

    rows = {d.get("index"): d for d in data.get("data", [])}
    idx = rows.get(index_name)
    if not idx:
        return None

    vix = rows.get("INDIA VIX", {})
    return {
        "price": _num(idx.get("last")),
        "prev_close": _num(idx.get("previousClose")),
        "change_pct": _num(idx.get("percentChange")),
        "open": _num(idx.get("open")),
        "high": _num(idx.get("high")),
        "low": _num(idx.get("low")),
        "advances": _num(idx.get("advances")),
        "declines": _num(idx.get("declines")),
        "vix": _num(vix.get("last")),
        "vix_change_pct": _num(vix.get("percentChange")),
        "timestamp": data.get("timestamp"),
    }


def _pick_expiry(expiries, now):
    """Nearest expiry that is still tradable (today counts until 15:30 IST)."""
    for e in expiries:
        try:
            d = datetime.strptime(e, "%d-%b-%Y").date()
        except ValueError:
            continue
        if d > now.date() or (d == now.date() and now.time() < dt_time(15, 30)):
            return e
    return None


def fetch_nse_option_chain(oc_symbol, spot_hint=None):
    """Nearest-expiry option chain metrics: PCR, OI walls, max pain, ATM IV."""
    now = datetime.now(IST)
    info = nse_get_json(f"/api/option-chain-contract-info?symbol={oc_symbol}")
    if not info:
        return None

    expiry = _pick_expiry(info.get("expiryDates", []), now)
    if not expiry:
        return None

    oc = nse_get_json(
        f"/api/option-chain-v3?type=Indices&symbol={oc_symbol}&expiry={expiry}"
    )
    if not oc:
        return None

    records = oc.get("records", {})
    rows = []
    for item in records.get("data", []):
        ce, pe = item.get("CE") or {}, item.get("PE") or {}
        strike = _num(item.get("strikePrice") or ce.get("strikePrice") or pe.get("strikePrice"))
        if strike is None:
            continue
        rows.append({
            "strike": strike,
            "ce_oi": _num(ce.get("openInterest")) or 0.0,
            "pe_oi": _num(pe.get("openInterest")) or 0.0,
            "ce_chg_oi": _num(ce.get("changeinOpenInterest")) or 0.0,
            "pe_chg_oi": _num(pe.get("changeinOpenInterest")) or 0.0,
            "ce_ltp": _num(ce.get("lastPrice")),
            "pe_ltp": _num(pe.get("lastPrice")),
            "ce_iv": _num(ce.get("impliedVolatility")),
            "pe_iv": _num(pe.get("impliedVolatility")),
        })

    if len(rows) < 5:
        return None

    chain = pd.DataFrame(rows).groupby("strike", as_index=False).sum(min_count=1)
    chain = chain.sort_values("strike").reset_index(drop=True)

    spot = _num(records.get("underlyingValue")) or spot_hint
    if spot is None:
        return None

    strikes = chain["strike"].to_numpy()
    step = float(pd.Series(strikes).diff().dropna().mode().iloc[0])
    atm = float(strikes[np.abs(strikes - spot).argmin()])

    # Use strikes within +/-10% of spot so deep, illiquid strikes don't dominate.
    near = chain[(chain["strike"] >= spot * 0.9) & (chain["strike"] <= spot * 1.1)]
    total_ce_oi = float(near["ce_oi"].sum())
    total_pe_oi = float(near["pe_oi"].sum())
    pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else None

    above = near[near["strike"] >= spot]
    below = near[near["strike"] <= spot]
    call_wall = float(above.loc[above["ce_oi"].idxmax(), "strike"]) if not above.empty else None
    put_wall = float(below.loc[below["pe_oi"].idxmax(), "strike"]) if not below.empty else None

    # Max pain: settlement strike that minimises total option-writer payout.
    ce_oi = chain["ce_oi"].to_numpy()
    pe_oi = chain["pe_oi"].to_numpy()
    payout = [
        float((ce_oi * np.clip(k - strikes, 0, None)).sum()
              + (pe_oi * np.clip(strikes - k, 0, None)).sum())
        for k in strikes
    ]
    max_pain = float(strikes[int(np.argmin(payout))])

    atm_row = chain[chain["strike"] == atm].iloc[0]
    ivs = [v for v in (atm_row["ce_iv"], atm_row["pe_iv"]) if pd.notna(v) and v > 0]
    atm_iv = float(np.mean(ivs)) if ivs else None
    straddle = None
    if pd.notna(atm_row["ce_ltp"]) and pd.notna(atm_row["pe_ltp"]):
        straddle = float(atm_row["ce_ltp"] + atm_row["pe_ltp"])

    return {
        "expiry": expiry,
        "timestamp": records.get("timestamp"),
        "spot": spot,
        "step": step,
        "atm": atm,
        "pcr": pcr,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "ce_oi_added": float(near["ce_chg_oi"].sum()),
        "pe_oi_added": float(near["pe_chg_oi"].sum()),
        "max_pain": max_pain,
        "atm_iv": atm_iv,
        "straddle": straddle,
        "chain": chain,
    }


def fetch_moneycontrol_index(mc_id):
    url = f"https://priceapi.moneycontrol.com/pricefeed/notapplicable/inidicesindia/{mc_id}"
    try:
        r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            return None
        d = r.json().get("data") or {}
    except (requests.RequestException, ValueError):
        return None

    price = _num(d.get("pricecurrent"))
    if price is None:
        return None

    return {
        "price": price,
        "prev_close": _num(d.get("priceprevclose")),
        "change_pct": _num(d.get("pricepercentchange")),
        "advances": _num(d.get("adv")),
        "declines": _num(d.get("decl")),
        "dma50": _num(d.get("50d")),
        "dma200": _num(d.get("200d")),
        "lot_size": _num(d.get("MKT_LOT")),
        "market_state": d.get("market_state"),
        "timestamp": d.get("lastupd"),
    }


# ---------------------------------------------------------------------------
# CORRELATION + CONSENSUS
# ---------------------------------------------------------------------------

def _clip(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def _round_strike(value, step):
    return float(round(value / step) * step)


def _ltp(chain, strike, side):
    row = chain[chain["strike"] == strike]
    if row.empty:
        return None
    v = row.iloc[0]["ce_ltp" if side == "CE" else "pe_ltp"]
    return float(v) if pd.notna(v) and v > 0 else None


def build_consensus(yahoo, nse, oc, mc):
    """
    Combine all sources into one score in [-1, +1].
    Each component is scored -1 (bearish) .. +1 (bullish) with a weight.
    """
    components = []

    if yahoo and yahoo.get("max_score"):
        tech = (yahoo["buy_score"] - yahoo["sell_score"]) / yahoo["max_score"]
        components.append(("Yahoo 5m technicals", _clip(tech), 2.0))

    day_change = next(
        (s["change_pct"] for s in (nse, mc) if s and s.get("change_pct") is not None),
        None,
    )
    if day_change is not None:
        components.append(("Day change (NSE/MC)", _clip(day_change / 0.75), 1.0))

    for label, src in (("NSE breadth", nse), ("Moneycontrol breadth", mc)):
        if src and src.get("advances") is not None and src.get("declines") is not None:
            total = src["advances"] + src["declines"]
            if total > 0:
                components.append(
                    (label, (src["advances"] - src["declines"]) / total, 0.5)
                )

    if oc and oc.get("pcr") is not None:
        pcr = oc["pcr"]
        # Moderately high PCR = put writers defending (bullish). Extremes are
        # treated as crowded and damped toward neutral.
        if pcr > 1.6 or pcr < 0.5:
            score = _clip((pcr - 1) / 0.3) * 0.3
        else:
            score = _clip((pcr - 1) / 0.3)
        components.append((f"NSE OI PCR {pcr:.2f}", score, 1.0))

        oi_flow = oc["pe_oi_added"] - oc["ce_oi_added"]
        denom = abs(oc["pe_oi_added"]) + abs(oc["ce_oi_added"])
        if denom > 0:
            components.append(("NSE OI change (put vs call writing)", oi_flow / denom, 0.5))

    spot = next((s["price"] for s in (nse, mc) if s and s.get("price")), None)
    if mc and spot:
        trend = 0.0
        n = 0
        for dma in (mc.get("dma50"), mc.get("dma200")):
            if dma:
                trend += 1.0 if spot > dma else -1.0
                n += 1
        if n:
            components.append(("Moneycontrol 50/200 DMA trend", trend / n, 1.0))

    if not components:
        return None

    total_w = sum(w for _, _, w in components)
    score = sum(s * w for _, s, w in components) / total_w
    agree_bull = sum(1 for _, s, _ in components if s > 0.1)
    agree_bear = sum(1 for _, s, _ in components if s < -0.1)

    if score >= 0.3:
        bias = "BULLISH"
    elif score <= -0.3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL / RANGE"

    return {
        "score": score,
        "bias": bias,
        "components": components,
        "agree_bull": agree_bull,
        "agree_bear": agree_bear,
    }


def suggest_option_trade(consensus, oc, nse, mc, yahoo, price_conflict, oc_symbol):
    """Turn the consensus into one defined-risk option idea (not advice)."""
    if not consensus or not oc:
        return ["No option idea: option-chain data unavailable."]

    chain, step, atm = oc["chain"], oc["step"], oc["atm"]
    spot = oc["spot"]
    vix = nse.get("vix") if nse else None
    rich = (vix is not None and vix >= HIGH_VIX) or (
        oc.get("atm_iv") is not None and oc["atm_iv"] >= HIGH_VIX
    )
    bias, score = consensus["bias"], consensus["score"]
    lot = (mc or {}).get("lot_size") or DEFAULT_LOT_SIZE.get(oc_symbol)
    call_wall, put_wall = oc["call_wall"], oc["put_wall"]
    width = 2 * step
    lines = []

    strong = abs(score) >= 0.5
    agree = consensus["agree_bull"] if score > 0 else consensus["agree_bear"]
    confidence = "HIGH" if strong and agree >= 4 else "MEDIUM" if abs(score) >= 0.3 else "LOW"
    if price_conflict or (yahoo and yahoo.get("stale")):
        confidence = "LOW"

    def debit_spread(side, buy_k, sell_k):
        b, s = _ltp(chain, buy_k, side), _ltp(chain, sell_k, side)
        if b is None or s is None:
            return None
        debit = b - s
        max_profit = abs(sell_k - buy_k) - debit
        return (f"Buy {oc_symbol} {buy_k:.0f} {side} @ ~{b:.2f}, "
                f"Sell {sell_k:.0f} {side} @ ~{s:.2f} | Net debit ~{debit:.2f} "
                f"| Max profit ~{max_profit:.2f} | Max loss ~{debit:.2f} (per unit)")

    def credit_spread(side, sell_k, buy_k):
        s, b = _ltp(chain, sell_k, side), _ltp(chain, buy_k, side)
        if b is None or s is None:
            return None
        credit = s - b
        max_loss = abs(sell_k - buy_k) - credit
        return (f"Sell {oc_symbol} {sell_k:.0f} {side} @ ~{s:.2f}, "
                f"Buy {buy_k:.0f} {side} @ ~{b:.2f} | Net credit ~{credit:.2f} "
                f"| Max profit ~{credit:.2f} | Max loss ~{max_loss:.2f} (per unit)")

    if bias == "BULLISH":
        if rich:
            sell_k = min(put_wall or atm - step, atm - step)
            idea = "Bull put spread (premium is rich, sell downside)"
            legs = credit_spread("PE", sell_k, sell_k - width)
        else:
            idea = "Bull call spread (premium is cheap, buy upside)"
            sell_k = atm + width
            if call_wall and atm < call_wall <= atm + 3 * step:
                sell_k = call_wall
            legs = debit_spread("CE", atm, sell_k)
        invalidation = f"spot sustains below {put_wall or atm - step:.0f} (put-OI support)"
    elif bias == "BEARISH":
        if rich:
            sell_k = max(call_wall or atm + step, atm + step)
            idea = "Bear call spread (premium is rich, sell upside)"
            legs = credit_spread("CE", sell_k, sell_k + width)
        else:
            idea = "Bear put spread (premium is cheap, buy downside)"
            sell_k = atm - width
            if put_wall and atm - 3 * step <= put_wall < atm:
                sell_k = put_wall
            legs = debit_spread("PE", atm, sell_k)
        invalidation = f"spot sustains above {call_wall or atm + step:.0f} (call-OI resistance)"
    else:
        if rich and call_wall and put_wall and put_wall < spot < call_wall:
            idea = "Iron condor around the OI range (range-bound + rich premium)"
            ce = credit_spread("CE", call_wall, call_wall + width)
            pe = credit_spread("PE", put_wall, put_wall - width)
            legs = " || ".join(x for x in (pe, ce) if x) or None
            invalidation = f"spot breaks outside {put_wall:.0f}-{call_wall:.0f}"
        else:
            idea = "NO TRADE - wait for a breakout (signals mixed, premium not rich)"
            legs = None
            lvl = f"{put_wall:.0f} / {call_wall:.0f}" if put_wall and call_wall else "OI walls"
            invalidation = f"re-evaluate on a 5m close beyond {lvl}"

    lines.append(f"Bias:        {bias} (consensus score {score:+.2f}, confidence {confidence})")
    lines.append(f"Volatility:  India VIX {vix if vix is not None else 'N/A'}"
                 f"{' -> premium rich' if rich else ' -> premium normal/cheap'}")
    lines.append(f"Expiry:      {oc['expiry']}  |  Lot size: {int(lot) if lot else 'verify'}")
    lines.append(f"Suggestion:  {idea}")
    if legs:
        lines.append(f"Legs:        {legs}")
        if lot:
            lines.append(f"             Multiply per-unit values by lot size ({int(lot)}) for rupee P&L.")
    if legs or "NO TRADE" not in idea:
        lines.append(f"Exit / stop: Exit if {invalidation}; book credit spreads at ~50% of max profit.")
    else:
        lines.append(f"Trigger:     {invalidation[0].upper() + invalidation[1:]}.")
    if yahoo and yahoo.get("atr"):
        lines.append(f"Risk ref:    5m ATR ~{yahoo['atr']:.1f} pts; "
                     f"ATM straddle (expected move to expiry) ~{oc['straddle'] or 0:.1f} pts")
    if confidence == "LOW":
        lines.append("Caution:     LOW confidence - prefer to stay flat or trade minimum size.")
    if not is_market_open():
        lines.append("Note:        Market closed - premiums are last-traded; recheck after 9:30 IST.")
    return lines


def multi_source_report(yahoo_result):
    cfg = MULTI_SOURCE.get(yahoo_result["symbol"]) if yahoo_result else None
    if not cfg:
        return

    nse = fetch_nse_index(cfg["nse_index"])
    mc = fetch_moneycontrol_index(cfg["mc_id"])
    oc = fetch_nse_option_chain(cfg["nse_oc"], spot_hint=(nse or {}).get("price"))

    print("\n" + "=" * 78)
    print(f"CROSS-SOURCE CHECK: {yahoo_result['name']}  (NSE India / Moneycontrol / Yahoo)")
    print("=" * 78)

    prices = {"Yahoo (last 5m close)": yahoo_result["price"]}
    if nse and nse.get("price"):
        prices["NSE India"] = nse["price"]
    if mc and mc.get("price"):
        prices["Moneycontrol"] = mc["price"]

    ref = prices.get("NSE India") or prices.get("Moneycontrol") or yahoo_result["price"]
    for src, p in prices.items():
        print(f"  {src:<24} ₹{p:,.2f}  ({(p - ref) / ref * 100:+.3f}% vs reference)")
    deviation = (max(prices.values()) - min(prices.values())) / ref * 100
    # Yahoo lags by up to one candle, so only flag a conflict between NSE and MC,
    # or a gross deviation involving Yahoo.
    exch = [v for k, v in prices.items() if not k.startswith("Yahoo")]
    exch_dev = (max(exch) - min(exch)) / ref * 100 if len(exch) > 1 else 0.0
    price_conflict = exch_dev > PRICE_DEVIATION_WARN_PCT or deviation > 1.0
    print(f"  Max spread across sources: {deviation:.3f}%"
          f"{'  <-- SOURCES DISAGREE' if price_conflict else '  (consistent)'}")

    if nse:
        print(f"\n  NSE:  change {nse['change_pct']:+.2f}% | A/D {nse['advances']:.0f}/{nse['declines']:.0f}"
              f" | India VIX {nse['vix']} ({(nse['vix_change_pct'] or 0):+.2f}%) | {nse['timestamp']}")
    else:
        print("\n  NSE:  unavailable")
    if mc:
        print(f"  MC:   change {(mc['change_pct'] or 0):+.2f}% | A/D {mc['advances']:.0f}/{mc['declines']:.0f}"
              f" | 50DMA {mc['dma50']} | 200DMA {mc['dma200']} | {mc['market_state']} {mc['timestamp']}")
    else:
        print("  MC:   unavailable")
    if oc:
        print(f"  OI:   expiry {oc['expiry']} | PCR {oc['pcr']:.2f} | Put wall {oc['put_wall']:.0f}"
              f" | Call wall {oc['call_wall']:.0f} | Max pain {oc['max_pain']:.0f}"
              f" | ATM {oc['atm']:.0f} IV {oc['atm_iv'] or 'N/A'} | {oc['timestamp']}")
    else:
        print("  OI:   NSE option chain unavailable")

    consensus = build_consensus(yahoo_result, nse, oc, mc)
    if consensus:
        print("\n  Consensus components (-1 bearish .. +1 bullish, weight):")
        for label, s, w in consensus["components"]:
            print(f"    {label:<38} {s:+.2f}  x{w}")

    print("\n" + "-" * 78)
    print("ONE COMMON OPTION-TRADING IDEA  (educational, NOT financial advice)")
    print("-" * 78)
    for line in suggest_option_trade(
        consensus, oc, nse, mc, yahoo_result, price_conflict, cfg["nse_oc"]
    ):
        print("  " + line)
    print("=" * 78)


# ---------------------------------------------------------------------------
# SCANNER
# ---------------------------------------------------------------------------

def scan_market():
    now = datetime.now(IST)

    print("\n" + "#" * 78)
    print("LIVE INDIAN MARKET ANALYZER")
    print(f"Scan time: {now.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Interval:  {INTERVAL}")
    print(f"Data:      Yahoo Finance")
    print("#" * 78)

    if not is_market_open(now):
        print("\n[!] NSE normal trading session is currently closed.")
        print("[i] The script can still retrieve the most recent available candles.\n")

    results = []

    for symbol, name in SYMBOLS.items():
        result = analyze_symbol(symbol, name)
        if result:
            results.append(result)

    if results:
        print("\n" + "=" * 78)
        print("MARKET SUMMARY")
        print("=" * 78)
        print(f"{'Symbol':<18} {'Price':>12} {'Session':>10} {'RSI':>8} {'Signal':<24}")
        print("-" * 78)

        for r in results:
            session_change = (
                f"{r['change_pct']:+.2f}%"
                if r["change_pct"] is not None
                else "N/A"
            )
            print(
                f"{r['symbol']:<18} "
                f"₹{r['price']:>10,.2f} "
                f"{session_change:>10} "
                f"{r['rsi']:>7.2f} "
                f"{r['signal']:<24}"
            )

        print("=" * 78)

    if ENABLE_MULTI_SOURCE:
        for r in results:
            try:
                multi_source_report(r)
            except Exception as exc:
                print(f"[!] {r['symbol']}: cross-source check failed: {exc}")

    return results


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def main():
    if not CONTINUOUS_MODE:
        scan_market()
        return

    print("Press Ctrl+C to stop.")

    try:
        while True:
            scan_market()

            print(f"\nNext scan in {REFRESH_SECONDS} seconds...")
            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\n\nAnalyzer stopped by user.")


if __name__ == "__main__":
    main()
