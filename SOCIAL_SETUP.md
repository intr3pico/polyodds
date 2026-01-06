# 🐦 Social Media Monitoring Setup Guide

Monitor Trump's Truth Social & Twitter, plus other influential accounts, and get alerted when they post about topics with Polymarket markets!

---

## 🎯 What This Does

1. **Monitors Twitter/X accounts** (Trump, Biden, Musk, etc.)
2. **Tracks Truth Social** (Trump's posts)
3. **Matches posts to markets** (AI-powered relevance scoring)
4. **Detects market reactions** (checks if smart wallets are trading)
5. **Instant Telegram alerts** when influential posts correlate with trading

---

## 🚀 Quick Start Options

### Option 1: FREE Mode (No Twitter API - Truth Social Only)

**Works NOW but limited:**

```powershell
# Edit social_config.py
# Set: ENABLE_TWITTER = False

python scanner_full.py
```

**What you get:**
- ✅ Truth Social monitoring (via RSSHub or scraping)
- ❌ No Twitter monitoring
- ✅ Market matching
- ✅ Telegram alerts

**Limitation:** Truth Social scraping is experimental and may not work reliably.

---

### Option 2: Twitter API (RECOMMENDED)

Get Twitter API access for monitoring tweets in real-time!

#### Step 1: Apply for Twitter API Access (10 minutes)

1. **Go to**: https://developer.twitter.com/
2. **Click "Sign up" or "Apply"**
3. **Choose "Free" tier**
4. **Fill out form:**
   - Purpose: "Research/Analysis"
   - Description: "Monitoring public tweets for market research"
5. **Wait for approval** (usually instant to 24 hours)

#### Step 2: Create App & Get Bearer Token

1. In **Twitter Developer Portal**
2. **Create a new App**
3. Go to **"Keys and tokens"**
4. **Generate Bearer Token**
5. **Copy it** (looks like: `AAAAAAAAAA...`)

#### Step 3: Configure

Edit `social_config.py`:
```python
TWITTER_BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"
```

Or use environment variable:
```powershell
# Windows PowerShell
$env:TWITTER_BEARER_TOKEN="your_token_here"
```

#### Step 4: Run
```powershell
python scanner_full.py
```

**What you get:**
- ✅ Monitor ANY Twitter account in real-time
- ✅ Trump, Biden, Musk, Fed, etc.
- ✅ Match tweets to markets
- ✅ Detect smart wallet reactions
- ✅ 900 requests per 15 minutes (plenty!)

---

### Option 3: Full Setup (Twitter + Truth Social via RSSHub)

For maximum coverage, add RSSHub for Truth Social.

#### Install RSSHub (Optional but recommended)

**Option A: Docker (Easiest)**
```bash
docker run -d --name rsshub -p 1200:1200 diygod/rsshub
```

**Option B: Public Instance**
Just use: `https://rsshub.app` (free but rate limited)

#### Configure
Edit `social_config.py`:
```python
RSSHUB_URL = "http://localhost:1200"  # If using Docker
# OR
RSSHUB_URL = "https://rsshub.app"  # If using public
```

---

## 📱 Alert Examples

### 🐦 Trump Tweet Matched to Market
```
🐦 SMART MONEY REACTING

🐦 @realDonaldTrump:
"Massive tariffs on China coming next week. 
The biggest in history!"
Engagement: 45,231 ❤️  12,547 🔄

💹 Related Market:
Will Trump impose new China tariffs in Q1?
Match: 92%

⚡ Market Reaction (30m):
• Trades: 8
• Volume: $34,500
• Smart Money: 3 trades ($21,200)

[View Post] | [View Market]

Posted 12m ago
```

### 🎺 Truth Social Post
```
🎺 INFLUENTIAL POST

🎺 @realDonaldTrump:
"Fed is a disaster. Rate cuts NOW!"

💹 Related Market:
Will the Fed cut rates in January 2025?
Match: 88%

⚡ Market Reaction (30m):
• Trades: 12
• Volume: $56,800
• Smart Money: 5 trades ($38,100)

[View Post] | [View Market]
```

### 🐦 Elon Musk on Crypto
```
🐦 MARKET MOVING

🐦 @elonmusk:
"Bitcoin looking interesting at these levels"
Engagement: 128,456 ❤️  34,221 🔄

💹 Related Market:
Will Bitcoin hit $100k in 2025?
Match: 85%

⚡ Market Reaction (30m):
• Trades: 23
• Volume: $127,300
• Smart Money: 7 trades ($89,400)

[View Post] | [View Market]
```

---

## ⚙️ Configuration

Edit `social_config.py`:

### Accounts to Monitor
```python
MONITORED_ACCOUNTS = [
    "realDonaldTrump",  # Add/remove accounts
    "JoeBiden",
    "elonmusk",
    "VitalikButerin",
    # Add your own!
    "balajis",
    "naval",
]
```

### Alert Sensitivity
```python
# Only alert when there's trading
REQUIRE_TRADING_ACTIVITY = True  # More selective

# Or alert on every matched post
REQUIRE_TRADING_ACTIVITY = False  # Get all Trump tweets about markets
```

### Check Frequency
```python
SOCIAL_CHECK_INTERVAL = 180  # 3 minutes (default)
SOCIAL_CHECK_INTERVAL = 300  # 5 minutes (slower)
SOCIAL_CHECK_INTERVAL = 120  # 2 minutes (faster)
```

### Influential Accounts (Priority Boost)
```python
INFLUENTIAL_ACCOUNTS = {
    "realDonaldTrump": 0.3,  # 30% relevance boost
    "JoeBiden": 0.3,
    "elonmusk": 0.25,
    "yourfavoritetrader": 0.2,  # Add custom weights
}
```

---

## 🎓 How It Works

### 1. Tweet Collection
- Fetches recent tweets from monitored accounts (last 1 hour)
- Uses Twitter API v2 (elevated access)
- Filters out retweets/replies (configurable)

### 2. Post → Market Matching
Matches based on:
- **Keywords** (40% weight)
- **Word overlap** (30% weight)
- **Username bonus** (30% weight) - Trump/Biden get priority

Example:
```
Tweet: "Tariffs on China starting Monday"
Market: "Will Trump impose tariffs on China?"
Match: 95% ✅
```

### 3. Market Reaction Check
- Looks for trades in last 30 minutes (shorter than news)
- Identifies smart wallet activity
- Calculates volume and impact

### 4. Alert Decision
Sends alert if:
- Tweet from influential account
- Matches market (>60% confidence)
- AND (has trading activity OR is high-profile poster)

---

## 💡 Use Cases

### 1. Policy Trades
Trump tweets about tariffs → Market moves → You get alerted before consensus

### 2. Crypto Signals
Musk tweets about Bitcoin → Whales start buying → Alert before pump

### 3. Fed Positioning
Powell or Fed account posts → Rate market moves → Early entry signal

### 4. Conflict Alpha
Trump/Biden post about geopolitics → War/peace markets react → Trade the flow

---

## 🔐 Twitter API Details

### Free Tier Limits:
- 1,500 tweets per month (read)
- 50 tweets per month (write - not needed)
- 900 requests per 15 minutes

### With Default Settings:
- 10 accounts × 20 checks/hour = 200 requests/hour
- Well under limits!

### Rate Limit Management:
The scanner automatically:
- Caches results
- Spaces requests
- Handles rate limit errors gracefully

---

## 🐛 Troubleshooting

### "Twitter bearer token not set"
- Get token from developer.twitter.com
- Add to `social_config.py`
- Restart scanner

### "401 Unauthorized"
- Token is invalid
- Regenerate in Twitter Developer Portal
- Update config

### "No Truth Social posts found"
**Option 1:** Install RSSHub
```bash
docker run -d -p 1200:1200 diygod/rsshub
```

**Option 2:** Use public RSSHub
```python
RSSHUB_URL = "https://rsshub.app"
```

**Option 3:** Disable Truth Social
```python
ENABLE_TRUTHSOCIAL = False
```

### "Rate limit exceeded"
- Increase `SOCIAL_CHECK_INTERVAL`
- Reduce `MONITORED_ACCOUNTS` count
- Wait 15 minutes for reset

### "Posts found but no matches"
- Lower `MIN_POST_MATCH_CONFIDENCE` (try 0.5)
- Add keywords to `HIGH_VALUE_KEYWORDS`
- Check that relevant markets exist

---

## 📊 Performance

### Twitter API:
- CPU: Minimal
- Memory: ~150MB
- Network: ~5MB per hour
- API calls: ~200/hour (well under 900/15min limit)

### Truth Social (RSSHub):
- CPU: Minimal
- Memory: ~50MB additional
- Network: ~2MB per hour

---

## 🎯 Best Practices

1. **Start with Twitter only** - easier to setup, more reliable
2. **Monitor 5-10 accounts** - focus on high-signal sources
3. **Adjust sensitivity** after 24 hours
4. **Combine with insider detection** - best edge when aligned
5. **Don't blindly follow** - use as research signal

---

## 🚀 Quick Commands

```powershell
# Install dependencies (if needed)
pip install -r requirements.txt

# Run full scanner (all features)
python scanner_full.py

# Test configuration
python social_config.py

# Just social monitoring (no scanner)
# (not available yet, use scanner_full.py)
```

---

## 💬 Examples of What You'll Catch

### Real-World Scenarios:

**Scenario 1:** Trump tweets about NATO
→ Matches "Will NATO expand?" market  
→ Smart wallets buy "Yes" within 10 minutes
→ You get alerted → Entry opportunity

**Scenario 2:** Fed account posts about inflation data
→ Matches "Fed rate cut" market
→ Large volume spike detected
→ Alert → Position before retail catches up

**Scenario 3:** Musk replies to a Bitcoin meme
→ Matches BTC price markets
→ Crypto whales start accumulating
→ Early signal before price moves

---

## 🎉 You're Ready!

With social monitoring, you now have:
- 🔴 Insider trade detection
- 📰 Breaking news correlation
- 🐦 Real-time social media signals

**The complete edge stack for prediction markets!**

---

## 🔄 Next Steps

1. **Apply for Twitter API** (free, ~24h approval)
2. **Add your bearer token** to `social_config.py`
3. **Customize accounts** to monitor
4. **Run `python scanner_full.py`**
5. **Refine based on first 24h** of alerts

---

**Questions? Check the logs or test with `python social_config.py`** 🎯
