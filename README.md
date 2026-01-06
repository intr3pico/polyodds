# Polymarket Insider Trading Scanner 🔍

A real-time monitoring system for detecting unusual trading patterns on Polymarket, with Telegram alerts for potential insider trading and high-performing traders.

## 🎯 Features

### Real-Time Detection
- **Large Bet Alerts**: Tiered alerts for $5k, $10k, and $50k+ trades
- **New Wallet Detection**: Flags wallets created within custom timeframes (default: 7 days)
- **Odds Movement Tracking**: Detects rapid price changes (10%+ movements)
- **Single-Market Focus**: Identifies wallets that only trade specific markets

### Wallet Analysis
- **Win Rate Calculation**: Tracks profitability across all positions
- **Trade History**: Complete transaction history per wallet
- **Volume Metrics**: Total trading volume and average bet sizes
- **Age Verification**: Determines wallet age from first trade

### Historical Analysis
- **High Performer Discovery**: Finds traders with 60%+ win rates
- **Volume Leaders**: Identifies whales and consistent traders
- **Pattern Recognition**: Analyzes trading behavior over time

### Alert System
- **Multi-Tier Severity**: LOW, MEDIUM, HIGH, CRITICAL
- **Telegram Integration**: Real-time notifications with rich formatting
- **Database Storage**: All alerts logged with SQLite
- **Smart Filtering**: Combines multiple signals for better alerts

## 📋 Prerequisites

- Python 3.8+
- Telegram account
- Internet connection (for API access)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Save the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Search for `@userinfobot` to get your **chat ID**

### 3. Configure the Scanner

Edit `polymarket_scanner.py` and update these lines:

```python
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # From @BotFather
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # From @userinfobot
```

### 4. Run the Scanner

```bash
python polymarket_scanner.py
```

## 📊 Alert Examples

### 🔴 CRITICAL Alert
```
🔴 CRITICAL ALERT - HUGE_BET

Market: Will Bitcoin reach $100k by end of 2025?
Trade: BUY Yes @ $0.650
Size: $75,000.00

Wallet: 0x1234...5678
Age: 12.5h | Trades: 3
Win Rate: N/A

Reason: Huge $75,000 bet | New wallet (12h old) | Only 3 trades | Only trades this market

[View Market] [View Wallet]
```

### 🟠 HIGH Alert
```
🟠 HIGH ALERT - VERY_LARGE_BET

Market: US Presidential Election 2028
Trade: BUY Republican @ $0.420
Size: $15,000.00

Wallet: 0xabcd...ef01
Age: 168.2h | Trades: 8
Win Rate: 75.0%

Reason: Very large $15,000 bet | Only 8 trades | High win rate (75%)

[View Market] [View Wallet]
```

### 🟡 MEDIUM Alert
```
🟡 MEDIUM ALERT - LARGE_BET

Market: Fed rate decision in March
Trade: SELL Rate Cut @ $0.280
Size: $7,500.00

Wallet: 0x9876...4321
Age: 720.0h | Trades: 45
Win Rate: 58.3%

Reason: Large $7,500 bet

[View Market] [View Wallet]
```

## 🎛️ Configuration Options

### Alert Thresholds

Edit these values in the `AlertGenerator` class:

```python
self.LARGE_BET = 5000          # First alert tier
self.VERY_LARGE_BET = 10000    # Second alert tier
self.HUGE_BET = 50000          # Highest alert tier

self.NEW_WALLET_HOURS = 168    # 1 week (suspicious if younger)
self.VERY_NEW_WALLET_HOURS = 24 # 1 day (very suspicious)

self.HIGH_WIN_RATE = 0.65      # 65% win rate threshold
self.LOW_TRADE_COUNT = 10      # Few trades = potential insider
```

### Polling Interval

Change how often the scanner checks for new trades:

```python
await scanner.run(analyze_history=True)
# Default: checks every 30 seconds

# In poll_recent_trades method:
await asyncio.sleep(interval)  # Change interval parameter
```

### Historical Analysis

```python
# Analyze last 30 days, minimum 10 trades
high_performers = scanner.analyze_historical_performance(
    days=30, 
    min_trades=10
)
```

## 📁 Database Structure

The scanner uses SQLite with 4 main tables:

### `trades`
- Stores all detected trades
- Indexed by wallet_address and timestamp
- Unique constraint on transaction_hash

### `wallet_stats`
- Cached wallet analysis results
- Updated on-demand or after TTL expires
- Includes win rates, volume, trade counts

### `alerts`
- All generated alerts
- Tracks Telegram delivery status
- Filterable by severity and timeframe

### `market_prices`
- Historical price data per token
- Used for odds movement detection
- Timestamped entries

## 🔧 Advanced Usage

### Custom Alert Logic

Add your own detection patterns by extending `AlertGenerator.generate_alert()`:

```python
# Example: Detect coordinated trading
if self.is_coordinated_trade(trade, wallet_stats):
    additional_flags.append("Coordinated trading detected")
    severity = "CRITICAL"
```

### Multiple Telegram Channels

Send different severity levels to different channels:

```python
# In __init__
self.high_priority_telegram = TelegramBot(token1, chat_id1)
self.low_priority_telegram = TelegramBot(token2, chat_id2)

# In send_alert
if alert.severity == "CRITICAL":
    self.high_priority_telegram.send_message(message)
else:
    self.low_priority_telegram.send_message(message)
```

### Export Top Performers

```python
import json

high_performers = scanner.analyze_historical_performance(days=30)

with open('top_traders.json', 'w') as f:
    json.dump(high_performers, f, indent=2)
```

### Filter by Market Category

```python
# Only monitor crypto markets
markets = self.api.get_active_markets()
crypto_markets = [m for m in markets if m.get('category') == 'Crypto']

for market in crypto_markets:
    self.tracked_markets[market['slug']] = market
```

## 🔍 Interpretation Guide

### What Makes a Trade Suspicious?

1. **New Wallet + Large Bet**
   - Wallet < 24 hours old + $10k+ bet = Very suspicious
   - Possible insider with fresh wallet

2. **Single-Market Focus**
   - Wallet only trades ONE specific market
   - Suggests specific inside information

3. **Low Trade Count + High Win Rate**
   - < 10 trades but 70%+ win rate
   - Either very lucky or very informed

4. **Huge Bet on Low-Probability Outcome**
   - $50k+ on 5% odds event
   - Strong conviction or inside info

5. **Rapid Odds Movement After Trade**
   - Large trade causes 10%+ price shift
   - Market-moving information

### False Positive Scenarios

- **Arbitrage Bots**: High win rate, many trades, not suspicious
- **Market Makers**: Large bets on both sides, providing liquidity
- **Whales**: Known large traders, not necessarily insiders
- **Hedging**: Same wallet taking opposite positions

## 📈 Performance Optimization

### Reduce API Calls

```python
# Increase cache TTL
self.cache_ttl = 600  # 10 minutes instead of 5

# Reduce polling frequency
await self.poll_recent_trades(interval=60)  # Once per minute

# Limit markets tracked
for slug, market in list(self.tracked_markets.items())[:20]:
```

### Database Optimization

```python
# Add more indexes for faster queries
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_trades_market 
    ON trades(market_id, timestamp)
""")

# Periodic cleanup of old data
cursor.execute("""
    DELETE FROM market_prices 
    WHERE timestamp < ?
""", (cutoff_timestamp,))
```

## 🐛 Troubleshooting

### "Rate limit exceeded"
- Reduce polling frequency
- Implement exponential backoff
- Use fewer concurrent market requests

### "No trades detected"
- Check internet connection
- Verify API endpoints are accessible
- Review market selection (ensure `active=true`)

### "Telegram messages not sending"
- Verify bot token is correct
- Ensure bot has been started (send `/start` in Telegram)
- Check chat_id is correct (should be a number or negative number for groups)

### "Database locked"
- Ensure only one scanner instance is running
- Check file permissions on `polymarket_scanner.db`

## 📊 Sample Output

```
2025-01-05 10:30:15 - INFO - Initializing scanner...
2025-01-05 10:30:17 - INFO - Tracking 87 markets
2025-01-05 10:30:18 - INFO - Analyzing historical performance for last 7 days...
2025-01-05 10:30:45 - INFO - High performer: 0x742d35... | Win rate: 72.5% | Volume: $125,450
2025-01-05 10:30:46 - INFO - High performer: 0x8a9b12... | Win rate: 68.2% | Volume: $89,320
2025-01-05 10:30:50 - INFO - Starting trade polling...
2025-01-05 10:31:22 - INFO - Alert sent: HIGH - Very large $12,500 bet | New wallet (36h old)
2025-01-05 10:32:15 - INFO - Alert sent: CRITICAL - Huge $55,000 bet | Only trades this market
```

## 🎯 Use Cases

1. **Copy Trading**: Follow high performers automatically
2. **Market Research**: Understand where smart money is flowing
3. **Risk Management**: Avoid markets with suspicious activity
4. **Due Diligence**: Investigate specific wallets or markets
5. **Academic Study**: Research prediction market behavior

## 🔐 Security Notes

- Never share your bot token publicly
- Keep your database file secure (contains trading patterns)
- Consider using environment variables for sensitive data
- Review alerts before acting on them (do your own research)

## 📝 License

This project is for educational and research purposes. Use responsibly and in accordance with Polymarket's Terms of Service.

## 🤝 Contributing

Improvements welcome! Consider adding:
- WebSocket support for true real-time monitoring
- Machine learning models for better pattern detection
- Discord/Slack integration
- Web dashboard for visualization
- Multi-exchange support (add Kalshi, Manifold, etc.)

## 📚 Resources

- [Polymarket API Docs](https://docs.polymarket.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Example Twitter Scanners](https://twitter.com/search?q=polymarket%20scanner)

---

**Disclaimer**: This tool is for monitoring public blockchain data. Trading decisions should be based on thorough research. Past performance doesn't guarantee future results.
