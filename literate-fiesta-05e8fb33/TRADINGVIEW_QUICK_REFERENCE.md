# 📋 TradingView Scripts for Nifty 50 Options - QUICK REFERENCE

## 🚀 Scripts Summary

| Script | Purpose | Best For | Key Metrics |
|--------|---------|----------|-------------|
| **Script 1** | Greeks & Volatility | Strike selection + Strategy type | IV Rank, RSI, Support/Resistance |
| **Script 2** | Momentum & Theta | Timing + Greeks tracking | MACD, Theta decay, ROC |
| **Script 3** | Volatility Crush | Straddle/Strangle/Spreads | BB Bands, IV expansion/contraction |
| **Script 4** | Strategy Recommender | Quick decision making | Strategy scores (0-100) |

---

## 🔧 How to Copy Scripts to TradingView

### **Option A: Copy-Paste Method (Recommended for Beginners)**

1. Open TradingView.com in browser
2. Go to any chart (search "NIFTY")
3. Click "fx" icon (Pine Script Editor) on right
4. Click "Create Script"
5. **Delete default code** and paste one of these scripts:
   - Copy entire code from `.pine` file
   - Paste in TradingView editor
   - Click "Save"
6. Click "Add to Chart"
7. Repeat for all 4 scripts

### **Option B: Quick Link Method (If Available)**

- Check if TradingView has "Community Scripts" section
- Search "Nifty Options" to find community-created versions
- Add to favorites if available

---

## ⚡ Quick Setup (5 Minutes)

### **Step 1: Add Scripts (2 min)**
- Copy 4 scripts from files
- Paste into 4 separate TradingView indicators
- Add to chart

### **Step 2: Configure Settings (2 min)**
```
Days to Expiry: 5 (adjust to your expiry date)
ATR Period: 14 (for Nifty 50)
IV Rank Period: 50 (lookback days)
BB Length: 20 (standard)
```

### **Step 3: Arrange Charts (1 min)**
- Chart 1 (Price): Add Script 3
- Chart 2 (Below): Add Script 1
- Chart 3 (Below): Add Script 2
- Chart 4 (Below): Add Script 4

---

## 📊 Reading the Dashboard

### **At Market Open (9:15 AM)**

**Check Script 1 (Volatility & Greeks)**
```
IF IV Rank > 70   → "HIGH IV" → Consider SELLING options
IF IV Rank < 30   → "LOW IV"  → Consider BUYING options
IF RSI > 70       → "Overbought" → Sell/Short Call bias
IF RSI < 30       → "Oversold"   → Buy/Long Call bias
```

**Check Script 3 (Volatility Crush)**
```
IF Blue background → Long Straddle setup
IF Orange background → Volatility Crush setup
IF Red zone → Short Call zone
IF Green zone → Short Put zone
```

**Check Script 4 (Recommender)**
```
Best Score > 60 = STRONG signal
Best Score 40-60 = MODERATE signal
Best Score < 40 = WEAK signal (SKIP)
```

**Check Script 2 (Momentum)**
```
MACD > Signal → BULLISH momentum
MACD < Signal → BEARISH momentum
```

---

## 🎯 Quick Decision Tree for Options Trading

```
START: Check Script 1 IV Rank

├─ IV Rank > 70 (HIGH VOLATILITY - SELL)
│  ├─ Script 2: Is momentum reversing? 
│  │  ├─ YES → Short Strangle/Straddle (Script 3 orange)
│  │  └─ NO → Continue holding, wait for reversal
│  └─ Best Strategies: Iron Condor, Short Call/Put
│
├─ IV Rank 30-70 (NORMAL - DIRECTIONAL)
│  ├─ Script 2: Which direction (MACD)?
│  │  ├─ BULLISH → Bull Call Spread or Long Call
│  │  ├─ BEARISH → Bear Put Spread or Long Put
│  │  └─ NEUTRAL → Iron Condor or Straddle
│  └─ Check Script 3 for strike levels
│
└─ IV Rank < 30 (LOW VOLATILITY - BUY)
   ├─ Script 3: Consolidating?
   │  ├─ YES → Long Straddle (expect breakout)
   │  └─ NO → Long Strangle (cheaper premium)
   └─ Best Strategies: Long Straddle, Long Strangle

```

---

## 📱 One-Page Cheat Sheet

### **For Each Option Strategy**

**🟢 BULL CALL SPREAD**
- Check: Script 1 (IV < 60), Script 2 (MACD > Signal), Script 3 (Call strike)
- Entry: Buy ATM Call + Sell OTM Call
- Exit: 50% profit or Script 2 reversal
- Risk: Spread width

**🔴 BEAR PUT SPREAD**
- Check: Script 1 (IV < 60), Script 2 (MACD < Signal), Script 3 (Put strike)
- Entry: Sell OTM Put + Buy further OTM Put
- Exit: 50% profit or Script 2 reversal
- Risk: Short put strike - Long put strike

**🟠 IRON CONDOR**
- Check: Script 1 (IV 40-70), Script 3 (consolidating), Script 4 (IC score > 50)
- Entry: Bull Put + Bear Call spread
- Exit: 50% profit of total credit
- Risk: Larger of two spreads

**🟡 LONG STRADDLE**
- Check: Script 1 (IV < 25), Script 3 (blue background), Script 2 (low momentum)
- Entry: Buy ATM Call + Buy ATM Put
- Exit: 50% profit or bands break (Script 3)
- Risk: Theta decay

**🔵 LONG STRANGLE**
- Check: Script 1 (IV < 40), Script 3 (purple background), Script 2 (consolidating)
- Entry: Buy OTM Call + Buy OTM Put
- Exit: 50% profit or price breaks BB
- Risk: Lower than straddle, needs bigger move

**⚪ SHORT CALL**
- Check: Script 1 (IV > 70), Script 2 (MACD bearish), Script 3 (red zone)
- Entry: Sell Call at resistance
- Exit: 50% profit or Script 2 acceleration
- Risk: Unlimited (use stop)

**⚫ SHORT PUT**
- Check: Script 1 (IV > 70), Script 2 (MACD bullish), Script 3 (green zone)
- Entry: Sell Put at support
- Exit: 50% profit or Script 2 acceleration
- Risk: Strike price to zero

---

## ⏰ Trading Timeline

**Before Market Open (8:00 - 9:15 AM)**
1. [ ] Load all 4 scripts on Nifty chart
2. [ ] Check Script 1: What's IV Rank?
3. [ ] Check Script 4: What's recommended?
4. [ ] Decide which strategy fits today
5. [ ] Set up alerts

**Market Open (9:15 AM - 9:45 AM)**
6. [ ] Wait for first 30 mins of volume
7. [ ] Confirm Script 2 momentum
8. [ ] Check Script 3 for strike levels
9. [ ] ENTER TRADE

**During Day (10:00 AM - 3:00 PM)**
10. [ ] Monitor for 50% profit exit
11. [ ] Watch Script 2 for reversal
12. [ ] Move stops if profitable
13. [ ] EXIT at targets or stops

**Before Close (3:00 - 3:30 PM)**
14. [ ] CLOSE all positions
15. [ ] Do NOT hold overnight
16. [ ] Log entry, exit, profit/loss

---

## ✅ Daily Checklist

```
□ Open TradingView with all 4 scripts
□ Set Days to Expiry correctly
□ Check Script 4 for best strategy today
□ Confirm with Script 1 (IV Rank)
□ Confirm with Script 2 (Momentum)
□ Confirm with Script 3 (Strike levels)
□ Paper trade first (no real money)
□ Risk only 1-2% per trade
□ Use stop-losses ALWAYS
□ Take profit at 50% max
□ Close all positions by 3:30 PM
□ Log your trades
```

---

## 🚨 DO's and DON'Ts

### **DO**
✅ Combine signals from 2+ scripts
✅ Wait for Script 2 confirmation
✅ Take 50% profit (don't be greedy)
✅ Use stop-losses (non-negotiable)
✅ Start paper trading before real money
✅ Keep position size small (1 lot)
✅ Close positions before market close
✅ Adjust for expiry dates

### **DON'T**
❌ Trade on only 1 script signal
❌ Enter at market open (wait 30 mins)
❌ Hold overnight without monitoring
❌ Ignore stop-losses
❌ Risk more than 1-2% per trade
❌ Hold past 50% profit (greed kills)
❌ Add to losing positions
❌ Trade on last 2 days before expiry

---

## 🎓 Practice Plan

### **Week 1: Observation Only**
- Load scripts on Nifty chart
- Watch signals for entire week
- Do NOT trade
- Note which strategies would have worked

### **Week 2-3: Paper Trading**
- Use TradingView alerts
- Trade on paper/demo
- Track P&L
- Observe script accuracy

### **Week 4: Live Trading**
- Start with 1 lot (smallest size)
- Follow scripts exactly
- Risk only ₹500-1000 per trade
- Scale up only after 10 profitable trades

---

## 📞 Support & Troubleshooting

**Q: Script showing error "Cannot use 'array' in overlay mode"**
- A: Delete `var table` lines if having issues
- Or switch to Study (not Overlay) mode

**Q: Days to Expiry - What should I set?**
- A: If trading 5 DTE options, set to 5
- Update daily as expiry approaches

**Q: IV Rank very different from broker's IV?**
- A: Normal - this calculates from price movements
- Use relative comparison (high vs low), not absolute

**Q: Which timeframe to use?**
- A: Recommended: 1D chart for swing options
- Use 4H for intraday, 1H for very short term

---

## 🎯 Quick Links

- **TradingView**: https://www.tradingview.com
- **Nifty Chart**: https://www.tradingview.com/symbols/NIFTY/
- **NSE Data**: https://www.nseindia.com
- **Options Chain**: Your broker's platform

---

**Last Update**: September 23, 2026

**Remember: These scripts are GUIDES, not guarantees. Always use risk management!**

⚠️ Trading involves risk of loss. Only risk what you can afford to lose.
