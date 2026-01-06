"""
Polymarket Scanner with News Correlation
Main entry point that includes news monitoring
"""

import asyncio
import sys
from polymarket_scanner import PolymarketScanner
from news_correlator import run_with_news_correlation

try:
    import config
    import news_config
except ImportError as e:
    print(f"⚠️  Configuration file missing: {e}")
    print("Run: python quick_start.py")
    sys.exit(1)


async def main():
    """Main entry point with news correlation"""
    
    print("\n" + "="*70)
    print("🔍 POLYMARKET SCANNER WITH NEWS CORRELATION")
    print("="*70 + "\n")
    
    # Validate configurations
    if not config.validate_config():
        print("❌ Configuration validation failed")
        return
    
    if news_config.ENABLE_NEWS_CORRELATION:
        news_config.validate_news_config()
    
    # Setup scanner
    scanner = PolymarketScanner(
        telegram_bot_token=config.TELEGRAM_BOT_TOKEN if config.ENABLE_TELEGRAM else None,
        telegram_chat_id=config.TELEGRAM_CHAT_ID if config.ENABLE_TELEGRAM else None
    )
    
    # Initialize
    await scanner.initialize()
    
    # Send startup message
    if scanner.telegram:
        scanner.telegram.send_message(
            "🚀 <b>Polymarket Scanner Started</b>\n\n"
            f"📊 Tracking {len(scanner.tracked_markets)} markets\n"
            f"📰 News Correlation: {'✅ Enabled' if news_config.ENABLE_NEWS_CORRELATION else '❌ Disabled'}\n"
            "⚡ Monitoring for insider patterns..."
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
    
    # Run with or without news correlation
    if news_config.ENABLE_NEWS_CORRELATION:
        print("\n📰 News correlation enabled!")
        print(f"   Checking news every {news_config.NEWS_CHECK_INTERVAL/60:.0f} minutes")
        print(f"   Using: {'NewsAPI + RSS' if news_config.NEWSAPI_KEY else 'RSS feeds only'}\n")
        
        # Run both scanner and news monitor
        await run_with_news_correlation(
            scanner,
            newsapi_key=news_config.NEWSAPI_KEY,
            twitter_bearer=news_config.TWITTER_BEARER_TOKEN
        )
    else:
        print("\n📰 News correlation disabled")
        print("   Enable in news_config.py\n")
        
        # Run normal scanner only
        await scanner.poll_recent_trades(interval=config.TRADE_POLL_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Scanner stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
