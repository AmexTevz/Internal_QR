import json
import os
from typing import Optional, Dict, Any


class JsonStorage:
    def __init__(self, file_path: str = "session_data.json"):
        self.file_path = file_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Ensure the directory for the JSON file exists"""
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def save_data(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data saved to {self.file_path}: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error saving data to JSON file: {str(e)}")

    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            if not os.path.exists(self.file_path):
                print(f"JSON file not found at {self.file_path}")
                return None
            
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading data from JSON file: {str(e)}")
            return None

    def get_value(self, key: str) -> Optional[Any]:
        """Get a specific value from the JSON file"""
        data = self.load_data()
        if data:
            return data.get(key)
        return None

    def update_value(self, key: str, value: Any):
        """Update a specific value in the JSON file"""
        data = self.load_data() or {}
        data[key] = value
        self.save_data(data)

    def clear_data(self):
        """Clear all data from the JSON file"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                print(f"JSON file cleared: {self.file_path}")
        except Exception as e:
            print(f"Error clearing JSON file: {str(e)}") 