"""
Data Science Utilities for Binance Price Tracking Analysis

This module provides tools to convert tracking data into formats 
suitable for data science analysis with pandas, numpy, and scikit-learn.
"""

import json
import glob
import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import warnings

class TrackingDataProcessor:
    """
    Processes tracking data for data science analysis
    """
    
    def __init__(self, tracking_directory: str = "config/saves/tracking"):
        self.tracking_directory = tracking_directory
    
    def load_all_tracking_sessions(self) -> List[Dict]:
        """Load all tracking session data"""
        pattern = os.path.join(self.tracking_directory, "*.json")
        files = glob.glob(pattern)
        
        sessions = []
        for file in files:
            if 'example_' in file:  # Skip example files
                continue
                
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['source_file'] = os.path.basename(file)
                    sessions.append(data)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")
        
        return sessions
    
    def to_analytics_dataframe(self) -> pd.DataFrame:
        """
        Convert tracking data to a pandas DataFrame optimized for analysis
        
        Returns:
            DataFrame with one row per tracking session and analytics features as columns
        """
        sessions = self.load_all_tracking_sessions()
        
        if not sessions:
            print("No tracking sessions found")
            return pd.DataFrame()
        
        # Extract analytics data
        rows = []
        for session in sessions:
            if 'analytics' not in session:
                continue  # Skip sessions without analytics data
            
            row = {
                # Identifiers
                'session_id': session['session_id'],
                'symbol': session['symbol'],
                'source_file': session['source_file'],
                
                # Time features
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'session_start_hour': session['analytics']['session_start_hour'],
                'session_start_weekday': session['analytics']['session_start_weekday'],
                'actual_duration_seconds': session['analytics']['actual_duration_seconds'],
                
                # Alert context
                'threshold_type': session['threshold_type'],
                'threshold_value': session['threshold_value'],
                'alert_direction': session['analytics']['alert_direction'],
                'alert_magnitude': session['analytics']['alert_magnitude'],
                'monitoring_window_minutes': session['analytics']['monitoring_window_minutes'],
                'initial_price': session['initial_price'],
                'initial_price_level': session['analytics']['initial_price_level'],
                
                # Price performance
                'final_price': session['analytics']['final_price'],
                'final_change_percent': session['analytics']['final_change_percent'],
                'max_change_percent': session['analytics']['max_change_percent'],
                'min_change_percent': session['analytics']['min_change_percent'],
                'avg_change_percent': session['analytics']['avg_change_percent'],
                'total_change_range': session['analytics']['total_change_range'],
                'price_range': session['analytics']['price_range'],
                
                # Volatility and risk
                'volatility_stdev': session['analytics']['volatility_stdev'],
                'variance': session['analytics']['variance'],
                'avg_absolute_change': session['analytics']['avg_absolute_change'],
                
                # Market behavior
                'trend_direction': session['analytics']['trend_direction'],
                'positive_moves': session['analytics']['positive_moves'],
                'negative_moves': session['analytics']['negative_moves'],
                'neutral_moves': session['analytics']['neutral_moves'],
                'positive_move_ratio': session['analytics']['positive_move_ratio'],
                
                # Data quality
                'total_data_points': session['analytics']['total_data_points'],
                'data_frequency_seconds': session['analytics']['data_frequency_seconds'],
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Convert datetime columns
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['end_time'] = pd.to_datetime(df['end_time'])
            
            # Add derived features
            df['is_weekend'] = df['session_start_weekday'].isin([5, 6])  # Saturday, Sunday
            df['alert_direction_name'] = df['alert_direction'].map({1: 'up', -1: 'down'})
            df['session_date'] = df['start_time'].dt.date
            df['exceeds_threshold'] = (
                (df['alert_direction'] == 1) & (df['final_change_percent'] > 0) |
                (df['alert_direction'] == -1) & (df['final_change_percent'] < 0)
            )
        
        return df
    
    def to_price_timeseries_dataframe(self) -> pd.DataFrame:
        """
        Convert tracking data to a time series DataFrame with all price data points
        
        Returns:
            DataFrame with columns: session_id, symbol, timestamp, price, normalized_time, change_from_initial
        """
        sessions = self.load_all_tracking_sessions()
        
        if not sessions:
            print("No tracking sessions found")
            return pd.DataFrame()
        
        rows = []
        for session in sessions:
            session_id = session['session_id']
            symbol = session['symbol']
            initial_price = session['initial_price']
            
            for timestamp_str, price in session['price_data']:
                timestamp = pd.to_datetime(timestamp_str)
                change_from_initial = ((price - initial_price) / initial_price) * 100
                
                # Normalized time (0 to 1, where 0 is start and 1 is end)
                start_time = pd.to_datetime(session['start_time'])
                end_time = pd.to_datetime(session['end_time'])
                total_duration = (end_time - start_time).total_seconds()
                elapsed = (timestamp - start_time).total_seconds()
                normalized_time = elapsed / total_duration if total_duration > 0 else 0
                
                rows.append({
                    'session_id': session_id,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'price': price,
                    'change_from_initial': change_from_initial,
                    'normalized_time': normalized_time,
                    'threshold_type': session['threshold_type'],
                    'threshold_value': session['threshold_value'],
                    'initial_price': initial_price
                })
        
        return pd.DataFrame(rows)
    
    def get_feature_matrix_for_ml(self, target_column: str = 'final_change_percent') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix and target vector for machine learning
        
        Args:
            target_column: Column to use as target variable
            
        Returns:
            Tuple of (features, target) as numpy arrays
        """
        df = self.to_analytics_dataframe()
        
        if df.empty:
            return np.array([]), np.array([])
        
        # Select numerical features for ML
        feature_columns = [
            'session_start_hour', 'session_start_weekday', 'actual_duration_seconds',
            'threshold_value', 'alert_direction', 'monitoring_window_minutes',
            'initial_price', 'max_change_percent', 'min_change_percent',
            'volatility_stdev', 'variance', 'avg_absolute_change',
            'positive_move_ratio', 'total_data_points', 'data_frequency_seconds'
        ]
        
        # Filter to available columns
        available_features = [col for col in feature_columns if col in df.columns]
        
        X = df[available_features].fillna(0).values
        y = df[target_column].fillna(0).values
        
        return X, y
    
    def export_to_csv(self, output_dir: str = "data_exports"):
        """Export tracking data to CSV files for external analysis"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export analytics DataFrame
        analytics_df = self.to_analytics_dataframe()
        if not analytics_df.empty:
            analytics_df.to_csv(os.path.join(output_dir, "tracking_analytics.csv"), index=False)
            print(f"✓ Exported {len(analytics_df)} tracking sessions to tracking_analytics.csv")
        
        # Export time series DataFrame
        timeseries_df = self.to_price_timeseries_dataframe()
        if not timeseries_df.empty:
            timeseries_df.to_csv(os.path.join(output_dir, "price_timeseries.csv"), index=False)
            print(f"✓ Exported {len(timeseries_df)} price data points to price_timeseries.csv")
        
        # Export summary statistics by symbol
        if not analytics_df.empty:
            symbol_stats = analytics_df.groupby('symbol').agg({
                'final_change_percent': ['mean', 'std', 'min', 'max', 'count'],
                'volatility_stdev': ['mean', 'std'],
                'positive_move_ratio': 'mean',
                'threshold_value': 'mean'
            }).round(4)
            symbol_stats.columns = ['_'.join(col).strip() for col in symbol_stats.columns]
            symbol_stats.to_csv(os.path.join(output_dir, "symbol_statistics.csv"))
            print(f"✓ Exported statistics for {len(symbol_stats)} symbols to symbol_statistics.csv")
        
        print(f"All exports saved to {output_dir}/ directory")
    
    def print_dataset_summary(self):
        """Print a summary of the available tracking data"""
        df = self.to_analytics_dataframe()
        
        if df.empty:
            print("No tracking data available for analysis")
            return
        
        print("📊 TRACKING DATA SUMMARY FOR DATA SCIENCE")
        print("=" * 60)
        print(f"Total tracking sessions: {len(df)}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['start_time'].min().date()} to {df['start_time'].max().date()}")
        print(f"Average session duration: {df['actual_duration_seconds'].mean() / 60:.1f} minutes")
        
        print(f"\n🎯 Alert Distribution:")
        print(f"Up alerts: {(df['alert_direction'] == 1).sum()}")
        print(f"Down alerts: {(df['alert_direction'] == -1).sum()}")
        
        print(f"\n📈 Performance Statistics:")
        print(f"Average final change: {df['final_change_percent'].mean():+.2f}%")
        print(f"Best performance: {df['final_change_percent'].max():+.2f}%")
        print(f"Worst performance: {df['final_change_percent'].min():+.2f}%")
        print(f"Average volatility: {df['volatility_stdev'].mean():.2f}%")
        
        print(f"\n🔄 Most Active Symbols:")
        top_symbols = df['symbol'].value_counts().head(5)
        for symbol, count in top_symbols.items():
            avg_change = df[df['symbol'] == symbol]['final_change_percent'].mean()
            print(f"  {symbol}: {count} sessions (avg: {avg_change:+.2f}%)")
        
        print(f"\n📊 Available for ML Analysis:")
        print(f"  - {len(df)} samples")
        print(f"  - {len([col for col in df.columns if df[col].dtype in ['int64', 'float64']])} numerical features")
        print(f"  - Target variables: final_change_percent, volatility_stdev, positive_move_ratio")

def main():
    """Command line interface for data processing"""
    import sys
    
    processor = TrackingDataProcessor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            processor.print_dataset_summary()
        
        elif command == "export":
            output_dir = sys.argv[2] if len(sys.argv) > 2 else "data_exports"
            processor.export_to_csv(output_dir)
        
        elif command == "preview":
            df = processor.to_analytics_dataframe()
            print("Analytics DataFrame Preview:")
            print(df.head())
            
            ts_df = processor.to_price_timeseries_dataframe()
            print("\nTime Series DataFrame Preview:")
            print(ts_df.head())
        
        else:
            print("Available commands: summary, export, preview")
    
    else:
        processor.print_dataset_summary()

if __name__ == "__main__":
    main()
