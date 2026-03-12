#!/usr/bin/env python3
"""
Data Preprocessing Script

This script provides utilities to explore and preprocess the challenge data
before running the main analysis.
"""

import json
import pandas as pd
from pathlib import Path
import argparse


def explore_data(data_dir: str):
    """Explore and summarize the data files."""
    
    data_path = Path(data_dir)
    
    print(f"Exploring data in: {data_path}")
    print("="*80)
    
    users_file = data_path / "users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
        print(f"\n✓ users.json: {len(users)} users")
        print(f"  Sample user: {users[0]['user_id']} - {users[0]['first_name']} {users[0]['last_name']}")
    
    personas_file = data_path / "personas.md"
    if personas_file.exists():
        with open(personas_file, 'r') as f:
            content = f.read()
        sections = content.split('---')
        print(f"\n✓ personas.md: ~{len(sections)-1} personas")
    
    status_file = data_path / "status.csv"
    if status_file.exists():
        df = pd.read_csv(status_file)
        print(f"\n✓ status.csv: {len(df)} records")
        print(f"  Columns: {', '.join(df.columns)}")
        print(f"  Citizens: {df['CitizenID'].nunique()}")
        print(f"  Event types: {', '.join(df['EventType'].unique())}")
        print(f"\n  Health Metrics Summary:")
        print(f"    PhysicalActivityIndex: {df['PhysicalActivityIndex'].min():.1f} - {df['PhysicalActivityIndex'].max():.1f}")
        print(f"    SleepQualityIndex: {df['SleepQualityIndex'].min():.1f} - {df['SleepQualityIndex'].max():.1f}")
        print(f"    EnvironmentalExposureLevel: {df['EnvironmentalExposureLevel'].min():.1f} - {df['EnvironmentalExposureLevel'].max():.1f}")
    
    locations_file = data_path / "locations.json"
    if locations_file.exists():
        with open(locations_file, 'r') as f:
            locations = json.load(f)
        df_loc = pd.DataFrame(locations)
        print(f"\n✓ locations.json: {len(locations)} location records")
        print(f"  Users tracked: {df_loc['user_id'].nunique()}")
        print(f"  Cities: {df_loc['city'].nunique()}")
        print(f"  Date range: {df_loc['timestamp'].min()} to {df_loc['timestamp'].max()}")
    
    print("\n" + "="*80)


def validate_data(data_dir: str):
    """Validate data integrity and consistency."""
    
    data_path = Path(data_dir)
    issues = []
    
    print("Validating data...")
    print("="*80)
    
    with open(data_path / "users.json", 'r') as f:
        users = json.load(f)
    user_ids = {u['user_id'] for u in users}
    
    status_df = pd.read_csv(data_path / "status.csv")
    status_ids = set(status_df['CitizenID'].unique())
    
    with open(data_path / "locations.json", 'r') as f:
        locations = json.load(f)
    location_ids = {loc['user_id'] for loc in locations}
    
    if status_ids - user_ids:
        issues.append(f"Status records for unknown users: {status_ids - user_ids}")
    
    if location_ids - user_ids:
        issues.append(f"Location records for unknown users: {location_ids - user_ids}")
    
    if user_ids - status_ids:
        print(f"⚠ Users without status records: {user_ids - status_ids}")
    
    if user_ids - location_ids:
        print(f"⚠ Users without location records: {user_ids - location_ids}")
    
    if issues:
        print("\n❌ Data validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Data validation passed")
    
    print("="*80)


def export_summary(data_dir: str, output_file: str):
    """Export a summary of the data to a file."""
    
    data_path = Path(data_dir)
    
    with open(data_path / "users.json", 'r') as f:
        users = json.load(f)
    
    status_df = pd.read_csv(data_path / "status.csv")
    
    summary = []
    summary.append("DATA SUMMARY")
    summary.append("="*80)
    summary.append(f"\nTotal Users: {len(users)}\n")
    
    for user in users:
        user_id = user['user_id']
        user_status = status_df[status_df['CitizenID'] == user_id]
        
        summary.append(f"\n{user_id} - {user['first_name']} {user['last_name']}")
        summary.append(f"  Age: {2026 - user['birth_year']}")
        summary.append(f"  Job: {user['job']}")
        summary.append(f"  Location: {user['residence']['city']}")
        summary.append(f"  Health Records: {len(user_status)}")
        
        if len(user_status) > 0:
            summary.append(f"  Activity: {user_status['PhysicalActivityIndex'].mean():.1f} avg")
            summary.append(f"  Sleep: {user_status['SleepQualityIndex'].mean():.1f} avg")
            summary.append(f"  Env Exposure: {user_status['EnvironmentalExposureLevel'].mean():.1f} avg")
    
    summary.append("\n" + "="*80)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"Summary exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Preprocess and explore health monitoring data")
    parser.add_argument('data_dir', help="Directory containing data files")
    parser.add_argument('--explore', action='store_true', help="Explore data files")
    parser.add_argument('--validate', action='store_true', help="Validate data integrity")
    parser.add_argument('--export', type=str, help="Export summary to file")
    
    args = parser.parse_args()
    
    if args.explore or (not args.validate and not args.export):
        explore_data(args.data_dir)
    
    if args.validate:
        validate_data(args.data_dir)
    
    if args.export:
        export_summary(args.data_dir, args.export)


if __name__ == "__main__":
    main()
