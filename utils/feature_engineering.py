import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import timedelta


class FeatureEngineer:
    """Extract features from raw health and location data."""
    
    @staticmethod
    def compute_health_trends(status_df: pd.DataFrame) -> pd.DataFrame:
        """Compute trends and changes in health metrics over time."""
        features = []
        
        for citizen_id in status_df['CitizenID'].unique():
            citizen_data = status_df[status_df['CitizenID'] == citizen_id].sort_values('Timestamp')
            
            if len(citizen_data) < 2:
                continue
            
            activity_values = citizen_data['PhysicalActivityIndex'].values
            sleep_values = citizen_data['SleepQualityIndex'].values
            env_values = citizen_data['EnvironmentalExposureLevel'].values
            
            feature_dict = {
                'CitizenID': citizen_id,
                'num_events': len(citizen_data),
                
                'activity_mean': np.mean(activity_values),
                'activity_std': np.std(activity_values),
                'activity_min': np.min(activity_values),
                'activity_max': np.max(activity_values),
                'activity_trend': activity_values[-1] - activity_values[0],
                'activity_recent_avg': np.mean(activity_values[-3:]) if len(activity_values) >= 3 else np.mean(activity_values),
                'activity_early_avg': np.mean(activity_values[:3]) if len(activity_values) >= 3 else np.mean(activity_values),
                
                'sleep_mean': np.mean(sleep_values),
                'sleep_std': np.std(sleep_values),
                'sleep_min': np.min(sleep_values),
                'sleep_max': np.max(sleep_values),
                'sleep_trend': sleep_values[-1] - sleep_values[0],
                'sleep_recent_avg': np.mean(sleep_values[-3:]) if len(sleep_values) >= 3 else np.mean(sleep_values),
                'sleep_early_avg': np.mean(sleep_values[:3]) if len(sleep_values) >= 3 else np.mean(sleep_values),
                
                'env_mean': np.mean(env_values),
                'env_std': np.std(env_values),
                'env_min': np.min(env_values),
                'env_max': np.max(env_values),
                'env_trend': env_values[-1] - env_values[0],
                'env_recent_avg': np.mean(env_values[-3:]) if len(env_values) >= 3 else np.mean(env_values),
                'env_early_avg': np.mean(env_values[:3]) if len(env_values) >= 3 else np.mean(env_values),
                
                'has_specialist_consultation': int('specialist consultation' in citizen_data['EventType'].values),
                'has_follow_up': int('follow-up assessment' in citizen_data['EventType'].values),
                'specialist_count': sum(citizen_data['EventType'] == 'specialist consultation'),
                'follow_up_count': sum(citizen_data['EventType'] == 'follow-up assessment'),
                
                'first_event_date': citizen_data['Timestamp'].min(),
                'last_event_date': citizen_data['Timestamp'].max(),
                'days_span': (citizen_data['Timestamp'].max() - citizen_data['Timestamp'].min()).days,
            }
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    @staticmethod
    def compute_mobility_features(locations_df: pd.DataFrame) -> pd.DataFrame:
        """Compute mobility patterns from location data."""
        features = []
        
        for user_id in locations_df['user_id'].unique():
            user_locs = locations_df[locations_df['user_id'] == user_id].sort_values('timestamp')
            
            if len(user_locs) < 2:
                continue
            
            lats = user_locs['lat'].values
            lngs = user_locs['lng'].values
            
            distances = []
            for i in range(1, len(lats)):
                dist = FeatureEngineer._haversine_distance(
                    lats[i-1], lngs[i-1], lats[i], lngs[i]
                )
                distances.append(dist)
            
            unique_cities = user_locs['city'].nunique()
            
            time_diffs = user_locs['timestamp'].diff().dt.total_seconds() / 3600
            time_diffs = time_diffs[time_diffs.notna()]
            
            feature_dict = {
                'user_id': user_id,
                'num_locations': len(user_locs),
                'unique_cities': unique_cities,
                'total_distance_km': sum(distances) if distances else 0,
                'avg_distance_km': np.mean(distances) if distances else 0,
                'max_distance_km': max(distances) if distances else 0,
                'lat_range': max(lats) - min(lats),
                'lng_range': max(lngs) - min(lngs),
                'avg_time_between_records_hours': np.mean(time_diffs) if len(time_diffs) > 0 else 0,
                'first_location_date': user_locs['timestamp'].min(),
                'last_location_date': user_locs['timestamp'].max(),
            }
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in kilometers."""
        R = 6371
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def compute_anomaly_scores(health_features: pd.DataFrame) -> pd.DataFrame:
        """Compute anomaly scores based on health metric changes."""
        df = health_features.copy()
        
        df['activity_decline_score'] = np.clip(-df['activity_trend'] / 50, 0, 2)
        df['sleep_decline_score'] = np.clip(-df['sleep_trend'] / 50, 0, 2)
        df['env_increase_score'] = np.clip(df['env_trend'] / 50, 0, 2)
        
        df['recent_vs_early_activity'] = df['activity_early_avg'] - df['activity_recent_avg']
        df['recent_vs_early_sleep'] = df['sleep_early_avg'] - df['sleep_recent_avg']
        df['recent_vs_early_env'] = df['env_recent_avg'] - df['env_early_avg']
        
        df['medical_escalation_score'] = (
            df['specialist_count'] * 2 + 
            df['follow_up_count'] * 1.5
        )
        
        df['composite_anomaly_score'] = (
            df['activity_decline_score'] * 1.5 +
            df['sleep_decline_score'] * 1.2 +
            df['env_increase_score'] * 1.3 +
            df['medical_escalation_score'] * 0.5
        )
        
        return df
