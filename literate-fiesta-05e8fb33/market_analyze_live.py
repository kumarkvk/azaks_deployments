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
INTERVAL = "2m"
PERIOD = "5d"

# Refresh interval in seconds.
REFRESH_SECONDS = 60

# Number of candles used for support/resistance.
SR_LOOKBACK = 20

# Volume spike threshold: current volume / average volume.
VOLUME_SPIKE_MULTIPLIER = 1.5

# Set to False if you only want one scan.
CONTINUOUS_MODE = True


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

        for col in required:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna()

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
    return 100 - (100 / (1 + rs))


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

    df["VOL_AVG20"] = df["Volume"].rolling(20).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_AVG20"]

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

    BUY points:
      +1 price above EMA20
      +1 EMA20 above EMA50
      +1 price above VWAP
      +1 MACD above signal
      +1 RSI between 50 and 70
      +1 volume spike

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
    reasons = []

    price = float(row["Close"])
    ema20 = float(row["EMA20"])
    ema50 = float(row["EMA50"])
    vwap = float(row["VWAP"])
    rsi = float(row["RSI14"])
    macd = float(row["MACD"])
    macd_signal = float(row["MACD_SIGNAL"])
    vol_ratio = float(row["VOL_RATIO"]) if pd.notna(row["VOL_RATIO"]) else 0

    # Trend
    if price > ema20:
        buy_score += 1
        reasons.append("Price > EMA20")
    else:
        sell_score += 1
        reasons.append("Price < EMA20")

    if ema20 > ema50:
        buy_score += 1
        reasons.append("EMA20 > EMA50")
    else:
        sell_score += 1
        reasons.append("EMA20 < EMA50")

    # VWAP
    if price > vwap:
        buy_score += 1
        reasons.append("Price > VWAP")
    else:
        sell_score += 1
        reasons.append("Price < VWAP")

    # MACD
    if macd > macd_signal:
        buy_score += 1
        reasons.append("MACD bullish")
    else:
        sell_score += 1
        reasons.append("MACD bearish")

    # RSI
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
    if vol_ratio >= VOLUME_SPIKE_MULTIPLIER:
        if buy_score > sell_score:
            buy_score += 1
            reasons.append("Bullish volume spike")
        elif sell_score > buy_score:
            sell_score += 1
            reasons.append("Bearish volume spike")
        else:
            reasons.append("Volume spike")

    if buy_score >= 5 and buy_score >= sell_score + 2:
        signal = "BUY"
    elif sell_score >= 5 and sell_score >= buy_score + 2:
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
    change_pct = ((price - previous) / previous) * 100

    print("\n" + "=" * 78)
    print(f"{name} ({symbol})")
    print("=" * 78)

    print(f"Last candle:   {format_timestamp(df.index[-1])}")
    print(f"Price:         ₹{price:,.2f}")
    print(f"Candle change: {change_pct:+.2f}%")
    print(f"High / Low:    ₹{float(row['High']):,.2f} / ₹{float(row['Low']):,.2f}")
    print(f"Volume:        {int(float(row['Volume'])):,}")

    print("\nIndicators")
    print(f"  EMA20:       ₹{float(row['EMA20']):,.2f}")
    print(f"  EMA50:       ₹{float(row['EMA50']):,.2f}")
    print(f"  SMA200:      ₹{float(row['SMA200']):,.2f}" if pd.notna(row["SMA200"]) else "  SMA200:      N/A")
    print(f"  RSI14:       {float(row['RSI14']):.2f}")
    print(f"  MACD:        {float(row['MACD']):.4f}")
    print(f"  MACD Signal: {float(row['MACD_SIGNAL']):.4f}")
    print(f"  VWAP:        ₹{float(row['VWAP']):,.2f}")
    print(f"  ATR14:       ₹{float(row['ATR14']):,.2f}")
    print(f"  Volume Avg:  {float(row['VOL_RATIO']):.2f}x" if pd.notna(row["VOL_RATIO"]) else "  Volume Avg:  N/A")

    print("\nSupport / Resistance")
    print(f"  Support:     ₹{support:,.2f}")
    print(f"  Resistance:  ₹{resistance:,.2f}")

    print("\nSignal")
    print(f"  {signal['signal']}")
    print(f"  Buy score:   {signal['buy_score']}/6")
    print(f"  Sell score:  {signal['sell_score']}/6")
    print("  Reasons:     " + ", ".join(signal["reasons"]))

    print("=" * 78)

    return {
        "symbol": symbol,
        "name": name,
        "price": price,
        "change_pct": change_pct,
        "rsi": float(row["RSI14"]),
        "vwap": float(row["VWAP"]),
        "signal": signal["signal"],
        "buy_score": signal["buy_score"],
        "sell_score": signal["sell_score"],
        "timestamp": format_timestamp(df.index[-1]),
    }


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
        print(f"{'Symbol':<18} {'Price':>12} {'Change':>10} {'RSI':>8} {'Signal':<18}")
        print("-" * 78)

        for r in results:
            print(
                f"{r['symbol']:<18} "
                f"₹{r['price']:>10,.2f} "
                f"{r['change_pct']:>+9.2f}% "
                f"{r['rsi']:>7.2f} "
                f"{r['signal']:<18}"
            )

        print("=" * 78)

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
