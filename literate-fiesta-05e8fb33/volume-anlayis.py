import requests
import pandas as pd
from datetime import datetime
import time

def get_nse_option_chain(symbol="NIFTY", expiry=None):
    """
    Fetch live NSE option chain.
    symbol: "NIFTY", "BANKNIFTY", "FINNIFTY", or any F&O stock e.g. "RELIANCE", "SBIN"
    expiry: None = nearest expiry, or "DD-Mon-YYYY" e.g. "09-Oct-2025"
    """
    # Correct endpoint
    if symbol.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol.upper()}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol.upper()}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/option-chain",
        "Connection": "keep-alive",
    }

    session = requests.Session()
    # First hit the main page to get cookies
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    time.sleep(0.5)  # be polite

    response = session.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()

    records = data["records"]["data"]
    underlying = data["records"]["underlyingValue"]
    timestamp = data["records"]["timestamp"]
    all_expiries = data["records"]["expiryDates"]

    if expiry is None:
        expiry = all_expiries[0]  # nearest

    print(f"\n{'='*70}")
    print(f"Symbol          : {symbol.upper()}")
    print(f"Underlying      : {underlying}")
    print(f"Expiry          : {expiry}")
    print(f"Server Time     : {timestamp}")
    print(f"Available Exp   : {all_expiries[:5]} ...")
    print(f"{'='*70}\n")

    rows = []
    for rec in records:
        if rec.get("expiryDate") != expiry:
            continue

        strike = rec["strikePrice"]
        ce = rec.get("CE", {})
        pe = rec.get("PE", {})

        rows.append({
            "Strike": strike,
            "CE_OI": ce.get("openInterest", 0),
            "CE_Chg_OI": ce.get("changeinOpenInterest", 0),
            "CE_Volume": ce.get("totalTradedVolume", 0),
            "CE_LTP": ce.get("lastPrice", 0),
            "CE_IV": ce.get("impliedVolatility", 0),
            "PE_OI": pe.get("openInterest", 0),
            "PE_Chg_OI": pe.get("changeinOpenInterest", 0),
            "PE_Volume": pe.get("totalTradedVolume", 0),
            "PE_LTP": pe.get("lastPrice", 0),
            "PE_IV": pe.get("impliedVolatility", 0),
        })

    df = pd.DataFrame(rows).sort_values("Strike").reset_index(drop=True)
    return df, underlying, expiry


def analyse_max_volume(df, top_n=5):
    """Find max volume CE / PE and show top N."""
    if df.empty:
        print("No data returned.")
        return

    # Max volume strikes
    max_ce_idx = df["CE_Volume"].idxmax()
    max_pe_idx = df["PE_Volume"].idxmax()

    print("🔥 MAX VOLUME STRIKES")
    print("-" * 50)
    print(f"CALL  (CE) → Strike: {df.loc[max_ce_idx, 'Strike']:>8}  "
          f"Volume: {df.loc[max_ce_idx, 'CE_Volume']:>10,}  "
          f"OI: {df.loc[max_ce_idx, 'CE_OI']:>10,}  "
          f"Chg OI: {df.loc[max_ce_idx, 'CE_Chg_OI']:>8,}")
    print(f"PUT   (PE) → Strike: {df.loc[max_pe_idx, 'Strike']:>8}  "
          f"Volume: {df.loc[max_pe_idx, 'PE_Volume']:>10,}  "
          f"OI: {df.loc[max_pe_idx, 'PE_OI']:>10,}  "
          f"Chg OI: {df.loc[max_pe_idx, 'PE_Chg_OI']:>8,}")

    print(f"\n📊 TOP {top_n} CALL VOLUME")
    print(df.nlargest(top_n, "CE_Volume")[
        ["Strike", "CE_Volume", "CE_OI", "CE_Chg_OI", "CE_LTP", "CE_IV"]
    ].to_string(index=False))

    print(f"\n📊 TOP {top_n} PUT VOLUME")
    print(df.nlargest(top_n, "PE_Volume")[
        ["Strike", "PE_Volume", "PE_OI", "PE_Chg_OI", "PE_LTP", "PE_IV"]
    ].to_string(index=False))

    # Quick PCR by volume
    total_ce_vol = df["CE_Volume"].sum()
    total_pe_vol = df["PE_Volume"].sum()
    pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0
    print(f"\nPCR (Volume) = {pcr_vol:.2f}  (PE Vol / CE Vol)")
    print(f"Total CE Volume: {total_ce_vol:,}")
    print(f"Total PE Volume: {total_pe_vol:,}")


# ====================== RUN ======================
if __name__ == "__main__":
    # Change these as needed
    SYMBOL = "NIFTY"          # or "BANKNIFTY", "RELIANCE", "SBIN", etc.
    EXPIRY = None             # None = nearest, or "09-Oct-2025"

    try:
        df, spot, expiry = get_nse_option_chain(SYMBOL, EXPIRY)
        analyse_max_volume(df, top_n=5)

        # Optional: save full chain
        # df.to_csv(f"{SYMBOL}_{expiry}_option_chain.csv", index=False)
        # print("\nSaved to CSV")

    except Exception as e:
        print("Error:", e)
        print("Tips: Run during market hours (9:15–15:30 IST).")
        print("If blocked, wait a few seconds and retry, or use Indian IP / disable VPN.")