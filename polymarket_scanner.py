"""
Polymarket Insider Trading Scanner
Monitors for unusual trading patterns, new wallets with large bets, and high-performing traders
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import requests
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

# Import configuration
try:
    import config
except ImportError:
    print("⚠️  Warning: config.py not found, using default values")
    config = None

# Configure logging
log_level = getattr(logging, config.LOG_LEVEL if config else "INFO")
log_format = config.LOG_FORMAT if config else '%(asctime)s - %(levelname)s - %(message)s'

if config and config.LOG_FILE:
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(level=log_level, format=log_format)

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    timestamp: int
    wallet_address: str
    market_id: str
    market_title: str
    token_id: str
    side: str  # BUY or SELL
    size: float  # Number of tokens
    price: float  # Price per token
    usdc_value: float
    outcome: str
    transaction_hash: str
    

@dataclass
class WalletStats:
    """Statistics for a wallet"""
    address: str
    first_trade_time: int
    total_trades: int
    total_volume: float
    markets_traded: Set[str]
    win_rate: Optional[float]
    avg_bet_size: float
    largest_bet: float
    profitable_markets: int
    total_markets: int
    

@dataclass
class Alert:
    """Alert data structure"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    wallet_address: str
    market_title: str
    market_slug: str
    trade_size: float
    price: float
    side: str
    outcome: str
    wallet_age_hours: Optional[float]
    wallet_total_trades: int
    wallet_win_rate: Optional[float]
    odds_movement: Optional[float]
    reason: str
    timestamp: int


class PolymarketAPI:
    """Wrapper for Polymarket API calls"""
    
    GAMMA_API = "https://gamma-api.polymarket.com"
    DATA_API = "https://data-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"
    
    @staticmethod
    def get_active_markets(limit=100, offset=0) -> List[Dict]:
        """Get all active markets"""
        try:
            response = requests.get(
                f"{PolymarketAPI.GAMMA_API}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "limit": limit,
                    "offset": offset
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    @staticmethod
    def get_market_by_slug(slug: str) -> Optional[Dict]:
        """Get market details by slug"""
        try:
            response = requests.get(f"{PolymarketAPI.GAMMA_API}/markets/{slug}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching market {slug}: {e}")
            return None
    
    @staticmethod
    def get_wallet_activity(wallet: str, limit=500) -> List[Dict]:
        """Get trading activity for a wallet"""
        try:
            response = requests.get(
                f"{PolymarketAPI.DATA_API}/activity",
                params={
                    "user": wallet,
                    "limit": limit,
                    "type": "TRADE"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching activity for {wallet}: {e}")
            return []
    
    @staticmethod
    def get_wallet_positions(wallet: str) -> List[Dict]:
        """Get current positions for a wallet"""
        try:
            response = requests.get(
                f"{PolymarketAPI.DATA_API}/positions",
                params={"user": wallet, "limit": 500}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching positions for {wallet}: {e}")
            return []
    
    @staticmethod
    def get_market_price(token_id: str) -> Optional[float]:
        """Get current market price for a token"""
        try:
            response = requests.get(
                f"{PolymarketAPI.CLOB_API}/price",
                params={"token_id": token_id, "side": "BUY"}
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get("price", 0))
        except Exception as e:
            logger.error(f"Error fetching price for {token_id}: {e}")
            return None


class Database:
    """SQLite database for storing trades and wallet stats"""
    
    def __init__(self, db_path="polymarket_scanner.db"):
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                wallet_address TEXT,
                market_id TEXT,
                market_title TEXT,
                token_id TEXT,
                side TEXT,
                size REAL,
                price REAL,
                usdc_value REAL,
                outcome TEXT,
                transaction_hash TEXT UNIQUE,
                created_at INTEGER
            )
        """)
        
        # Wallet stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_stats (
                wallet_address TEXT PRIMARY KEY,
                first_trade_time INTEGER,
                last_updated INTEGER,
                total_trades INTEGER,
                total_volume REAL,
                markets_traded TEXT,
                win_rate REAL,
                avg_bet_size REAL,
                largest_bet REAL,
                profitable_markets INTEGER,
                total_markets INTEGER
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                severity TEXT,
                wallet_address TEXT,
                market_title TEXT,
                market_slug TEXT,
                trade_size REAL,
                price REAL,
                side TEXT,
                outcome TEXT,
                wallet_age_hours REAL,
                wallet_total_trades INTEGER,
                wallet_win_rate REAL,
                odds_movement REAL,
                reason TEXT,
                timestamp INTEGER,
                sent_to_telegram INTEGER DEFAULT 0
            )
        """)
        
        # Market prices cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                token_id TEXT,
                price REAL,
                timestamp INTEGER,
                PRIMARY KEY (token_id, timestamp)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_wallet ON trades(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        self.conn.commit()
        logger.info("Database initialized")
    
    def save_trade(self, trade: Trade):
        """Save a trade to the database"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO trades 
                (timestamp, wallet_address, market_id, market_title, token_id, 
                 side, size, price, usdc_value, outcome, transaction_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.timestamp, trade.wallet_address, trade.market_id, 
                trade.market_title, trade.token_id, trade.side, trade.size,
                trade.price, trade.usdc_value, trade.outcome, 
                trade.transaction_hash, int(time.time())
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
    
    def save_wallet_stats(self, stats: WalletStats):
        """Save wallet statistics"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO wallet_stats 
                (wallet_address, first_trade_time, last_updated, total_trades, 
                 total_volume, markets_traded, win_rate, avg_bet_size, 
                 largest_bet, profitable_markets, total_markets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.address, stats.first_trade_time, int(time.time()),
                stats.total_trades, stats.total_volume, 
                json.dumps(list(stats.markets_traded)), stats.win_rate,
                stats.avg_bet_size, stats.largest_bet, 
                stats.profitable_markets, stats.total_markets
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving wallet stats: {e}")
    
    def get_wallet_stats(self, wallet_address: str) -> Optional[WalletStats]:
        """Get wallet statistics from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM wallet_stats WHERE wallet_address = ?
        """, (wallet_address,))
        row = cursor.fetchone()
        
        if row:
            return WalletStats(
                address=row[0],
                first_trade_time=row[1],
                total_trades=row[3],
                total_volume=row[4],
                markets_traded=set(json.loads(row[5])),
                win_rate=row[6],
                avg_bet_size=row[7],
                largest_bet=row[8],
                profitable_markets=row[9],
                total_markets=row[10]
            )
        return None
    
    def save_alert(self, alert: Alert):
        """Save an alert to the database"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO alerts 
                (alert_type, severity, wallet_address, market_title, market_slug,
                 trade_size, price, side, outcome, wallet_age_hours, 
                 wallet_total_trades, wallet_win_rate, odds_movement, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_type, alert.severity, alert.wallet_address,
                alert.market_title, alert.market_slug, alert.trade_size,
                alert.price, alert.side, alert.outcome, alert.wallet_age_hours,
                alert.wallet_total_trades, alert.wallet_win_rate,
                alert.odds_movement, alert.reason, alert.timestamp
            ))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            return None
    
    def mark_alert_sent(self, alert_id: int):
        """Mark an alert as sent to Telegram"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE alerts SET sent_to_telegram = 1 WHERE id = ?
        """, (alert_id,))
        self.conn.commit()
    
    def save_price(self, token_id: str, price: float, timestamp: int):
        """Save market price"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO market_prices (token_id, price, timestamp)
                VALUES (?, ?, ?)
            """, (token_id, price, timestamp))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving price: {e}")
    
    def get_price_history(self, token_id: str, hours: int = 24) -> List[tuple]:
        """Get price history for a token"""
        cursor = self.conn.cursor()
        cutoff = int(time.time()) - (hours * 3600)
        cursor.execute("""
            SELECT price, timestamp FROM market_prices 
            WHERE token_id = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (token_id, cutoff))
        return cursor.fetchall()
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        cursor = self.conn.cursor()
        cutoff = int(time.time()) - (hours * 3600)
        cursor.execute("""
            SELECT * FROM alerts WHERE timestamp > ? ORDER BY timestamp DESC
        """, (cutoff,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'id': row[0],
                'alert_type': row[1],
                'severity': row[2],
                'wallet_address': row[3],
                'market_title': row[4],
                'trade_size': row[6],
                'reason': row[14],
                'timestamp': row[15]
            })
        return alerts


class TelegramBot:
    """Telegram bot for sending alerts"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML"):
        """Send a message to Telegram"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def format_alert(self, alert: Alert) -> str:
        """Format an alert for Telegram"""
        severity_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }
        
        emoji = severity_emoji.get(alert.severity, "⚪")
        
        # Create shortened wallet address
        short_wallet = f"{alert.wallet_address[:6]}...{alert.wallet_address[-4:]}"
        
        message = f"""
{emoji} <b>{alert.severity} ALERT</b> - {alert.alert_type}

<b>Market:</b> {alert.market_title}
<b>Trade:</b> {alert.side} {alert.outcome} @ ${alert.price:.3f}
<b>Size:</b> ${alert.trade_size:,.2f}

<b>Wallet:</b> <code>{short_wallet}</code>
<b>Age:</b> {alert.wallet_age_hours:.1f}h | <b>Trades:</b> {alert.wallet_total_trades}
<b>Win Rate:</b> {alert.wallet_win_rate*100:.1f}% if alert.wallet_win_rate else "N/A"

<b>Reason:</b> {alert.reason}

<a href="https://polymarket.com/event/{alert.market_slug}">View Market</a>
<a href="https://polygonscan.com/address/{alert.wallet_address}">View Wallet</a>
"""
        return message.strip()


class WalletAnalyzer:
    """Analyzes wallet behavior and calculates statistics"""
    
    def __init__(self, api: PolymarketAPI, db: Database):
        self.api = api
        self.db = db
        self.wallet_cache: Dict[str, WalletStats] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, float] = {}
    
    def analyze_wallet(self, wallet_address: str, force_refresh: bool = False) -> Optional[WalletStats]:
        """Analyze a wallet's trading history and performance"""
        
        # Check cache
        if not force_refresh and wallet_address in self.wallet_cache:
            if time.time() - self.cache_timestamps.get(wallet_address, 0) < self.cache_ttl:
                return self.wallet_cache[wallet_address]
        
        # Check database
        db_stats = self.db.get_wallet_stats(wallet_address)
        if db_stats and not force_refresh:
            self.wallet_cache[wallet_address] = db_stats
            self.cache_timestamps[wallet_address] = time.time()
            return db_stats
        
        # Fetch from API
        logger.info(f"Analyzing wallet: {wallet_address}")
        activity = self.api.get_wallet_activity(wallet_address)
        
        if not activity:
            return None
        
        # Calculate statistics
        trades = [a for a in activity if a.get('type') == 'TRADE']
        
        if not trades:
            return None
        
        total_volume = sum(t.get('usdcSize', 0) for t in trades)
        markets_traded = set(t.get('conditionId') for t in trades if t.get('conditionId'))
        
        first_trade_time = min(t.get('timestamp', 0) for t in trades)
        avg_bet_size = total_volume / len(trades) if trades else 0
        largest_bet = max(t.get('usdcSize', 0) for t in trades)
        
        # Calculate win rate from positions
        positions = self.api.get_wallet_positions(wallet_address)
        profitable = sum(1 for p in positions if p.get('cashPnl', 0) > 0)
        total_positions = len(positions)
        win_rate = profitable / total_positions if total_positions > 0 else None
        
        stats = WalletStats(
            address=wallet_address,
            first_trade_time=first_trade_time,
            total_trades=len(trades),
            total_volume=total_volume,
            markets_traded=markets_traded,
            win_rate=win_rate,
            avg_bet_size=avg_bet_size,
            largest_bet=largest_bet,
            profitable_markets=profitable,
            total_markets=total_positions
        )
        
        # Cache and save to database
        self.wallet_cache[wallet_address] = stats
        self.cache_timestamps[wallet_address] = time.time()
        self.db.save_wallet_stats(stats)
        
        return stats
    
    def is_new_wallet(self, wallet_address: str, hours_threshold: int = 168) -> tuple[bool, Optional[float]]:
        """
        Check if wallet is new (created within threshold hours)
        Returns (is_new, age_in_hours)
        """
        stats = self.analyze_wallet(wallet_address)
        
        if not stats or not stats.first_trade_time:
            return True, None  # Unknown, treat as new
        
        age_seconds = time.time() - stats.first_trade_time
        age_hours = age_seconds / 3600
        
        is_new = age_hours < hours_threshold
        return is_new, age_hours


class AlertGenerator:
    """Generates alerts based on trading patterns"""
    
    def __init__(self, db: Database, wallet_analyzer: WalletAnalyzer, telegram_bot: TelegramBot):
        self.db = db
        self.wallet_analyzer = wallet_analyzer
        self.telegram = telegram_bot
        
        # Alert thresholds - use config if available
        if config:
            self.LARGE_BET = config.LARGE_BET_THRESHOLD
            self.VERY_LARGE_BET = config.VERY_LARGE_BET_THRESHOLD
            self.HUGE_BET = config.HUGE_BET_THRESHOLD
            self.NEW_WALLET_HOURS = config.NEW_WALLET_HOURS
            self.VERY_NEW_WALLET_HOURS = config.VERY_NEW_WALLET_HOURS
            self.HIGH_WIN_RATE = config.HIGH_WIN_RATE_THRESHOLD
            self.LOW_TRADE_COUNT = config.LOW_TRADE_COUNT_THRESHOLD
            self.SIGNIFICANT_ODDS_MOVE = config.SIGNIFICANT_ODDS_MOVE
            self.MIN_SEVERITY = config.MIN_ALERT_SEVERITY
        else:
            # Defaults if no config
            self.LARGE_BET = 5000
            self.VERY_LARGE_BET = 10000
            self.HUGE_BET = 50000
            self.NEW_WALLET_HOURS = 168
            self.VERY_NEW_WALLET_HOURS = 24
            self.HIGH_WIN_RATE = 0.65
            self.LOW_TRADE_COUNT = 10
            self.SIGNIFICANT_ODDS_MOVE = 0.10
            self.MIN_SEVERITY = "MEDIUM"
    
    def generate_alert(self, trade: Trade, market_slug: str) -> Optional[Alert]:
        """Generate an alert if trade meets criteria"""
        
        # Analyze wallet
        wallet_stats = self.wallet_analyzer.analyze_wallet(trade.wallet_address)
        is_new, age_hours = self.wallet_analyzer.is_new_wallet(trade.wallet_address)
        
        alert_type = None
        severity = "LOW"
        reason = ""
        
        # Check bet size thresholds
        if trade.usdc_value >= self.HUGE_BET:
            alert_type = "HUGE_BET"
            severity = "CRITICAL"
            reason = f"Huge ${trade.usdc_value:,.0f} bet"
        elif trade.usdc_value >= self.VERY_LARGE_BET:
            alert_type = "VERY_LARGE_BET"
            severity = "HIGH"
            reason = f"Very large ${trade.usdc_value:,.0f} bet"
        elif trade.usdc_value >= self.LARGE_BET:
            alert_type = "LARGE_BET"
            severity = "MEDIUM"
            reason = f"Large ${trade.usdc_value:,.0f} bet"
        
        if not alert_type:
            return None
        
        # Enhance alert based on wallet characteristics
        additional_flags = []
        
        if wallet_stats:
            # New wallet with large bet
            if is_new and age_hours and age_hours < self.NEW_WALLET_HOURS:
                additional_flags.append(f"New wallet ({age_hours:.0f}h old)")
                if age_hours < self.VERY_NEW_WALLET_HOURS:
                    severity = "CRITICAL"
            
            # Low trade count (possible insider)
            if wallet_stats.total_trades < self.LOW_TRADE_COUNT:
                additional_flags.append(f"Only {wallet_stats.total_trades} trades")
                if severity == "MEDIUM":
                    severity = "HIGH"
            
            # High win rate
            if wallet_stats.win_rate and wallet_stats.win_rate > self.HIGH_WIN_RATE:
                additional_flags.append(f"High win rate ({wallet_stats.win_rate*100:.0f}%)")
                if severity == "MEDIUM":
                    severity = "HIGH"
            
            # Single market focus
            if len(wallet_stats.markets_traded) == 1:
                additional_flags.append("Only trades this market")
                severity = "CRITICAL"
        
        if additional_flags:
            reason += " | " + ", ".join(additional_flags)
        
        # Create alert
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            wallet_address=trade.wallet_address,
            market_title=trade.market_title,
            market_slug=market_slug,
            trade_size=trade.usdc_value,
            price=trade.price,
            side=trade.side,
            outcome=trade.outcome,
            wallet_age_hours=age_hours,
            wallet_total_trades=wallet_stats.total_trades if wallet_stats else 0,
            wallet_win_rate=wallet_stats.win_rate if wallet_stats else None,
            odds_movement=None,  # Can be calculated separately
            reason=reason,
            timestamp=trade.timestamp
        )
        
        return alert
    
    def send_alert(self, alert: Alert):
        """Save alert and send to Telegram"""
        
        # Check if alert meets minimum severity threshold
        severity_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        min_level = severity_levels.get(self.MIN_SEVERITY, 1)
        alert_level = severity_levels.get(alert.severity, 0)
        
        if alert_level < min_level:
            logger.debug(f"Alert below minimum severity ({alert.severity} < {self.MIN_SEVERITY})")
            return
        
        alert_id = self.db.save_alert(alert)
        
        if alert_id and self.telegram:
            message = self.telegram.format_alert(alert)
            success = self.telegram.send_message(message)
            
            if success:
                self.db.mark_alert_sent(alert_id)
                logger.info(f"Alert sent: {alert.severity} - {alert.reason}")
            else:
                logger.error(f"Failed to send alert {alert_id}")
        elif alert_id:
            logger.info(f"Alert saved (Telegram disabled): {alert.severity} - {alert.reason}")


class PolymarketScanner:
    """Main scanner class that orchestrates everything"""
    
    def __init__(self, telegram_bot_token: str = None, telegram_chat_id: str = None):
        self.api = PolymarketAPI()
        self.db = Database()
        
        self.telegram = None
        if telegram_bot_token and telegram_chat_id:
            self.telegram = TelegramBot(telegram_bot_token, telegram_chat_id)
        
        self.wallet_analyzer = WalletAnalyzer(self.api, self.db)
        self.alert_generator = AlertGenerator(self.db, self.wallet_analyzer, self.telegram)
        
        self.tracked_markets: Dict[str, Dict] = {}
        self.processed_trades: Set[str] = set()
        
    async def initialize(self):
        """Initialize scanner with active markets"""
        logger.info("Initializing scanner...")
        
        markets = self.api.get_active_markets(limit=100)
        for market in markets:
            slug = market.get('slug')
            if slug:
                self.tracked_markets[slug] = market
        
        logger.info(f"Tracking {len(self.tracked_markets)} markets")
    
    def process_trade(self, trade_data: Dict, market_slug: str = None):
        """Process a single trade and generate alerts if needed"""
        
        # Extract trade information
        tx_hash = trade_data.get('transactionHash')
        if not tx_hash or tx_hash in self.processed_trades:
            return
        
        self.processed_trades.add(tx_hash)
        
        trade = Trade(
            timestamp=trade_data.get('timestamp', int(time.time())),
            wallet_address=trade_data.get('proxyWallet', ''),
            market_id=trade_data.get('conditionId', ''),
            market_title=trade_data.get('title', 'Unknown Market'),
            token_id=trade_data.get('asset', ''),
            side=trade_data.get('side', ''),
            size=trade_data.get('size', 0),
            price=trade_data.get('price', 0),
            usdc_value=trade_data.get('usdcSize', 0),
            outcome=trade_data.get('outcome', ''),
            transaction_hash=tx_hash
        )
        
        # Save trade to database
        self.db.save_trade(trade)
        
        # Generate and send alert if criteria met
        alert = self.alert_generator.generate_alert(
            trade, 
            market_slug or trade_data.get('slug', '')
        )
        
        if alert:
            self.alert_generator.send_alert(alert)
    
    async def poll_recent_trades(self, interval: int = 60):
        """Poll for recent trades across all markets"""
        logger.info("Starting trade polling...")
        
        while True:
            try:
                # Get recent trades for each tracked market
                for slug, market in list(self.tracked_markets.items())[:50]:  # Limit to avoid rate limits
                    condition_id = market.get('conditionId')
                    if not condition_id:
                        continue
                    
                    # Get trades for this market
                    response = requests.get(
                        f"{self.api.DATA_API}/trades",
                        params={
                            "market": condition_id,
                            "limit": 20
                        }
                    )
                    
                    if response.status_code == 200:
                        trades = response.json()
                        for trade in trades:
                            self.process_trade(trade, slug)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                
                # Wait before next poll
                logger.info(f"Waiting {interval}s before next poll...")
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(interval)
    
    def analyze_historical_performance(self, days: int = 30, min_trades: int = 10):
        """
        Analyze historical data to find high-performing traders
        """
        logger.info(f"Analyzing historical performance for last {days} days...")
        
        cutoff = int(time.time()) - (days * 86400)
        cursor = self.db.conn.cursor()
        
        # Get wallets with significant activity
        cursor.execute("""
            SELECT wallet_address, COUNT(*) as trade_count, SUM(usdc_value) as total_volume
            FROM trades
            WHERE timestamp > ?
            GROUP BY wallet_address
            HAVING trade_count >= ?
            ORDER BY total_volume DESC
            LIMIT 100
        """, (cutoff, min_trades))
        
        high_performers = []
        
        for row in cursor.fetchall():
            wallet, trade_count, volume = row
            
            # Analyze this wallet in detail
            stats = self.wallet_analyzer.analyze_wallet(wallet, force_refresh=True)
            
            if stats and stats.win_rate and stats.win_rate > 0.6:
                high_performers.append({
                    'wallet': wallet,
                    'trades': trade_count,
                    'volume': volume,
                    'win_rate': stats.win_rate,
                    'avg_bet': stats.avg_bet_size,
                    'markets': len(stats.markets_traded)
                })
                
                logger.info(
                    f"High performer: {wallet[:8]}... | "
                    f"Win rate: {stats.win_rate*100:.1f}% | "
                    f"Volume: ${volume:,.0f}"
                )
        
        return high_performers
    
    async def run(self, analyze_history: bool = True):
        """Main run loop"""
        await self.initialize()
        
        if self.telegram:
            self.telegram.send_message(
                "🚀 <b>Polymarket Scanner Started</b>\n\n"
                f"Tracking {len(self.tracked_markets)} active markets\n"
                "Monitoring for insider trading patterns..."
            )
        
        # Analyze historical data first
        if analyze_history:
            high_performers = self.analyze_historical_performance(days=7)
            
            if high_performers and self.telegram:
                message = "📊 <b>Top Performers (7 days)</b>\n\n"
                for i, perf in enumerate(high_performers[:10], 1):
                    message += (
                        f"{i}. <code>{perf['wallet'][:10]}...</code>\n"
                        f"   Win: {perf['win_rate']*100:.0f}% | "
                        f"Vol: ${perf['volume']:,.0f} | "
                        f"Trades: {perf['trades']}\n\n"
                    )
                self.telegram.send_message(message)
        
        # Start polling for new trades
        await self.poll_recent_trades(interval=30)


async def main():
    """Main entry point"""
    
    # Validate configuration
    if config and not config.validate_config():
        logger.error("Configuration validation failed")
        return
    
    # Configuration - from config.py or environment
    if config and config.ENABLE_TELEGRAM:
        TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
        TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID
    else:
        TELEGRAM_BOT_TOKEN = None
        TELEGRAM_CHAT_ID = None
        logger.warning("Telegram notifications disabled")
    
    # Create and run scanner
    scanner = PolymarketScanner(
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID
    )
    
    # Determine if we should analyze history
    analyze_history = config.ANALYZE_HISTORY_ON_START if config else True
    
    await scanner.run(analyze_history=analyze_history)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
