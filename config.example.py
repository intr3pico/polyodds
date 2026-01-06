"""
Configuration file for Polymarket Scanner
Edit these values to customize your scanner's behavior
"""

import os

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

# Get bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7669736221:AAEqyOR6VYuXUZfFBZhLv0UUiBrjU26BKek")

# Get your chat ID from @userinfobot on Telegram
# For groups, use the negative group ID (e.g., -1001234567890)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "974305190")

# Enable/disable Telegram notifications
ENABLE_TELEGRAM = True


# ============================================================================
# ALERT THRESHOLDS
# ============================================================================

# Bet size thresholds (in USDC)
LARGE_BET_THRESHOLD = 5000      # Medium severity
VERY_LARGE_BET_THRESHOLD = 10000  # High severity
HUGE_BET_THRESHOLD = 50000      # Critical severity

# Wallet age thresholds (in hours)
NEW_WALLET_HOURS = 168          # 1 week - considered "new"
VERY_NEW_WALLET_HOURS = 24      # 1 day - highly suspicious

# Trading behavior thresholds
HIGH_WIN_RATE_THRESHOLD = 0.65  # 65% win rate triggers higher alert
LOW_TRADE_COUNT_THRESHOLD = 10  # < 10 trades = potential insider
MIN_VOLUME_FOR_ANALYSIS = 1000  # Minimum $1k volume to analyze wallet

# Price movement thresholds
SIGNIFICANT_ODDS_MOVE = 0.10    # 10% price change = significant
RAPID_ODDS_TIME_WINDOW = 3600   # 1 hour window for "rapid" movement


# ============================================================================
# SCANNING CONFIGURATION
# ============================================================================

# Polling intervals (in seconds)
TRADE_POLL_INTERVAL = 30        # How often to check for new trades
MARKET_REFRESH_INTERVAL = 300   # How often to refresh market list
WALLET_CACHE_TTL = 300          # Cache wallet stats for 5 minutes

# Market filters
MAX_MARKETS_TO_TRACK = 100      # Limit markets to avoid rate limits
ONLY_HIGH_LIQUIDITY = False     # Only track markets with > $10k liquidity
MIN_MARKET_LIQUIDITY = 10000    # If above is True, minimum liquidity

# Categories to monitor (leave empty to monitor all)
# Options: "Crypto", "Politics", "Sports", "Business", "Pop Culture", "Science"
CATEGORIES_TO_MONITOR = []      # Empty = all categories

# Exclude specific categories
CATEGORIES_TO_EXCLUDE = []      # e.g., ["Sports"] to ignore sports


# ============================================================================
# HISTORICAL ANALYSIS
# ============================================================================

# Enable historical analysis on startup
ANALYZE_HISTORY_ON_START = True

# Historical analysis parameters
HISTORICAL_DAYS = 7             # Analyze last N days
MIN_TRADES_FOR_PERFORMER = 10   # Minimum trades to be "high performer"
TOP_PERFORMERS_TO_SHOW = 10     # Show top N performers on startup


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database file path
DB_PATH = "polymarket_scanner.db"

# Data retention (0 = keep forever)
KEEP_TRADES_DAYS = 90           # Delete trades older than 90 days
KEEP_ALERTS_DAYS = 30           # Delete alerts older than 30 days
KEEP_PRICES_DAYS = 7            # Delete price data older than 7 days


# ============================================================================
# API CONFIGURATION
# ============================================================================

# API endpoints (don't change unless Polymarket updates)
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 100   # Be conservative to avoid bans
REQUEST_DELAY = 0.5             # Seconds between requests


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Log file (None = console only)
LOG_FILE = "scanner.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


# ============================================================================
# ADVANCED FEATURES
# ============================================================================

# Enable/disable specific alert types
ALERT_NEW_WALLET_LARGE_BET = True
ALERT_SINGLE_MARKET_FOCUS = True
ALERT_HIGH_WINRATE_LOW_TRADES = True
ALERT_RAPID_ODDS_MOVEMENT = True
ALERT_WHALE_ACTIVITY = True

# Minimum severity to send alerts (LOW, MEDIUM, HIGH, CRITICAL)
MIN_ALERT_SEVERITY = "MEDIUM"   # Only send MEDIUM, HIGH, CRITICAL

# Send daily summary at specific hour (24-hour format, None = disabled)
DAILY_SUMMARY_HOUR = 9          # 9 AM daily summary

# Track specific wallets (send alerts regardless of thresholds)
WATCHED_WALLETS = [
    # "0x1234567890123456789012345678901234567890",
]

# Ignore specific wallets (known bots, market makers, etc.)
IGNORED_WALLETS = [
    # "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
]


# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

# Enable experimental features (use at your own risk)
ENABLE_WEBSOCKET = False        # Real-time WebSocket monitoring (not implemented yet)
ENABLE_ML_PREDICTIONS = False   # ML-based pattern detection (not implemented yet)
ENABLE_BLOCKCHAIN_ANALYSIS = False  # Deep blockchain analysis (not implemented yet)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values"""
    errors = []
    
    if ENABLE_TELEGRAM:
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            errors.append("TELEGRAM_BOT_TOKEN not configured")
        if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
            errors.append("TELEGRAM_CHAT_ID not configured")
    
    if LARGE_BET_THRESHOLD >= VERY_LARGE_BET_THRESHOLD:
        errors.append("LARGE_BET_THRESHOLD must be less than VERY_LARGE_BET_THRESHOLD")
    
    if VERY_LARGE_BET_THRESHOLD >= HUGE_BET_THRESHOLD:
        errors.append("VERY_LARGE_BET_THRESHOLD must be less than HUGE_BET_THRESHOLD")
    
    if HIGH_WIN_RATE_THRESHOLD < 0.5 or HIGH_WIN_RATE_THRESHOLD > 1.0:
        errors.append("HIGH_WIN_RATE_THRESHOLD must be between 0.5 and 1.0")
    
    if errors:
        print("\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these issues before running the scanner.\n")
        return False
    
    return True


if __name__ == "__main__":
    """Test configuration when run directly"""
    print("🔧 Configuration Test")
    print("=" * 50)
    print(f"Telegram Enabled: {ENABLE_TELEGRAM}")
    print(f"Large Bet Threshold: ${LARGE_BET_THRESHOLD:,}")
    print(f"Very Large Bet Threshold: ${VERY_LARGE_BET_THRESHOLD:,}")
    print(f"Huge Bet Threshold: ${HUGE_BET_THRESHOLD:,}")
    print(f"New Wallet Hours: {NEW_WALLET_HOURS}h")
    print(f"High Win Rate: {HIGH_WIN_RATE_THRESHOLD*100}%")
    print(f"Poll Interval: {TRADE_POLL_INTERVAL}s")
    print("=" * 50)
    
    if validate_config():
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors!")
