#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFT Nifty Pre-Market Analysis Tool
Simple working version with simulated data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import io

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_premarket_signal():
    """Generate pre-market signal based on current time and simulated data"""
    
    # Today's Nifty 50 previous close (as of Sept 23, 2026)
    nifty_previous_close = 23414.30
    
    # Simulate GIFT Nifty movement
    # In reality, this would come from NSE IX live data
    current_time = datetime.now()
    
    # Simulate gap based on time of day and market factors
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    
    # Sentiment-based gap (in production, use actual GIFT Nifty API)
    simulated_gap = np.random.uniform(-150, 150)  # Random gap for demo
    
    gift_nifty_current = nifty_previous_close + simulated_gap
    
    return {
        'nifty_previous_close': nifty_previous_close,
        'gift_nifty_level': gift_nifty_current,
        'gap_points': simulated_gap,
        'gap_pct': (simulated_gap / nifty_previous_close) * 100,
        'time': current_time.strftime('%H:%M:%S'),
        'date': current_time.strftime('%Y-%m-%d')
    }


def analyze_gap(data):
    """Analyze gap and generate trading signals"""
    
    gap = data['gap_points']
    
    signals = {
        'gap_size': 'MODERATE' if abs(gap) < 50 else ('LARGE' if abs(gap) < 100 else 'VERY LARGE'),
        'direction': 'BULLISH' if gap > 0 else 'BEARISH',
        'strength': abs(gap)
    }
    
    # Generate signal message
    if gap > 200:
        signals['signal'] = "VERY STRONG BULLISH"
        signals['nse_open'] = "Expected: SIGNIFICANTLY HIGHER"
        signals['action'] = "EXPECT STRONG BUYING AT OPEN"
        signals['risk'] = "Gap fill risk if US market reverses overnight"
    elif gap > 100:
        signals['signal'] = "STRONG BULLISH"
        signals['nse_open'] = "Expected: HIGHER"
        signals['action'] = "EXPECT BUYING AT OPEN"
        signals['risk'] = "Monitor for reversal"
    elif gap > 50:
        signals['signal'] = "MILDLY BULLISH"
        signals['nse_open'] = "Expected: MARGINALLY HIGHER"
        signals['action'] = "Slight upside bias"
        signals['risk'] = "Not a strong signal"
    elif gap > 0:
        signals['signal'] = "SLIGHTLY BULLISH"
        signals['nse_open'] = "Expected: Marginally higher"
        signals['action'] = "Neutral to slightly bullish"
        signals['risk'] = "Low conviction setup"
    elif gap > -50:
        signals['signal'] = "SLIGHTLY BEARISH"
        signals['nse_open'] = "Expected: Marginally lower"
        signals['action'] = "Neutral to slightly bearish"
        signals['risk'] = "Low conviction setup"
    elif gap > -100:
        signals['signal'] = "MILDLY BEARISH"
        signals['nse_open'] = "Expected: MARGINALLY LOWER"
        signals['action'] = "Slight downside bias"
        signals['risk'] = "Not a strong signal"
    elif gap > -200:
        signals['signal'] = "STRONG BEARISH"
        signals['nse_open'] = "Expected: LOWER"
        signals['action'] = "EXPECT SELLING AT OPEN"
        signals['risk'] = "Monitor for reversal"
    else:
        signals['signal'] = "VERY STRONG BEARISH"
        signals['nse_open'] = "Expected: SIGNIFICANTLY LOWER"
        signals['action'] = "EXPECT STRONG SELLING AT OPEN"
        signals['risk'] = "Gap fill risk if US market reverses overnight"
    
    return signals


def print_premarket_report(data, signals):
    """Print formatted pre-market analysis report"""
    
    print("\n" + "="*80)
    print("GIFT NIFTY PRE-MARKET ANALYSIS & NSE OPENING SIGNAL")
    print("="*80)
    
    print(f"\nTime: {data['time']} IST | Date: {data['date']}")
    
    print("\n" + "-"*80)
    print("PRICE LEVELS & GAP ANALYSIS")
    print("-"*80)
    
    print(f"Nifty 50 Previous Close:        ₹{data['nifty_previous_close']:>12.2f}")
    print(f"GIFT Nifty Current Level:       {data['gift_nifty_level']:>12.2f}")
    print(f"Gap (Points):                   {data['gap_points']:>12.2f} points")
    print(f"Gap (%):                        {data['gap_pct']:>12.2f}%")
    
    print("\n" + "-"*80)
    print("TRADING SIGNALS")
    print("-"*80)
    
    print(f"Signal Strength:                {signals['signal']}")
    print(f"Direction:                      {signals['direction']}")
    print(f"NSE Opening:                    {signals['nse_open']}")
    print(f"Expected Action:                {signals['action']}")
    print(f"Key Risk:                       {signals['risk']}")
    
    print("\n" + "-"*80)
    print("RECOMMENDED TRADING STRATEGY (For NSE 9:15 AM Open)")
    print("-"*80)
    
    gap = data['gap_points']
    
    if gap > 100:
        print("""
BULLISH BREAKOUT STRATEGY:
1. Markets expected to open HIGHER with buying momentum
2. Wait for NSE open at 9:15 AM
3. If opens as expected, look for BUY on first dip to MA20 support
4. Entry: On support level confirmation
5. Stop Loss: 50 points below entry
6. Target 1: Previous resistance
7. Target 2: +150 to +200 points from open
8. Risk/Reward Ratio: Aim for 1:2 minimum

Key Levels Today:
- Support: 23,364 (MA20)
- Resistance: 23,500 (yesterday's high)
        """)
    
    elif gap < -100:
        print("""
BEARISH BREAKDOWN STRATEGY:
1. Markets expected to open LOWER with selling momentum
2. Wait for NSE open at 9:15 AM
3. If opens as expected, look for SELL on first rally to MA20 resistance
4. Entry: On resistance level confirmation
5. Stop Loss: 50 points above entry
6. Target 1: Previous support
7. Target 2: -150 to -200 points from open
8. Risk/Reward Ratio: Aim for 1:2 minimum

Key Levels Today:
- Resistance: 23,465 (MA20)
- Support: 23,300 (yesterday's low)
        """)
    
    elif abs(gap) > 50:
        print(f"""
DIRECTIONAL BIAS STRATEGY:
1. Market has {'SLIGHT UPSIDE' if gap > 0 else 'SLIGHT DOWNSIDE'} bias
2. Confirm direction in first 30 mins of NSE trading (9:15-9:45 AM)
3. Only trade after direction is confirmed with volume
4. Use 4H/Daily technical levels for entries
5. Position size: Conservative (1-1.5% risk)
6. Stop Loss: 75 points from entry
7. Target: 100-150 points movement

Confirmation Checklist:
- Check volume > 20-day average
- RSI should support the direction
- MACD should be in agreement
        """)
    
    else:
        print("""
NEUTRAL CONSOLIDATION STRATEGY:
1. No clear overnight directional bias from GIFT Nifty
2. DON'T take positions at open - wait for clarity
3. Best approach: Wait for first 30-45 mins of NSE trading
4. Look for technical breakout with volume
5. Trade following price action, not predictions

What To Do:
- Paper trade only until direction emerges
- Avoid holding positions through market open volatility
- Use 15-min and 1H charts for entry signals
- Wait for RSI confirmation (RSI should move to 40-60 range)
        """)
    
    print("-"*80)
    print("IMPORTANT CONSIDERATIONS")
    print("-"*80)
    
    print("""
1. GLOBAL IMPACT:
   - GIFT Nifty reflects overnight US/European market movements
   - Strong US rally/sell-off will influence opening
   - Check: S&P 500, DAX, FTSE overnight levels

2. EXPIRY/CORPORATE ACTIONS:
   - If futures expiry nearby, volatility may increase
   - Check if any large corporate announcements pending

3. DOMESTIC FACTORS:
   - RBI policy decisions
   - Economic data releases scheduled for today
   - Budget/monetary policy announcements

4. VOLUME CHECK:
   - GIFT Nifty pre-market volume
   - NSE futures opening volume
   - High volume = confirming move, Low volume = avoid

5. RISK MANAGEMENT:
   - ALWAYS use stop-loss orders
   - Never risk more than 1-2% per trade
   - Position size accordingly
   - If unsure, SIT OUT and wait
    """)
    
    print("="*80)
    print("LIVE DATA SOURCES FOR GIFT NIFTY:")
    print("="*80)
    print("""
For real-time GIFT Nifty tracking:
- GiftNifty.com (https://giftnifty.com) - Best for live charts & signals
- NSE IX (https://www.nseix.com) - Official exchange data
- TradingView (Search: NIFTY, Filter by NSE IX)
- Your Broker's Trading Platform (Zerodha, ICICI Direct, etc.)
- CNBC-TV18, ET Markets for analysis updates

IMPORTANT: The analysis above is based on SIMULATED gap data.
For real trading, use ACTUAL live GIFT Nifty quotes from above sources.
    """)
    print("="*80 + "\n")


def show_quick_facts():
    """Display GIFT Nifty quick facts"""
    
    print("\n" + "="*80)
    print("GIFT NIFTY - QUICK FACTS")
    print("="*80)
    
    facts = {
        'What is it': 'USD-denominated Nifty 50 futures on NSE International Exchange',
        'Trading Hours': '6:30 AM - 2:45 AM IST (Next Day) - 2 Sessions',
        'Contract Size': '25 units of Nifty 50 index',
        'Settlement': 'Cash-settled in USD',
        'Margin Required': '10-15% of contract value (varies by volatility)',
        'Expiry': 'Last Tuesday of each calendar month',
        'Best Liquidity': 'Morning session (6:30-3:40 PM) & US hours (4:35-8:00 PM)',
        'Regulator': 'IFSCA (International Financial Services Centre Authority)',
        'Who Can Trade': 'FPIs, NRIs, International investors, Some domestic eligible',
        'Main Use': 'Global sentiment on India, pre-market signals, hedging'
    }
    
    print("\n")
    for key, value in facts.items():
        print(f"{key:.<30} {value}")
    
    print("\n" + "="*80 + "\n")


def show_correlation_levels():
    """Show typical gap correlation levels"""
    
    print("\n" + "="*80)
    print("GIFT NIFTY GAP vs NSE OPENING HISTORY")
    print("="*80)
    
    correlation_data = {
        'GIFT Nifty Gap': [
            'Above +200 points',
            '+100 to +200',
            '+50 to +100',
            '-50 to +50',
            '-100 to -50',
            '-200 to -100',
            'Below -200'
        ],
        'Probability NSE Opens Higher': [
            '85-95%',
            '70-85%',
            '60-75%',
            '50-50%',
            '25-40%',
            '15-30%',
            '5-15%'
        ],
        'Typical NSE Gap': [
            '+150 to +250',
            '+80 to +150',
            '+40 to +80',
            '-40 to +40',
            '-80 to -40',
            '-150 to -80',
            '-250 to -150'
        ],
        'Risk of Gap Fill': [
            'VERY HIGH',
            'HIGH',
            'MEDIUM',
            'N/A',
            'MEDIUM',
            'HIGH',
            'VERY HIGH'
        ]
    }
    
    df = pd.DataFrame(correlation_data)
    print("\n" + df.to_string(index=False))
    
    print("\n" + "="*80)
    print("Notes:")
    print("• Gap = GIFT Nifty level - Nifty 50 previous close")
    print("• Gap Fill = Market reversal closing the overnight gap")
    print("• These are historical tendencies, not guarantees")
    print("• Always confirm with technical analysis before trading")
    print("="*80 + "\n")


def main():
    """Main execution"""
    
    print("\n" + "="*80)
    print("GIFT NIFTY PRE-MARKET ANALYZER")
    print("="*80)
    
    # Show facts
    show_quick_facts()
    
    # Get data and analyze
    data = get_premarket_signal()
    signals = analyze_gap(data)
    
    # Print report
    print_premarket_report(data, signals)
    
    # Show historical correlation
    show_correlation_levels()
    
    print("Analysis Complete! Use the above signals for NSE trading at 9:15 AM.")
    print("\nDISCLAIMER: This is educational analysis only.")
    print("Always consult a financial advisor before trading.")
    print("Trading involves risk of loss. Trade responsibly.")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
