#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFT Nifty Analysis & Pre-Market Signal Tool
Tracks GIFT Nifty futures and predicts NSE Nifty 50 opening direction
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import io
import warnings
warnings.filterwarnings('ignore')

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class GiftNiftyAnalyzer:
    """Analyze GIFT Nifty and provide pre-market signals"""
    
    def __init__(self):
        self.nifty_data = None
        self.previous_close = None
        self.session_1_data = None
        self.session_2_data = None
        
    def get_nifty_data(self):
        """Get Nifty 50 previous close"""
        try:
            print("[*] Fetching Nifty 50 data...")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            
            df = yf.download('^NSEI', start=start_date, end=end_date, 
                            progress=False, threads=False)
            
            if df is None or len(df) == 0:
                print("[!] No Nifty 50 data found")
                return False
            
            # Handle data structure
            df = df.reset_index()
            
            # Convert to numeric
            if 'Close' in df.columns:
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            
            df = df.dropna(subset=['Close'])
            
            if len(df) < 2:
                print("[!] Not enough data")
                return False
            
            self.previous_close = float(df.iloc[-1]['Close'])
            print(f"[+] Nifty 50 Previous Close: ₹{self.previous_close:.2f}")
            
            self.nifty_data = df
            return True
            
        except Exception as e:
            print(f"[!] Error fetching Nifty data: {str(e)}")
            return False
    
    def get_gift_nifty_data(self):
        """Get GIFT Nifty current price"""
        try:
            print("[*] Fetching GIFT Nifty data...")
            
            # Yahoo Finance doesn't have live GIFT Nifty, so we'll use a placeholder
            # In real scenario, you'd use: NSE IX data feed, TradingView API, or broker API
            
            # For demonstration, we'll create a simulated GIFT Nifty based on US market impact
            gift_data = self.simulate_gift_nifty()
            
            if gift_data:
                print(f"[+] GIFT Nifty Current Level: {gift_data['current_level']:.2f}")
                return gift_data
            return None
            
        except Exception as e:
            print(f"[!] Error fetching GIFT Nifty: {str(e)}")
            return None
    
    def simulate_gift_nifty(self):
        """
        Simulate GIFT Nifty movement based on:
        - Previous NSE Nifty 50 close
        - Time of day
        - Expected global market sentiment
        
        In production, replace with live API calls to NSE IX or broker platforms
        """
        
        if self.previous_close is None:
            return None
        
        # Get current time
        current_time = datetime.now()
        hours = current_time.hour
        minutes = current_time.minute
        
        # Simulate based on time of day
        # Note: This is for demonstration; use actual GIFT Nifty API in production
        
        # Random sentiment-based gap (in real scenario, based on US/EU market)
        np.random.seed(int(datetime.now().timestamp()) % 100)
        sentiment_gap = np.random.uniform(-200, 200)  # Points gap
        
        current_level = self.previous_close + sentiment_gap
        
        # Determine trading session
        if 6.5 <= hours < 15.67:  # 6:30 AM - 3:40 PM (Session 1)
            session = "Session 1 (Morning)"
        elif 16.58 <= hours or hours < 2.75:  # 4:35 PM - 2:45 AM (Session 2)
            session = "Session 2 (Evening/Night)"
        else:
            session = "Break"
        
        return {
            'current_level': current_level,
            'previous_close': self.previous_close,
            'gap': current_level - self.previous_close,
            'gap_pct': ((current_level - self.previous_close) / self.previous_close) * 100,
            'session': session,
            'timestamp': current_time.strftime('%H:%M:%S'),
            'date': current_time.strftime('%Y-%m-%d')
        }
    
    def analyze_and_signal(self, gift_data):
        """Generate pre-market trading signals"""
        
        if gift_data is None:
            return None
        
        signals = {}
        gap = gift_data['gap']
        gap_pct = gift_data['gap_pct']
        
        # Gap Analysis
        if gap > 100:
            signals['gap_signal'] = "STRONGLY BULLISH"
            signals['direction'] = "Expected Opening: HIGHER"
        elif gap > 50:
            signals['gap_signal'] = "BULLISH"
            signals['direction'] = "Expected Opening: HIGHER"
        elif gap > 0:
            signals['gap_signal'] = "SLIGHTLY BULLISH"
            signals['direction'] = "Expected Opening: Marginally HIGHER"
        elif gap > -50:
            signals['gap_signal'] = "SLIGHTLY BEARISH"
            signals['direction'] = "Expected Opening: Marginally LOWER"
        elif gap > -100:
            signals['gap_signal'] = "BEARISH"
            signals['direction'] = "Expected Opening: LOWER"
        else:
            signals['gap_signal'] = "STRONGLY BEARISH"
            signals['direction'] = "Expected Opening: SIGNIFICANTLY LOWER"
        
        # Trading Recommendation
        if gap > 150:
            signals['recommendation'] = "STRONG BUY at NSE open (Upside momentum)"
            signals['caution'] = "Beware of gap fill risk if US market reverses"
        elif gap > 0:
            signals['recommendation'] = "MILD BUY bias for NSE open"
            signals['caution'] = "Watch for selling on opening rally"
        elif gap < -150:
            signals['recommendation'] = "STRONG SELL at NSE open (Downside momentum)"
            signals['caution'] = "Beware of gap fill risk if US market reverses"
        elif gap < 0:
            signals['recommendation'] = "MILD SELL bias for NSE open"
            signals['caution'] = "Watch for buying on opening dip"
        else:
            signals['recommendation'] = "NEUTRAL - Wait for direction confirmation"
            signals['caution'] = "No clear pre-market direction"
        
        return signals
    
    def print_report(self, gift_data, signals):
        """Print comprehensive pre-market report"""
        
        print("\n" + "="*75)
        print("GIFT NIFTY PRE-MARKET ANALYSIS & NSE OPENING SIGNAL")
        print("="*75)
        
        print(f"\nTime: {gift_data['timestamp']} | Date: {gift_data['date']}")
        print(f"Session: {gift_data['session']}")
        
        print("\n" + "-"*75)
        print("PRICE LEVELS")
        print("-"*75)
        print(f"Nifty 50 Previous Close:   ₹{gift_data['previous_close']:>10.2f}")
        print(f"GIFT Nifty Current Level:  {gift_data['current_level']:>10.2f}")
        print(f"Gap (Points):              {gift_data['gap']:>10.2f} points")
        print(f"Gap (%):                   {gift_data['gap_pct']:>10.2f}%")
        
        print("\n" + "-"*75)
        print("ANALYSIS & SIGNALS")
        print("-"*75)
        print(f"Gap Assessment:            {signals['gap_signal']}")
        print(f"Opening Direction:         {signals['direction']}")
        print(f"Recommendation:            {signals['recommendation']}")
        print(f"Caution:                   {signals['caution']}")
        
        print("\n" + "-"*75)
        print("TRADING STRATEGY FOR NSE OPEN (9:15 AM)")
        print("-"*75)
        
        gap = gift_data['gap']
        
        if gap > 100:
            print("""
Strategy: BULLISH BREAKOUT
1. Wait for NSE open at 9:15 AM
2. If Nifty opens higher as expected, enter BUY on support levels
3. Set stop-loss 50 points below entry
4. Target: Previous resistance or +100 to +200 points from open
5. Risk/Reward: 1:2 or better
            """)
        elif gap < -100:
            print("""
Strategy: BEARISH BREAKDOWN  
1. Wait for NSE open at 9:15 AM
2. If Nifty opens lower as expected, enter SELL on resistance levels
3. Set stop-loss 50 points above entry
4. Target: Previous support or -100 to -200 points from open
5. Risk/Reward: 1:2 or better
            """)
        else:
            print("""
Strategy: NEUTRAL/CONSOLIDATION
1. No clear direction from overnight GIFT moves
2. Wait for first 15-30 minutes of trading for direction clarity
3. Follow market structure (support/resistance)
4. Use technical indicators for confirmation
5. Conservative position sizing until direction established
            """)
        
        print("-"*75)
        print("IMPORTANT NOTES")
        print("-"*75)
        print("• GIFT Nifty gap does NOT guarantee NSE opening in same direction")
        print("• Gap fill risk: Markets can reverse opening moves within 1-2 hours")
        print("• This analysis is based on SIMULATION (use live GIFT Nifty API in production)")
        print("• Always confirm with technical analysis and risk management")
        print("• Monitor global market news (US, Europe, China) for surprises")
        print("• Adjust positions based on 9:15 AM actual opening")
        
        print("\n" + "="*75)
    
    def run_full_analysis(self):
        """Run complete GIFT Nifty analysis"""
        
        print("\n" + "="*75)
        print("GIFT NIFTY PRE-MARKET ANALYSIS TOOL")
        print("="*75)
        
        # Get data
        if not self.get_nifty_data():
            print("[!] Failed to get Nifty data")
            return
        
        gift_data = self.get_gift_nifty_data()
        if gift_data is None:
            print("[!] Failed to get GIFT Nifty data")
            return
        
        # Analyze
        signals = self.analyze_and_signal(gift_data)
        
        # Report
        self.print_report(gift_data, signals)
        
        print("\nNote: For live GIFT Nifty tracking, visit:")
        print("  - https://giftnifty.com (Live GIFT Nifty quotes)")
        print("  - https://www.nseix.com (Official NSE IX website)")
        print("  - Your broker's trading platform")


def show_quick_reference():
    """Show quick trading reference"""
    
    print("\n" + "="*75)
    print("GIFT NIFTY QUICK REFERENCE")
    print("="*75)
    
    ref_data = {
        'Aspect': [
            'Trading Hours',
            'Contract Size',
            'Tick Size',
            'Expiry',
            'Settlement',
            'Margin (Approx)',
            'Best Liquidity',
            'Regulator',
            'Who Can Trade'
        ],
        'Details': [
            '6:30 AM - 2:45 AM IST (21 hours, 2 sessions)',
            '25 units of Nifty 50',
            '0.05 points',
            'Last Tuesday of month',
            'Cash-settled in USD',
            '10-15% of contract value',
            'During market overlaps (Asia/EU/US)',
            'IFSCA (International)',
            'FPIs, NRIs, Eligible investors'
        ]
    }
    
    df_ref = pd.DataFrame(ref_data)
    print("\n" + df_ref.to_string(index=False))
    
    print("\n" + "="*75 + "\n")


def main():
    """Main execution"""
    
    # Show quick reference
    show_quick_reference()
    
    # Run analysis
    analyzer = GiftNiftyAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
