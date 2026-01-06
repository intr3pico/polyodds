# Polymarket Scanner - Usage Guide

## 🚀 Getting Started (5 minutes)

### Step 1: Run Quick Setup
```bash
python quick_start.py
```
This will guide you through:
- Setting up Telegram bot credentials
- Configuring alert thresholds
- Creating your config.py file

### Step 2: Test Your Setup
```bash
python test_scanner.py
```
This verifies:
- API connectivity to Polymarket
- Telegram bot is working
- Database can be created
- All components are functional

### Step 3: Start Scanning
```bash
python polymarket_scanner.py
```
The scanner will:
- Analyze top performers from the last 7 days
- Start monitoring for new trades
- Send alerts to your Telegram

---

## 📱 Setting Up Telegram Bot

### Get Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get Chat ID
1. Search for `@userinfobot` in Telegram
2. Send `/start`
3. Copy your ID (a number like `123456789`)

### For Group Alerts
1. Add your bot to a Telegram group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find the `"chat":{"id":` field (will be negative, like `-1001234567890`)
5. Use this negative number as your CHAT_ID

---

## 🎛️ Configuration Options

Edit `config.py` to customize:

### Alert Thresholds
```python
LARGE_BET_THRESHOLD = 5000          # $5k = Medium alert
VERY_LARGE_BET_THRESHOLD = 10000    # $10k = High alert  
HUGE_BET_THRESHOLD = 50000          # $50k = Critical alert

NEW_WALLET_HOURS = 168              # 1 week
VERY_NEW_WALLET_HOURS = 24          # 1 day (very suspicious)

HIGH_WIN_RATE_THRESHOLD = 0.65      # 65%+ win rate
LOW_TRADE_COUNT_THRESHOLD = 10      # <10 trades = potential insider
```

### Scanning Behavior
```python
TRADE_POLL_INTERVAL = 30            # Check every 30 seconds
MAX_MARKETS_TO_TRACK = 100          # Limit to 100 markets
MIN_ALERT_SEVERITY = "MEDIUM"       # Only send MEDIUM+ alerts
```

### Categories to Monitor
```python
# Monitor only specific categories
CATEGORIES_TO_MONITOR = ["Politics", "Crypto"]

# Or exclude specific categories  
CATEGORIES_TO_EXCLUDE = ["Sports"]
```

---

## 🔍 Using the Utilities

### View Recent Alerts
```bash
# Last 24 hours
python alert_viewer.py list 24

# Last 48 hours, only CRITICAL
python alert_viewer.py list 48 CRITICAL

# Show statistics
python alert_viewer.py stats 168  # Last week

# Export to CSV
python alert_viewer.py export 24 alerts.csv
```

### Analyze a Specific Wallet
```bash
# Basic analysis
python wallet_analyzer.py 0x1234...5678

# Include recent trades
python wallet_analyzer.py 0x1234...5678 --trades
```

Example output:
```
======================================================================
Analyzing Wallet: 0x1234567890123456789012345678901234567890
======================================================================

📊 WALLET STATISTICS
----------------------------------------------------------------------
First Trade:     2024-12-15 14:23:45
Age:             456.3 hours
Total Trades:    47
Total Volume:    $127,450.00
Average Bet:     $2,711.70
Largest Bet:     $15,000.00
Markets Traded:  12
Win Rate:        68.2%
Profitable:      15/22 markets

🎯 RISK ASSESSMENT
----------------------------------------------------------------------
⚠️  High win rate (68%) with few trades
⚠️  Large average bet size ($2,712)
```

### Test Individual Components
```bash
# Test API connectivity
python test_scanner.py api

# Test Telegram  
python test_scanner.py telegram

# Test database
python test_scanner.py database

# Test wallet analysis
python test_scanner.py wallet

# Test configuration
python test_scanner.py config
```

---

## 🎯 Understanding Alerts

### Alert Severity Levels

**🔴 CRITICAL** - Immediate attention
- $50k+ bets
- New wallet (<24h) + large bet
- Single-market focus wallets
- Combines multiple suspicious factors

**🟠 HIGH** - Very suspicious
- $10k-$50k bets  
- New wallet + medium bet
- High win rate (65%+) + low trades (<10)

**🟡 MEDIUM** - Noteworthy
- $5k-$10k bets
- Some suspicious characteristics

**🟢 LOW** - Informational
- Below thresholds but logged

### Alert Example
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

### What Makes a Trade Suspicious?

1. **New Wallet + Large Bet**
   - Fresh wallet with immediate large position
   - Suggests insider using new identity

2. **Single Market Focus**
   - Wallet only trades ONE specific market
   - Strong signal of specific inside information

3. **Low Trades + High Win Rate**  
   - <10 trades but 70%+ accuracy
   - Either very lucky or very informed

4. **Huge Bet on Unlikely Outcome**
   - $50k+ on 5% probability
   - Requires strong conviction or knowledge

---

## 📊 Interpreting Results

### Historical Analysis
When scanner starts, it shows top performers:
```
📊 Top Performers (7 days)

1. 0x742d35c...
   Win: 72% | Vol: $125,450 | Trades: 34

2. 0x8a9b12f...  
   Win: 68% | Vol: $89,320 | Trades: 28
```

**How to use this:**
- Monitor these wallets closely
- Check their recent trades
- See what markets they're entering
- Consider following their positions

### Database Queries

The scanner creates a SQLite database with all data:

```bash
sqlite3 polymarket_scanner.db

# Find wallets with high win rates
SELECT wallet_address, win_rate, total_volume 
FROM wallet_stats 
WHERE win_rate > 0.65 
ORDER BY total_volume DESC 
LIMIT 10;

# Find biggest recent bets
SELECT wallet_address, market_title, usdc_value, side, outcome
FROM trades 
WHERE timestamp > strftime('%s', 'now', '-24 hours')
ORDER BY usdc_value DESC 
LIMIT 20;

# Alert frequency by market
SELECT market_title, COUNT(*) as alerts, SUM(trade_size) as total_size
FROM alerts
GROUP BY market_title
ORDER BY alerts DESC;
```

---

## 🔧 Advanced Usage

### Watch Specific Wallets
Add to config.py:
```python
WATCHED_WALLETS = [
    "0x1234567890123456789012345678901234567890",
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
]
```
These wallets will ALWAYS trigger alerts regardless of bet size.

### Ignore Bot Wallets
Add to config.py:
```python
IGNORED_WALLETS = [
    "0x0000000000000000000000000000000000000000",  # Known bot
]
```

### Multiple Alert Channels
Edit `polymarket_scanner.py`:
```python
# High priority alerts to one channel
high_priority_bot = TelegramBot(token1, chat_id1)

# Low priority to another
low_priority_bot = TelegramBot(token2, chat_id2)

# Send based on severity
if alert.severity in ["CRITICAL", "HIGH"]:
    high_priority_bot.send_message(message)
else:
    low_priority_bot.send_message(message)
```

### Run as Background Service (Linux)
Create systemd service file:
```bash
sudo nano /etc/systemd/system/polymarket-scanner.service
```

Add:
```ini
[Unit]
Description=Polymarket Scanner
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/scanner
ExecStart=/usr/bin/python3 /path/to/scanner/polymarket_scanner.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable polymarket-scanner
sudo systemctl start polymarket-scanner
sudo systemctl status polymarket-scanner
```

---

## 🐛 Troubleshooting

### No Alerts Appearing
1. Check `MIN_ALERT_SEVERITY` in config.py
2. Verify thresholds aren't too high
3. Confirm markets are being tracked: check logs

### Telegram Not Working
1. Verify bot token: send message to your bot manually
2. Check chat ID is correct
3. Ensure bot is started (send `/start`)
4. For groups: make sure bot is admin

### Database Errors
1. Check file permissions on `.db` file
2. Ensure only one scanner instance running
3. Delete database and restart (data will be rebuilt)

### API Rate Limits
1. Increase `TRADE_POLL_INTERVAL` (default: 30s)
2. Reduce `MAX_MARKETS_TO_TRACK` (default: 100)
3. Add `REQUEST_DELAY` between calls

---

## 📈 Best Practices

### Starting Out
1. Run for 24 hours with default settings
2. Review the alerts you receive
3. Adjust thresholds based on noise level
4. Focus on markets you understand

### Regular Maintenance
1. Check logs weekly: `tail -f scanner.log`
2. Review alert statistics: `python alert_viewer.py stats 168`
3. Clean old data periodically
4. Update ignored wallets list (bots, market makers)

### Research Workflow
1. Get alert on Telegram
2. Check wallet with: `python wallet_analyzer.py <address>`
3. View wallet on Polygonscan
4. Check market fundamentals
5. Make informed decision

---

## 🎓 Understanding Prediction Markets

### Why This Matters
- Insider trading is common in prediction markets
- Early detection can provide trading opportunities
- High-performing traders often have edge/information
- Market manipulation attempts can be spotted

### Limitations
- Not all large bets are insider trading
- High win rates can be skill or luck
- Market makers will trigger false positives
- Past performance ≠ future results

### Responsible Use
- Use as research tool, not trading signal
- Do your own due diligence
- Respect Polymarket ToS
- Don't harass other traders

---

## 📚 Resources

### Polymarket
- [Polymarket Docs](https://docs.polymarket.com/)
- [API Reference](https://docs.polymarket.com/api-reference/)
- [Discord](https://discord.gg/polymarket)

### This Project
- README.md - Full documentation
- config.py - All configuration options
- Database schema - SQLite tables

### Getting Help
- Check logs: `tail -f scanner.log`
- Run tests: `python test_scanner.py`
- Validate config: `python config.py`

---

## 🔐 Security Notes

- Keep `config.py` private (contains API keys)
- Don't share your bot token
- Use environment variables for production
- Review code before running
- Monitor for unexpected behavior

## 📝 Quick Reference

```bash
# Setup
python quick_start.py          # Initial configuration
python test_scanner.py         # Verify setup

# Running
python polymarket_scanner.py   # Start scanner

# Analysis
python wallet_analyzer.py <address>     # Analyze wallet
python alert_viewer.py list 24          # View alerts
python alert_viewer.py stats 168        # Statistics

# Testing  
python test_scanner.py api              # Test API
python test_scanner.py telegram         # Test Telegram
python config.py                        # Validate config
```

---

**Remember**: This tool is for research and monitoring. Always do your own research before making trading decisions.
