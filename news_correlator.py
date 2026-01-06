"""
News Aggregator & Market Correlator
Detects breaking news and correlates with Polymarket activity
"""

import asyncio
import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import requests
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Represents a news article or tweet"""
    source: str  # "twitter", "rss", "newsapi"
    title: str
    content: str
    url: str
    published_at: int
    author: Optional[str] = None
    keywords: List[str] = None


@dataclass
class MarketNewsMatch:
    """Match between news and a Polymarket market"""
    news: NewsItem
    market_slug: str
    market_title: str
    market_id: str
    confidence: float  # 0-1 relevance score
    related_tokens: List[str]
    current_price: float
    price_1h_ago: Optional[float]
    recent_volume: float
    top_wallet_activity: List[Dict]


class NewsAggregator:
    """Aggregates news from multiple sources"""
    
    def __init__(self, newsapi_key: Optional[str] = None, twitter_bearer_token: Optional[str] = None):
        self.newsapi_key = newsapi_key
        self.twitter_bearer = twitter_bearer_token
        self.seen_urls: Set[str] = set()
        
    def get_breaking_news(self, sources: List[str] = None, keywords: List[str] = None) -> List[NewsItem]:
        """Get breaking news from multiple sources"""
        news_items = []
        
        # NewsAPI
        if self.newsapi_key:
            news_items.extend(self._fetch_newsapi(keywords))
        
        # RSS Feeds (free, no API key needed)
        news_items.extend(self._fetch_rss_feeds())
        
        # Twitter/X (requires bearer token)
        if self.twitter_bearer:
            news_items.extend(self._fetch_twitter(keywords))
        
        # Filter out duplicates
        unique_news = []
        for item in news_items:
            if item.url not in self.seen_urls:
                self.seen_urls.add(item.url)
                unique_news.append(item)
        
        return unique_news
    
    def _fetch_newsapi(self, keywords: List[str] = None) -> List[NewsItem]:
        """Fetch from NewsAPI.org"""
        if not self.newsapi_key:
            return []
        
        try:
            query = " OR ".join(keywords) if keywords else "breaking"
            
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 20,
                    "apiKey": self.newsapi_key
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"NewsAPI error: {response.status_code}")
                return []
            
            data = response.json()
            news_items = []
            
            for article in data.get("articles", []):
                # Parse published date
                published_str = article.get("publishedAt", "")
                try:
                    published_dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    published_ts = int(published_dt.timestamp())
                except:
                    published_ts = int(time.time())
                
                news_items.append(NewsItem(
                    source="newsapi",
                    title=article.get("title", ""),
                    content=article.get("description", ""),
                    url=article.get("url", ""),
                    published_at=published_ts,
                    author=article.get("author"),
                    keywords=self._extract_keywords(article.get("title", ""))
                ))
            
            logger.info(f"Fetched {len(news_items)} articles from NewsAPI")
            return news_items
            
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []
    
    def _fetch_rss_feeds(self) -> List[NewsItem]:
        """Fetch from RSS feeds (free sources)"""
        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser not installed. Install with: pip install feedparser")
            return []
        
        feeds = [
            "http://feeds.bbci.co.uk/news/rss.xml",  # BBC
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",  # NYT
            "https://feeds.reuters.com/reuters/topNews",  # Reuters
            "https://www.theguardian.com/world/rss",  # Guardian
        ]
        
        news_items = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Latest 10 per feed
                    # Parse published date
                    published_ts = int(time.time())
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_ts = int(time.mktime(entry.published_parsed))
                    
                    news_items.append(NewsItem(
                        source="rss",
                        title=entry.get("title", ""),
                        content=entry.get("summary", ""),
                        url=entry.get("link", ""),
                        published_at=published_ts,
                        keywords=self._extract_keywords(entry.get("title", ""))
                    ))
                
            except Exception as e:
                logger.error(f"RSS feed error for {feed_url}: {e}")
                continue
        
        logger.info(f"Fetched {len(news_items)} articles from RSS feeds")
        return news_items
    
    def _fetch_twitter(self, keywords: List[str] = None) -> List[NewsItem]:
        """Fetch from Twitter/X"""
        if not self.twitter_bearer:
            return []
        
        # Twitter API v2 implementation
        # Requires Twitter API access (paid or approved developer account)
        # Placeholder for now
        logger.info("Twitter integration requires API access")
        return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction (can be improved with NLP)
        important_words = []
        
        # Common keywords in prediction markets
        patterns = [
            r'\b(Trump|Biden|Harris|election|president)\b',
            r'\b(Bitcoin|BTC|crypto|Ethereum|ETH)\b',
            r'\b(Fed|inflation|rate|economy|recession)\b',
            r'\b(AI|GPT|OpenAI|Google|Microsoft)\b',
            r'\b(war|conflict|Ukraine|Russia|China)\b',
            r'\b(COVID|pandemic|vaccine)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            important_words.extend(matches)
        
        return list(set(important_words))


class MarketMatcher:
    """Matches news to Polymarket markets using semantic similarity"""
    
    def __init__(self, polymarket_api):
        self.api = polymarket_api
        self.markets_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = 0
    
    def find_matching_markets(self, news_item: NewsItem, min_confidence: float = 0.6) -> List[Dict]:
        """Find Polymarket markets related to news"""
        
        # Refresh market cache if needed
        if time.time() - self.last_cache_update > self.cache_ttl:
            self._update_markets_cache()
        
        matches = []
        
        # Combine title and content for matching
        news_text = f"{news_item.title} {news_item.content}".lower()
        
        for slug, market in self.markets_cache.items():
            market_text = f"{market.get('question', '')} {market.get('description', '')}".lower()
            
            # Calculate relevance score
            confidence = self._calculate_relevance(news_text, market_text, news_item.keywords)
            
            if confidence >= min_confidence:
                matches.append({
                    "slug": slug,
                    "market": market,
                    "confidence": confidence
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches[:5]  # Top 5 matches
    
    def _update_markets_cache(self):
        """Update cache of active markets"""
        try:
            markets = self.api.get_active_markets(limit=100)
            self.markets_cache = {m.get("slug"): m for m in markets if m.get("slug")}
            self.last_cache_update = time.time()
            logger.info(f"Updated markets cache: {len(self.markets_cache)} markets")
        except Exception as e:
            logger.error(f"Error updating markets cache: {e}")
    
    def _calculate_relevance(self, news_text: str, market_text: str, keywords: List[str]) -> float:
        """Calculate relevance score between news and market (0-1)"""
        score = 0.0
        
        # Keyword matching (40% weight)
        if keywords:
            keywords_lower = [k.lower() for k in keywords]
            keyword_matches = sum(1 for k in keywords_lower if k in market_text)
            keyword_score = min(keyword_matches / len(keywords), 1.0) * 0.4
            score += keyword_score
        
        # Word overlap (30% weight)
        news_words = set(re.findall(r'\b\w{4,}\b', news_text))
        market_words = set(re.findall(r'\b\w{4,}\b', market_text))
        
        if news_words and market_words:
            overlap = len(news_words & market_words)
            overlap_score = min(overlap / 10, 1.0) * 0.3
            score += overlap_score
        
        # Entity matching (30% weight)
        # Check for specific named entities
        entities = self._extract_entities(news_text)
        entity_matches = sum(1 for e in entities if e in market_text)
        if entities:
            entity_score = min(entity_matches / len(entities), 1.0) * 0.3
            score += entity_score
        
        return score
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (people, organizations, etc.)"""
        # Simple entity extraction (can be improved with NLP library)
        entities = []
        
        # Capitalized words (potential names/orgs)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(words)
        
        return list(set(entities))


class WalletActivityAnalyzer:
    """Analyzes if top wallets are trading on matched markets"""
    
    def __init__(self, db, api):
        self.db = db
        self.api = api
    
    def get_recent_activity(self, market_id: str, hours: int = 1) -> List[Dict]:
        """Get recent trading activity on a market"""
        try:
            cutoff = int(time.time()) - (hours * 3600)
            
            # Query trades from database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT t.*, w.win_rate, w.total_volume
                FROM trades t
                LEFT JOIN wallet_stats w ON t.wallet_address = w.wallet_address
                WHERE t.market_id = ? AND t.timestamp > ?
                ORDER BY t.timestamp DESC
                LIMIT 50
            """, (market_id, cutoff))
            
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    "wallet": row[2],
                    "side": row[6],
                    "size": row[7],
                    "usdc_value": row[9],
                    "timestamp": row[1],
                    "win_rate": row[13] if len(row) > 13 else None,
                    "total_volume": row[14] if len(row) > 14 else None
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def check_top_wallet_positions(self, market_id: str, top_wallets: List[str]) -> List[Dict]:
        """Check if any top-performing wallets have positions"""
        positions = []
        
        for wallet in top_wallets:
            try:
                wallet_positions = self.api.get_wallet_positions(wallet)
                
                for pos in wallet_positions:
                    if pos.get("conditionId") == market_id:
                        positions.append({
                            "wallet": wallet,
                            "outcome": pos.get("outcome"),
                            "size": pos.get("size"),
                            "value": pos.get("currentValue"),
                            "pnl": pos.get("cashPnl")
                        })
                
            except Exception as e:
                logger.error(f"Error checking wallet {wallet}: {e}")
                continue
        
        return positions


class NewsMarketCorrelator:
    """Main coordinator for news-to-market-to-wallet correlation"""
    
    def __init__(self, polymarket_scanner, newsapi_key: str = None, twitter_bearer: str = None):
        self.scanner = polymarket_scanner
        self.news_aggregator = NewsAggregator(newsapi_key, twitter_bearer)
        self.market_matcher = MarketMatcher(self.scanner.api)
        self.wallet_analyzer = WalletActivityAnalyzer(self.scanner.db, self.scanner.api)
        
        self.processed_news: Set[str] = set()
        
    async def monitor_news_correlation(self, check_interval: int = 300):
        """Monitor news and correlate with market activity"""
        logger.info("Starting news-market correlation monitoring...")
        
        while True:
            try:
                # Fetch breaking news
                news_items = self.news_aggregator.get_breaking_news(
                    keywords=["Trump", "Biden", "Bitcoin", "Fed", "AI", "election", "war"]
                )
                
                logger.info(f"Found {len(news_items)} news items")
                
                for news in news_items:
                    if news.url in self.processed_news:
                        continue
                    
                    self.processed_news.add(news.url)
                    
                    # Find matching markets
                    matches = self.market_matcher.find_matching_markets(news, min_confidence=0.7)
                    
                    if not matches:
                        continue
                    
                    logger.info(f"News matched {len(matches)} markets: {news.title[:50]}")
                    
                    # Check wallet activity for each match
                    for match in matches:
                        await self._analyze_market_reaction(news, match)
                
                # Clean up old processed news (keep last 1000)
                if len(self.processed_news) > 1000:
                    self.processed_news = set(list(self.processed_news)[-1000:])
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in news correlation loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def _analyze_market_reaction(self, news: NewsItem, match: Dict):
        """Analyze if smart wallets are reacting to news"""
        market = match["market"]
        market_id = market.get("conditionId")
        market_slug = match["slug"]
        
        # Get recent trades
        recent_trades = self.wallet_analyzer.get_recent_activity(market_id, hours=1)
        
        if not recent_trades:
            return
        
        # Get top wallets from scanner
        cursor = self.scanner.db.conn.cursor()
        cursor.execute("""
            SELECT wallet_address FROM wallet_stats
            WHERE win_rate > 0.65 AND total_trades > 10
            ORDER BY win_rate DESC
            LIMIT 20
        """)
        top_wallets = [row[0] for row in cursor.fetchall()]
        
        # Check if top wallets are trading
        top_wallet_trades = [t for t in recent_trades if t["wallet"] in top_wallets]
        
        if top_wallet_trades or len(recent_trades) >= 5:
            # Significant activity detected!
            await self._send_news_alert(news, match, recent_trades, top_wallet_trades)
    
    async def _send_news_alert(self, news: NewsItem, match: Dict, all_trades: List[Dict], top_trades: List[Dict]):
        """Send alert about news-market correlation"""
        market = match["market"]
        
        total_volume = sum(t["usdc_value"] for t in all_trades)
        top_wallet_volume = sum(t["usdc_value"] for t in top_trades)
        
        # Determine alert type
        if top_trades:
            alert_type = "🎯 SMART MONEY MOVING"
            severity = "CRITICAL"
        elif len(all_trades) >= 10:
            alert_type = "📈 HIGH ACTIVITY"
            severity = "HIGH"
        else:
            alert_type = "📰 NEWS MATCHED"
            severity = "MEDIUM"
        
        # Build message
        message = f"""
{alert_type}

<b>📰 Breaking News:</b>
{news.title[:100]}

<b>💹 Related Market:</b>
{market.get('question', 'Unknown')[:100]}
<b>Match Confidence:</b> {match['confidence']*100:.0f}%

<b>⚡ Recent Activity (1h):</b>
• Total Trades: {len(all_trades)}
• Volume: ${total_volume:,.0f}
• Smart Money: {len(top_trades)} trades (${top_wallet_volume:,.0f})

<b>🔗 Links:</b>
<a href="{news.url}">Read News</a> | <a href="https://polymarket.com/event/{match['slug']}">View Market</a>

<i>Posted {int((time.time() - news.published_at)/60)}m ago</i>
"""
        
        # Send via Telegram
        if self.scanner.telegram:
            self.scanner.telegram.send_message(message.strip())
            logger.info(f"Sent news correlation alert: {news.title[:50]}")


# Integration with main scanner
async def run_with_news_correlation(scanner, newsapi_key: str = None, twitter_bearer: str = None):
    """Run scanner with news correlation enabled"""
    
    # Create correlator
    correlator = NewsMarketCorrelator(scanner, newsapi_key, twitter_bearer)
    
    # Run both scanner and news monitor concurrently
    await asyncio.gather(
        scanner.poll_recent_trades(interval=30),  # Regular scanning
        correlator.monitor_news_correlation(check_interval=300)  # News every 5 min
    )
