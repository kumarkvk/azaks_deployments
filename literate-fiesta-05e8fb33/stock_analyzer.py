import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import yfinance as yf
from ta.momentum import RSIIndicator, MACD
from ta.trend import SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (15, 10)

class StockAnalyzer:
    """
    Comprehensive Stock Analysis Tool for NSE stocks, Nifty 50, and Bank Nifty
    """
    
    def __init__(self, symbol, period='1y', interval='1d'):
        """
        Initialize analyzer with stock symbol
        
        Args:
            symbol: Stock ticker (e.g., 'HDFC.NS', '^NSEI' for Nifty, '^NSEBANK' for Bank Nifty)
            period: Data period ('1mo', '3mo', '1y', '5y')
            interval: Data interval ('1d', '1wk', '1mo')
        """
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self.data = None
        self.fetch_data()
        
    def fetch_data(self):
        """Fetch stock data from yfinance"""
        try:
            print(f"📊 Fetching data for {self.symbol}...")
            self.data = yf.download(self.symbol, period=self.period, interval=self.interval, progress=False)
            if self.data.empty:
                print(f"❌ No data found for {self.symbol}")
                return False
            print(f"✅ Data fetched successfully! ({len(self.data)} records)")
            return True
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return False
    
    def calculate_indicators(self):
        """Calculate technical indicators"""
        if self.data is None:
            return None
        
        df = self.data.copy()
        
        # Simple Moving Averages (SMA)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Exponential Moving Average (EMA)
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        rsi = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi.rsi()
        
        # MACD (Moving Average Convergence Divergence)
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        # Volume-based indicators
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        return df
    
    def get_signals(self, df):
        """Generate buy/sell signals based on technical indicators"""
        signals = {}
        
        latest = df.iloc[-1]
        
        # RSI Signals
        if latest['RSI'] < 30:
            signals['RSI'] = '🟢 BUY (Oversold)'
        elif latest['RSI'] > 70:
            signals['RSI'] = '🔴 SELL (Overbought)'
        else:
            signals['RSI'] = '🟡 NEUTRAL'
        
        # MA Crossover
        if latest['EMA_12'] > latest['EMA_26']:
            signals['EMA'] = '🟢 BUY (Bullish Crossover)'
        else:
            signals['EMA'] = '🔴 SELL (Bearish Crossover)'
        
        # Price vs Bollinger Bands
        if latest['Close'] < latest['BB_Lower']:
            signals['BB'] = '🟢 BUY (Below Lower Band)'
        elif latest['Close'] > latest['BB_Upper']:
            signals['BB'] = '🔴 SELL (Above Upper Band)'
        else:
            signals['BB'] = '🟡 NEUTRAL'
        
        # Volume Signal
        if latest['Volume'] > latest['Volume_MA'] * 1.5:
            signals['Volume'] = '📈 HIGH (Strong Move Expected)'
        else:
            signals['Volume'] = '📊 NORMAL'
        
        return signals
    
    def plot_analysis(self):
        """Create comprehensive visualization"""
        df = self.calculate_indicators()
        if df is None:
            return
        
        # Get recent 100 records for cleaner chart
        df = df.tail(100)
        
        fig = plt.figure(figsize=(18, 12))
        
        # Plot 1: Price with Moving Averages
        ax1 = plt.subplot(3, 2, 1)
        ax1.plot(df.index, df['Close'], label='Close Price', color='black', linewidth=2)
        ax1.plot(df.index, df['SMA_20'], label='SMA 20', alpha=0.7)
        ax1.plot(df.index, df['SMA_50'], label='SMA 50', alpha=0.7)
        ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='blue')
        ax1.set_title(f'{self.symbol} - Price & Moving Averages', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: RSI
        ax2 = plt.subplot(3, 2, 2)
        ax2.plot(df.index, df['RSI'], label='RSI (14)', color='purple')
        ax2.axhline(70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax2.axhline(30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax2.set_title('Relative Strength Index (RSI)', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True)
        
        # Plot 3: MACD
        ax3 = plt.subplot(3, 2, 3)
        ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
        ax3.plot(df.index, df['MACD_Signal'], label='Signal', color='red')
        ax3.bar(df.index, df['MACD_Diff'], label='Histogram', alpha=0.3)
        ax3.set_title('MACD (Moving Average Convergence Divergence)', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True)
        
        # Plot 4: Volume
        ax4 = plt.subplot(3, 2, 4)
        colors = ['green' if df['Close'].iloc[i] >= df['Close'].iloc[i-1] else 'red' 
                  for i in range(1, len(df))]
        ax4.bar(df.index[1:], df['Volume'].iloc[1:], color=colors, alpha=0.6)
        ax4.plot(df.index, df['Volume_MA'], label='Volume MA (20)', color='blue', linewidth=2)
        ax4.set_title('Volume Analysis', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True)
        
        # Plot 5: EMA Crossover
        ax5 = plt.subplot(3, 2, 5)
        ax5.plot(df.index, df['Close'], label='Close', color='black', linewidth=2)
        ax5.plot(df.index, df['EMA_12'], label='EMA 12', color='blue', linewidth=2)
        ax5.plot(df.index, df['EMA_26'], label='EMA 26', color='red', linewidth=2)
        ax5.set_title('EMA Crossover Strategy', fontsize=12, fontweight='bold')
        ax5.legend()
        ax5.grid(True)
        
        # Plot 6: Daily Returns
        ax6 = plt.subplot(3, 2, 6)
        returns = df['Close'].pct_change() * 100
        colors_returns = ['green' if x > 0 else 'red' for x in returns]
        ax6.bar(df.index, returns, color=colors_returns, alpha=0.7)
        ax6.set_title('Daily Returns (%)', fontsize=12, fontweight='bold')
        ax6.grid(True)
        
        plt.tight_layout()
        return fig
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        df = self.calculate_indicators()
        if df is None:
            return
        
        latest = df.iloc[-1]
        signals = self.get_signals(df)
        
        print("\n" + "="*70)
        print(f"📈 STOCK ANALYSIS REPORT: {self.symbol}")
        print("="*70)
        
        print(f"\n📊 PRICE DATA:")
        print(f"  Current Price:    ₹{latest['Close']:.2f}")
        print(f"  Open:             ₹{latest['Open']:.2f}")
        print(f"  High:             ₹{latest['High']:.2f}")
        print(f"  Low:              ₹{latest['Low']:.2f}")
        
        # Calculate returns
        price_change = latest['Close'] - df['Close'].iloc[0]
        price_change_pct = (price_change / df['Close'].iloc[0]) * 100
        print(f"  Period Return:    {price_change_pct:+.2f}% ({price_change:+.2f})")
        
        print(f"\n📊 TECHNICAL INDICATORS:")
        print(f"  RSI (14):         {latest['RSI']:.2f} {signals['RSI']}")
        print(f"  MACD:             {latest['MACD']:.4f} {signals['EMA']}")
        print(f"  SMA 20:           ₹{latest['SMA_20']:.2f}")
        print(f"  SMA 50:           ₹{latest['SMA_50']:.2f}")
        print(f"  Bollinger Bands:  {signals['BB']}")
        print(f"  Volume:           {signals['Volume']}")
        
        print(f"\n🎯 TRADING SIGNALS:")
        for indicator, signal in signals.items():
            if indicator != 'RSI':
                print(f"  {indicator.upper():12} → {signal}")
        
        print(f"\n📌 TREND ANALYSIS:")
        if latest['Close'] > latest['SMA_50']:
            print(f"  Price above SMA 50: 🟢 UPTREND")
        else:
            print(f"  Price below SMA 50: 🔴 DOWNTREND")
        
        volatility = df['Close'].pct_change().std() * 100
        print(f"  Volatility (Daily): {volatility:.2f}%")
        
        print("\n" + "="*70)


def main():
    """Main function with examples"""
    
    print("\n🚀 STOCK ANALYSIS TOOL FOR INDIAN MARKETS")
    print("="*70)
    
    # Example 1: Analyze Nifty 50
    print("\n1️⃣  ANALYZING NIFTY 50...")
    nifty = StockAnalyzer('^NSEI', period='6mo')  # Nifty 50
    nifty.plot_analysis()
    nifty.generate_report()
    
    # Example 2: Analyze Bank Nifty
    print("\n2️⃣  ANALYZING BANK NIFTY...")
    bank_nifty = StockAnalyzer('^NSEBANK', period='6mo')  # Bank Nifty
    bank_nifty.plot_analysis()
    bank_nifty.generate_report()
    
    # Example 3: Analyze a specific stock (HDFC Bank)
    print("\n3️⃣  ANALYZING HDFC BANK...")
    hdfc = StockAnalyzer('HDFC.NS', period='3mo')
    hdfc.plot_analysis()
    hdfc.generate_report()
    
    # Save figures
    plt.savefig('nifty_analysis.png', dpi=300, bbox_inches='tight')
    print("\n✅ Charts saved as 'nifty_analysis.png'")
    plt.show()


if __name__ == "__main__":
    # Uncomment to run
    # main()
    
    # Or use individual analyzer:
    print("Stock Analysis Tool Ready!")
    print("\nUsage Example:")
    print("-" * 70)
    print("analyzer = StockAnalyzer('^NSEI', period='1y')  # Nifty 50")
    print("analyzer.plot_analysis()   # Show charts")
    print("analyzer.generate_report()  # Show signals")
    print("\nCommon Symbols:")
    print("  '^NSEI'      - Nifty 50")
    print("  '^NSEBANK'   - Bank Nifty")
    print("  'HDFC.NS'    - HDFC Bank")
    print("  'RELIANCE.NS' - Reliance")
    print("  'TCS.NS'     - TCS")
