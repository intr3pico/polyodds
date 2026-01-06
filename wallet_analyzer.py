#!/usr/bin/env python3
"""
Wallet Analyzer Utility
Analyze a specific wallet's trading history and performance
"""

import sys
import json
from polymarket_scanner import PolymarketAPI, Database, WalletAnalyzer
from datetime import datetime


def format_timestamp(ts):
    """Format Unix timestamp to readable date"""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def analyze_wallet(wallet_address: str, show_trades: bool = False):
    """Analyze a specific wallet"""
    
    print(f"\n{'='*70}")
    print(f"Analyzing Wallet: {wallet_address}")
    print(f"{'='*70}\n")
    
    # Initialize components
    api = PolymarketAPI()
    db = Database()
    analyzer = WalletAnalyzer(api, db)
    
    # Get wallet statistics
    stats = analyzer.analyze_wallet(wallet_address, force_refresh=True)
    
    if not stats:
        print("❌ No trading activity found for this wallet")
        return
    
    # Display wallet statistics
    print("📊 WALLET STATISTICS")
    print("-" * 70)
    print(f"First Trade:     {format_timestamp(stats.first_trade_time)}")
    print(f"Age:             {(datetime.now().timestamp() - stats.first_trade_time) / 3600:.1f} hours")
    print(f"Total Trades:    {stats.total_trades}")
    print(f"Total Volume:    ${stats.total_volume:,.2f}")
    print(f"Average Bet:     ${stats.avg_bet_size:,.2f}")
    print(f"Largest Bet:     ${stats.largest_bet:,.2f}")
    print(f"Markets Traded:  {len(stats.markets_traded)}")
    
    if stats.win_rate:
        print(f"Win Rate:        {stats.win_rate*100:.1f}%")
        print(f"Profitable:      {stats.profitable_markets}/{stats.total_markets} markets")
    else:
        print(f"Win Rate:        N/A (no closed positions)")
    
    # Get current positions
    positions = api.get_wallet_positions(wallet_address)
    
    if positions:
        print(f"\n💼 CURRENT POSITIONS ({len(positions)})")
        print("-" * 70)
        
        total_value = sum(p.get('currentValue', 0) for p in positions)
        total_pnl = sum(p.get('cashPnl', 0) for p in positions)
        
        print(f"Total Position Value: ${total_value:,.2f}")
        print(f"Total P&L:            ${total_pnl:,.2f}")
        
        # Show top 5 positions
        positions_sorted = sorted(positions, key=lambda x: x.get('currentValue', 0), reverse=True)
        
        print("\nTop 5 Positions:")
        for i, pos in enumerate(positions_sorted[:5], 1):
            title = pos.get('title', 'Unknown')[:50]
            value = pos.get('currentValue', 0)
            pnl = pos.get('cashPnl', 0)
            pnl_pct = pos.get('percentPnl', 0)
            outcome = pos.get('outcome', 'Unknown')
            
            print(f"\n{i}. {title}")
            print(f"   Outcome: {outcome}")
            print(f"   Value: ${value:,.2f}")
            print(f"   P&L: ${pnl:,.2f} ({pnl_pct:.1f}%)")
    
    # Show recent trades if requested
    if show_trades:
        activity = api.get_wallet_activity(wallet_address, limit=20)
        trades = [a for a in activity if a.get('type') == 'TRADE']
        
        if trades:
            print(f"\n📝 RECENT TRADES (Last {len(trades)})")
            print("-" * 70)
            
            for i, trade in enumerate(trades[:10], 1):
                title = trade.get('title', 'Unknown')[:45]
                side = trade.get('side', 'UNKNOWN')
                outcome = trade.get('outcome', 'Unknown')
                size = trade.get('usdcSize', 0)
                price = trade.get('price', 0)
                timestamp = trade.get('timestamp', 0)
                
                print(f"\n{i}. [{format_timestamp(timestamp)}]")
                print(f"   {title}")
                print(f"   {side} {outcome} @ ${price:.3f} | Size: ${size:,.2f}")
    
    # Risk assessment
    print(f"\n🎯 RISK ASSESSMENT")
    print("-" * 70)
    
    risk_factors = []
    
    # Check if new wallet
    age_hours = (datetime.now().timestamp() - stats.first_trade_time) / 3600
    if age_hours < 168:  # Less than 1 week
        risk_factors.append(f"⚠️  New wallet ({age_hours:.0f}h old)")
    
    # Check if low trade count
    if stats.total_trades < 10:
        risk_factors.append(f"⚠️  Low trade count ({stats.total_trades} trades)")
    
    # Check if single market focus
    if len(stats.markets_traded) == 1:
        risk_factors.append(f"⚠️  Only trades 1 market (possible insider)")
    elif len(stats.markets_traded) <= 3:
        risk_factors.append(f"⚠️  Only trades {len(stats.markets_traded)} markets")
    
    # Check if high win rate with few trades
    if stats.win_rate and stats.win_rate > 0.7 and stats.total_trades < 20:
        risk_factors.append(f"⚠️  High win rate ({stats.win_rate*100:.0f}%) with few trades")
    
    # Check average bet size
    if stats.avg_bet_size > 10000:
        risk_factors.append(f"⚠️  Large average bet size (${stats.avg_bet_size:,.0f})")
    
    if risk_factors:
        print("\n".join(risk_factors))
    else:
        print("✅ No significant risk factors detected")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python wallet_analyzer.py <wallet_address> [--trades]")
        print("\nExample:")
        print("  python wallet_analyzer.py 0x1234567890123456789012345678901234567890")
        print("  python wallet_analyzer.py 0x1234567890123456789012345678901234567890 --trades")
        sys.exit(1)
    
    wallet_address = sys.argv[1]
    show_trades = '--trades' in sys.argv
    
    # Validate wallet address format
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        print("❌ Invalid wallet address format")
        print("Expected format: 0x followed by 40 hexadecimal characters")
        sys.exit(1)
    
    try:
        analyze_wallet(wallet_address, show_trades)
    except Exception as e:
        print(f"\n❌ Error analyzing wallet: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
