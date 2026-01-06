# 📰 News Correlation Setup Guide

This feature detects breaking news and correlates it with Polymarket activity and smart wallet movements.

## 🎯 What It Does

1. **Monitors Breaking News** from multiple sources
2. **Matches Headlines** to Polymarket markets using AI
3. **Detects Smart Money** - checks if top wallets are trading
4. **Sends Instant Alerts** when news + market + wallet activity align

---

## 🚀 Quick Start (5 minutes)

### Option 1: Free Mode (RSS Only - NO API KEY NEEDED)

This works immediately without any setup!

```powershell
# Just run the scanner with news enabled
python scanner_with_news.py
```

**What you get:**
- ✅ BBC, Reuters, NYT, Guardian RSS feeds
- ✅ News-to-market matching
- ✅ Smart wallet activity detection
- ❌ Limited to ~50 articles per check
- ❌ No Twitter monitoring

---

### Option 2: Enhanced Mode (NewsAPI - FREE TIER)

Get 100 requests/day for free = check every 15 minutes!

#### Step 1: Get Free NewsAPI Key (2 minutes)

1. **Go to**: https://newsapi.org/register
2. **Sign up** with your email (free, no credit card)
3. **Copy your API key** (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

#### Step 2: Configure

Edit `news_config.py`:
```python
NEWSAPI_KEY = "YOUR_KEY_HERE"
```

Or use environment variable (more secure):
```powershell
# Windows PowerShell
$env:NEWSAPI_KEY="your_key_here"

# Windows CMD
set NEWSAPI_KEY=your_key_here
```

#### Step 3: Run
```powershell
python scanner_with_news.py
```

**What you get:**
- ✅ All RSS feeds
- ✅ NewsAPI (thousands of sources)
- ✅ Breaking news priority
- ✅ Keyword filtering
- ✅ Check every 5-15 minutes
- ❌ No Twitter (requires paid API)

---

### Option 3: Full Mode (Twitter + NewsAPI)

Requires Twitter Developer Account (harder to get, may require approval).

1. **Apply**: https://developer.twitter.com/
2. **Get bearer token** from Twitter Developer Portal
3. **Add to `news_config.py`**:
   ```python
   TWITTER_BEARER_TOKEN = "your_twitter_token"
   ```

---

## 📱 Alert Examples

### Example 1: Breaking News Match
```
📰 NEWS MATCHED

📰 Breaking News:
Fed announces surprise rate cut of 0.5%

💹 Related Market:
Will the Fed cut rates in January 2025?
Match Confidence: 95%

⚡ Recent Activity (1h):
• Total Trades: 3
• Volume: $8,500
• Smart Money: 0 trades ($0)

🔗 Links:
[Read News] | [View Market]

Posted 5m ago
```

### Example 2: Smart Money Moving
```
🎯 SMART MONEY MOVING

📰 Breaking News:
Trump announces tariff plan for China

💹 Related Market:
Will Trump impose new China tariffs by March?
Match Confidence: 88%

⚡ Recent Activity (1h):
• Total Trades: 12
• Volume: $45,300
• Smart Money: 4 trades ($32,100)

🔗 Links:
[Read News] | [View Market]

Posted 12m ago
```

### Example 3: High Activity
```
📈 HIGH ACTIVITY

📰 Breaking News:
Bitcoin surges past $100,000 for first time

💹 Related Market:
Will Bitcoin hit $100k in 2025?
Match Confidence: 92%

⚡ Recent Activity (1h):
• Total Trades: 23
• Volume: $127,500
• Smart Money: 2 trades ($18,000)

🔗 Links:
[Read News] | [View Market]

Posted 8m ago
```

---

## ⚙️ Configuration Options

Edit `news_config.py` to customize:

### Matching Sensitivity
```python
# Higher = fewer but more accurate matches
MIN_MATCH_CONFIDENCE = 0.7  # 70% (default)
MIN_MATCH_CONFIDENCE = 0.8  # 80% (stricter)
MIN_MATCH_CONFIDENCE = 0.6  # 60% (more matches)
```

### Check Frequency
```python
NEWS_CHECK_INTERVAL = 300   # 5 minutes (default)
NEWS_CHECK_INTERVAL = 900   # 15 minutes (slower)
NEWS_CHECK_INTERVAL = 180   # 3 minutes (faster, needs NewsAPI)
```

### Keywords to Monitor
```python
NEWS_KEYWORDS = [
    "Trump", "Biden",           # Politics
    "Bitcoin", "crypto",        # Crypto
    "Fed", "inflation",         # Economy
    "AI", "OpenAI",            # Tech
    # Add your own!
]
```

### Alert Filters
```python
# Only alert when smart wallets are active
REQUIRE_SMART_WALLET_ACTIVITY = True

# Alert on every news match (even without trades)
ALERT_ON_NEWS_MATCH = False

# Minimum trades to trigger "high activity"
MIN_TRADES_FOR_ACTIVITY = 5  # Default
```

---

## 🎓 How It Works

### 1. News Collection
- **RSS Feeds**: BBC, Reuters, NYT, Guardian (free, always on)
- **NewsAPI**: 68,000+ sources worldwide (with API key)
- **Twitter**: Real-time tweets from key accounts (with bearer token)

### 2. Market Matching Algorithm
Calculates relevance score based on:
- **Keyword overlap** (40% weight)
- **Entity matching** (30% weight) - names, organizations
- **Word similarity** (30% weight)

Example:
```
News: "Fed announces rate cut"
Market: "Will Fed cut rates in Q1?"
Match: 95% ✅
```

### 3. Wallet Activity Check
- Looks for trades in last 1 hour
- Identifies if "smart wallets" (65%+ win rate) are trading
- Calculates total volume and activity level

### 4. Alert Decision
Sends alert if:
- News matches market (>70% confidence)
- AND (recent trades OR smart wallet activity)

---

## 💡 Use Cases

### 1. Front-Run the Crowd
News breaks → Smart wallets trade → You get alerted → Take position before market moves

### 2. Validate Positions
You hold position → News breaks → Check if smart money agrees or disagrees

### 3. Discover Markets
News about topic you didn't know had a market → Get notified → Explore opportunity

### 4. Exit Signals
Hold position → Negative news breaks → Smart money exits → You get warning

---

## 🐛 Troubleshooting

### "No news items found"
- Check internet connection
- Verify NewsAPI key if using it
- RSS feeds might be temporarily down (try again in 5 min)

### "News found but no matches"
- Lower `MIN_MATCH_CONFIDENCE` in news_config.py
- Add more keywords to `NEWS_KEYWORDS`
- News might not be related to active markets

### "Matches found but no alerts"
- Check `REQUIRE_SMART_WALLET_ACTIVITY` setting
- Increase `REACTION_TIME_WINDOW` (currently 1 hour)
- Lower `MIN_TRADES_FOR_ACTIVITY` threshold

### "Too many alerts"
- Raise `MIN_MATCH_CONFIDENCE` (try 0.8)
- Enable `REQUIRE_SMART_WALLET_ACTIVITY = True`
- Increase `NEWS_CHECK_INTERVAL` (slower checks)

---

## 📊 Performance

### With Free RSS Only:
- ~30-50 articles per check (every 5 min)
- CPU: Minimal
- Memory: ~100MB
- Network: ~5MB per hour

### With NewsAPI:
- ~100-200 articles per check
- CPU: Minimal
- Memory: ~150MB
- Network: ~10MB per hour
- API Limit: 100 requests/day (check every 15 min)

---

## 🔐 Privacy & Security

- All news processing is local (no data sent anywhere)
- API keys stored locally in config files
- No personal data collected
- News sources are public RSS/API feeds

**⚠️ Never commit API keys to GitHub!**

Add to `.gitignore`:
```
news_config.py
.env
```

---

## 🎯 Best Practices

1. **Start with RSS only** - see if you like it
2. **Add NewsAPI** for better coverage
3. **Monitor first 24h** - adjust thresholds
4. **Focus keywords** on topics you trade
5. **Cross-reference** - don't blindly follow alerts

---

## 📚 Additional Resources

- **NewsAPI Docs**: https://newsapi.org/docs
- **RSS Feed List**: https://github.com/topics/rss-feeds
- **Polymarket API**: https://docs.polymarket.com/

---

## 🚀 Quick Commands

```powershell
# Install dependencies (includes feedparser for RSS)
pip install -r requirements.txt

# Run with news correlation
python scanner_with_news.py

# Run without news (original scanner)
python polymarket_scanner.py

# Test news configuration
python news_config.py
```

---

## 💡 Pro Tips

1. **Morning routine**: Check overnight alerts for position ideas
2. **Keyword alerts**: Add niche keywords competitors miss
3. **Confidence tweaking**: Start at 0.8, lower if too quiet
4. **Smart money only**: Enable `REQUIRE_SMART_WALLET_ACTIVITY` for signal
5. **Multiple time windows**: Check 1h, 6h, 24h for different strategies

---

**You're all set! Run `python scanner_with_news.py` and start catching news-driven opportunities!** 🎯
