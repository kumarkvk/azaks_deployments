#!/usr/bin/env python3
"""
NSE Options Volume / Flow Analyzer
----------------------------------
Reads the live NSE option chain and shows where options are trading most
heavily and whether that activity looks buyer-led or seller-led.

Per strike it reports:
  * Traded volume (max-volume strikes for CE and PE)
  * Open interest (OI), change in OI, and the resulting buildup type
  * Pending order-book buy vs sell quantity (book pressure)
  * Since-last-scan volume flow, classified with a tick rule

Important:
  NSE does not publish the aggressor side of trades. Every traded contract
  has both a buyer and a seller, so "buy volume" vs "sell volume" is inferred
  from price/OI changes and the pending order book. Treat it as an estimate.

  The NSE endpoints used are the unofficial JSON APIs behind nseindia.com.
  They may change, rate-limit, or block automated access. Personal use only.
  This is analysis for learning, not financial advice.

Usage:
  python nse_options_flow.py                      # NIFTY, nearest expiry, live
  python nse_options_flow.py --symbol BANKNIFTY
  python nse_options_flow.py --symbol RELIANCE    # stock options
  python nse_options_flow.py --once --csv flow.csv
"""

import argparse
import io
import sys
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IST = ZoneInfo("Asia/Kolkata")
INDEX_SYMBOLS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"}
BASE = "https://www.nseindia.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
MIN_INTERVAL = 30  # Seconds. Polling NSE faster risks getting blocked.


# ---------------------------------------------------------------------------
# NSE CLIENT
# ---------------------------------------------------------------------------

class NSEClient:
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.session = None

    def _new_session(self):
        s = requests.Session()
        s.headers.update({
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"{BASE}/option-chain",
        })
        # NSE requires the cookies set by its website before API calls.
        s.get(f"{BASE}/option-chain", timeout=self.timeout)
        self.session = s

    def get_json(self, path):
        last_error = None
        for attempt in range(3):
            try:
                if self.session is None or attempt > 0:
                    self._new_session()
                r = self.session.get(BASE + path, timeout=self.timeout)
                if r.status_code == 200:
                    return r.json()
                last_error = f"HTTP {r.status_code}"
            except (requests.RequestException, ValueError) as exc:
                last_error = str(exc)
            time.sleep(1 + attempt)
        raise RuntimeError(f"NSE request failed for {path}: {last_error}")

    def expiries(self, symbol):
        data = self.get_json(f"/api/option-chain-contract-info?symbol={symbol}")
        return data.get("expiryDates", [])

    def option_chain(self, symbol, expiry):
        kind = "Indices" if symbol in INDEX_SYMBOLS else "Equity"
        return self.get_json(
            f"/api/option-chain-v3?type={kind}&symbol={symbol}&expiry={expiry}"
        )


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def is_market_open(now=None):
    now = now or datetime.now(IST)
    return now.weekday() < 5 and dt_time(9, 15) <= now.time() <= dt_time(15, 30)


def pick_expiry(expiries, requested=None):
    if requested:
        for e in expiries:
            if e.lower() == requested.lower():
                return e
        raise SystemExit(f"Expiry {requested!r} not found. Available: {', '.join(expiries[:8])}")

    now = datetime.now(IST)
    for e in expiries:
        try:
            d = datetime.strptime(e, "%d-%b-%Y").date()
        except ValueError:
            continue
        if d > now.date() or (d == now.date() and now.time() < dt_time(15, 30)):
            return e
    raise SystemExit("No tradable expiry found.")


def num(v):
    try:
        x = float(v)
        return x if np.isfinite(x) else 0.0
    except (TypeError, ValueError):
        return 0.0


def human(n):
    n = float(n)
    for unit, div in (("Cr", 1e7), ("L", 1e5), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n / div:.2f}{unit}"
    return f"{n:.0f}"


# ---------------------------------------------------------------------------
# PARSING + CLASSIFICATION
# ---------------------------------------------------------------------------

BUILDUP = {
    (1, 1): "Long buildup",      # price up, OI up    -> fresh buying
    (-1, 1): "Short buildup",    # price down, OI up  -> fresh writing/selling
    (1, -1): "Short covering",   # price up, OI down  -> sellers exiting
    (-1, -1): "Long unwinding",  # price down, OI down -> buyers exiting
}


def classify_buildup(price_chg, oi_chg):
    if price_chg == 0 or oi_chg == 0:
        return "Neutral"
    return BUILDUP[(int(np.sign(price_chg)), int(np.sign(oi_chg)))]


def parse_chain(raw):
    records = raw.get("records", {})
    rows = []
    for item in records.get("data", []):
        for side in ("CE", "PE"):
            d = item.get(side)
            if not d:
                continue
            rows.append({
                "strike": num(d.get("strikePrice") or item.get("strikePrice")),
                "side": side,
                "ltp": num(d.get("lastPrice")),
                "chg": num(d.get("change")),
                "pchg": num(d.get("pChange")),
                "volume": num(d.get("totalTradedVolume")),
                "oi": num(d.get("openInterest")),
                "chg_oi": num(d.get("changeinOpenInterest")),
                "iv": num(d.get("impliedVolatility")),
                "bid_qty": num(d.get("totalBuyQuantity")),
                "ask_qty": num(d.get("totalSellQuantity")),
                "bid": num(d.get("buyPrice1")),
                "ask": num(d.get("sellPrice1")),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Option chain returned no rows.")

    book = df["bid_qty"] + df["ask_qty"]
    df["book_imb"] = np.where(book > 0, (df["bid_qty"] - df["ask_qty"]) / book, 0.0)
    df["buildup"] = [classify_buildup(p, o) for p, o in zip(df["chg"], df["chg_oi"])]
    df["turnover"] = df["volume"] * df["ltp"]

    spot = num(records.get("underlyingValue"))
    return df, spot, records.get("timestamp")


def book_label(imb):
    if imb >= 0.2:
        return "Bid-heavy"
    if imb <= -0.2:
        return "Ask-heavy"
    return "Balanced"


def interval_flow(curr, prev):
    """
    Volume traded between two scans, classified with a tick rule:
    LTP up on new volume -> buyer-led; LTP down -> seller-led.
    """
    if prev is None:
        return None
    m = curr.merge(
        prev[["strike", "side", "volume", "ltp", "oi"]],
        on=["strike", "side"], suffixes=("", "_prev"),
    )
    m["d_vol"] = (m["volume"] - m["volume_prev"]).clip(lower=0)
    m["d_ltp"] = m["ltp"] - m["ltp_prev"]
    m["d_oi"] = m["oi"] - m["oi_prev"]
    m["flow"] = np.select(
        [m["d_vol"] <= 0, m["d_ltp"] > 0, m["d_ltp"] < 0],
        ["-", "Buyer-led", "Seller-led"],
        default="Two-sided",
    )
    return m[m["d_vol"] > 0]


# ---------------------------------------------------------------------------
# SENTIMENT
# ---------------------------------------------------------------------------

# How each buildup on each side tilts the underlying (+ bullish / - bearish).
SENTIMENT = {
    ("CE", "Long buildup"): 1.0,
    ("CE", "Short covering"): 0.7,
    ("CE", "Short buildup"): -1.0,
    ("CE", "Long unwinding"): -0.5,
    ("PE", "Long buildup"): -1.0,
    ("PE", "Short covering"): -0.7,
    ("PE", "Short buildup"): 1.0,
    ("PE", "Long unwinding"): 0.5,
}


def sentiment_score(df):
    w = df["chg_oi"].abs() + df["volume"] * 0.1
    s = np.array([SENTIMENT.get((sd, b), 0.0) for sd, b in zip(df["side"], df["buildup"])])
    total = w.sum()
    return float((s * w).sum() / total) if total > 0 else 0.0


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def print_table(df, cols, headers, fmt):
    out = df[cols].copy()
    for c, f in fmt.items():
        out[c] = out[c].map(f)
    out.columns = headers
    print(out.to_string(index=False))


def report(symbol, expiry, df_all, spot, nse_ts, prev, window, top):
    now = datetime.now(IST)
    strikes = np.sort(df_all["strike"].unique())
    step = float(pd.Series(strikes).diff().dropna().mode().iloc[0])
    atm = float(strikes[np.abs(strikes - spot).argmin()])
    df = df_all[(df_all["strike"] >= atm - window * step)
                & (df_all["strike"] <= atm + window * step)].copy()

    ce, pe = df[df["side"] == "CE"], df[df["side"] == "PE"]
    ce_vol, pe_vol = ce["volume"].sum(), pe["volume"].sum()
    ce_oi, pe_oi = ce["oi"].sum(), pe["oi"].sum()

    print("\n" + "#" * 92)
    print(f"NSE OPTIONS FLOW  |  {symbol}  |  Expiry {expiry}  |  Scan {now:%Y-%m-%d %H:%M:%S} IST")
    print(f"Spot {spot:,.2f}  |  ATM {atm:,.0f}  |  Step {step:,.0f}  |  "
          f"Window ATM ±{window} strikes  |  NSE time {nse_ts}")
    if not is_market_open(now):
        print("[!] Market closed - figures are from the last session.")
    print("#" * 92)

    def top_row(frame, col):
        r = frame.loc[frame[col].idxmax()]
        return f"{r['strike']:,.0f} ({human(r[col])})"

    # Resistance must be at/above spot and support at/below spot.
    ce_above = ce[ce["strike"] >= spot]
    pe_below = pe[pe["strike"] <= spot]
    ce_res = ce_above if not ce_above.empty else ce
    pe_sup = pe_below if not pe_below.empty else pe
    resistance = ce_res.loc[ce_res["oi"].idxmax(), "strike"]
    support = pe_sup.loc[pe_sup["oi"].idxmax(), "strike"]

    print("\nKEY LEVELS")
    print(f"  Max volume CE : {top_row(ce, 'volume'):<22} Max volume PE : {top_row(pe, 'volume')}")
    print(f"  Max OI CE at/above spot : {top_row(ce_res, 'oi'):<20} -> resistance")
    print(f"  Max OI PE at/below spot : {top_row(pe_sup, 'oi'):<20} -> support")
    print(f"  Max CE OI addition : {top_row(ce, 'chg_oi')}")
    print(f"  Max PE OI addition : {top_row(pe, 'chg_oi')}")

    ce_chg, pe_chg = ce["chg_oi"].sum(), pe["chg_oi"].sum()
    meaningful_ce_chg = ce_chg > max(1.0, 0.01 * ce_oi)
    chg_pcr = f"{pe_chg / ce_chg:.2f}" if meaningful_ce_chg and pe_chg >= 0 else "N/A"
    print("\nRATIOS (put / call)")
    print(f"  Volume PCR {pe_vol / ce_vol if ce_vol else 0:.2f}   |   "
          f"OI PCR {pe_oi / ce_oi if ce_oi else 0:.2f}   |   "
          f"Chg-OI PCR {chg_pcr}  (CE chg OI {human(ce_chg)}, PE chg OI {human(pe_chg)})")
    print(f"  CE volume {human(ce_vol)}  vs  PE volume {human(pe_vol)}   |   "
          f"Premium flow (vol×LTP) CE {human(ce['turnover'].sum())}  vs  PE {human(pe['turnover'].sum())}")

    cols = ["strike", "ltp", "pchg", "volume", "oi", "chg_oi", "iv", "book_imb", "buildup"]
    headers = ["Strike", "LTP", "Chg%", "Volume", "OI", "ChgOI", "IV", "Book", "Buildup"]
    fmt = {
        "strike": lambda v: f"{v:,.0f}", "ltp": lambda v: f"{v:,.2f}",
        "pchg": lambda v: f"{v:+.1f}%", "volume": human, "oi": human,
        "chg_oi": lambda v: ("+" if v > 0 else "") + human(v),
        "iv": lambda v: f"{v:.1f}",
        "book_imb": lambda v: f"{book_label(v)} {v:+.2f}",
    }
    for side, frame in (("CALLS (CE)", ce), ("PUTS (PE)", pe)):
        print(f"\nTOP {top} {side} BY VOLUME")
        print_table(frame.nlargest(top, "volume"), cols, headers, fmt)

    flow = interval_flow(df, prev)
    if flow is not None:
        print(f"\nLIVE FLOW SINCE LAST SCAN (tick-rule estimate)")
        if flow.empty:
            print("  No new trades in window.")
        else:
            buy = flow.loc[flow["flow"] == "Buyer-led"]
            sell = flow.loc[flow["flow"] == "Seller-led"]
            for side in ("CE", "PE"):
                b = buy.loc[buy["side"] == side, "d_vol"].sum()
                s = sell.loc[sell["side"] == side, "d_vol"].sum()
                print(f"  {side}: buyer-led {human(b):>8}  |  seller-led {human(s):>8}")
            f = flow.nlargest(top, "d_vol").copy()
            f["leg"] = f["strike"].map(lambda v: f"{v:,.0f}") + " " + f["side"]
            print_table(
                f, ["leg", "d_vol", "d_ltp", "d_oi", "flow"],
                ["Strike", "New vol", "LTP chg", "OI chg", "Flow"],
                {"d_vol": human, "d_ltp": lambda v: f"{v:+.2f}",
                 "d_oi": lambda v: ("+" if v > 0 else "") + human(v)},
            )

    score = sentiment_score(df)
    bias = "BULLISH" if score >= 0.2 else "BEARISH" if score <= -0.2 else "NEUTRAL / RANGE"
    print("\nINTERPRETATION")
    print(f"  OI/price buildup score {score:+.2f}  ->  {bias}")
    print(f"  OI range: {support:,.0f} (put-OI support) to {resistance:,.0f} (call-OI resistance)")
    print("  Note: buy/sell split is inferred - NSE doesn't publish trade aggressor side.")
    print("=" * 92)

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="NSE options max-volume buy/sell analyzer")
    ap.add_argument("--symbol", default="NIFTY", help="NIFTY, BANKNIFTY, FINNIFTY, RELIANCE, ...")
    ap.add_argument("--expiry", help="e.g. 13-Oct-2026 (default: nearest)")
    ap.add_argument("--window", type=int, default=10, help="Strikes each side of ATM (default 10)")
    ap.add_argument("--top", type=int, default=5, help="Rows in top tables (default 5)")
    ap.add_argument("--interval", type=int, default=60, help=f"Refresh seconds (min {MIN_INTERVAL})")
    ap.add_argument("--once", action="store_true", help="Run a single scan")
    ap.add_argument("--csv", help="Append each scan's per-strike data to this CSV")
    args = ap.parse_args()

    symbol = args.symbol.upper()
    interval = max(args.interval, MIN_INTERVAL)
    client = NSEClient()
    expiry = pick_expiry(client.expiries(symbol), args.expiry)
    prev = None

    try:
        while True:
            try:
                df, spot, ts = parse_chain(client.option_chain(symbol, expiry))
                prev = report(symbol, expiry, df, spot, ts, prev, args.window, args.top)
                if args.csv:
                    out = df.assign(scan_time=datetime.now(IST).isoformat(), spot=spot,
                                    symbol=symbol, expiry=expiry)
                    out.to_csv(args.csv, mode="a", index=False,
                               header=not pd.io.common.file_exists(args.csv))
            except Exception as exc:
                print(f"[!] Scan failed: {exc}")

            if args.once:
                break
            print(f"Next scan in {interval}s (Ctrl+C to stop)...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
