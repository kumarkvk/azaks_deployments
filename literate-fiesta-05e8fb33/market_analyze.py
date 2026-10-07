#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Working Stock Analysis Script
Handles yfinance quirks
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime, timedelta
import sys
import io
import warnings
warnings.filterwarnings('ignore')

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sns.set_style("darkgrid")

def get_stock_data(symbol):
    """Safely download stock data"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        df = yf.download(symbol, start=start_date, end=end_date, progress=False, threads=False)
        
        if df is None or len(df) == 0:
            return None
        
        # Reset index if it's a MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        return df.reset_index()
        
    except Exception as e:
        return None


def calculate_rsi(close_prices, period=14):
    """Calculate RSI"""
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def analyze_symbol(symbol, name):
    """Analyze a stock symbol"""
    
    print(f"\n[*] Downloading {name} ({symbol})...")
    df = get_stock_data(symbol)
    
    if df is None or len(df) < 30:
        print(f"    [!] No sufficient data for {symbol}")
        return None
    
    try:
        # Make sure Close is numeric
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
        df['High'] = pd.to_numeric(df['High'], errors='coerce')
        df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        # Drop NaN rows
        df = df.dropna()
        
        if len(df) < 30:
            print(f"    [!] Not enough data after cleaning for {symbol}")
            return None
        
        # Calculate indicators
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        df['RSI'] = calculate_rsi(df['Close'], 14)
        
        # Get current and previous values
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        curr_price = float(curr['Close'])
        prev_price = float(prev['Close'])
        change_pct = ((curr_price - prev_price) / prev_price) * 100
        
        ma20 = float(curr['MA20'])
        ma50 = float(curr['MA50'])
        rsi = float(curr['RSI'])
        
        # Print analysis
        print(f"\n{'='*70}")
        print(f"{name} ({symbol})")
        print(f"{'='*70}")
        print(f"Price:         ₹{curr_price:>10.2f}")
        print(f"Change:        {change_pct:>10.2f}%")
        print(f"High/Low:      {float(curr['High']):>10.2f} / {float(curr['Low']):>10.2f}")
        print(f"Volume:        {int(float(curr['Volume'])):>10,}")
        
        print(f"\nIndicators:")
        print(f"  RSI(14):     {rsi:>10.2f}", end="")
        if rsi < 30:
            print("  <- OVERSOLD (BUY)")
        elif rsi > 70:
            print("  <- OVERBOUGHT (SELL)")
        else:
            print("  <- NEUTRAL")
        
        print(f"  MA20:        ₹{ma20:>10.2f}", end="")
        if curr_price > ma20:
            print("  <- ABOVE")
        else:
            print("  <- BELOW")
        
        print(f"  MA50:        ₹{ma50:>10.2f}", end="")
        if curr_price > ma50:
            print("  <- UPTREND")
        else:
            print("  <- DOWNTREND")
        
        # Overall signal
        print(f"\nSignal:", end=" ")
        if rsi < 40 and curr_price > ma50:
            print("BUY (Oversold + Uptrend)")
        elif rsi > 60 and curr_price < ma50:
            print("SELL (Overbought + Downtrend)")
        elif curr_price > ma50 and curr_price > ma20:
            print("BULLISH (Strong Uptrend)")
        elif curr_price < ma50 and curr_price < ma20:
            print("BEARISH (Strong Downtrend)")
        else:
            print("NEUTRAL (Mixed Signals)")
        
        print(f"{'='*70}")
        
        return df
        
    except Exception as e:
        print(f"    [!] Error processing {symbol}: {str(e)}")
        return None


def plot_stock(df, symbol):
    """Plot stock analysis"""
    
    try:
        plot_data = df.tail(60).copy()
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        fig.suptitle(f'{symbol} Analysis', fontsize=14, fontweight='bold')
        
        # Price chart
        ax1 = axes[0]
        ax1.plot(range(len(plot_data)), plot_data['Close'], 'k-', linewidth=2, label='Close')
        ax1.plot(range(len(plot_data)), plot_data['MA20'], 'b--', linewidth=1, alpha=0.7, label='MA20')
        ax1.plot(range(len(plot_data)), plot_data['MA50'], 'r--', linewidth=1, alpha=0.7, label='MA50')
        ax1.fill_between(range(len(plot_data)), plot_data['Close'], alpha=0.2)
        ax1.set_title('Price & Moving Averages', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylabel('Price (INR)')
        
        # RSI chart
        ax2 = axes[1]
        ax2.plot(range(len(plot_data)), plot_data['RSI'], 'purple', linewidth=2)
        ax2.axhline(70, color='r', linestyle='--', alpha=0.5)
        ax2.axhline(30, color='g', linestyle='--', alpha=0.5)
        ax2.fill_between(range(len(plot_data)), 30, 70, alpha=0.1, color='gray')
        ax2.set_title('RSI (14)', fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylabel('RSI')
        
        # Volume chart
        ax3 = axes[2]
        colors = ['green' if plot_data['Close'].iloc[i] >= plot_data['Close'].iloc[i-1] else 'red' 
                  for i in range(1, len(plot_data))]
        ax3.bar(range(1, len(plot_data)), plot_data['Volume'].iloc[1:], color=colors, alpha=0.6)
        ax3.set_title('Volume', fontweight='bold')
        ax3.set_ylabel('Volume')
        ax3.set_xlabel('Days (Last 60)')
        ax3.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        fname = f"{symbol.replace('^', '').replace('.NS', '')}_chart.png"
        plt.savefig(fname, dpi=120, bbox_inches='tight')
        print(f"[+] Saved: {fname}\n")
        plt.close()
        
    except Exception as e:
        print(f"[!] Could not create chart: {str(e)}\n")


def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("INDIAN MARKET STOCK ANALYZER")
    print("="*70)
    
    # Symbols to analyze (Yahoo Finance format)
    symbols = [
        ('^NSEI', 'Nifty 50'),
        ('RELIANCE.BO', 'Reliance Industries'),
        ('TCS.BO', 'Tata Consultancy Services'),
    ]
    
    results = {}
    
    for symbol, name in symbols:
        df = analyze_symbol(symbol, name)
        if df is not None:
            results[symbol] = df
            plot_stock(df, symbol)
    
    # Summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    if results:
        for symbol, df in results.items():
            curr_price = float(df.iloc[-1]['Close'])
            prev_price = float(df.iloc[-2]['Close'])
            change = ((curr_price - prev_price) / prev_price) * 100
            print(f"{symbol:20} | Price: ₹{curr_price:10.2f} | Change: {change:+7.2f}%")
    
    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
