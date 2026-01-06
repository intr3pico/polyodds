"""
Social Media Monitoring Configuration
Configure Twitter/X and Truth Social monitoring
"""

import os

# ============================================================================
# TWITTER/X API CONFIGURATION
# ============================================================================

# Twitter API v2 Bearer Token
# Get it from: https://developer.twitter.com/
# Requires: Elevated access (free, but needs approval)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", None)

# Enable Twitter monitoring
ENABLE_TWITTER = True


# ============================================================================
# TRUTH SOCIAL CONFIGURATION
# ============================================================================

# Truth Social doesn't have a public API
# Options:
# 1. RSSHub: https://docs.rsshub.app/en/social-media.html#truth-social
# 2. Browser automation (Selenium/Playwright)
# 3. Manual monitoring via web scraping services

# Enable Truth Social monitoring (experimental)
ENABLE_TRUTHSOCIAL = True

# RSSHub instance (if you're running one)
RSSHUB_URL = os.getenv("RSSHUB_URL", "https://rsshub.app")


# ============================================================================
# MONITORED ACCOUNTS
# ============================================================================

# Accounts to monitor (Twitter usernames without @)
MONITORED_ACCOUNTS = [
    # Politics
    "realDonaldTrump",  # Trump
    "JoeBiden",         # Biden
    "KamalaHarris",     # Harris
    "SpeakerJohnson",   # House Speaker
    
    # Crypto/Tech
    "elonmusk",         # Musk
    "VitalikButerin",   # Vitalik
    "cz_binance",       # CZ
    "brian_armstrong",  # Coinbase CEO
    
    # Economy/Fed
    "federalreserve",   # Fed
    "SecYellen",        # Treasury
    
    # Add your own!
    # "naval",          # Naval Ravikant
    # "balajis",        # Balaji
]

# Influential accounts (get priority in matching)
INFLUENTIAL_ACCOUNTS = {
    "realDonaldTrump": 0.3,  # 30% boost to relevance score
    "JoeBiden": 0.3,
    "elonmusk": 0.25,
    "federalreserve": 0.2,
    "VitalikButerin": 0.15,
}


# ============================================================================
# MONITORING SETTINGS
# ============================================================================

# How often to check for new posts (seconds)
SOCIAL_CHECK_INTERVAL = 180  # 3 minutes

# Time window to look for posts (hours)
POST_LOOKBACK_HOURS = 1

# Maximum posts to fetch per account per check
MAX_POSTS_PER_ACCOUNT = 10

# Minimum confidence to match post with market (0-1)
MIN_POST_MATCH_CONFIDENCE = 0.6  # Lower than news (60%)

# Time window to look for market reactions (hours)
REACTION_TIME_WINDOW = 0.5  # 30 minutes (shorter for social)


# ============================================================================
# ALERT SETTINGS
# ============================================================================

# Alert on every influential post that matches a market
ALERT_ON_INFLUENTIAL_POST = True

# Only alert if there's trading activity
REQUIRE_TRADING_ACTIVITY = False  # Set False to get all Trump tweets matched to markets

# Minimum trades to trigger "market moving" alert
MIN_TRADES_FOR_REACTION = 3  # Lower than news (more sensitive)

# Alert severity by account
ACCOUNT_ALERT_SEVERITY = {
    "realDonaldTrump": "CRITICAL",  # Always critical
    "JoeBiden": "CRITICAL",
    "elonmusk": "HIGH",
    "federalreserve": "HIGH",
    "default": "MEDIUM"
}


# ============================================================================
# POST FILTERING
# ============================================================================

# Ignore retweets/reposts
IGNORE_RETWEETS = True

# Ignore replies
IGNORE_REPLIES = True

# Minimum engagement (likes + retweets) to process post
MIN_ENGAGEMENT = 0  # Set to 1000+ to only track viral posts

# Keywords that boost relevance (in addition to general matching)
HIGH_VALUE_KEYWORDS = [
    # Policy
    "tariff", "trade deal", "executive order", "announce",
    
    # Markets
    "rate cut", "rate hike", "inflation", "recession",
    
    # Crypto
    "Bitcoin", "crypto", "regulation", "SEC",
    
    # Geopolitics
    "China", "Russia", "NATO", "war",
]


# ============================================================================
# RATE LIMITING
# ============================================================================

# Twitter API rate limits (per 15 minutes):
# - User lookup: 900 requests
# - User tweets: 900 requests
# - Timeline: 180 requests

# To stay under limits with default settings:
# - 10 accounts × 20 checks/hour = 200 requests/hour
# - Well under 900/15min limit

# Requests per account per hour (for rate limit calculation)
REQUESTS_PER_ACCOUNT_PER_HOUR = 20  # 3 min intervals = 20 per hour


# ============================================================================
# TRUTH SOCIAL SPECIFIC
# ============================================================================

# Username on Truth Social (usually same as Twitter)
TRUTHSOCIAL_TRUMP_USERNAME = "realDonaldTrump"

# Method to use for Truth Social monitoring
# Options: "rsshub", "scraping", "manual"
TRUTHSOCIAL_METHOD = "rsshub"  # Easiest if you have RSSHub


# ============================================================================
# VALIDATION
# ============================================================================

def validate_social_config():
    """Validate social media configuration"""
    
    warnings = []
    errors = []
    
    if ENABLE_TWITTER and not TWITTER_BEARER_TOKEN:
        warnings.append("Twitter enabled but no bearer token - Twitter monitoring disabled")
    
    if ENABLE_TRUTHSOCIAL and TRUTHSOCIAL_METHOD == "rsshub":
        warnings.append("Truth Social via RSSHub - requires RSSHub instance")
    
    if not MONITORED_ACCOUNTS:
        errors.append("No accounts to monitor - add usernames to MONITORED_ACCOUNTS")
    
    if SOCIAL_CHECK_INTERVAL < 60:
        warnings.append("Check interval <60s may hit rate limits")
    
    # Calculate rate limit usage
    accounts = len(MONITORED_ACCOUNTS)
    checks_per_hour = 3600 / SOCIAL_CHECK_INTERVAL
    requests_per_hour = accounts * checks_per_hour
    
    if requests_per_hour > 800:
        warnings.append(f"High API usage: ~{requests_per_hour:.0f} requests/hour (limit: 900/15min)")
    
    if warnings:
        print("\n⚠️  Social Media Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print("\n❌ Social Media Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("\n🔧 Social Media Monitoring Configuration")
    print("=" * 60)
    print(f"Twitter Enabled: {ENABLE_TWITTER}")
    print(f"Twitter Token: {'✅ Set' if TWITTER_BEARER_TOKEN else '❌ Not Set'}")
    print(f"Truth Social: {ENABLE_TRUTHSOCIAL} (Method: {TRUTHSOCIAL_METHOD})")
    print(f"Monitored Accounts: {len(MONITORED_ACCOUNTS)}")
    print(f"  - {', '.join(MONITORED_ACCOUNTS[:5])}")
    print(f"Check Interval: {SOCIAL_CHECK_INTERVAL}s ({SOCIAL_CHECK_INTERVAL/60:.0f} min)")
    print(f"Match Confidence: {MIN_POST_MATCH_CONFIDENCE*100:.0f}%")
    
    # Rate limit calculation
    checks_per_hour = 3600 / SOCIAL_CHECK_INTERVAL
    requests_per_hour = len(MONITORED_ACCOUNTS) * checks_per_hour
    print(f"\nAPI Usage: ~{requests_per_hour:.0f} requests/hour")
    print("=" * 60)
    
    validate_social_config()
