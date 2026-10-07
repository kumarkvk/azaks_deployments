# 📊 TradingView Pine Scripts for Nifty 50 Options Trading

Complete guide on using advanced TradingView scripts to analyze Nifty 50 for options trading.

---

## 🎯 Overview of Scripts

### **Script 1: Options Greeks & Volatility Analysis**
**File**: `script_1_options_greeks.pine`

**What It Does**:
- Calculates IV Rank (Implied Volatility Rank)
- Shows Support/Resistance levels
- Plots RSI for directional bias
- Identifies optimal strike levels using ATR
- Highlights option trading setups with background colors

**Best For**:
- Choosing which strategy to trade (Call/Put/Spread)
- Strike selection
- Understanding volatility environment
- Timing entries

**Key Indicators**:
- **IV Rank (0-100)**: 
  - <25 = Low IV (Good for Long options)
  - 25-75 = Normal
  - >75 = High IV (Good for Selling options)
- **Support/Resistance**: Where to place orders
- **RSI**: Direction bias
- **ATR**: Strike width recommendation

**Trading Signals**:
- 🟢 **Long Call Setup**: Low IV + Oversold + Support
- 🔴 **Short Call Setup**: High IV + Overbought + Resistance
- 🔵 **Long Put Setup**: Low IV + Overbought + Resistance
- 🟠 **Short Put Setup**: High IV + Oversold + Support

---

### **Script 2: Momentum & Theta Analysis**
**File**: `script_2_momentum_theta.pine`

**What It Does**:
- MACD for momentum and direction
- Theta decay tracking (days to expiry matter!)
- Rate of Change (ROC) for speed
- Divergence detection for reversals
- Acceleration indicators for Gamma trades

**Best For**:
- Identifying momentum reversals
- Theta decay strategies (Iron Condor, Straddle)
- Knowing when to exit
- Gamma trading setups

**Key Indicators**:
- **MACD**: Momentum direction
  - MACD > Signal = Bullish
  - MACD < Signal = Bearish
- **Theta Intensity**: Days to expiry impact
  - More days = Lower theta decay
  - Less days = Higher theta acceleration
- **Momentum**: How strong the move is
- **ROC**: Rate of price change

**Trading Setups**:
- **Iron Condor**: Consolidation + Low momentum + Theta acceleration
- **Call Spread**: Bullish momentum + Positive acceleration
- **Put Spread**: Bearish momentum + Negative acceleration
- **Theta Decay Play**: When expiry <3 days and price consolidating

---

### **Script 3: Volatility Crush & Strangle Setup**
**File**: `script_3_volatility_crush.pine`

**What It Does**:
- Bollinger Bands for volatility visualization
- Automatic strike level calculation
- Volatility crush detection
- Straddle/Strangle setup identification
- Price position relative to bands

**Best For**:
- Selling volatility (Credit spreads)
- Long straddle/strangle strategies
- Volatility crush trades
- Entry/Exit level identification

**Key Indicators**:
- **Bollinger Bands Width**: Volatility magnitude
  - Wide bands = High volatility
  - Narrow bands = Low volatility
- **Call/Put Strike Levels**: Colored horizontal lines
- **Distance from Bands**: Where price is positioned
- **IV Rank & Vol Status**: Expanding/Contracting

**Trading Setups**:
- 🟠 **Volatility Crush**: IV peaked then contracting
- 🔵 **Straddle**: Low IV + Consolidation
- 🟣 **Strangle**: Moderate IV + Mid-range price
- 🔴 **Short Call**: High IV + Near resistance
- 🟢 **Short Put**: High IV + Near support

---

## 📱 How to Use on TradingView

### **Step 1: Add Scripts to TradingView**

1. Go to **TradingView.com** (logged in)
2. Open **Pine Script Editor** (right side, "fx" icon)
3. Create new script:
   - Click "Create Script"
   - Paste one of the script codes
   - Click "Save"
4. Run the script:
   - Click "Add to Chart"
   - Choose chart timeframe (1D, 4H, 1H recommended)

### **Step 2: Apply to Nifty 50 Chart**

1. Search for "NIFTY" (NSE index)
2. Add all three scripts as separate indicators
3. Arrange in panels for easy viewing:
   - Panel 1: Price with Script 3 (Volatility Crush)
   - Panel 2: Script 1 (Volatility & Greeks)
   - Panel 3: Script 2 (Momentum & Theta)

### **Step 3: Customize Settings**

Each script has adjustable parameters:
- **IV Rank Period**: How far back to look
- **ATR Period**: Volatility measurement
- **Days to Expiry**: Adjust for your expiry date
- **Strike Distance**: How far from current price

---

## 🎯 Option Trading Strategies Using These Scripts

### **Strategy 1: Directional Spreads (Bull Call / Bear Put)**

**Setup**:
- Script 1 shows RSI bias (>65 or <35)
- Script 2 shows MACD direction
- Script 3 shows strike levels
- Script 1 shows IV rank

**Entry**:
1. Wait for high IV (>70) + momentum (MACD bullish)
2. Identify Call strike from Script 3 (orange line)
3. Check ATR width for spread width
4. Enter Bull Call Spread (Buy ATM, Sell OTM)

**Exit**:
1. Take profit at 50% max profit
2. Use Script 2 to exit if momentum reverses
3. Exit before last 2 days to avoid gamma blow-up

---

### **Strategy 2: Iron Condor (Theta Decay)**

**Setup**:
- Script 1: IV between 40-70 (not extreme)
- Script 3: Price consolidating (narrow bands)
- Script 2: Theta > 2 days to expiry
- Price in middle of Bollinger Bands

**Entry**:
1. Sell Call at resistance (Script 3 red line)
2. Buy Call further out (Script 3 extended)
3. Sell Put at support (Script 3 green line)
4. Buy Put further out
5. Width = 1-2 ATR

**Exit**:
1. Close at 50% max profit
2. Watch Script 2 for momentum change
3. Adjust if price approaches strike

---

### **Strategy 3: Long Straddle (Volatility Expansion)**

**Setup**:
- Script 1: IV Rank < 25 (Low volatility)
- Script 3: Straddle Setup signal (blue background)
- Script 2: Consolidation with low momentum
- 7-10 DTE (Days to Expiry)

**Entry**:
1. Buy Call at Script 3 call strike level
2. Buy Put at Script 3 put strike level
3. Same expiry, equidistant from current price

**Exit**:
1. Exit if Script 3 shows Volatility Crush
2. Take profit when price moves 2 ATR
3. Close both legs when 50% profit reached

---

### **Strategy 4: Long Strangle (Cheap Volatility)**

**Setup**:
- Script 1: IV Rank 30-50 (Cheaper than straddle)
- Script 3: Strangle Setup signal (purple background)
- Script 2: Low momentum
- 5-7 DTE

**Entry**:
1. Buy Call at Strike 1 (first resistance - Script 3)
2. Buy Put at Strike 2 (first support - Script 3)
3. Strikes are OTM (outside Bollinger Bands)

**Exit**:
1. Price breaks band = Take profit
2. 50% max profit achieved = Close
3. Script 2 shows reversal = Close both

---

### **Strategy 5: Volatility Crush (Short Straddle/Strangle)**

**Setup**:
- Script 3: Volatility Crush Setup (orange background)
- Script 1: IV Rank > 75 (High IV peak)
- Script 2: MACD shows reversal
- 3-5 DTE

**Entry**:
1. Sell Call at ATM (Script 3 call line)
2. Sell Put at ATM (Script 3 put line)
3. Collect premium from high IV

**Exit**:
1. Close at 50% profit (IV crushed)
2. Move stops to breakeven after 50% profit
3. Watch Script 2 for acceleration (close immediately)

---

## 📊 Reading the Scripts - Quick Reference

### **Script 1 Panel**
```
IV Rank > 75    = RED ZONE = Sell options, high premium decay
IV Rank 50      = YELLOW = Normal, use technicals to decide
IV Rank < 25    = GREEN ZONE = Buy options, cheap premium
Support Line    = Buy near this level
Resistance Line = Sell near this level
RSI > 70        = Overbought (Short/Put bias)
RSI < 30        = Oversold (Long/Call bias)
```

### **Script 2 Panel**
```
MACD > Signal   = BULLISH momentum (Long bias)
MACD < Signal   = BEARISH momentum (Short bias)
Theta 3+        = Good for theta strategies (Iron Condor)
Theta 0-2       = Theta accelerating fast (be careful!)
ROC positive    = Strong upward momentum
ROC negative    = Strong downward momentum
```

### **Script 3 Panel**
```
Blue Band (Straddle)   = Low IV consolidation
Purple Band (Strangle) = Moderate IV setup
Red Zone (Short Call)  = Sell calls here
Green Zone (Short Put) = Sell puts here
Orange Zone (Crush)    = Sell straddle here
Call Line (Red)        = Buy call or sell call strike
Put Line (Green)       = Buy put or sell put strike
```

---

## ⚠️ Important Rules for Options Trading

### **Risk Management**
1. **Never risk more than 1-2% per trade**
2. **Always use stops**:
   - Long options: Stop at 50-75% of premium paid
   - Short options: Stop at 2x credit received
3. **Position sizing**:
   - Keep buffer for early assignment
   - Adjust for margin requirements

### **Timing Rules**
- **Entry**: When Script signals are clear + IV conditions met
- **Exit**: At 50% profit OR when Script reverses
- **Don't hold**: Last 2 days before expiry (gamma risk!)

### **Script Combinations**
- **Script 1 + Script 2**: Decide direction
- **Script 1 + Script 3**: Decide strike levels
- **Script 2 + Script 3**: Decide timing
- **All 3 together**: Strongest signals

---

## 🔧 Settings for Nifty 50 (Recommended)

### **For Daily Charts (Multi-day holds)**
```
IV Rank Period: 50 days
ATR Period: 14
MACD: 12, 26, 9 (default)
BB Length: 20
Days to Expiry: 5-7 (adjust to your expiry)
```

### **For 4H Charts (Intraday)**
```
IV Rank Period: 30 days
ATR Period: 10
MACD: 8, 17, 9
BB Length: 14
Days to Expiry: Same as daily
```

### **For 1H Charts (Active Day Trading)**
```
IV Rank Period: 20 days
ATR Period: 8
MACD: 5, 13, 5
BB Length: 10
Days to Expiry: 1-2 days
```

---

## 📝 Daily Trading Checklist

**Before Market Open (9:15 AM)**:
- [ ] Check Script 1: What's the IV Rank today?
- [ ] Check Script 3: Where are strike levels?
- [ ] Check Script 2: What's the momentum?
- [ ] Decide which strategy fits best

**During Trading Hours**:
- [ ] Monitor Script signals
- [ ] Take profit at 50%
- [ ] Move stops when profitable
- [ ] Close at reversal signals

**Before Exit (3:30 PM)**:
- [ ] Close all positions
- [ ] Never hold overnight without monitoring
- [ ] Log the trade result

---

## 🎓 Examples (Real Scenarios)

### **Example 1: High IV Sell Setup**
- Script 1: IV Rank = 82% (Very high)
- Script 3: Price at middle of bands
- Script 2: Momentum reversal signal
- **Decision**: Sell Call/Put spread (credit strategy)
- **Entry**: Sell at resistance/support
- **Exit**: 50% profit or Script 2 reversal

### **Example 2: Low IV Buy Setup**
- Script 1: IV Rank = 18% (Very low)
- Script 3: Narrow Bollinger Bands
- Script 2: Consolidation
- **Decision**: Long Straddle
- **Entry**: Equidistant call/put from ATM
- **Exit**: 50% profit or bands break

### **Example 3: Volatility Crush**
- Script 3: Orange background (Crush signal)
- Script 1: IV dropped from 75 to 45
- Script 2: MACD reversed
- **Decision**: Short Straddle to profit from decay
- **Entry**: Sell ATM call & put
- **Exit**: 50% profit immediately

---

## 📞 Troubleshooting

**Q: Script not showing signals?**
- A: Adjust timeframe to 1D or 4H
- Make sure Days to Expiry matches your trade
- Check IV Rank period (should be 50+)

**Q: Strikes look wrong?**
- A: Strike Distance % might be too small/large
- ATR Period might need adjustment
- Make sure you're on right symbol (NIFTY, not NIFTY-I)

**Q: Signals conflicting?**
- A: Use Script 1 + Script 2 together for confirmation
- Weight Script 1 more heavily for IV extremes
- Wait for Script 2 momentum confirmation

---

## 🎯 Best Practices

1. **Always confirm signals across 2+ scripts**
2. **Trade with the direction of Script 2 (momentum)**
3. **Use Script 1 for strike selection**
4. **Use Script 3 for volatility environment**
5. **Start with small size** until you're confident
6. **Paper trade first** for 2-3 weeks
7. **Keep trading journal** of all entries/exits

---

## 📚 Next Steps

1. **Load all 3 scripts on Nifty chart**
2. **Spend 1 week observing signals** (no trading)
3. **Paper trade for 2-3 weeks**
4. **Start small: 1 lot when confident**
5. **Scale up slowly** as you gain experience

---

**Happy Trading! Remember: Risk Management > Profits** 📊

Last Updated: September 23, 2026
