import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from core.binance_utils import get_all_futures_prices

class PriceTracker:
    def __init__(self):
        self.tracking_sessions = {}  # symbol -> tracking_info
        self.tracking_directory = "config/saves/tracking"
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Ensure the tracking directory exists"""
        os.makedirs(self.tracking_directory, exist_ok=True)
    
    def start_tracking(self, symbol: str, initial_price: float, threshold_type: str, 
                      threshold_value: float, window_minutes: int):
        """
        Start tracking a symbol for the next hour after an alert
        
        Args:
            symbol: The cryptocurrency symbol
            initial_price: Price when alert was triggered
            threshold_type: 'up' or 'down' 
            threshold_value: The percentage change that triggered the alert
            window_minutes: The timeframe window that was being monitored
        """
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(hours=1)
        
        tracking_info = {
            'symbol': symbol,
            'start_time': now.isoformat(),
            'end_time': end_time.isoformat(),
            'initial_price': initial_price,
            'threshold_type': threshold_type,
            'threshold_value': threshold_value,
            'window_minutes': window_minutes,
            'price_data': [(now.isoformat(), initial_price)],
            'session_id': f"{symbol}_{now.strftime('%Y%m%d_%H%M%S')}"
        }
        
        self.tracking_sessions[symbol] = tracking_info
        print(f"Started tracking {symbol} for 1 hour after {threshold_type} alert of {threshold_value:.2f}%")
    
    def update_tracking_data(self):
        """Update tracking data for all active sessions"""
        if not self.tracking_sessions:
            return
        
        prices = get_all_futures_prices()
        if not prices:
            return
        
        now = datetime.now(timezone.utc)
        completed_sessions = []
        
        for symbol, tracking_info in self.tracking_sessions.items():
            end_time = datetime.fromisoformat(tracking_info['end_time'])
            
            # Check if tracking period is over
            if now >= end_time:
                completed_sessions.append(symbol)
                self._save_tracking_session(tracking_info)
                continue
            
            # Update price data if price is available
            if symbol in prices:
                current_price = prices[symbol]
                tracking_info['price_data'].append((now.isoformat(), current_price))
                
                # Calculate current change from initial price
                initial_price = tracking_info['initial_price']
                current_change = ((current_price - initial_price) / initial_price) * 100
                
                print(f"Tracking {symbol}: {current_change:+.2f}% from alert trigger price")
        
        # Remove completed sessions
        for symbol in completed_sessions:
            del self.tracking_sessions[symbol]
    
    def _save_tracking_session(self, tracking_info: dict):
        """Save completed tracking session to file with data science optimized format"""
        session_id = tracking_info['session_id']
        filename = f"{session_id}.json"
        filepath = os.path.join(self.tracking_directory, filename)
        
        # Calculate comprehensive statistics for data science analysis
        price_data = tracking_info['price_data']
        if len(price_data) > 1:
            prices = [price[1] for price in price_data]
            timestamps = [price[0] for price in price_data]
            initial_price = tracking_info['initial_price']
            
            # Basic price statistics
            final_price = prices[-1]
            max_price = max(prices)
            min_price = min(prices)
            avg_price = sum(prices) / len(prices)
            
            # Percentage changes from initial price
            final_change = ((final_price - initial_price) / initial_price) * 100
            max_change = ((max_price - initial_price) / initial_price) * 100
            min_change = ((min_price - initial_price) / initial_price) * 100
            avg_change = ((avg_price - initial_price) / initial_price) * 100
            
            # Calculate price movements and volatility metrics
            price_changes = []
            percent_changes = []
            for i in range(1, len(prices)):
                price_change = prices[i] - prices[i-1]
                percent_change = (price_change / prices[i-1]) * 100
                price_changes.append(price_change)
                percent_changes.append(percent_change)
            
            # Volatility metrics
            import statistics
            volatility = statistics.stdev(percent_changes) if len(percent_changes) > 1 else 0
            variance = statistics.variance(percent_changes) if len(percent_changes) > 1 else 0
            
            # Time-based analysis
            start_dt = datetime.fromisoformat(tracking_info['start_time'])
            end_dt = datetime.fromisoformat(tracking_info['end_time'])
            actual_duration_seconds = (datetime.fromisoformat(timestamps[-1]) - start_dt).total_seconds()
            
            # Market trend analysis
            positive_moves = sum(1 for change in percent_changes if change > 0)
            negative_moves = sum(1 for change in percent_changes if change < 0)
            neutral_moves = sum(1 for change in percent_changes if change == 0)
            
            tracking_info['analytics'] = {
                # Basic statistics
                'final_price': final_price,
                'max_price': max_price,
                'min_price': min_price,
                'avg_price': avg_price,
                'price_range': max_price - min_price,
                
                # Percentage changes from initial
                'final_change_percent': final_change,
                'max_change_percent': max_change,
                'min_change_percent': min_change,
                'avg_change_percent': avg_change,
                'total_change_range': max_change - min_change,
                
                # Volatility and risk metrics
                'volatility_stdev': volatility,
                'variance': variance,
                'price_movements_count': len(price_changes),
                'avg_absolute_change': sum(abs(change) for change in percent_changes) / len(percent_changes) if percent_changes else 0,
                
                # Market behavior
                'positive_moves': positive_moves,
                'negative_moves': negative_moves,
                'neutral_moves': neutral_moves,
                'positive_move_ratio': positive_moves / len(percent_changes) if percent_changes else 0,
                'trend_direction': 'bullish' if final_change > 0 else 'bearish' if final_change < 0 else 'neutral',
                
                # Time metrics
                'total_data_points': len(price_data),
                'actual_duration_seconds': actual_duration_seconds,
                'data_frequency_seconds': actual_duration_seconds / len(price_data) if len(price_data) > 1 else 0,
                
                # Additional features for ML
                'alert_magnitude': tracking_info['threshold_value'],
                'alert_direction': 1 if tracking_info['threshold_type'] == 'up' else -1,
                'monitoring_window_minutes': tracking_info['window_minutes'],
                'session_start_hour': start_dt.hour,
                'session_start_weekday': start_dt.weekday(),  # 0=Monday, 6=Sunday
                'initial_price_level': 'high' if initial_price > avg_price else 'low',
            }
            
            # Keep original summary for backward compatibility
            tracking_info['summary'] = {
                'final_price': final_price,
                'final_change_percent': final_change,
                'max_price': max_price,
                'max_change_percent': max_change,
                'min_price': min_price,
                'min_change_percent': min_change,
                'total_data_points': len(price_data)
            }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(tracking_info, f, indent=2)
            
            symbol = tracking_info['symbol']
            threshold_type = tracking_info['threshold_type']
            threshold_value = tracking_info['threshold_value']
            
            if 'analytics' in tracking_info:
                final_change = tracking_info['analytics']['final_change_percent']
                volatility = tracking_info['analytics']['volatility_stdev']
                trend = tracking_info['analytics']['trend_direction']
                print(f"✓ Completed tracking for {symbol} after {threshold_type} alert of {threshold_value:.2f}%")
                print(f"  Final change: {final_change:+.2f}% | Volatility: {volatility:.2f}% | Trend: {trend}")
                print(f"  Data points: {tracking_info['analytics']['total_data_points']} | Saved to: {filename}")
            else:
                print(f"✓ Completed tracking for {symbol} (insufficient data) | Saved to: {filename}")
                
        except Exception as e:
            print(f"Failed to save tracking data for {tracking_info['session_id']}: {e}")
    
    def get_active_tracking_count(self) -> int:
        """Get the number of currently active tracking sessions"""
        return len(self.tracking_sessions)
    
    def get_active_symbols(self) -> List[str]:
        """Get list of symbols currently being tracked"""
        return list(self.tracking_sessions.keys())
    
    def is_tracking(self, symbol: str) -> bool:
        """Check if a symbol is currently being tracked"""
        return symbol in self.tracking_sessions
