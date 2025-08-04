import json
import os
from datetime import datetime
from typing import List, Dict
import glob

class TrackingDataAnalyzer:
    def __init__(self):
        self.tracking_directory = "config/saves/tracking"
    
    def list_all_tracking_files(self) -> List[str]:
        """Get list of all tracking files"""
        pattern = os.path.join(self.tracking_directory, "*.json")
        return glob.glob(pattern)
    
    def load_tracking_data(self, filepath: str) -> Dict:
        """Load tracking data from a specific file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def get_recent_tracking_data(self, days: int = 7) -> List[Dict]:
        """Get tracking data from the last N days"""
        files = self.list_all_tracking_files()
        recent_data = []
        
        from datetime import datetime, timedelta, timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        for file in files:
            data = self.load_tracking_data(file)
            if data:
                start_time = datetime.fromisoformat(data['start_time'])
                # Make start_time timezone-aware if it's naive
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                
                if start_time >= cutoff_date:
                    data['filename'] = os.path.basename(file)
                    recent_data.append(data)
        
        # Sort by start time, most recent first
        recent_data.sort(key=lambda x: x['start_time'], reverse=True)
        return recent_data
    
    def print_summary(self, days: int = 7):
        """Print a summary of recent tracking data"""
        data = self.get_recent_tracking_data(days)
        
        if not data:
            print(f"No tracking data found in the last {days} days.")
            return
        
        print(f"\n📊 TRACKING SUMMARY - Last {days} days")
        print("=" * 60)
        
        # Group by symbol
        by_symbol = {}
        for entry in data:
            symbol = entry['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(entry)
        
        for symbol, entries in by_symbol.items():
            print(f"\n🪙 {symbol} ({len(entries)} alerts)")
            print("-" * 40)
            
            for entry in entries:
                start_time = datetime.fromisoformat(entry['start_time'])
                threshold_type = entry['threshold_type']
                threshold_value = entry['threshold_value']
                
                print(f"  📅 {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                print(f"  🚨 Alert: {threshold_value:.2f}% {threshold_type}")
                
                # Check for new analytics format first, then fallback to summary
                if 'analytics' in entry:
                    analytics = entry['analytics']
                    final_change = analytics['final_change_percent']
                    max_change = analytics['max_change_percent']
                    min_change = analytics['min_change_percent']
                    volatility = analytics.get('volatility_stdev', 0)
                    trend = analytics.get('trend_direction', 'unknown')
                    
                    print(f"  📈 Final: {final_change:+.2f}% | Max: {max_change:+.2f}% | Min: {min_change:+.2f}%")
                    print(f"  📊 Volatility: {volatility:.2f}% | Trend: {trend}")
                    print(f"  📊 Data points: {analytics['total_data_points']}")
                elif 'summary' in entry:
                    summary = entry['summary']
                    final_change = summary['final_change_percent']
                    max_change = summary['max_change_percent']
                    min_change = summary['min_change_percent']
                    
                    print(f"  📈 Final: {final_change:+.2f}% | Max: {max_change:+.2f}% | Min: {min_change:+.2f}%")
                    print(f"  📊 Data points: {summary['total_data_points']}")
                else:
                    print(f"  ⚠️  Insufficient data collected")
                
                print(f"  📁 File: {entry['filename']}")
                print()
    
    def get_symbol_statistics(self, symbol: str, days: int = 30) -> Dict:
        """Get statistics for a specific symbol"""
        data = self.get_recent_tracking_data(days)
        symbol_data = [entry for entry in data if entry['symbol'] == symbol]
        
        if not symbol_data:
            return {}
        
        stats = {
            'total_alerts': len(symbol_data),
            'up_alerts': len([e for e in symbol_data if e['threshold_type'] == 'up']),
            'down_alerts': len([e for e in symbol_data if e['threshold_type'] == 'down']),
            'avg_threshold': sum(e['threshold_value'] for e in symbol_data) / len(symbol_data),
            'completed_tracking_sessions': len([e for e in symbol_data if 'summary' in e])
        }
        
        completed_sessions = [e for e in symbol_data if 'summary' in e]
        if completed_sessions:
            final_changes = [e['summary']['final_change_percent'] for e in completed_sessions]
            stats['avg_final_change'] = sum(final_changes) / len(final_changes)
            stats['best_final_change'] = max(final_changes)
            stats['worst_final_change'] = min(final_changes)
        
        return stats

def main():
    """Command line interface for tracking data analysis"""
    import sys
    
    analyzer = TrackingDataAnalyzer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            analyzer.print_summary(days)
        
        elif command == "stats":
            if len(sys.argv) < 3:
                print("Usage: python tracking_analyzer.py stats <SYMBOL> [days]")
                return
            
            symbol = sys.argv[2].upper()
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            stats = analyzer.get_symbol_statistics(symbol, days)
            
            if not stats:
                print(f"No tracking data found for {symbol} in the last {days} days.")
                return
            
            print(f"\n📊 STATISTICS FOR {symbol} - Last {days} days")
            print("=" * 50)
            print(f"Total alerts: {stats['total_alerts']}")
            print(f"Up alerts: {stats['up_alerts']}")
            print(f"Down alerts: {stats['down_alerts']}")
            print(f"Average threshold: {stats['avg_threshold']:.2f}%")
            print(f"Completed tracking sessions: {stats['completed_tracking_sessions']}")
            
            if 'avg_final_change' in stats:
                print(f"Average final change: {stats['avg_final_change']:+.2f}%")
                print(f"Best final change: {stats['best_final_change']:+.2f}%")
                print(f"Worst final change: {stats['worst_final_change']:+.2f}%")
        
        else:
            print("Unknown command. Available commands: summary, stats")
    
    else:
        analyzer.print_summary()

if __name__ == "__main__":
    main()
