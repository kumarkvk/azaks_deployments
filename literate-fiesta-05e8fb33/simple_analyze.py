#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Stock Analysis Script
Works reliably with Indian market indices
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime
import sys
import io
import warnings
warnings.filterwarnings('ignore')

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sns.set_style("darkgrid")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def analyze_stock(symbol, days=180):
    """Analyze a stock/index"""
    
    try:
        print(f"\n[*] Downloading data for {symbol}...")
        data = yf.download(symbol, period=f"{days}d", progress=False, threads=False)
        
        if data.empty:
            print(f"    ERROR: No data found for {symbol}")
            return None
        
        # Ensure we have a proper dataframe
        if isinstance(data, pd.Series):
            print(f"    ERROR: Single row data, need more days")
            return None
        
        # Calculate indicators
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        data['RSI'] = calculate_rsi(data['Close'], 14)
        
        # Get the last two valid rows
        last_idx = len(data) - 1
        current = data.iloc[last_idx]
        previous = data.iloc[last_idx - 1]
        
        # Extract values safely
        curr_price = float(current['Close'])
        prev_price = float(previous['Close'])
        curr_high = float(current['High'])
        curr_low = float(current['Low'])
        curr_volume = int(float(current['Volume']))
        
        curr_ma20 = float(current['MA20']) if pd.notna(current['MA20']) else curr_price
        curr_ma50 = float(current['MA50']) if pd.notna(current['MA50']) else curr_price
        curr_rsi = float(current['RSI']) if pd.notna(current['RSI']) else 50
        
        # Calculate change
        price_change = curr_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        # Generate signals
        if curr_rsi < 30:
            rsi_signal = "OVERSOLD (BUY)"
        elif curr_rsi > 70:
            rsi_signal = "OVERBOUGHT (SELL)"
        else:
            rsi_signal = "NEUTRAL"
        
        if curr_price > curr_ma20:
            ma20_signal = "ABOVE"
        else:
            ma20_signal = "BELOW"
        
        if curr_price > curr_ma50:
            ma50_signal = "UPTREND"
        else:
            ma50_signal = "DOWNTREND"
        
        # Print report
        print("\n" + "="*70)
        print(f"ANALYSIS: {symbol}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        print(f"\nPRICE DATA:")
        print(f"  Current:   ₹{curr_price:>12.2f}")
        print(f"  Change:    {price_change_pct:>12.2f}% ({price_change:+.2f})")
        print(f"  High/Low:  {curr_high:>12.2f} / {curr_low:.2f}")
        print(f"  Volume:    {curr_volume:>12,}")
        
        print(f"\nTECHNICAL:")
        print(f"  RSI:       {curr_rsi:>12.2f}  [{rsi_signal}]")
        print(f"  MA20:      ₹{curr_ma20:>12.2f}  [PRICE {ma20_signal}]")
        print(f"  MA50:      ₹{curr_ma50:>12.2f}  [{ma50_signal}]")
        
        print(f"\nSIGNAL:")
        if curr_rsi < 40 and curr_price > curr_ma50:
            print("  >>> BUY - Oversold in uptrend")
        elif curr_rsi > 60 and curr_price < curr_ma50:
            print("  >>> SELL - Overbought in downtrend")
        elif curr_price > curr_ma50 and curr_price > curr_ma20:
            print("  >>> BULLISH - Strong uptrend")
        elif curr_price < curr_ma50 and curr_price < curr_ma20:
            print("  >>> BEARISH - Strong downtrend")
        else:
            print("  >>> NEUTRAL - Wait for confirmation")
        
        print("="*70)
        
        return data
        
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        return None


def create_charts(data, symbol):
    """Create analysis charts"""
    
    try:
        # Use last 60 days for clean chart
        chart_data = data.tail(60).copy()
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        fig.suptitle(f'{symbol} - Stock Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Price & MA
        ax1 = axes[0]
        ax1.plot(chart_data.index, chart_data['Close'], label='Price', linewidth=2, color='black')
        ax1.plot(chart_data.index, chart_data['MA20'], label='MA20', linewidth=1.5, alpha=0.7)
        ax1.plot(chart_data.index, chart_data['MA50'], label='MA50', linewidth=1.5, alpha=0.7)
        ax1.fill_between(chart_data.index, chart_data['Close'], alpha=0.2)
        ax1.set_title('Price & Moving Averages', fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylabel('Price (INR)')
        
        # Chart 2: RSI
        ax2 = axes[1]
        ax2.plot(chart_data.index, chart_data['RSI'], linewidth=2, color='purple')
        ax2.axhline(70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax2.axhline(30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax2.fill_between(chart_data.index, 30, 70, alpha=0.1, color='gray')
        ax2.set_title('RSI (14) - Momentum Indicator', fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylabel('RSI Value')
        
        # Chart 3: Volume
        ax3 = axes[2]
        colors_vol = ['green' if chart_data['Close'].iloc[i] >= chart_data['Close'].iloc[i-1] else 'red' 
                      for i in range(1, len(chart_data))]
        ax3.bar(range(1, len(chart_data)), chart_data['Volume'].iloc[1:], color=colors_vol, alpha=0.6)
        ax3.set_title('Trading Volume', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.set_ylabel('Volume')
        ax3.set_xlabel('Days')
        
        plt.tight_layout()
        
        # Save chart
        chart_name = f'{symbol.replace("^", "").replace(".NS", "")}_analysis.png'
        plt.savefig(chart_name, dpi=150, bbox_inches='tight')
        print(f"\n[+] Chart saved: {chart_name}")
        plt.show()
        
    except Exception as e:
        print(f"\n[!] Could not create charts: {str(e)}")


def main():
    """Main analysis function"""
    
    print("\n" + "="*70)
    print("INDIAN STOCK MARKET ANALYZER")
    print("="*70)
    
    # Stocks to analyze
    stocks = [
        ('^NSEI', 'Nifty 50'),
        ('^NSEBANK', 'Bank Nifty'),
        ('HDFC.NS', 'HDFC Bank'),
    ]
    
    results = {}
    
    # Analyze each stock
    for symbol, name in stocks:
        print(f"\n\n>>> Analyzing {name} ({symbol})...")
        data = analyze_stock(symbol, days=180)
        if data is not None:
            results[symbol] = data
            try:
                create_charts(data, symbol)
            except Exception as e:
                print(f"[!] Skipping charts for {symbol}: {str(e)}")
    
    # Summary comparison
    print("\n\n" + "="*70)
    print("SUMMARY COMPARISON")
    print("="*70)
    
    summary_data = []
    for symbol, name in stocks:
        if symbol in results:
            data = results[symbol]
            curr_price = float(data.iloc[-1]['Close'])
            prev_price = float(data.iloc[-2]['Close'])
            pct_change = ((curr_price - prev_price) / prev_price) * 100
            
            summary_data.append({
                'Symbol': symbol,
                'Name': name,
                'Price': f"₹{curr_price:.2f}",
                'Change %': f"{pct_change:+.2f}%",
                'RSI': f"{float(data.iloc[-1]['RSI']):.2f}" if pd.notna(data.iloc[-1]['RSI']) else 'N/A'
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        print("\n" + summary_df.to_string(index=False))
    
    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
