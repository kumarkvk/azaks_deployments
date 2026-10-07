#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start Stock Analysis Script
Simpler version for immediate use
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime
import sys
import io

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sns.set_style("darkgrid")

def quick_analyze(symbol, days=180):
    """
    Quick analysis of any stock/index
    
    Args:
        symbol: Stock ticker (e.g., '^NSEI', 'HDFC.NS')
        days: Number of days to analyze
    """
    print(f"\n📊 Analyzing {symbol}...")
    
    # Download data
    data = yf.download(symbol, period=f"{days}d", progress=False)
    
    if data.empty:
        print(f"❌ No data found for {symbol}")
        return
    
    # Calculate indicators
    data['MA20'] = data['Close'].rolling(20).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    data['RSI'] = calculate_rsi(data['Close'], 14)
    
    # Get latest values - handle both Series and DataFrame
    if isinstance(data, pd.DataFrame):
        latest = data.iloc[-1]
    else:
        latest = data[-1]
    
    prev_close = float(data['Close'].iloc[-2])
    
    # Display info
    print(f"\n{'='*60}")
    print(f"Stock: {symbol}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Current Price:  ₹{float(latest['Close']):.2f}")
    print(f"Change:         {((float(latest['Close']) - prev_close) / prev_close * 100):+.2f}%")
    print(f"Day High/Low:   ₹{float(latest['High']):.2f} / ₹{float(latest['Low']):.2f}")
    print(f"Volume:         {int(float(latest['Volume'])):,}")
    
    print(f"\n{'─'*60}")
    print("📈 TECHNICAL INDICATORS")
    print(f"{'─'*60}")
    
    rsi_val = float(latest['RSI']) if pd.notna(latest['RSI']) else 50
    print(f"RSI (14):       {rsi_val:.2f}", end="")
    if rsi_val < 30:
        print(" 🟢 OVERSOLD - BUY SIGNAL")
    elif rsi_val > 70:
        print(" 🔴 OVERBOUGHT - SELL SIGNAL")
    else:
        print(" 🟡 NEUTRAL")
    
    ma20_val = float(latest['MA20']) if pd.notna(latest['MA20']) else float(latest['Close'])
    print(f"MA 20:          ₹{ma20_val:.2f}", end="")
    if float(latest['Close']) > ma20_val:
        print(" (✅ Price above)")
    else:
        print(" (❌ Price below)")
    
    ma50_val = float(latest['MA50']) if pd.notna(latest['MA50']) else float(latest['Close'])
    print(f"MA 50:          ₹{ma50_val:.2f}", end="")
    if float(latest['Close']) > ma50_val:
        print(" (✅ Uptrend)")
    else:
        print(" (❌ Downtrend)")
    
    # Overall signal
    print(f"\n{'─'*60}")
    print("🎯 OVERALL SIGNAL")
    print(f"{'─'*60}")
    
    if rsi_val < 40 and float(latest['Close']) > ma50_val:
        print("🟢 BUY - Oversold with uptrend")
    elif rsi_val > 60 and float(latest['Close']) < ma50_val:
        print("🔴 SELL - Overbought with downtrend")
    elif float(latest['Close']) > ma50_val and float(latest['Close']) > ma20_val:
        print("🟢 BULLISH - Strong uptrend")
    elif float(latest['Close']) < ma50_val and float(latest['Close']) < ma20_val:
        print("🔴 BEARISH - Strong downtrend")
    else:
        print("🟡 MIXED SIGNALS - Wait for confirmation")
    
    print(f"{'='*60}\n")
    
    # Plot
    plot_simple(data, symbol)
    
    return data


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def plot_simple(data, symbol):
    """Create simple visualization"""
    
    # Use last 60 days for cleaner chart
    data = data.tail(60)
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Chart 1: Price and MAs
    ax1 = axes[0]
    ax1.plot(data.index, data['Close'], label='Close', linewidth=2, color='black')
    ax1.plot(data.index, data['MA20'], label='MA 20', alpha=0.7)
    ax1.plot(data.index, data['MA50'], label='MA 50', alpha=0.7)
    ax1.fill_between(data.index, data['Close'], alpha=0.3)
    ax1.set_title(f'{symbol} - Price & Moving Averages', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel('Price (₹)')
    
    # Chart 2: RSI
    ax2 = axes[1]
    ax2.plot(data.index, data['RSI'], label='RSI (14)', linewidth=2, color='purple')
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
    ax2.fill_between(data.index, 30, 70, alpha=0.1, color='gray')
    ax2.set_title('RSI - Momentum', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylabel('RSI Value')
    
    # Chart 3: Volume
    ax3 = axes[2]
    colors = ['green' if data['Close'].iloc[i] >= data['Close'].iloc[i-1] else 'red' 
              for i in range(1, len(data))]
    ax3.bar(range(1, len(data)), data['Volume'].iloc[1:], color=colors, alpha=0.6)
    ax3.set_title('Trading Volume', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylabel('Volume')
    ax3.set_xlabel('Days')
    
    plt.tight_layout()
    
    # Save
    filename = f'{symbol.replace("^", "").replace(".NS", "")}_analysis.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✅ Chart saved as '{filename}'")
    
    plt.show()


def analyze_multiple(symbols):
    """Compare multiple stocks/indices"""
    
    print("\n" + "="*70)
    print("COMPARING MULTIPLE SYMBOLS")
    print("="*70)
    
    comparison_data = {}
    
    for symbol in symbols:
        try:
            data = yf.download(symbol, period='6mo', progress=False)
            if not data.empty:
                returns = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / 
                          data['Close'].iloc[0] * 100)
                comparison_data[symbol] = {
                    'Current': data['Close'].iloc[-1],
                    '6M Return %': returns,
                    'High': data['Close'].max(),
                    'Low': data['Close'].min(),
                }
        except:
            pass
    
    # Display comparison
    df_comparison = pd.DataFrame(comparison_data).T
    print("\n" + df_comparison.to_string())
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    
    print("\n" + "="*70)
    print("🚀 QUICK STOCK ANALYZER")
    print("="*70)
    
    # Analyze Nifty 50
    nifty_data = quick_analyze('^NSEI')
    
    # Analyze Bank Nifty
    banknifty_data = quick_analyze('^NSEBANK')
    
    # Analyze HDFC
    hdfc_data = quick_analyze('HDFC.NS')
    
    # Compare all
    print("\n" + "="*70)
    print("📊 QUICK COMPARISON TABLE")
    print("="*70)
    analyze_multiple(['^NSEI', '^NSEBANK', 'HDFC.NS', 'RELIANCE.NS', 'TCS.NS'])
    
    print("\n💡 TIP: Modify the script to analyze any symbol you want!")
    print("Example: quick_analyze('INFY.NS') for Infosys")
