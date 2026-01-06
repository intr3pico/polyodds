"""
Social Media Profile Monitor
Tracks specific Twitter/X and Truth Social accounts and correlates with markets
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
class SocialPost:
    """Represents a social media post"""
    platform: str  # "twitter" or "truthsocial"
    username: str
    content: str
    post_id: str
    url: str
    posted_at: int
    engagement: Dict  # likes, retweets, etc.
    keywords: List[str]


class TwitterMonitor:
    """Monitor specific Twitter/X accounts"""
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        self.user_cache = {}  # Cache user IDs
        
    def get_user_tweets(self, username: str, since_hours: int = 1, max_results: int = 10) -> List[SocialPost]:
        """Get recent tweets from a user"""
        
        if not self.bearer_token:
            logger.warning("Twitter bearer token not set")
            return []
        
        try:
            # Get user ID (cached)
            user_id = self._get_user_id(username)
            if not user_id:
                return []
            
            # Calculate since timestamp
            since_timestamp = datetime.utcnow() - timedelta(hours=since_hours)
            since_iso = since_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Fetch tweets
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            params = {
                "max_results": min(max_results, 100),
                "start_time": since_iso,
                "tweet.fields": "created_at,public_metrics",
                "expansions": "author_id"
            }
            
            response = requests.get(
                f"{self.base_url}/users/{user_id}/tweets",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                logger.warning("Twitter rate limit hit")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for tweet in data.get("data", []):
                # Parse timestamp
                created_str = tweet.get("created_at", "")
                try:
                    created_dt = datetime.strptime(created_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    created_ts = int(created_dt.timestamp())
                except:
                    created_ts = int(time.time())
                
                metrics = tweet.get("public_metrics", {})
                
                posts.append(SocialPost(
                    platform="twitter",
                    username=username,
                    content=tweet.get("text", ""),
                    post_id=tweet.get("id", ""),
                    url=f"https://twitter.com/{username}/status/{tweet.get('id')}",
                    posted_at=created_ts,
                    engagement={
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "quotes": metrics.get("quote_count", 0)
                    },
                    keywords=self._extract_keywords(tweet.get("text", ""))
                ))
            
            logger.info(f"Fetched {len(posts)} tweets from @{username}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Twitter posts for @{username}: {e}")
            return []
    
    def _get_user_id(self, username: str) -> Optional[str]:
        """Get Twitter user ID from username"""
        
        if username in self.user_cache:
            return self.user_cache[username]
        
        try:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            response = requests.get(
                f"{self.base_url}/users/by/username/{username}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            user_id = response.json().get("data", {}).get("id")
            if user_id:
                self.user_cache[username] = user_id
            
            return user_id
            
        except Exception as e:
            logger.error(f"Error getting user ID for @{username}: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from tweet"""
        keywords = []
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        keywords.extend(hashtags)
        
        # Extract mentions
        mentions = re.findall(r'@(\w+)', text)
        keywords.extend(mentions)
        
        # Common market-relevant terms
        patterns = [
            r'\b(tariff|trade|China|Mexico|border)\b',
            r'\b(Fed|inflation|economy|recession)\b',
            r'\b(NATO|Ukraine|Russia|war)\b',
            r'\b(crypto|Bitcoin|regulation)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        return list(set([k.lower() for k in keywords]))


class TruthSocialMonitor:
    """Monitor Truth Social accounts (Trump's platform)"""
    
    def __init__(self, username: str = "realDonaldTrump"):
        self.base_url = "https://truthsocial.com"
        self.username = username
        
        # Truth Social doesn't have a public API, so we'll use web scraping
        # This is a simplified version - real implementation would need:
        # 1. Browser automation (Selenium/Playwright)
        # 2. Session management
        # 3. CAPTCHA handling
        
    def get_user_posts(self, since_hours: int = 1, max_results: int = 10) -> List[SocialPost]:
        """
        Get recent Truth Social posts
        
        Note: Truth Social doesn't have a public API. Options:
        1. Use RSSHub: https://docs.rsshub.app/en/social-media.html#truth-social
        2. Use browser automation (Selenium)
        3. Use third-party scraping services
        4. Monitor via RSS aggregators
        """
        
        logger.warning("Truth Social monitoring requires browser automation or RSSHub")
        
        # Try RSSHub if available
        try:
            posts = self._fetch_via_rsshub(since_hours, max_results)
            if posts:
                return posts
        except Exception as e:
            logger.error(f"RSSHub fetch failed: {e}")
        
        # Fallback: Try direct scraping (simplified)
        try:
            posts = self._scrape_profile(since_hours, max_results)
            return posts
        except Exception as e:
            logger.error(f"Truth Social scraping failed: {e}")
            return []
    
    def _fetch_via_rsshub(self, since_hours: int, max_results: int) -> List[SocialPost]:
        """Fetch via RSSHub (if you have it running)"""
        
        # RSSHub format: https://rsshub.app/truthsocial/user/{username}
        # You'd need to run RSSHub locally or use a public instance
        
        rsshub_url = f"https://rsshub.app/truthsocial/user/{self.username}"
        
        try:
            import feedparser
            feed = feedparser.parse(rsshub_url)
            
            posts = []
            cutoff = time.time() - (since_hours * 3600)
            
            for entry in feed.entries[:max_results]:
                # Parse timestamp
                published_ts = int(time.time())
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_ts = int(time.mktime(entry.published_parsed))
                
                if published_ts < cutoff:
                    continue
                
                posts.append(SocialPost(
                    platform="truthsocial",
                    username=self.username,
                    content=entry.get("title", "") + " " + entry.get("summary", ""),
                    post_id=entry.get("id", ""),
                    url=entry.get("link", ""),
                    posted_at=published_ts,
                    engagement={},
                    keywords=self._extract_keywords(entry.get("title", ""))
                ))
            
            logger.info(f"Fetched {len(posts)} Truth Social posts via RSSHub")
            return posts
            
        except Exception as e:
            logger.error(f"RSSHub error: {e}")
            return []
    
    def _scrape_profile(self, since_hours: int, max_results: int) -> List[SocialPost]:
        """
        Scrape Truth Social profile (requires browser automation)
        
        This is a placeholder - real implementation would use:
        - Selenium/Playwright for browser automation
        - Proxy rotation to avoid rate limits
        - Session management
        """
        
        logger.warning("Direct Truth Social scraping not implemented")
        logger.info("Consider using: 1) RSSHub, 2) Nitter-like proxy, or 3) Manual feed")
        
        return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from post"""
        keywords = []
        
        # Common Trump/political terms
        patterns = [
            r'\b(China|Mexico|Canada|tariff|trade)\b',
            r'\b(border|wall|immigration)\b',
            r'\b(NATO|Ukraine|Putin)\b',
            r'\b(election|vote|fraud|rigged)\b',
            r'\b(fake news|media|corrupt)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        return list(set([k.lower() for k in keywords]))


class SocialMediaCorrelator:
    """Correlate social media posts with Polymarket activity"""
    
    def __init__(self, scanner, market_matcher, wallet_analyzer):
        self.scanner = scanner
        self.market_matcher = market_matcher
        self.wallet_analyzer = wallet_analyzer
        
        # Initialize monitors
        self.twitter = None
        self.truthsocial = None
        
        self.processed_posts: Set[str] = set()
        
    def setup_monitors(self, twitter_bearer: Optional[str] = None, 
                      monitored_accounts: List[str] = None):
        """Setup social media monitors"""
        
        if twitter_bearer:
            self.twitter = TwitterMonitor(twitter_bearer)
            logger.info("Twitter monitor enabled")
        
        # Truth Social (always try, falls back gracefully)
        self.truthsocial = TruthSocialMonitor()
        
        self.monitored_accounts = monitored_accounts or [
            "realDonaldTrump",  # Trump's Twitter
            "JoeBiden",         # Biden
            "elonmusk",         # Musk
            "federalreserve",   # Fed
            "VitalikButerin",   # Vitalik (crypto)
        ]
        
        logger.info(f"Monitoring {len(self.monitored_accounts)} accounts")
    
    async def monitor_social_activity(self, check_interval: int = 180):
        """Monitor social media posts and correlate with markets"""
        
        logger.info("Starting social media monitoring...")
        
        while True:
            try:
                all_posts = []
                
                # Fetch from Twitter
                if self.twitter:
                    for account in self.monitored_accounts:
                        posts = self.twitter.get_user_tweets(
                            account, 
                            since_hours=1,
                            max_results=10
                        )
                        all_posts.extend(posts)
                        
                        # Rate limit protection
                        await asyncio.sleep(1)
                
                # Fetch from Truth Social (Trump only)
                if self.truthsocial and "realDonaldTrump" in self.monitored_accounts:
                    trump_posts = self.truthsocial.get_user_posts(since_hours=1)
                    all_posts.extend(trump_posts)
                
                logger.info(f"Found {len(all_posts)} recent posts")
                
                # Process each post
                for post in all_posts:
                    if post.post_id in self.processed_posts:
                        continue
                    
                    self.processed_posts.add(post.post_id)
                    
                    # Find matching markets
                    matches = self._find_matching_markets(post)
                    
                    if matches:
                        logger.info(f"Post from @{post.username} matched {len(matches)} markets")
                        
                        for match in matches:
                            await self._analyze_market_reaction(post, match)
                
                # Cleanup old processed posts
                if len(self.processed_posts) > 1000:
                    self.processed_posts = set(list(self.processed_posts)[-1000:])
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in social monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    def _find_matching_markets(self, post: SocialPost) -> List[Dict]:
        """Find markets related to social media post"""
        
        # Update markets cache
        if time.time() - self.market_matcher.last_cache_update > 300:
            self.market_matcher._update_markets_cache()
        
        matches = []
        post_text = post.content.lower()
        
        for slug, market in self.market_matcher.markets_cache.items():
            market_text = f"{market.get('question', '')} {market.get('description', '')}".lower()
            
            # Calculate relevance
            confidence = self._calculate_relevance(
                post_text, 
                market_text, 
                post.keywords,
                post.username
            )
            
            if confidence >= 0.6:  # Lower threshold for influential accounts
                matches.append({
                    "slug": slug,
                    "market": market,
                    "confidence": confidence
                })
        
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:5]
    
    def _calculate_relevance(self, post_text: str, market_text: str, 
                            keywords: List[str], username: str) -> float:
        """Calculate relevance score"""
        
        score = 0.0
        
        # Keyword matching (40%)
        if keywords:
            keyword_matches = sum(1 for k in keywords if k in market_text)
            score += min(keyword_matches / max(len(keywords), 1), 1.0) * 0.4
        
        # Word overlap (30%)
        post_words = set(re.findall(r'\b\w{4,}\b', post_text))
        market_words = set(re.findall(r'\b\w{4,}\b', market_text))
        
        if post_words and market_words:
            overlap = len(post_words & market_words)
            score += min(overlap / 10, 1.0) * 0.3
        
        # Username bonus (30%) - boost for influential accounts
        influential = {
            "realDonaldTrump": 0.3,
            "JoeBiden": 0.3,
            "elonmusk": 0.25,
            "federalreserve": 0.2,
            "VitalikButerin": 0.15
        }
        
        if username.lower() in [u.lower() for u in influential.keys()]:
            score += influential.get(username, 0.1)
        
        return min(score, 1.0)
    
    async def _analyze_market_reaction(self, post: SocialPost, match: Dict):
        """Check if market is reacting to social media post"""
        
        market = match["market"]
        market_id = market.get("conditionId")
        
        # Get recent trades (last 30 minutes - shorter window for social)
        recent_trades = self.wallet_analyzer.get_recent_activity(market_id, hours=0.5)
        
        if not recent_trades:
            # Still alert if high confidence match from influential account
            if match["confidence"] > 0.8 and post.username.lower() in ["realdonaldtrump", "joebiden"]:
                await self._send_social_alert(post, match, [], [])
            return
        
        # Get top wallets
        cursor = self.scanner.db.conn.cursor()
        cursor.execute("""
            SELECT wallet_address FROM wallet_stats
            WHERE win_rate > 0.65 AND total_trades > 10
            ORDER BY win_rate DESC
            LIMIT 20
        """)
        top_wallets = [row[0] for row in cursor.fetchall()]
        
        # Check smart wallet activity
        top_wallet_trades = [t for t in recent_trades if t["wallet"] in top_wallets]
        
        # Alert if activity or high confidence
        if top_wallet_trades or len(recent_trades) >= 3:
            await self._send_social_alert(post, match, recent_trades, top_wallet_trades)
    
    async def _send_social_alert(self, post: SocialPost, match: Dict, 
                                 all_trades: List[Dict], smart_trades: List[Dict]):
        """Send alert about social post + market correlation"""
        
        market = match["market"]
        
        # Calculate metrics
        total_volume = sum(t["usdc_value"] for t in all_trades)
        smart_volume = sum(t["usdc_value"] for t in smart_trades)
        
        # Platform emoji
        platform_emoji = "🐦" if post.platform == "twitter" else "🎺"
        
        # Determine alert type
        if smart_trades:
            alert_type = f"{platform_emoji} SMART MONEY REACTING"
            severity = "CRITICAL"
        elif len(all_trades) >= 5:
            alert_type = f"{platform_emoji} MARKET MOVING"
            severity = "HIGH"
        else:
            alert_type = f"{platform_emoji} INFLUENTIAL POST"
            severity = "MEDIUM"
        
        # Get engagement metrics
        engagement_str = ""
        if post.engagement:
            likes = post.engagement.get("likes", 0)
            retweets = post.engagement.get("retweets", 0)
            if likes or retweets:
                engagement_str = f"\n<b>Engagement:</b> {likes:,} ❤️  {retweets:,} 🔄"
        
        # Build message
        message = f"""
{alert_type}

<b>{platform_emoji} @{post.username}:</b>
"{post.content[:150]}{'...' if len(post.content) > 150 else ''}"
{engagement_str}

<b>💹 Related Market:</b>
{market.get('question', 'Unknown')[:100]}
<b>Match:</b> {match['confidence']*100:.0f}%

<b>⚡ Market Reaction (30m):</b>
• Trades: {len(all_trades)}
• Volume: ${total_volume:,.0f}
• Smart Money: {len(smart_trades)} trades (${smart_volume:,.0f})

<b>🔗 Links:</b>
<a href="{post.url}">View Post</a> | <a href="https://polymarket.com/event/{match['slug']}">View Market</a>

<i>Posted {int((time.time() - post.posted_at)/60)}m ago</i>
"""
        
        # Send via Telegram
        if self.scanner.telegram:
            self.scanner.telegram.send_message(message.strip())
            logger.info(f"Sent social alert for @{post.username} post")


# Integration function
async def run_with_social_monitoring(scanner, twitter_bearer: str = None,
                                    monitored_accounts: List[str] = None):
    """Run scanner with social media monitoring"""
    
    from news_correlator import MarketMatcher, WalletActivityAnalyzer
    
    # Setup components
    market_matcher = MarketMatcher(scanner.api)
    wallet_analyzer = WalletActivityAnalyzer(scanner.db, scanner.api)
    
    correlator = SocialMediaCorrelator(scanner, market_matcher, wallet_analyzer)
    correlator.setup_monitors(twitter_bearer, monitored_accounts)
    
    # Run both
    await asyncio.gather(
        scanner.poll_recent_trades(interval=30),
        correlator.monitor_social_activity(check_interval=180)  # Check every 3 min
    )
