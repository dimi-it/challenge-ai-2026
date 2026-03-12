#!/usr/bin/env python3
"""
Test script to verify the health monitoring system components.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer


def test_data_loading():
    """Test data loading functionality."""
    print("Testing Data Loading...")
    print("-" * 60)
    
    loader = DataLoader("input_sandbox/public_lev_1")
    
    users = loader.load_users()
    print(f"[OK] Loaded {len(users)} users")
    
    personas = loader.load_personas()
    print(f"[OK] Loaded {len(personas)} personas")
    
    status = loader.load_status()
    print(f"[OK] Loaded {len(status)} status records")
    print(f"  Columns: {list(status.columns)}")
    
    locations = loader.load_locations()
    print(f"[OK] Loaded {len(locations)} location records")
    
    print("\nSample User:")
    sample_user = list(users.values())[0]
    print(f"  ID: {sample_user.user_id}")
    print(f"  Name: {sample_user.first_name} {sample_user.last_name}")
    print(f"  Age: {2026 - sample_user.birth_year}")
    print(f"  Job: {sample_user.job}")
    print(f"  City: {sample_user.city}")
    
    return users, personas, status, locations


def test_feature_engineering(status, locations):
    """Test feature engineering functionality."""
    print("\n" + "="*60)
    print("Testing Feature Engineering...")
    print("-" * 60)
    
    engineer = FeatureEngineer()
    
    health_features = engineer.compute_health_trends(status)
    print(f"[OK] Computed health features for {len(health_features)} citizens")
    print(f"  Columns: {list(health_features.columns)[:10]}...")
    
    health_features = engineer.compute_anomaly_scores(health_features)
    print(f"[OK] Computed anomaly scores")
    
    mobility_features = engineer.compute_mobility_features(locations)
    print(f"[OK] Computed mobility features for {len(mobility_features)} citizens")
    
    print("\nTop 3 Citizens by Anomaly Score:")
    top_3 = health_features.nlargest(3, 'composite_anomaly_score')
    for idx, row in top_3.iterrows():
        print(f"\n  {idx+1}. {row['CitizenID']}")
        print(f"     Anomaly Score: {row['composite_anomaly_score']:.2f}")
        print(f"     Activity Trend: {row['activity_trend']:.1f}")
        print(f"     Sleep Trend: {row['sleep_trend']:.1f}")
        print(f"     Env Trend: {row['env_trend']:.1f}")
        print(f"     Specialist Visits: {row['specialist_count']}")
    
    return health_features, mobility_features


def test_integration():
    """Test full integration."""
    print("\n" + "="*60)
    print("Integration Test")
    print("="*60)
    
    users, personas, status, locations = test_data_loading()
    health_features, mobility_features = test_feature_engineering(status, locations)
    
    print("\n" + "="*60)
    print("[SUCCESS] All tests passed!")
    print("="*60)
    print("\nSystem is ready. Run the main analysis with:")
    print("  python run_health_analysis.py input_sandbox/public_lev_1")


if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
