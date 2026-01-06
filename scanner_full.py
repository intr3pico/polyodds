"""
Polymarket Scanner - FULL VERSION
Includes: Insider Detection + News Correlation + Social Media Monitoring
"""

import asyncio
import sys

from polymarket_scanner import PolymarketScanner
from news_correlator import NewsMarketCorrelator, run_with_news_correlation
from social_monitor import run_with_social_monitoring

try:
    import config
    import news_config
    import social_config
except ImportError as e:
    print(f"⚠️  Configuration file missing: {e}")
    sys.exit(1)


async def main():
    """Main entry point with all features"""
    
    print("\n" + "="*70)
    print("🔍 POLYMARKET SCANNER - FULL SUITE")
    print("="*70 + "\n")
    
    # Validate configurations
    if not config.validate_config():
        return
    
    if news_config.ENABLE_NEWS_CORRELATION:
        news_config.validate_news_config()
    
    if social_config.ENABLE_TWITTER or social_config.ENABLE_TRUTHSOCIAL:
        social_config.validate_social_config()
    
    # Setup scanner
    scanner = PolymarketScanner(
        telegram_bot_token=config.TELEGRAM_BOT_TOKEN if config.ENABLE_TELEGRAM else None,
        telegram_chat_id=config.TELEGRAM_CHAT_ID if config.ENABLE_TELEGRAM else None
    )
    
    # Initialize
    await scanner.initialize()
    
    # Build feature list
    features = ["✅ Insider Detection"]
    if news_config.ENABLE_NEWS_CORRELATION:
        features.append("✅ News Correlation")
    if social_config.ENABLE_TWITTER:
        features.append("✅ Twitter Monitoring")
    if social_config.ENABLE_TRUTHSOCIAL:
        features.append("✅ Truth Social (experimental)")
    
    # Send startup message
    if scanner.telegram:
        scanner.telegram.send_message(
            "🚀 <b>Polymarket Scanner - FULL SUITE</b>\n\n"
            f"📊 Tracking {len(scanner.tracked_markets)} markets\n"
            f"\n<b>Active Features:</b>\n" + "\n".join(features) + "\n"
            f"\n⚡ Monitoring for opportunities..."
        )
    
    # Analyze history
    if config.ANALYZE_HISTORY_ON_START:
        print("📊 Analyzing historical performance...")
        high_performers = scanner.analyze_historical_performance(
            days=config.HISTORICAL_DAYS,
            min_trades=config.MIN_TRADES_FOR_PERFORMER
        )
        
        if high_performers and scanner.telegram:
            message = "📊 <b>Top Performers (7 days)</b>\n\n"
            for i, perf in enumerate(high_performers[:10], 1):
                message += (
                    f"{i}. <code>{perf['wallet'][:10]}...</code>\n"
                    f"   Win: {perf['win_rate']*100:.0f}% | "
                    f"Vol: ${perf['volume']:,.0f} | "
                    f"Trades: {perf['trades']}\n\n"
                )
            scanner.telegram.send_message(message)
    
    # Determine what to run
    tasks = []
    
    # Base scanner
    tasks.append(scanner.poll_recent_trades(interval=config.TRADE_POLL_INTERVAL))
    
    # Add news correlation
    if news_config.ENABLE_NEWS_CORRELATION:
        print(f"\n📰 News correlation enabled!")
        print(f"   Checking every {news_config.NEWS_CHECK_INTERVAL/60:.0f} minutes\n")
        
        from news_correlator import NewsMarketCorrelator, MarketMatcher, WalletActivityAnalyzer
        
        market_matcher = MarketMatcher(scanner.api)
        wallet_analyzer = WalletActivityAnalyzer(scanner.db, scanner.api)
        news_correlator = NewsMarketCorrelator(scanner, news_config.NEWSAPI_KEY, news_config.TWITTER_BEARER_TOKEN)
        
        tasks.append(news_correlator.monitor_news_correlation(
            check_interval=news_config.NEWS_CHECK_INTERVAL
        ))
    
    # Add social media monitoring
    if social_config.ENABLE_TWITTER or social_config.ENABLE_TRUTHSOCIAL:
        print(f"\n🐦 Social media monitoring enabled!")
        print(f"   Watching {len(social_config.MONITORED_ACCOUNTS)} accounts")
        print(f"   Checking every {social_config.SOCIAL_CHECK_INTERVAL/60:.0f} minutes\n")
        
        from social_monitor import SocialMediaCorrelator, MarketMatcher, WalletActivityAnalyzer
        
        if 'market_matcher' not in locals():
            market_matcher = MarketMatcher(scanner.api)
            wallet_analyzer = WalletActivityAnalyzer(scanner.db, scanner.api)
        
        social_correlator = SocialMediaCorrelator(scanner, market_matcher, wallet_analyzer)
        social_correlator.setup_monitors(
            twitter_bearer=social_config.TWITTER_BEARER_TOKEN,
            monitored_accounts=social_config.MONITORED_ACCOUNTS
        )
        
        tasks.append(social_correlator.monitor_social_activity(
            check_interval=social_config.SOCIAL_CHECK_INTERVAL
        ))
    
    print("🚀 All systems active!\n")
    
    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Scanner stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
