#!/usr/bin/env python3
"""
Test Script for Polymarket Scanner
Verifies API connectivity and configuration
"""

import sys
import requests
from datetime import datetime


def print_header(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def test_polymarket_api():
    """Test Polymarket API connectivity"""
    print_header("🌐 Testing Polymarket API")
    
    try:
        # Test Gamma API (markets)
        print("Testing Gamma API (markets)...")
        response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 5, "active": "true"},
            timeout=10
        )
        response.raise_for_status()
        markets = response.json()
        
        print(f"✅ Gamma API working - Found {len(markets)} markets")
        
        if markets:
            print(f"   Sample market: {markets[0].get('question', 'N/A')[:60]}")
        
        # Test CLOB API (prices)
        print("\nTesting CLOB API (prices)...")
        
        # Get a token ID from the first market
        token_id = None
        if markets and markets[0].get('clobTokenIds'):
            token_ids = markets[0].get('clobTokenIds', [])
            if isinstance(token_ids, list) and token_ids:
                token_id = token_ids[0]
            elif isinstance(token_ids, str):
                token_id = token_ids
        
        if token_id:
            response = requests.get(
                f"https://clob.polymarket.com/price",
                params={"token_id": token_id, "side": "BUY"},
                timeout=10
            )
            response.raise_for_status()
            price_data = response.json()
            
            print(f"✅ CLOB API working - Price: {price_data.get('price', 'N/A')}")
        else:
            print("⚠️  Could not test CLOB API (no token ID found)")
        
        # Test Data API (activity endpoint)
        print("\nTesting Data API (wallet activity)...")
        # Use a known active wallet address
        test_wallet = "0x0000000000000000000000000000000000000000"
        
        response = requests.get(
            f"https://data-api.polymarket.com/activity",
            params={"user": test_wallet, "limit": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Data API working")
        else:
            print(f"⚠️  Data API returned status code: {response.status_code}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False


def test_telegram_config():
    """Test Telegram configuration"""
    print_header("📱 Testing Telegram Configuration")
    
    try:
        import config
        
        if not config.ENABLE_TELEGRAM:
            print("⚠️  Telegram notifications are disabled in config")
            return True
        
        if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ Bot token not configured")
            return False
        
        if config.TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
            print("❌ Chat ID not configured")
            return False
        
        print(f"Bot Token: {config.TELEGRAM_BOT_TOKEN[:10]}...")
        print(f"Chat ID: {config.TELEGRAM_CHAT_ID}")
        
        # Test sending a message
        response = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": "🧪 Test message from Polymarket Scanner setup",
                "parse_mode": "HTML"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("\n✅ Telegram bot is working!")
            print("   Check your Telegram for a test message")
        else:
            print(f"\n❌ Telegram error: {response.text}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  config.py not found - run quick_start.py first")
        return False
    except Exception as e:
        print(f"❌ Error testing Telegram: {e}")
        return False


def test_database():
    """Test database creation and access"""
    print_header("💾 Testing Database")
    
    try:
        from polymarket_scanner import Database
        
        print("Creating database instance...")
        db = Database()
        
        print("✅ Database created successfully")
        print(f"   Location: {db.db_path}")
        
        # Test writing a dummy trade
        from polymarket_scanner import Trade
        
        test_trade = Trade(
            timestamp=int(datetime.now().timestamp()),
            wallet_address="0x0000000000000000000000000000000000000000",
            market_id="test_market",
            market_title="Test Market",
            token_id="test_token",
            side="BUY",
            size=100,
            price=0.5,
            usdc_value=50,
            outcome="Yes",
            transaction_hash="test_" + str(int(datetime.now().timestamp()))
        )
        
        db.save_trade(test_trade)
        print("✅ Database write test successful")
        
        # Clean up test data
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM trades WHERE market_id = 'test_market'")
        db.conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_wallet_analyzer():
    """Test wallet analysis functionality"""
    print_header("👛 Testing Wallet Analyzer")
    
    try:
        from polymarket_scanner import PolymarketAPI, Database, WalletAnalyzer
        
        api = PolymarketAPI()
        db = Database()
        analyzer = WalletAnalyzer(api, db)
        
        print("Wallet analyzer initialized")
        
        # Test with a known active wallet (you can replace with any active wallet)
        test_wallet = "0x6af75d4e4aaf700450efbac3708cce1665810ff1"
        
        print(f"\nTesting analysis of wallet: {test_wallet[:10]}...")
        
        stats = analyzer.analyze_wallet(test_wallet)
        
        if stats:
            print("✅ Wallet analysis successful")
            print(f"   Total trades: {stats.total_trades}")
            print(f"   Total volume: ${stats.total_volume:,.2f}")
            if stats.win_rate:
                print(f"   Win rate: {stats.win_rate*100:.1f}%")
        else:
            print("⚠️  No activity found for test wallet (this is okay)")
        
        return True
        
    except Exception as e:
        print(f"❌ Wallet analyzer error: {e}")
        return False


def test_config_validation():
    """Test configuration validation"""
    print_header("⚙️  Testing Configuration")
    
    try:
        import config
        
        print("Configuration loaded")
        print(f"  Large bet threshold: ${config.LARGE_BET_THRESHOLD:,}")
        print(f"  Very large bet threshold: ${config.VERY_LARGE_BET_THRESHOLD:,}")
        print(f"  Huge bet threshold: ${config.HUGE_BET_THRESHOLD:,}")
        print(f"  New wallet hours: {config.NEW_WALLET_HOURS}h")
        print(f"  Poll interval: {config.TRADE_POLL_INTERVAL}s")
        
        if config.validate_config():
            print("\n✅ Configuration is valid")
            return True
        else:
            print("\n❌ Configuration validation failed")
            return False
        
    except ImportError:
        print("⚠️  config.py not found")
        print("   Run: python quick_start.py")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 POLYMARKET SCANNER - SYSTEM TEST")
    print("="*70)
    
    results = {
        "API Connectivity": test_polymarket_api(),
        "Configuration": test_config_validation(),
        "Database": test_database(),
        "Telegram": test_telegram_config(),
        "Wallet Analyzer": test_wallet_analyzer()
    }
    
    # Summary
    print_header("📊 TEST RESULTS")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to start scanning.")
        print("\nRun: python polymarket_scanner.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before running.")
    
    print("\n" + "="*70 + "\n")
    
    return passed == total


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        tests = {
            "api": test_polymarket_api,
            "telegram": test_telegram_config,
            "database": test_database,
            "wallet": test_wallet_analyzer,
            "config": test_config_validation
        }
        
        if test_name in tests:
            success = tests[test_name]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available tests: {', '.join(tests.keys())}")
            sys.exit(1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
