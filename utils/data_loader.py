import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class UserProfile:
    user_id: str
    first_name: str
    last_name: str
    birth_year: int
    job: str
    city: str
    lat: float
    lng: float


class DataLoader:
    """Utility class to load and preprocess challenge data files."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        
    def load_users(self) -> Dict[str, UserProfile]:
        """Load user profiles from users.json."""
        users_file = self.data_dir / "users.json"
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        users = {}
        for user in users_data:
            profile = UserProfile(
                user_id=user['user_id'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                birth_year=user['birth_year'],
                job=user['job'],
                city=user['residence']['city'],
                lat=float(user['residence']['lat']),
                lng=float(user['residence']['lng'])
            )
            users[profile.user_id] = profile
        
        return users
    
    def load_personas(self) -> Dict[str, str]:
        """Load persona descriptions from personas.md."""
        personas_file = self.data_dir / "personas.md"
        with open(personas_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        personas = {}
        sections = content.split('---')
        
        for section in sections[1:]:
            lines = section.strip().split('\n')
            if len(lines) < 2:
                continue
            
            header = lines[0]
            if '##' in header:
                user_id = header.split('##')[1].strip().split(' - ')[0].strip()
                persona_text = '\n'.join(lines)
                personas[user_id] = persona_text
        
        return personas
    
    def load_status(self) -> pd.DataFrame:
        """Load health status data from status.csv."""
        status_file = self.data_dir / "status.csv"
        df = pd.read_csv(status_file)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    
    def load_locations(self) -> pd.DataFrame:
        """Load location tracking data from locations.json."""
        locations_file = self.data_dir / "locations.json"
        with open(locations_file, 'r', encoding='utf-8') as f:
            locations_data = json.load(f)
        
        df = pd.DataFrame(locations_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def load_all(self) -> Tuple[Dict[str, UserProfile], Dict[str, str], pd.DataFrame, pd.DataFrame]:
        """Load all data files."""
        users = self.load_users()
        personas = self.load_personas()
        status = self.load_status()
        locations = self.load_locations()
        
        return users, personas, status, locations
