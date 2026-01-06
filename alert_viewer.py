#!/usr/bin/env python3
"""
Alert Viewer Utility
View and analyze alerts stored in the database
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Optional


class AlertViewer:
    """View and filter alerts from the database"""
    
    def __init__(self, db_path="polymarket_scanner.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def get_alerts(self, hours: int = 24, severity: Optional[str] = None, 
                   limit: int = 50) -> list:
        """Get alerts from the database"""
        cursor = self.conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        query = """
            SELECT * FROM alerts 
            WHERE timestamp > ?
        """
        params = [cutoff]
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_statistics(self, hours: int = 24) -> dict:
        """Get alert statistics"""
        cursor = self.conn.cursor()
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        # Total alerts by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE timestamp > ?
            GROUP BY severity
        """, (cutoff,))
        
        severity_counts = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        # Top alerted wallets
        cursor.execute("""
            SELECT wallet_address, COUNT(*) as alert_count,
                   AVG(trade_size) as avg_trade_size,
                   MAX(trade_size) as max_trade_size
            FROM alerts
            WHERE timestamp > ?
            GROUP BY wallet_address
            ORDER BY alert_count DESC
            LIMIT 10
        """, (cutoff,))
        
        top_wallets = cursor.fetchall()
        
        # Top alerted markets
        cursor.execute("""
            SELECT market_title, COUNT(*) as alert_count,
                   SUM(trade_size) as total_volume
            FROM alerts
            WHERE timestamp > ?
            GROUP BY market_title
            ORDER BY alert_count DESC
            LIMIT 10
        """, (cutoff,))
        
        top_markets = cursor.fetchall()
        
        return {
            'severity_counts': severity_counts,
            'top_wallets': top_wallets,
            'top_markets': top_markets
        }
    
    def display_alerts(self, hours: int = 24, severity: Optional[str] = None,
                       limit: int = 50):
        """Display alerts in a formatted way"""
        
        alerts = self.get_alerts(hours, severity, limit)
        
        print(f"\n{'='*80}")
        print(f"ALERTS - Last {hours} hours" + (f" (Severity: {severity})" if severity else ""))
        print(f"{'='*80}\n")
        
        if not alerts:
            print("No alerts found matching criteria")
            return
        
        severity_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }
        
        for i, alert in enumerate(alerts, 1):
            emoji = severity_emoji.get(alert['severity'], "⚪")
            timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            wallet = f"{alert['wallet_address'][:8]}...{alert['wallet_address'][-6:]}"
            
            print(f"{i}. {emoji} {alert['severity']} - {alert['alert_type']}")
            print(f"   Time: {timestamp}")
            print(f"   Market: {alert['market_title'][:60]}")
            print(f"   Wallet: {wallet}")
            print(f"   Trade: {alert['side']} {alert['outcome']} @ ${alert['price']:.3f}")
            print(f"   Size: ${alert['trade_size']:,.2f}")
            
            if alert['wallet_age_hours']:
                print(f"   Wallet Age: {alert['wallet_age_hours']:.1f}h | Trades: {alert['wallet_total_trades']}")
            
            if alert['wallet_win_rate']:
                print(f"   Win Rate: {alert['wallet_win_rate']*100:.1f}%")
            
            print(f"   Reason: {alert['reason']}")
            print(f"   Sent: {'Yes' if alert['sent_to_telegram'] else 'No'}")
            print()
    
    def display_statistics(self, hours: int = 24):
        """Display alert statistics"""
        
        stats = self.get_statistics(hours)
        
        print(f"\n{'='*80}")
        print(f"ALERT STATISTICS - Last {hours} hours")
        print(f"{'='*80}\n")
        
        # Severity breakdown
        print("📊 BY SEVERITY")
        print("-" * 40)
        total_alerts = sum(stats['severity_counts'].values())
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = stats['severity_counts'].get(severity, 0)
            pct = (count / total_alerts * 100) if total_alerts > 0 else 0
            print(f"{severity:10} {count:4} ({pct:5.1f}%)")
        
        print(f"\nTotal Alerts: {total_alerts}")
        
        # Top wallets
        if stats['top_wallets']:
            print(f"\n🔍 TOP ALERTED WALLETS")
            print("-" * 80)
            
            for i, wallet in enumerate(stats['top_wallets'][:5], 1):
                addr = wallet['wallet_address']
                short_addr = f"{addr[:8]}...{addr[-6:]}"
                count = wallet['alert_count']
                avg_size = wallet['avg_trade_size']
                max_size = wallet['max_trade_size']
                
                print(f"{i}. {short_addr}")
                print(f"   Alerts: {count} | Avg Trade: ${avg_size:,.0f} | Max Trade: ${max_size:,.0f}")
        
        # Top markets
        if stats['top_markets']:
            print(f"\n📈 TOP ALERTED MARKETS")
            print("-" * 80)
            
            for i, market in enumerate(stats['top_markets'][:5], 1):
                title = market['market_title'][:60]
                count = market['alert_count']
                volume = market['total_volume']
                
                print(f"{i}. {title}")
                print(f"   Alerts: {count} | Total Volume: ${volume:,.0f}")
        
        print("\n" + "="*80 + "\n")
    
    def export_to_csv(self, hours: int = 24, filename: str = "alerts_export.csv"):
        """Export alerts to CSV"""
        import csv
        
        alerts = self.get_alerts(hours, limit=1000)
        
        if not alerts:
            print("No alerts to export")
            return
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'severity', 'alert_type', 'wallet_address',
                'market_title', 'side', 'outcome', 'price', 'trade_size',
                'wallet_age_hours', 'wallet_total_trades', 'wallet_win_rate',
                'reason'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for alert in alerts:
                writer.writerow({
                    'timestamp': datetime.fromtimestamp(alert['timestamp']).isoformat(),
                    'severity': alert['severity'],
                    'alert_type': alert['alert_type'],
                    'wallet_address': alert['wallet_address'],
                    'market_title': alert['market_title'],
                    'side': alert['side'],
                    'outcome': alert['outcome'],
                    'price': alert['price'],
                    'trade_size': alert['trade_size'],
                    'wallet_age_hours': alert['wallet_age_hours'],
                    'wallet_total_trades': alert['wallet_total_trades'],
                    'wallet_win_rate': alert['wallet_win_rate'],
                    'reason': alert['reason']
                })
        
        print(f"✅ Exported {len(alerts)} alerts to {filename}")


def main():
    """Main entry point"""
    
    viewer = AlertViewer()
    
    if len(sys.argv) < 2:
        print("Usage: python alert_viewer.py <command> [options]")
        print("\nCommands:")
        print("  list [hours] [severity]  - List recent alerts")
        print("  stats [hours]            - Show alert statistics")
        print("  export [hours] [file]    - Export alerts to CSV")
        print("\nExamples:")
        print("  python alert_viewer.py list 24")
        print("  python alert_viewer.py list 48 CRITICAL")
        print("  python alert_viewer.py stats 168")
        print("  python alert_viewer.py export 24 alerts.csv")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == 'list':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            severity = sys.argv[3] if len(sys.argv) > 3 else None
            viewer.display_alerts(hours, severity)
            
        elif command == 'stats':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            viewer.display_statistics(hours)
            
        elif command == 'export':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            filename = sys.argv[3] if len(sys.argv) > 3 else "alerts_export.csv"
            viewer.export_to_csv(hours, filename)
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
