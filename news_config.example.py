"""
News Correlation Configuration
Add your API keys here to enable news monitoring
"""

import os

# ============================================================================
# NEWS API CONFIGURATION
# ============================================================================

# NewsAPI.org - Get free API key at https://newsapi.org/
# Free tier: 100 requests/day, good for every 5-10 min checks
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "31b8df9b2e9f460b91ecc4c12948bba9")

# Twitter/X API - Requires Twitter Developer Account
# https://developer.twitter.com/
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", None)

# Enable news correlation feature
ENABLE_NEWS_CORRELATION = True

# ============================================================================
# NEWS MONITORING SETTINGS
# ============================================================================

# How often to check for breaking news (seconds)
NEWS_CHECK_INTERVAL = 300  # 5 minutes (don't go below 120 with free tier)

# Minimum confidence score to match news with market (0-1)
MIN_MATCH_CONFIDENCE = 0.7  # 70% confidence

# Time window to look for wallet reactions (hours)
REACTION_TIME_WINDOW = 1  # Look for trades in last 1 hour after news

# Minimum trades to trigger "high activity" alert
MIN_TRADES_FOR_ACTIVITY = 5

# Keywords to monitor (add what you care about)
NEWS_KEYWORDS = [
    # Politics
    "Trump", "Biden", "Harris", "election", "president", "congress", "2024 election", "primaries", 
    "swing state", "polling", "campaign", "debate", "Brazil", "Lula", "Bolsonaro", "Venezuela", "Maduro", "UN", "Europe", "Sweden"
    
    # Crypto
    "Bitcoin", "BTC", "Ethereum", "ETH", "crypto", "cryptocurrency", "Coinbase",
    "Binance", "SEC crypto", "Bitcoin ETF", "stablecoin", "Solana", "Memecoin", "Claude", ""
    
    # Economy
    "Fed", "Federal Reserve", "Powell", "inflation", "recession", "rate cut", "taxes", 
    
    # Tech
    "AI", "artificial intelligence", "OpenAI", "GPT", "Google", "Microsoft", "Claude", "Anthropic", 
    "Google Gemini", "AI regulation", "AGI", "Sam Altman", "art", "artist", "vibecode"
    
    # Geopolitics
    "war", "Ukraine", "Russia", "China", "Taiwan", "Israel", "Venezuela", "Latin America", "Brazil"
    
    # Markets
    "stock market", "SPX", "Nasdaq", "earnings"
]

# RSS feeds to monitor (free, no API key needed)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",  # BBC News
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",  # NYT World
    "https://feeds.reuters.com/reuters/topNews",  # Reuters Top News
    "https://www.theguardian.com/world/rss",  # Guardian World
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Top News
]

# ============================================================================
# ALERT SETTINGS
# ============================================================================

# Send alert when news matches market (even without trades)
ALERT_ON_NEWS_MATCH = True

# Only alert if smart wallets are trading
REQUIRE_SMART_WALLET_ACTIVITY = False

# Minimum wallet win rate to consider "smart money" (0-1)
SMART_WALLET_WIN_RATE = 0.65  # 65%+

# Minimum trades for wallet to be considered "experienced"
SMART_WALLET_MIN_TRADES = 10


# ============================================================================
# VALIDATION
# ============================================================================

def validate_news_config():
    """Check if news correlation can be enabled"""
    
    if not ENABLE_NEWS_CORRELATION:
        return True
    
    warnings = []
    
    if not NEWSAPI_KEY:
        warnings.append("NewsAPI key not set - will only use free RSS feeds")
    
    if not TWITTER_BEARER_TOKEN:
        warnings.append("Twitter API not configured - Twitter monitoring disabled")
    
    if NEWS_CHECK_INTERVAL < 120 and NEWSAPI_KEY:
        warnings.append("News check interval <2min may exceed free tier limits")
    
    if warnings:
        print("\n⚠️  News Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    return True


if __name__ == "__main__":
    print("\n🔧 News Correlation Configuration")
    print("=" * 60)
    print(f"News API Enabled: {ENABLE_NEWS_CORRELATION}")
    print(f"NewsAPI Key: {'✅ Set' if NEWSAPI_KEY else '❌ Not Set (RSS only)'}")
    print(f"Twitter API: {'✅ Set' if TWITTER_BEARER_TOKEN else '❌ Not Set'}")
    print(f"Check Interval: {NEWS_CHECK_INTERVAL}s ({NEWS_CHECK_INTERVAL/60:.0f} min)")
    print(f"Match Confidence: {MIN_MATCH_CONFIDENCE*100:.0f}%")
    print(f"Monitoring Keywords: {len(NEWS_KEYWORDS)}")
    print(f"RSS Feeds: {len(RSS_FEEDS)}")
    print("=" * 60)
    
    validate_news_config()
