# 📊 Stock Analysis Tool for Indian Markets

A Python-based technical analysis tool for analyzing **Nifty 50**, **Bank Nifty**, and individual NSE stocks.

## 📋 Features

✅ **Real-time Data Fetching** - Downloads live market data from Yahoo Finance  
✅ **Technical Indicators** - RSI, MACD, Bollinger Bands, Moving Averages  
✅ **Trading Signals** - Automatic buy/sell signals based on multiple strategies  
✅ **Interactive Charts** - 6 comprehensive visualizations  
✅ **Detailed Reports** - Price analysis, trend detection, volatility metrics  

## 🔧 Installation

### Step 1: Install Python (if not already installed)
- Download from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Step 2: Install Required Libraries

```bash
pip install pandas numpy matplotlib seaborn yfinance ta-lib
```

**Alternative (if ta-lib fails):**
```bash
pip install pandas numpy matplotlib seaborn yfinance pandas-ta
```

## 🚀 Quick Start

### Method 1: Run Pre-built Analysis
```python
from stock_analyzer import StockAnalyzer

# Analyze Nifty 50
nifty = StockAnalyzer('^NSEI', period='6mo')
nifty.plot_analysis()
nifty.generate_report()
```

### Method 2: Analyze Specific Stocks
```python
# Bank Nifty
bank_nifty = StockAnalyzer('^NSEBANK', period='3mo')
bank_nifty.plot_analysis()
bank_nifty.generate_report()

# Individual Stock (HDFC Bank)
hdfc = StockAnalyzer('HDFC.NS', period='1y')
hdfc.plot_analysis()
hdfc.generate_report()
```

## 📍 Supported Symbols

| Symbol | Company/Index |
|--------|---------------|
| `^NSEI` | Nifty 50 |
| `^NSEBANK` | Bank Nifty |
| `HDFC.NS` | HDFC Bank |
| `RELIANCE.NS` | Reliance Industries |
| `TCS.NS` | Tata Consultancy Services |
| `ICICIBANK.NS` | ICICI Bank |
| `SBIN.NS` | State Bank of India |
| `BHARTIARTL.NS` | Bharti Airtel |
| `LT.NS` | Larsen & Toubro |
| `INFY.NS` | Infosys |

*Add `.NS` suffix for NSE stocks*

## 📊 Indicators Explained

### 1. **RSI (Relative Strength Index)**
- **Value:** 0-100
- **Buy Signal:** < 30 (Oversold)
- **Sell Signal:** > 70 (Overbought)
- **Interpretation:** Momentum indicator

### 2. **MACD (Moving Average Convergence Divergence)**
- **Buy Signal:** MACD crosses above Signal line
- **Sell Signal:** MACD crosses below Signal line
- **Interpretation:** Trend-following momentum

### 3. **Moving Averages (SMA/EMA)**
- **SMA 20:** Short-term trend
- **SMA 50:** Medium-term trend
- **SMA 200:** Long-term trend
- **Buy Signal:** Price above MA
- **Sell Signal:** Price below MA

### 4. **Bollinger Bands**
- **Upper Band:** Resistance level
- **Lower Band:** Support level
- **Buy Signal:** Price below lower band
- **Sell Signal:** Price above upper band

### 5. **Volume Analysis**
- **High Volume:** Confirms price move
- **Low Volume:** Weak trend
- **Signal:** Volume > 1.5x MA = Strong move expected

## 📈 Charts Generated

1. **Price & Moving Averages** - Price trend with SMA 20, 50 and Bollinger Bands
2. **RSI** - Overbought/Oversold levels
3. **MACD** - Trend change signals
4. **Volume** - Trading volume with MA
5. **EMA Crossover** - Short-term trend
6. **Daily Returns** - Volatility visualization

## ⚠️ Risk Management Tips

- **Always use Stop Loss** - Limit losses to 1-2% per trade
- **Risk-Reward Ratio** - Never risk more than you can afford to lose
- **Diversification** - Don't put all capital in one stock
- **Follow Multiple Signals** - Don't rely on single indicator
- **Confirm with Volume** - Volume should support price move
- **Backtest** - Test strategy on historical data first

## 📌 Trading Strategy Example

```python
analyzer = StockAnalyzer('HDFC.NS', period='1y')
df = analyzer.calculate_indicators()
latest = df.iloc[-1]

# Combined Signal Strategy
if (latest['RSI'] < 40 and 
    latest['Close'] > latest['SMA_50'] and 
    latest['EMA_12'] > latest['EMA_26']):
    print("🟢 STRONG BUY SIGNAL")
elif (latest['RSI'] > 60 and 
      latest['Close'] < latest['SMA_50']):
    print("🔴 STRONG SELL SIGNAL")
```

## 🔗 External Resources

- **Technical Analysis Guide:** https://www.investopedia.com/
- **NSE Website:** https://www.nseindia.com/
- **Chart Patterns:** https://en.wikipedia.org/wiki/Candlestick_pattern

## 📝 Disclaimer

⚠️ **This tool is for educational purposes only.**
- Past performance doesn't guarantee future results
- Always consult a financial advisor before trading
- Use this tool to understand markets, not to make guaranteed profits
- Trading involves risk of loss of capital

## 🤝 Support

For issues or questions:
1. Check internet connection (needed for live data)
2. Ensure all libraries are installed correctly
3. Verify stock symbols are correct (use `.NS` for NSE)
4. Check if market is open (NSE operates 9:15 AM - 3:30 PM IST)

---

**Happy Trading! 📈**
